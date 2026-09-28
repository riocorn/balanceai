"""
BalanceAI -- Master Medicine & Injection Reference Table (Real Pharmaceutical Agents Only).

CORRECTION OF PRIOR SCOPING MISTAKE (2026-09-24): the previous version of this script
built a table containing EVERY named entry recursively collected from
exhaustive_medicine_survey / curative_option -- surgeries, procedures, physical/voice/
behavioural therapies, devices, lifestyle/dietary advice, rehabilitation, monitoring, etc,
all mixed in as rows alongside real medicines. The user's explicit correction: "chemical
salt name pure hona chahiye pdf me, bas medicine aur injection ka baat ho raha hai, other
treatment ka nahi" -- the table must contain ONLY real pharmaceutical medicines and
injections (an actual administrable substance with a real chemical/generic/brand-salt
name: tablets, capsules, injections, drops, ointments, topical creams, oral suspensions,
biologics, vaccines, or a named supplement formulation with defined compound doses like
AREDS2). It must EXCLUDE surgery/procedures, non-drug therapies (voice/physical/
occupational/speech/behavioural/psychotherapy/CBT), radiotherapy-as-a-procedure (its
companion chemo drugs, e.g. cisplatin, ARE included -- only the radiation-delivery
technique itself is excluded), devices/implants/prostheses, diet/lifestyle modification
with no named compound, rehabilitation, monitoring/surveillance, and vague category
labels with no specific compound name of their own (e.g. "Intranasal Corticosteroid
Spray" names no salt and is excluded; "Ranibizumab / Aflibercept / Bevacizumab" are each
included as their own row, not collapsed into the "anti-VEGF injections" category label).

CLASSIFICATION RULE (calibrated empirically against real KB entries -- cataract,
age_related_macular_degeneration, vocal_cord_nodules, deviated_nasal_septum,
diabetic_retinopathy, and ~15 more, plus a full pass over all 3,958 unique
specific_drugs strings in the KB, manually spot-checked in batches):

  1. Every named entry is still collected exactly as before (recursive collector over
     exhaustive_medicine_survey and curative_option -- unchanged, see
     _collect_named_entries()).
  2. Per entry, the candidate drug-name text is:
       - each string in the entry's "specific_drugs" list, if present (this is the
         KB's own most granular, most reliable per-compound field -- e.g. AMD's
         anti-VEGF entry carries specific_drugs = ["Ranibizumab 0.5 mg intravitreal
         injection", "Aflibercept ...", "Bevacizumab ..."], each becoming its own row);
       - otherwise the entry's own "name" field.
  3. A candidate string that is itself a class-label wrapping an explicit parenthetical
     list of >=2 named compounds (e.g. "Somatostatin analogues (Octreotide,
     Lanreotide)", "GLP-1 Agonist Pharmacotherapy (Tirzepatide, Semaglutide)") is split
     so each named compound becomes its own row -- this is the exact mechanism the
     user's AMD anti-VEGF example calls for, generalised to every disease.
  4. Each resulting candidate string (whole, or split piece) is classified drug vs
     non-drug by is_drug_text(): a broad EXCLUDE_STRONG_RE first flags surgical/
     procedural/device/therapy/diet/monitoring/radiotherapy-as-procedure/blood-product/
     IV-fluid/oxygen language; BUT if the same string also names a real administrable
     compound (a dose number, a recognised generic-drug suffix such as -mab/-pril/
     -statin/-cillin/-mycin/..., a drug-specific route phrase such as "intrathecal
     tofersen", or a small whitelist of common drugs whose names carry no
     distinctive suffix, e.g. tacrolimus, cyclosporine, cisplatin's radiotherapy-
     adjacent peers), the real compound wins and the row IS included -- this is what
     correctly keeps "Cisplatin (given concurrently with daily radiotherapy)",
     "Verteporfin (intravenous infusion, then laser activation)" [PDT's drug, not
     the laser procedure], "Dexamethasone intravitreal implant 0.7 mg (Ozurdex)"
     [a real drug-eluting implant, not a bare device], and perioperative antibiotics
     given alongside a named surgery, while still dropping "Watchman FLX device",
     "Cognitive Behavioral Therapy (CBT)", "Total Knee Arthroplasty", "Intranasal
     Corticosteroid Spray Plus Saline Spray" (a vague class label naming no specific
     salt), "Normal saline nasal irrigation", and "Supplemental Oxygen".
  5. For a candidate drawn from an entry's own "name" field (no specific_drugs list
     present), an additional vague-category gate applies first: is_vague_category()
     tokenises the name and drops it if every token is a generic pharmacology/route/
     formulation noun (spray, drop, corticosteroid, topical, therapy, supplement, ...)
     with no proper compound name surviving -- this is what correctly drops
     deviated_nasal_septum's generic "Intranasal Corticosteroid Spray Plus Saline
     Spray" (no named salt anywhere in it) while keeping "Calcitriol (1,25-(OH)2-D3,
     active hormone)" and "Rotigotine Transdermal Patch (brand: Neupro)" (a real
     compound name survives the tokenisation).

This two-stage design (specific-compound extraction from specific_drugs/parenthetical
lists FIRST, drug-vs-procedure classification SECOND, vague-category gate only on the
bare-name fallback path) is what lets a single disease end up with real drug rows drawn
from an otherwise mostly-surgical survey (e.g. diabetic_retinopathy's anti-VEGF/
corticosteroid-implant entries survive even though panretinal photocoagulation and
vitrectomy in the same survey are correctly dropped), while a purely-surgical/
behavioural disease (deviated_nasal_septum, vocal_cord_nodules) can legitimately end up
with zero qualifying rows -- reported honestly below, not treated as a bug.

Effectiveness-%% matching, curative-flag merging against curative_option, and the
reportlab category -> disease -> row grouping/styling are otherwise unchanged from the
prior version of this script.
"""
import json
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

