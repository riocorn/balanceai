import torch
import numpy as np
from PIL import Image
import io, json, sys, os
from pathlib import Path
from functools import lru_cache

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[2] / "models"))
sys.path.insert(0, str(Path(__file__).parents[2] / "voice"))

from visual_cnn import BalanceAICNN, VAL_TRANSFORMS, DEFICIENCY_CLASSES
from deficiency_predictor import BalanceAIPredictor, BayesianWrapper, DEFICIENCIES, SYMPTOMS, DIET_FEATURES, VISUAL_FEATURES, encode_user_input
from voice_pipeline import process_voice_input
from core.config import settings

MODALITY_LABELS = ["nail", "tongue", "eye"]

_model_cache = {}


def get_cnn_model():
    if "cnn" not in _model_cache:
        model = BalanceAICNN(backbone="efficientnet_b3", pretrained=False)
        if Path(settings.CNN_MODEL_PATH).exists():
            model.load_state_dict(torch.load(settings.CNN_MODEL_PATH, map_location="cpu"))
            model.eval()
        else:
            model.eval()
        _model_cache["cnn"] = model
    return _model_cache["cnn"]


def get_predictor():
    if "predictor" not in _model_cache:
        base = BalanceAIPredictor(use_temporal=True)
        bayesian = BayesianWrapper(base, n_mc=20)
        if Path(settings.PREDICTOR_MODEL_PATH).exists():
            base.load_state_dict(torch.load(settings.PREDICTOR_MODEL_PATH, map_location="cpu"))
        _model_cache["predictor"] = bayesian
    return _model_cache["predictor"]


def get_knowledge_base():
    if "kb" not in _model_cache:
        kb = {}
        for key, path in [
            ("rda", settings.ICMR_RDA_PATH),
            ("usda", settings.USDA_PATH),
            ("state_diet", settings.STATE_DIET_PATH),
            ("deficiency_map", settings.DEFICIENCY_MAP_PATH),
        ]:
            if Path(path).exists():
                with open(path, encoding="utf-8") as f:
                    kb[key] = json.load(f)
            else:
                kb[key] = {}
        _model_cache["kb"] = kb
    return _model_cache["kb"]


def analyze_image(image_bytes: bytes, modality: str) -> dict:
    model = get_cnn_model()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = VAL_TRANSFORMS(img).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=-1)[0]

    results = []
    for cls, prob in zip(DEFICIENCY_CLASSES, probs.tolist()):
        results.append({"class": cls, "probability": round(prob, 4)})
    results.sort(key=lambda x: x["probability"], reverse=True)

    top = results[0]
    visual_signs = []
    VISUAL_SIGN_MAP = {
        "nail": {
            "iron_deficiency": ["nail_pale", "nail_spoon"],
            "zinc_deficiency": ["nail_white_spots", "nail_brittle"],
            "calcium_deficiency": ["nail_ridged", "nail_brittle"],
            "vitamin_b12_deficiency": ["nail_pale"],
            "vitamin_c_deficiency": ["nail_spoon"],
        },
        "tongue": {
            "iron_deficiency": ["tongue_atrophic", "tongue_red_smooth"],
            "vitamin_b12_deficiency": ["tongue_beefy_red", "tongue_atrophic"],
            "folate_deficiency": ["tongue_red_smooth", "tongue_geographic"],
            "niacin_deficiency": ["tongue_red_smooth"],
        },
        "eye": {
            "iron_deficiency": ["eye_conjunctival_pallor"],
            "vitamin_a_deficiency": ["eye_bitots_spots", "eye_night_blind"],
            "vitamin_d_deficiency": ["eye_dry"],
            "omega3_deficiency": ["eye_dry"],
        },
    }

    if top["probability"] > 0.25 and top["class"] != "normal":
        signs = VISUAL_SIGN_MAP.get(modality, {}).get(top["class"], [])
        visual_signs.extend(signs)

    return {
        "modality": modality,
        "top_prediction": top,
        "all_predictions": results[:5],
        "visual_signs_inferred": visual_signs,
        "confidence": round(top["probability"], 4),
    }


def run_deficiency_prediction(symptoms: list, diet: dict, visual_signs: list, history_sequence: list = None) -> dict:
    predictor = get_predictor()

    x = torch.tensor(encode_user_input(symptoms, diet, visual_signs)).unsqueeze(0)
    x_seq = None
    if history_sequence and len(history_sequence) >= 2:
        seq = [encode_user_input(h["symptoms"], h["diet"], h["visual_signs"]) for h in history_sequence[-30:]]
        while len(seq) < 30:
            seq.insert(0, np.zeros(x.shape[-1], dtype=np.float32))
        x_seq = torch.tensor(np.array(seq)).unsqueeze(0)

    result = predictor(x, x_seq)
    probs = result["deficiency_probs"][0].detach().numpy()
    uncertainty = result["uncertainty"][0].detach().numpy()

    predictions = []
    for i, name in enumerate(DEFICIENCIES):
        p = float(probs[i])
        u = float(uncertainty[i])
        predictions.append({
            "deficiency": name,
            "probability": round(p, 4),
            "confidence": round(1.0 - u, 4),
            "risk_level": "high" if p > 0.6 else "medium" if p > 0.35 else "low",
        })
    predictions.sort(key=lambda x: x["probability"], reverse=True)
    return predictions


