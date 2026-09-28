"""
medicine_lookup.py

Standalone module: given a disease_id, return the real, effectiveness-ordered
list of medicines for it, each with a real citation and a simple layperson
explanation of how it helps the body.

Data sources (the ONLY sources of truth used):
  - data/disease_master.json   -> effectiveness_ranked_table (real order, never re-ranked)
  - data/medicine_details.json -> real per-medicine facts (dosage, fact_box, sources)

A local Ollama model (qwen2.5:3b-instruct) is used ONLY to rephrase already-real
facts into simple language. It is never allowed to introduce a new fact, dose,
number or claim. If the model call fails or no real facts exist at all, the
code falls back to the real raw facts themselves (truncated) or an honest
"not documented" message -- it never fabricates content.
"""

import json
import os
import re

import requests

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BALANCEAI_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))
DATA_DIR = os.path.join(_BALANCEAI_DIR, "data")
DISEASE_MASTER_PATH = os.path.join(DATA_DIR, "disease_master.json")
MEDICINE_DETAILS_PATH = os.path.join(DATA_DIR, "medicine_details.json")
NAME_CLEANUP_MAP_PATH = os.path.join(DATA_DIR, "medicine_name_cleanup_map.json")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = "qwen2.5:3b-instruct"
OLLAMA_TIMEOUT_SECONDS = 45

NOT_DOCUMENTED_MESSAGE = "Iska mechanism is dataset mein detail mein documented nahi hai."

_STOPWORDS = {
    "the", "a", "an", "of", "for", "with", "and", "or", "in", "to", "vs", "at",
    "on", "real", "-", "--", "is", "are", "as", "from", "by", "than", "over",
    "study", "trial", "rct", "meta", "analysis", "review", "case", "cases",
    "combined", "postoperative", "freedom", "score", "reduction", "rate",
    "week", "weeks", "month", "months", "year", "years", "vs.", "cohort",
    "prospective", "controlled", "randomised", "randomized", "multicentre",
    "multicenter", "single", "series", "guideline", "guideline-endorsed",
    "guideline-cited", "pooled", "vs", "high", "low", "into", "per",
    # generic route/form/dosing/severity words: excluded because on their own
    # they are not distinctive enough to prove two names refer to the same
    # medicine (e.g. "first-line" appearing in two unrelated drug names would
    # otherwise register as a false "match").
    "oral", "iv", "im", "sc", "topical", "injection", "injectable", "tablet",
    "tablets", "capsule", "capsules", "spray", "cream", "gel", "gels",
    "solution", "drug", "drugs", "agent", "agents", "class", "classes",
    "therapy", "therapies", "combination", "dose", "dosing", "regimen",
    "regimens", "drops", "patch", "patches", "inhaler", "route", "treatment",
    "management", "medicine", "medicines", "medication", "medications",
    "compound", "monotherapy", "fixed", "alone", "standalone", "acute",
    "chronic", "add", "adjunct", "adjuvant", "based", "first", "second",
    "third", "line", "primary", "secondary", "arm", "group",
    # Real bug found, 2026-09-28: a well-documented, real, specific compound
    # in medicine_details.json (e.g. "eptinezumab or , iv infusion, once
    # every 12 weeks", "coenzyme q10 three times daily",
    # "prochlorperazine iv/im, or per-rectal suppository") is often keyed
    # under a long real-world administration/frequency description rather
    # than the bare drug name. Those extra route/frequency/form words were
    # inflating the KB key's own token count enough to fail the >=50%
    # candidate-ratio fuzzy-match threshold against a short, correctly
    # cleaned candidate name like "Eptinezumab IV" -- a real medicine was
    # silently dropped from the ranked results because of this, not because
    # any exclusion rule fired. Full route words, dosing-frequency words, and
    # common dosage-form words are stripped here the same way the abbreviated
    # forms (oral/iv/im/sc/topical) already were.
    "intravenous", "intramuscular", "subcutaneous", "intranasal", "nasal",
    "rectal", "sublingual", "buccal", "vaginal", "transdermal",
    "transmucosal", "ophthalmic", "otic", "intrathecal", "intraarticular",
    "intra-articular", "epidural", "intradermal", "inhalational", "infusion",
    "infusions", "bolus", "suppository", "suppositories", "ointment",
    "lotion", "foam", "lozenge", "lozenges", "syrup", "elixir", "suspension",
    "powder", "once", "twice", "thrice", "daily", "weekly", "monthly",
    "hourly", "every", "times", "then", "day", "days", "hour", "hours",
    "minute", "minutes", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "twelve",
}

# ---------------------------------------------------------------------------
# Data loading (cached at module level)
# ---------------------------------------------------------------------------

_disease_master_cache = None
_medicine_details_cache = None
_medicine_index_cache = None  # list of (key, name_tokens, record)
_name_cleanup_map_cache = None  # {raw_name: {cleaned_name, confidence, ...}}


def _load_disease_master():
    global _disease_master_cache
    if _disease_master_cache is None:
        with open(DISEASE_MASTER_PATH, "r", encoding="utf-8") as f:
            _disease_master_cache = json.load(f)["diseases"]
    return _disease_master_cache


def _load_medicine_details():
    global _medicine_details_cache
    if _medicine_details_cache is None:
        with open(MEDICINE_DETAILS_PATH, "r", encoding="utf-8") as f:
            _medicine_details_cache = json.load(f)["medicines"]
    return _medicine_details_cache


# data/medicine_name_cleanup_map.json's "high confidence" mappings carry a
# "reason" field explaining HOW the name was cleaned, not WHETHER it names a
# real purchasable drug. Verified by hand against real samples from every
# reason bucket, 2026-09-28: these two are the only ones that reliably mean
# "this text already looks like one real, specific compound name" on their
# own -- every other reason (device/procedure name pattern; "short
# capitalized phrase (plausible name)"; "too many words after cleaning";
# etc.) mixes in real non-drug rows (devices, procedures, care models,
# lifestyle interventions, disease/diagnosis labels) often enough that it is
# trusted only together with a real medicine_details.json match.
_TRUSTED_BYPASS_REASONS = {
    "matches known drug-name suffix / salt-name / reference / device acronym",
    "extracted real name from trial-acronym(name) pattern",
}


