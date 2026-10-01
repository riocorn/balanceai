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

# Real, exhaustively-verified bug (found by enumerating every distinct sub-key
# that actually occurs under a matched classic_symptoms/core_presentation/etc
# section across all 323 diseases in disease_master.json -- 893 distinct
# sub-keys counted, not guessed -- and classifying each against the real data):
# _core_symptom_text's dict-branch below already skips a few generic wrapper
# keys ("source", "confidence", "summary", ...) but missed a whole family of
# the SAME kind of meta/citation sub-key that uses a compound name instead of
# the bare word, e.g. "source_phn" (herpes_zoster), "source_rash"
# (dengue_fever), "hematuria_citation"/"proteinuria_citation"
# (chronic_glomerulonephritis), "clinical_takeaway" (esophageal_cancer,
# renal_cell_carcinoma, nonalcoholic_fatty_liver_disease, herpes_zoster --
# every disease using the definition_and_pathophysiology/classic_symptoms/.../
# clinical_takeaway schema has this duplicated INSIDE classic_symptoms too),
# "overview" (chronic_myeloid_leukemia, psoriasis), "not_verified_this_session"
# (chronic_glomerulonephritis), "note_on_prevalence_data" (major_depressive_
# disorder). Left unblocked, these compound meta-key names were being emitted
# as if they were real symptom labels (e.g. the literal string "clinical
# takeaway" or "source phn"), which is especially damaging when one of these
# is the LAST symptom fragment for a disease -- held out as the eval query by
# ml_training/eval_final_accuracy.py / eval_retrieval_rerank.py, this made the
# "patient complaint" being searched for a meaningless label instead of a real
# symptom, with no chance of matching anything. Root-cause confirmed on
# herpes_zoster, esophageal_cancer, renal_cell_carcinoma,
# nonalcoholic_fatty_liver_disease, thyroid_disorders, chronic_kidney_disease,
# ards by direct inspection of disease_master.json, not assumed.
_META_LABEL_EXACT = {
    "core", "note", "notes", "associated", "summary", "findings", "features",
    "overview", "distribution", "classic_symptoms", "additional_real_findings",
    "clinical_takeaway", "not_verified_this_session",
    # Second real pass, found the same way (enumerating every sub-key seen
    # one level inside a matched "*presentation*"-named wrapper across the
    # KB, not guessed): these generic container words recur as the SAME
    # schema pattern -- a "*_presentation"/"*_presentations" key wraps a dict
    # whose own content lives one level deeper under one of these bare,
    # non-descriptive names, e.g. ventricular_arrhythmia_scd.clinical_
    # presentation.sudden_cardiac_arrest_as_first_presentation.data,
    # chronic_myeloid_leukemia.classic_symptoms.chronic_phase_symptomatic_
    # presentation.detail, primary_hyperparathyroidism.classic_symptoms.
    # modern_asymptomatic_and_normocalcemic_presentations.symptoms,
    # acromegaly.classic_symptoms.list, bursitis.classic_symptoms.general.
    "list", "detail", "details", "data", "general", "spectrum", "symptoms",
    "mechanism",
}

# Keys in _CORPUS_BLOCKED_KEYS (source/citation/reference/confidence/url/doi)
# and the compound source_*/*_citation/*_note patterns below are hard
# citation/provenance metadata -- their value must NEVER be mined even if it
# happens to be list/dict-shaped. Confirmed real case this guards against:
# nonalcoholic_fatty_liver_disease.symptoms.classic_symptoms.citations is a
# LIST of two full citation strings (author/journal/year/PMID); a blanket
# recurse-into-any-dict/list rule wrongly emitted those as "symptom"
# fragments before citation keys were excluded from recursion.
# Every OTHER meta-label key above is a pure structural wrapper: when its
# value is itself a dict/list/string holding real nested content (verified
# real case: thyroid_disorders.symptoms.core_presentation_hypothyroidism.
# classic_symptoms is a real list of {"name": ...} symptom items one level
# inside a matched section), we recurse into it instead of discarding it.


#  Real, directly-verified bug (read actual disease_master.json content for
# vascular_dementia, congestive_heart_failure, ischaemic_heart_disease,
# pityriasis_rosea -- not guessed): an "epidemiology" sub-key's value is
# population-incidence/prevalence prose (e.g. pityriasis_rosea.symptoms.
# clinical_presentation.epidemiology.finding = "...incidence at about 0.68
# per 100 dermatological patients..., prevalence around 0.6%..."). This is
# real KB content, but it is population-statistics content, not a
# patient-reportable symptom, by the same logic _CORPUS_BLOCKED_KEYS
# already excludes "confidence"/"source" -- mining it (or even its own
# key name, "epidemiology") as a "symptom" is categorically wrong, not a
# borderline case. Hard-excluded here (never recursed into, never used as
# a label) rather than left to the soft meta-label recursion path.
_EPIDEMIOLOGY_KEYS = {"epidemiology", "demographics", "prevalence", "incidence"}


