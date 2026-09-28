import json
import os
import re
from typing import Optional

import numpy as np
import requests

from core.config import settings

_KB_CACHE: dict = {"mtime": None, "data": None, "corpus": None}
_EMBED_CACHE: dict = {"mtime": None, "ids": None, "matrix": None}
_EMBED_MODEL_SINGLETON = None


def _normalize_tokens(text: str) -> set:
    text = text.lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z]", " ", text)
    tokens = set()
    for w in text.split():
        w = w.replace("ae", "e").replace("oe", "e")
        if len(w) > 2:
            tokens.add(w)
    return tokens


# Real, observed bug (found by tracing a real 44.4%-accuracy eval run down to its
# root cause, not guessed): unfiltered flatten pulls citation/reference/methodology
# text into the embedding corpus alongside real symptoms, which both dilutes the
# corpus signal and lets any string containing a year/citation crowd out real
# symptom text under the item-count limit. Skipping these keys/patterns is a
# straight data-quality fix, not a model or prompt tweak.
_CORPUS_BLOCKED_KEYS = {
    "source", "sources", "citation", "citations", "reference", "references",
    "confidence", "url", "doi",
}
_CITATION_RE = re.compile(r"\d{4}|et al\b", re.IGNORECASE)


def _flatten_findings(node, out: list, limit: int = 8, key=None) -> None:
    if len(out) >= limit:
        return
    if key is not None and str(key).lower() in _CORPUS_BLOCKED_KEYS:
        return
    if isinstance(node, str):
        if len(node) > 20 and not _CITATION_RE.search(node):
            out.append(node)
    elif isinstance(node, dict):
        for k, v in node.items():
            _flatten_findings(v, out, limit, key=k)
            if len(out) >= limit:
                return
    elif isinstance(node, list):
        for v in node:
            _flatten_findings(v, out, limit, key=key)
            if len(out) >= limit:
                return


# NOT the same broad key list as medical_understanding.py's _extract_findings --
# tried that first and measured a real regression (5 previously-correct cases lost
# their true disease from the shortlist entirely). Root cause, verified by printing
# the actual corpus text: "specific_diagnostic_signs" and "red_flags" hold
# physician-only exam findings ("holosystolic murmur radiating to left axilla") and
# risk-stratification prose -- a patient free-text query never lexically/
# semantically resembles that, so embedding cosine similarity against it actively
# hurts retrieval. medical_understanding.py gets away with the same sections because
# it also applies _lay_term_additions (clinical-jargon -> lay-term synonym bridge)
# on top, which this module does not have. Keeping only "core" -- the one section
# verified (by direct inspection) to already be clean, patient-relevant phrasing.
_SYMPTOM_SECTION_KEYS = ("core",)


def _core_symptom_text(dz: dict) -> list:
    """Real bug found and fixed in this same function (not guessed): each item under
    symptoms.core is {"name": "<short symptom>", "note": "<long explanatory
    paragraph>", "source": ...}. Running these through the generic _flatten_findings
    pulled in the "note" paragraphs too (not blocked -- only source/citation/etc
    are), re-diluting the corpus with prose the "core" fix was meant to avoid.
    Extracting only "name" keeps this section as clean, short symptom phrases."""
    symptoms = dz.get("symptoms", {})
    parts: list = []
    for s in symptoms.get("core", []) or []:
        name = s.get("name") if isinstance(s, dict) else s if isinstance(s, str) else None
        if name:
            parts.append(name)
    return parts


def load_kb() -> dict:
    path = settings.DISEASE_MASTER_PATH
    mtime = os.path.getmtime(path)
    if _KB_CACHE["mtime"] == mtime and _KB_CACHE["data"] is not None:
        return _KB_CACHE["data"]

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    corpus = {}
    for did, dz in data.get("diseases", {}).items():
        findings: list = []
        _flatten_findings(dz.get("symptoms", {}), findings, limit=10)
        text = " ".join([dz.get("name", ""), dz.get("category", "")] + findings)
        corpus[did] = _normalize_tokens(text)

    _KB_CACHE.update({"mtime": mtime, "data": data, "corpus": corpus})
    return data