def _load_name_cleanup_map():
    """Real, verified {raw_name: {cleaned_name, confidence, reason, method}}
    map covering all 3,360 unique raw treatment/medicine names actually found
    in disease_master.json's ranked tables (see
    data/medicine_name_cleanup_map.json's own _meta for the generation
    method). disease_master.json itself is never modified -- this is applied
    at render time only, and takes priority over the regex-based
    clean_medicine_name() for any raw name it covers."""
    global _name_cleanup_map_cache
    if _name_cleanup_map_cache is None:
        try:
            with open(NAME_CLEANUP_MAP_PATH, "r", encoding="utf-8") as f:
                _name_cleanup_map_cache = json.load(f).get("mappings", {})
        except (FileNotFoundError, ValueError):
            _name_cleanup_map_cache = {}
    return _name_cleanup_map_cache


# Real disease_master.json ranked tables (and a handful of medicine_details.json
# entries themselves, e.g. "dietary modification", "weight loss",
# "lifestyle/risk-factor modification", "dietary sodium restriction",
# "treatment of tinea pedis and other skin-barrier breaks") contain genuine
# clinical recommendations that are not a purchasable medicine/injection/
# equipment. Matched only on the LEADING phrase or a whole-phrase pattern so
# a real drug name is never miscaught (e.g. "Cholecalciferol - stoss therapy"
# is a real drug and must not match).
_NON_DRUG_PATTERNS = [re.compile(p, re.I) for p in [
    r"^physiotherapy\b", r"^physical therapy\b", r"^occupational therapy\b",
    r"^exercise therapy\b", r"^exercise program(me)?\b",
    r"^dietary\b", r"^diet\b", r"^weight[\s-]loss\b", r"^lifestyle\b",
    r"^surgery\b", r"^surgical\b", r"^counsel(l)?ing\b", r"^psychotherapy\b",
    r"^cognitive behavio(u)?ral therapy\b",
    r"reconstructive surgery", r"behavio(u)?ral weight-loss",
    r"^positional therapy\b", r"^smoking cessation\b",
    # structural "this is a recommendation, not a product name" phrasing
    r"^treatment of\b", r"^prevention of\b", r"^avoidance of\b", r"^screening\b",
]]

# A real surgical PROCEDURE name -- never a purchasable medicine -- doesn't
# reliably lead with one of the _NON_DRUG_PATTERNS words above (it usually
# leads with the anatomical site or a device brand, e.g. "Ferguson closed
# hemorrhoidectomy", "Nd:YAG Laser Peripheral Iridotomy", "VA-ECMO"), so
# these are matched anywhere in the string by their distinctive procedure-
# name suffix/acronym instead of only at the start. Ported 1:1 from the
# identical addition in frontend/src/lib/medicines.ts's
# NON_DRUG_PROCEDURE_RE -- see that file for the full note.
_NON_DRUG_PROCEDURE_RE = re.compile(
    r"(ectomy|otomy|oscopy|ostomy|plasty|rrhaphy|centesis|\bECMO\b|\bCPR\b|"
    r"vessel-sealing|catheteri[sz]ation|angioplasty|defibrillat|"
    r"pacemaker implant|bypass graft)",
    re.I,
)


def _is_non_drug_intervention(name):
    n = (name or "").strip()
    if not n:
        return False
    if _NON_DRUG_PROCEDURE_RE.search(n):
        return True
    return any(p.search(n) for p in _NON_DRUG_PATTERNS)


# Trailing-word variant, applied only to the SHORT, already-cleaned ranked-
# table candidate name (never to medicine_details.json keys/names, which are
# real drug entries that legitimately mention "surgery"/"physiotherapy" in a
# clinical-context sentence, e.g. "cinacalcet -- ... for patients who cannot
# or decline surgery"). A real disease_master.json ranked-table row is often
# a short "X surgery" / "Structured physiotherapy" phrase that the leading-
# anchored _NON_DRUG_PATTERNS above misses because the non-drug word isn't
# the first word.
_NON_DRUG_TRAILING_PATTERNS = [re.compile(p, re.I) for p in [
    r"\bsurgery$", r"\bsurgical$", r"\bphysiotherapy$", r"\bphysical therapy$",
]]


def _is_non_drug_candidate_name(candidate_name):
    n = (candidate_name or "").strip()
    if not n:
        return False
    return any(p.search(n) for p in _NON_DRUG_TRAILING_PATTERNS)


# The symptom-checker must NEVER surface a bare pharmacological CLASS (e.g.
# "JAK inhibitor", "ACE inhibitors", "NSAIDs") as if it were one specific,
# purchasable compound. Ported 1:1 from frontend/src/lib/medicines.ts's
# looksLikeDrugClassOnly() (built/verified against the full real catalog by a
# concurrent effort this session) so both surfaces apply the same real rule.
_CLASS_SUFFIX_RE = r"(?:inhibitor|inhibitors|blocker|blockers|antagonist|antagonists|agonist|agonists|receptor blocker|receptor antagonists?)"
_CLASS_CORE_RE = re.compile(
    r"^([A-Za-z0-9]{1,12}(?:[/-][A-Za-z0-9]{1,12})*\s+" + _CLASS_SUFFIX_RE + r")\b", re.I
)
_BARE_CLASS_WORDS = {
    "nsaid", "nsaids", "statin", "statins", "ssri", "ssris", "snri", "snris",
    "ppi", "ppis", "beta blocker", "beta-blocker", "beta blockers",
    "ace inhibitor", "ace inhibitors",
}
_CLASS_CORE_SPLIT_RE = re.compile(r"\s+(?:after|for|before|when|if|once|given)\b", re.I)

# Real disease_master.json ranked-table rows sometimes wrap a bare class noun
# in a longer descriptive phrase rather than using it alone (e.g. "NSAID
# class: proportion of regimens...", "NSAID gel/solution responder rate...").
# clean_medicine_name()/the cleanup map reduce these to "NSAID class" /
# "NSAID gel/solution responder" -- neither is a whole-string match against
# _BARE_CLASS_WORDS nor the inhibitor/blocker/antagonist/agonist suffix
# pattern, so a bare-class candidate whose FIRST WORD is one of these nouns is
# also treated as a class-only, not-one-compound name. Verified by hand,
# 2026-09-28: no real single-named compound in the dataset begins with one of
# these words.
_BARE_CLASS_LEADING_WORDS = {"nsaid", "nsaids"}


