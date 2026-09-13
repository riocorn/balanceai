import whisper
import spacy
import re
import json
import os
from pathlib import Path
from symptom_knowledge import ALL_SYMPTOM_MAPS, DIET_QUESTIONS_HINDI

MODEL_CACHE = {}

def load_whisper(model_size="base"):
    if model_size not in MODEL_CACHE:
        MODEL_CACHE[model_size] = whisper.load_model(model_size)
    return MODEL_CACHE[model_size]

def load_spacy():
    if "spacy" not in MODEL_CACHE:
        MODEL_CACHE["spacy"] = spacy.load("en_core_web_sm")
    return MODEL_CACHE["spacy"]


def transcribe_audio(audio_path, model_size="base"):
    model = load_whisper(model_size)
    result = model.transcribe(
        audio_path,
        language=None,
        task="transcribe",
        fp16=False,
        verbose=False,
    )
    return {
        "text": result["text"].strip(),
        "language": result.get("language", "unknown"),
        "segments": result.get("segments", []),
    }


def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r"[।,!?।;:।]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_symptoms_fuzzy(text):
    text_norm = normalize_text(text)
    words = text_norm.split()
    found = {}

    for phrase, symptom in ALL_SYMPTOM_MAPS.items():
        phrase_norm = normalize_text(phrase)
        if phrase_norm in text_norm:
            if symptom not in found:
                found[symptom] = []
            found[symptom].append(phrase)

    for i in range(len(words)):
        for window in [1, 2, 3]:
            chunk = " ".join(words[i:i+window])
            if chunk in ALL_SYMPTOM_MAPS:
                sym = ALL_SYMPTOM_MAPS[chunk]
                if sym not in found:
                    found[sym] = []
                if chunk not in found[sym]:
                    found[sym].append(chunk)

    for phrase, symptom in ALL_SYMPTOM_MAPS.items():
        phrase_words = normalize_text(phrase).split()
        if len(phrase_words) < 2:
            continue
        for i, word in enumerate(words):
            if word == phrase_words[0]:
                window = words[i:i+6]
                if all(pw in window for pw in phrase_words):
                    if symptom not in found:
                        found[symptom] = []
                    found[symptom].append(phrase + " [proximity]")

    return found


def extract_symptoms_spacy(text):
    nlp = load_spacy()
    doc = nlp(text)

    SYMPTOM_ENTITIES = {"DISEASE", "ORG", "PRODUCT"}
    found = {}

    for ent in doc.ents:
        if ent.label_ in SYMPTOM_ENTITIES:
            text_lower = ent.text.lower()
            if text_lower in ALL_SYMPTOM_MAPS:
                sym = ALL_SYMPTOM_MAPS[text_lower]
                found[sym] = [ent.text]

    symptom_keywords = [
        "pain", "ache", "weak", "tired", "fatigue", "loss", "poor", "slow",
        "dry", "pale", "numb", "cramp", "swell", "bleed", "itch", "rash"
    ]
    for token in doc:
        if token.lemma_.lower() in symptom_keywords:
            context = " ".join([t.text for t in doc[max(0,token.i-2):token.i+3]])
            for phrase, sym in ALL_SYMPTOM_MAPS.items():
                if any(word in context.lower() for word in phrase.split()):
                    if sym not in found:
                        found[sym] = [context]

    return found


def extract_diet_info(text):
    text_norm = normalize_text(text)
    diet = {}

    veg_patterns = ["vegetarian", "veg", "shakahari", "veg khata", "meat nahi", "non-veg nahi"]
    if any(p in text_norm for p in veg_patterns):
        diet["is_vegetarian"] = 1

    vegan_patterns = ["vegan", "dairy nahi", "doodh nahi", "plant based"]
    if any(p in text_norm for p in vegan_patterns):
        diet["is_vegan"] = 1
        diet["is_vegetarian"] = 1

    fish_patterns = ["machli", "fish", "seafood", "prawn", "crab", "salmon"]
    if any(p in text_norm for p in fish_patterns):
        diet["eats_fish"] = 1

    dairy_patterns = ["doodh", "milk", "dahi", "yogurt", "paneer", "cheese", "dairy"]
    if any(p in text_norm for p in dairy_patterns):
        diet["eats_dairy"] = 1

    egg_patterns = [" anda ", " egg ", " eggs ", " ande "]
    if any(p in f" {text_norm} " for p in egg_patterns):
        diet["eats_eggs"] = 1

    greens_patterns = ["palak", "saag", "methi", "spinach", "greens", "hari sabzi", "leafy"]
    if any(p in text_norm for p in greens_patterns):
        diet["eats_leafy_greens_daily"] = 1

    legume_patterns = ["dal", "chana", "rajma", "beans", "lentil", "moong", "masoor"]
    if any(p in text_norm for p in legume_patterns):
        diet["eats_legumes_daily"] = 1

    nut_patterns = ["badam", "akhrot", "mungfali", "almond", "walnut", "peanut", "nuts", "seeds"]
    if any(p in text_norm for p in nut_patterns):
        diet["eats_nuts_seeds"] = 1

    fruit_patterns = ["fal", "aam", "seb", "kela", "amrood", "fruit", "apple", "banana", "mango"]
    if any(p in text_norm for p in fruit_patterns):
        diet["eats_fruits_daily"] = 1

    sun_patterns = ["dhoop mein", "sun exposure", "outdoor", "bahar rehte", "sun mein"]
    if any(p in text_norm for p in sun_patterns):
        diet["outdoor_sun_exposure_hrs"] = 1.0

    iodine_patterns = ["iodized salt", "iodine namak", "aayodine", "iodized"]
    if any(p in text_norm for p in iodine_patterns):
        diet["uses_iodized_salt"] = 1

    ferment_patterns = ["dahi", "idli", "dosa", "kanji", "fermented", "probiotic"]
    if any(p in text_norm for p in ferment_patterns):
        diet["eats_fermented_foods"] = 1

    return diet