def compute_balance_score(predictions: list) -> dict:
    HIGH_WEIGHT = 3.0
    MED_WEIGHT = 1.5
    LOW_WEIGHT = 0.3
    MAX_SCORE = 100.0

    penalty = 0
    for p in predictions:
        if p["risk_level"] == "high":
            penalty += HIGH_WEIGHT * p["probability"]
        elif p["risk_level"] == "medium":
            penalty += MED_WEIGHT * p["probability"]
        else:
            penalty += LOW_WEIGHT * p["probability"]

    max_penalty = HIGH_WEIGHT * len(DEFICIENCIES)
    score = max(0.0, MAX_SCORE * (1 - penalty / max_penalty))

    high_risk = [p["deficiency"] for p in predictions if p["risk_level"] == "high"]
    medium_risk = [p["deficiency"] for p in predictions if p["risk_level"] == "medium"]

    if score >= 80:
        label = "Excellent"
    elif score >= 65:
        label = "Good"
    elif score >= 45:
        label = "Fair — action needed"
    else:
        label = "Poor — consult doctor"

    return {
        "score": round(score, 1),
        "label": label,
        "high_risk_deficiencies": high_risk,
        "medium_risk_deficiencies": medium_risk,
    }


def get_food_recommendations(high_risk: list, medium_risk: list, state: str = None, is_vegetarian: bool = False) -> list:
    kb = get_knowledge_base()
    deficiency_map = kb.get("deficiency_map", {})
    state_diet = kb.get("state_diet", {})

    recommendations = []
    priority = high_risk[:3] + medium_risk[:2]

    for deficiency in priority:
        info = deficiency_map.get(deficiency, {})
        foods = info.get("food_sources_india", [])
        if is_vegetarian:
            foods = [f for f in foods if not any(m in f for m in ["fish", "chicken", "meat", "egg", "beef", "pork", "mutton"])]

        state_key = state.replace(" ", "_") if state else None
        state_foods = []
        if state_key and state_key in state_diet:
            s = state_diet[state_key]
            state_foods = s.get("common_vegetables", [])[:2] + s.get("common_fruits", [])[:2]

        rec = {
            "for_deficiency": deficiency,
            "rda": info.get("rda_india", ""),
            "top_foods": foods[:5],
            "state_specific_foods": state_foods[:3],
            "prevalence_note": info.get("prevalence_india", ""),
        }
        recommendations.append(rec)

    return recommendations


def process_full_checkin(
    voice_text: str = None,
    audio_bytes: bytes = None,
    nail_image: bytes = None,
    tongue_image: bytes = None,
    eye_image: bytes = None,
    user_state: str = None,
    is_vegetarian: bool = False,
    history: list = None,
) -> dict:

    voice_result = {}
    if audio_bytes:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        voice_result = process_voice_input(audio_path=tmp_path, whisper_model=settings.WHISPER_MODEL_SIZE)
        os.unlink(tmp_path)
    elif voice_text:
        voice_result = process_voice_input(text_input=voice_text)

    symptoms = voice_result.get("symptoms_detected", [])
    diet = voice_result.get("diet_info", {})
    if is_vegetarian:
        diet["is_vegetarian"] = 1
    visual_signs = voice_result.get("visual_signs_mentioned", [])

    cnn_results = {}
    for modality, img_bytes in [("nail", nail_image), ("tongue", tongue_image), ("eye", eye_image)]:
        if img_bytes:
            result = analyze_image(img_bytes, modality)
            cnn_results[modality] = result
            visual_signs.extend(result.get("visual_signs_inferred", []))

    visual_signs = list(set(visual_signs))

    predictions = run_deficiency_prediction(symptoms, diet, visual_signs, history)
    balance = compute_balance_score(predictions)
    recommendations = get_food_recommendations(
        balance["high_risk_deficiencies"],
        balance["medium_risk_deficiencies"],
        state=user_state,
        is_vegetarian=is_vegetarian,
    )

    return {
        "voice": {
            "transcript": voice_result.get("raw_text", voice_text or ""),
            "language": voice_result.get("language", "text"),
            "symptoms_detected": symptoms,
            "diet_info": diet,
        },
        "camera": cnn_results,
        "visual_signs": visual_signs,
        "deficiency_predictions": predictions[:10],
        "balance_score": balance,
        "recommendations": recommendations,
        "top_3_risks": predictions[:3],
    }