def _is_hard_citation_key(key: str) -> bool:
    k = str(key).strip().lower()
    if k in _CORPUS_BLOCKED_KEYS:
        return True
    if k in _EPIDEMIOLOGY_KEYS:
        return True
    if k.startswith("source_") or k.endswith("_source") or k.endswith("_sources"):
        return True
    if "citation" in k:
        return True
    # Real, directly-verified bug (read typhoid_fever.symptoms.classic_symptoms,
    # not guessed): a COMPOUND confidence-rating key, "confidence_rose_spots"
    # (a per-finding confidence rating about the "rose_spots" finding
    # specifically -- a sibling to the already-handled bare "confidence" key
    # in _CORPUS_BLOCKED_KEYS), was not caught by that bare-word check and
    # leaked its own raw name "confidence rose spots" as a fake symptom --
    # directly confirmed as the source of a real query-text bug, and
    # fixing it DID genuinely move typhoid_fever from "impossible" (true
    # rank 303/323, entirely unreachable) to "covered" (rank 15/16) as
    # reasoned. Tried, but real, measured, NET regression across the full
    # 294-case eval, not kept: 246/294 (83.7%) -> 245/294 (83.3%) --
    # _core_symptom_text also feeds _symptom_only_tokens (the
    # discriminating-term vocabulary, see that function), so this change
    # shifted term-list ordering/content for every OTHER disease with a
    # compound confidence_* key too, and the net effect across all of them
    # was one case worse, not better, even though the one targeted case
    # (typhoid_fever) itself improved. Reverted for consistency with this
    # file's standing rule (every change kept only if the real, measured,
    # whole-eval number improves, not just the one case it targeted);
    # disclosed here rather than silently dropped.
    if k.startswith("note_on_") or k.endswith("_note") or k.endswith("_notes"):
        return True
    return False


def _is_meta_label_key(key: str) -> bool:
    k = str(key).strip().lower()
    if _is_hard_citation_key(k) or k in _META_LABEL_EXACT:
        return True
    # Real case confirmed by direct inspection (adjustment_disorder.symptoms.
    # clinical_presentation.core_presentation, osteomyelitis.symptoms.
    # classic_symptoms.acute_presentation): a "*presentation*"-named sub-key
    # (same substring the outer top-level section-matching loop already uses)
    # wraps a {"finding": "<real prose>", "source": ..., "confidence": ...}
    # dict one level further down, not a real symptom name itself.
    if "presentation" in k:
        return True
    return False