ROOT = Path("/home/abhay/Downloads/medical/balanceai")
SNAPSHOT = Path(
    "/tmp/claude-1000/-home-abhay/745550ad-74ad-4919-9b55-49194446d148/scratchpad/disease_master_snapshot.json"
)
SRC_PATH = SNAPSHOT if SNAPSHOT.exists() else (ROOT / "data" / "disease_master.json")
DATA = json.loads(SRC_PATH.read_text(encoding="utf-8"))
OUT_PDF = ROOT / "data" / "BalanceAI_Master_Medicine_Table.pdf"
ROW_LOG_PATH = Path(
    "/tmp/claude-1000/-home-abhay/745550ad-74ad-4919-9b55-49194446d148/scratchpad/medicine_table_row_log.json"
)

# ============ colour/font scheme reused from generate_disease_prescription_pdf.py ============
GREEN = colors.HexColor("#1d5c3d")
GREEN_LT = colors.HexColor("#eef7f2")
CORAL = colors.HexColor("#c0392b")
GREY = colors.HexColor("#5a6571")
GOLD = colors.HexColor("#d4a043")
BLACK = colors.black
WHITE = colors.white

styles = getSampleStyleSheet()
title_s = ParagraphStyle("title", parent=styles["Title"], textColor=GREEN, fontSize=18, alignment=TA_CENTER)
subtitle_s = ParagraphStyle("subtitle", parent=styles["BodyText"], textColor=GREY, fontSize=9.0,
                             alignment=TA_CENTER, spaceAfter=4, leading=12)
meta_s = ParagraphStyle("meta", parent=styles["BodyText"], textColor=GREY, fontSize=8.2,
                         alignment=TA_CENTER, spaceAfter=10)

cat_cell_s = ParagraphStyle("cat_cell", parent=styles["BodyText"], textColor=WHITE,
                             fontName="Helvetica-Bold", fontSize=11.5, leading=13.5)
dis_cell_s = ParagraphStyle("dis_cell", parent=styles["BodyText"], textColor=WHITE,
                             fontName="Helvetica-Bold", fontSize=9.3, leading=11)
hdr_cell_s = ParagraphStyle("hdr_cell", parent=styles["BodyText"], textColor=WHITE,
                             fontName="Helvetica-Bold", fontSize=8.2, leading=9.8, alignment=TA_CENTER)
name_cell_s = ParagraphStyle("name_cell", parent=styles["BodyText"], fontSize=7.7, leading=9.2)
dosage_cell_s = ParagraphStyle("dosage_cell", parent=styles["BodyText"], fontSize=7.2, leading=8.6, textColor=GREY)
eff_cell_s = ParagraphStyle("eff_cell", parent=styles["BodyText"], fontSize=7.6, leading=9.0, alignment=TA_CENTER)
cur_cell_s = ParagraphStyle("cur_cell", parent=styles["BodyText"], fontSize=7.6, leading=9.0,
                             alignment=TA_CENTER, textColor=CORAL, fontName="Helvetica-Bold")
notcur_cell_s = ParagraphStyle("notcur_cell", parent=styles["BodyText"], fontSize=7.6, leading=9.0,
                                alignment=TA_CENTER, textColor=GREY)
source_cell_s = ParagraphStyle("source_cell", parent=styles["BodyText"], fontSize=6.6, leading=7.9, textColor=GREY)
empty_row_s = ParagraphStyle("empty_row", parent=styles["BodyText"], fontSize=7.6, leading=9.0,
                              textColor=GREY, fontName="Helvetica-Oblique")


# ============ generic extraction/matching helpers (mirrors pharmacy_service.py's approach) ============

def _normalize_tokens(text) -> set:
    text = (text or "")
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z]", " ", text)
    tokens = set()
    for w in text.split():
        w = w.replace("ae", "e").replace("oe", "e")
        if len(w) > 2:
            tokens.add(w)
    return tokens


def _score_name_match(a, b) -> int:
    return len(_normalize_tokens(a) & _normalize_tokens(b))