def extract_visual_signs_from_description(text):
    text_norm = normalize_text(text)
    signs = []

    nail_patterns = {
        "nail_pale": ["nails pale", "light nails", "nakhun safed", "nakhun halka"],
        "nail_spoon": ["spoon shaped nails", "koilonychia", "nakhun kaunde"],
        "nail_brittle": ["nails breaking", "brittle nails", "nakhun toota", "nakhun kamzor"],
        "nail_white_spots": ["white spots nails", "nakhun dabbe", "leukonychia"],
        "nail_ridged": ["ridged nails", "nails grooves", "nakhun khaanche"],
    }

    tongue_patterns = {
        "tongue_red_smooth": ["smooth tongue", "red tongue", "jibh laal", "jibh smooth"],
        "tongue_geographic": ["geographic tongue", "map tongue", "patchy tongue"],
        "tongue_atrophic": ["tongue atrophy", "papillae loss", "jibh smooth flat"],
        "tongue_swollen": ["swollen tongue", "jibh sooji", "macroglossia"],
    }

    eye_patterns = {
        "eye_conjunctival_pallor": ["eyes pale", "inner eyelid white", "aankhein safed", "conjunctiva pale"],
        "eye_dry": ["dry eyes", "aankhein sukhna", "eye dryness"],
        "eye_bitots_spots": ["bitots spots", "white spots eyes", "foamy eyes"],
        "eye_night_blind": ["night blindness", "cant see night", "raat ko nahi dikhta"],
    }

    skin_patterns = {
        "skin_pallor": ["skin pale", "pale complexion", "rang safed", "chehra safed"],
        "skin_dry": ["dry skin", "rough skin", "khushki", "skin sookhi"],
        "skin_hyperkeratosis": ["rough bumpy skin", "chicken skin", "keratosis"],
    }

    for sign, patterns in {**nail_patterns, **tongue_patterns, **eye_patterns, **skin_patterns}.items():
        if any(p in text_norm for p in patterns):
            signs.append(sign)

    return signs


def process_voice_input(audio_path=None, text_input=None, whisper_model="base"):
    if audio_path and os.path.exists(audio_path):
        transcription = transcribe_audio(audio_path, whisper_model)
        raw_text = transcription["text"]
        language = transcription["language"]
    elif text_input:
        raw_text = text_input
        language = "text"
    else:
        return {"error": "No audio file or text provided"}

    symptoms_fuzzy = extract_symptoms_fuzzy(raw_text)
    symptoms_spacy = extract_symptoms_spacy(raw_text)

    all_symptoms = set(symptoms_fuzzy.keys()) | set(symptoms_spacy.keys())

    diet_info = extract_diet_info(raw_text)
    visual_signs = extract_visual_signs_from_description(raw_text)

    return {
        "raw_text": raw_text,
        "language": language,
        "symptoms_detected": list(all_symptoms),
        "symptom_evidence": {**symptoms_fuzzy, **symptoms_spacy},
        "diet_info": diet_info,
        "visual_signs_mentioned": visual_signs,
        "symptom_count": len(all_symptoms),
    }


if __name__ == "__main__":
    test_cases = [
        "Main bahut thaka rehta hoon aur mere baal bahut gir rahe hain. Haath pair bhi thande rehte hain.",
        "I feel very tired all the time, hair is falling, nails are brittle and I have mouth ulcers.",
        "Meri aankhein raat ko kamzor ho gayi hain aur skin bohot dry hai. Masude se khoon bhi aata hai.",
        "I'm vegetarian, don't eat dairy, always tired, forget things, tingling in hands.",
        "Vaal bahut jhadte ne, thakaan rehti hai, hath pair sunn ho jaande ne.",
    ]

    print("=== Voice Pipeline Test ===\n")
    for i, text in enumerate(test_cases, 1):
        result = process_voice_input(text_input=text)
        print(f"Test {i}: '{text[:60]}...'")
        print(f"  Symptoms: {result['symptoms_detected']}")
        print(f"  Diet: {result['diet_info']}")
        print(f"  Visual signs: {result['visual_signs_mentioned']}")
        print()