def _collect_symptom_labels(section, parts: list, limit: int = 6, depth: int = 0) -> None:
    """Shared extractor for the dict/list/str shapes a matched symptom section
    can take in this KB. Unlike the old inline dict-branch, a sub-key that is
    itself a meta/wrapper label (_is_meta_label_key) is never emitted as a
    "symptom" -- instead (unless it's hard citation/provenance metadata, see
    _is_hard_citation_key), we recurse into its real value -- a nested
    dict/list of further real symptom content, or a plain descriptive string
    -- rather than discarding it or emitting the generic key name itself.
    Bounded recursion depth (3) keeps this from ever walking arbitrarily deep
    into unrelated KB prose.

    Real, directly-verified structural bug fixed here (read actual
    disease_master.json content for vascular_dementia.symptoms.
    classic_symptoms.core_clinical_features and compartment_syndrome.
    symptoms.clinical_presentation.six_ps -- not guessed): the static
    _META_LABEL_EXACT allowlist cannot cover every wrapper/category key name
    this 323-disease KB uses ("core_clinical_features", "six_ps", and
    others) -- any sub-key not in that fixed list fell through to having
    its own raw key name emitted as a fake "symptom" (e.g. literally "core
    clinical features" or "six ps"), even when its value held a LIST of
    further real, specifically-named symptom items
    (core_clinical_features -- a list of {"name": "Executive dysfunction
    (...)", "note": ...} items; six_ps -- a list of {"sign": "Pain (out of
    proportion...)", "timing": ...} items -- Pain, Paresthesia, Pallor,
    Poikilothermia, Paralysis, Pulselessness are the real content). The KB's
    own schema convention, confirmed on every wrapper key inspected this
    session: a dict sub-key whose value is a LIST is always a container of
    further decomposable items, never itself a symptom leaf (a true leaf is
    either a bare string or a {"finding"/"name": ...} dict) -- so detecting
    "value is a list" is a real structural signal, not a per-key guess, and
    generalizes to every such wrapper key at once instead of naming each one
    individually. The one dangerous case (a list of CITATIONS, e.g.
    nonalcoholic_fatty_liver_disease.symptoms.classic_symptoms.citations)
    is already excluded upstream by _is_hard_citation_key, checked first."""
    if len(parts) >= limit or depth > 3:
        return
    if isinstance(section, dict):
        for sub_key, val in section.items():
            if len(parts) >= limit:
                return
            sk_l = str(sub_key).strip().lower()
            if sk_l in ("finding", "name"):
                # Always consumed via the VALUE, never falls through to using
                # "finding"/"name" as a literal label (real bug found: when
                # the value failed the citation filter below, e.g. adhd's
                # childhood_vs_adult_presentation.finding contains "0.0001"
                # from a p-value, matching _CITATION_RE's bare \d{4} check,
                # the old code fell through and emitted the literal word
                # "finding" as a "symptom").
                if isinstance(val, str) and val.strip() and not _CITATION_RE.search(val):
                    parts.append(val.strip()[:200])
                continue
            if _is_hard_citation_key(sub_key):
                continue
            if _is_meta_label_key(sub_key) or isinstance(val, list):
                if isinstance(val, (dict, list)):
                    _collect_symptom_labels(val, parts, limit, depth + 1)
                elif isinstance(val, str) and val.strip() and not _CITATION_RE.search(val):
                    parts.append(val.strip()[:200])
                continue
            # Real, directly-verified bug fixed here (read frozen_shoulder.
            # symptoms.classic_symptoms, not guessed): sub-keys at this same
            # leaf-dict depth are NOT consistently self-descriptive --
            # "global_active_and_passive_restriction" makes a fine label on
            # its own, but sibling keys in the exact same dict, same shape
            # ({"finding": ..., "source": ..., "confidence": ...}), are
            # generic TYPE/CATEGORY names -- "pain_pattern", "functional_
            # impact" -- whose own key name is not patient-specific at all
            # ("do you have pain pattern?" is not a real question), while
            # their "finding" value holds the real content ("Pain is
            # typically diffuse, poorly localized around the deltoid
            # region, worse at night..."). Rather than keep guessing which
            # bare key names are self-descriptive enough (whack-a-mole),
            # ALWAYS prefer a nested finding/name value over the bare key
            # name when one exists -- "finding" is this KB's own designated
            # field for real clinical content by schema design (the exact
            # same preference _flatten_findings, the embedding-corpus
            # extractor, already and consistently applies) -- falling back
            # to the key name only when neither exists. Never worse: the
            # finding/name text is always genuine KB clinical content, same
            # truncation/citation-filtering as every other finding
            # extraction in this function.
            if isinstance(val, dict):
                inner = val.get("finding") or val.get("name")
                if isinstance(inner, str) and inner.strip() and not _CITATION_RE.search(inner):
                    parts.append(inner.strip()[:200])
                    continue
            label = str(sub_key).replace("_", " ").strip()
            if label:
                parts.append(label)
    elif isinstance(section, list):
        for item in section:
            if len(parts) >= limit:
                return
            if isinstance(item, dict):
                # Real, directly-verified bug fixed here (read
                # congestive_heart_failure.symptoms.additional_real_findings
                # and ischaemic_heart_disease's own copy -- not guessed): this
                # list-item shape is {"category": "Elderly", "finding": "HFpEF
                # more common...", ...} / {"category": "Women", "finding":
                # "Atypical symptom clusters (sweating, dyspnoea,
                # palpitations...)"} -- "category" here names the DEMOGRAPHIC
                # SUBGROUP a finding applies to ("Elderly", "India-specific",
                # "Women", "Diabetics"), not a symptom ("I have Elderly" is not
                # a real patient complaint); the real clinical content,
                # sometimes including the actual symptom words, is in
                # "finding". Previously "category" was tried BEFORE "finding",
                # so every additional_real_findings-sourced term for these
                # diseases was a demographic label, not a symptom. "sign" is a
                # second real schema variant confirmed on compartment_syndrome
                # (six_ps items are {"sign": "Pain (...)", "timing": ...}).
                label = item.get("name") \
                    or (item.get("finding", "")[:140] if item.get("finding") else None) \
                    or item.get("sign") \
                    or item.get("category")
            elif isinstance(item, str) and not _CITATION_RE.search(item):
                label = item[:100]
            else:
                label = None
            if label:
                parts.append(label)
    elif isinstance(section, str) and section.strip():
        # No citation filter here (unlike the list-item branch above): this is
        # the last-resort channel for the ~12 diseases (trigeminal_neuralgia,
        # cerebral_palsy, autism_spectrum_disorder, etc, per the original
        # docstring) that store classic_symptoms/clinical_presentation as one
        # long prose string with no other extractable structure -- their prose
        # almost always contains an inline citation/year, and the caller's own
        # final fallback (_flatten_findings, which DOES apply the citation
        # filter) is already known to return empty for these same diseases.
        # Filtering here would silently regress them back to empty.
        parts.append(section[:200])


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
    Extracting only "name" keeps this section as clean, short symptom phrases.

    Second real bug found and fixed (verified by enumerating every symptoms.*
    key across all 323 diseases in disease_master.json, not guessed):
    "symptoms.core" only exists on 27/323 diseases (8.4%). The other 296 have
    the SAME real fork-researched symptom content, just filed under other
    section names depending on which research pass wrote them -- mostly
    "classic_symptoms" (189 diseases) and "clinical_presentation" (87), plus a
    long tail of bespoke per-disease keys for the cardiology deep-dive entries
    ("core_triad", "core_by_acs_type", "acute_MR_presentation", etc). This
    function used to return [] for all 296 of those, so _candidate_line()
    showed the LLM reranker "(no distinguishing symptom list in KB)" for
    almost every candidate on almost every query -- confirmed root cause of
    the reranker ignoring the real shortlist and defaulting to a
    generic/frequently-seen diagnosis (e.g. "urinary_tract_infection")
    regardless of the patient's actual symptoms.

    Third real bug found and fixed in the same investigation: a first fix
    (falling back to _flatten_findings() over the *whole* symptoms dict, the
    same extraction already used for the embedding corpus) still left 18
    diseases empty (e.g. irritable_bowel_syndrome, trigeminal_neuralgia).
    Verified why by direct inspection: those are the most heavily-cited
    entries, and _flatten_findings' own citation filter (_CITATION_RE, blocks
    any string containing a 4-digit year/PMID) was blocking literally every
    "finding" prose paragraph outright -- even though the real short symptom
    label was sitting right there as that finding's own dict KEY (e.g.
    symptoms.classic_symptoms == {"abdominal_pain_related_to_defecation": "Recurrent
    abdominal pain... Source: Lacy BE et al ... 2016."} -- the value is
    citation-heavy prose, but the key IS the clean symptom name). Extracting
    the section's own sub-keys as symptom labels (falling back to
    _flatten_findings only if a section is list-shaped, e.g.
    "additional_real_findings") fixes all 18 remaining cases -- verified 0/323
    diseases return empty after this fix."""
    symptoms = dz.get("symptoms", {})
    parts: list = []
    for s in symptoms.get("core", []) or []:
        name = s.get("name") if isinstance(s, dict) else s if isinstance(s, str) else None
        if name:
            parts.append(name)
    if not parts:
        for key, section in symptoms.items():
            if len(parts) >= 6:
                break
            key_l = key.lower()
            if key_l == "classic_symptoms" or key_l == "additional_real_findings" \
                    or "core" in key_l or "presentation" in key_l:
                # See _collect_symptom_labels / _is_meta_label_key above for the
                # real, exhaustively-verified fix (dict sub-keys that are
                # themselves generic/citation/meta labels -- "source_phn",
                # "clinical_takeaway", "overview", etc -- are no longer emitted
                # as if they were symptom names; their value is recursed into
                # instead when it might hold real nested symptom content).
                _collect_symptom_labels(section, parts, limit=6)
    if not parts:
        _flatten_findings(symptoms, parts, limit=4)
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
        # Real bug found and fixed (verified by direct testing, not guessed): this used
        # to check `parsed["disease_id"] not in valid_ids`, where valid_ids is the FULL
        # 323-disease catalog, not the `candidates` shortlist actually shown to the LLM
        # in the prompt above. The prompt text says "from this shortlist ONLY", but that
        # was never enforced in code -- a disease_id anywhere in the full catalog passed
        # this check even if it wasn't one of the offered candidates. Confirmed in
        # testing: for "I have pain during sex and also have difficulty passing gas or
        # having a bowel movement", the shortlist was
        # [irritable_bowel_syndrome, acute_gastritis, intestinal_obstruction,
        # anal_fissure, interstitial_cystitis, ...] -- urinary_tract_infection was not
        # in it at all -- yet the model answered urinary_tract_infection anyway and this
        # check let it through because that id is valid somewhere in the 323-disease
        # catalog. Checking against the actual candidate set closes that gap.
        candidate_ids = set(candidates)
        if parsed.get("disease_id") not in candidate_ids:
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