def _ranked_list(effectiveness_ranked_table):
    if isinstance(effectiveness_ranked_table, list):
        return effectiveness_ranked_table
    if isinstance(effectiveness_ranked_table, dict):
        rr = effectiveness_ranked_table.get("ranked_high_to_low")
        return rr if isinstance(rr, list) else []
    return []


def _collect_named_entries(node, out: list) -> None:
    """Recursively collect every dict carrying a non-empty string "name" key,
    anywhere under `node`, continuing to descend into that same dict's other
    fields afterward. Unchanged from the prior version of this script."""
    if isinstance(node, dict):
        nm = node.get("name")
        if isinstance(nm, str) and nm.strip():
            out.append(node)
        for v in node.values():
            _collect_named_entries(v, out)
    elif isinstance(node, list):
        for item in node:
            _collect_named_entries(item, out)


def _fmt_pct(pct) -> str:
    if pct is None:
        return "—"
    if isinstance(pct, (int, float)):
        return f"{pct:g}%"
    s = str(pct).strip()
    if not s:
        return "—"
    return s if "%" in s else f"{s}%"


def _text(v, limit=None) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        v = "; ".join(str(x) for x in v if isinstance(x, str))
    v = str(v)
    v = v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if limit and len(v) > limit:
        v = v[: limit - 1].rstrip() + "…"
    return v


# ============ drug-vs-procedure classification (the actual scope fix) ============

DOSE_RE = re.compile(
    r'\d+(\.\d+)?\s*(mg|mcg|microg|g/day|iu|ml|units?|mg/kg|mg/m2|mg/m²|meq)\b'
    r'|\d+(\.\d+)?\s*%\s*\w*\s*(solution|ointment|cream|gel|drops?|spray|suspension|w/v)', re.I)

ROUTE_OVERRIDE_RE = re.compile(
    r'\b(intrathecal(ly)?|intravitreal(ly)?|subcutaneous(ly)?|intravenous(ly)?|'
    r'intramuscular(ly)?|transdermal patch|sublingual(ly)?|'
    r'intracameral|intraarticular|intra-articular|epidural)\b', re.I)

SUFFIX_RE = re.compile(
    r'\b\w+(mab|nib|tinib|ciclib|parib|zumab|ximab|umab|oxetine|triptan|sartan|pril|olol|dipine|'
    r'statin|prazole|azole|cillin|mycin|micin|cycline|floxacin|conazole|navir|parin|caine|azepam|'
    r'barbital|glutide|gliflozin|gliptin|dronate|mustine|platin|rubicin|taxel|limumab|vudine|profen|'
    r'oxacin|sone|olone|thiazide|pramine|zolam|setron|afil|vir|zosin|bactam|purinol|ostat|opram|'
    r'axine|icline|calcet)\b', re.I)

CEF_RE = re.compile(r'\bcef[a-z]{3,}\b', re.I)

KNOWN_DRUG_NAMES = {
    'tacrolimus', 'cyclosporine', 'ciclosporin', 'methotrexate', 'cinacalcet', 'phenoxybenzamine',
    'doxazosin', 'allopurinol', 'febuxostat', 'varenicline', 'sertraline', 'escitalopram',
    'venlafaxine', 'metronidazole', 'tinidazole', 'rifampin', 'rifampicin', 'gentamicin',
    'tamsulosin', 'silodosin', 'terazosin', 'prazosin', 'alfuzosin', 'diazoxide', 'lidocaine',
    'bupivacaine', 'ropivacaine', 'heparin', 'warfarin', 'digoxin', 'metformin', 'insulin',
    'levodopa', 'carbidopa', 'phenytoin', 'fosphenytoin', 'lamotrigine', 'gabapentin',
    'pregabalin', 'baclofen', 'colchicine', 'lithium', 'clozapine', 'olanzapine',
    'risperidone', 'haloperidol', 'quetiapine', 'aripiprazole', 'sildenafil', 'tadalafil',
    'octreotide', 'lanreotide', 'atropine', 'pyridostigmine', 'prednisone', 'prednisolone',
    'pyridoxine',
    'hydrocortisone', 'fludrocortisone', 'imipramine', 'clomipramine', 'levonorgestrel',
    'etonogestrel', 'ulipristal', 'medroxyprogesterone', 'tofersen', 'nusinersen',
    'riboflavin', 'verteporfin', 'lanosterol', 'pilocarpine', 'timolol', 'salbutamol',
    'epinephrine', 'amiodarone', 'mexiletine', 'nadolol', 'propranolol', 'clopidogrel',
    'nitroprusside', 'dobutamine', 'milrinone', 'norepinephrine', 'vasopressin',
    'phenylephrine', 'levosimendan',
}