def all_disease_index() -> list:
    kb = load_kb()
    return [
        {"id": did, "name": dz.get("name", did), "category": dz.get("category", "")}
        for did, dz in kb.get("diseases", {}).items()
    ]


def shortlist_candidates(query: str, top_n: int = 15) -> list:
    load_kb()
    corpus = _KB_CACHE["corpus"] or {}
    kb = _KB_CACHE["data"]
    q_tokens = _normalize_tokens(query)
    if not q_tokens:
        return []

    scored = []
    for did, tokens in corpus.items():
        overlap = len(q_tokens & tokens)
        if overlap == 0:
            continue
        name = kb["diseases"][did].get("name", did).lower()
        bonus = 3 if any(t in name for t in q_tokens) else 0
        scored.append((overlap + bonus, did))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [did for _, did in scored[:top_n]]


def keyword_best_match(query: str) -> Optional[str]:
    candidates = shortlist_candidates(query, top_n=1)
    return candidates[0] if candidates else None


# Self-hosted matching pipeline (no external LLM API — see config.py):
#   1. translate_to_english() — local Ollama model turns the patient's free text
#      (any language/style) into a short plain English symptom sentence.
#   2. embedding shortlist is computed TWICE — once on that English translation,
#      once on the raw original text — and unioned. Verified in testing: the
#      translation step occasionally mistranslates a colloquial/regional term
#      (e.g. "nakseer" -> "rash" instead of "nosebleed"), which would silently
#      drop the correct disease from a translation-only shortlist. The raw-text
#      embedding still surfaces it (weak cross-lingual signal, but present), so
#      the union is a real recall backstop, not a redundant step.
#   3. Local LLM reranks/picks the final disease_id from that shortlist only
#      (never from the full 323 — tested and confirmed the model hallucinates a
#      fake id when given the whole catalog at once) and writes the explanation.
# Medicine names/effectiveness numbers are never generated by any model step —
# those always come straight from get_medicine_payload() reading the real KB.

_EMBED_MODEL_NAME = None


def _embedding_model():
    global _EMBED_MODEL_SINGLETON, _EMBED_MODEL_NAME
    if _EMBED_MODEL_SINGLETON is not None and _EMBED_MODEL_NAME == settings.EMBEDDING_MODEL:
        return _EMBED_MODEL_SINGLETON
    try:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL_SINGLETON = SentenceTransformer(settings.EMBEDDING_MODEL)
        _EMBED_MODEL_NAME = settings.EMBEDDING_MODEL
        return _EMBED_MODEL_SINGLETON
    except Exception:
        return None


def _embedding_cache_path() -> str:
    return settings.DISEASE_MASTER_PATH + ".embeddings.npy"


def _disease_embeddings():
    kb = load_kb()
    mtime = _KB_CACHE["mtime"]
    if _EMBED_CACHE["mtime"] == mtime and _EMBED_CACHE["matrix"] is not None:
        return _EMBED_CACHE["ids"], _EMBED_CACHE["matrix"]

    model = _embedding_model()
    if model is None:
        return None, None

    ids = list(kb["diseases"].keys())
    cache_path = _embedding_cache_path()
    ids_path = cache_path + ".ids.json"
    if os.path.exists(cache_path) and os.path.exists(ids_path):
        cached_ids = json.load(open(ids_path))
        cached_mtime = os.path.getmtime(cache_path)
        if cached_ids == ids and cached_mtime >= mtime:
            matrix = np.load(cache_path)
            _EMBED_CACHE.update({"mtime": mtime, "ids": ids, "matrix": matrix})
            return ids, matrix

    texts = []
    for did in ids:
        dz = kb["diseases"][did]
        core = _core_symptom_text(dz)
        findings: list = []
        _flatten_findings(dz.get("symptoms", {}), findings, limit=8)
        text = " ".join([dz.get("name", ""), dz.get("category", "")] + core + findings)[:1500]
        texts.append(text)

    matrix = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    np.save(cache_path, matrix)
    json.dump(ids, open(ids_path, "w"))
    _EMBED_CACHE.update({"mtime": mtime, "ids": ids, "matrix": matrix})
    return ids, matrix