def _looks_like_drug_class_only(name):
    n = (name or "").strip()
    if not n:
        return False
    core = _CLASS_CORE_SPLIT_RE.split(n, maxsplit=1)[0].strip()
    if not core:
        return False
    if core.lower() in _BARE_CLASS_WORDS:
        return True
    first_word = core.split(" ", 1)[0].strip(".,:;").lower()
    if first_word in _BARE_CLASS_LEADING_WORDS:
        return True
    m = _CLASS_CORE_RE.match(core)
    if m and m.group(1).strip().lower() == core.lower():
        return True
    return _is_bare_class_after_stripping_descriptors(n)


# Real disease_master.json ranked-table rows very often show a bare hormone/
# steroid class name wrapped in a route/frequency/severity adjective instead
# of naming one specific compound -- "Adjunctive Corticosteroids", "Systemic
# Corticosteroids", "Intranasal corticosteroid", "Intra-articular
# corticosteroid", "Mini-pulse corticosteroid", "Daily Corticosteroid",
# "Beta-Blocker Therapy". Verified by hand, 2026-09-28: this exact pattern
# (a bare class noun plus only generic route/frequency filler words, no real
# compound name) appears across 30+ real diseases (pericardial_disease,
# myocarditis, bronchial_asthma, ards, sarcoidosis, osteoarthritis, vitiligo,
# allergic_rhinitis, tennis_elbow, etc.), none of it a specific named
# medicine. _normalize_tokens() already strips the common route/dose/form
# filler words (oral, IV, topical, injection, therapy, daily, ...); this adds
# the handful of severity/route adjectives specific to this pattern that
# aren't already in that stopword list, then checks whether anything other
# than a bare class noun/phrase is left. A real combination row like
# "Epidural glucocorticoid+lidocaine" is left alone because "lidocaine" (a
# real, specific compound) survives the strip.
_BARE_CLASS_NOUNS = {
    "corticosteroid", "corticosteroids", "glucocorticoid", "glucocorticoids",
    "steroid", "steroids",
}
_BARE_CLASS_PHRASES = {
    "beta blocker", "beta blockers",
    "ace inhibitor", "ace inhibitors",
    "calcium channel blocker", "calcium channel blockers",
}
_GENERIC_DESCRIPTOR_WORDS = {
    "adjunctive", "systemic", "intranasal", "intra", "articular",
    "intratympanic", "topical", "induction", "daily", "epidural", "early",
    "mini", "pulse", "minipulse",
}


def _is_bare_class_after_stripping_descriptors(name):
    tokens = [t for t in _normalize_tokens(name) if t not in _GENERIC_DESCRIPTOR_WORDS]
    if not tokens:
        return False
    if " ".join(tokens) in _BARE_CLASS_PHRASES:
        return True
    return all(t in _BARE_CLASS_NOUNS for t in tokens)


# A handful of real disease_master.json ranked-table "name" fields are stray
# sentence fragments or multi-component regimen descriptions rather than one
# purchasable product. Ported 1:1 from frontend/src/lib/medicines.ts's
# looksLikeMalformedFragment() (minus the disease-staging-label check, which
# is specific to medicine_details.json catalog entries, not ranked-table
# rows).
_FRAGMENT_LEADING_WORDS = {
    "can", "could", "or", "and", "with", "without", "when", "if", "per",
    "given", "plus", "versus", "while", "after", "before", "during", "for",
    "the", "a", "an", "to", "in", "on", "at", "as", "that", "which", "this",
    "these", "those", "its", "not", "no", "same",
    # Added in the "100% cleaner" self-audit pass, 2026-09-28 -- ported 1:1
    # from the identical addition in frontend/src/lib/medicines.ts, see that
    # file for the full note.
    "consider", "guides", "guide", "relief", "children", "adults", "infants",
    "avoid", "add", "switch", "continue", "start", "stop", "monitor",
    "screen", "test", "check", "assess", "evaluate", "refer", "ensure",
    "provide", "administer", "apply", "review", "reassess", "repeat",
    "alternative", "alternatives", "option", "options", "approach",
    "standard", "routine", "treat", "treatment", "management", "manage",
    "slow", "immediate", "late", "early", "single", "second", "first",
    "third", "initial", "ongoing", "real",
}
_FIRST_WORD_RE = re.compile(r"^[A-Za-z]+")

# Real bug found and fixed here, 2026-09-28 (user directly found multiple
# live examples via the symptom-checker results flow: "Alternatives when
# dexamethasone cannot be given : IV hydrocortisone or methylprednisolone at
# equivalent dosage", "Deflazacort /kg/day" (a real medicine whose dosage
# NUMBER was dropped during extraction, leaving a dangling unit), "combined
# with a progestin such as medroxyprogesterone acetate in women with an
# intact uterus"). None of these are caught by the leading-word check above
# because they start with a capitalized word or don't start with a function
# word at all. Ported 1:1 from the same fix in
# frontend/src/lib/medicines.ts's looksLikeMalformedFragment() -- see that
# file for the full verification note (183/3,126 real catalog entries
# matched, zero real single-product names wrongly caught).
_FRAGMENT_CONNECTOR_WORDS = {
    "with", "in", "for", "when", "if", "or", "and", "such", "as", "combined",
    "given", "used", "added", "per", "of", "than", "versus", "including",
    "plus", "without", "during", "after", "before", "while", "unless",
    "once", "until", "because", "since", "due", "via", "through", "despite",
    "across", "among", "between", "within", "against", "towards", "upon",
    "regarding", "concerning",
}
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'/-]*")
_ALPHA_WORD_RE = re.compile(r"[a-z]+")
_BROKEN_DOSAGE_RE = re.compile(
    r"\s/(kg|day|dose|doses|m2|m\^2|hr|hrs|week|weeks|ml|mg)\b", re.I
)