EXCLUDE_STRONG_RE = re.compile(
    r'\b(surg(er|ical|ically)|laparoscop|arthroplasty|arthroscop|gastrectomy|gastroplasty|'
    r'endarterectomy|thoracentesis|septoplasty|septorhinoplasty|phacoemulsification|vitrectomy|'
    r'mastectomy|colectomy|appendectomy|excision|resection|debridement|amputation|anastomosis|'
    r'curettage|cauteriz|\bcautery\b|cryotherapy|cryosurgery|'
    r'reconstructive surgery|bariatric surgery|transplant|transplantation|grafting|stenting|'
    r'angioplasty|lithotripsy|\bprocedure\b|ablation(?! .*(psoralen|verteporfin|riboflavin))|'
    r'\bdevice\b|prosthe|valve replacement|mechanical valve|bioprosthetic|pacemaker|'
    r'defibrillator|\bstents?\b|\bballoons?\b|\bcatheter\w*\b|\bimplant\w*\b|\bbraces?\b|\bsplints?\b|'
    r'orthosis|orthotic|wheelchair|\bcanes?\b|\bwalkers?\b|hearing aid|cochlear implant|spectacles|'
    r'contact lens|\bcpap\b|\bbipap\b|\bapap\b|oxygen concentrator|pulse oximet|ecg monitor|'
    r'telemetry|icp monitor|external ventricular drain|dialysis machine|mechanical ventilat|'
    r'feeding tube|biopsy kit|fna kit|diagnostic ultrasound|rfa generator|electrode\b|'
    r'stimulator|neurostimulator|\bsystem\s*\(|'
    r'voice therapy|physical therapy|physiotherapy|occupational therapy|speech therapy|'
    r'hand therapy|psychotherapy|cognitive beha?vioral|\bcbt\b|\bdbt\b|dialectical behavior|'
    r'cognitive therapy|behavio(u)?ral (therapy|intervention|treatment|parent training)|'
    r'exposure therapy|biofeedback|counsel(l)?ing|hypnotherapy|mindfulness|relaxation training|'
    r'breathing retraining|classroom behavio(u)?ral|'
    r'\bdiet\b(?! soft)|lifestyle modification|exercise programme|exercise program\b|weight loss program|'
    r'smoking cessation counsel|foot hygiene|moisture control|patient education|activity modification|'
    r'pulmonary rehabilitat|cardiac rehabilitat|vestibular rehabilitat|vision rehabilitat|'
    r'low-vision rehabilitat|rehabilitation\b|'
    r'radiotherapy|radiation therapy|brachytherapy|stereotactic radiosurgery|proton beam|'
    r'photocoagulation|photodynamic therapy|phototherapy|'
    r'multidisciplinary .*team|standardi[sz]ed .*protocol|escalation protocol|care-delivery model|'
    r'strategy comparison|management strategy|not a drug class|not a pharmaceutical|not a drug\b|'
    r'not a medicine\b|'
    r'not applicable\b|no drug\b|no medicine\b|no pharmacolog|selection criteri|'
    r'screening/eligibility|risk-stratification|clinical prediction rule|'
    r'\bn/a\b|audiometry|bioelectrical impedance|intragastric balloon|endoscopic suturing device|'
    r'pneumatic compression device|excimer laser|stapling device|infrared coagulation probe|'
    r'compression (stocking|garment)|watchman|amplatzer|farapulse|intrathecal baclofen pump|'
    r'\boxygen\b|crystalloid|colloid|ringer|hartmann|normal saline|\bsaline\b|whole blood|'
    r'packed red blood cell|platelet transfusion|fresh frozen plasma|blood transfusion|'
    r'red[- ]cell transfusion|'
    r'non-pharmacolog|not pharmacolog|intraocular lens|\biol\b|corrective glasses|\bspectacle|'
    r'dilator strip|nasal strip|orthokeratology|watchful waiting|spontaneous resolution|'
    r'nutritional support|caloric (intake|support)|enteral nutrition|parenteral nutrition|'
    r'therapeutic ultrasound|\bacupuncture\b|\byoga\b|tai chi|'
    r'thoracostomy|chest tube|\bdrainage\b|\btransfusion\b|stretching exercise|'
    r'causative (drug|agent) trigger|discontinuation of the (causative|offending|suspected)|'
    r'identification and discontinuation|causative toxic agent|'
    r'withdrawal (of|or dose reduction of) the causative|'
    r'spirometer|spirometry|sugar-sweetened|soft drinks?\b|early mobili[sz]ation|'
    r'not a specific drug)',
    re.I)

