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
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests

logger = logging.getLogger("medical_understanding")

# ---------------------------------------------------------------------------
# Paths / config
# ---------------------------------------------------------------------------

_THIS_FILE = Path(__file__).resolve()
BASE_DIR = _THIS_FILE.parents[3]  # .../balanceai
DATA_PATH = BASE_DIR / "data" / "disease_master.json"
EMBED_CACHE_PATH = Path(str(DATA_PATH) + ".understanding_embeddings.npy")
EMBED_META_PATH = Path(str(DATA_PATH) + ".understanding_embeddings.meta.json")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_MODEL = "qwen2.5:3b-instruct"
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
RERANK_MODEL = "qwen2.5:7b-instruct"
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
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# Bump whenever _extract_findings/_build_corpus_entry's text-construction
# logic changes, so the on-disk embedding cache (keyed only on ids/mtime/
# model, not on corpus-building code) is correctly invalidated and rebuilt
# instead of silently serving embeddings built from the old corpus text.
CORPUS_VERSION = 2

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
    if len(out) >= max_items:
        return
    if isinstance(obj, dict):
        for key in ("name", "finding"):
            v = obj.get(key)
            if isinstance(v, str) and v.strip():
                out.append(v.strip()[:180])
        for k, v in obj.items():
            if k in _SKIP_KEYS or k in ("name", "finding"):
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
    is not strict enough for that use."""
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
    return sorted(best.items(), key=lambda x: -x[1])


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

CLARIFY_MAX_CANDIDATES = 8
CLARIFY_MIN_QUESTIONS = 2
CLARIFY_MAX_QUESTIONS = 4


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
    guessing."""
    shown = candidates[:CLARIFY_MAX_CANDIDATES]
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
    fallback = {"questions": []}
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
        questions = list(dict.fromkeys(questions))
        return {"questions": questions[:CLARIFY_MAX_QUESTIONS]}
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