def _looks_like_malformed_fragment(name, is_validated_combination=False):
    n = (name or "").strip()
    if not n:
        return False
    # Case-insensitive on purpose -- see the identical fix/note in
    # frontend/src/lib/medicines.ts's looksLikeMalformedFragment (11 more
    # real garbage entries, e.g. "Not applicable -- devices, not medicines",
    # were sentence-cased and slipped past a lowercase-only check).
    m = _FIRST_WORD_RE.match(n)
    if m and m.group(0).lower() in _FRAGMENT_LEADING_WORDS:
        return True
    # A real bug found, 2026-09-28: "Ibuprofen + Aspirin + Triptan" (a real
    # migraine acute-treatment row, each named drug real) was being excluded
    # here purely because it has two "+" signs, the same signal meant to
    # catch an actual unnamed multi-component regimen description. When the
    # cleanup map's own method is "validated_combination", every "+"-joined
    # component was already independently checked to be a real drug/device/
    # procedure name (data/medicine_name_cleanup_map.json's own generation
    # step) -- that per-component vetting is stronger evidence than a bare
    # "+" count, so the count check is skipped in that case.
    if not is_validated_combination and n.count("+") >= 2:
        return True
    if _looks_like_drug_class_only(n):
        return True
    alpha_words = _ALPHA_WORD_RE.findall(n.lower())
    connector_hits = sum(1 for w in alpha_words if w in _FRAGMENT_CONNECTOR_WORDS)
    word_count = len(_WORD_RE.findall(n))
    if connector_hits >= 3 or word_count > 16:
        return True
    if _BROKEN_DOSAGE_RE.search(n):
        return True
    # Second pass, tightened after further real examples the founder found
    # live ("Avoidance of QT-Prolonging Drugs - Critical Preventive Measure,
    # ALL LQTS Genotypes", "Same four pillar drugs - up-titrated faster and
    # more completely, not a new molecule") -- ported 1:1 from the identical
    # tightening in frontend/src/lib/medicines.ts's looksLikeMalformedFragment.
    dash_separator_count = len(re.findall(r" -- | - ", n))
    has_note_dash_format = " -- " in n or dash_separator_count >= 2
    if has_note_dash_format and (connector_hits >= 1 or word_count > 10):
        return True
    # Third pass (founder directive: zero tolerance, "100% cleaner") --
    # ported 1:1 from the identical tightening in
    # frontend/src/lib/medicines.ts's looksLikeMalformedFragment; see that
    # file for the full manual-review note on the 102 entries this catches.
    if connector_hits >= 1 and word_count > 8:
        return True
    return False


# Real medicine_details.json entries sometimes carry their own explicit
# curator note saying an entry is a guideline/procedure/regimen-description,
# not a real compound (e.g. "This is a generic procedure description, not a
# single named compound; specific corticosteroids are covered under other
# entries."). Ported 1:1 from frontend/src/lib/medicines.ts's
# NOT_A_COMPOUND_RE / GENERIC_DESCRIPTION_RE / noteIndicatesNonPurchasable()
# (the old version here only allowed ONE qualifier word between "not a" and
# "medicine"/"compound", so real phrasing with two qualifiers in a row --
# "not a single named compound" -- silently failed to match; fixed to match
# the frontend's corrected regex).
_NOTE_NOT_A_MEDICINE_RE = re.compile(
    r"not (?:a|one) (?:single |named |distinct |specific |identifiable )*(?:medicine|compound)\b"
    r"|drug[- ]class (?:label|description)"
    r"|names? a (?:drug )?class\b"
    r"|no (?:single|specific) (?:compound|agent) (?:specified|named)\b"
    r"|not one (?:distinct|specific)(?:,? \w+)? (?:compound|marketed drug|drug)\b"
    r"|generic .{0,40}product category",
    re.I,
)
_NOTE_GENERIC_DESCRIPTION_RE = re.compile(
    r"generic (?:procedure|regimen|intervention|treatment[- ]class|drug[- ]class|"
    r"dosing[- ]strategy|clinical[- ]strategy|pharmacologic[- ]strategy|"
    r"treatment[- ]strategy|treatment[- ]approach|supportive[- ]care|"
    r"treatment[- ]category)\s*(?:/[a-z-]+)?\s*description\b",
    re.I,
)

# Real medical equipment/device entries (CPAP machines, neurostimulators,
# glucometers, dialyzers, etc.) are explicitly allowed to stay listed in the
# general /medicines catalog (frontend/src/lib/medicines.ts's isDeviceEntry())
# because that catalog also sells devices. The symptom-checker's ranked
# result list is different: it must show ONLY real, specific, named
# medicines/injections and must NEVER show a device/equipment name, so here a
# device note is a hard exclusion instead of an exemption. Same detection
# regex as isDeviceEntry(), just used with the opposite polarity.
_DEVICE_NOTE_RE = re.compile(
    r"\b(medical device|device|equipment|machine|cpap|stimulator|electrode|"
    r"glucometer|implant|prosthe|analyzer|cartridge|embolic|embolization coil|"
    r"dialyzer|occluder|ecmo|icd\b|pulse generator|circulatory support|"
    r"apheresis|adsorption column|graft\b)",
    re.I,
)

# A tiny number of real medicine_details.json entries are themselves a bare
# drug-class label with no curator note flagging it (verified by hand,
# 2026-09-28: exactly these 2 -- "nsaids" already carries a protective note,
# "corticosteroid injection" and "opioids" do not). Excluded outright so a
# ranked-table row that fuzzy-matches one of them (e.g. "Epidural
# corticosteroid injection", "Intrabursal corticosteroid injection") never
# surfaces as if it named a specific compound.
_BARE_CLASS_RECORD_KEYS = {"corticosteroid injection", "opioids"}


def _is_device_note(note):
    return bool(_DEVICE_NOTE_RE.search((note or "").strip()))


def _note_indicates_non_purchasable(note):
    n = (note or "").strip()
    if not n:
        return False
    return bool(_NOTE_NOT_A_MEDICINE_RE.search(n) or _NOTE_GENERIC_DESCRIPTION_RE.search(n))


def _medicine_index():
    """List of (key, tokens, record) built once from medicine_details.json,
    excluding the handful of real entries that are non-drug interventions
    (see _is_non_drug_intervention), devices/equipment (see _is_device_note --
    unlike the general /medicines catalog, the symptom-checker must never
    show a device), and bare drug-class labels, so they never surface as a
    fuzzy-match "real medicine" and never appear as a symptom-checker result
    item."""
    global _medicine_index_cache
    if _medicine_index_cache is None:
        details = _load_medicine_details()
        index = []
        for key, record in details.items():
            display_name = record.get("name") or key
            if _is_non_drug_intervention(key) or _is_non_drug_intervention(display_name):
                continue
            if key.strip().lower() in _BARE_CLASS_RECORD_KEYS:
                continue
            note = record.get("note")
            if _note_indicates_non_purchasable(note) or _is_device_note(note):
                continue
            # Real medicine_details.json entries with research_status
            # "not_found" sometimes also carry an explicit "not_found_reason"
            # explaining WHY -- verified by hand against all 146 real entries
            # that have this field (2026-09-28): every single one explains
            # that the key is a device, procedure, drug class, diagnostic
            # test, guideline statement, lifestyle measure, or unresolved
            # fragment, never a genuine single named compound that is simply
            # under-researched (the other 478 real "not_found" entries carry
            # no such reason at all -- those stay, since for them "not_found"
            # only means "not yet researched", not "not a real medicine").
            if record.get("not_found_reason"):
                continue
            fact_box = record.get("fact_box") or {}
            if str(fact_box.get("chemical_class") or "").strip().lower() == "not applicable":
                continue
            tokens = set(_normalize_tokens(display_name)) | set(_normalize_tokens(key))
            index.append((key, tokens, record))
        _medicine_index_cache = index
    return _medicine_index_cache