GENERIC_STOPWORDS = {
    'intranasal', 'nasal', 'oral', 'topical', 'corticosteroid', 'corticosteroids', 'steroid',
    'steroids', 'spray', 'drop', 'drops', 'cream', 'ointment', 'gel', 'tablet', 'tablets',
    'capsule', 'capsules', 'injection', 'injections', 'therapy', 'treatment', 'treatments',
    'medication', 'medications', 'drug', 'drugs', 'agent', 'agents', 'formula', 'saline',
    'supplement', 'supplementation', 'antibiotic', 'antibiotics', 'analgesic', 'analgesics',
    'anti-inflammatory', 'inflammatory', 'inhibitor', 'inhibitors', 'antagonist', 'antagonists',
    'agonist', 'agonists', 'blocker', 'blockers', 'diuretic', 'diuretics', 'laxative',
    'laxatives', 'hormone', 'hormonal', 'replacement', 'plus', 'and', 'or', 'with', 'for',
    'the', 'of', 'a', 'an', 'real', 'first', 'line', 'first-line', 'standard', 'management',
    'control', 'regimen', 'dose', 'dosing', 'combined', 'combination', 'care', 'solution',
    'irrigation', 'wash', 'rinse', 'patch', 'transdermal', 'subcutaneous', 'intravenous',
    'intramuscular', 'sublingual', 'rectal', 'vaginal', 'ophthalmic', 'otic', 'inhaled',
    'inhaler', 'nebulizer', 'nebulised', 'nebulized', 'pharmacotherapy', 'pharmacologic',
    'pharmacological', 'dual', 'glp', 'gip', 'active', 'options', 'option',
    'antidepressant', 'antidepressants', 'antihypertensive', 'antihypertensives',
    'anticoagulant', 'anticoagulants', 'antipsychotic', 'antipsychotics', 'anxiolytic',
    'anxiolytics', 'bronchodilator', 'bronchodilators', 'antiemetic', 'antiemetics',
    'antipyretic', 'antipyretics', 'immunosuppressant', 'immunosuppressants',
    'antiplatelet', 'antiplatelets', 'alone',
}

PAREN_LIST_RE = re.compile(r'\(([A-Z][A-Za-z0-9\-\s/]*?(?:,\s*[A-Z][A-Za-z0-9\-\s/]*?){1,})\)')
CITATION_WORD_RE = re.compile(
    r'\b(19|20)\d{2}\b|\btrial\b|\bstudy\b|\bstudies\b|\bcomparator\b|\barm\b|\bguideline\b|'
    r'\bprotocol\b|\bgroup\b|\bet al\b|\bcochrane\b|\breview\b|\bregimen\b|\bpmid\b', re.I)
DRUG_CLASS_PREFIX_RE = re.compile(
    r'\b(analog(ue)?s?|agonists?|antagonists?|inhibitors?|blockers?|antibiotics?|'
    r'chelators?|pharmacotherapy|vaccines?|immunosuppress\w*|antivirals?|'
    r'anticoagulants?|nsaids?|ssris?|snris?|statins?|biologics?|monoclonal antibod\w*|'
    r'chemotherap\w*|corticosteroids?|antimetabolites?|bisphosphonates?|diuretics?|'
    r'triptans?|opioids?|implants?)\b', re.I)
BARE_STRING_TITLE_RE = re.compile(r':\s+(?=[a-z])')

_METADATA_KEYS = {
    "note", "source", "confidence", "effectiveness", "effectiveness_pct",
    "effectiveness_metric", "reason_why", "type", "important_caveat",
    "real_working_solution", "name", "citation", "citations", "references",
    "pmid", "url", "accessed", "accessed_date", "doctor_reference_only",
    "caveat", "mechanism", "summary", "specific_drugs",
}
_METADATA_KEY_HINT_RE = re.compile(
    r'curative_and|what_is|summary|overview|comparison|_vs_|caveat|limitation|'
    r'evidence_grade|real_world_context|honest|disclaimer|scope_note|key_takeaway',
    re.I)

DOSAGE_EXTRACT_RE = re.compile(
    r'(\d+(?:\.\d+)?\s*(?:mg|mcg|microg|g|iu|ml|units?)(?:/(?:kg|m2|m²|day))?'
    r'(?:[^.;]{0,45})?)', re.I)
DOSAGE_PCT_TOKEN_RE = re.compile(r'\d+(?:\.\d+)?\s*%')


def _override_signal(text: str) -> bool:
    tl = text.lower()
    if DOSE_RE.search(text) or SUFFIX_RE.search(text) or CEF_RE.search(text):
        return True
    if ROUTE_OVERRIDE_RE.search(text):
        return True
    return any(re.search(r'\b' + re.escape(k) + r'\b', tl) for k in KNOWN_DRUG_NAMES)


def is_drug_text(text: str) -> bool:
    """Primary drug-vs-non-drug gate for a specific_drugs string (or a bare entry
    name, see is_vague_category for that path's extra gate). See module docstring
    point 4 for the exact reasoning."""
    if not text:
        return False
    if EXCLUDE_STRONG_RE.search(text):
        return _override_signal(text)
    return True


def is_vague_category(name: str) -> bool:
    """Second gate, used only for the bare entry-name fallback (no specific_drugs
    list present): drop a name if every token in it is a generic pharmacology/
    route/formulation noun with no surviving proper compound name. See module
    docstring point 5."""
    core = re.split(r'\s+--\s+|\s+-\s+Real\b', name)[0]
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'\-]*", core.lower())
    tokens = [t for t in tokens if t]
    if not tokens:
        return True
    return all(t in GENERIC_STOPWORDS for t in tokens)


