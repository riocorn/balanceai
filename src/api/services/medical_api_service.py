import json
import os
import re

import numpy as np
import requests

from core.config import settings

_DISEASE_CACHE = {"mtime": None, "diseases": None, "corpus_ids": None, "corpus_matrix": None}
_MEDICINE_CACHE = {"mtime": None, "medicines": None, "name_rows": None}
_EMBED_MODEL = {"instance": None, "name": None}


def _norm_tokens(text: str) -> set:
    text = re.sub(r"[^a-z0-9]+", " ", (text or "").lower())
    return {w for w in text.split() if len(w) > 2}


def _norm_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


# Same real, observed bug and root-cause fix as pharmacy_service.py's
# _flatten_findings (found by tracing a real 44.4%-accuracy eval run): unfiltered
# flatten pulls citation/reference/methodology text into the embedding corpus,
# diluting/crowding out real symptom text under the item-count limit.
_CORPUS_BLOCKED_KEYS = {
    "source", "sources", "citation", "citations", "reference", "references",
    "confidence", "url", "doi",
}
_CITATION_RE = re.compile(r"\d{4}|et al\b", re.IGNORECASE)


def _flatten_strings(node, out: list, limit: int = 8, key=None) -> None:
    if len(out) >= limit:
        return
    if key is not None and str(key).lower() in _CORPUS_BLOCKED_KEYS:
        return
    if isinstance(node, str):
        if len(node) > 20 and not _CITATION_RE.search(node):
            out.append(node)
    elif isinstance(node, dict):
        for k, v in node.items():
            _flatten_strings(v, out, limit, key=k)
            if len(out) >= limit:
                return
    elif isinstance(node, list):
        for v in node:
            _flatten_strings(v, out, limit, key=key)
            if len(out) >= limit:
                return


# NOT the same broad key list as medical_understanding.py's _extract_findings --
# tried that first and measured a real regression. Root cause, verified by printing
# actual corpus text: "specific_diagnostic_signs"/"red_flags" hold physician-only
# exam findings and risk-stratification prose that never lexically/semantically
# resembles patient free text, so embedding cosine similarity against it hurts
# retrieval. medical_understanding.py gets away with those sections because it also
# applies a lay-term synonym bridge on top, which this module does not have.
# Keeping only "core" -- verified clean, patient-relevant phrasing.
_SYMPTOM_SECTION_KEYS = ("core",)


def _core_symptom_text(dz: dict) -> list:
    """Same real bug/fix as pharmacy_service.py's _core_symptom_text: each item
    under symptoms.core is {"name": "<short symptom>", "note": "<long paragraph>"},
    and the generic flatten was pulling the "note" prose in too. Only "name" is
    used here to keep this section as clean, short symptom phrases."""
    symptoms = dz.get("symptoms", {})
    parts: list = []
    for s in symptoms.get("core", []) or []:
        name = s.get("name") if isinstance(s, dict) else s if isinstance(s, str) else None
        if name:
            parts.append(name)
    return parts


def _embedding_model():
    if _EMBED_MODEL["instance"] is not None and _EMBED_MODEL["name"] == settings.EMBEDDING_MODEL:
        return _EMBED_MODEL["instance"]
    try:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL["instance"] = SentenceTransformer(settings.EMBEDDING_MODEL)
        _EMBED_MODEL["name"] = settings.EMBEDDING_MODEL
        return _EMBED_MODEL["instance"]
    except Exception:
        return None


def load_diseases() -> dict:
    path = settings.DISEASE_MASTER_PATH
    mtime = os.path.getmtime(path)
    if _DISEASE_CACHE["mtime"] == mtime and _DISEASE_CACHE["diseases"] is not None:
        return _DISEASE_CACHE["diseases"]

    diseases = json.load(open(path, encoding="utf-8"))["diseases"]
    _DISEASE_CACHE.update({"mtime": mtime, "diseases": diseases, "corpus_ids": None, "corpus_matrix": None})
    return diseases


