import torch
import numpy as np
from PIL import Image
import io, json, sys, os
from pathlib import Path
from functools import lru_cache
import torchvision.transforms as T

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[2] / "models"))
sys.path.insert(0, str(Path(__file__).parents[2] / "voice"))

# The real trained checkpoints (best_nail_model.pt etc.) were produced by
# train_cnn.py's ModalityCNN (MobileNetV3-small, one model per modality, num_classes
# inferred from that modality's own class folders) — NOT visual_cnn.py's BalanceAICNN
# (EfficientNet-B3, one shared 10-class head). Loading a ModalityCNN checkpoint into a
# BalanceAICNN would fail on both architecture and output-shape. Use the real one.
from train_cnn import ModalityCNN, VAL_TF as MODALITY_VAL_TRANSFORMS
from deficiency_predictor import BalanceAIPredictor, BayesianWrapper, DEFICIENCIES, SYMPTOMS, DIET_FEATURES, VISUAL_FEATURES, encode_user_input
from voice_pipeline import process_voice_input
from core.config import settings

MODALITY_LABELS = ["nail", "tongue", "skin"]  # "eye" excluded — no eye model was ever trained

# Each checkpoint's class names already encode which nutrient(s) it implicates —
# map straight from class name to the 25-nutrient keys used by the rest of the app.
CLASS_TO_NUTRIENTS = {
    "nail_iron_deficiency":  ["iron"],
    "nail_zinc_deficiency":  ["zinc"],
    "tongue_b12_iron":       ["vitamin_b12", "iron"],
    "tongue_folate_b12":     ["folate", "vitamin_b12"],
    "skin_iron_pallor":      ["iron"],
    "skin_vitA_deficiency":  ["vitamin_a"],
}
CLASS_TO_VISUAL_SIGN = {
    "nail_iron_deficiency":  ["nail_pale", "nail_spoon"],
    "nail_zinc_deficiency":  ["nail_white_spots", "nail_brittle"],
    "tongue_b12_iron":       ["tongue_beefy_red", "tongue_atrophic"],
    "tongue_folate_b12":     ["tongue_red_smooth", "tongue_geographic"],
    "skin_iron_pallor":      ["skin_pale"],
    "skin_vitA_deficiency":  ["skin_dry", "skin_hyperkeratosis"],
}
# Val accuracy on these models is 55-68% (3-class, ~33% chance baseline) — real signal,
# but modest. Only trust a prediction meaningfully above chance before surfacing it.
IMAGE_CONFIDENCE_THRESHOLD = 0.40

_model_cache = {}


def get_modality_model(modality: str):
    """Load the real per-modality checkpoint. Returns (model, classes) or (None, None)
    if no checkpoint exists for this modality (e.g. "eye" — never trained)."""
    cache_key = f"cnn_{modality}"
    if cache_key not in _model_cache:
        path = settings.MODALITY_MODEL_PATHS.get(modality)
        if not path or not Path(path).exists():
            _model_cache[cache_key] = (None, None)
        else:
            # train_cnn.py saves a dict (model_state + the exact class list/order used
            # for that modality), not a bare state_dict — load it as what it actually is.
            ckpt = torch.load(path, map_location="cpu")
            classes = ckpt["classes"]
            model = ModalityCNN(num_classes=len(classes), pretrained=False)
            model.load_state_dict(ckpt["model_state"])
            model.eval()
            _model_cache[cache_key] = (model, classes)
    return _model_cache[cache_key]