def _split_one_clause(s: str):
    """Split a single class-label clause ending in a parenthetical list of >=2
    named compounds into one (name, prefix, suffix) tuple per compound. Returns
    [] unless the parenthetical looks like a genuine drug-name list: no
    citation/trial-name words, the prefix names an actual drug class (so a
    subgroup/criteria list like "Early Liver Transplantation (Steroid
    Non-Responders, Strict Selection)" or a device parts list like "VATS
    Equipment (Thoracoscope, Endostaplers, Ports)" is correctly rejected), and
    none of the individual names is itself flagged as non-drug text. See module
    docstring point 3."""
    m = PAREN_LIST_RE.search(s)
    if not m:
        return []
    names = [n.strip() for n in m.group(1).split(',') if n.strip()]
    if len(names) < 2:
        return []
    if any(CITATION_WORD_RE.search(nm) for nm in names):
        return []
    prefix = s[:m.start()].strip(' -')
    if not DRUG_CLASS_PREFIX_RE.search(prefix):
        return []
    if any(EXCLUDE_STRONG_RE.search(nm) and not _override_signal(nm) for nm in names):
        return []
    suffix = s[m.end():].strip(' -.;')
    return [(nm, prefix, suffix) for nm in names]


def _split_top_level(s: str, sep: str = ';'):
    """Split `s` on `sep` only where it is not nested inside parentheses, so a
    semicolon used INSIDE a single compound's own explanatory parenthetical
    (e.g. "Lanosterol (investigational compound; no approved ophthalmic drug
    product or brand exists)") is not mistaken for a clause boundary."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(s):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth = max(0, depth - 1)
        elif ch == sep and depth == 0:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def split_named_compounds(s: str):
    """Split `s` on ';'-separated clauses first (several KB specific_drugs
    strings bundle multiple independent drug-class mentions into one string,
    e.g. "Somatostatin analogues (Octreotide, Lanreotide); Diazoxide for
    insulinoma...; Proton pump inhibitors (Omeprazole, Pantoprazole)"), then
    applies _split_one_clause to each. Returns [] if nothing in `s` contains a
    genuine named-compound list (caller then falls back to treating the whole
    of `s` as a single candidate)."""
    clauses = [c.strip() for c in _split_top_level(s, ';') if c.strip()]
    if len(clauses) <= 1:
        return _split_one_clause(s)
    out = []
    for clause in clauses:
        got = _split_one_clause(clause)
        if got:
            out.extend(got)
        elif is_drug_text(clause):
            out.append((clause, "", ""))
    return out


def extract_bare_string_entries(container):
    """Some diseases (myopia, molluscum_contagiosum, and a handful of stray keys
    elsewhere) store exhaustive_medicine_survey values as plain narrative strings
    rather than the usual {"name": ..., ...} dicts, so _collect_named_entries()
    never sees them (it only walks dict/list nodes). Recover a usable pseudo-entry
    from each such string: this KB's convention is "<Header sentence>: <body...>"
    (the header may itself contain a redundant leading disease-name clause, e.g.
    "Molluscum Contagiosum -- Cantharidin 0.7% w/v Topical Solution (VP-102/
    YCANTH), Real ...: <body>"), so the header text up to the first colon that
    introduces a lowercase-starting body is used as the pseudo-entry "name" --
    good enough for the drug/procedure classifier, and the full string is kept
    as the source of any dose figures for the dosage column."""
    out = []
    if not isinstance(container, dict):
        return out
    for key, v in container.items():
        if key in _METADATA_KEYS or _METADATA_KEY_HINT_RE.search(key) or not isinstance(v, str) or not v.strip():
            continue
        v = v.strip()
        if len(v) < 200:
            continue
        parts = BARE_STRING_TITLE_RE.split(v, maxsplit=1)
        if len(parts) != 2 or not parts[0].strip():
            continue
        header = parts[0].strip()
        out.append({"name": header, "type": "", "specific_drugs": None,
                    "source": "", "_full_text": v})
    return out


def extract_dosage(s: str) -> str:
    m = DOSAGE_EXTRACT_RE.search(s or "")
    if m:
        return m.group(1).strip(" ,;")
    pct_tokens = []
    for tok in DOSAGE_PCT_TOKEN_RE.findall(s or ""):
        tok = tok.replace(" ", "")
        if tok not in pct_tokens:
            pct_tokens.append(tok)
        if len(pct_tokens) >= 6:
            break
    return "/".join(pct_tokens)


def candidate_drug_rows(entry: dict):
    """Return a list of (display_name, dosage_hint) tuples of real drug rows
    extracted from one collected KB entry (see module docstring)."""
    rows = []
    specific = entry.get("specific_drugs")
    if isinstance(specific, list) and any(isinstance(x, str) and x.strip() for x in specific):
        for s in specific:
            if not isinstance(s, str) or not s.strip():
                continue
            s = s.strip()
            split = split_named_compounds(s)
            if split:
                for nm, prefix, suffix in split:
                    ctx = " -- ".join(x for x in [prefix, suffix] if x)
                    disp = f"{nm} ({ctx})" if ctx else nm
                    rows.append((disp, extract_dosage(s)))
            elif is_drug_text(s):
                rows.append((s, extract_dosage(s)))
        return rows

    nm_field = (entry.get("name") or "").strip()
    if not nm_field:
        return rows
    dosage_source = entry.get("_full_text") or nm_field
    split = split_named_compounds(nm_field)
    if split:
        for nm, prefix, suffix in split:
            ctx = " -- ".join(x for x in [prefix, suffix] if x)
            disp = f"{nm} ({ctx})" if ctx else nm
            rows.append((disp, extract_dosage(dosage_source)))
        return rows

    if is_vague_category(nm_field):
        return rows
    combined = nm_field + " " + (entry.get("type") or "")
    if is_drug_text(combined):
        rows.append((nm_field, extract_dosage(dosage_source)))
    return rows


def build_rows():
    diseases = DATA.get("diseases", {})
    grouped = {}
    zero_drug_diseases = []
    stats = {"candidate_entries_total": 0, "raw_candidate_rows": 0, "final_drug_rows": 0}

    for did, dz in sorted(
        diseases.items(),
        key=lambda kv: ((kv[1].get("category") or "zzz_uncategorized"), (kv[1].get("name") or kv[0])),
    ):
        category = dz.get("category") or "Uncategorized"
        dname = dz.get("name") or did

        ranked = _ranked_list(dz.get("effectiveness_ranked_table"))
        ranked_pairs = [
            ((r.get("name") or ""), r.get("effectiveness_pct"))
            for r in ranked
            if isinstance(r, dict) and (r.get("name") or "").strip()
        ]

        ems = dz.get("exhaustive_medicine_survey")
        ems_entries = []
        if isinstance(ems, (dict, list)):
            _collect_named_entries(ems, ems_entries)
        if isinstance(ems, dict):
            ems_entries.extend(extract_bare_string_entries(ems))

        curative = dz.get("curative_option")
        curative_entries = []
        if curative is not None:
            _collect_named_entries(curative, curative_entries)
        if isinstance(curative, dict):
            curative_entries.extend(extract_bare_string_entries(curative))

        stats["candidate_entries_total"] += len(ems_entries) + len(curative_entries)

        disease_rows = []
        matched_curative_idx = set()

        for entry in ems_entries:
            entry_name = (entry.get("name") or "").strip()
            is_cur = False
            for i, ce in enumerate(curative_entries):
                if i in matched_curative_idx:
                    continue
                cname = (ce.get("name") or "").strip()
                if cname and entry_name and _score_name_match(entry_name, cname) >= 2:
                    is_cur = True
                    matched_curative_idx.add(i)
                    break

            drug_rows = candidate_drug_rows(entry)
            stats["raw_candidate_rows"] += len(drug_rows)
            pct = entry.get("effectiveness_pct")
            if pct is None:
                for rname, rpct in ranked_pairs:
                    if entry_name and _score_name_match(entry_name, rname) >= 2:
                        pct = rpct
                        break
            for disp_name, dosage in drug_rows:
                if pct is None:
                    for rname, rpct in ranked_pairs:
                        if _score_name_match(disp_name, rname) >= 2:
                            pct = rpct
                            break
                disease_rows.append({
                    "name": disp_name,
                    "dosage": dosage,
                    "eff_pct": pct,
                    "is_curative": is_cur,
                    "source": entry.get("source") or "",
                })

        for i, ce in enumerate(curative_entries):
            if i in matched_curative_idx:
                continue
            drug_rows = candidate_drug_rows(ce)
            stats["raw_candidate_rows"] += len(drug_rows)
            pct = ce.get("effectiveness_pct")
            for disp_name, dosage in drug_rows:
                p = pct
                if p is None:
                    for rname, rpct in ranked_pairs:
                        if _score_name_match(disp_name, rname) >= 2:
                            p = rpct
                            break
                disease_rows.append({
                    "name": disp_name,
                    "dosage": dosage,
                    "eff_pct": p,
                    "is_curative": True,
                    "source": ce.get("source") or "",
                })

        stats["final_drug_rows"] += len(disease_rows)
        if not disease_rows:
            zero_drug_diseases.append((did, dname))

        grouped.setdefault(category, []).append((dname, did, disease_rows))

    return grouped, zero_drug_diseases, stats


def render_pdf(grouped, zero_drug_diseases, stats):
    col_widths = [10.5 * cm, 5.5 * cm, 1.8 * cm, 1.6 * cm, 8.9 * cm]

    header_row = [
        Paragraph("Full Drug / Salt Name", hdr_cell_s),
        Paragraph("Dosage / Formulation", hdr_cell_s),
        Paragraph("Eff. %", hdr_cell_s),
        Paragraph("Curative", hdr_cell_s),
        Paragraph("Source / Citation", hdr_cell_s),
    ]
    data = [header_row]
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]

    total_rows_rendered = 0
    row_idx = 1

    for category in sorted(grouped.keys()):
        n_dz = len(grouped[category])
        data.append([Paragraph(f"{category}  ({n_dz} diseases)", cat_cell_s), "", "", "", ""])
        style_cmds.append(("SPAN", (0, row_idx), (-1, row_idx)))
        style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), BLACK))
        row_idx += 1

        for dname, did, disease_rows in grouped[category]:
            data.append([Paragraph(f"{dname}  ({len(disease_rows)} drug/injection entries)", dis_cell_s),
                         "", "", "", ""])
            style_cmds.append(("SPAN", (0, row_idx), (-1, row_idx)))
            style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), GREEN))
            row_idx += 1

            if not disease_rows:
                data.append([
                    Paragraph("No qualifying real pharmaceutical medicine/injection in the KB for this "
                              "disease (its documented treatment is non-drug -- e.g. surgical, procedural, "
                              "or behavioural -- or research on a drug option is still pending).", empty_row_s),
                    "", "", "", "",
                ])
                style_cmds.append(("SPAN", (0, row_idx), (-1, row_idx)))
                style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#fbfbfb")))
                row_idx += 1
                continue

            for r in disease_rows:
                cur_style = cur_cell_s if r["is_curative"] else notcur_cell_s
                data.append([
                    Paragraph(_text(r["name"]), name_cell_s),
                    Paragraph(_text(r["dosage"]) or "—", dosage_cell_s),
                    Paragraph(_fmt_pct(r["eff_pct"]), eff_cell_s),
                    Paragraph("Yes" if r["is_curative"] else "No", cur_style),
                    Paragraph(_text(r["source"], 170), source_cell_s),
                ])
                row_idx += 1
                total_rows_rendered += 1

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))

    elements = []
    elements.append(Paragraph(
        "BalanceAI — Master Medicine &amp; Injection Reference Table (Real Pharmaceutical Agents Only)",
        title_s))
    elements.append(Paragraph(
        "Every real, chemically/generically named pharmaceutical medicine and injection found across this "
        "project's entire disease research -- all researched diseases, grouped by category and disease. "
        "Scope is drugs and injections ONLY: surgeries, procedures, devices, and non-drug therapies "
        "(voice/physical/occupational therapy, CBT, radiotherapy-as-a-procedure, lifestyle/diet advice, "
        "rehabilitation) are excluded even where the knowledge base documents them as the real treatment "
        "of choice -- a disease shown with zero rows below is a real, expected consequence of this scope, "
        "not missing research. “Curative” = flagged as this disease's real curative_option in the knowledge "
        "base. Effectiveness %% is shown where the knowledge base records one for this entry, or matched to "
        "the disease's ranked-effectiveness table where the entry itself does not carry its own number.",
        subtitle_s))
    elements.append(Paragraph(
        f"Diseases covered: {sum(len(v) for v in grouped.values())} &nbsp;|&nbsp; "
        f"Drug/injection rows in this table: {total_rows_rendered} &nbsp;|&nbsp; "
        f"Diseases with zero qualifying drug rows: {len(zero_drug_diseases)}",
        meta_s))
    elements.append(Spacer(1, 6))
    elements.append(table)

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=landscape(A4),
        leftMargin=1.1 * cm, rightMargin=1.1 * cm,
        topMargin=1.2 * cm, bottomMargin=1.1 * cm,
        title="BalanceAI Master Medicine & Injection Reference Table (Real Pharmaceutical Agents Only)",
    )
    doc.build(elements)
    return total_rows_rendered


if __name__ == "__main__":
    grouped, zero_drug_diseases, stats = build_rows()
    total_rows_rendered = render_pdf(grouped, zero_drug_diseases, stats)

    row_log = {
        "source_file": str(SRC_PATH),
        "diseases_processed": sum(len(v) for v in grouped.values()),
        "candidate_entries_total": stats["candidate_entries_total"],
        "raw_candidate_rows_pre_render": stats["raw_candidate_rows"],
        "final_drug_rows_rendered": total_rows_rendered,
        "zero_drug_diseases_count": len(zero_drug_diseases),
        "zero_drug_diseases": [{"id": did, "name": dname} for did, dname in zero_drug_diseases],
    }
    ROW_LOG_PATH.write_text(json.dumps(row_log, indent=2), encoding="utf-8")

    print("=== BUILD SUMMARY (drugs/injections only) ===")
    print(f"Source file used: {SRC_PATH}")
    print(f"Diseases processed: {sum(len(v) for v in grouped.values())}")
    print(f"KB entries scanned (ems + curative, recursive): {stats['candidate_entries_total']}")
    print(f"Raw candidate drug rows (pre-any-dedup): {stats['raw_candidate_rows']}")
    print(f"Final drug/injection rows rendered: {total_rows_rendered}")
    print(f"Diseases with ZERO qualifying drug rows: {len(zero_drug_diseases)}")
    for did, dname in zero_drug_diseases[:40]:
        print(f"  - {did}  ({dname})")
    if len(zero_drug_diseases) > 40:
        print(f"  ... and {len(zero_drug_diseases) - 40} more (see {ROW_LOG_PATH})")
    print(f"Output PDF: {OUT_PDF}")
    print(f"Row log JSON: {ROW_LOG_PATH}")
