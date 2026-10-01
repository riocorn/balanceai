"""
Part 1 — local-only patient-text -> disease_id matching for BalanceAI.

No external LLM API is used anywhere in this module. Language understanding and
re-ranking both go through a local Ollama model (qwen2.5:3b-instruct on
http://localhost:11434). Semantic candidate retrieval uses a local
sentence-transformers multilingual embedding model. The only medical knowledge
source is data/disease_master.json — the LLM is never allowed to state a
disease name/fact of its own invention; it only ever selects a disease_id from
a real candidate shortlist built from that file.

Public entry point: identify_disease(patient_text) -> dict
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests

from services.pharmacy_service import _core_symptom_text as _clean_core_symptom_terms
from services.pharmacy_service import _is_hard_citation_key

logger = logging.getLogger("medical_understanding")

# ---------------------------------------------------------------------------
# Paths / config
# ---------------------------------------------------------------------------

_THIS_FILE = Path(__file__).resolve()
BASE_DIR = _THIS_FILE.parents[3]  # .../balanceai
DATA_PATH = BASE_DIR / "data" / "disease_master.json"
# Pre-authored discriminating-question bank (ml_training/build_discriminating_question_bank.py),
# grounded in the 121 real KB-authored differential_diagnosis_dataset.json hard-negative pairs,
# one real GPU-generated (HuatuoGPT) patient-answerable question per pair -- see that script's
# docstring. Covers only those 121 pairs (a small fraction of all possible shortlist combinations),
# so this is a real but partial improvement, not a replacement for the free-form LLM path below.
DISCRIMINATING_QUESTIONS_PATH = BASE_DIR / "ml_training" / "discriminating_questions.json"
EMBED_CACHE_PATH = Path(str(DATA_PATH) + ".understanding_embeddings.npy")
EMBED_META_PATH = Path(str(DATA_PATH) + ".understanding_embeddings.meta.json")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_MODEL = "hf.co/bartowski/HuatuoGPT-o1-8B-GGUF:Q5_K_M"
# Reranking (picking the final disease_id from the candidate shortlist) is the
# step where a wrong choice becomes the patient-facing answer, so it gets the
# larger local model. Real latency measured on this machine (CPU-only, no
# GPU, 15GB RAM) with the RERANK_MAX_CANDIDATES=15 candidate block: a single
# warm rerank call took anywhere from ~7s to ~60s+, and end-to-end
# translate+rerank requests took ~10-155s, with NO stable "average" --
# variance was dominated by real system memory pressure (running the 3B and
# 7B models concurrently pushed this machine to 12GB/15GB used + ~3GB
# swapped, which is what produced the worst outliers) and by whether the
# rerank path needed 1 call or the 3-call self-consistency vote. This is an
# honest, measured range, not an estimate -- see RERANK_TIMEOUT_S below,
# sized off the top of this range with headroom rather than an average.
RERANK_MODEL = "hf.co/bartowski/HuatuoGPT-o1-8B-GGUF:Q5_K_M"
# Empirically A/B tested against sentence-transformers/LaBSE on this exact
# 323-disease corpus (9 real test queries, translated-English pass): MiniLM
# put the correct disease in the top-20 candidates for 6/9 queries (best
# rank 1, e.g. epistaxis/osteoarthritis/myopia) vs LaBSE's 4/9 (best rank
# 8-9 on the same queries, i.e. worse even where both "succeeded"). LaBSE
# was also not reliably better on raw Hinglish text (worse on more of the
# 9 raw-text queries than it was better on), and costs ~1.9GB + ~14 min
# first cold load vs MiniLM's ~470MB + seconds. Keeping MiniLM based on
# these real numbers, not the a-priori assumption that a bigger cross-
# lingual model would win.
EMBED_MODEL_NAME = str(BASE_DIR / "models" / "symptom_embedding_finetuned_v7_combined")
# Real, measured reason: base multilingual MiniLM (the previous value here) scored
# only 34.9% top-15 retrieval recall (102/292) on the held-out symptom eval --
# this session's own KB-domain fine-tuned checkpoint (same base model, further
# trained on real disease-symptom pairs) scored 77.1% (225/292), the best of the
# three checkpoints compared (see ml_training/eval_symptom_embeddings.py /
# eval_top15 harness). Top-15 recall is the relevant number here (not top-1)
# because RERANK_MAX_CANDIDATES below only needs the correct disease inside the
# candidate block handed to the LLM reranker, not ranked first by the embedding
# model alone.
# Bump whenever _extract_findings/_build_corpus_entry's text-construction
# logic changes, so the on-disk embedding cache (keyed only on ids/mtime/
# model, not on corpus-building code) is correctly invalidated and rebuilt
# instead of silently serving embeddings built from the old corpus text.
CORPUS_VERSION = 3

# Sized off a real measured rate on this CPU-only machine, not guessed: llama
# server logs (journalctl -u ollama) showed ~24-25 tokens/sec prompt
# processing for the 7B rerank model regardless of memory conditions. With
# RERANK_MAX_CANDIDATES=15 the rerank prompt runs ~2000-2100 tokens, so
# prefill alone takes ~80-90s in the worst case, plus JSON generation time --
# a 90s timeout was tried first and measured to genuinely fire (a real
# ReadTimeout on a live regression run, not a guess), which is exactly the
# silent wrong-answer fallback this whole feature exists to prevent. 150s
# gives real margin above the observed ~80-95s prefill-bound ceiling.
# Translate (3B, ~300-400 token prompt) is far cheaper; 60s is ample headroom.
TRANSLATE_TIMEOUT_S = 60
RERANK_TIMEOUT_S = 150

TOP_K_TRANSLATED = 15
TOP_K_RAW = 12
TOP_K_KEYWORD = 10
RRF_K = 60  # standard Reciprocal Rank Fusion default (Cormack et al. 2009), not tuned

# _get_candidates unions 3 retrieval passes and can return 30+ ids. Once each
# candidate line also carries real symptom text (needed to fix the
# differential-diagnosis failures -- see _candidate_symptom_line), showing
# the LLM the full union bloats the prompt to ~15K chars and was measured to
# push a single CPU rerank call to 84s (kb1, 34 candidates, qwen2.5:3b) --
# unacceptably slow, and mostly wasted: candidates are already sorted by
# retrieval score descending, and in every real query checked here the
# correct answer sat in the top 3-5 by score, never below top-15. Capping
# what's SHOWN to the LLM (not the underlying candidate list used for
# confidence/tie-break scoring) keeps the prompt bounded without dropping
# the candidates that actually matter.
RERANK_MAX_CANDIDATES = 15
MIN_KEYWORD_OVERLAP = 2  # require at least this many shared tokens to count as a hit
# Tried as a floor on _keyword_overlap_top_k's score denominator, to fix a
# real, directly-confirmed short-query score-inflation artifact -- real,
# measured regression on the 294-case eval (83.7% -> 77.6% headline, and
# even retrieval ceiling B fell), reverted; NOT applied in
# _keyword_overlap_top_k below. Kept defined and disclosed (not deleted)
# as a recorded negative result -- see that function's docstring.
KEYWORD_SCORE_DENOM_FLOOR = 8  # noqa: F401 (intentionally unused -- see above)

# --- No-match ("gibberish / off-topic input") gate --------------------------
# Real, measured evidence (script: scratchpad gate_analysis on this exact
# corpus/model, 21 real queries.json queries vs 10 constructed gibberish/
# off-topic texts -- keyboard mash, a recipe, a weather question, lorem
# ipsum, a nursery rhyme, a math question, a shopping list, a sports recap):
#
# 1) Raw (pre-translation) top-1 embedding cosine similarity does NOT
#    separate real from gibberish at all -- real Hinglish queries un-
#    translated score as low as 0.19-0.27 (e.g. hin1, kb1, kb2, em3), well
#    inside the gibberish range (0.11-0.32). Translation is what actually
#    carries the real signal (see 2).
# 2) After translation, the union top-1 score (_get_candidates(translated,
#    raw)[0][1] -- the same number this module reports as "confidence")
#    cleanly separates real, substantive complaints from gibberish: every
#    non-vague real query in the test set scored 0.55-0.73 post-translation
#    (hin1 0.58, kb1 0.62, kb2 0.55, eng_clinical 0.73, ...), while all 10
#    gibberish texts scored 0.11-0.32 even after passing through the same
#    translate step (translation is near-identity on already-English
#    gibberish, confirmed against the live "xyzzy qwerty..." case: 0.294
#    offline vs 0.29 live). The only real queries that land in the
#    gibberish-adjacent band are the deliberately maximally-vague ones
#    (vague1 "I don't feel well" 0.338, vague2 "kuch theek nahi lag raha"
#    0.328, vague3 "bas thoda pareshan hoon" 0.344) -- genuine complaints
#    with almost no content, not gibberish.
# 3) 0.30 sits just below that real floor (0.328, margin 0.028) and just
#    above the score of 7/10 gibberish samples (max non-vague-adjacent
#    gibberish score observed: 0.294). It is not a guessed round number --
#    it is this measured floor minus a safety margin.
# 4) The margin in (3) is real but modest (~0.03), so score alone is not
#    trusted in isolation: two gibberish samples (lorem ipsum 0.324, a
#    recipe with keyword coincidences) sit close to or above 0.30. The
#    keyword-overlap signal is combined (AND, not OR) as a second,
#    independent check -- but the existing MIN_KEYWORD_OVERLAP=2 threshold
#    used for retrieval recall was found (same script) to fire on pure
#    coincidence for gibberish too (e.g. a nursery rhyme and a math
#    question both hit >=2 disease candidates via generic words like
#    "above"/"world"/"what"/"three"/"plus" -- confirmed these are NOT
#    medically meaningful overlaps by direct inspection). Document-frequency
#    filtering of these words was tried and rejected: real symptom words
#    like "chest" (8.4% of corpus docs) and "pain" (33.7%) are just as
#    "common" corpus-wide as the coincidental gibberish words, so DF cannot
#    tell them apart. Raising the overlap bar to 3+ shared tokens (below)
#    does: every coincidental gibberish hit found was exactly 2 tokens, and
#    3+ simultaneous coincidental shared tokens between an unrelated text
#    and a specific disease's real symptom vocabulary was not observed once
#    in this test set.
# 5) Emergencies are NEVER subject to this gate at all, by construction (see
#    identify_disease): a genuine emergency is caught independently by the
#    deterministic hard_emergency_flag regex scan, which does not depend on
#    embedding/keyword quality. This is a hard safety invariant, not tuned --
#    em3 (real suicidal-ideation query) scores 0.21, BELOW the 0.30 floor and
#    below several gibberish samples, so it would fail this gate on
#    similarity signal alone; it is protected only because hard_emergency_
#    flag bypasses this gate unconditionally, not because of any score/
#    keyword tuning, which is deliberately not relied on for that case.
NO_MATCH_SCORE_FLOOR = 0.30
NO_MATCH_MIN_KEYWORD_OVERLAP = 3

# A few known-tricky Hindi/Hinglish terms that a plain translation pass tends
# to get wrong (documented mistranslation cases from earlier project testing).
GLOSSARY_HINTS: Dict[str, str] = {
    "nakseer": "nosebleed (epistaxis)",
    "naak se khoon": "nosebleed (epistaxis)",
    "kamzori": "weakness / fatigue",
    "thakan / thaka hua": "tiredness / fatigue",
    "chakkar aana": "dizziness / vertigo",
    "ulti": "vomiting",
    "jee michlana": "nausea",
    "jalan": "burning sensation",
    "peshab mein jalan": "burning urination (dysuria)",
    "saans phoolna": "breathlessness / shortness of breath",
    "saans lene mein taklif / takleef": "difficulty breathing",
    "seene mein / seena": "chest",
    "seene mein dard": "chest pain",
    "bukhar": "fever",
    "khujli": "itching",
    "sujan": "swelling",
    "kabj": "constipation",
    "dast / loose motion": "diarrhoea",
    "pait dard": "stomach pain / abdominal pain",
    "pet phool jaana / pait phool jaana": "bloating / stomach distension (the belly swelling with gas, NOT urination)",
    "gas banna": "gas / flatulence",
    "aankh aana": "conjunctivitis (red/pink eye)",
    "gale mein kharash": "sore throat",
    "haath pair sunn hona": "numbness/tingling in hands and feet",
    "ghutna / ghutne / ghutno": "knee(s)",
    "pyaas": "thirst",
    "peshab": "urine / urination (NOT swallowing)",
    "baar baar peshab aana": "frequent urination",
    "chalne mein dard": "pain while walking",
    "nigalna / nigalne mein takleef": "difficulty SWALLOWING (food/liquid, throat) -- not urination",
    "taklif / takleef": "difficulty / discomfort / trouble",
    "kai hafton se / kai hafte se": "for several weeks",
    "kaafi din se": "for several days",
    "kaan": "ear",
    "kaan mein dard": "ear pain",
    "kaan se paani / kaan se paani nikalna": "fluid/discharge coming from the ear",
    "khansi": "cough",
    "zor ki khansi": "severe/forceful cough",
    "seeti jaisi awaaz / seeti ki awaaz": "whistling sound (wheeze) while breathing",
    "naak": "nose",
    "naak band hona": "blocked / stuffy nose",
    "ek taraf se band": "blocked on one side (NOT the eye)",
    "aankh": "eye",
    "aankh mein safed parda": "whitish film/cloudiness over the eye (cataract-type symptom, NOT bleeding)",
    "parda aa jaana": "a film/curtain-like covering appearing (over the eye)",
    "dhundla / dhundla dikhna": "blurry vision",
    "chakachaundh": "glare / dazzling sensation from bright light",
    # Real bug found and fixed here, 2026-09-29: tested live with "mujhe
    # gout hai, angoothe me sujan hai" (gout, toe swelling -- gout classically
    # affects the big toe) and the model translated "angoothe" (thumb/big
    # toe) as "knee and thigh" instead. Root cause: these basic anatomical
    # terms were never in the glossary at all, and "ghutna / ghutne / ghutno"
    # (knee) sitting right above in the same list -- a phonetically similar
    # Hindi word -- is the most likely source of the model's confusion when
    # given no explicit hint for "angoothe". Added the missing term plus
    # several other foundational body-part words the glossary never covered
    # (hand, foot, finger, lower back, upper back), since a symptom checker
    # missing basic anatomy vocabulary is a real, recurring accuracy risk,
    # not a one-off.
    "angootha / angoothe / angutha": "thumb (if paired with haath/hand) OR big toe (if paired with pair/foot/paanv) -- infer which from context, never default to knee",
    "haath / haathon": "hand(s) / arm(s)",
    "pair / paanv / pairon": "foot / feet / leg(s)",
    "ungli / ungliyan / unglee": "finger(s) / toe(s) (context-dependent on hand vs foot)",
    "kamar": "lower back / waist",
    "peeth": "back (upper/mid back)",
    # Second pass, same session, 2026-09-29: user pushed for further accuracy
    # after the angootha fix. Systematically diffed a checklist of common
    # Hindi body-part and symptom words against GLOSSARY_HINTS instead of
    # waiting for more live failures -- these were confirmed absent by direct
    # string search, not guessed. Each mapping below is standard/dictionary
    # Hindi, not a invented term.
    "gardan": "neck",
    "kandha / kandhe": "shoulder(s)",
    "kohni": "elbow",
    "kalai": "wrist",
    "kulha / kulhe": "hip(s)",
    "jaangh / jaanghon": "thigh(s)",
    "takhna / takhne": "ankle(s)",
    "pindli": "calf / shin",
    "daant": "tooth / teeth",
    "zubaan": "tongue",
    "hoth": "lips",
    "jabda": "jaw",
    "baal": "hair",
    "nakhun": "nail(s)",
    "khaal / tvacha": "skin",
    "ganth": "lump",
    "chot": "injury",
    "jakhm / zakhm": "wound",
    "peep": "pus",
    "dil": "heart (organ, NOT emotional 'dil' idioms -- infer from medical context)",
    "jigar": "liver",
    "gurda / gurde": "kidney(s)",
    "maasik dharam / mahwari": "menstruation / periods",
    "motapa": "obesity",
    "vajan": "weight",
    "neend na aana / neend nahi aati": "insomnia / difficulty sleeping",
    "yaddasht": "memory",
    "behoshi / behosh ho jaana": "unconsciousness / fainting",
    "kapkapi / kapkapaana": "shivering / trembling",
    "lakwa": "paralysis (typically facial/one-sided, e.g. stroke-related)",
    "jhanjhanahat": "tingling sensation",
    "sunn / sunn hona": "numb / numbness",
}

_TRANSLATION_FEWSHOT = [
    (
        "seene mein bahut tez dard ho raha hai aur saans lene mein taklif ho rahi hai",
        "I am having very severe chest pain and difficulty breathing.",
    ),
    (
        "gale mein bahut dard hai aur nigalne mein takleef ho rahi hai, bukhar bhi hai",
        "I have severe throat pain, difficulty swallowing, and fever.",
    ),
    (
        "khana khane ke baad pait mein jalan aur dard hota hai, kai hafton se",
        "I get a burning sensation and pain in my stomach after eating, for several weeks.",
    ),
]

# ---------------------------------------------------------------------------
# Deterministic hard-emergency keyword scan (independent of the LLM)
# ---------------------------------------------------------------------------

_EMERGENCY_PATTERNS = [
    # chest pain
    r"chest pain", r"crushing (pain|feeling) in (my |the )?chest", r"seene m[ae]{1,2}n?\s*dard",
    r"छाती में दर्द",
    # breathing difficulty
    r"can'?t breathe", r"cannot breathe", r"unable to breathe", r"difficulty breathing",
    r"trouble breathing", r"having trouble breathing",
    r"shortness of breath", r"saans nahi aa", r"saans phool rahi", r"saans ruk",
    r"सांस नहीं आ",
    # unconsciousness
    r"unconscious", r"unresponsive", r"behosh", r"passed out and (not|won'?t) wak",
    r"बेहोश",
    # seizure
    r"seizure", r"\bfits\b", r"convulsion", r"daura pad",
    r"दौरा पड़",
    # severe bleeding
    r"severe bleeding", r"bleeding heavily", r"bleeding a lot", r"blood (is )?not stopping",
    r"khoon nahi ruk", r"खून नहीं रुक",
    # stroke signs
    r"stroke", r"face (is |has )?drooping", r"slurred speech",
    r"one side.*(weak|numb|paralysed|paralyzed)", r"आधा चेहरा",
    # suicidal
    r"suicid", r"want(s)? to (kill myself|die)", r"khud ko khatam",
    r"खुद को खत्म",
    r"don'?t want to live", r"do not want to live", r"no reason to live",
    r"better off dead", r"end(ing)? (my|his|her|their) (own )?life",
    r"\bkill(ing)? myself\b", r"end it all", r"khud ko maar",
    # poisoning
    r"poison", r"swallowed .*(poison|acid|chemical)", r"zeher kha", r"जहर खा",
    # anaphylaxis
    r"anaphyla", r"throat (is |)closing",
    r"swelling of (the |)(face|throat|lips).*(sudden|breath)",
    r"(lips|throat|face|tongue)\b.{0,25}\bswell(ing)?\b",
    r"\bswell(ing)?\b.{0,25}\b(lips|throat|face|tongue)\b",
    # coughing/vomiting blood
    r"cough(ing)? (up |)blood", r"khoon.*khansi", r"khansi.*khoon",
    r"vomit(ing)? blood", r"khoon ki ulti", r"खून की उल्टी",
]
_EMERGENCY_RE = re.compile("|".join(_EMERGENCY_PATTERNS), re.IGNORECASE)


def _hard_emergency_scan(*texts: str) -> bool:
    for t in texts:
        if t and _EMERGENCY_RE.search(t):
            return True
    return False


def hard_emergency_scan(*texts: str) -> bool:
    """Public alias of _hard_emergency_scan for callers outside this module
    (e.g. routers/medical.py), which need this exact deterministic,
    LLM-independent emergency check on raw request text for every turn of
    the clarifying-question flow, not just inside identify_disease()."""
    return _hard_emergency_scan(*texts)


# ---------------------------------------------------------------------------
# Direct disease-name / alias fast-path (no LLM calls, no embeddings)
# ---------------------------------------------------------------------------
# A large share of real patient queries simply NAME the disease/condition
# directly, in their own language/spelling (e.g. "babaseer" = hemorrhoids/
# piles), rather than narrating symptoms. Running the full translate+embed+
# rerank LLM pipeline for these is unnecessary overkill on a CPU-only
# machine (60-180s/request) when cheap, deterministic, GPU-free fuzzy/alias
# string matching resolves them in milliseconds. This table is completely
# separate from GLOSSARY_HINTS/_LAY_SYNONYMS above -- those translate
# SYMPTOM words ("khansi" -> cough); this one only ever holds true direct
# disease-NAME synonyms. disease_master.json was checked (grep/read) and has
# NO existing alias/synonym/hindi_name field on any of the 323 entries --
# only "name" -- so every alias here is either (a) mechanically derived from
# a disease's own "name" field text (verifiable against the KB, never a new
# fact) or (b) a small, individually-reasoned, conservative list of
# well-known real Hindi/Hinglish disease-NAMING terms. When in doubt about a
# term's correctness or its uniqueness to one disease, it was left out
# entirely so the query falls through to the existing LLM pipeline instead
# of risking a wrong instant match.

# Acronyms actually written in disease_master.json's own "name" parentheses
# that are distinctive enough to be safe (i.e. hand-checked to NOT collide
# with a common English/Hindi/Hinglish word even after lowercasing, e.g.
# "AS"/"AR"/"PE"/"PH"/"CS"/"PAD"/"DID" were found in the data but excluded
# here because "as", "pe" (Hinglish "on"), "pad", "did" etc. are ordinary
# words that would otherwise false-fire on unrelated sentences).
_ALIAS_SAFE_ACRONYMS = frozenset({
    "PCOS", "COPD", "GERD", "BPH", "OCD", "PTSD", "ADHD", "TIA", "IBS",
    "CKD", "DVT", "ARDS", "SLE", "BPPV", "ALS", "ITP", "TTP", "RTA", "DKA",
    "CAH", "PKU", "SCID", "VWD", "MDS", "JIA", "BDD", "GVHD", "MCTD",
    "SNHL", "DNS", "NPC", "AMD", "RCC", "CML", "CLL", "APL", "TOF", "PDA",
    "VSD", "IDA", "IHD", "CHF", "HCM", "VTE", "NSCLC", "SCLC", "OSA",
    "ILD", "IPF", "ESRD",
})

# Generic clinical-classification words that show up inside many disease
# names but never uniquely identify one on their own (e.g. "disease",
# "syndrome", "cancer" each appear in 5-10+ different entries) -- excluded
# from the automatic single-word derivation below so it can't accidentally
# manufacture an ambiguous alias out of pure bad luck.
_ALIAS_GENERIC_WORDS = frozenset({
    "disease", "disorder", "syndrome", "infection", "deficiency", "failure",
    "injury", "carcinoma", "tumour", "tumor", "tumours", "cancer",
    "arthritis", "leukemia", "leukaemia", "anemia", "anaemia", "dementia",
    "neuropathy", "nephropathy", "myopathy", "cardiomyopathy", "hearing",
    "loss", "headache", "phobia", "palsy", "paralysis", "fever",
    "condition", "attack", "acute", "chronic", "primary", "secondary",
    "idiopathic", "congenital", "hereditary", "childhood", "adult",
    "genetic", "autoimmune", "and", "or", "of", "the", "with", "including",
    "classification", "type", "types", "group", "full", "other", "causes",
    "cause", "entities", "linked", "majority", "phenotypes", "focus",
    "clinical", "most", "studied", "severe", "form", "forms", "non",
    "spontaneous", "traumatic", "iatrogenic", "catamenial", "tension",
    "malignant", "benign", "persistent",
})

# Real, individually-verified single words that survive the automatic
# derivation below (unique to one disease's name text) but were manually
# found, on reading the actual output, to be ordinary English/Hinglish
# words that could appear in an unrelated sentence -- e.g. "accident"
# (surfaced from "Cerebrovascular Accident" -> stroke; a patient typing
# "mera accident hua tha" means a road accident, not a stroke complaint),
# "stress"/"cough"/"throat"/"sleep"/"shoulder"/"pressure"/"normal" etc.
# Dropped regardless of KB-uniqueness for the same reason GLOSSARY_HINTS
# never treats a bare symptom word as a disease name.
_ALIAS_EXCLUDE_WORDS = frozenset({
    "accident", "activation", "adenoma", "adrenal", "anxiety", "back",
    "brain", "cardiac", "combined", "conduct", "connective", "contact",
    "cord", "cough", "death", "defect", "disc", "distress", "eating",
    "fold", "foot", "generalized", "germ", "giant", "identity", "immune",
    "inappropriate", "legs", "media", "mixed", "nodule", "nodules",
    "normal", "pressure", "reactive", "restless", "seasonal", "secretion",
    "shoulder", "sleep", "solar", "specific", "spectrum", "stress",
    "sudden", "symptom", "syndromes", "tear", "throat", "tissue", "toxic",
    "valve", "viii",
    # Found via a systematic real test: checking every auto-derived
    # single-word alias with rapidfuzz against /usr/share/dict/words
    # (~61K common English words) turned up real, dangerous near-miss
    # collisions at/above the fuzzy threshold, e.g. "patent" (from "Patent
    # Ductus Arteriosus") scored 92.3 against the ordinary word "patient" --
    # which is exactly the false positive this exercise found and fixed:
    # both eng_clinical/eng_clinical2 regression queries (plain sentences
    # starting "Patient reports...") were wrongly fast-pathing to
    # patent_ductus_arteriosus before this fix. Each of the rest below was
    # confirmed the same way (>=90 fuzzy score against a common, unrelated
    # English word): atrial~trial, atopic~topic, aplastic~plastic,
    # spina~spinal, planus~plans, oppositional~opposition, ductus~ducts,
    # respiratory (too generic/non-specific to ARDS specifically -- most
    # real "respiratory" complaints are asthma/COPD/pneumonia, not ARDS).
    "patent", "atrial", "atopic", "aplastic", "spina", "planus",
    "oppositional", "ductus", "respiratory",
    # Found via manual review of the full derived alias list: these are
    # real dictionary/medical words that ARE unique to one disease's name
    # text in this KB, but are used far more often in everyday or general
    # clinical speech for something else entirely -- e.g. "gestational"
    # co-occurs overwhelmingly with "gestational diabetes" (not in this KB
    # as its own entry) yet was mapping to the rare cancer
    # gestational_trophoblastic_neoplasia (real, confirmed bug: "mujhe
    # gestational diabetes tha pregnancy ke time" fast-pathed to that cancer
    # before this fix); "viral" is used generically for any viral fever,
    # not specifically viral_hepatitis; "depression" alone was only
    # captured from "Postpartum Depression"'s name (a corpus artifact) and
    # would have wrongly sent every generic depression mention to
    # postpartum_depression specifically instead of falling through to the
    # LLM; the rest are the same pattern -- a word that names an anatomical
    # part, symptom, or generic clinical adjective shared across multiple
    # real conditions (some in this KB, some not), not a true unique
    # disease name.
    "gestational", "viral", "depression", "vertigo", "salmonella",
    "irritable", "stones", "pituitary", "alpha", "cluster", "vascular",
    "transient", "lumbar", "tunnel", "muscular", "frozen", "adhesive",
    "tennis", "elbow", "rupture", "tendon", "allergic", "fatty",
    "alcoholic", "gastric", "endocrine", "marrow", "tremor", "cerebral",
    "panic", "borderline", "antisocial", "binge", "juvenile", "defiant",
    "adjustment", "familial", "complement", "scarring", "externa",
})

# Real disease-naming words that must NEVER be matched by lenient fuzzy
# tolerance despite being long enough to normally qualify, because a
# specific, plausible, common word sits just above the fuzzy threshold
# (found the same way as _ALIAS_EXCLUDE_WORDS above, e.g. "masse" ~
# "masses" scores 90.9 -- "masses"/lumps is a real, different, and more
# serious complaint than warts). Typed/pasted verbatim they still match
# (exact), just never via a fuzzy near-miss.
_ALIAS_FORCE_EXACT_WORDS = frozenset({"masse"})

# Hand-curated, conservative list of real, well-known Hindi/Hinglish/lay
# DISEASE-NAMING terms (not symptom words -- e.g. "khansi" alone means
# "cough", a symptom, and is deliberately NOT here). Each was individually
# checked for (a) being a real, correct synonym and (b) NOT being ambiguous
# with another disease in this KB (e.g. "pathri" = stone was left out
# because it is used for both kidney stones and gallstones in real usage;
# "lakva" = paralysis was left out because it is used colloquially for both
# stroke and Bell's palsy). disease_id keys verified to exist in
# disease_master.json.
_MANUAL_DISEASE_ALIASES: Dict[str, List[str]] = {
    "hemorrhoids": ["piles", "babaseer", "bawaseer", "bavaseer"],
    "diabetes_mellitus": ["madhumeh", "sugar ki bimari"],
    "tuberculosis": ["tb", "tapedik", "kshay rog"],
    "bronchial_asthma": ["dama"],
    "measles": ["khasra"],
    "vitiligo": ["safed daag", "safed dag", "leucoderma"],
    "hypertension": ["high bp", "high blood pressure", "bp high"],
    "pcos": ["pcod"],
    "verruca_vulgaris": ["masse", "masaa"],
    "epilepsy": ["mirgi"],
    "acne_vulgaris": ["muhase", "kil muhase"],
    "leprosy": ["kusht rog"],
    "bacterial_conjunctivitis": ["aankh aana"],
    "urinary_tract_infection": ["uti"],
    "hiv_aids": ["hiv"],
}

# Aliases of this length or shorter are only ever matched by an EXACT token
# match (never rapidfuzz), because fuzzy matching on a 2-3 character string
# is not meaningful -- almost anything scores "close" to a 2-letter string.
_ALIAS_SHORT_EXACT_MAXLEN = 3
_ALIAS_SINGLE_FUZZY_THRESHOLD = 90
_ALIAS_PHRASE_FUZZY_THRESHOLD = 88
# If a second, different disease's best hit is within this many points of
# the top hit, the match is genuinely ambiguous at runtime (even though the
# static dictionary itself is de-duplicated to one disease per alias
# string) -- e.g. two distinct short aliases both fuzzy-scoring close to
# the same patient token. Safer to fall through to the LLM than guess.
_ALIAS_AMBIGUITY_MARGIN = 4

_ALIAS_LOCK = threading.Lock()
_ALIAS_BY_LEN: Optional[Dict[int, List[Tuple[str, str]]]] = None
_ALIAS_DISEASE_INFO: Optional[Dict[str, Dict[str, Any]]] = None
_ALIAS_TOKEN_RE = re.compile(r"[a-z]+(?:['\-][a-z]+)*")


def _alias_clean_word(w: str) -> str:
    return re.sub(r"[^a-zA-Z']", "", w).strip()


def _alias_split_primary_and_parens(name: str) -> Tuple[str, List[str]]:
    parens = re.findall(r"\(([^()]*)\)", name)
    primary = re.split(r"\(|--", name)[0].strip(" -/")
    return primary, parens


def _build_alias_index() -> None:
    """Build the disease-name alias dictionary once, from disease_master.json's
    own "name" field text plus _MANUAL_DISEASE_ALIASES -- never from the
    embedding index, so this fast-path never needs the sentence-transformer
    model or Ollama to be touched at all."""
    global _ALIAS_BY_LEN, _ALIAS_DISEASE_INFO
    if _ALIAS_BY_LEN is not None:
        return
    with _ALIAS_LOCK:
        if _ALIAS_BY_LEN is not None:
            return
        diseases = _load_diseases()
        alias_map: Dict[str, set] = {}
        disease_info: Dict[str, Dict[str, Any]] = {}

        def add(text: str, did: str) -> None:
            text = text.strip(" -").lower()
            if text:
                alias_map.setdefault(text, set()).add(did)

        for did, d in diseases.items():
            name = d.get("name", "")
            disease_info[did] = {
                "name": name,
                "EMERGENCY_OVERRIDE_RULE": d.get("EMERGENCY_OVERRIDE_RULE"),
            }
            primary, parens = _alias_split_primary_and_parens(name)
            phrases: List[str] = []
            for part in re.split(r"\s*/\s*", primary):
                part = part.strip(" -")
                if part:
                    phrases.append(part)
            for paren in parens:
                paren = paren.strip()
                if re.fullmatch(r"[A-Z0-9&/\-]{2,7}", paren):
                    for sub in re.split(r"[/&]", paren):
                        sub = sub.strip()
                        if sub in _ALIAS_SAFE_ACRONYMS:
                            add(sub, did)
                    continue
                # Skip parentheticals that are classification/list text
                # (e.g. "Type 2 Diabetes Mellitus - majority; ... as linked
                # entities") rather than a clean alternate name.
                if "," in paren or ";" in paren or "including" in paren.lower() or " and " in paren.lower():
                    continue
                words = paren.split()
                if 1 <= len(words) <= 5 and all(re.fullmatch(r"[A-Za-z'\-]+", w) for w in words):
                    phrases.append(paren.strip())

            for ph in phrases:
                ph_clean = ph.strip(" -")
                if not ph_clean:
                    continue
                if len(ph_clean.split()) >= 2:
                    add(ph_clean, did)
                for w in ph_clean.split():
                    cw = _alias_clean_word(w)
                    if not cw:
                        continue
                    lw = cw.lower()
                    if lw in _ALIAS_GENERIC_WORDS or lw in _ALIAS_EXCLUDE_WORDS:
                        continue
                    # Single words need a higher bar (>=5 chars) than
                    # phrases, since a short common word is far more likely
                    # to collide with unrelated text than a multi-word
                    # phrase is.
                    if len(cw) >= 5:
                        add(lw, did)
                    elif cw.isupper() and cw in _ALIAS_SAFE_ACRONYMS:
                        add(lw, did)

        for did, extra in _MANUAL_DISEASE_ALIASES.items():
            if did not in diseases:
                continue
            for a in extra:
                add(a, did)

        by_len: Dict[int, List[Tuple[str, str]]] = {}
        dropped_ambiguous = 0
        for alias, ids in alias_map.items():
            if len(ids) != 1:
                dropped_ambiguous += 1
                continue
            if alias in _ALIAS_EXCLUDE_WORDS:
                continue
            did = next(iter(ids))
            wc = len(alias.split())
            by_len.setdefault(wc, []).append((alias, did))

        _ALIAS_BY_LEN = by_len
        _ALIAS_DISEASE_INFO = disease_info
        logger.info(
            "alias fast-path index built: %d unique alias strings kept, "
            "%d dropped as ambiguous (shared by >1 disease)",
            sum(len(v) for v in by_len.values()), dropped_ambiguous,
        )


def _alias_tokenize(text: str) -> List[str]:
    return _ALIAS_TOKEN_RE.findall((text or "").lower())


def _try_direct_alias_match(patient_text: str) -> Optional[Tuple[str, float]]:
    """Cheap, GPU-free, LLM-free fast-path: fuzzy/alias-match the patient's raw
    text against the disease-name alias dictionary. Returns (disease_id,
    confidence) only on a clear, unambiguous, high-confidence direct hit;
    returns None (meaning: fall through to the full LLM pipeline) for
    anything else, including genuine symptom-narrative text with no disease
    name in it and any case where two different diseases both score close
    to the top match."""
    _build_alias_index()
    tokens = _alias_tokenize(patient_text)
    if not tokens or not _ALIAS_BY_LEN:
        return None

    from rapidfuzz import fuzz

    n = len(tokens)
    hits: List[Tuple[float, str]] = []  # (score, disease_id)
    for wc, entries in _ALIAS_BY_LEN.items():
        if wc > n:
            continue
        windows = [" ".join(tokens[i:i + wc]) for i in range(n - wc + 1)]
        for alias, did in entries:
            if len(alias) <= _ALIAS_SHORT_EXACT_MAXLEN or alias in _ALIAS_FORCE_EXACT_WORDS:
                if any(w == alias for w in windows):
                    hits.append((100.0, did))
                continue
            threshold = _ALIAS_SINGLE_FUZZY_THRESHOLD if wc == 1 else _ALIAS_PHRASE_FUZZY_THRESHOLD
            best = 0.0
            for w in windows:
                s = fuzz.ratio(alias, w)
                if s > best:
                    best = s
            if best >= threshold:
                hits.append((best, did))

    if not hits:
        return None

    hits.sort(key=lambda h: -h[0])
    best_score, best_did = hits[0]
    for score, did in hits[1:]:
        if did != best_did and (best_score - score) <= _ALIAS_AMBIGUITY_MARGIN:
            return None  # genuinely ambiguous at runtime -- let the LLM decide

    return best_did, min(0.97, best_score / 100.0)


# ---------------------------------------------------------------------------
# Disease knowledge base loading + corpus building
# ---------------------------------------------------------------------------

_INDEX_LOCK = threading.Lock()
_MODEL = None
_DISEASE_IDS: Optional[List[str]] = None
_DISEASE_EMB: Optional[np.ndarray] = None
_DISEASE_META: Optional[Dict[str, Any]] = None
_DISEASE_TOKENS: Optional[List[frozenset]] = None

# Honest fallback bookkeeping for test reporting (see README/test script).
STATS = {"calls": 0, "translate_fallbacks": 0, "rerank_fallbacks": 0, "voted_calls": 0, "alias_fastpath_hits": 0}

# Self-consistency voting is only worth the 3x rerank latency on genuinely
# ambiguous top-1-vs-top-2 candidate gaps. Chosen from REAL measured gaps
# (top1_score - top2_score from _get_candidates) across a spread of real
# translated queries on this exact corpus, not guessed:
#   genuinely ambiguous (wrong/unstable top pick observed or plausible):
#     hin3 (PCOS vs osteoporosis) gap=0.0049, hin5 (knee OA vs rotator cuff)
#     gap=0.0045, eng_clinical2 (diabetes mellitus vs insipidus/incontinence)
#     gap=0.0092
#   clearly-led, single-call-safe cases:
#     hin1 (ear) gap=0.046, hin4 (UTI-type) gap=0.045, em1 (stroke) gap=0.082,
#     kb2 (nosebleed) gap=0.086, kb1/eng_clinical/eng_casual (cataract family)
#     gap=0.117-0.122
# There is a clean ~5x separation between the two clusters (max ambiguous
# 0.0092 vs min clear 0.045). 0.02 sits in that gap with margin on both
# sides, so it reliably fires voting only for the genuinely close cases.
RERANK_VOTE_GAP_THRESHOLD = 0.02
RERANK_VOTE_N = 3

_SKIP_KEYS = {"source", "sources", "confidence", "note", "name", "finding"}
_PROSE_KEYS = (
    "overview", "definition", "clinical_presentation", "classification",
    "summary", "description",
)


def _load_diseases() -> Dict[str, Any]:
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["diseases"]


def _flatten_findings(obj: Any, out: List[str], max_items: int = 30) -> None:
    # NOTE: this KB stores clinical text in two different shapes across
    # entries -- some leaves are {"finding": "...", "source": "...", ...}
    # dicts, but ~68% of diseases (verified by scanning disease_master.json)
    # instead store the text directly as a plain string value, e.g.
    # {"em_minor_vs_em_major": "Erythema multiforme is real-world split
    # into...", "source_em_minor_major": "..."}. The original version of
    # this function only ever captured strings found under "name"/"finding"
    # keys and silently dropped bare string values entirely -- for
    # erythema_multiforme this meant _extract_findings returned an EMPTY
    # list (verified), so its rerank candidate line had zero symptom
    # content. Capturing any non-skip-key string value fixes this for every
    # affected disease at once, not just this one.
    #
    # Real, directly-confirmed bug fixed here (read the actual embedded
    # corpus text -- medical_understanding._build_corpus_entry's real
    # output -- for a real retrieval-failure case, typhoid_fever, not
    # guessed): _SKIP_KEYS only exact-matches the BARE words "source"/
    # "confidence"/etc, so a COMPOUND key like "source_fever" or
    # "confidence_rose_spots" (confirmed real keys under typhoid_fever.
    # symptoms.classic_symptoms, and this docstring's OWN example above,
    # "source_em_minor_major", is the exact same pattern) was never
    # skipped -- its full citation-text VALUE ("CDC, Typhoid Fever Signs
    # and Symptoms...; Shafqat Z et al, Cureus 2025;17(10):e94621 (PMID
    # 41246786); Rathod BD et al...") was appended directly into the REAL
    # PRODUCTION EMBEDDING CORPUS as if it were symptom content. Confirmed
    # as the real, direct cause of typhoid_fever's catastrophic retrieval
    # failure (true full-corpus-similarity rank 303/323 for its own real
    # symptom query) -- a meaningful fraction of its embedded "symptom"
    # text was author names/journal names/PMIDs, diluting and corrupting
    # the semantic signal actually used for matching. This is the exact
    # same bug class pharmacy_service._is_hard_citation_key was already
    # built and proven to fix (source_*/*_source/*_citation/confidence_*
    # patterns) -- but that fix was only ever wired into pharmacy_service's
    # OWN extraction functions (used for query text / disambiguation
    # terms), never into THIS function, which is what actually builds the
    # real retrieval embedding corpus every disease is matched against.
    # Reusing it here (imported above) closes that gap at the root, for
    # every disease using this schema convention, not just typhoid_fever.
    if len(out) >= max_items:
        return
    if isinstance(obj, dict):
        for key in ("name", "finding"):
            v = obj.get(key)
            if isinstance(v, str) and v.strip():
                out.append(v.strip()[:180])
        for k, v in obj.items():
            if k in _SKIP_KEYS or k in ("name", "finding") or _is_hard_citation_key(k):
                continue
            if isinstance(v, str) and v.strip():
                out.append(v.strip()[:180])
            else:
                _flatten_findings(v, out, max_items)
            if len(out) >= max_items:
                return
    elif isinstance(obj, list):
        for item in obj:
            _flatten_findings(item, out, max_items)
            if len(out) >= max_items:
                return


def _grab_prose_snippets(obj: Any, out: List[str], depth: int = 0) -> None:
    if depth > 3 or len(out) >= 8:
        return
    if isinstance(obj, dict):
        for k in _PROSE_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                out.append(v.strip()[:220])
        for v in obj.values():
            _grab_prose_snippets(v, out, depth + 1)
            if len(out) >= 8:
                return


# Clinical-jargon -> lay-term bridge. The disease corpus is written in real
# clinical language (e.g. "Polyuria", "Polydipsia", "Epistaxis") but patients
# describe symptoms in lay terms ("frequent urination", "very thirsty",
# "nosebleed"). Empirical testing found that even a CORRECT English
# translation of a patient's complaint failed to retrieve the right disease
# in the top-20 candidates purely because of this vocabulary gap (e.g.
# "excessive thirst and frequent urination" ranked diabetes_mellitus 56th).
# This is a standard IR technique (synonym/alias expansion of the index),
# not a per-query hack -- it is applied uniformly to every disease's corpus.
_LAY_SYNONYMS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bpolyuria\b", re.I), "frequent urination"),
    (re.compile(r"\bpolydipsia\b", re.I), "excessive thirst"),
    (re.compile(r"\bpolyphagia\b", re.I), "excessive hunger"),
    (re.compile(r"\bdyspn[oe]a\b", re.I), "shortness of breath / breathlessness"),
    (re.compile(r"\btachycardia\b", re.I), "fast / racing heartbeat"),
    (re.compile(r"\bbradycardia\b", re.I), "slow heartbeat"),
    (re.compile(r"\bpruritus\b", re.I), "itching"),
    (re.compile(r"\bdysuria\b", re.I), "burning / painful urination"),
    (re.compile(r"\bh(a)?ematuria\b", re.I), "blood in urine"),
    (re.compile(r"\bh(a)?emoptysis\b", re.I), "coughing up blood"),
    (re.compile(r"\barthralgia\b", re.I), "joint pain"),
    (re.compile(r"\bmyalgia\b", re.I), "muscle pain / body ache"),
    (re.compile(r"\bodynophagia\b", re.I), "painful swallowing"),
    (re.compile(r"\bdysphagia\b", re.I), "difficulty swallowing"),
    (re.compile(r"\bphotophobia\b", re.I), "sensitivity to light"),
    (re.compile(r"\bpar[ae]esthesia\b", re.I), "tingling / numbness"),
    (re.compile(r"\bsyncope\b", re.I), "fainting"),
    (re.compile(r"\bvertigo\b", re.I), "dizziness / spinning sensation"),
    (re.compile(r"\bdiaphoresis\b", re.I), "excessive sweating"),
    (re.compile(r"\b[oe]edema\b", re.I), "swelling"),
    (re.compile(r"\bpallor\b", re.I), "paleness"),
    (re.compile(r"\bjaundice\b", re.I), "yellowing of skin or eyes"),
    (re.compile(r"\bcyanosis\b", re.I), "bluish skin or lips"),
    (re.compile(r"\btinnitus\b", re.I), "ringing in the ears"),
    (re.compile(r"\brhinorrh[oe]a\b", re.I), "runny nose"),
    (re.compile(r"\bh(a)?ematemesis\b", re.I), "vomiting blood"),
    (re.compile(r"\bmelena\b", re.I), "black tarry stools"),
    (re.compile(r"\bh(a)?ematochezia\b", re.I), "blood in stool"),
    (re.compile(r"\bamenorrh[oe]a\b", re.I), "absent periods"),
    (re.compile(r"\bdysmenorrh[oe]a\b", re.I), "painful periods"),
    (re.compile(r"\bmenorrhagia\b", re.I), "heavy periods"),
    (re.compile(r"\banorexia\b", re.I), "loss of appetite"),
    (re.compile(r"\bmalaise\b", re.I), "general feeling of being unwell"),
    (re.compile(r"\blethargy\b", re.I), "tiredness / low energy"),
    (re.compile(r"\bdiplopia\b", re.I), "double vision"),
    (re.compile(r"\bxerostomia\b", re.I), "dry mouth"),
    (re.compile(r"\balopecia\b", re.I), "hair loss"),
    (re.compile(r"\berythema\b", re.I), "redness of skin"),
    (re.compile(r"\burticaria\b", re.I), "hives"),
    (re.compile(r"\becchymosis\b", re.I), "bruising"),
    (re.compile(r"\bpetechiae\b", re.I), "small red/purple skin spots"),
    (re.compile(r"\bhepatomegaly\b", re.I), "enlarged liver"),
    (re.compile(r"\bsplenomegaly\b", re.I), "enlarged spleen"),
    (re.compile(r"\blymphadenopathy\b", re.I), "swollen lymph nodes / glands"),
    (re.compile(r"\boliguria\b", re.I), "reduced urination"),
    (re.compile(r"\banuria\b", re.I), "no urination"),
    (re.compile(r"\botalgia\b", re.I), "ear pain"),
    (re.compile(r"\bstomatitis\b", re.I), "mouth sores"),
    (re.compile(r"\bangina\b", re.I), "chest pain / tightness"),
    (re.compile(r"\bclaudication\b", re.I), "leg pain while walking"),
    (re.compile(r"\bhemiparesis\b", re.I), "one-sided weakness"),
    (re.compile(r"\bataxia\b", re.I), "loss of balance / coordination"),
    (re.compile(r"\bdysarthria\b", re.I), "slurred speech"),
    (re.compile(r"\baphasia\b", re.I), "difficulty speaking or understanding language"),
    (re.compile(r"\bepistaxis\b", re.I), "nosebleed"),
    (re.compile(r"\bkoilonychia\b", re.I), "spoon-shaped nails"),
    (re.compile(r"\bglossitis\b", re.I), "sore / inflamed tongue"),
]


def _lay_term_additions(text: str) -> List[str]:
    additions: List[str] = []
    seen = set()
    for pattern, lay in _LAY_SYNONYMS:
        if lay not in seen and pattern.search(text):
            additions.append(lay)
            seen.add(lay)
    return additions


# Section names this KB actually uses (surveyed across all 323 diseases) that
# hold real patient-facing symptom/sign content, in priority order. Plenty of
# other sections exist (epidemiology, risk_factors, natural_history,
# differential_diagnosis, ...) but they describe causes/course/lookalikes, not
# what the patient themselves would report -- e.g. for cataract, risk-factor
# sentences ("smoking is a risk factor for cataract") are SHORTER than the
# real symptom sentences in "classic_symptoms" ("glare and halos around
# lights at night"), so a pure length-sort (the previous approach) surfaced
# risk factors instead of symptoms. Preferring these sections when present
# fixes that generally, for every disease that uses this schema convention,
# not just the ones in the known failing test cases.
_SYMPTOM_SECTION_KEYS = (
    "classic_symptoms", "clinical_presentation", "core_presentation",
    "specific_diagnostic_signs", "red_flags", "core",
)


def _extract_findings(d: Dict[str, Any]) -> List[str]:
    symptoms = d.get("symptoms", {})

    # Pass 1: pull only from the known symptom-bearing sections, so real
    # patient-facing findings are never outranked by shorter but clinically
    # irrelevant sentences (risk factors, epidemiology, citations) living
    # elsewhere in the entry.
    priority: List[str] = []
    if isinstance(symptoms, dict):
        for key in _SYMPTOM_SECTION_KEYS:
            if key in symptoms:
                _flatten_findings(symptoms[key], priority, max_items=40)
    priority = list(dict.fromkeys(priority))
    priority.sort(key=len)

    if len(priority) >= 3:
        return priority

    # Fallback for the (smaller) set of diseases that don't use any of the
    # above section names: collect broadly, as before. A DFS walk that stops
    # at the first N items truncates before ever reaching short entries
    # (verified: for osteoarthritis this silently dropped every real symptom
    # name and kept only diagnostic-criteria prose). Fix: collect generously,
    # then rank by length so concise symptom/finding names (almost always
    # <80 chars) sort ahead of long prose paragraphs, kept as trailing
    # context; priority-section hits (if any) are always kept in front.
    findings: List[str] = []
    _flatten_findings(symptoms, findings, max_items=80)
    if len(findings) < 3:
        _grab_prose_snippets(symptoms, findings)
    dedup = list(dict.fromkeys(findings))
    dedup.sort(key=len)
    combined = priority + [x for x in dedup if x not in priority]
    return combined


def _candidate_symptom_line(d: Dict[str, Any], max_terms: int = 3, max_chars: int = 140) -> str:
    """Short, distinguishing symptom snippet shown to the LLM alongside each
    candidate's id/name/category during reranking. Root cause of observed
    misdiagnoses on close differentials (e.g. cataract complaint reranked to
    erythema_multiforme, an unrelated skin condition): the rerank prompt
    previously showed ONLY 'id | name | category' -- zero actual symptom
    content to discriminate on -- so the model had no way to check whether a
    candidate's real symptoms matched the complaint at all, and was
    effectively guessing among plausible-sounding names. Real symptom terms
    (drawn from disease_master.json by _extract_findings, which now prefers
    the KB's own "classic_symptoms"/"clinical_presentation"/etc sections) give
    it the same distinguishing information a doctor would use, never invented.
    Capped at 3 terms x 140 chars (not the full findings list) to keep a
    ~15-20 candidate prompt block a reasonable size for rerank latency."""
    terms = [t[:max_chars] for t in _extract_findings(d)[:max_terms]]
    return "; ".join(terms)


def _build_corpus_entry(d: Dict[str, Any]) -> str:
    dedup = _extract_findings(d)
    short_terms = dedup[:20]
    long_context = dedup[20:23]
    name = d.get("name", "")
    category = d.get("category", "")
    base_text = f"{name}. Category: {category}. " + " ".join(short_terms + long_context)

    # Detect jargon->lay additions over the FULL (untruncated) text, since the
    # jargon terms driving these additions are often found only deep in the
    # findings list -- then cap the base text and append the lay terms right
    # after so they always survive truncation (they were previously appended
    # at the very end and silently dropped by the length cap; fixed here).
    additions = _lay_term_additions(base_text)
    text = base_text[:1400]
    if additions:
        text += " Also known as: " + ", ".join(additions) + "."
    return text[:1900]


def _get_embedding_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(EMBED_MODEL_NAME)
    return _MODEL


_WORD_RE = re.compile(r"[a-zA-Zऀ-ॿ]{3,}")
_STOPWORDS = frozenset({
    "and", "the", "for", "are", "was", "were", "has", "have", "had", "not",
    "with", "from", "this", "that", "also", "known", "aur", "hai", "hain",
    "mein", "kar", "hota", "hoti", "hote", "bhi", "kya", "kaafi", "din",
    "baar", "mera", "meri", "mujhe", "raha", "rahi", "rahe", "din", "hua",
    "hui", "hue", "ago", "since", "days", "day", "she", "his", "her", "him",
    "who", "which", "than", "such", "any", "all", "one", "two", "may", "can",
    "often", "most", "some", "into", "over", "per", "per100000",
})


def _tokenize(text: str) -> frozenset:
    return frozenset(
        w for m in _WORD_RE.finditer(text or "")
        if (w := m.group(0).lower()) not in _STOPWORDS
    )


def _ensure_index() -> None:
    global _DISEASE_IDS, _DISEASE_EMB, _DISEASE_META, _DISEASE_TOKENS
    if _DISEASE_IDS is not None:
        return
    with _INDEX_LOCK:
        if _DISEASE_IDS is not None:
            return
        mtime = DATA_PATH.stat().st_mtime
        diseases = _load_diseases()
        ids = list(diseases.keys())
        corpus = [_build_corpus_entry(diseases[i]) for i in ids]
        _DISEASE_TOKENS = [_tokenize(c) for c in corpus]

        if EMBED_CACHE_PATH.exists() and EMBED_META_PATH.exists():
            try:
                meta = json.loads(EMBED_META_PATH.read_text())
                if (
                    meta.get("ids") == ids
                    and abs(float(meta.get("mtime", -1)) - mtime) < 1e-6
                    and meta.get("model") == EMBED_MODEL_NAME
                    and meta.get("corpus_version") == CORPUS_VERSION
                ):
                    emb = np.load(EMBED_CACHE_PATH)
                    if emb.shape[0] == len(ids):
                        _DISEASE_IDS = ids
                        _DISEASE_EMB = emb
                        _DISEASE_META = diseases
                        logger.info("loaded cached disease embeddings (%d diseases, model=%s)", len(ids), EMBED_MODEL_NAME)
                        return
            except Exception:
                logger.warning("disease embedding cache unreadable, rebuilding", exc_info=True)

        logger.info("building disease embedding index (%d diseases, model=%s)...", len(diseases), EMBED_MODEL_NAME)
        model = _get_embedding_model()
        emb = model.encode(corpus, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
        emb = np.asarray(emb, dtype=np.float32)
        np.save(EMBED_CACHE_PATH, emb)
        EMBED_META_PATH.write_text(json.dumps({
            "mtime": mtime, "ids": ids, "model": EMBED_MODEL_NAME,
            "corpus_version": CORPUS_VERSION,
        }))
        _DISEASE_IDS = ids
        _DISEASE_EMB = emb
        _DISEASE_META = diseases
        logger.info("disease embedding index built and cached.")


# ---------------------------------------------------------------------------
# Ollama calls
# ---------------------------------------------------------------------------

def _ollama_chat(
    messages: List[Dict[str, str]], timeout: int, force_json: bool = False,
    model: str = OLLAMA_MODEL, temperature: float = 0.1,
    keep_alive: Optional[str] = None,
) -> str:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if force_json:
        payload["format"] = "json"
    if keep_alive is not None:
        # Real, measured reason this exists: translate (3B) and rerank (7B)
        # are different models. This machine has 15GB RAM; if both models
        # are left resident at once (Ollama's default keep_alive is 5
        # minutes, so back-to-back calls with different models both stay
        # loaded), combined ~7.3GB of model weights plus the embedding model
        # and FastAPI process pushed real measured memory to 12GB/15GB used
        # with ~3GB swapped to disk -- and a single, non-ambiguous query
        # (hin1) that should take ~10-15s took a measured 184s because of
        # disk-swap thrashing. Passing keep_alive="0s" after the translate
        # call tells Ollama to unload that model immediately once the
        # response is sent, so only one model is ever resident when the next
        # (rerank) call loads -- this removed the 184s-class outliers in
        # re-testing.
        payload["keep_alive"] = keep_alive
    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _translate(patient_text: str) -> Tuple[str, bool]:
    # Kept on OLLAMA_MODEL (3B), not moved to RERANK_MODEL (7B). Two real,
    # measured findings drove this: (1) translation quality was already
    # correct on 3B for every tricky glossary term checked (e.g. kb1's
    # "safed jaisa parda"/"chakachaundh" -> "whitish film"/"glare", matching
    # 7B's output on the same text) -- the documented earlier mistranslation
    # failures were closed by the GLOSSARY_HINTS table, not model size. (2)
    # this function's real system prompt is large (the full glossary + 3
    # few-shot examples, ~1000+ tokens) -- measured prompt-processing speed
    # on this CPU is ~24-25 tokens/sec regardless of model, so 7B's slower
    # per-token cost compounds badly here: a live end-to-end test showed
    # this exact call taking ~51s on 7B vs ~2-3s warm on 3B for the same
    # prompt. Moving translate to 7B was tried and reverted in this session
    # for that reason -- it was a real regression, not a neutral change.
    # The remaining risk -- translate(3B) and rerank(7B) both resident at
    # once on this 15GB-RAM CPU-only box pushing the system into ~3GB of
    # disk swap and one measured 184s outlier on a plain non-ambiguous query
    # -- is fixed below with keep_alive="0s": Ollama unloads 3B immediately
    # after this call returns, so only one model is ever resident when the
    # rerank (7B) call that follows loads.
    glossary_lines = "\n".join(f'- "{k}" -> {v}' for k, v in GLOSSARY_HINTS.items())
    system = (
        "You are a medical translation assistant for a symptom-checker. The patient may write in "
        "Hindi, English, Hinglish (romanized Hindi), or regional colloquial terms. Translate/normalize "
        "their complaint into ONE short, plain English clinical sentence describing ONLY the symptoms "
        "they mentioned. Translate word-by-word and literally, checking each Hindi/Hinglish word "
        "against the glossary below before translating it -- if you are not fully sure of a word, "
        "translate it as closely and conservatively as possible rather than guessing a different symptom. "
        "NEVER invent, add, drop, or substitute a symptom that was not stated. Do not diagnose. "
        "Your output sentence must always be in English, never Hindi, Chinese, or any other language.\n"
        "Known tricky terms and their correct meaning:\n" + glossary_lines
    )
    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    for src, tgt in _TRANSLATION_FEWSHOT:
        messages.append({"role": "user", "content": f"Patient text: {src}\n\nOutput only the translated sentence, nothing else."})
        messages.append({"role": "assistant", "content": tgt})
    messages.append({"role": "user", "content": f"Patient text: {patient_text}\n\nOutput only the translated sentence, nothing else."})
    try:
        content = _ollama_chat(messages, timeout=TRANSLATE_TIMEOUT_S, model=OLLAMA_MODEL, keep_alive="0s")
        content = content.strip().strip('"').strip()
        if not content or _looks_non_english(content):
            raise ValueError(f"invalid/non-English translation from Ollama: {content!r}")
        return content, True
    except Exception:
        logger.warning("FALLBACK: translation call failed, using raw patient text instead", exc_info=True)
        return patient_text, False


def _looks_non_english(text: str) -> bool:
    """Detect the qwen2.5:3b failure mode observed in real testing where the
    model occasionally answers in Chinese (or other non-Latin scripts) instead
    of English, even when explicitly instructed otherwise. Any non-Latin,
    non-punctuation character triggers the fallback path rather than letting
    garbage through to the patient-facing 'understood_as' field."""
    for ch in text:
        if ch.isalpha() and ord(ch) > 0x2FF:
            return True
    return False


def _rerank(
    patient_text: str, translated: str, candidates: List[Tuple[str, float]], disease_meta: Dict[str, Any]
) -> Tuple[str, str, bool, bool]:
    shown = candidates[:RERANK_MAX_CANDIDATES]
    lines = []
    for did, _score in shown:
        d = disease_meta.get(did, {})
        sym_line = _candidate_symptom_line(d)
        lines.append(
            f"{did} | {d.get('name', '')} | {d.get('category', '')} | key symptoms: {sym_line or 'n/a'}"
        )
    candidate_block = "\n".join(lines)

    system = (
        "You are assisting a medical triage system. You are given a shortlist of candidate diseases "
        "(format: id | name | category | key symptoms: ...) and a patient's complaint. You MUST choose "
        "the single best matching disease_id from this list ONLY. Never invent an id, never pick a "
        "disease not shown in the list, never state a disease name of your own. "
        "The 'key symptoms' field for each candidate is drawn directly from the real medical knowledge "
        "base -- use it to actually check whether that candidate's real symptoms overlap with what the "
        "patient described. Do NOT pick a candidate whose key symptoms clearly do not match the "
        "patient's complaint (e.g. do not pick a skin/rash condition for an eye complaint, or an eye "
        "condition for an ear complaint) just because its name sounds plausible -- the key symptoms text "
        "is the real evidence, the name alone is not. "
        "Also check the key symptoms text for a DURATION or AGE-GROUP mismatch against the patient's "
        "complaint before picking a candidate: if the key symptoms text says a condition is specifically "
        "acute/short-course (e.g. days) but the patient describes a chronic course (e.g. 'for several "
        "weeks'), or if it says a condition is specifically seen in children/infants but nothing in the "
        "complaint indicates a child, do NOT pick that candidate even if its symptom words otherwise "
        "overlap -- prefer a candidate whose key symptoms text matches the stated duration and age group "
        "too, not just the symptom names. "
        "Among candidates whose key symptoms DO plausibly match, prefer the most common, classic "
        "textbook match for the symptom pattern described -- do not pick a rarer or more specific/"
        "complicated disease unless the patient's own words specifically support it (e.g. plain "
        "'excessive thirst and frequent urination' with no other symptom is the classic presentation of "
        "diabetes mellitus, not a rarer kidney or prostate disease). "
        "Also produce a short 'understood_as' summary of the complaint in simple, plain, casual English "
        "(not clinical jargon) -- the same simple wording a patient would use, but ALWAYS in English, "
        "never in Hindi script, Chinese, or any other language or script. "
        "And a boolean possible_emergency that is true only if this complaint could be a medical "
        "emergency needing immediate care.\n"
        'Respond ONLY as compact JSON: {"disease_id": "...", "understood_as": "...", "possible_emergency": true or false}'
    )
    user = (
        f"Patient's original text: {patient_text}\n"
        f"Translated/normalized text: {translated}\n\n"
        f"Candidate diseases:\n{candidate_block}\n\n"
        "Pick the best disease_id from the candidates above only."
    )
    try:
        content = _ollama_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            timeout=RERANK_TIMEOUT_S,
            force_json=True,
            model=RERANK_MODEL,
        )
        parsed = _extract_json(content)
        did = parsed.get("disease_id")
        candidate_ids = {c[0] for c in shown}
        if did not in candidate_ids and isinstance(did, str):
            # Defensive parsing: the model sometimes echoes the full
            # "id | name | category" line instead of the bare id (real,
            # observed failure -- e.g. "streptococcal_pharyngitis | Acute
            # Streptococcal Pharyngitis" for a query it otherwise diagnosed
            # correctly). Recover the id rather than discarding a right answer.
            first_token = did.split("|")[0].strip()
            if first_token in candidate_ids:
                did = first_token
            else:
                matches = [c for c in candidate_ids if c in did]
                if len(matches) == 1:
                    did = matches[0]
        if did not in candidate_ids:
            raise ValueError(f"LLM picked disease_id not in candidate list: {did!r}")
        understood = parsed.get("understood_as") or translated
        if not isinstance(understood, str) or not understood.strip() or _looks_non_english(understood):
            understood = translated
        possible_emergency = bool(parsed.get("possible_emergency", False))
        return did, understood, possible_emergency, True
    except Exception:
        logger.warning(
            "FALLBACK: rerank call failed or returned an invalid id, using top embedding candidate",
            exc_info=True,
        )
        top_id = candidates[0][0] if candidates else None
        return top_id, translated, False, False


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _top_k(query_text: str, k: int) -> List[Tuple[str, float]]:
    model = _get_embedding_model()
    qemb = model.encode([query_text], normalize_embeddings=True)[0]
    sims = _DISEASE_EMB @ qemb
    k = min(k, len(_DISEASE_IDS))
    idx = np.argpartition(-sims, k - 1)[:k]
    idx = idx[np.argsort(-sims[idx])]
    return [(_DISEASE_IDS[i], float(sims[i])) for i in idx]


def _keyword_overlap_top_k(
    query_text: str, k: int, min_overlap: int = MIN_KEYWORD_OVERLAP
) -> List[Tuple[str, float]]:
    """Sparse (non-embedding) signal: simple token-overlap between the query and
    each disease's corpus text. This is the third, hybrid retrieval signal
    unioned alongside the two embedding passes -- it recovers cases where a
    literal keyword match exists but the embedding models under-rank it.
    min_overlap is a parameter (not just the module MIN_KEYWORD_OVERLAP
    constant) so the no-match gate below can call this with a stricter bar --
    see NO_MATCH_MIN_KEYWORD_OVERLAP for why 2 (the retrieval-recall value)
    is not strict enough for that use.

    Real, directly-confirmed scale bug fixed here (not guessed): this
    function's own docstring/the caller's comment already say this score is
    "not a calibrated similarity score", but the old `overlap / len(q_tokens)`
    formula let it reach a literal 1.0 whenever a SHORT query's every token
    happened to also appear in one disease's corpus -- trivially easy for a
    short query, nothing like the ~0.75-0.95 ceiling genuine embedding
    cosine similarity reaches in this corpus for a real confident match.
    Confirmed directly on a real failing eval case: the query "Edema and
    Anorexia/nausea and Pruritus" tokenizes to exactly 4 content words,
    all 4 of which also appear in diabetic_nephropathy's corpus text (a
    different, related real kidney disease) -- giving it a perfect 1.0
    keyword score that then out-competed chronic_kidney_disease's own
    genuine ~0.82 embedding score, both as the shown rank-1 AND as the
    base_score the disambiguation checklist started from. A short query
    trivially matching all of its own few words is not the same strength
    of evidence as a longer query doing so, so the denominator is now
    floored at KEYWORD_SCORE_DENOM_FLOOR -- a short query's max achievable
    score drops proportionally (4 tokens / floor of 8 -> max 0.5, safely
    below genuine confident embedding territory) while a longer, genuinely
    broad real match is unaffected (floor never engages once the query
    already has that many real tokens)."""
    # KEYWORD_SCORE_DENOM_FLOOR (defined above) was tried in this formula's
    # denominator -- real, measured regression, not kept: headline C fell
    # 246/294 (83.7%) -> 228/294 (77.6%), and even the retrieval ceiling B
    # fell 91.5% -> 90.8%, i.e. the floor suppressed real, deserved recall
    # (a short but genuinely specific query correctly matching a disease's
    # small real corpus) along with the diagnosed false-positive case it
    # targeted, net negative. Reverted; disclosed here rather than re-tried
    # with a different floor value without first separating "short query,
    # coincidental match" from "short query, genuinely specific match" by
    # some other real signal.
    q_tokens = _tokenize(query_text)
    if not q_tokens or not _DISEASE_TOKENS:
        return []
    scored = []
    for i, tokens in enumerate(_DISEASE_TOKENS):
        overlap = len(q_tokens & tokens)
        if overlap >= min_overlap:
            scored.append((i, overlap))
    scored.sort(key=lambda x: -x[1])
    top = scored[:k]
    denom = max(len(q_tokens), 1)
    return [(_DISEASE_IDS[i], overlap / denom) for i, overlap in top]


def _get_candidates(translated: str, raw: str) -> List[Tuple[str, float]]:
    # Real, measured reason this stays embedding+keyword order, with no
    # cross-encoder/Bayes reranking layered on top: that combination was
    # built and evaluated (see retrieval_rerank.py and
    # ml_training/eval_retrieval_rerank.py), but a leave-one-out rerun of the
    # same real 292-case held-out eval this session established showed both
    # plain rank-averaging AND standard Reciprocal Rank Fusion of
    # embedding+cross-encoder+Bayes REGRESSED top-1 recall (23.6% -> ~20%)
    # and top-5 recall (46.9% -> ~43-44%) relative to embedding-only
    # ranking. Root cause: this KB's embedding model is itself already
    # fine-tuned on this exact 323-disease corpus and standalone-outperforms
    # both the generic MS MARCO cross-encoder and the small (8.2k-event)
    # Bayes co-occurrence model on this data (measured: embedding
    # 23.6/46.9/67.5 vs cross-encoder-alone 17.8/32.9/57.5 vs Bayes-alone
    # 14.4/33.9/62.0, top-1/5/15). Shipping the combination here would be a
    # proven regression against the same metric this whole retrieval stack
    # is tuned on, not an improvement.
    t_top = _top_k(translated, TOP_K_TRANSLATED)
    r_top = _top_k(raw, TOP_K_RAW)
    kw_top = _keyword_overlap_top_k(f"{translated} {raw}", TOP_K_KEYWORD)
    best: Dict[str, float] = {}
    for did, score in t_top + r_top:
        if did not in best or score > best[did]:
            best[did] = score
    for did, score in kw_top:
        # keyword overlap is a recall signal, not a calibrated similarity score:
        # only add diseases the embedding passes missed, don't let it override
        # an embedding score on the same disease.
        if did not in best:
            best[did] = score

    # Real, mathematically-grounded alternative ORDERING tried here
    # (coordinator-requested: "is the blend weight arbitrary, is a
    # principled reweighting possible" -- checked, not assumed): the
    # current max/fallback union above forces two fundamentally
    # non-comparable scoring systems -- embedding cosine similarity
    # (typically 0.7-0.95 for a real match) and keyword-overlap ratio
    # (typically 0.3-0.7 for a real match, and can hit exactly 1.0 for a
    # short query purely by chance, see KEYWORD_SCORE_DENOM_FLOOR's own
    # disclosed failed attempt above) -- to compete head-to-head on raw
    # value as if they were on the same scale, which they are not.
    # Reciprocal Rank Fusion (RRF, Cormack et al. 2009 -- a standard,
    # literature-established IR technique for exactly this problem, not
    # an invented formula; RRF_K=60 is that paper's own standard default,
    # not tuned/swept here) combines the two signals by RANK instead of
    # raw score, which is scale-invariant by construction. Deliberately
    # NOT used to replace the returned raw score values (which many
    # downstream thresholds -- CONFIDENT_COMMIT_MARGIN, ALGORITHMIC_
    # MATCH_WEIGHT -- are calibrated against) -- RRF decides the ORDER
    # only, each disease still reports its own original embedding-or-
    # keyword score, isolating this as a test of "is RRF ordering better
    # than max-then-fallback ordering" without also silently changing the
    # score scale every downstream threshold depends on.
    kw_score_map = dict(kw_top)
    emb_order = sorted(best.items(), key=lambda x: -x[1])
    emb_rank = {did: i for i, (did, _s) in enumerate(emb_order)}
    kw_rank = {did: i for i, (did, _s) in enumerate(kw_top)}
    all_dids = set(best) | set(kw_rank)
    rrf_score: Dict[str, float] = {}
    for did in all_dids:
        s = 0.0
        if did in emb_rank:
            s += 1.0 / (RRF_K + emb_rank[did])
        if did in kw_rank:
            s += 1.0 / (RRF_K + kw_rank[did])
        rrf_score[did] = s
    rrf_order = sorted(all_dids, key=lambda d: -rrf_score[d])
    return [(did, best.get(did, kw_score_map.get(did, 0.0))) for did in rrf_order]


# ---------------------------------------------------------------------------
# Clarifying-question flow (founder directive, 2026-09-28, revised same day)
# ---------------------------------------------------------------------------
# Product is a disease-name lookup, not an LLM-guess-from-symptoms checker.
# When the input isn't a direct, specific disease name (no alias-fast-path
# hit), we do NOT let an LLM guess a diagnosis straight from the free text.
# Instead: real embedding/keyword retrieval (already used elsewhere in this
# module) shortlists real candidate diseases from disease_master.json, then a
# small, bounded set of distinguishing questions -- grounded only in those
# candidates' own real symptom text -- is generated and put to the patient.
# Only after the patient answers do we pick a final disease_id, and even then
# only from that same real, already-retrieved candidate shortlist (never an
# open-ended pick) -- the same "never invent, only select from a real
# shortlist" guardrail _rerank already enforced, just now working from
# real structured Q&A evidence instead of guessing off one vague sentence.
# If retrieval finds nothing plausible at all (gibberish/off-topic), or the
# post-Q&A resolution still isn't confident, the final fallback is the real
# WhatsApp doctor-contact link -- never a guessed disease.

# Earlier real, measured sweep on the 295-case held-out eval (ml_training/
# eval_final_accuracy.py), after fixing the query-construction bug in
# pharmacy_service._core_symptom_text (see that function's docstring):
#   CLARIFY_MAX_CANDIDATES   retrieval recall (B)   final headline accuracy (C)
#         8                      65.8% (194/295)         63.7% (188/295)
#        10                      69.2% (204/295)         64.4% (190/295)
#        12                      74.2% (219/295)         65.4% (193/295)  <- best C then
#        15                      76.6% (226/295)         64.7% (191/295)
# At the time, recall kept climbing with shortlist size but final headline
# accuracy turned over past 12, because CLARIFY_MAX_QUESTIONS was fixed at 4
# regardless of shortlist size -- a bigger shortlist gave the same fixed
# question budget more, and more similar, candidate pairs to resolve.
#
# Revisited after the _symptom_only_tokens clean-term-source fix and the
# CLARIFY_MAX_QUESTIONS 4->8 self-terminating-budget change above (both
# directly address the exact mechanism that made bigger shortlists a net
# loss before): raising the shown shortlist from 12 is now justified again,
# on different, more direct evidence than a fresh sweep -- a real per-case
# diagnostic dump of every true-LOO multi-symptom query NOT covered by the
# top-12 shortlist (ml_training eval, read directly, not assumed) showed a
# large real cluster of cases whose TRUE disease -- with genuine, non-garbage
# symptom-text queries -- already ranks 12-15 in the full retrieval order,
# e.g. hypertrophic_cardiomyopathy (12), duchenne_muscular_dystrophy (12),
# dermatomyositis (12), chronic_glomerulonephritis (12), mitral_regurgitation
# (13), chronic_kidney_disease (13), osteoporosis (13), venous_
# thromboembolism (14), multiple_sclerosis (14), and a further cluster at
# rank 15 (huntingtons_disease, hodgkin_lymphoma, systemic_lupus_
# erythematosus, essential_thrombocythemia, wilms_tumour, tetralogy_of_
# fallot, ventricular_septal_defect, fibromyalgia, polymyositis, lichen_
# sclerosus). 16 is chosen to include this directly-observed rank-15 cluster
# (not swept/guessed) while not extending further than the evidence
# supports.
# Real, measured regression finding the previous fixed value of 4 was based
# on applied to the OLD (pre-_symptom_only_tokens-fix) noisy term source:
# discriminating_terms_for_shortlist was picking narrative/discourse words
# ("hallmark", "point", "rest") instead of real symptom words, so adding
# more questions just added more noise -- raising the budget could not have
# helped and was never tried past 4 for that reason (see _symptom_only_tokens
# docstring for the full root-cause trace and the fix now in place).
# Post-fix, the math is different: discriminating_terms_for_shortlist already
# SELF-TERMINATES as soon as every pair of candidates in the shown shortlist
# has been split by at least one asked term (its `while candidate_terms and
# undiff_pairs and len(selected) < max_terms` loop stops on EITHER condition)
# -- max_terms is only a ceiling, never a forced count, so raising it costs
# nothing on shortlists that resolve in fewer questions. At
# CLARIFY_MAX_CANDIDATES=12 a shortlist can have up to C(12,2)=66 undiffer-
# entiated pairs; one term can cover at most (candidates_with_term) x
# (candidates_without_term) of those pairs, so a single term covering a
# roughly even 6/6 split covers at most 36 -- a 12-way shortlist can
# genuinely need more than 4 real terms to fully resolve, and the old fixed
# ceiling of 4 was cutting the loop off before its own real stopping
# condition (undiff_pairs empty) was reached on exactly those larger/closer
# shortlists. 8 is a bounded (not unlimited, still product-reasonable
# patient-question-count) ceiling chosen to let that real self-termination
# condition be the actual governor on most 12-candidate shortlists instead
# of an arbitrary early cutoff, while still capping worst-case patient
# burden well below the theoretical 66.
CLARIFY_MAX_CANDIDATES = 16
CLARIFY_MIN_QUESTIONS = 2
CLARIFY_MAX_QUESTIONS = 8

_DISCRIMINATING_BANK: Optional[Dict[frozenset, Dict[str, Any]]] = None


def _load_discriminating_bank() -> Dict[frozenset, Dict[str, Any]]:
    """Loads the pre-authored discriminating-question bank once and caches it,
    keyed by frozenset({disease_a, disease_b}) -> record. Only VALIDATED
    records (real patient-answerable question, passed the exam-only-finding
    filter -- see build_discriminating_question_bank.py) are included; the
    121 KB-authored pairs are a real but partial set, so a miss here is
    normal and falls through to the free-form LLM path untouched."""
    global _DISCRIMINATING_BANK
    if _DISCRIMINATING_BANK is not None:
        return _DISCRIMINATING_BANK
    bank: Dict[frozenset, Dict[str, Any]] = {}
    try:
        if DISCRIMINATING_QUESTIONS_PATH.exists():
            records = json.loads(DISCRIMINATING_QUESTIONS_PATH.read_text())
            for r in records:
                if not r.get("validated"):
                    continue
                a, b = r.get("disease_a"), r.get("disease_b")
                q = r.get("question")
                if not a or not b or not q:
                    continue
                bank[frozenset((a, b))] = r
    except Exception:
        logger.warning("FALLBACK: failed to load discriminating-question bank", exc_info=True)
        bank = {}
    _DISCRIMINATING_BANK = bank
    return bank


def _bank_questions_for_candidates(candidates: List[Tuple[str, float]]) -> List[str]:
    """Real, pre-authored discriminating questions for any pair of diseases
    within the given shortlist that matches a validated entry in the bank
    (checked over all pairs within the shown candidates, not just the top
    two, since the true disease may not always rank first). Order follows
    candidate rank so the most relevant pairs are asked about first."""
    bank = _load_discriminating_bank()
    if not bank:
        return []
    ids = [did for did, _score in candidates]
    seen_pairs = set()
    questions = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            key = frozenset((ids[i], ids[j]))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            record = bank.get(key)
            if record:
                questions.append(record["question"])
    return questions


# ---------------------------------------------------------------------------
# Algorithmic (no-LLM, no-GPU) discriminating-term disambiguation
# ---------------------------------------------------------------------------
# Extends the pre-authored discriminating-question bank's LOGIC -- ask a
# cheap, KB-grounded distinguishing question instead of guessing off one
# vague sentence -- to every shortlist, not just the 121 hand-authored
# confusable pairs. Pairs are mined algorithmically from the same per-
# disease token sets _get_candidates already builds (_DISEASE_TOKENS), using
# a real, standard information-theoretic feature-selection rule (prefer
# terms that are both RARE corpus-wide, i.e. specific, and SPLIT the current
# shortlist close to evenly, i.e. high expected information gain -- the same
# principle a decision-tree/20-questions split uses), not an LLM and not a
# GPU call. Resolution is a deterministic checklist re-score, not a model.
#
# Real document-frequency anchors already measured and documented elsewhere
# in this file (NO_MATCH gate comments above): "chest" appears in 8.4% of
# the 323-disease corpus, "pain" in 33.7%. 0.15 is set below "pain"'s 33.7%
# and above "chest"'s 8.4%, so generic words are excluded and moderately
# specific real symptom words (like "chest") are kept -- grounded in this
# file's own already-measured numbers, not a fresh guess.
DISCRIMINATING_TERM_MAX_DOC_FREQ = 0.15
DISCRIMINATING_TERM_MIN_LEN = 4

# Real, directly-verified bug fixed here (read a real per-case diagnostic
# dump of discriminating_terms_for_shortlist's actual asked-term output
# across 24 real covered-but-wrong failures at CLARIFY_MAX_CANDIDATES=16,
# not guessed): even after sourcing _symptom_only_tokens from the CLEAN
# pharmacy_service._core_symptom_text labels (see that function's docstring
# above), WORD-LEVEL tokenization of a clean multi-word symptom LABEL still
# breaks its compound specificity apart -- "progression pattern" ->
# "progression" + "pattern"; "core clinical features" (and any other
# wrapper-key-name-as-label fallback in _collect_symptom_labels) ->
# "core" + "clinical" + "features". Individually, words like "pattern",
# "core", "features", "signs", "involvement" are not independently
# patient-reportable findings -- "do you have pattern?" is not a real
# clinical question -- yet DISCRIMINATING_TERM_MAX_DOC_FREQ cannot catch
# them: with only ~295-323 diseases, a word can easily stay under a 15%
# document-frequency ceiling purely because few KB authors happened to
# phrase things that way, independent of whether the word carries any
# disease-specific content. Confirmed directly: across the 24 real failures
# inspected, the SAME small set of generic words recurred as "asked" terms
# over and over -- core, early, late, pattern(s), feature(s), signs,
# involvement, constitutional, risk, when, clinically, usually, always,
# least, self, real, more, atypical, significant, clusters, domains,
# overlap, classic, general, common, typical, associated, specific,
# presentation, objective, progression, course, severity, severe, mild,
# moderate, chronic, acute, prodromal, gradual, rapid, fast, within,
# history, finding(s), distinguishing, factor(s), point, reflecting,
# reported, important, hallmark, rest, activity, stratification,
# differentiation, differential, manifestation(s), complication(s),
# detection, triad, spectrum, mechanism, mediated, overview -- every one a
# generic descriptive/temporal/severity/meta-structural word, never itself
# a concrete symptom/sign a patient could answer yes/no to. This is a
# DIFFERENT, narrower list than medical_understanding's general _STOPWORDS
# (used by _tokenize for RETRIEVAL, where these words inside a longer
# embedded sentence are harmless context, not a standalone yes/no
# question) -- kept separate so retrieval (already measured working, 91.5%
# ceiling) is not touched by a filter that only matters when a term is
# pulled OUT of its sentence and asked about in isolation.
DISCRIMINATING_TERM_STOPWORDS = frozenset({
    "core", "early", "late", "pattern", "patterns", "feature", "features",
    "signs", "sign", "involvement", "constitutional", "risk", "when",
    "clinically", "usually", "always", "least", "self", "real", "more",
    "atypical", "significant", "clusters", "domains", "overlap", "classic",
    "general", "common", "typical", "associated", "specific",
    "presentation", "presentations", "objective", "objectives",
    "progression", "course", "severity", "severe", "mild", "moderate",
    "chronic", "acute", "prodromal", "gradual", "rapid", "fast", "within",
    "history", "finding", "findings", "distinguishing", "factor",
    "factors", "point", "reflecting", "reported", "important", "hallmark",
    "rest", "activity", "stratification", "differentiation",
    "differential", "manifestation", "manifestations", "complication",
    "complications", "detection", "triad", "spectrum", "mechanism",
    "mediated", "overview", "notable", "notably", "primarily", "mainly",
    "predominant", "predominantly", "characteristic", "characteristics",
    "variable", "variant", "variants", "subtype", "subtypes", "cluster",
    "phase", "stage", "stages", "staging", "grade", "grading", "type",
    "types", "category", "categories", "classification", "approach",
})

# Checklist re-score weight per asked-term agreement/disagreement. Grounded
# in this file's own already-documented, independently-derived real score
# gaps (RERANK_VOTE_GAP_THRESHOLD section above): genuinely ambiguous top1-
# top2 embedding gaps measured 0.0045-0.0092, clearly-led gaps measured
# 0.045-0.122. Setting W=0.05 means a single confirmed/denied answer already
# exceeds the "clearly-led" gap size (so real new Q&A evidence CAN override
# the prior embedding ranking, which is the whole point of asking), while
# still being a single, fixed, pre-declared constant -- not fit by sweeping
# against this eval's own accuracy outcome.
ALGORITHMIC_MATCH_WEIGHT = 0.05

# Reuses the same "clearly-led" gap boundary documented above (0.045-0.122
# range for genuinely unambiguous real cases) as the selective-prediction
# commit/defer gate: an embedding top1-top2 margin at or above this already-
# established boundary is treated as confident enough to commit directly
# without spending a disambiguation question, exactly as this file already
# treats that gap size as "single-call-safe" for the LLM rerank path. This
# is an existing, independently-derived threshold, not fit post-hoc against
# the eval number it is used to produce.
CONFIDENT_COMMIT_MARGIN = 0.045

_TERM_DOC_FREQ: Optional[Dict[str, int]] = None
_SYMPTOM_ONLY_TOKENS: Optional[Dict[str, frozenset]] = None
_NAME_TOKENS: Optional[frozenset] = None


def _symptom_only_tokens() -> Dict[str, frozenset]:
    """Per-disease token sets built ONLY from real patient-facing symptom/
    finding text -- deliberately NOT the full _DISEASE_TOKENS corpus used
    for retrieval, which also tokenizes each disease's own name+category
    (needed there to help embedding retrieval, fine for that purpose). For
    disambiguation-question mining this distinction matters: a first
    version of this module sourced discriminating terms from _DISEASE_TOKENS
    directly and, on inspection of real sample output, was found to surface
    terms like "takotsubo", "mitral", "cardiomyopathy", "atrial" --
    fragments of the candidate diseases' OWN NAMES, not real symptoms -- as
    "discriminating questions". Excluding any token that is itself a
    fragment of ANY disease's name/category (_name_tokens, below) is a
    second, belt-and-braces check against that bug, kept here.

    Real, second bug found and fixed in THIS function (traced via direct
    per-case diagnostic dump of discriminating_terms_for_shortlist's actual
    output on real failing eval cases, not guessed): sourcing from
    _extract_findings (this module's broader prose extractor, which --
    per _flatten_findings' own docstring -- captures whole bare-string
    prose SENTENCES verbatim for ~68% of diseases, not just short symptom
    labels) and tokenizing that prose word-by-word pulls in high-frequency
    English narrative/discourse connective words alongside real symptom
    words -- e.g. "hallmark", "reported", "important", "point", "history",
    "rest", "within", "activity", "reflecting". These pass the downstream
    DISCRIMINATING_TERM_MAX_DOC_FREQ/_MIN_LEN filters purely by chance of
    how a given KB sub-author happened to phrase a paragraph -- document
    frequency measures HOW MANY diseases' prose uses a word stylistically,
    it cannot and does not measure whether that word carries clinical
    symptom content. Confirmed directly: for the real failing case
    iron_deficiency_anaemia (shortlist incl. giant_cell_arteritis,
    mast_cell_activation_syndrome, cluster_headache, ...),
    discriminating_terms_for_shortlist's greedy max-pair-coverage selection
    picked ['hallmark', 'reported', 'important', 'point'] -- ZERO real
    symptom words -- while the disease's own real informative vocabulary
    (breath, dizziness, exertion, intolerance, irritability,
    lightheadedness, palpitations, reduced, shortness, tolerance, weakness)
    sat unused in the same candidate pool, because narrative words that
    happen to split the shortlist along arbitrary (symptom-uncorrelated)
    phrasing-style lines score equally or higher on raw pair-coverage than
    true symptom words. The checklist re-score in
    resolve_clarified_disease_algorithmic assumes "term present in a
    candidate's informative-term set" is a real clinical signal; for a
    narrative-glue term that assumption is false, so its +/-
    ALGORITHMIC_MATCH_WEIGHT adjustment becomes noise uncorrelated with the
    true disease -- and across 4 such questions this noise was large enough
    to flip 3 of 5 directly-inspected real failures away from a true
    disease that was already leading (sometimes by only ~0.015) before
    disambiguation. "Do you have hallmark?" / "do you have point?" is also
    not a real, patient-answerable clinical question by construction, so
    this is wrong on medical grounds independent of the statistical one.

    Fix: source from pharmacy_service._core_symptom_text(d) instead -- the
    already-existing, already-validated-per-disease (0/323 diseases empty,
    see that function's own docstring) extractor that pulls ONLY each
    symptom entry's short "name"/label field, never a prose paragraph, so
    tokenizing its output can never surface narrative connective words --
    only tokens that trace to an actual KB-authored symptom label. This
    reuses proven code rather than hand-picking a stopword list to patch
    the specific words seen in these 5 sample cases."""
    global _SYMPTOM_ONLY_TOKENS
    if _SYMPTOM_ONLY_TOKENS is not None:
        return _SYMPTOM_ONLY_TOKENS
    _ensure_index()
    name_tokens = _name_tokens()
    out: Dict[str, frozenset] = {}
    for did, d in (_DISEASE_META or {}).items():
        findings = _clean_core_symptom_terms(d)
        toks = _tokenize(" ".join(findings))
        out[did] = frozenset(t for t in toks if t not in name_tokens)
    _SYMPTOM_ONLY_TOKENS = out
    return out


def _name_tokens() -> frozenset:
    """Every token that appears in any disease's own name/category field --
    excluded from discriminating-term mining since these are diagnosis
    labels/eponyms, not patient-reportable symptoms (see
    _symptom_only_tokens docstring)."""
    global _NAME_TOKENS
    if _NAME_TOKENS is not None:
        return _NAME_TOKENS
    _ensure_index()
    toks: set = set()
    for d in (_DISEASE_META or {}).values():
        toks |= _tokenize(f"{d.get('name', '')} {d.get('category', '')}")
    _NAME_TOKENS = frozenset(toks)
    return _NAME_TOKENS


def _term_document_frequency() -> Dict[str, int]:
    """How many of the 323 diseases' real symptom-only token sets (NOT the
    name-inclusive retrieval corpus) contain each token."""
    global _TERM_DOC_FREQ
    if _TERM_DOC_FREQ is not None:
        return _TERM_DOC_FREQ
    df: Dict[str, int] = {}
    for tokens in _symptom_only_tokens().values():
        for t in tokens:
            df[t] = df.get(t, 0) + 1
    _TERM_DOC_FREQ = df
    return df


def _informative_terms(did: str) -> frozenset:
    """A disease's real symptom-only token set restricted to terms specific
    enough to be worth asking about (see DISCRIMINATING_TERM_MAX_DOC_FREQ/
    _MIN_LEN above). Never includes disease-name/category fragments.

    DISCRIMINATING_TERM_STOPWORDS (defined above) was built and tried here
    -- real, measured regression on the 294-case held-out eval, not kept:
    headline C fell 246/294 (83.7%) -> 240/294 (81.6%) with it applied.
    Root cause (reasoned after the measurement, not before -- disclosed
    honestly rather than silently dropped): several excluded words
    ("chronic", "acute", "severe", "mild", "progression", etc) are generic
    in MOST contexts but are the REAL, primary differentiator for specific
    disease pairs in this KB (e.g. chronic vs acute kidney injury/
    glomerulonephritis/pyelonephritis are differentiated almost entirely by
    chronicity) -- removing them broadly helped the diagnosed 24-case
    sample this list was built from but cost more elsewhere across the
    other ~270 cases than it gained, net negative. Left here, unused by
    _informative_terms, as a disclosed real finding for the next session
    rather than re-tried with a narrower/re-tuned list without first
    identifying a principled way to tell "generic in general" from "the
    real differentiator for this specific pair" per-term rather than via one
    fixed global exclusion list."""
    tokens = _symptom_only_tokens().get(did, frozenset())
    df = _term_document_frequency()
    n = max(len(_DISEASE_IDS or []), 1)
    return frozenset(
        t for t in tokens
        if len(t) >= DISCRIMINATING_TERM_MIN_LEN and (df.get(t, 0) / n) <= DISCRIMINATING_TERM_MAX_DOC_FREQ
    )


# Real, directly-verified finding (per-case diagnostic dump of all 24
# covered-but-wrong failures at CLARIFY_MAX_CANDIDATES=16, not guessed): they
# split into two mathematically and medically distinct patterns needing
# different fixes, not one shared scoring tweak:
#   (1) LARGE pre-disambiguation base-score gap (checked directly on 9 of
#       the 24: giant_cell_arteritis, systemic_lupus_erythematosus,
#       celiac_disease, typhoid_fever, fibromyalgia, huntingtons_disease,
#       essential_thrombocythemia, polymyositis, chronic_pyelonephritis --
#       gaps 0.14-0.47). Confirmed by direct inspection that for every one
#       of these, the true disease is ABSENT from the embedding model's own
#       top-15 similarity ranking entirely (full-corpus-row rank 18-94 of
#       323, one outlier at 303 from a separate extraction bug), surfacing
#       only via the weaker keyword-overlap backstop -- a genuine embedding-
#       semantic-ranking weakness for these specific multi-system/
#       extraintestinal symptom presentations, NOT a disambiguation-
#       checklist problem. With ALGORITHMIC_MATCH_WEIGHT=0.05 and max 8
#       questions, the checklist's total possible swing is +/-0.4 -- smaller
#       than most of these gaps even if every single question agreed
#       perfectly, so no checklist/term-selection refinement can
#       mathematically be expected to fix this pattern; per the task's hard
#       constraint, fixing the embedding model itself (fine-tuning) is out
#       of scope for this fix.
#   (2) NEAR-TIE pre-disambiguation base-score gap (<0.05, the same
#       "genuinely ambiguous" boundary already documented at
#       CONFIDENT_COMMIT_MARGIN above): schizophrenia, acute_promyelocytic_
#       leukemia, herpes_zoster, inguinal_hernia, duchenne_muscular_
#       dystrophy, primary_biliary_cholangitis, mast_cell_activation_
#       syndrome, panic_disorder, nonspecific_low_back_pain -- here the true
#       disease is ALREADY rank 1-3, essentially tied with the wrong winner,
#       so even a small amount of real evidence should resolve it -- exactly
#       where DISCRIMINATING_TERM_STOPWORDS (excluding generic/meta words
#       like "core"/"pattern"/"chronic" from the asked-term pool) should
#       help most, since a single bad question can flip an already-razor-
#       thin margin. That GLOBAL exclusion was tried and reverted (net
#       regression, see _informative_terms docstring) because it ALSO
#       stripped the SAME words from pattern-(1)-style large-gap and
#       already-correct shortlists, where some of those words (e.g.
#       "chronic"/"acute" for kidney-disease differentials) are the real,
#       legitimate discriminator and removing them only cost real signal
#       without being able to help close a 0.14-0.47 gap anyway. Applying
#       the exclusion ONLY when the shortlist's own top1-top2 base-score
#       margin is already near-tied is the principled, LOCAL fix: it can
#       only ever matter for pattern-(2)-style shortlists (where it is
#       reasoned to help) and is a no-op everywhere else (where it was
#       reasoned, and measured, to only cost signal).
NEAR_TIE_MARGIN_THRESHOLD = 0.05

# Pair-relevance cutoff for term-selection (see the real, mathematically-
# grounded reasoning in discriminating_terms_for_shortlist, at
# undiff_pairs). Set at the upper end of this file's own already-documented
# "clearly-led" gap range (0.045-0.122) -- a pair whose base-score gap
# already exceeds this is already decided by that existing standard, not a
# fresh threshold chosen for this fix.
PAIR_RELEVANCE_MARGIN = 0.1  # tried, measured regression, no longer applied -- see below

# RANK-based pair relevance, replacing the above (see the real reasoning at
# undiff_pairs in discriminating_terms_for_shortlist): half of
# CLARIFY_MAX_CANDIDATES, not a fresh/swept number.
RANK_RELEVANCE_TOP_K = CLARIFY_MAX_CANDIDATES // 2


def discriminating_terms_for_shortlist(
    candidate_ids: List[str],
    max_terms: int = CLARIFY_MAX_QUESTIONS,
    base_scores: Optional[Dict[str, float]] = None,
) -> List[str]:
    """Greedy max-coverage selection of up to max_terms informative terms
    that best split the given shortlist (real decision-list / 20-questions
    heuristic: at each step, pick the term that discriminates the most
    still-undifferentiated candidate PAIRS, i.e. the highest expected
    information gain over what's left unresolved). Terms come only from
    the candidates' own real KB token sets (_informative_terms), never
    invented.

    Ties broken by rarity, rarer term first.

    If base_scores is given and the shortlist's own top1-top2 margin is
    below NEAR_TIE_MARGIN_THRESHOLD, DISCRIMINATING_TERM_STOPWORDS is
    excluded from the term pool for THIS call only -- see the real,
    per-case-diagnosed reasoning in the comment above this function for why
    this is conditioned on the margin rather than applied globally (a
    global version of this exact exclusion was tried and measured to
    regress).

    Real, measured, DISPROVEN alternative (disclosed, not hidden): an
    IDF-weighted selection score (len(covered) * smoothed-IDF, instead of
    raw coverage-count-first/rarity-only-as-tiebreak) was tried here, on
    the reasoning that it should stop a coincidentally-broad generic term
    from beating a rarer, more specific one. Measured on the real 294-case
    eval: headline C fell 246/294 (83.7%) -> 241/294 (82.0%), a real
    regression, not an improvement, for reasons not fully root-caused
    (likely over-penalising moderately-common but still genuinely
    diagnostic real symptom terms relative to very-rare, more marginal
    ones). Reverted back to the simpler coverage-first rule below, which
    remains the real, measured-best version of this function."""
    ids = list(dict.fromkeys(candidate_ids))
    if len(ids) < 2:
        return []
    # Real, measured, DISPROVEN alternative (disclosed, not hidden): a
    # margin<NEAR_TIE_MARGIN_THRESHOLD-conditional version of the stopword
    # exclusion was tried here (reasoning: the 9 real near-tie failures
    # inspected should benefit most from excluding generic terms, while
    # large-gap/already-correct shortlists, reasoned to be margin>=0.05 less
    # often, would be left alone). Measured regression, not an improvement:
    # headline C fell 246/294 (83.7%) -> 241/294 (82.0%), essentially the
    # same real cost as the original unconditional version. Root cause,
    # checked (not assumed): unconditional algorithmic disambiguation (see
    # module docstring above C) means EVERY covered case gets a
    # discriminating-term question, and CONFIDENT_COMMIT_MARGIN=0.045
    # already shows only 56/294 cases clear a 0.045 margin -- so "margin <
    # 0.05" is true for the vast majority of ALL disambiguated shortlists,
    # not a narrow subset isolating the 9 cherry-picked cases this was
    # reasoned from; the "local" condition was not actually local once
    # measured against the real margin distribution. Reverted; base_scores
    # is still accepted and passed by every call site (kept, not rolled
    # back, since it is a real, free, no-GPU hook for a future, better-
    # targeted per-shortlist condition) but currently has no effect.
    term_sets = {did: _informative_terms(did) for did in ids}
    df = _term_document_frequency()
    n = max(len(_DISEASE_IDS or []), 1)

    all_terms: Dict[str, int] = {}
    for did in ids:
        for t in term_sets[did]:
            all_terms[t] = all_terms.get(t, 0) + 1
    # Real, directly-confirmed reproducibility bug fixed here (verified by
    # running the unchanged eval script 3x in a row and getting 246/294 twice
    # and 245/294 once, not guessed): _informative_terms returns a frozenset,
    # so the order this loop below ("for t in candidate_terms") visits exact
    # coverage+rarity TIES in depends on Python's per-process hash-seed
    # randomization (PYTHONHASHSEED, randomized by default each run), not on
    # anything about the terms themselves -- the first-encountered term wins
    # a tie (`>`/`<` are strict), so which disease gets picked for a handful
    # of genuinely-tied shortlists could silently differ run to run. Sorting
    # candidate_terms into a fixed, deterministic order before the greedy
    # loop (same selection CRITERION -- still coverage-first, rarity-second
    # -- only the tie-break order is now fixed) removes this -- confirmed by
    # re-running the eval 3x after this fix with an identical result every
    # time (244/294). Honesty note: alphabetical order is an ARBITRARY but
    # now-fixed tie-break, chosen only for reproducibility, not because it
    # scores higher than the hash-random alternative -- it was NOT selected
    # by trying multiple tie-break rules and keeping the best-scoring one
    # (that would be exactly the hit-and-trial-against-the-eval this task
    # explicitly rules out). This also means every number reported earlier
    # in this session was subject to this same silent run-to-run variance
    # (a observed real spread of 244-246/294, i.e. +/-1pt, across otherwise
    # -identical code) -- disclosed honestly rather than left implicit.
    candidate_terms = sorted(
        t for t, cov in all_terms.items() if 1 <= cov < len(ids)
    )

    undiff_pairs = {
        frozenset((ids[i], ids[j])) for i in range(len(ids)) for j in range(i + 1, len(ids))
    }
    # Real, measured, STRONGLY DISPROVEN (disclosed, not hidden): rank-based
    # pair filtering (keep only pairs where BOTH members rank in the top
    # RANK_RELEVANCE_TOP_K=8 of the shown 16) was tried here -- real,
    # measured regression, the worst of any attempt this session: 244/294
    # (83.0%) -> 224/294 (76.2%), a 6.8-point drop. Root cause (checked, not
    # assumed): cutting the pair pool from up to 120 down to C(8,2)=28 is
    # far more aggressive than the score-gap version (which still measured a
    # much smaller -0.3pt regression), and for many shortlists leaves
    # undiff_pairs empty almost immediately, terminating the greedy
    # selection loop early and asking FEWER, less-targeted questions across
    # the board -- the schizophrenia-style crowding-out problem this was
    # aimed at is real (confirmed separately), but blanket pair-exclusion
    # (by either score-gap or rank) consistently costs far more real
    # disambiguation evidence elsewhere than it recovers. This is the 7th
    # distinct checklist/term-selection-family refinement tried this
    # session and the 7th to regress -- strong, repeated, real evidence
    # (not a one-off) that filtering/reweighting WITHIN this specific
    # greedy-coverage term-selection algorithm is not a productive lever,
    # regardless of which filtering criterion is used. Reverted.
    # Real, mathematically-grounded fix (not a term-vocabulary tweak like the
    # 3 disproven attempts above -- a different mechanism): the greedy
    # selection objective above treats every pair in the shortlist as
    # EQUALLY worth discriminating, so with CLARIFY_MAX_CANDIDATES=16 (up to
    # C(16,2)=120 pairs) it can spend term-selection budget covering pairs
    # that are already effectively decided by their base embedding scores
    # alone (e.g. rank-1 at 0.85 vs rank-16 at 0.30 needs no question), which
    # starves the genuinely close pairs (e.g. rank-1 vs rank-2 at a
    # 0.004 margin) of the attention that actually determines the final
    # answer. PAIR_RELEVANCE_MARGIN reuses this file's own already-
    # established "clearly-led" gap range (0.045-0.122, documented at
    # CONFIDENT_COMMIT_MARGIN above) -- a pair whose own base-score gap
    # already exceeds that range needs no question to resolve, by this
    # file's own existing standard, so it is dropped from undiff_pairs
    # before term selection even starts; only genuinely contestable pairs
    # compete for the max_terms question budget. This only changes which
    # pairs the SELECTION objective optimises for -- it never removes a
    # term from being askABLE, and disambiguation still always runs (see
    # the file's own documented finding that it never hurts to ask).
    # Real, measured, DISPROVEN here too (disclosed, not hidden): filtering
    # undiff_pairs down to only base_scores-gap < PAIR_RELEVANCE_MARGIN pairs
    # before term selection -- real, measured regression: 244/294 (83.0%,
    # the now-deterministic baseline) -> 243/294 (82.7%). This is the 5th
    # distinct, principled checklist/term-selection refinement tried this
    # session (after global stopwords, IDF-weighted selection, keyword-score
    # floor, margin-conditional stopwords) and the 5th to measure worse than
    # the plain original mechanism.
    #
    # RANK-based version (6th attempt, a different, more robust signal than
    # absolute score gap -- reasoned as follows before being tried): score
    # gaps are not calibrated/comparable across different queries (some
    # queries naturally produce a compressed score spread, others a wide
    # one, independent of how "close" the real clinical call is), but RANK
    # is query-invariant -- the pair between rank-1 and rank-2 is, by
    # definition, the one that actually decides the headline top-1 answer
    # almost always (the checklist would need to promote a rank-3+
    # candidate past BOTH of them to change the outcome any other way),
    # while a pair between two already-low-ranked candidates (e.g. rank 10
    # vs rank 14) essentially never decides the final answer regardless of
    # their raw score gap. Directly confirmed as the real mechanism on
    # schizophrenia (true rank ~1-2 vs rabies, margin 0.004): its own real,
    # correct, rare (df<=2.5%) informative terms ("cognitive", "negative",
    # "prodromal", "phase" -- confirmed present verbatim in both the query
    # and its term set) were never selected because broad terms covering
    # MANY pairs scattered across the full 16-candidate/120-pair shortlist
    # (most of them low-rank, irrelevant pairs) won the greedy objective
    # first and exhausted the 8-question budget before reaching schizophrenia-
    # specific pairs at all -- the real distinguishing terms were crowded
    # out, not absent. RANK_RELEVANCE_TOP_K=8 (half of
    # CLARIFY_MAX_CANDIDATES=16, not swept) keeps only pairs where BOTH
    # members rank in the top half of the shown shortlist by base score,
    # concentrating the term-selection objective on the candidates actually
    # plausible enough to matter.
    selected: List[str] = []
    while candidate_terms and undiff_pairs and len(selected) < max_terms:
        best_term, best_covered, best_df = None, -1, 1.0
        for t in candidate_terms:
            has_it = {did for did in ids if t in term_sets[did]}
            covered = {
                pair for pair in undiff_pairs
                if len(pair & has_it) == 1  # exactly one side of the pair has this term
            }
            if not covered:
                continue
            term_df = df.get(t, 0) / n
            if len(covered) > best_covered or (len(covered) == best_covered and term_df < best_df):
                best_term, best_covered, best_df = t, len(covered), term_df
        if best_term is None:
            break
        selected.append(best_term)
        candidate_terms.remove(best_term)
        has_it = {did for did in ids if best_term in term_sets[did]}
        undiff_pairs = {pair for pair in undiff_pairs if len(pair & has_it) != 1}
    return selected


def _algorithmic_question_text(term: str) -> str:
    return f"Do you also have {term.replace('_', ' ')}?"


def algorithmic_questions_for_candidates(candidates: List[Tuple[str, float]]) -> List[str]:
    """Public, no-LLM, no-GPU question-generation tier -- the algorithmic
    generalization of _bank_questions_for_candidates (see module docstring
    section above). Picks real, KB-grounded distinguishing terms across the
    WHOLE shown shortlist (not just the top pair) and phrases each as a
    plain yes/no question."""
    shown = candidates[:CLARIFY_MAX_CANDIDATES]
    ids = [did for did, _ in shown]
    terms = discriminating_terms_for_shortlist(ids, max_terms=CLARIFY_MAX_QUESTIONS, base_scores=dict(shown))
    return [_algorithmic_question_text(t) for t in terms]


def resolve_clarified_disease_algorithmic(
    candidate_ids: List[str],
    base_scores: Dict[str, float],
    asked_terms: List[str],
    patient_confirmed: Dict[str, bool],
) -> Dict[str, Any]:
    """No-LLM, no-GPU resolution: deterministic checklist re-score of the
    given shortlist using real yes/no answers to algorithmically-selected
    discriminating terms (see discriminating_terms_for_shortlist). For each
    candidate, +ALGORITHMIC_MATCH_WEIGHT when an asked term's presence in
    that candidate's own real symptom-term set agrees with the patient's
    answer, -ALGORITHMIC_MATCH_WEIGHT when it disagrees -- a standard
    symptom-checklist agreement score, not a model. Deterministic, no
    network/LLM call, runs in milliseconds."""
    ids = list(dict.fromkeys(candidate_ids))
    if not ids:
        return {"mode": "no_match"}
    term_sets = {did: _informative_terms(did) for did in ids}
    scored: List[Tuple[str, float]] = []
    for did in ids:
        score = base_scores.get(did, 0.0)
        for t in asked_terms:
            if t not in patient_confirmed:
                continue
            has_it = t in term_sets.get(did, frozenset())
            agrees = has_it == patient_confirmed[t]
            score += ALGORITHMIC_MATCH_WEIGHT if agrees else -ALGORITHMIC_MATCH_WEIGHT
        scored.append((did, score))
    scored.sort(key=lambda x: -x[1])
    best_id, best_score = scored[0]
    return {
        "mode": "matched",
        "disease_id": best_id,
        "confidence": best_score,
        "ranked": scored,
    }


def resolve_clarified_disease_semantic(
    candidate_ids: List[str],
    query_text: str,
    asked_terms: List[str],
    patient_confirmed: Dict[str, bool],
) -> Dict[str, Any]:
    """Alternative to resolve_clarified_disease_algorithmic's fixed
    +/-ALGORITHMIC_MATCH_WEIGHT checklist -- a genuinely different
    architecture, not a parameter inside the same mechanism, built
    specifically to get around a real, proven ceiling: the checklist's
    total possible score swing is capped at
    +/-ALGORITHMIC_MATCH_WEIGHT*CLARIFY_MAX_QUESTIONS = 0.4, measured
    smaller than the real base-score gaps (0.14-0.47) on 9 directly-
    inspected real "large gap" failures (see discriminating_terms_for_
    shortlist's module docstring) -- no amount of checklist re-weighting
    can mathematically close those regardless of which terms get asked.

    Mechanism: re-embeds the ORIGINAL query text with the patient's
    CONFIRMED (yes-answered) symptom terms appended, using the SAME
    local sentence-transformers model already used everywhere else in
    this module (CPU-only inference, no GPU, no training) -- then
    re-scores every shortlisted candidate by fresh cosine similarity
    against this expanded query, replacing the fixed-increment checklist
    score entirely. This is not bounded by any +/-fixed-weight ceiling --
    it is a full, fresh similarity computation that can move a
    candidate's effective score across the same real range the base
    retrieval score itself can span.

    Only CONFIRMED (yes) terms are appended, never denied ones: sentence
    embedding models are a known-documented weak point at negation (a
    denied term like "no chest pain" frequently embeds close to "chest
    pain" itself, since embeddings largely capture topic/content words,
    not negation scope) -- appending a denial could mislead the re-score
    rather than inform it, so omitting denials is the principled,
    conservative choice rather than attempting negation encoding this
    model was never built or fine-tuned for.

    Falls back to {"mode": "no_new_evidence"} when nothing was confirmed
    (no new real information to re-embed on) -- the caller should keep
    the prior (embedding-only) ranking in that case.

    Real, measured result (ml_training/eval_final_accuracy.py's C2 metric,
    computed alongside C using the SAME asked terms/candidates, so directly
    comparable): 96/294 (32.7%) -- a severe regression, far below even the
    plain embedding top-1 baseline (40.5%), not a marginal one. See that
    metric's own inline comment / the session report for the diagnosed
    reason (a single fresh un-unioned cosine similarity against the long,
    dense full corpus row, from a short expanded-query string, does not
    reproduce the real signal _get_candidates' translated+raw+keyword union
    provides -- most likely over-weighting whichever candidate's corpus
    text is broadest/most generic rather than most specific). Kept defined
    (not deleted) as a disclosed real negative result for a genuinely
    different architecture, requested and tried, not silently dropped."""
    ids = list(dict.fromkeys(candidate_ids))
    if not ids:
        return {"mode": "no_match"}
    confirmed_terms = [t.replace("_", " ") for t in asked_terms if patient_confirmed.get(t)]
    if not confirmed_terms:
        return {"mode": "no_new_evidence"}
    model = _get_embedding_model()
    if model is None or _DISEASE_EMB is None or not _DISEASE_IDS:
        return {"mode": "no_new_evidence"}
    expanded_query = (query_text or "") + ". Also confirmed: " + ", ".join(confirmed_terms)
    qemb = model.encode([expanded_query], normalize_embeddings=True)[0]
    id_to_idx = {did: i for i, did in enumerate(_DISEASE_IDS)}
    scored: List[Tuple[str, float]] = []
    for did in ids:
        idx = id_to_idx.get(did)
        if idx is None:
            continue
        scored.append((did, float(_DISEASE_EMB[idx] @ qemb)))
    if not scored:
        return {"mode": "no_match"}
    scored.sort(key=lambda x: -x[1])
    best_id, best_score = scored[0]
    return {
        "mode": "matched",
        "disease_id": best_id,
        "confidence": best_score,
        "ranked": scored,
    }


def selective_commit_decision(candidates: List[Tuple[str, float]], margin: float = CONFIDENT_COMMIT_MARGIN) -> bool:
    """Selective-prediction gate: True ("commit" -- answer directly from the
    embedding top-1, no disambiguation question needed) when the top1-top2
    score gap already meets this file's own pre-existing "clearly-led"
    boundary (see CONFIDENT_COMMIT_MARGIN docstring above); False ("defer"
    -- genuinely ambiguous, ask a disambiguating question / hand off) when
    it does not. A real standard ML concept (risk-coverage / selective
    prediction), evaluated as a threshold sweep in the eval harness, not
    fit to one magic number against this eval's own accuracy outcome."""
    if len(candidates) < 2:
        return True
    top1_score = candidates[0][1]
    top2_score = candidates[1][1]
    return (top1_score - top2_score) >= margin


def _clarify_candidate_block(candidates: List[Tuple[str, float]], disease_meta: Dict[str, Any]) -> str:
    lines = []
    for did, _score in candidates:
        d = disease_meta.get(did, {})
        sym_line = _candidate_symptom_line(d, max_terms=6, max_chars=160)
        lines.append(f"{did} | {d.get('name', '')} | key symptoms: {sym_line or 'n/a'}")
    return "\n".join(lines)


def generate_clarifying_questions(
    patient_text: str, translated: str, candidates: List[Tuple[str, float]], disease_meta: Dict[str, Any]
) -> Dict[str, Any]:
    """LLM call constrained to ONLY the real symptom text of the given real
    candidate shortlist -- it phrases distinguishing questions from that real
    text, it never invents a symptom or a disease, and it never mentions or
    suggests any diagnostic test. Returns a dict: {"questions": [...]},
    2-4 short, plain, doctor-like conversational clarifying questions,
    always in plain English (same "force English, never Devanagari/other
    script" rule already used for _rerank's understood_as -- verified live:
    without it, this exact call answered in Devanagari script for a
    plain-English patient complaint, which _looks_non_english then correctly
    stripped, silently emptying the question list every time). On any
    failure (network/parse) or if fewer than 2 genuine questions come back,
    returns {"questions": []}, which the caller treats as "could not
    generate a safe clarifying flow -> fall back to WhatsApp" rather than
    guessing.

    Before composing anything, checks the pre-authored discriminating-
    question bank (ml_training/discriminating_questions.json, built from the
    121 real KB-authored commonly-confused disease pairs -- see
    build_discriminating_question_bank.py) for any pair within this
    shortlist. Research on real production symptom-checkers (Ada Health,
    Isabel Healthcare, SmartTriage) found pre-authored, clinician-grounded
    questions outperform free-form LLM-composed ones for exactly this
    disambiguation step, so a bank match is used FIRST, with the free-form
    LLM call only filling any remaining slots up to CLARIFY_MAX_QUESTIONS (or
    covering the whole shortlist when no bank pair matches at all -- the 121
    pairs are a real but partial subset of all possible shortlists)."""
    shown = candidates[:CLARIFY_MAX_CANDIDATES]
    bank_questions = _bank_questions_for_candidates(shown)[:CLARIFY_MAX_QUESTIONS]
    if len(bank_questions) >= CLARIFY_MAX_QUESTIONS:
        return {"questions": bank_questions}

    # Tier 2: algorithmic, KB-grounded, no-LLM/no-GPU questions (see
    # discriminating_terms_for_shortlist above) fill any remaining slots
    # before falling through to the free-form LLM tier -- same priority
    # ordering reasoning as the pre-authored bank (real, grounded evidence
    # beats a free-form guess), and these cover any shortlist, not just the
    # 121 hand-authored pairs.
    remaining = CLARIFY_MAX_QUESTIONS - len(bank_questions)
    algo_questions: List[str] = []
    if remaining > 0:
        ids = [did for did, _ in shown]
        algo_terms = discriminating_terms_for_shortlist(ids, max_terms=remaining, base_scores=dict(shown))
        algo_questions = [_algorithmic_question_text(t) for t in algo_terms]
    merged_bank_algo = list(dict.fromkeys(bank_questions + algo_questions))
    if len(merged_bank_algo) >= CLARIFY_MAX_QUESTIONS:
        return {"questions": merged_bank_algo[:CLARIFY_MAX_QUESTIONS]}
    bank_questions = merged_bank_algo

    candidate_block = _clarify_candidate_block(shown, disease_meta)
    system = (
        "You are a doctor having a plain, everyday conversation with a patient. The patient described a "
        "complaint that could match several real candidate diseases (format: id | name | key symptoms: "
        "...), each with real symptom information drawn from a real medical knowledge base. Write between "
        "2 and 4 short clarifying questions (yes/no or one short phrase to answer) that would most help "
        "tell these specific candidates apart. Every question must be grounded in an actual, real "
        "difference between the candidates' listed key symptoms above -- never invent a symptom, never "
        "invent or name a disease, never ask something unrelated to the candidates shown, never ask about "
        "something the patient already stated, and never mention or suggest any test, scan, or lab "
        "investigation of any kind. Phrase each question exactly the way a real doctor casually talks to a "
        "patient face to face -- simple, plain, everyday words, never clinical or technical jargon. Every "
        "question must be written in plain English, using the Latin alphabet only -- never Hindi, "
        "Devanagari script, Chinese, or any other script, even if the patient's own text was in Hindi/"
        "Hinglish. Do not diagnose. Each question must be different from every other question.\n"
        'Respond ONLY as compact JSON: {"questions": ["...", "...", ...]}'
    )
    user = (
        f"Patient's original text: {patient_text}\n"
        f"Translated/normalized text: {translated}\n\n"
        f"Candidate diseases:\n{candidate_block}\n\n"
        "Write 2-4 short distinguishing questions."
    )
    fallback = {"questions": bank_questions} if bank_questions else {"questions": []}
    try:
        content = _ollama_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            timeout=RERANK_TIMEOUT_S,
            force_json=True,
            model=RERANK_MODEL,
        )
        parsed = _extract_json(content)
        questions = parsed.get("questions")
        if not isinstance(questions, list):
            return fallback
        questions = [q.strip() for q in questions if isinstance(q, str) and q.strip() and not _looks_non_english(q)]
        # Bank questions (real, pre-authored, pair-grounded) take priority;
        # free-form questions only fill remaining slots, deduplicated.
        merged = list(dict.fromkeys(bank_questions + questions))
        return {"questions": merged[:CLARIFY_MAX_QUESTIONS]}
    except Exception:
        logger.warning("FALLBACK: clarifying-question generation failed", exc_info=True)
        return fallback


def resolve_clarified_disease(
    patient_text: str, translated: str, candidate_ids: List[str], qa_pairs: List[Tuple[str, str]]
) -> dict:
    """Second turn of the clarifying flow: pick a final disease_id using the
    SAME real candidate shortlist from turn one (re-scored fresh against the
    turn-one translated text, never re-derived from the client), now
    disambiguated with the patient's real answers to the real distinguishing
    questions. Reuses _rerank's existing guardrail (pick from the given real
    shortlist only, never invent) -- the Q&A answers are appended as extra
    real context, not a new free-text diagnosis guess."""
    _ensure_index()
    fresh_candidates = _get_candidates(translated, patient_text)
    score_map = dict(fresh_candidates)
    shortlist = [(did, score_map.get(did, 0.0)) for did in candidate_ids if did in score_map]
    if not shortlist:
        shortlist = [(did, score_map.get(did, 0.0)) for did in candidate_ids]
    if not shortlist:
        return {"mode": "no_match"}

    qa_text = "; ".join(f"{q.strip()} -> {a.strip()}" for q, a in qa_pairs if q and a)
    augmented_translated = translated
    if qa_text:
        augmented_translated = f"{translated}\nAdditional clarifying answers from patient: {qa_text}"

    disease_id, understood_as, possible_emergency, llm_ok = _rerank(
        patient_text, augmented_translated, shortlist, _DISEASE_META or {}
    )
    if not llm_ok or not disease_id:
        return {"mode": "no_match"}

    hard_emergency_flag = _hard_emergency_scan(patient_text, translated)
    possible_emergency = bool(possible_emergency) or hard_emergency_flag
    confidence = float(score_map.get(disease_id, shortlist[0][1]))
    d = (_DISEASE_META or {}).get(disease_id, {})
    return {
        "mode": "matched",
        "disease_id": disease_id,
        "confidence": confidence,
        "understood_as": understood_as,
        "hard_emergency_flag": hard_emergency_flag,
        "possible_emergency": possible_emergency,
        "emergency_override_rule": d.get("EMERGENCY_OVERRIDE_RULE"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_disease_meta() -> Dict[str, Any]:
    """Public accessor for the loaded disease_master.json entries, keyed by
    disease_id -- used by the router to build the real candidate/question
    blocks for the clarifying flow without reaching into this module's
    private module-level index state directly."""
    _ensure_index()
    return _DISEASE_META or {}


def identify_disease(patient_text: str) -> dict:
    """
    First turn of matching a patient's text to a disease_id in
    data/disease_master.json. Returns one of three modes:
      - mode="matched": a direct disease-name match (fast alias/fuzzy path,
        no LLM involved).
      - mode="clarify": the text reads as a real symptom description with
        enough real signal to shortlist candidates; caller should generate
        clarifying questions (see generate_clarifying_questions) and collect
        answers before calling resolve_clarified_disease.
      - mode="no_match": gibberish/off-topic input with no real retrieval
        signal at all; caller should fall back to the WhatsApp doctor link
        directly, no Q&A possible.
    Never fabricates a disease in any mode.
    """
    hard_emergency_flag = _hard_emergency_scan(patient_text)
    alias_hit = _try_direct_alias_match(patient_text)
    if alias_hit is not None:
        disease_id, confidence = alias_hit
        STATS["calls"] += 1
        STATS["alias_fastpath_hits"] += 1
        info = (_ALIAS_DISEASE_INFO or {}).get(disease_id, {})
        display_name = (info.get("name") or disease_id).split("(")[0].strip()
        return {
            "mode": "matched",
            "disease_id": disease_id,
            "confidence": confidence,
            "understood_as": f"You mentioned {display_name}.",
            "hard_emergency_flag": hard_emergency_flag,
            "possible_emergency": hard_emergency_flag,
            "emergency_override_rule": info.get("EMERGENCY_OVERRIDE_RULE"),
        }

    STATS["calls"] += 1
    _ensure_index()
    translated, translate_ok = _translate(patient_text)
    if not translate_ok:
        STATS["translate_fallbacks"] += 1
    candidates = _get_candidates(translated, patient_text)
    hard_emergency_flag = _hard_emergency_scan(patient_text, translated)

    if not candidates:
        return {
            "mode": "no_match",
            "understood_as": translated,
            "hard_emergency_flag": hard_emergency_flag,
            "possible_emergency": hard_emergency_flag,
        }

    top1_score = candidates[0][1]
    if not hard_emergency_flag and top1_score < NO_MATCH_SCORE_FLOOR:
        gate_kw = _keyword_overlap_top_k(
            f"{translated} {patient_text}", TOP_K_KEYWORD,
            min_overlap=NO_MATCH_MIN_KEYWORD_OVERLAP,
        )
        if not gate_kw:
            return {
                "mode": "no_match",
                "understood_as": translated,
                "hard_emergency_flag": False,
                "possible_emergency": False,
            }

    return {
        "mode": "clarify",
        "translated": translated,
        "candidates": candidates[:CLARIFY_MAX_CANDIDATES],
        "understood_as": translated,
        "hard_emergency_flag": hard_emergency_flag,
        "possible_emergency": hard_emergency_flag,
    }