# ---------------------------------------------------------------------------
# Fuzzy name matching
# ---------------------------------------------------------------------------

def _normalize_tokens(name):
    if not name:
        return []
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    tokens = [t for t in name.split() if t and t not in _STOPWORDS and not t.isdigit()]
    return tokens


def is_curative_match(row_name, curative_name):
    """True if row_name and curative_name share >=2 significant tokens."""
    if not row_name or not curative_name:
        return False
    row_tokens = set(_normalize_tokens(row_name))
    cur_tokens = set(_normalize_tokens(curative_name))
    return len(row_tokens & cur_tokens) >= 2


# A fuzzy match is only accepted when ALL are true:
#  - the candidate medicine's own identity is substantially present in the
#    row name (>=50% of its significant tokens), so a 1-word drug name like
#    "Aspirin" can still match; and
#  - the overlap is a meaningful fraction of the row name's own content
#    (>=30%), so a long, multi-concept row name doesn't get matched to an
#    unrelated medicine purely because they happen to share one stray word;
#    and
#  - real bug found and fixed here (verified by reproducing live): with only
#    the two ratio checks above, a single shared GENERIC word was enough to
#    pass both ratios whenever both names were themselves short -- e.g.
#    "Total knee replacement" (row) vs. the medicine "nicotine replacement
#    therapy" (candidate, "therapy" is a stopword) share only the one word
#    "replacement", yet that gave cand_ratio=1/2=0.5 and row_ratio=1/3=0.33,
#    clearing both thresholds and wrongly attaching nicotine-patch sources
#    and mechanism text to a knee/hip replacement surgery row. Requiring
#    overlap_count >= 2 (unless the candidate is genuinely a single real
#    token, e.g. "Aspirin", where 1 overlapping token IS the whole identity)
#    blocks this class of single-generic-word false match while still
#    allowing real single-word drug names to match.
_MIN_CANDIDATE_RATIO = 0.5
_MIN_ROW_RATIO = 0.3
_MIN_OVERLAP_COUNT = 2


def _best_token_match(row_tokens, candidates):
    """candidates: iterable of (identifier, cand_tokens). Returns best identifier or None."""
    if not row_tokens:
        return None

    best = None
    best_score = 0
    best_cand_ratio = 0.0
    for identifier, cand_tokens in candidates:
        if not cand_tokens:
            continue
        overlap = row_tokens & cand_tokens
        overlap_count = len(overlap)
        if overlap_count == 0:
            continue
        # The >=2-overlap guard only applies when BOTH sides are multi-token:
        # if either side is a single token (e.g. the row name is just
        # "Duloxetine", or the candidate name's whole identity reduces to one
        # word after stopword-stripping), that one token already IS that
        # side's entire identity, so a real drug name like "Duloxetine"
        # matching a longer candidate/row that contains it must still work
        # (verified live: without this exception, "Duloxetine" stopped
        # matching the disease-specific survey entry "Duloxetine - Centrally
        # Acting SNRI for OA Pain..." entirely).
        if overlap_count < _MIN_OVERLAP_COUNT and len(cand_tokens) > 1 and len(row_tokens) > 1:
            continue
        cand_ratio = overlap_count / len(cand_tokens)
        row_ratio = overlap_count / len(row_tokens)
        if cand_ratio < _MIN_CANDIDATE_RATIO or row_ratio < _MIN_ROW_RATIO:
            continue
        if overlap_count > best_score or (overlap_count == best_score and cand_ratio > best_cand_ratio):
            best_score = overlap_count
            best_cand_ratio = cand_ratio
            best = identifier
    return best


def _match_medicine_details(row_name):
    """Fuzzy-match row_name against medicine_details.json entries.

    Returns (key, record) or None.
    """
    row_tokens = set(_normalize_tokens(row_name))
    candidates = (((key, record), cand_tokens) for key, cand_tokens, record in _medicine_index())
    return _best_token_match(row_tokens, candidates)


def _match_survey_entry(row_name, survey_entries):
    """Match row_name (a short canonical medicine/treatment name, e.g.
    "Duloxetine") against a disease's own exhaustive_medicine_survey entries.

    Real bug found and fixed here, 2026-09-28 (reproduced live): this used to
    call the same ratio-based _best_token_match() used for
    _match_medicine_details(), but that function's _MIN_CANDIDATE_RATIO check
    requires the CANDIDATE's tokens to be substantially covered by the row --
    correct for _match_medicine_details (row = long disease_master.json row
    name, candidate = short canonical drug name from the global 3,126-drug
    index), but backwards here, where the row is the short canonical name and
    every real survey entry name in this dataset is a long descriptive title
    ("Duloxetine - Centrally Acting SNRI for OA Pain with Central
    Sensitisation"). With the ratio check applied in that direction, a short
    row like "Duloxetine" (1 token) against an 8+-token title always scored
    cand_ratio ~0.1-0.2, well under 0.5, so the correct, disease-specific
    survey fact (which is what should be preferred -- see get_ranked_medicines)
    was silently unreachable for virtually every entry in the dataset, not
    just this one.

    The correct criterion for this direction is containment, not a ratio: a
    survey entry only every needs to be an "of course" match ("Duloxetine"
    inside a title that begins "Duloxetine - ..."), so requiring every one of
    row_name's own significant tokens to appear in the candidate's tokens
    (a full subset, not a fraction) is both correct and safe -- survey_entries
    is already scoped to this one disease (10-30 entries), not the global
    3,126-drug index, so the false-positive risk that justified a stricter
    ratio for _match_medicine_details does not apply here.
    """
    row_tokens = set(_normalize_tokens(row_name))
    if not row_tokens:
        return None
    best = None
    best_cand_len = None
    for entry in survey_entries:
        cand_tokens = set(_normalize_tokens(entry.get("name")))
        if not cand_tokens or not row_tokens.issubset(cand_tokens):
            continue
        if best_cand_len is None or len(cand_tokens) < best_cand_len:
            best = entry
            best_cand_len = len(cand_tokens)
    return best