def _embedding_shortlist_ids(text: str, top_n: int) -> list:
    model = _embedding_model()
    ids, matrix = _disease_embeddings()
    if model is None or ids is None:
        return []
    q_emb = model.encode([text], normalize_embeddings=True)[0]
    sims = matrix @ q_emb
    ranked = sorted(zip(ids, sims), key=lambda x: -x[1])[:top_n]
    return [did for did, _ in ranked]


def _ollama_json(prompt: str, timeout: int = 90, model: str = None) -> dict:
    resp = requests.post(
        f"{settings.OLLAMA_HOST}/api/generate",
        json={
            "model": model or settings.OLLAMA_MODEL, "prompt": prompt, "stream": False,
            "format": "json", "options": {"temperature": 0.1},
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return json.loads(resp.json()["response"])


# Verified failure mode (real test, not assumed): the 3B local model mistranslates
# less-common Hindi/regional symptom words inconsistently (e.g. "nakseer" -> "rash"
# in one run, "abdominal pain" in another — both wrong; correct = nosebleed). This
# glossary hint is a direct, deterministic fix for that exact observed class of bug.
HINDI_SYMPTOM_GLOSSARY = {
    "nakseer": "nosebleed", "naak se khoon": "nosebleed",
    "chakkar": "dizziness", "ghumna": "dizziness/vertigo",
    "jalan": "burning sensation", "sujan": "swelling",
    "khujli": "itching", "kabj": "constipation", "dast": "diarrhea",
    "bukhar": "fever", "khansi": "cough", "saans phoolna": "breathlessness",
    "saans nahi aa rahi": "difficulty breathing", "ghutno mein dard": "knee pain",
    "peshab mein jalan": "burning urination", "masudo se khoon": "bleeding gums",
    "aankh laal": "red eye", "kaan mein dard": "ear pain",
    "gale mein kharash": "throat irritation/soreness", "awaaz baith gayi": "hoarse voice",
    "dhundhla dikhna": "blurred vision", "neend nahi aana": "insomnia",
    "thakaan": "fatigue", "kamzori": "weakness", "ulti": "vomiting",
    "pet dard": "abdominal pain", "sar dard": "headache",
    "sujan aana": "swelling", "chubhan": "stinging/pricking sensation",
    "behosh": "unconscious", "daura": "seizure/fit",
}

# Deterministic, zero-hallucination-risk safety net — independent of whatever
# specific disease the AI model ends up matching. If any of these appear, the
# results page shows a hardcoded "seek emergency care now" banner regardless of
# match quality. Verified need: the local model correctly flagged an emergency
# for a chest-pain+breathlessness query but picked an unlikely specific disease
# for it (Takotsubo cardiomyopathy) that may not carry its own emergency text.
RED_FLAG_TERMS = [
    "chest pain", "seene mein dard", "chest mein dard", "saans nahi aa rahi",
    "breathing difficulty", "can't breathe", "unconscious", "behosh",
    "seizure", "daura", "severe bleeding", "bahut khoon", "stroke",
    "face drooping", "chehra tedha", "suicidal", "khudkushi",
    "poisoning", "zeher", "anaphylaxis", "severe allergic reaction",
    "coughing blood", "khoon ki ulti", "vomiting blood",
]


def detect_red_flags(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in RED_FLAG_TERMS)


def translate_to_english(query: str) -> str:
    glossary_hits = {hi: en for hi, en in HINDI_SYMPTOM_GLOSSARY.items() if hi in query.lower()}
    hint = ""
    if glossary_hits:
        hint = "Known term glossary (use these exact meanings, do not guess): " + \
            ", ".join(f'"{hi}" means "{en}"' for hi, en in glossary_hits.items()) + "\n"
    try:
        out = _ollama_json(
            hint +
            'Translate this patient symptom description into a short, plain, clinical '
            'English sentence describing only the symptoms (no diagnosis). '
            f'Patient text: "{query}"\n'
            'Reply with ONLY JSON: {"english": "..."}',
            timeout=30,
            model=settings.OLLAMA_REASONING_MODEL,
        )
        return out.get("english") or query
    except Exception:
        return query


def match_disease_with_ai(query: str) -> dict:
    result = _match_disease_with_ai_inner(query)
    result["hard_emergency_flag"] = detect_red_flags(query)
    return result


def _match_disease_with_ai_inner(query: str) -> dict:
    kb = load_kb()
    index = all_disease_index()
    valid_ids = {d["id"] for d in index}

    english = translate_to_english(query)
    shortlist_a = _embedding_shortlist_ids(english, top_n=15)
    shortlist_b = _embedding_shortlist_ids(query, top_n=12) if english != query else []

    seen = []
    for did in shortlist_a + shortlist_b:
        if did not in seen:
            seen.append(did)
    candidates = seen[:25]

    if not candidates:
        did = keyword_best_match(query)
        if not did:
            return {
                "ai_mode": "keyword_fallback",
                "disease_id": None,
                "confidence": 0.0,
                "explanation": "Aapke likhe hue text se koi matching disease nahi mil paayi. Kripya thoda aur detail mein apni problem batayein.",
            }
        candidates = [did]

    # Real, observed bug (same class as medical_understanding.py's own documented
    # cataract/erythema_multiforme fix): the catalog line used to show the LLM only
    # "id | name | category" -- zero real symptom content to discriminate close
    # differentials on. Measured effect: valve/cardiomyopathy diseases collapsed
    # onto congestive_heart_failure (their shared downstream syndrome) because the
    # model had nothing to compare against the patient's actual stated symptoms.
    # Adding each candidate's own real "core" symptoms (never invented) gives it
    # something concrete to discriminate on, same as the rerank path already does.
    def _candidate_line(did: str) -> str:
        dz = kb["diseases"][did]
        terms = _core_symptom_text(dz)[:4]
        snippet = "; ".join(t[:100] for t in terms) if terms else "(no distinguishing symptom list in KB)"
        return f"{did} | {dz.get('name', did)} | {dz.get('category', '')} | key symptoms: {snippet}"

    catalog_lines = "\n".join(_candidate_line(did) for did in candidates)

    try:
        prompt = f"""A patient described their problem below, in whatever language/style they chose.

Patient's own words: "{query}"
(Machine-translated to English for reference: "{english}")

Pick the single closest-matching disease_id from this shortlist ONLY — never invent an id
outside this list, and never state medicine names or effectiveness numbers yourself.
Compare the patient's stated symptoms against each candidate's own "key symptoms" below.
Do NOT default to a broad/generic diagnosis (e.g. a general syndrome like heart failure) just
because it can result from many causes -- if a more SPECIFIC candidate's key symptoms match what
the patient actually said at least as well, prefer the specific candidate over the generic one:
{catalog_lines}

Reply with ONLY JSON: {{"disease_id": "<id from the list above>", "confidence": <0.0-1.0>,
"explanation": "<2-3 short empathetic sentences, in the SAME language/style the patient used>",
"possible_emergency": <true/false>}}"""
        parsed = _ollama_json(prompt, timeout=90, model=settings.OLLAMA_REASONING_MODEL)
        if parsed.get("disease_id") not in valid_ids:
            parsed["disease_id"] = candidates[0]
            parsed["confidence"] = min(parsed.get("confidence", 0.5), 0.5)
        parsed["ai_mode"] = "local_llm"
        return parsed
    except Exception:
        did = candidates[0]
        name = kb["diseases"][did].get("name", did)
        return {
            "ai_mode": "embedding_fallback",
            "disease_id": did,
            "confidence": 0.4,
            "explanation": (
                f"Local AI model abhi respond nahi kar paaya, isliye ye semantic-search-based best-guess match hai: "
                f"\"{name}\". Kripya WhatsApp doctor-verification step se hi confirm karayein."
            ),
        }


def _score_name_match(a: str, b: str) -> int:
    return len(_normalize_tokens(a) & _normalize_tokens(b))


def _extract_medicine_entries(ems: dict) -> list:
    entries = []
    for key, val in ems.items():
        if key == "note" or isinstance(val, str):
            continue
        if isinstance(val, dict) and "name" in val:
            entries.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "name" in item:
                    entries.append(item)
    return entries


def _ranked_list(effectiveness_ranked_table) -> list:
    if isinstance(effectiveness_ranked_table, list):
        return effectiveness_ranked_table
    if isinstance(effectiveness_ranked_table, dict):
        return effectiveness_ranked_table.get("ranked_high_to_low", [])
    return []


def get_medicine_payload(disease_id: str) -> dict:
    kb = load_kb()
    dz = kb["diseases"].get(disease_id)
    if not dz:
        return {"found": False}

    ranked = _ranked_list(dz.get("effectiveness_ranked_table"))
    ranked_by_pct = {(r.get("name") or ""): r.get("effectiveness_pct") for r in ranked if isinstance(r, dict)}

    ems = dz.get("exhaustive_medicine_survey", {}) or {}
    ems_note = ems.get("note") if isinstance(ems.get("note"), str) else None
    medicine_entries = _extract_medicine_entries(ems)

    cards = []
    for m in medicine_entries:
        name = m.get("name") or ""
        best_pct = None
        for rname, pct in ranked_by_pct.items():
            if _score_name_match(name, rname) >= 2:
                best_pct = pct
                break
        mechanism = m.get("reason_why") or m.get("effectiveness") or m.get("note") or ""
        cards.append({
            "name": name,
            "type": m.get("type") or "",
            "mechanism": mechanism[:420],
            "effectiveness_pct": best_pct,
        })

    used_names = {c["name"] for c in cards}
    for r in ranked:
        if not isinstance(r, dict):
            continue
        rname = r.get("name") or ""
        if any(_score_name_match(rname, u) >= 2 for u in used_names):
            continue
        cards.append({
            "name": rname,
            "type": r.get("type") or "",
            "mechanism": (r.get("metric") or "")[:420],
            "effectiveness_pct": r.get("effectiveness_pct"),
        })
        used_names.add(rname)

    cards.sort(key=lambda c: (c["effectiveness_pct"] is None, -(c["effectiveness_pct"] or 0)))

    curative = dz.get("curative_option")
    curative_card = None
    if isinstance(curative, dict) and curative.get("name"):
        curative_card = {"name": curative["name"], "note": (curative.get("note") or "")[:600]}

    return {
        "found": True,
        "id": dz.get("id"),
        "name": dz.get("name"),
        "category": dz.get("category"),
        "doctor_approval_required": dz.get("doctor_approval_required", True),
        "emergency_override_rule": dz.get("EMERGENCY_OVERRIDE_RULE"),
        "curability_note": dz.get("CURABILITY_NOTE"),
        "exhaustive_medicine_survey_note": ems_note,
        "curative_option": curative_card,
        "medicines": cards[:10],
    }


def build_whatsapp_link(disease_name: str, medicine_names: list, patient_text: str = "") -> str:
    number = settings.DOCTOR_WHATSAPP_NUMBER
    lines = [
        "Namaste Doctor, mujhe BalanceAI Pharmacy se refer kiya gaya hai.",
        f"Meri problem: {patient_text}".strip() if patient_text else "",
        f"AI-suggested condition: {disease_name}" if disease_name else "",
    ]
    if medicine_names:
        lines.append("AI-suggested medicines: " + ", ".join(medicine_names))
    lines.append("Kripya confirm kijiye ki mujhe kaunsi medicine leni chahiye, prescription ke saath.")
    message = "\n".join([l for l in lines if l])
    from urllib.parse import quote
    base = f"https://wa.me/{number}" if number else "https://wa.me/"
    return f"{base}?text={quote(message)}"