def _disease_embeddings():
    diseases = load_diseases()
    if _DISEASE_CACHE["corpus_matrix"] is not None:
        return _DISEASE_CACHE["corpus_ids"], _DISEASE_CACHE["corpus_matrix"]

    model = _embedding_model()
    if model is None:
        return None, None

    ids = list(diseases.keys())
    cache_file = settings.DISEASE_MASTER_PATH + ".medapi_embeddings.npy"
    ids_file = cache_file + ".ids.json"
    mtime = _DISEASE_CACHE["mtime"]
    if os.path.exists(cache_file) and os.path.exists(ids_file):
        if json.load(open(ids_file)) == ids and os.path.getmtime(cache_file) >= mtime:
            matrix = np.load(cache_file)
            _DISEASE_CACHE["corpus_ids"], _DISEASE_CACHE["corpus_matrix"] = ids, matrix
            return ids, matrix

    texts = []
    for did in ids:
        dz = diseases[did]
        core = _core_symptom_text(dz)
        findings = []
        _flatten_strings(dz.get("symptoms", {}), findings, limit=8)
        texts.append(" ".join([dz.get("name", ""), dz.get("category", "")] + core + findings)[:1500])

    matrix = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    np.save(cache_file, matrix)
    json.dump(ids, open(ids_file, "w"))
    _DISEASE_CACHE["corpus_ids"], _DISEASE_CACHE["corpus_matrix"] = ids, matrix
    return ids, matrix


def load_medicines() -> dict:
    path = settings.MEDICINE_DETAILS_PATH
    mtime = os.path.getmtime(path)
    if _MEDICINE_CACHE["mtime"] == mtime and _MEDICINE_CACHE["medicines"] is not None:
        return _MEDICINE_CACHE["medicines"]

    medicines = json.load(open(path, encoding="utf-8"))["medicines"]
    rows = []
    for key, v in medicines.items():
        status = (v.get("research_status") or "").split(" ")[0].split("-")[0].strip()
        if status == "not_found":
            continue
        rows.append({"key": key, "norm": _norm_text(v.get("name", key))})
    _MEDICINE_CACHE.update({"mtime": mtime, "medicines": medicines, "name_rows": rows})
    return medicines


def _find_medicine_by_name(name: str):
    medicines = load_medicines()
    target = _norm_tokens(name)
    if not target:
        return None
    best, best_score = None, 0
    for row in _MEDICINE_CACHE["name_rows"]:
        row_tokens = set(row["norm"].split())
        score = len(target & row_tokens)
        if score > best_score:
            best_score, best = score, row["key"]
    if best_score < 1:
        return None
    return medicines[best]


def _ollama(prompt: str, timeout: int = 60, model: str = None) -> dict:
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


RED_FLAG_TERMS = [
    "chest pain", "seene mein dard", "chest mein dard", "saans nahi aa rahi",
    "breathing difficulty", "can't breathe", "unconscious", "behosh",
    "seizure", "daura", "severe bleeding", "bahut khoon", "stroke",
    "face drooping", "chehra tedha", "suicidal", "khudkushi",
    "poisoning", "zeher", "anaphylaxis", "severe allergic reaction",
    "coughing blood", "khoon ki ulti", "vomiting blood",
]


def _hard_emergency(text: str) -> bool:
    t = text.lower()
    return any(term in t for term in RED_FLAG_TERMS)


def _shortlist_diseases(text: str, top_n: int) -> list:
    model = _embedding_model()
    ids, matrix = _disease_embeddings()
    if model is None or ids is None:
        return []
    q = model.encode([text], normalize_embeddings=True)[0]
    sims = matrix @ q
    ranked = sorted(zip(ids, sims), key=lambda x: -x[1])[:top_n]
    return [did for did, _ in ranked]