def get_predictor():
    if "predictor" not in _model_cache:
        base = BalanceAIPredictor(use_temporal=False)
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
    if modality not in MODALITY_LABELS:
        # "eye" (or anything else untrained) — be explicit, never fabricate a prediction.
        return {
            "available": False,
            "modality": modality,
            "reason": f"no trained model for '{modality}'",
            "top_prediction": None,
            "all_predictions": [],
            "visual_signs_inferred": [],
            "nutrients": [],
            "confidence": 0.0,
        }

    model, classes = get_modality_model(modality)
    if model is None:
        return {
            "available": False,
            "modality": modality,
            "reason": f"checkpoint missing for '{modality}'",
            "top_prediction": None,
            "all_predictions": [],
            "visual_signs_inferred": [],
            "nutrients": [],
            "confidence": 0.0,
        }

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = MODALITY_VAL_TRANSFORMS(img).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=-1)[0]

    results = [{"class": cls, "probability": round(prob, 4)} for cls, prob in zip(classes, probs.tolist())]
    results.sort(key=lambda x: x["probability"], reverse=True)

    top = results[0]
    is_confident = top["probability"] > IMAGE_CONFIDENCE_THRESHOLD and "normal" not in top["class"]
    visual_signs = CLASS_TO_VISUAL_SIGN.get(top["class"], []) if is_confident else []
    nutrients = CLASS_TO_NUTRIENTS.get(top["class"], []) if is_confident else []

    return {
        "available": True,
        "modality": modality,
        "top_prediction": top,
        "all_predictions": results[:5],
        "visual_signs_inferred": visual_signs,
        "nutrients": nutrients,
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


# ── Layer 5: Food Photo Log ──────────────────────────────────────────────────
# No custom-trained classifier here — food has hundreds of dishes, not a fixed
# small class set, so a from-scratch CNN (like the nail/tongue/skin models) would
# need per-dish training data we don't have. Instead this uses CLIP zero-shot
# matching (pretrained, no training required) against the existing Indian food
# database — genuinely correct approach for this problem, it was just never wired
# into the API.
#
# Portion size (grams) is NOT detected from the photo — a 2D image with no depth
# or reference object cannot reveal how much food is on THIS plate, and body size
# doesn't change that either (a tall and a short person can equally have a small
# or huge portion in front of them in any given photo). What body size DOES give
# us is a reasonable proxy for someone's TYPICAL portion, via the same Mifflin-St
# Jeor TDEE calculation already used elsewhere (activity_calorie_engine.py) — so
# when a profile is provided, the flat "standard Indian serving" default is scaled
# by the person's TDEE relative to a reference adult, capped to a modest range
# since appetite doesn't scale linearly with body size. This personalizes the
# ASSUMPTION; it does not measure the actual photo. Every response says so.
FOOD_MATCH_MIN_SCORE = 0.18  # matches camera_interface.CLIP_THRESHOLD
REFERENCE_TDEE = 2200.0      # ~average sedentary adult, used as the scaling baseline
PORTION_SCALE_MIN, PORTION_SCALE_MAX = 0.75, 1.35  # keep personalization modest


def _portion_scale_factor(weight_kg, height_cm, age_years, sex, job_type, exercise_type, exercise_min) -> float:
    if not (weight_kg and height_cm and age_years and sex):
        return 1.0
    from activity_calorie_engine import calculate_tdee
    try:
        tdee_info = calculate_tdee(
            weight_kg, height_cm, age_years, sex,
            job_type or "sedentary", exercise_type or "none", exercise_min or 0,
        )
        raw = tdee_info["tdee"] / REFERENCE_TDEE
        return max(PORTION_SCALE_MIN, min(PORTION_SCALE_MAX, raw))
    except Exception:
        return 1.0


def analyze_meal_photo(
    image_bytes: bytes,
    weight_kg: float = None,
    height_cm: float = None,
    age_years: float = None,
    sex: str = None,
    job_type: str = None,
    exercise_type: str = None,
    exercise_min: int = None,
) -> dict:
    from camera_interface import recognize_foods_in_image
    from indian_food_database import FOOD_LOOKUP
    from food_diary_analyzer import DEFAULT_PORTIONS

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    try:
        matches = recognize_foods_in_image(img)
    except Exception as e:
        return {"available": False, "reason": f"food recognition failed: {e}", "items": []}

    if not matches:
        return {
            "available": False,
            "reason": "no food matched with enough confidence",
            "items": [],
        }

    scale_factor = _portion_scale_factor(weight_kg, height_cm, age_years, sex, job_type, exercise_type, exercise_min)
    personalized = scale_factor != 1.0

    items = []
    for m in matches[:3]:  # top-3 candidates — a plate is often more than one dish
        entry = FOOD_LOOKUP.get(m["lookup_key"])
        if entry is None:
            continue
        base_portion_g = DEFAULT_PORTIONS.get(m["lookup_key"], 100)
        portion_g = round(base_portion_g * scale_factor)
        scale = portion_g / 100.0
        nutrients = {n: round(entry["nutrients"].get(n, 0.0) * scale, 4) for n in DEFICIENCIES}
        items.append({
            "food_name": entry["name"],
            "confidence": m["score"],
            "assumed_portion_g": portion_g,
            "standard_portion_g": base_portion_g,
            "portion_personalized": personalized,
            "kcal": round(entry.get("kcal", 0) * scale, 1),
            "nutrients": nutrients,
        })

    return {
        "available": len(items) > 0,
        "items": items,
        "note": (
            "Portion size is scaled to your typical intake (via TDEE) as a personalized "
            "default, not measured from this photo."
            if personalized else
            "Portion size is a standard Indian serving assumption, not measured from the photo."
        ),
    }