# ---------------------------------------------------------------------------
# Extracting rows / survey entries from a disease record
# ---------------------------------------------------------------------------

def _extract_ranked_rows(disease):
    """Return the disease's ranked medicine/treatment rows in their real
    existing order. Handles the two real shapes seen in disease_master.json:
      - {"caveat": ..., "ranked_high_to_low": [ {...}, ... ]}
      - a bare list [ {...}, ... ]
      - the PCOS-style {"ranked_by_goal": {goal: [ {...}, ... ], ...}}
    """
    table = disease.get("effectiveness_ranked_table")
    if table is None:
        return []

    if isinstance(table, list):
        return [r for r in table if isinstance(r, dict) and r.get("name")]

    if isinstance(table, dict):
        rows = table.get("ranked_high_to_low")
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict) and r.get("name")]

        goal_map = table.get("ranked_by_goal")
        if isinstance(goal_map, dict):
            out = []
            for goal_rows in goal_map.values():
                if isinstance(goal_rows, list):
                    out.extend(r for r in goal_rows if isinstance(r, dict) and r.get("name"))
            return out

    return []


def _extract_survey_entries(disease):
    """Flatten every medicine-like entry out of exhaustive_medicine_survey.

    Real data shows this field is a dict whose values are either a plain
    string note, or a list of medicine-entry dicts (the common "medicines"
    key, plus disease-specific sub-lists like "hfref_medicines"). We collect
    every dict with a "name" field found in any list value.
    """
    survey = disease.get("exhaustive_medicine_survey")
    entries = []
    if isinstance(survey, dict):
        for value in survey.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and item.get("name"):
                        entries.append(item)
    return entries


_CITATION_TRAIL_RE = re.compile(r"\s*\(([^()]*)\)\s*$")
_CITATION_INNER_RE = re.compile(r"(19|20)\d{2}|\b(trial|study|rct|cohort|pooled|registry|regimen)\b", re.I)
_ALLCAPS_PAREN_RE = re.compile(r"^[A-Z0-9][A-Z0-9 \-]{2,}$")
_DASH_SPLIT_RE = re.compile(r"\s+--\s+|\s+—\s+|\s+-\s+(?=[A-Z])")
_VS_SPLIT_RE = re.compile(r"\s+(?:vs\.?|versus)\s+", re.I)
_AS_AN_RE = re.compile(r"\s+as\s+(?:an|a)\b", re.I)
# Trailing dosing-frequency/duration/amount fragments (e.g. "Apremilast twice
# daily", "Amoxicillin 500mg TID for 7 days") -- these are real dosing
# instructions carried into the name field, not part of the drug's identity.
_TRAILING_DOSING_RE = re.compile(
    r"\s+(?:(?:once|twice|thrice|two times|three times|four times)\s+(?:a\s+)?(?:day|daily|weekly|monthly)\b.*"
    r"|every\s+\d+[\s-]*\d*\s*(?:hours?|hrs?|days?|weeks?)\b.*"
    r"|(?:BID|TID|QID|QDS|TDS|OD|QD|PRN|STAT)\b.*"
    r"|x\s*\d+\s*(?:days?|weeks?)\b.*"
    r"|for\s+\d+\s*(?:days?|weeks?)\b.*"
    r"|\d+(?:\.\d+)?\s*-?/?\d*\s*(?:mg|mcg|g|ml|iu|units?)\b.*)$",
    re.I,
)
_LEADING_ROUTE_RE = re.compile(r"^(?:oral|iv|im|intravenous|intramuscular|subcutaneous|sc|topical|rectal)\s+(?=[A-Z])", re.I)


def clean_medicine_name(raw):
    """Real disease_master.json 'name' fields for ranked-table rows are often
    full clinical-context phrases, not clean product names -- e.g.
    "Gentamicin as an optional synergistic partner" or "Osilodrostat --
    Randomized-Withdrawal Maintained Complete Response (LINC 3)". This
    extracts just the leading real drug/salt name for display, keeping the
    fuller original text available separately (raw_facts/sources) for detail
    views. Never invents a name -- only trims real descriptive suffixes.
    """
    if not raw:
        return raw
    s = raw.strip()

    # Strip a leading route-of-administration word (e.g. "Oral Acyclovir...").
    s = _LEADING_ROUTE_RE.sub("", s)

    # Cut at an em-dash/double-dash or capitalised-clause dash suffix.
    s = _DASH_SPLIT_RE.split(s, maxsplit=1)[0]
    # Cut at a colon-introduced descriptive clause.
    s = s.split(":", 1)[0]

    # Strip a trailing parenthetical only if it reads like a citation/trial
    # reference (a year, trial/study wording, or an ALL-CAPS trial acronym) --
    # short clarifying abbreviations like "(CBT)" or brand names like
    # "(Gardasil 9)" are deliberately kept.
    m = _CITATION_TRAIL_RE.search(s)
    if m and (_CITATION_INNER_RE.search(m.group(1)) or _ALLCAPS_PAREN_RE.match(m.group(1).strip())):
        s = s[: m.start()].rstrip()

    # Cut at a drug-vs-drug/treatment-vs-treatment comparison clause.
    s = _VS_SPLIT_RE.split(s, maxsplit=1)[0]

    # Cut at a qualifying "as an/a ..." clause.
    m2 = _AS_AN_RE.search(s)
    if m2 and m2.start() > 0:
        s = s[: m2.start()]

    # Strip a trailing dosing-frequency/duration/amount fragment.
    s = _TRAILING_DOSING_RE.sub("", s)

    # A comma almost always introduces dosing/context, never part of a real
    # drug name in this dataset.
    s = s.split(",", 1)[0]

    s = s.strip(" -–—,;:")
    return s if len(s) >= 2 else raw.strip()


def _split_sources(raw):
    """Return raw source data as a list of citation strings.

    Scientific citations commonly use ";" internally (e.g. "Journal
    2009;35(4):629-36"), so a string value is kept intact as a single
    citation rather than being split on ";" (splitting would fragment a
    single real citation into nonsense pieces). Only an actual list input
    (e.g. medicine_details.json's "sources" URL list) is treated as
    already-separate items.
    """
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if s]
    text = str(raw).strip()
    return [text] if text else []


# ---------------------------------------------------------------------------
# Raw-fact extraction (real facts only, no invention)
# ---------------------------------------------------------------------------