def _identify_disease(patient_text: str) -> dict:
    """
    Our own understanding layer: a local model (never Claude/an external API)
    only ever picks a disease_id from a real, KB-derived shortlist, or rewrites
    an already-real fact into plain language. It is never allowed to state a
    medicine name, dose or effectiveness number itself — those always come
    straight from disease_master.json, so a hallucinated fact can't reach the
    patient even if the language model misfires.
    """
    diseases = load_diseases()

    shortlist = _shortlist_diseases(patient_text, top_n=20)
    if not shortlist:
        shortlist = list(diseases.keys())[:20]

    # Same real bug/fix as pharmacy_service.py's _candidate_line: showing only
    # id|name|category gives the model nothing to discriminate close differentials
    # on, and measurably collapses several distinct diseases onto whichever shares
    # a broad downstream syndrome (e.g. congestive_heart_failure).
    def _candidate_line(did: str) -> str:
        dz = diseases[did]
        terms = _core_symptom_text(dz)[:4]
        snippet = "; ".join(t[:100] for t in terms) if terms else "(no distinguishing symptom list in KB)"
        return f"{did} | {dz.get('name', did)} | {dz.get('category', '')} | key symptoms: {snippet}"

    catalog = "\n".join(_candidate_line(did) for did in shortlist)
    prompt = f"""A patient described their health problem below, in whatever language or style they used.

Patient's own words: "{patient_text}"

Pick the single closest-matching disease_id from this list ONLY. Never invent an id
outside this list, and never mention a medicine name or a percentage yourself.
Compare the patient's stated symptoms against each candidate's own "key symptoms" below.
Do NOT default to a broad/generic diagnosis just because it can result from many causes -- if a
more SPECIFIC candidate's key symptoms match what the patient actually said at least as well,
prefer the specific candidate over the generic one:

{catalog}

Reply with ONLY JSON: {{"disease_id": "<id from the list above, or null>", "confidence": <0.0-1.0>,
"understood_as": "<one short sentence, in the same language/style as the patient, saying what you understood>"}}"""

    try:
        parsed = _ollama(prompt, timeout=60, model=settings.OLLAMA_REASONING_MODEL)
        did = parsed.get("disease_id")
        if did not in diseases:
            did = shortlist[0]
            parsed["confidence"] = min(parsed.get("confidence", 0.4), 0.4)
        parsed["disease_id"] = did
        return parsed
    except Exception:
        did = shortlist[0]
        return {
            "disease_id": did,
            "confidence": 0.3,
            "understood_as": f"Best-guess match based on your description: {diseases[did].get('name', did)}.",
        }


def _ranked_medicine_names(disease: dict) -> list:
    table = disease.get("effectiveness_ranked_table")
    if isinstance(table, dict):
        rows = table.get("ranked_high_to_low", [])
    elif isinstance(table, list):
        rows = table
    else:
        rows = []
    out = []
    for r in rows:
        if isinstance(r, dict) and r.get("name"):
            out.append({"name": r["name"], "effectiveness_pct": r.get("effectiveness_pct"), "source": r.get("source", "")})
    return out


def _simplify_mechanism(medicine_name: str, real_facts: str) -> str:
    """Rewrites already-real, sourced facts into plain language. Never adds a
    fact that isn't in real_facts -- if real_facts is empty, returns a plain
    'not documented' line instead of asking the model to invent one."""
    if not real_facts.strip():
        return "Iska mechanism is dataset mein detail mein documented nahi hai."
    prompt = f"""Explain, in 1-2 short simple sentences a non-medical person can understand,
how "{medicine_name}" helps the body -- using ONLY the real facts given below.
Do not add any fact, number, or claim that is not stated in these facts.

Real facts: {real_facts[:900]}

Reply with ONLY JSON: {{"simple_explanation": "..."}}"""
    try:
        out = _ollama(prompt, timeout=45)
        text = out.get("simple_explanation", "").strip()
        return text or real_facts[:300]
    except Exception:
        return real_facts[:300]


def answer_patient_query(patient_text: str) -> dict:
    patient_text = patient_text.strip()
    identification = _identify_disease(patient_text)
    disease_id = identification.get("disease_id")
    diseases = load_diseases()
    disease = diseases.get(disease_id, {})

    ranked = _ranked_medicine_names(disease)
    medicines = []
    for entry in ranked[:10]:
        med_record = _find_medicine_by_name(entry["name"])
        if med_record:
            real_facts = " ".join(filter(None, [
                med_record.get("dosage_administration"),
                (med_record.get("fact_box") or {}).get("action_class"),
            ]))
            sources = med_record.get("sources") or ([entry["source"]] if entry["source"] else [])
        else:
            real_facts = entry["source"]
            sources = [entry["source"]] if entry["source"] else []

        medicines.append({
            "name": entry["name"],
            "effectiveness_pct": entry["effectiveness_pct"],
            "simple_explanation": _simplify_mechanism(entry["name"], real_facts),
            "sources": sources,
        })

    return {
        "disease_id": disease_id,
        "disease_name": disease.get("name"),
        "understood_as": identification.get("understood_as", ""),
        "confidence": identification.get("confidence"),
        "medicines": medicines,
        "doctor_verification_required": True,
        "disclaimer": (
            "Yeh AI-suggested information hai, real medical research (FDA/DailyMed/PubMed) se li gayi hai "
            "lekin ek doctor ka confirmation zaroori hai kisi bhi medicine lene se pehle."
        ),
        "hard_emergency_flag": _hard_emergency(patient_text),
        "emergency_override_rule": disease.get("EMERGENCY_OVERRIDE_RULE"),
    }