def _facts_from_medicine_details(record):
    parts = []
    dosage = record.get("dosage_administration")
    if dosage:
        parts.append(str(dosage))
    fact_box = record.get("fact_box") or {}
    action_class = fact_box.get("action_class")
    if action_class:
        parts.append(str(action_class))
    return ". ".join(parts).strip(), _split_sources(record.get("sources"))


def _facts_from_survey_entry(entry):
    """Real disease_master.json data has "reason_why" as either a plain
    string or (in ~430 entries) a list of strings -- both are handled here
    so a Python list repr (e.g. "['...']") never leaks into the raw facts
    handed to the LLM."""
    parts = []
    reason_why = entry.get("reason_why")
    if isinstance(reason_why, list):
        parts.extend(str(r).strip() for r in reason_why if r)
    elif reason_why:
        parts.append(str(reason_why).strip())
    elif entry.get("effectiveness"):
        parts.append(str(entry.get("effectiveness")).strip())
    facts = " ".join(p for p in parts if p).strip()
    sources = _split_sources(entry.get("source"))
    return facts, sources


# ---------------------------------------------------------------------------
# LLM simplification (language only, zero new facts)
# ---------------------------------------------------------------------------

def _simplify_with_ollama(medicine_name, raw_facts):
    prompt = (
        "Explain in 1-2 short simple sentences a non-medical person can "
        f"understand how {medicine_name} helps the body, using ONLY these "
        f"real facts: {raw_facts}. Do not add any fact, number, timeframe, "
        "adjective of degree, or claim that is not explicitly stated in "
        "those facts. Stay strictly grounded in the given facts, with no "
        "embellishment. Respond with JSON only in the form "
        '{"explanation": "..."}.'
    )
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1},
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        body = resp.json()
        text = body.get("response", "")
        parsed = json.loads(text)
        explanation = parsed.get("explanation")
        if explanation and isinstance(explanation, str) and explanation.strip():
            return explanation.strip()
    except Exception:
        pass

    truncated = raw_facts.strip()
    if len(truncated) > 220:
        truncated = truncated[:217].rstrip() + "..."
    return truncated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_ranked_medicines(disease_id: str, limit: int = 10) -> list:
    """Return the real, effectiveness-ordered list of medicines for a disease.

    Each item: {"name": str, "effectiveness_pct": float|None, "is_curative": bool,
                "simple_explanation": str, "sources": list[str]}
    """
    diseases = _load_disease_master()
    disease = diseases.get(disease_id)
    if not disease:
        return []

    rows = _extract_ranked_rows(disease)
    if not rows:
        return []

    curative_name = None
    curative_option = disease.get("curative_option")
    if isinstance(curative_option, dict):
        curative_name = curative_option.get("name")

    survey_entries = _extract_survey_entries(disease)
    name_cleanup_map = _load_name_cleanup_map()

    results = []
    for row in rows:
        # Real bug found, 2026-09-28: this used to break out of the loop as
        # soon as `limit` real medicines had been collected IN THE RAW
        # disease_master.json ROW ORDER, not by effectiveness. Since the
        # filters above (device/class/lifestyle exclusion) can reject rows
        # ahead of a real, highly-effective one further down the table (e.g.
        # migraine's real 82%-effective "Prochlorperazine" row appears after
        # several lower/no-effectiveness rows), a real >=40%-effective
        # medicine could be silently cut off purely by table position. All
        # qualifying rows are now collected first and sorted by effectiveness
        # below; the `limit` is applied only after sorting, and is widened to
        # never drop a real medicine with effectiveness_pct >= 40 (see the
        # founder's firm rule: every real medicine from 40% to 100% must
        # always be shown).

        name = row.get("name")

        # Real, verified per-raw-name cleanup map (data/medicine_name_cleanup_map.json,
        # built from an exhaustive pass over every unique name in
        # disease_master.json's ranked tables) takes priority over the
        # regex-based clean_medicine_name() below. A "low" confidence entry
        # could not be confidently reduced to a single real name, so per the
        # purchasable-only exclusion rule it is excluded outright rather than
        # shown as an uncertain/possibly-wrong name.
        mapping = name_cleanup_map.get(name)
        if mapping and mapping.get("confidence") == "low":
            continue

        # Only real, purchasable medicines/injections/equipment are ever
        # surfaced to the customer. Real disease_master.json ranked tables
        # also contain genuine clinical entries that are NOT a purchasable
        # product -- diet/lifestyle/physiotherapy/surgery/exercise-programme
        # entries, or general risk-factor recommendations (e.g. "Treatment of
        # tinea pedis and other skin-barrier breaks"). Rather than chasing an
        # ever-growing list of keyword patterns, this cross-references every
        # ranked row (using its cleaned leading name, so descriptive noise
        # like "vs rivaroxaban" doesn't dilute the match) against the real,
        # known drug list in medicine_details.json (~3,126 real medicines,
        # itself scrubbed of its own handful of non-drug entries) -- a row
        # that does not reasonably match a real drug name there is excluded
        # outright, and a direct pattern check catches anything that still
        # slips past the fuzzy match.
        if _is_non_drug_intervention(name):
            continue

        # Bare drug-class labels ("JAK inhibitor", "NSAIDs") and malformed
        # sentence-fragment/multi-component-regimen "names" are never a
        # single purchasable medicine -- checked on the raw name up front so
        # a row like "NSAIDs versus placebo (acute flare)" is excluded
        # regardless of what the cleanup map or clean_medicine_name() later
        # reduce it to.
        is_validated_combination = bool(mapping and mapping.get("method") == "validated_combination")

        if _looks_like_drug_class_only(name) or _looks_like_malformed_fragment(name, is_validated_combination):
            continue

        is_map_verified = bool(mapping and mapping.get("confidence") == "high" and mapping.get("cleaned_name"))
        candidate_name = mapping["cleaned_name"] if is_map_verified else clean_medicine_name(name)

        # Re-check the same non-drug/class/fragment signals on the cleaned
        # candidate name -- clean_medicine_name()/the cleanup map can surface
        # a short "Bariatric surgery" / "Structured physiotherapy" / "NSAIDs"
        # style name that the raw-name checks above missed because the
        # non-drug word wasn't in the leading position of the fuller raw text.
        if (
            _is_non_drug_intervention(candidate_name)
            or _is_non_drug_candidate_name(candidate_name)
            or _looks_like_drug_class_only(candidate_name)
            or _looks_like_malformed_fragment(candidate_name, is_validated_combination)
        ):
            continue

        # The cleanup map's "high confidence" only certifies that the text
        # extraction is clean, not that the result is a purchasable medicine.
        # Verified by hand, 2026-09-28 against real samples from every
        # mapping "reason" bucket: only two reasons reliably mean "this is a
        # real, specific compound name" without needing further proof --
        # everything else (device/procedure names; bare acronyms like CPAP/
        # UPPP/TAVR that are just as often a procedure as a drug; "short
        # capitalized phrase (plausible name)", which mixes real undocumented
        # drugs like Shingrix with real non-drug rows like "Positional
        # therapy"/"Non-Invasive Ventilation"/"Smoking Cessation"/"Newborn-
        # screening-identified SCID"; and "too many words after cleaning",
        # which is the map's own admission the text is still a descriptive
        # sentence, not a name) is trusted ONLY when it ALSO has a real,
        # corroborating medicine_details.json match (e.g. "Extended-release
        # buprenorphine injection" really does match a real buprenorphine
        # record; "Dupilumab" matches a real dupilumab record).
        mapping_reason = (mapping.get("reason") or "") if mapping else ""
        is_bare_acronym = bool(re.match(r"^[A-Z0-9]{2,6}$", candidate_name.strip()))
        is_trusted_reason = mapping_reason in _TRUSTED_BYPASS_REASONS and not is_bare_acronym

        matched_details = _match_medicine_details(candidate_name)
        if matched_details is None:
            # A map-verified name is trusted on its own only when its own
            # reason is one of the two reliable ones above; anything else
            # (including a name that isn't in the map at all) requires a real
            # fuzzy-match hit against medicine_details.json to be included.
            if not is_map_verified or not is_trusted_reason:
                continue
        elif _is_device_note(matched_details[1].get("note")):
            # Defense in depth: _medicine_index() already excludes
            # device-noted records, so this should be unreachable, but a
            # device/procedure-labelled row must never display real facts
            # borrowed from an unrelated device record either.
            continue

        effectiveness_pct = row.get("effectiveness_pct")
        try:
            effectiveness_pct = float(effectiveness_pct) if effectiveness_pct is not None else None
        except (TypeError, ValueError):
            effectiveness_pct = None

        row_source = _split_sources(row.get("source"))

        raw_facts = ""
        facts_sources = []

        # Real bug found and fixed here, 2026-09-28 (reproduced live): the
        # disease's own exhaustive_medicine_survey entry for a medicine is
        # ALWAYS specific to this exact disease (that is its entire purpose),
        # while a medicine_details.json record is one universal per-drug
        # record that may only document a completely different real
        # indication for the same drug -- e.g. the one real "Duloxetine"
        # record in medicine_details.json documents dosage/mechanism ONLY for
        # stress urinary incontinence, so showing it under Osteoarthritis
        # produced a technically-real but disease-irrelevant explanation
        # ("...urethral sphincter tone...") even though the disease's own
        # oa_duloxetine survey entry has the real, correct OA-pain mechanism
        # (central pain-pathway modulation) right there. The disease-specific
        # survey entry is therefore tried FIRST; medicine_details.json is
        # used only when this disease's own survey has no real facts for the
        # medicine at all.
        # Match on candidate_name (the already-cleaned canonical name, e.g.
        # "Duloxetine"), not the raw row name (e.g. "Duloxetine >=50% pain
        # responder rate versus placebo") -- the raw row name's own
        # statistical/trial-arm suffix is never going to be a subset of a
        # survey entry's descriptive title, so matching on it defeats the
        # subset check above even when the medicine itself clearly matches.
        matched_survey = _match_survey_entry(candidate_name, survey_entries)
        if matched_survey is not None:
            raw_facts, facts_sources = _facts_from_survey_entry(matched_survey)

        if not raw_facts and matched_details is not None:
            _, record = matched_details
            status = str(record.get("research_status") or "")
            if status.startswith("complete") or status.startswith("partial"):
                raw_facts, facts_sources = _facts_from_medicine_details(record)

        sources = []
        for s in (facts_sources + row_source):
            if not s:
                continue
            if any(s == existing or s in existing or existing in s for existing in sources):
                continue
            sources.append(s)

        display_name = candidate_name

        # Ollama simplification is deferred until after sorting/truncation
        # below (see there) -- calling it here, for every row that passes the
        # real-medicine filters, would waste time simplifying rows that get
        # cut by the limit anyway now that ALL qualifying rows are collected
        # up front instead of stopping at the first `limit` found.
        results.append({
            "name": display_name,
            "effectiveness_pct": effectiveness_pct,
            "is_curative": is_curative_match(name, curative_name),
            "raw_facts": raw_facts,
            "sources": sources,
        })

    # Real bug found, 2026-09-28: real, highly-effective medicines (e.g.
    # migraine's Prochlorperazine at 82%, Dihydroergotamine at 67%) were
    # missing from the API response purely because they sat lower in
    # disease_master.json's raw ranked-table order than `limit` other rows
    # that happened to pass the filters first -- the old code returned
    # whichever `limit` real medicines it hit FIRST while scanning the table,
    # not the `limit` most effective ones. Sort by effectiveness_pct
    # descending (unknown-effectiveness rows last, in their original relative
    # order) so the API always returns medicines highest-effectiveness first.
    results.sort(key=lambda r: (r["effectiveness_pct"] is None, -(r["effectiveness_pct"] or 0.0)))

    # Firm rule: every real medicine with effectiveness_pct >= 40 must always
    # be returned, never cut off by `limit` -- `limit` still caps how many
    # additional lower-effectiveness/undocumented-effectiveness medicines are
    # included beyond that guaranteed set. Since the list above is already
    # sorted descending (with unknowns last), every >=40% row is contiguous
    # at the front, so this is a single slice.
    guaranteed_count = sum(
        1 for r in results if r["effectiveness_pct"] is not None and r["effectiveness_pct"] >= 40
    )
    results = results[: max(limit, guaranteed_count)]

    for r in results:
        raw_facts = r.pop("raw_facts")
        if raw_facts:
            r["simple_explanation"] = _simplify_with_ollama(r["name"], raw_facts)
        else:
            r["simple_explanation"] = NOT_DOCUMENTED_MESSAGE

    return results


if __name__ == "__main__":
    import sys
    did = sys.argv[1] if len(sys.argv) > 1 else "cataract"
    out = get_ranked_medicines(did)
    print(json.dumps(out, indent=2))
