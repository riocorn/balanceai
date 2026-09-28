"""
Disease Prescription PDF — gold-standard, source-verified.
Exactly two sections per disease: (1) all real medicines with effectiveness %
and the biological/pharmacological reason for that effectiveness, and
(2) all detailed real symptoms. Built from data/disease_master.json.
"""
import json
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

ROOT = Path("/home/abhay/Downloads/medical/balanceai")
DATA = json.loads((ROOT / "data" / "disease_master.json").read_text())
OUT_PDF = ROOT / "data" / "BalanceAI_Disease_Prescription_Report.pdf"

GREEN = colors.HexColor("#1d5c3d")
GREEN_LT = colors.HexColor("#eef7f2")
CORAL = colors.HexColor("#c0392b")
GREY = colors.HexColor("#5a6571")

styles = getSampleStyleSheet()
title_s = ParagraphStyle("title", parent=styles["Title"], textColor=GREEN, fontSize=22, alignment=TA_CENTER)
subtitle_s = ParagraphStyle("subtitle", parent=styles["BodyText"], textColor=GREY, fontSize=10.5,
                             alignment=TA_CENTER, spaceAfter=6)
disease_h = ParagraphStyle("disease_h", parent=styles["Heading1"], textColor=colors.white, fontSize=16,
                            backColor=GREEN, borderPadding=10, spaceBefore=0, spaceAfter=0)
category_h = ParagraphStyle("category_h", parent=styles["Heading1"], textColor=colors.white, fontSize=18,
                             backColor=colors.black, borderPadding=12, alignment=TA_CENTER,
                             spaceBefore=0, spaceAfter=0)
section_h = ParagraphStyle("section_h", parent=styles["Heading1"], textColor=colors.white, fontSize=13,
                            backColor=colors.HexColor("#d4a043"), borderPadding=8, spaceBefore=16, spaceAfter=8)
subhead = ParagraphStyle("subhead", parent=styles["Heading2"], textColor=GREEN, fontSize=11.5,
                          spaceBefore=10, spaceAfter=3)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.7, leading=14)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, spaceAfter=3)
small_grey = ParagraphStyle("small_grey", parent=body, fontSize=8.5, textColor=GREY, leftIndent=10)
ref_entry_s = ParagraphStyle("ref_entry", parent=small_grey, fontSize=7.2, leading=8.6, spaceAfter=0, leftIndent=8)
ref_heading_s = ParagraphStyle("ref_heading", parent=body, fontSize=9.3, leading=11, textColor=GREY,
                                fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=2)
# Inline citation-marker line (e.g. "Source: [3]" or "Confidence: High | Source: [3], [4]") now
# carries only a short bracket marker, never the full citation text, so it no longer needs
# small_grey's generous leading (tuned for multi-line wrapped citation prose) -- a tighter
# footnote-style line is used instead, consistent with the References list's own font sizing.
cite_marker_s = ParagraphStyle("cite_marker", parent=small_grey, fontSize=8, leading=9.5)

elements = []
elements.append(Paragraph("BalanceAI — Disease Prescription Report", title_s))
elements.append(Paragraph(
    "Gold-standard, source-verified: (1) every real medicine used for this disease with its real "
    "effectiveness and the medical/biological reason behind that effectiveness, and (2) the complete "
    "real symptom profile. Every claim is sourced; nothing is fabricated.",
    subtitle_s))
elements.append(Spacer(1, 14))


# ============ MEDICINE/INJECTION vs OTHER-TREATMENT SPLIT (effectiveness tables) ============
# 779 ranked-table rows across 61 diseases use 578 distinct free-text "type" strings
# (different research forks phrased them differently), so this is a keyword heuristic,
# not an exact taxonomy. It never drops a row: every row is classified into exactly one
# of the two buckets (checked in this order: explicit non-drug signal -> explicit
# drug/injection signal -> default to medicine, since the large majority of unmatched
# free-text types in this KB are still drug classes phrased unusually, e.g. "Pillar 1",
# "Add-on", "Strategy").
_OTHER_TREATMENT_KEYWORDS = (
    "surg", "procedure", "procedural", "catheter", "device", "implant", "transplant",
    "neurostimulat", "stimulator", "stimulation", "pacing", "pacemaker", "ablation",
    "revascularization", "resection", "endovascular", "mechanical", "compression garment",
    "exercise", "rehabilitation", "physiotherapy", "occupational therapy", "dietary",
    "nutritional", "lifestyle", "education", "screening", "apheresis",
    "plasma exchange", "radiotherapy", "sbrt", "phototherapy", "ventilator", "ventilation",
    "cpap", "bipap", "intubat", "tracheostom", "shunt",
    "circulatory support", "structured non-drug", "non-drug programme", "cognitive",
    "behavioural", "behavioral", "psychotherapy", "clip", "teer", "commissurotomy",
    "thoracostomy", "proctocolectomy", "fundoplication", "thymectomy", "cholecystectomy",
    "angioplasty", "spinal fusion", "joint fusion", "vertebral fusion", "arthrodesis",
    "decompression", "septostomy", "pleurodesis",
    # NOTE: "fusion" (bare) and "biopsy" and "dialysis" were deliberately removed/narrowed
    # after verification found they were 100% false-positive substring hits in this
    # dataset ("fusion" matched inside "infusion"/"effusion"; "biopsy" and "dialysis"
    # each matched only inside a drug row's outcome/context description, never an
    # actual biopsy/dialysis treatment row) -- see verification notes.
)
_MEDICINE_OR_INJECTION_KEYWORDS = (
    "oral", "iv ", "iv-", "iv/", "subcutaneous", " sc ", "intramuscular", "injectable",
    "injection", "infusion", "drug", "tablet", "capsule", "inhibitor", "agonist",
    "antagonist", "antibody", "biologic", "monoclonal", "vaccine", "interferon",
    "hormone", "analog", "dmard", "statin", "fibrate", "bisphosphonate", "contraceptive",
    "anticoagulant", "antiplatelet", "thrombolytic", "antibiotic", "antifungal",
    "antiviral", "immunosuppressant", "corticosteroid", "nsaid", "uricosuric",
    "beta-blocker", "blocker", "sglt2", "pcsk9", "reversal agent", "neuromuscular blocking",
    "pineal hormone", "prophylaxis", "chemotherapy", "small molecule", "kinase inhibitor",
    "guanylate cyclase", "myosin inhibitor", "receptor modulator", "gepant", "triptan",
    "immunoglobulin", "toxin", "enzyme replacement",
)


def classify_treatment_row(r):
    """Return 'other' if the row's type/name clearly indicates a non-drug treatment
    (surgery, procedure, device, lifestyle/behavioural, etc.), else 'medicine'
    (covers oral/IV/SC/IM drugs, biologics, and vaccines/other injections)."""
    text = f"{r.get('type', '')} {r.get('name', '')}".lower()
    if any(k in text for k in _OTHER_TREATMENT_KEYWORDS):
        return "other"
    if any(k in text for k in _MEDICINE_OR_INJECTION_KEYWORDS):
        return "medicine"
    return "medicine"


def add_bullets(items, style=bullet, prefix="• "):
    for it in items:
        elements.append(Paragraph(prefix + it, style))


# ============ IEEE-STYLE PER-DISEASE NUMBERED CITATIONS ============
# Every "source" field in disease_master.json is a citation string, sometimes several
# citations jammed into one string separated by "; ". Repeating the full citation text
# inline at every claim that references it is the main source of this PDF's page-count
# bloat (the same citation is often quoted verbatim dozens of times within one disease).
# Instead: cite(source_text) returns inline marker(s) like "[1]" or "[1], [2]", looked up
# in a small per-disease registry (_cite_registry/_cite_order) that is reset at the top of
# every "for disease_id, disease in DATA['diseases'].items():" iteration (see disease_num
# reset below), and the full citation text for each number is printed once, in first-seen
# order, in a "References" list at the end of that disease's own section (not one running
# list for the whole ~1100-page document -- numbering restarts at [1] per disease).
#
# split_citations() splits a "source" string on "; " into separate citations, but only at
# boundaries that look like a genuine new citation (not the page-range/volume ";" inside
# "Lancet 2022;400:1363-1380", which has no space after the ";" and is never a candidate).
# A "; " is treated as a split point only when paren-nesting is balanced at that point
# (so "(PMID 123; PMC456)" is never split apart) AND the text right after "; " looks like
# the start of a new citation: a closing ")" right before the "; " (most citations end in a
# PMID/DOI/ISBN parenthetical), or an author-name-like token ("Feldman EL", "Liu RY et al"),
# a recognised guideline/organisation acronym (WHO, FDA, IDSA, Cochrane, PMC123, ...), a
# trial-ID-like token with a digit (EVOLVE-1, SUSTAIN-6), or an editorial lead-in ("contrast:
# Clark W et al ..."). Anything not matching one of these is deliberately left un-split
# (safer to under-split one citation than to wrongly fragment it into nonsense pieces).
_CITE_ORG_TOKENS = (
    r"(?:WHO|IDSA|AHA|ACC|ACR|ESC|EAN|ERS|ATS|NICE|FDA|CDC|Cochrane|MDS|EASL|AASLD|ADA|"
    r"KDIGO|GOLD|GINA|ESCMID|BTS|SIGN|NCCN|ASCO|ESMO|RCOG|ACOG|ISUOG|HRS|NCT\d+|PMC\d+|PMID\s*\d+|"
    r"StatPearls|ACG|PubMed\s*\d+|ScienceDirect|JACC|BMC|MDCalc|Cleveland Clinic|Merck|NCBI|"
    r"ECCO|AAFP|Mayo Clinic|MSD Manual|Medscape|DailyMed|UpToDate|MedlinePlus)"
)
_CITE_AUTHOR_RE = re.compile(r"^[A-Z][a-z]+(?:['\-][A-Za-z]+)?(?:,?\s+[A-Z]{1,2}\b(?!\.?[a-z])|\s+et al\.?\b)")
_CITE_ORG_RE = re.compile(r"^" + _CITE_ORG_TOKENS + r"\b")
_CITE_TRIAL_RE = re.compile(r"^[A-Z][A-Za-z]*-?\d+\b")
_CITE_EDITORIAL_RE = re.compile(r"^(?:contrast|see also|cf\.?|also|and)\s*:?\s+[A-Z][a-z]+\s+[A-Z]")


def split_citations(text):
    text = (text or "").strip()
    if not text:
        return []
    parts, last_start, depth, i, n = [], 0, 0, 0, len(text)
    while i < n - 1:
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if depth == 0 and ch == ";" and text[i + 1] == " ":
            before, after = text[last_start:i].rstrip(), text[i + 2:].lstrip()
            is_boundary = (before.endswith(")") or _CITE_AUTHOR_RE.match(after) or _CITE_ORG_RE.match(after)
                           or _CITE_TRIAL_RE.match(after) or _CITE_EDITORIAL_RE.match(after))
            if is_boundary:
                parts.append(text[last_start:i].strip())
                last_start = i + 2
                i += 2
                continue
        i += 1
    parts.append(text[last_start:].strip())
    return [p for p in parts if p]


_cite_registry = {}
_cite_order = []


def cite(source_text):
    markers = []
    for part in split_citations(source_text):
        if not part or part.strip().upper() == "N/A":
            continue
        num = _cite_registry.get(part)
        if num is None:
            _cite_order.append(part)
            num = len(_cite_order)
            _cite_registry[part] = num
        markers.append(f"[{num}]")
    return ", ".join(markers) if markers else ""


def render_references():
    if not _cite_order:
        return
    elements.append(Spacer(1, 3))
    elements.append(Paragraph("References", ref_heading_s))
    for idx, ref_text in enumerate(_cite_order, start=1):
        elements.append(Paragraph(f"[{idx}] {ref_text}", ref_entry_s))


EXCLUDED_FROM_PDF = {"iron_deficiency_anaemia", "rickets_osteomalacia"}

def _normalize_category(cat):
    return (cat or "Uncategorized").split(" (")[0].strip()

disease_num = 0
_sorted_diseases = sorted(
    DATA["diseases"].items(),
    key=lambda item: (_normalize_category(item[1].get("category", "")), item[1].get("name", "") or item[0]),
)
current_category = None
for disease_id, disease in _sorted_diseases:
    if disease_id in EXCLUDED_FROM_PDF:
        continue
    disease_num += 1
    cat = _normalize_category(disease.get("category", ""))
    if cat != current_category:
        current_category = cat
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(cat, category_h))
        elements.append(Spacer(1, 6))
    _cite_registry.clear()
    _cite_order.clear()
    elements.append(Paragraph(f"&nbsp;Disease {disease_num}: {disease['name']}", disease_h))
    elements.append(Spacer(1, 10))


    if disease.get("EMERGENCY_OVERRIDE_RULE"):
        emergency_style = ParagraphStyle("emergency", parent=body, textColor=colors.white,
                                          backColor=CORAL, borderPadding=8, fontSize=9.5)
        eor = disease["EMERGENCY_OVERRIDE_RULE"]
        eor_text = eor.get("rule", "") if isinstance(eor, dict) else eor
        elements.append(Paragraph(f"<b>EMERGENCY OVERRIDE RULE:</b> {eor_text}",
                                   emergency_style))
        if isinstance(eor, dict) and eor.get("source"):
            elements.append(Paragraph(f"Confidence: {eor.get('confidence', '')} | Source: {cite(eor['source'])}", cite_marker_s))
        elements.append(Spacer(1, 8))

    if disease.get("URGENT_REFERRAL_RULE"):
        urgent_style = ParagraphStyle("urgent", parent=body, textColor=colors.white,
                                       backColor=colors.HexColor("#c98a1e"), borderPadding=8, fontSize=9.5)
        elements.append(Paragraph(f"<b>URGENT REFERRAL RULE:</b> {disease['URGENT_REFERRAL_RULE']}",
                                   urgent_style))
        elements.append(Spacer(1, 8))

    if disease.get("CURABILITY_NOTE"):
        elements.append(Paragraph(f"<b>Curability:</b> {disease['CURABILITY_NOTE']}",
                                   ParagraphStyle("curability", parent=small_grey, fontSize=9,
                                                  backColor=colors.HexColor("#fff8e6"), borderPadding=6)))
        elements.append(Spacer(1, 8))

    def render_procedure_block(block, heading_style=subhead):
        elements.append(Paragraph(block["name"], heading_style))
        if block.get("note"):
            elements.append(Paragraph(block["note"], body))
        if block.get("real_survival_data"):
            elements.append(Paragraph("Real survival: " + ", ".join(
                f"{k.replace('_', ' ')}: {v}" for k, v in block["real_survival_data"].items()), small_grey))
        if block.get("real_recovery_data"):
            elements.append(Paragraph("Real recovery data: " + ", ".join(
                f"{k.replace('_', ' ')}: {v}" for k, v in block["real_recovery_data"].items()), small_grey))
        if block.get("safety_note"):
            elements.append(Paragraph(f"<i>Safety note: {block['safety_note']}</i>", small_grey))
        if block.get("source"):
            elements.append(Paragraph(f"Source: {cite(block['source'])}", cite_marker_s))
        if block.get("alternative"):
            elements.append(Paragraph(f"Alternative: {block['alternative']['name']}", subhead))
            render_procedure_block(block["alternative"], heading_style=body)

    co = disease.get("curative_option")
    if isinstance(co, str):
        elements.append(Paragraph("Real Curative-Intent Option:", subhead))
        elements.append(Paragraph(co, body))
        co = None
    if isinstance(co, dict) and "name" not in co and any(isinstance(v, dict) for v in co.values()):
        # Multi-variant shape keyed by a descriptive label string per variant (e.g. MEN1 vs MEN2
        # in multiple_endocrine_neoplasia, or terminal_complement_deficiency vs c1_inhibitor_deficiency_hae
        # in complement_deficiency_disorders), each dict value itself a full name/note/source
        # curative-option dict -- rendered as separate options instead of crashing on the missing
        # top-level "name". A plain string sibling key (e.g. "note") is rendered first as an intro,
        # not silently dropped.
        for intro_key, intro_val in co.items():
            if isinstance(intro_val, str) and intro_val.strip():
                elements.append(Paragraph(intro_val, body))
                elements.append(Spacer(1, 4))
        elements.append(Paragraph("Real Curative-Intent Options:", subhead))
        for sub_label, sub_co in co.items():
            if not isinstance(sub_co, dict):
                continue
            elements.append(Paragraph(f"Real Curative-Intent Option: {sub_co.get('name', sub_label)}", subhead))
            elements.append(Paragraph(sub_co.get("note", sub_co.get("why_this_is_the_real_closest_thing_to_a_cure", "")), body))
            if sub_co.get("real_effectiveness_pct") is not None:
                elements.append(Paragraph(f"Real effectiveness: {sub_co['real_effectiveness_pct']}%", small_grey))
            if sub_co.get("source"):
                elements.append(Paragraph(f"Source: {cite(sub_co['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))
        co = None
    if co:
        elements.append(Paragraph(f"Real Curative-Intent Option: {co['name']}", subhead))
        if co.get("why_this_is_the_real_closest_thing_to_a_cure") and "note" not in co:
            # TIA's curative_option (see disease-specific block below) has no "note" key -- fall back to
            # its own summary field instead of the generic "note" so real content is not dropped, and the
            # KeyError this line used to raise (which silently blocked PDF generation for every disease,
            # not just TIA) is avoided.
            elements.append(Paragraph(co["why_this_is_the_real_closest_thing_to_a_cure"], body))
        else:
            elements.append(Paragraph(co.get("note", ""), body))
        if "real_survival_data" in co:
            # Original flat shape (single procedure + optional alternative)
            elements.append(Paragraph("Real survival: " + ", ".join(f"{k.replace('_',' ')}: {v}" for k, v in co["real_survival_data"].items()), small_grey))
            elements.append(Paragraph(f"Source: {cite(co.get('source', ''))}", cite_marker_s))
            if co.get("alternative"):
                alt = co["alternative"]
                elements.append(Paragraph(f"Alternative: {alt['name']}", subhead))
                elements.append(Paragraph(alt["note"], body))
                if alt.get("real_survival_data"):
                    elements.append(Paragraph("Real survival: " + ", ".join(f"{k.replace('_',' ')}: {v}" for k, v in alt["real_survival_data"].items()), small_grey))
                if alt.get("source"):
                    elements.append(Paragraph(f"Source: {cite(alt['source'])}", cite_marker_s))
            # Aortic aneurysm/dissection's curative_option uses the original flat
            # real_survival_data shape above, but also carries an important_caveat
            # (real RCT-vs-registry honesty checks: IMPROVE trial found no significant
            # ruptured-AAA mortality difference vs the registry-derived EVAR-vs-open
            # gap quoted above, and EVAR-1/OVER long-term follow-up found EVAR's early
            # survival advantage lost by 14-15 years) that the generic flat-shape
            # rendering above does not cover -- rendered explicitly here, matching
            # this file's established per-disease-guard pattern, so it is not
            # silently dropped.
            if disease_id == "aortic_aneurysm_dissection" and co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
        elif co.get("step_1_treat_the_trigger") or co.get("step_2_lung_protective_ventilation"):
            # Two-step cause-treatment + supportive-care shape (e.g. ARDS: treat trigger + lung-protective ventilation)
            for step_key in ("step_1_treat_the_trigger", "step_2_lung_protective_ventilation"):
                step = co.get(step_key)
                if not step:
                    continue
                render_procedure_block(step, heading_style=subhead)
                elements.append(Spacer(1, 4))
            if co.get("real_recovery_in_survivors"):
                elements.append(Paragraph(f"<i>{co['real_recovery_in_survivors']}</i>", small_grey))
        else:
            # Newer shape: distinct real reversible-subtype cures + a separate definitive option
            # for the non-reversible majority (e.g. dilated_cardiomyopathy)
            if co.get("reversible_subtypes"):
                elements.append(Paragraph("Real reversible-subtype interventions (closest thing to a cure, subtype-specific):", subhead))
                for rs in co["reversible_subtypes"]:
                    render_procedure_block(rs, heading_style=body)
                    elements.append(Spacer(1, 4))
            dom = co.get("definitive_option_nonreversible_majority")
            if dom:
                elements.append(Paragraph("Definitive option for the non-reversible majority:", subhead))
                render_procedure_block(dom, heading_style=subhead)
        if co.get("riociguat_dual_indication_note"):
            elements.append(Paragraph(f"<i>{co['riociguat_dual_indication_note']}</i>", small_grey))

        # IBD's curative_option (total proctocolectomy with IPAA for Ulcerative Colitis) and GERD's
        # curative_option (fundoplication/TIF/LINX) both carry the same real, distinctive shape
        # (type/real_indications/why_this_is_a_genuine_cure_.../real_outcome_data[/contrast_with_
        # crohns_surgery for IBD only]) that the generic co-rendering above (built for the
        # real_survival_data / step-1-step-2 / reversible-subtype shapes used elsewhere) does not
        # match at all beyond name+note -- rendered explicitly here so none of this real content is
        # silently dropped. GERD's curative_option has no contrast_with_crohns_surgery key, so that
        # line is simply skipped (co.get returns None) for gerd.
        if disease_id in ("inflammatory_bowel_disease", "gerd"):
            if co.get("type"):
                elements.append(Paragraph(f"<b>Type of procedure:</b> {co['type']}", body))
            ri = co.get("real_indications")
            if isinstance(ri, list):
                elements.append(Paragraph("<b>Real indications:</b>", body))
                add_bullets(ri)
            if co.get("why_this_is_a_genuine_cure_not_just_remission"):
                elements.append(Paragraph(f"<b>Why this is a genuine cure, not just remission:</b> {co['why_this_is_a_genuine_cure_not_just_remission']}", body))
            rod = co.get("real_outcome_data")
            if isinstance(rod, dict):
                elements.append(Paragraph("<b>Real outcome data:</b>", body))
                for rk, rv in rod.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("contrast_with_crohns_surgery"):
                elements.append(Paragraph(f"<b>Contrast with Crohn's disease surgery (NOT curative):</b> {co['contrast_with_crohns_surgery']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Chronic gastritis' curative_option (H. pylori eradication therapy) carries a real,
        # distinctive shape (name/note/gastric_cancer_prevention_benefit/source) that the
        # generic name+note rendering above already covers for note, but
        # gastric_cancer_prevention_benefit and source would otherwise be silently dropped
        # (matching this file's established per-disease-guard pattern above for GERD/IBD/GPA).
        if disease_id == "chronic_gastritis":
            if co.get("gastric_cancer_prevention_benefit"):
                elements.append(Paragraph(f"<b>Real gastric cancer prevention benefit:</b> {co['gastric_cancer_prevention_benefit']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Source: {cite(co['source'])}", cite_marker_s))

        # GPA's curative_option (induction: rituximab or cyclophosphamide + glucocorticoids,
        # followed by rituximab or azathioprine maintenance) carries the same real
        # type/specific_drugs/note/real_outcome_data/source/confidence shape as IBD/GERD above,
        # but is a distinct disease_id, so it needs its own explicit guard here -- otherwise the
        # real RAVE/MAINRITSAN/ADVOCATE/Fauci-1983 real_outcome_data dict, the exact drug list, and
        # the source/confidence line would all be silently dropped, matching this file's
        # established per-disease-guard pattern.
        if disease_id == "granulomatosis_with_polyangiitis":
            if co.get("type"):
                elements.append(Paragraph(f"<b>Type of therapy:</b> {co['type']}", body))
            sd = co.get("specific_drugs")
            if isinstance(sd, list):
                elements.append(Paragraph("<b>Exact regimen:</b>", body))
                add_bullets(sd)
            rod = co.get("real_outcome_data")
            if isinstance(rod, dict):
                elements.append(Paragraph("<b>Real outcome data:</b>", body))
                for rk, rv in rod.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Acute pancreatitis' curative_option (same-admission cholecystectomy for gallstone
        # pancreatitis, PONCHO trial) carries a distinct real shape (name/note/real_trial_data dict/
        # source/important_caveat) that the generic co-rendering above (built for the real_survival_data
        # / step-1-step-2 / reversible-subtype shapes used elsewhere) does not match at all beyond
        # name+note -- without this block, real_trial_data, source, and important_caveat would be
        # silently dropped exactly like the recurring bug this file's header comments warn about.
        if disease_id == "acute_pancreatitis":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (PONCHO trial):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Source: {cite(co['source'])}", cite_marker_s))

        # Acute appendicitis' curative_option (appendectomy as the real definitive cure, with
        # antibiotics-alone as a real evidence-based alternative for select uncomplicated cases)
        # carries a distinct real shape (name/note/real_success_data dict/source/alternative dict
        # with its own real_outcome_data dict/source) that the generic co-rendering above does not
        # match at all beyond name+note -- rendered explicitly here so the real APPAC/APPAC
        # II/CODA/10-year-follow-up trial numbers are not silently dropped.
        if disease_id == "acute_appendicitis":
            rsd = co.get("real_success_data")
            if isinstance(rsd, dict):
                elements.append(Paragraph("Real success data:", body))
                for rk, rv in rsd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("source"):
                elements.append(Paragraph(f"Source: {cite(co['source'])}", cite_marker_s))
            alt = co.get("alternative")
            if isinstance(alt, dict):
                elements.append(Paragraph(f"Alternative: {alt.get('name', '')}", subhead))
                if alt.get("note"):
                    elements.append(Paragraph(alt["note"], body))
                rod = alt.get("real_outcome_data")
                if isinstance(rod, dict):
                    elements.append(Paragraph("Real outcome data:", body))
                    for rk, rv in rod.items():
                        if isinstance(rv, str):
                            elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
                if alt.get("source"):
                    elements.append(Paragraph(f"Source: {cite(alt['source'])}", cite_marker_s))

        # Myasthenia gravis' curative_option (thymectomy, MGTX trial) carries a distinct real shape
        # (name/note/real_trial_data dict/who_does_not_clearly_benefit/important_caveat/source/confidence)
        # that the generic co-rendering above does not match beyond name+note -- rendered explicitly
        # here, matching this file's established per-disease-guard pattern, so the real MGTX 3-year and
        # 5-year-extension numbers, the thymoma-regardless-of-severity indication, the VATS/robotic vs
        # transsternal approach note, and the MuSK/LRP4/agrin/ocular/seronegative non-benefit statement
        # are not silently dropped.
        if disease_id == "myasthenia_gravis":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (MGTX trial and international consensus guidance):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Myelofibrosis' curative_option (allogeneic HSCT, MTSS risk-stratified 5-year survival + real
        # reduced-intensity-conditioning cohort outcomes) carries a distinct real shape (name/note/
        # real_trial_data dict/who_does_not_clearly_benefit/important_caveat/source/confidence) that the
        # generic co-rendering above does not match beyond name+note -- rendered explicitly here so the
        # real MTSS 83%/64%/37%/22% risk-stratified 5-year survival figures, the real reduced-intensity
        # transplant-related-mortality/relapse data, and the very-high-risk-group honesty caveat are not
        # silently dropped.
        if disease_id == "myelofibrosis":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real risk-stratified transplant outcome data (MTSS and reduced-intensity-conditioning cohort):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # TIA's curative_option (urgent ABCD2-triaged secondary-stroke-prevention bundle: same-day
        # assessment + short-course DAPT + high-intensity statin +/- anticoagulation +/- carotid
        # revascularization) carries a distinct real shape (name/type/note/components list of
        # step-dicts/overall_real_effect/source/confidence) that the generic co-rendering above does
        # not match beyond name+note -- rendered explicitly here so the real EXPRESS/CHANCE/POINT/
        # SPARCL/EAFT/ARISTOTLE/NASCET/CREST step-by-step numbers are not silently dropped.
        if disease_id == "transient_ischemic_attack":
            if co.get("type"):
                elements.append(Paragraph(f"<b>Type:</b> {co['type']}", body))
            comps = co.get("components")
            if isinstance(comps, list):
                for comp in comps:
                    if not isinstance(comp, dict):
                        continue
                    elements.append(Paragraph(comp.get("step", ""), body))
                    if comp.get("regimen"):
                        elements.append(Paragraph(f"<b>Regimen:</b> {comp['regimen']}", bullet))
                    if comp.get("real_evidence"):
                        elements.append(Paragraph(f"<b>Real evidence:</b> {comp['real_evidence']}", bullet))
                    if comp.get("source"):
                        elements.append(Paragraph(f"Confidence: {comp.get('confidence', '')} | Source: {cite(comp['source'])}", cite_marker_s))
                    elements.append(Spacer(1, 3))
            if co.get("overall_real_effect"):
                elements.append(Paragraph(f"<b>Overall real effect:</b> {co['overall_real_effect']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Gout's curative_option (sustained treat-to-target urate-lowering therapy: crystal dissolution and
        # flare cessation, explicitly NOT a cure of the underlying hyperuricaemia) carries a distinct real
        # shape (name/note/real_trial_data dict/what_is_curative_and_what_is_not/who_does_not_clearly_benefit/
        # important_caveat/source/confidence) that the generic co-rendering above does not match beyond
        # name+note -- rendered explicitly here so the real crystal-dissolution, flare-cessation, 5-year and
        # withdrawal data and the curative/not-curative boundary are not silently dropped.
        # Polymyalgia rheumatica's curative_option (low-dose oral glucocorticoid induction, real
        # dramatic/near-diagnostic response + genuine finite-course discontinuation data) carries the
        # same real shape as gout's above (name/note/real_trial_data dict/what_is_curative_and_what_is_not/
        # who_does_not_clearly_benefit/important_caveat/source/confidence) -- rendered via the same branch
        # so the real Caporali 2004 discontinuation/flare numbers, the EULAR/ACR 2015 tapering-framework
        # citation, and the honest methotrexate trial-to-trial inconsistency are not silently dropped.
        if disease_id in ("gout", "polymyalgia_rheumatica"):
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial and guideline data (crystal dissolution, flare cessation, durability, withdrawal):" if disease_id == "gout" else "Real trial and guideline data (glucocorticoid response speed, discontinuation rates, relapse risk, tapering framework):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Tendinitis/tendinopathy's curative_option (progressive heavy-load/eccentric loading exercise
        # therapy -- Alfredson 1998 Achilles, Jonsson & Alfredson 2005 patellar, Rompe 2007 independent
        # RCT replication) carries the same real shape (name/note/real_trial_data dict/
        # what_is_curative_and_what_is_not/who_does_not_clearly_benefit/important_caveat/source/confidence)
        # as gout/myasthenia_gravis/narcolepsy/ischaemic_heart_disease -- rendered explicitly here so the
        # real Alfredson 100%, Jonsson & Alfredson 90%, and Rompe 60%-vs-24% numbers and the
        # curative/not-curative boundary are not silently dropped.
        if disease_id == "tendinitis":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (Alfredson Achilles cohort, Jonsson & Alfredson patellar RCT, Rompe independent replication, durability):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Sarcopenia's curative_option (progressive resistance training + adequate protein intake, with
        # vitamin D correction in deficient patients) carries the same real shape (name/note/real_trial_data
        # dict/what_is_curative_and_what_is_not/who_does_not_clearly_benefit/source/confidence) as
        # gout/tendinitis/narcolepsy -- rendered explicitly here so the real Cochrane/Peterson/Cermak/
        # Beaudart/Bauer/Rooks numbers and the curative/not-curative boundary are not silently dropped.
        if disease_id == "sarcopenia":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (resistance training Cochrane review, Peterson strength/lean-mass meta-analyses, Cermak protein meta-analysis, PROT-AGE protein dosing, Beaudart vitamin D meta-analysis):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Narcolepsy's curative_option (honestly no cure -- irreversible hypocretin/orexin neuron loss --
        # combination pharmacotherapy plus the emerging orexin receptor-2 agonist oveporexton as the
        # closest-to-disease-modifying real option) carries the same real shape (name/note/real_trial_data
        # dict/what_is_curative_and_what_is_not/who_does_not_clearly_benefit/important_caveat/source/
        # confidence) as gout/myasthenia_gravis/acute_pancreatitis/ischaemic_heart_disease -- rendered
        # explicitly here so the real oveporexton First Light/Radiant Light phase 3 numbers, the HARMONY
        # CTP pitolisant and sodium-oxybate withdrawal-trial numbers, the TAK-994 hepatotoxicity
        # discontinuation note, and the curative/not-curative boundary are not silently dropped.
        if disease_id == "narcolepsy":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (oveporexton phase 3, pitolisant HARMONY CTP, sodium oxybate withdrawal trial, TAK-994 discontinuation):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # IHD/CAD's curative_option (ultra-early reperfusion achieving 'aborted' myocardial infarction
        # - real prevention of the single acute STEMI event, explicitly NOT a cure of the underlying
        # coronary atherosclerosis) carries a distinct real shape (name/note/real_trial_data dict/
        # what_is_curative_and_what_is_not/who_does_not_clearly_benefit/important_caveat/source/
        # confidence) that the generic co-rendering above does not match beyond name+note -- rendered
        # explicitly here, matching this file's established per-disease-guard pattern (same shape as
        # gout/myasthenia_gravis/acute_pancreatitis), so the real ASSENT-3, prehospital-vs-in-hospital
        # thrombolysis, Verheugt review, and STREAM aborted-MI data and the curative/not-curative
        # boundary are not silently dropped.
        if disease_id == "ischaemic_heart_disease":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (ASSENT-3, prehospital-vs-in-hospital thrombolysis, Verheugt review, STREAM):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Contact dermatitis' curative_option (allergen/irritant identification via patch testing
        # plus genuine sustained avoidance -- a real, guideline-endorsed route to complete,
        # drug-independent resolution in the great majority of cases, since unlike an intrinsic
        # immune/genetic disease the causative agent is external and removable) carries the same
        # distinct real shape (name/note/real_trial_data dict/what_is_curative_and_what_is_not/
        # who_does_not_clearly_benefit/source/confidence) as IHD/gout above -- rendered explicitly
        # here so the real Korkmaz 2019, Rajagopalan 1997, and Usatine/Riojas 2010 outcome data and
        # the curative/not-curative boundary are not silently dropped.
        if disease_id == "contact_dermatitis":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (Korkmaz 2019 patch-test outcome study, Rajagopalan 1997 multicenter QoL study, Usatine/Riojas 2010 guideline):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Cluster headache's curative_option (high-flow oxygen / subcutaneous sumatriptan for real
        # attack abortion plus verapamil for real bout suppression -- explicitly NOT a cure of the
        # underlying trigeminal-autonomic/hypothalamic disorder) carries the same distinct real shape
        # (name/note/real_trial_data dict/what_is_curative_and_what_is_not/who_does_not_clearly_benefit/
        # important_caveat/source/confidence) as gout/IHD above -- rendered explicitly here so the real
        # Cohen 2009 oxygen RCT, Ekbom 1991 sumatriptan RCT, Leone 2000 verapamil RCT, and episodic-CH
        # natural-remission data are not silently dropped.
        if disease_id == "cluster_headache":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (Cohen 2009 oxygen RCT, Ekbom 1991 sumatriptan RCT, Leone 2000 verapamil RCT, episodic natural remission):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Phenylketonuria's curative_option (newborn-screening-triggered lifelong low-Phe diet +
        # real adjunct medicines -- real prevention of the neurodevelopmental disease, explicitly NOT
        # a correction of the underlying PAH enzyme defect) carries the same real shape (name/note/
        # real_trial_data dict/what_is_curative_and_what_is_not/who_does_not_clearly_benefit/
        # important_caveat/source/confidence) as gout/myasthenia_gravis/ischaemic_heart_disease --
        # rendered explicitly here, matching this file's established per-disease-guard pattern, so the
        # real untreated-vs-early-treated IQ numbers, sapropterin/sepiapterin/pegvaliase efficacy data,
        # and maternal-PKU-prevention data are not silently dropped.
        if disease_id == "phenylketonuria":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real natural-history, early-treatment and adjunct-medicine data:", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("what_is_curative_and_what_is_not"):
                elements.append(Paragraph(f"<b>What is curative and what is not:</b> {co['what_is_curative_and_what_is_not']}", body))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Stroke's curative_option (time-critical acute reperfusion therapy) carries its own real,
        # distinctive shape (iv_thrombolysis / mechanical_thrombectomy sub-blocks, each with
        # real_survival_functional_data / reason_why / specific_drugs / source / confidence, plus a
        # the_permanence_boundary closing note) that none of the generic co-rendering branches above
        # match beyond name+note -- rendered explicitly here so this real content is not silently
        # dropped, matching this file's established per-disease-guard pattern.
        if disease_id == "stroke":
            for sub_key, sub_label in (
                ("iv_thrombolysis", "IV Thrombolysis (Alteplase / Tenecteplase)"),
                ("mechanical_thrombectomy", "Mechanical Thrombectomy (Large-Vessel Occlusion)"),
            ):
                sub = co.get(sub_key)
                if not isinstance(sub, dict):
                    continue
                elements.append(Paragraph(sub_label, body))
                rsfd = sub.get("real_survival_functional_data")
                if isinstance(rsfd, dict):
                    for rk, rv in rsfd.items():
                        if isinstance(rv, str):
                            elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
                rw = sub.get("reason_why")
                if isinstance(rw, list):
                    elements.append(Paragraph("<b>Why (biological reason):</b> " + " ".join(rw), body))
                if sub.get("specific_drugs"):
                    sd = sub["specific_drugs"]
                    elements.append(Paragraph("<b>Exact medicine(s)/device(s):</b> " + (", ".join(sd) if isinstance(sd, list) else str(sd)), body))
                if sub.get("source"):
                    elements.append(Paragraph(f"Confidence: {sub.get('confidence', '')} | Source: {cite(sub['source'])}", cite_marker_s))
                elements.append(Spacer(1, 4))
            if co.get("the_permanence_boundary"):
                elements.append(Paragraph(f"<i>The permanence boundary: {co['the_permanence_boundary']}</i>", small_grey))

        # BPPV's curative_option (Epley maneuver -- a real procedural near-cure, not a drug)
        # carries its own distinctive shape (real_trial_data dict / who_does_not_clearly_benefit /
        # important_caveat / horizontal_canal_variant_note / alternative sub-block with its own
        # real_trial_data) that none of the generic co-rendering branches above match beyond
        # name+note -- rendered explicitly here, matching this file's established per-disease-guard
        # pattern (same shape family as gout/myasthenia_gravis/ischaemic_heart_disease), so the real
        # Cochrane/Saishoji/Cetin/network-meta-analysis numbers, the canal-subtype caveat and the
        # Semont alternative are not silently dropped.
        if disease_id == "bppv":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (Cochrane 2014, Saishoji 2023, Cetin 2018, network meta-analysis 2026):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("horizontal_canal_variant_note"):
                elements.append(Paragraph(f"<b>Horizontal-canal variant note:</b> {co['horizontal_canal_variant_note']}", body))
            alt = co.get("alternative")
            if isinstance(alt, dict):
                elements.append(Paragraph(f"Alternative: {alt.get('name', '')}", subhead))
                if alt.get("note"):
                    elements.append(Paragraph(alt["note"], body))
                art = alt.get("real_trial_data")
                if isinstance(art, dict):
                    for rk, rv in art.items():
                        if isinstance(rv, str):
                            elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
                if alt.get("source"):
                    elements.append(Paragraph(f"Confidence: {alt.get('confidence', '')} | Source: {cite(alt['source'])}", cite_marker_s))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # Bell's palsy's curative_option (early oral prednisolone within 72h, Sullivan 2007 NEJM)
        # carries its own real shape (name/note/real_trial_data dict/who_does_not_clearly_benefit/
        # important_caveat/source) matching the bppv guard-block pattern above -- rendered explicitly
        # here so the real Sullivan 2007 3-month/9-month recovery numbers and the Madhok 2016 Cochrane
        # numbers are not silently dropped.
        if disease_id == "bells_palsy":
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data (Sullivan 2007 NEJM, Madhok 2016 Cochrane):", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))
            if co.get("who_does_not_clearly_benefit"):
                elements.append(Paragraph(f"<b>Who does NOT clearly benefit:</b> {co['who_does_not_clearly_benefit']}", body))
            if co.get("important_caveat"):
                elements.append(Paragraph(f"<b>Important caveat:</b> {co['important_caveat']}", body))
            if co.get("source"):
                elements.append(Paragraph(f"Confidence: {co.get('confidence', '')} | Source: {cite(co['source'])}", cite_marker_s))

        # VSD's curative_option carries its own real, distinctive dual-pathway shape
        # (pathway_1_spontaneous_closure dict / pathway_2_definitive_repair dict /
        # real_honest_caveat) reflecting the genuinely different real curative routes for
        # this disease (small/muscular defects that close on their own vs haemodynamically
        # significant defects needing surgical/transcatheter definitive repair) -- none of
        # the generic co-rendering branches above match this shape beyond name+note, so it
        # is rendered explicitly here, matching this file's established per-disease-guard
        # pattern, so the real Roguin/Hiraishi spontaneous-closure numbers, the 2026
        # 30-year perimembranous cohort numbers, the surgical/transcatheter definitive-
        # repair numbers, and the honest caveat are not silently dropped.
        if disease_id == "ventricular_septal_defect":
            p1 = co.get("pathway_1_spontaneous_closure")
            if isinstance(p1, dict):
                elements.append(Paragraph("Pathway 1 — Real Spontaneous Closure (No Intervention Needed):", body))
                for rk, rv in p1.items():
                    if rk == "source":
                        continue
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('vsd_', '').replace('_', ' ').title()}:</b> {rv}", bullet))
                if p1.get("source"):
                    elements.append(Paragraph(f"Source: {cite(p1['source'])}", cite_marker_s))
                elements.append(Spacer(1, 4))
            p2 = co.get("pathway_2_definitive_repair")
            if isinstance(p2, dict):
                elements.append(Paragraph("Pathway 2 — Real Definitive Repair (Surgical Patch or Transcatheter Device Closure):", body))
                for rk, rv in p2.items():
                    if rk == "source":
                        continue
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('vsd_', '').replace('_', ' ').title()}:</b> {rv}", bullet))
                if p2.get("source"):
                    elements.append(Paragraph(f"Source: {cite(p2['source'])}", cite_marker_s))
                elements.append(Spacer(1, 4))
            if co.get("real_honest_caveat"):
                elements.append(Paragraph(f"<b>Real honest caveat:</b> {co['real_honest_caveat']}", body))

        # Bursitis' curative_option carries its own real dual-pathway shape (aseptic_protocol
        # dict / septic_protocol dict / real_trial_data dict) reflecting the two genuinely
        # different real cure routes -- staged conservative care for aseptic bursitis vs
        # antibiotics-first management for septic bursitis -- that none of the generic
        # co-rendering branches above match beyond name+note, so it is rendered explicitly
        # here, matching this file's established per-disease-guard pattern, so the real
        # Sayegh/Deal/Pien/Smith/Weinstein/Germawi/Meade numbers are not silently dropped.
        if disease_id == "bursitis":
            ap = co.get("aseptic_protocol")
            if isinstance(ap, dict):
                elements.append(Paragraph("Aseptic Bursitis — Real Staged Conservative Protocol:", body))
                for rk, rv in ap.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• {rv}", bullet))
                elements.append(Spacer(1, 4))
            sp = co.get("septic_protocol")
            if isinstance(sp, dict):
                elements.append(Paragraph("Septic Bursitis — Real Antibiotics-First Protocol:", body))
                for rk, rv in sp.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• {rv}", bullet))
                elements.append(Spacer(1, 4))
            rtd = co.get("real_trial_data")
            if isinstance(rtd, dict):
                elements.append(Paragraph("Real trial data:", body))
                for rk, rv in rtd.items():
                    if isinstance(rv, str):
                        elements.append(Paragraph(f"• <b>{rk.replace('_', ' ').title()}:</b> {rv}", bullet))

        # Dupuytren's contracture's curative_option carries its own real, distinctive
        # by_severity shape (a list of stage/recommended/effectiveness/source dicts,
        # stratifying real treatment choice by disease stage and joint involved) that
        # none of the generic co-rendering branches above match beyond name+note, so it
        # is rendered explicitly here, matching this file's established per-disease-guard
        # pattern, so the real CORD I/II, needle-aponeurotomy and fasciectomy stratified
        # numbers are not silently dropped.
        if disease_id == "dupuytrens_contracture":
            by_sev = co.get("by_severity")
            if isinstance(by_sev, list):
                for stage in by_sev:
                    if not isinstance(stage, dict):
                        continue
                    if stage.get("stage"):
                        elements.append(Paragraph(f"<b>{stage['stage']}</b>", body))
                    if stage.get("recommended"):
                        elements.append(Paragraph(f"Recommended: {stage['recommended']}", bullet))
                    if stage.get("effectiveness"):
                        elements.append(Paragraph(f"• {stage['effectiveness']}", bullet))
                    if stage.get("source"):
                        elements.append(Paragraph(f"Source: {cite(stage['source'])}", cite_marker_s))
                    elements.append(Spacer(1, 4))

        # Addison's disease's curative_option (lifelong glucocorticoid + mineralocorticoid
        # replacement combined with structured patient education) carries its own real,
        # distinctive "components" list shape (component/real_recovery_data/source per item,
        # plus a top-level safety_note) that none of the generic co-rendering branches above
        # match beyond name+note, so it is rendered explicitly here, matching this file's
        # established per-disease-guard pattern, so the real Bornstein/Hahner/Husebye numbers
        # are not silently dropped.
        if disease_id == "addisons_disease":
            comps = co.get("components")
            if isinstance(comps, list):
                for comp in comps:
                    if not isinstance(comp, dict):
                        continue
                    if comp.get("component"):
                        elements.append(Paragraph(f"<b>{comp['component']}</b>", body))
                    if comp.get("real_recovery_data"):
                        elements.append(Paragraph(str(comp["real_recovery_data"]), small_grey))
                    if comp.get("source"):
                        elements.append(Paragraph(f"Source: {cite(comp['source'])}", cite_marker_s))
                    elements.append(Spacer(1, 4))
            if co.get("confidence"):
                elements.append(Paragraph(f"Confidence: {co['confidence']}", cite_marker_s))
            if co.get("safety_note"):
                elements.append(Paragraph(f"<i>Safety note: {co['safety_note']}</i>", small_grey))

        # Essential tremor's curative_option (MRgFUS thalamotomy and DBS of the VIM thalamus)
        # carries a distinct real shape (name/note/mrgfus_thalamotomy dict/deep_brain_stimulation
        # dict/the_durability_and_selection_boundary string) that the generic name+note rendering
        # above does not match at all beyond name+note -- rendered explicitly here, matching this
        # file's established per-disease-guard pattern, so the real Elias 2016 NEJM pivotal-trial
        # numbers, the Schuurman 2000 / Pahwa 2006 DBS numbers, and the honest durability/candidate-
        # selection caveat are not silently dropped.
        if disease_id == "essential_tremor":
            for proc_key, proc_title in (
                ("mrgfus_thalamotomy", "MRI-Guided Focused Ultrasound (MRgFUS) Thalamotomy"),
                ("deep_brain_stimulation", "Deep Brain Stimulation (VIM Thalamus)"),
            ):
                proc = co.get(proc_key)
                if not isinstance(proc, dict):
                    continue
                elements.append(Paragraph(proc_title, subhead))
                for pk, pv in proc.items():
                    if isinstance(pv, str):
                        elements.append(Paragraph(f"• <b>{pk.replace('_', ' ').title()}:</b> {pv}", bullet))
                elements.append(Spacer(1, 4))
            if co.get("the_durability_and_selection_boundary"):
                elements.append(Paragraph(f"<i>{co['the_durability_and_selection_boundary']}</i>", small_grey))

        elements.append(Spacer(1, 8))

    # ============ SECTION 1: EFFECTIVENESS BY TREATMENT TYPE ============
    elements.append(Paragraph("1. Effectiveness by Treatment Type", section_h))

    ert = disease.get("effectiveness_ranked_table")
    if ert:
        cell = ParagraphStyle("cell", parent=body, fontSize=8.3, leading=10.5)

        # Rows must render strictly high-to-low by effectiveness_pct, regardless of
        # the order/"rank" field stored in the JSON (several research forks left rows
        # in research order and only noted "not reordered" in their own report instead
        # of actually sorting) -- sort here so the PDF is always correct. Null/invalid
        # (>100 or non-numeric) percentages sort to the bottom rather than being dropped.
        def sort_key(r):
            v = r.get("effectiveness_pct")
            if isinstance(v, (int, float)) and 0 <= v <= 100:
                return (0, -v)
            return (1, 0)

        def build_ert_table(sorted_rows):
            rows = [["Rank", "Medicine", "Type", "Effectiveness", "Real metric"]]
            for i, r in enumerate(sorted_rows, 1):
                eff_pct = r.get("effectiveness_pct")
                if isinstance(eff_pct, (int, float)) and 0 <= eff_pct <= 100:
                    eff_str = f"{eff_pct:.1f}%"
                elif isinstance(eff_pct, (int, float)):
                    # A handful of rows legitimately fall outside 0-100% (e.g. a real
                    # placebo-adjusted reduction that mathematically exceeds 100%, or a
                    # deliberately negative value flagging a harm/worsening signal rather
                    # than a benefit) -- print the real number as-is; the row's own
                    # "metric" text explains why, rather than mislabeling it "invalid".
                    eff_str = f"{eff_pct:.1f}%"
                else:
                    eff_str = "N/A (see metric)"
                rows.append([str(i), Paragraph(r["name"], cell), Paragraph(r["type"], cell),
                             eff_str, Paragraph(r.get("metric") or "N/A", cell)])
            t = Table(rows, colWidths=[1.0 * cm, 3.6 * cm, 2.4 * cm, 2.0 * cm, 7.2 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8.3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GREEN_LT, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            return t

        def render_ert_table(rows_list):
            # Split into medicine/injection vs other (surgery/procedure/device/
            # lifestyle/non-drug) treatments -- every row must land in exactly one
            # bucket (no-data-loss guarantee), each sorted and rendered as its own
            # table under its own sub-heading.
            medicine_rows = [r for r in rows_list if classify_treatment_row(r) == "medicine"]
            other_rows = [r for r in rows_list if classify_treatment_row(r) == "other"]
            assert len(medicine_rows) + len(other_rows) == len(rows_list)
            if medicine_rows:
                elements.append(Paragraph(
                    "1a. Medicine / Injection Treatments — Effectiveness % and Why", subhead))
                elements.append(build_ert_table(sorted(medicine_rows, key=sort_key)))
                elements.append(Spacer(1, 6))
            if other_rows:
                elements.append(Paragraph(
                    "1b. Other Treatments (Surgery / Procedure / Device / Lifestyle / Non-Drug) "
                    "— Effectiveness % and Why", subhead))
                elements.append(build_ert_table(sorted(other_rows, key=sort_key)))
                elements.append(Spacer(1, 6))

        if "ranked_high_to_low" in ert:
            # Original flat shape — single ranking applies across the whole disease.
            elements.append(Paragraph("Effectiveness ranking — high to low (real, sourced %):", subhead))
            render_ert_table(ert["ranked_high_to_low"])
        elif "ranked_by_goal" in ert:
            # Goal-stratified shape (e.g. PCOS) — a single cross-goal ranking is not
            # clinically meaningful, so each treatment goal gets its own labeled table.
            elements.append(Paragraph("Effectiveness ranking — by treatment goal (real, sourced %):", subhead))
            for goal_key, goal_rows in ert["ranked_by_goal"].items():
                goal_label = goal_key.replace("_", " ").title()
                elements.append(Paragraph(f"Goal: {goal_label}", body))
                render_ert_table(goal_rows)
                elements.append(Spacer(1, 4))
        if ert.get("caveat"):
            elements.append(Paragraph(f"<i>{ert['caveat']}</i>", small_grey))
        elements.append(Spacer(1, 10))

    def render_medicine(m):
        m_type = m.get("type", "")
        m_name = m.get("name") or m.get("finding") or "Details"
        header = f"<b>{m_name}</b> &nbsp;<i>({m_type})</i>" if m_type else f"<b>{m_name}</b>"
        elements.append(Paragraph(header, subhead))
        if m.get("specific_drugs"):
            drugs = m["specific_drugs"]
            drugs_str = ", ".join(drugs) if isinstance(drugs, list) else str(drugs)
            elements.append(Paragraph(f"<b>Exact medicine(s):</b> {drugs_str}", body))
        if m.get("specific_procedure"):
            elements.append(Paragraph(f"<b>Exact procedure:</b> {m['specific_procedure']}", body))
        if "effectiveness" in m:
            eff_text = m["effectiveness"]
        else:
            # TIA's exhaustive_medicine_survey entries use effectiveness_pct + effectiveness_metric
            # instead of a single free-text "effectiveness" field -- render that shape instead of
            # crashing (mirrors this file's established defensive-fallback pattern elsewhere).
            eff_text = m.get("effectiveness_metric", "")
            if "effectiveness_pct" in m:
                eff_text = f"{m['effectiveness_pct']}% -- {eff_text}" if eff_text else f"{m['effectiveness_pct']}%"
        elements.append(Paragraph(f"<b>Effectiveness:</b> {eff_text}", body))
        reason = m.get("reason_why")
        if reason:
            reason_str = " ".join(reason) if isinstance(reason, list) else str(reason)
            elements.append(Paragraph(f"<b>Why (biological reason):</b> {reason_str}", body))
        if m.get("important_caveat"):
            elements.append(Paragraph(f"<b>Important caveat:</b> {m['important_caveat']}", body))
        if m.get("real_working_solution"):
            elements.append(Paragraph(f"<b>Real working solution:</b> {m['real_working_solution']}", body))
        if m.get("source") or m.get("confidence"):
            elements.append(Paragraph(f"Source: {cite(m.get('source', ''))} &nbsp;|&nbsp; Confidence: {m.get('confidence', '')}", cite_marker_s))
        elements.append(Spacer(1, 6))

    ems = disease.get("exhaustive_medicine_survey", {})
    if ems.get("note"):
        elements.append(Paragraph(ems["note"], body))
        elements.append(Spacer(1, 6))
    MED_GROUP_LABELS = {
        "larc_tlm_early_stage_glottic": "Laryngeal Cancer -- Transoral Laser Microsurgery (TLM), Real Primary Curative Option for Early-Stage (Tis-T1-T2) Glottic Cancer (Korkmaz 2022; Vaculik 2019 Meta-Analysis):",
        "larc_radiotherapy_alone_early_stage_glottic": "Laryngeal Cancer -- Radiotherapy Alone, Real Primary Curative Option for Early-Stage (T1-T2) Glottic Cancer (Murakami 2005; Seno 2024):",
        "larc_concurrent_chemoradiation_larynx_preservation_locally_advanced": "Laryngeal Cancer -- Concurrent Cisplatin-Radiotherapy, Real RTOG 91-11-Proven Larynx-Preservation Standard for Locally Advanced Disease (Forastiere 2003 NEJM; Forastiere 2013 JCO):",
        "larc_total_laryngectomy_advanced_salvage": "Laryngeal Cancer -- Total Laryngectomy, Real Standard for Advanced/Salvage Disease Not Amenable to Organ Preservation (Meulemans 2021):",
        "larc_immunotherapy_recurrent_metastatic": "Laryngeal Cancer -- Nivolumab/Pembrolizumab (Anti-PD-1 Immunotherapy), Real Non-Curative Survival Benefit for Recurrent/Metastatic Disease, CheckMate 141/KEYNOTE-048 Trials (Ferris 2016 NEJM; Burtness 2019 Lancet):",
        "hs_adalimumab": "Hidradenitis Suppurativa -- Adalimumab (Anti-TNF-alpha), Real First Regulatory-Approved Biologic, PIONEER I/II Phase 3 Trials (Kimball 2016 NEJM):",
        "hs_secukinumab": "Hidradenitis Suppurativa -- Secukinumab (Anti-IL-17A), Real Phase 3 Trial-Proven Alternative Biologic, SUNSHINE/SUNRISE Trials (Kimball 2023 Lancet):",
        "hs_bimekizumab": "Hidradenitis Suppurativa -- Bimekizumab (Dual Anti-IL-17A/IL-17F), Real Newest Phase 3 Trial-Proven Biologic, BE HEARD I/II Trials (Kimball 2024 Lancet):",
        "hs_wide_surgical_excision": "Hidradenitis Suppurativa -- Wide Surgical Excision (Flap/Graft Closure), Real Highest-Cure-Rate Procedural Option for Localized Chronic Disease (Mehdizadeh 2015 Meta-Analysis):",
        "hs_topical_oral_antibiotics_mild_disease": "Hidradenitis Suppurativa -- Topical Clindamycin and Oral Clindamycin+Rifampicin, Real Guideline First-/Second-Line Antibiotic Therapy for Mild-to-Moderate Disease (Clemmensen 1983; Jemec/Wendelboe 1998; Gener 2009):",
        "hs_intralesional_corticosteroids_flares": "Hidradenitis Suppurativa -- Intralesional Triamcinolone Acetonide, Real Prospective-Case-Series-Verified Option for Acute Flares (Riis 2016 JAAD):",
        "pr_watchful_waiting_self_resolution": "Pityriasis Rosea -- Watchful Waiting / Self-Resolution, Real Default Curative Course for the Great Majority of Cases (Contreras-Ruiz Cochrane 2019; Ganguly 2014 RCT):",
        "pr_oral_antihistamines_pruritus": "Pityriasis Rosea -- Oral Antihistamines for Pruritus, Real Guideline-Endorsed Symptomatic First-Line (Villalon-Gomez AFP 2018; Ciccarese 2024 Network Meta-Analysis):",
        "pr_topical_corticosteroids_itch_relief": "Pityriasis Rosea -- Topical Corticosteroids for Itch Relief, Real Guideline-Endorsed Symptomatic Option (Villalon-Gomez AFP 2018; Chuh JEADV 2016 Position Statement):",
        "pr_high_dose_oral_acyclovir_early_severe": "Pityriasis Rosea -- High-Dose Oral Acyclovir for Early/Severe Disease, Real Best-Ranked Intervention for Rash Improvement in a 2024 Network Meta-Analysis (Ganguly 2014 RCT; Das 2015 RCT; Ciccarese 2024):",
        "pr_oral_erythromycin_mixed_replication": "Pityriasis Rosea -- Oral Erythromycin, Real Original Positive RCT but Honestly Unreplicated by Other Macrolides (Sharma 2000 JAAD; Amer/Fischer 2006 Pediatrics; Pandhi 2014; Ahmed 2014):",
        "cdrm_patch_testing_allergen_identification": "Contact Dermatitis -- Patch Testing for Allergen Identification, Real Diagnostic Gateway to Curative Avoidance (Korkmaz 2019 Outcome Study; Rajagopalan 1997 Multicenter QoL Study):",
        "cdrm_allergen_irritant_avoidance": "Contact Dermatitis -- Allergen/Irritant Avoidance, Real Disease-Removing Intervention Following Identification (Korkmaz 2019; Usatine/Riojas 2010 AFP Guideline):",
        "cdrm_topical_corticosteroids": "Contact Dermatitis -- Topical Corticosteroids (Triamcinolone 0.1%, Clobetasol 0.05%), Real First-Line Symptomatic Therapy for Active Flares (Usatine/Riojas 2010 AFP):",
        "cdrm_emollients_barrier_repair": "Contact Dermatitis -- Emollients/Moisturizing Cream, Real Measured Barrier-Repair Adjunct in Both Irritant and Allergic Disease (De Paepe 2001 Contact Dermatitis):",
        "cdrm_topical_calcineurin_inhibitors": "Contact Dermatitis -- Topical Calcineurin Inhibitor (Tacrolimus 0.1%), Real Trial-Verified Non-Steroidal Option for Sensitive Areas (Saripalli 2003 JAAD RCT):",
        "cdrm_oral_systemic_corticosteroids": "Contact Dermatitis -- Oral/Systemic Corticosteroids, Real Guideline Option for Severe Widespread (>20% BSA) Reactions Only (Usatine/Riojas 2010 AFP):",
        "mc_watchful_waiting_spontaneous_resolution": "Molluscum Contagiosum -- Watchful Waiting / Spontaneous Resolution, Real Guideline-Endorsed Route to Genuine Cure in Immunocompetent Patients (Olsen 2015 UK Cohort; Cochrane 2017 Review):",
        "mc_cantharidin_topical_application": "Molluscum Contagiosum -- Cantharidin 0.7% w/v Topical Solution (VP-102/YCANTH), Real Pivotal Phase III Trial-Verified In-Office Vesicant Therapy (Eichenfield 2021 Pooled Phase III CAMP-1/CAMP-2):",
        "mc_berdazimer_topical_gel": "Molluscum Contagiosum -- Berdazimer Gel 10.3% (Zelsuvmi), Real FDA-Approved (January 2024) At-Home Nitric-Oxide-Releasing Antiviral, Real Integrated Phase III B-SIMPLE Trial Data (Sugarman 2024 JAAD):",
        "mc_cryotherapy": "Molluscum Contagiosum -- Cryotherapy (Liquid Nitrogen), Real Single-Center RCT-Verified Rapid In-Office Physical Ablation (Al-Mutairi 2010 Comparative RCT; Chao 2023 Network Meta-Analysis):",
        "mc_curettage_refractory_lesions": "Molluscum Contagiosum -- Curettage, Real Pooled-Systematic-Review-Verified Highest-Clearance Physical Option for Refractory/Solitary Lesions (Wang 2026 Systematic Review; Hanna 2006 Comparative RCT):",
        "cu_standard_dose_second_gen_antihistamines": "Chronic Urticaria -- Standard-Dose Second-Generation Antihistamines (Cetirizine, Levocetirizine, Desloratadine, Fexofenadine, Loratadine), Real Guideline First-Line Therapy (Staevska 2010, EAACI/GA2LEN Zuberbier 2022):",
        "cu_updosed_antihistamines_4x": "Chronic Urticaria -- Up-Dosed (Up to 4x) Second-Generation Antihistamines, Real Guideline Step 2, Highest-Responder-Rate Option (Staevska 2010 JACI):",
        "cu_omalizumab_anti_ige": "Chronic Urticaria -- Omalizumab (Anti-IgE), Real Pivotal-Trial-Proven Step 3 for Antihistamine-Refractory Disease (ASTERIA II, Maurer 2013 NEJM; GLACIAL, Kaplan 2013 JACI):",
        "cu_cyclosporine_refractory": "Chronic Urticaria -- Cyclosporine, Real Step 4 Option for Omalizumab-Refractory Disease (Vena 2006 JAAD):",
        "cu_short_course_corticosteroids_flares": "Chronic Urticaria -- Short-Course Oral Corticosteroids for Severe Acute Flares Only, Real Guideline-Endorsed Rescue Option, Not for Maintenance (EAACI/GA2LEN Zuberbier 2022):",
        "lp_topical_corticosteroids": "Lichen Planus -- Topical Corticosteroids, Real Guideline First-Line Therapy for All Forms (Usatine 2011 AFP; Thongprasom 1992 Head-to-Head RCT):",
        "lp_topical_calcineurin_inhibitors": "Lichen Planus -- Topical Calcineurin Inhibitors (Tacrolimus, Pimecrolimus), Real Steroid-Sparing Option Especially for Oral/Genital Disease (Laeijendecker 2006; Cochrane Cheng 2012):",
        "lp_oral_corticosteroids": "Lichen Planus -- Oral (Systemic) Corticosteroids for Severe, Widespread Disease (Usatine 2011 AFP; Iraji 2011 RCT):",
        "lp_oral_retinoids_acitretin": "Lichen Planus -- Oral Retinoids (Acitretin), Real Placebo-Controlled RCT for Refractory Disease (Laurberg 1991 JAAD):",
        "lp_phototherapy_nbuvb": "Lichen Planus -- Narrowband UVB Phototherapy, Real RCT-Proven Alternative to Systemic Corticosteroids (Iraji 2011 RCT):",
        "lp_malignant_transformation_monitoring": "Lichen Planus -- Lifelong Malignant-Transformation Surveillance for Oral Disease, Real Quantified Oncologic Risk (Gonzalez-Moles 2024 Meta-Analysis):",
        "scd_allogeneic_hsct_curative": "Sickle Cell Disease -- Allogeneic HSCT (Preferably HLA-Matched Sibling Donor), Real Established Cure (Folarin 2026 Meta-Analysis, Alshahrani 2024 Meta-Analysis, Eapen 2019):",
        "scd_exa_cel_casgevy_gene_therapy": "Sickle Cell Disease -- Exagamglogene Autotemcel (Casgevy, exa-cel), Real First-Ever FDA-Approved CRISPR Gene-Editing Cure (CLIMB SCD-121, Frangoul 2024 NEJM):",
        "scd_lovo_cel_lyfgenia_gene_therapy": "Sickle Cell Disease -- Lovotibeglogene Autotemcel (Lyfgenia, lovo-cel), Real Lentiviral Gene Addition Cure (HGB-206, Kanter 2022 NEJM):",
        "scd_hydroxyurea_disease_modifying_therapy": "Sickle Cell Disease -- Hydroxyurea, Real Foundational Disease-Modifying Therapy, Not Curative (MSH Trial, Charache 1995 NEJM):",
        "scd_voxelotor_hb_oxygen_affinity_modulator": "Sickle Cell Disease -- Voxelotor (Oxbryta), Real Haemoglobin-Oxygen Affinity Modulator, Not Curative (HOPE Trial, Vichinsky 2019 NEJM, Howard 2021):",
        "scd_crizanlizumab_p_selectin_inhibitor": "Sickle Cell Disease -- Crizanlizumab (Adakveo), Real P-Selectin Inhibitor, Not Curative (SUSTAIN Trial, Ataga 2017 NEJM; Real-World Evidence, DeBonnett 2025):",
        "scd_l_glutamine_oxidative_stress_reduction": "Sickle Cell Disease -- L-Glutamine (Endari), Real Modest-Effect Oral Antioxidant, Not Curative (Niihara 2018 NEJM):",
        "scd_chronic_transfusion_stroke_prevention": "Sickle Cell Disease -- Chronic Transfusion for Primary Stroke Prevention, Real Guideline-Mandated Preventive Therapy (STOP Trial, Adams 1998 NEJM):",
        "scd_vaccination_penicillin_prophylaxis_functional_asplenia": "Sickle Cell Disease -- Penicillin Prophylaxis Plus Pneumococcal Vaccination for Functional Asplenia, Real Guideline-Mandated Infection Prevention (PROPS Trial, Gaston 1986 NEJM):",
        "ad_glucocorticoid_replacement_hydrocortisone": "Addison's Disease -- Glucocorticoid Replacement (Hydrocortisone/Cortisone Acetate/Dual-Release Hydrocortisone), Real First-Line Lifelong Therapy (Bornstein/Endocrine Society Guideline 2016, Johannsson 2012):",
        "ad_mineralocorticoid_replacement_fludrocortisone": "Addison's Disease -- Fludrocortisone Mineralocorticoid Replacement, Real Mandatory Second Hormone Axis in Primary Adrenal Insufficiency (Bornstein/Endocrine Society Guideline 2016):",
        "ad_dhea_supplementation_select_patients": "Addison's Disease -- DHEA Supplementation for Selected Patients With Persistent Impaired Well-Being (Arlt 1999 NEJM, Bennett 2022):",
        "ad_emergency_injectable_hydrocortisone_crisis": "Addison's Disease -- Emergency Injectable Hydrocortisone for Adrenal Crisis Prevention/Rescue, Real Guideline-Mandatory Rescue Medication (Bornstein 2016, Hahner 2010, Husebye 2021):",
        "ad_patient_education_steroid_alert_card_sick_day_rules": "Addison's Disease -- Steroid Alert Card, Sick-Day Dose Escalation and Emergency-Injection Training, Real Guideline-Mandated Crisis-Prevention Education (Bornstein 2016, Pilz 2022):",
        "vur_observation_watchful_waiting": "Vesicoureteral Reflux -- Observation/Watchful Waiting, Real Default First-Line Management for Low-Grade VUR (Skoog 1987, Peters/AUA Guideline 2010, Sjostrom 2010):",
        "vur_antibiotic_prophylaxis_rivur": "Vesicoureteral Reflux -- Continuous Antibiotic Prophylaxis, Real RIVUR-Trial-Proven UTI Recurrence Reduction (Hoberman 2014 NEJM):",
        "vur_endoscopic_deflux_injection": "Vesicoureteral Reflux -- Endoscopic Dextranomer/Hyaluronic Acid (Deflux) Injection, Real High-Success Outpatient Correction (Kirsch 2004, Lackgren 2001, Peters/AUA Guideline 2010):",
        "vur_ureteral_reimplantation_surgery": "Vesicoureteral Reflux -- Ureteral Reimplantation Surgery, Real Definitive Cure for Persistent/High-Grade Disease (Peters/AUA Guideline 2010):",
        "apn_oral_fluoroquinolones_first_line": "Acute Pyelonephritis -- Oral Fluoroquinolones (Ciprofloxacin, Levofloxacin), Real First-Line Short-Course Cure (Talan 2000, Klausner 2007):",
        "apn_oral_tmp_smx_susceptibility_dependent": "Acute Pyelonephritis -- Oral Trimethoprim-Sulfamethoxazole, Real Option Only If Culture-Confirmed Susceptible (Talan 2000, IDSA/ESCMID 2011):",
        "apn_initial_parenteral_empiric_long_acting": "Acute Pyelonephritis -- Initial Parenteral Ceftriaxone/Aminoglycoside, Real Bridge Therapy for High/Unknown Resistance (IDSA/ESCMID 2011):",
        "apn_hospitalized_severe_intravenous_regimens": "Acute Pyelonephritis -- Intravenous Regimens for Hospitalized/Severe Disease (IDSA/ESCMID 2011, Johnson & Russo 2018):",
        "apn_source_control_obstruction_procedures": "Acute Pyelonephritis -- Percutaneous Nephrostomy / Ureteral Stent, Real Mandatory Source Control for Obstructive/Complicated Disease (Pearle 1998, Newcomer 2022):",
        "ui_pelvic_floor_muscle_training_conservative": "Urinary Incontinence -- Pelvic Floor Muscle Training (Kegel Exercises), Real First-Line Non-Surgical Option, No Doctor Gate Needed (Dumoulin Cochrane 2018, Subak PRIDE Trial NEJM 2009):",
        "ui_anticholinergic_medicines": "Urinary Incontinence -- Oral Anticholinergics (Solifenacin and Class) for Urge Incontinence/Overactive Bladder (Wagg 2006):",
        "ui_beta3_agonist_medicines": "Urinary Incontinence -- Mirabegron (Beta-3 Agonist) for Urge Incontinence/Overactive Bladder (Khullar SCORPIO Trial, Eur Urol 2013):",
        "ui_snri_medicine_off_label_or_regional_approval": "Urinary Incontinence -- Duloxetine (SNRI) for Stress Urinary Incontinence (Norton 2002):",
        "ui_botulinum_toxin_injection_procedure": "Urinary Incontinence -- Intradetrusor OnabotulinumtoxinA Injection for Refractory Urge Incontinence (Chapple 2013):",
        "ui_urethral_bulking_injection_procedure": "Urinary Incontinence -- Urethral Bulking Agent Injection (Macroplastique) for Stress Urinary Incontinence, Real Lower-Invasiveness Alternative to Sling Surgery:",
        "ui_mid_urethral_sling_surgery_procedure": "Urinary Incontinence -- Mid-Urethral Sling Surgery (TVT/TOT), Real Closest-to-Permanent-Cure Option for Stress Urinary Incontinence (Nilsson 17-Year Follow-Up 2013, Ford Cochrane 2017):",
        "ui_neuromodulation_procedure_refractory_urge": "Urinary Incontinence -- Sacral Neuromodulation / Posterior Tibial Nerve Stimulation for Refractory Urge Incontinence (van Ophoven 2010):",
        "bldc_turbt_diagnostic_and_therapeutic_procedure": "Bladder Cancer -- TURBT, Real Mandatory Diagnostic-and-Therapeutic First Step (EAU Guidelines, Babjuk 2022):",
        "bldc_intravesical_bcg_immunotherapy_nmibc": "Bladder Cancer -- Intravesical BCG Immunotherapy, Real Leading Cure/Long-Term-Control Story for NMIBC (Malmstrom 2009, Sylvester 2002/2005, Lamm 2000):",
        "bldc_intravesical_chemotherapy_mitomycin_c_nmibc": "Bladder Cancer -- Intravesical Mitomycin C, Real Standard for Low-Risk NMIBC (Sylvester 2004, Malmstrom 2009):",
        "bldc_radical_cystectomy_mibc": "Bladder Cancer -- Radical Cystectomy With Pelvic Lymphadenectomy, Real Curative-Intent Standard for Muscle-Invasive Disease (SEER; Grossman 2003):",
        "bldc_neoadjuvant_chemotherapy_mibc": "Bladder Cancer -- Neoadjuvant Cisplatin-Based Chemotherapy (MVAC/GC) Before Cystectomy, Real Survival-Extending Addition (Grossman 2003 NEJM):",
        "bldc_bladder_preservation_trimodality_therapy_mibc": "Bladder Cancer -- Bladder-Sparing Trimodality Therapy (TURBT + Chemoradiotherapy), Real Evidence-Based Alternative to Cystectomy (BC2001, James 2012 NEJM):",
        "bldc_immune_checkpoint_inhibitors_advanced": "Bladder Cancer -- Pembrolizumab, Real Standard Immunotherapy for Advanced/Metastatic Urothelial Carcinoma (KEYNOTE-045 Bellmunt 2017, KEYNOTE-052 Balar 2017):",
        "bldc_antibody_drug_conjugate_ev_pembrolizumab_advanced": "Bladder Cancer -- Enfortumab Vedotin Plus Pembrolizumab, Real New First-Line Standard, Practice-Changing (EV-302, Powles 2024 NEJM):",
        "bldc_bcg_unresponsive_gene_therapy_nadofaragene": "Bladder Cancer -- Nadofaragene Firadenovec Intravesical Gene Therapy, Real FDA-Approved Option for BCG-Unresponsive NMIBC (Boorjian 2021 Lancet Oncol):",
        "gc_endoscopic_submucosal_dissection_early_gastric_cancer": "Gastric Cancer -- Endoscopic Submucosal Dissection (ESD), Real Leading Cure Story for Early-Stage Disease (Isomoto 2009, Oda 2006):",
        "gc_lymph_node_metastasis_risk_basis_for_expanded_indication": "Gastric Cancer -- Real Lymph-Node-Metastasis Risk Evidence Underpinning ESD's Curative-Resection Criteria (Gotoda 2000):",
        "gc_perioperative_flot_chemotherapy_locally_advanced": "Gastric Cancer -- Perioperative FLOT Chemotherapy + Gastrectomy, Real Current Standard for Locally Advanced Disease (FLOT4, Al-Batran 2019):",
        "gc_magic_perioperative_ecf_vs_surgery_alone": "Gastric Cancer -- Perioperative ECF Chemotherapy + Surgery vs Surgery Alone, Real Foundational Trial (MAGIC, Cunningham 2006):",
        "gc_her2_targeted_trastuzumab_advanced": "Gastric Cancer -- Trastuzumab Plus Chemotherapy, Real HER2-Targeted Option for HER2-Positive Advanced Disease (ToGA, Bang 2010):",
        "gc_first_line_immunotherapy_nivolumab_checkmate649": "Gastric Cancer -- Nivolumab Plus Chemotherapy, Real First-Line Immunotherapy Standard for PD-L1 CPS>=5 Advanced Disease (CheckMate 649, Janjigian 2021):",
        "gc_later_line_immunotherapy_nivolumab_attraction2": "Gastric Cancer -- Nivolumab Monotherapy, Real Later-Line Option for Heavily Pretreated Advanced Disease (ATTRACTION-2, Kang 2017):",
        "gc_screening_and_surgical_procedures": "Gastric Cancer -- National Endoscopic Screening (Japan/Korea) + D2 Gastrectomy, Real Enabling Infrastructure and Surgical Standard:",
        "sjs_causative_drug_identification_withdrawal": "Stevens-Johnson Syndrome/TEN -- Immediate Causative-Drug Identification and Withdrawal, Real Single Most Life-Saving Intervention (Garcia-Doval 2000 Arch Dermatol):",
        "sjs_burn_unit_specialized_supportive_care": "Stevens-Johnson Syndrome/TEN -- Burn-Unit/Specialized-Center Supportive Care (Fluid/Electrolyte Management, Wound Care, Infection Prevention), Real Referral-Timing-Dependent Survival Benefit (McGee & Munster 1998 Plast Reconstr Surg; Halebian 1986 Ann Surg):",
        "sjs_cyclosporine": "Stevens-Johnson Syndrome/TEN -- Ciclosporin, Real Open-Trial Signal Not Yet Confirmed by a Controlled Trial (Valeyrie-Allanore 2010 Br J Dermatol):",
        "sjs_ivig": "Stevens-Johnson Syndrome/TEN -- Intravenous Immunoglobulin (IVIG), Real Honest Mixed/Negative Evidence, Not Guideline-Recommended (Bachot 2003 Arch Dermatol; Schneck/EuroSCAR 2008 JAAD):",
        "sjs_systemic_corticosteroids": "Stevens-Johnson Syndrome/TEN -- Systemic Corticosteroids, Real Honest Conflicting Evidence Across Studies and Decades (Halebian 1986 Ann Surg; Schneck/EuroSCAR 2008 JAAD):",
        "sjs_etanercept_tnf_inhibitor": "Stevens-Johnson Syndrome/TEN -- Etanercept (TNF-alpha Antagonist), Real Randomized Controlled Trial Advance Over Corticosteroids (Wang 2018 J Clin Invest):",
        "cg_h_pylori_bismuth_amoxicillin_vonoprazan_triple_therapy": "Chronic Gastritis -- Bismuth-Amoxicillin-Vonoprazan (BAV) Triple Therapy, Real Highest-Efficacy First-Line H. pylori Eradication Regimen (Hsu 2026):",
        "cg_h_pylori_bismuth_quadruple_therapy": "Chronic Gastritis -- Bismuth Quadruple Therapy, Real Standard Resistance-Independent H. pylori Eradication Regimen (Koh 2026, Venerito 2013):",
        "cg_h_pylori_vonoprazan_amoxicillin_dual_therapy": "Chronic Gastritis -- Vonoprazan-Amoxicillin Dual Therapy, Real Simplified H. pylori Eradication Regimen (Hsu 2026, Georgiev 2026):",
        "cg_h_pylori_clarithromycin_triple_therapy_legacy": "Chronic Gastritis -- Clarithromycin Triple Therapy, Real Legacy H. pylori Regimen Now Resistance-Limited (Venerito 2013, Maastricht VI 2022):",
        "cg_acid_suppression_symptom_control": "Chronic Gastritis -- Proton Pump Inhibitors for Real Symptom Control and Eradication-Regimen Support (Maastricht VI 2022):",
        "cg_vitamin_b12_replacement_autoimmune_gastritis": "Chronic Gastritis -- Vitamin B12 (Cobalamin) Replacement for Autoimmune Gastritis, Real Fully Correctable Deficiency (OB12 Trial 2020, AGA 2021):",
        "cg_iron_replacement_autoimmune_gastritis": "Chronic Gastritis -- Iron Replacement for Autoimmune/Atrophic Gastritis, Real Second Correctable Deficiency (AGA 2021):",
        "cg_gastric_cancer_and_neuroendocrine_tumor_surveillance_autoimmune_gastritis": "Chronic Gastritis -- Endoscopic Gastric Cancer/Neuroendocrine Tumor Surveillance for Autoimmune Gastritis, Real Risk-Reduction Procedure (AGA 2021):",
        "aa_intralesional_corticosteroid_injection": "Alopecia Areata -- Intralesional Corticosteroid Injection, Real First-Line Treatment for Limited Patchy Disease (Ustuner 2017, Cochrane 2023):",
        "aa_jak_inhibitor_baricitinib": "Alopecia Areata -- Baricitinib (Olumiant), Real FDA-Approved Oral JAK1/JAK2 Inhibitor Breakthrough for Severe Disease (BRAVE-AA1/AA2, King 2022 NEJM):",
        "aa_jak_inhibitor_ritlecitinib": "Alopecia Areata -- Ritlecitinib (Litfulo), Real FDA-Approved Oral JAK3/TEC-Kinase Inhibitor Including Adolescents (ALLEGRO, King 2023 Lancet):",
        "aa_topical_corticosteroids": "Alopecia Areata -- Topical Corticosteroids for Limited Patchy Disease (Pratt 2017):",
        "aa_oral_systemic_corticosteroids": "Alopecia Areata -- Oral/Systemic Corticosteroids for Extensive or Rapidly Progressive Disease (Olsen 1992):",
        "aa_contact_immunotherapy_dpcp": "Alopecia Areata -- Contact Immunotherapy with Diphenylcyclopropenone (DPCP) for Extensive/Refractory Disease (Wiseman 2001, Hull 1991):",
        "aa_topical_minoxidil_adjunct": "Alopecia Areata -- Topical Minoxidil, Real Adjunct Hair-Growth Stimulant, Not Disease-Modifying (Cochrane 2023):",
        "ar_oral_antihistamines_second_generation": "Allergic Rhinitis -- Second-Generation Oral Antihistamines: Cetirizine, Loratadine, Fexofenadine (Lockey 1996, Ciprandi 1997):",
        "ar_intranasal_corticosteroids": "Allergic Rhinitis -- Intranasal Corticosteroids: Fluticasone Furoate/Propionate, Mometasone Furoate (Weiner 1998 Meta-Analysis, Mandl 1997, Andrews 2009):",
        "ar_combination_intranasal_azelastine_fluticasone": "Allergic Rhinitis -- Combination Intranasal Azelastine-Fluticasone Spray (MP29-02/Dymista; Carr 2012):",
        "ar_leukotriene_receptor_antagonists": "Allergic Rhinitis -- Leukotriene Receptor Antagonist: Montelukast (Wilson 2002, Wilson 2000):",
        "ar_allergen_immunotherapy_scit_slit": "Allergic Rhinitis -- Allergen Immunotherapy: Subcutaneous (SCIT) and Sublingual (SLIT) Tablets/Drops, Real Disease-Modifying Option (Durham 1999/2010/2012, PAT Study, Cochrane Reviews):",
        "ar_anti_ige_biologic_refractory": "Allergic Rhinitis -- Omalizumab (Anti-IgE) for Refractory/Comorbid Disease (Casale 2001 JAMA):",
        "ar_saline_nasal_irrigation": "Allergic Rhinitis -- Saline Nasal Irrigation, Real Low-Cost Adjunct (Chitsuthipakorn 2022 Systematic Review):",
        "ar_negative_or_neutral_evidence": "Allergic Rhinitis -- Negative/Neutral Evidence: First-Generation Sedating Antihistamines (ARIA-EAACI 2024-2025 Guideline):",
        "crs_intranasal_corticosteroids": "Chronic Rhinosinusitis -- Intranasal Corticosteroids, Real First-Line Therapy for All CRS (Chong 2016 Cochrane):",
        "crs_saline_nasal_irrigation": "Chronic Rhinosinusitis -- Saline Nasal Irrigation, Real Low-Cost Adjunct (Chong 2016 Cochrane):",
        "crs_dupilumab_crswnp": "Chronic Rhinosinusitis -- Dupilumab (Anti-IL-4Ra) for CRSwNP, Real Dramatic-Improvement Biologic, SINUS-24/SINUS-52 Phase 3 Trials (Bachert 2019 Lancet):",
        "crs_other_biologics_omalizumab_mepolizumab": "Chronic Rhinosinusitis -- Other Real Trial-Proven Biologics for CRSwNP: Omalizumab (POLYP 1/2, Gevaert 2020) and Mepolizumab (SYNAPSE, Han 2021):",
        "crs_short_course_oral_corticosteroids": "Chronic Rhinosinusitis -- Short-Course Oral Corticosteroids, Adjunct for Flares (Head 2016 Cochrane):",
        "crs_endoscopic_sinus_surgery": "Chronic Rhinosinusitis -- Endoscopic Sinus Surgery, Real High-Success Definitive Option for Medically-Refractory Disease (Hopkins 2009 English National Comparative Audit):",
        "crs_negative_or_limited_evidence": "Chronic Rhinosinusitis -- Real But Weak/Limited Evidence: Systemic and Topical Antibiotics (Head 2016 Cochrane):",
        "epi_direct_compression": "Epistaxis -- Direct Nasal Compression, Real Guideline First-Line First Aid (Tunkel 2020 AAO-HNS Guideline):",
        "epi_topical_vasoconstrictor_compression": "Epistaxis -- Topical Vasoconstrictor (Oxymetazoline) / Topical Tranexamic Acid-Assisted Compression (Mylonas 2023 Review; Fatahi 2026 Meta-Analysis):",
        "epi_chemical_cautery": "Epistaxis -- Chemical Cautery with Silver Nitrate, Real High-Cure-Rate Definitive Treatment for Recurrent Anterior Epistaxis (Limbrick 2019; Alsaif 2020 Meta-Analysis):",
        "epi_electrocautery": "Epistaxis -- Electrocautery, Real More-Durable Alternative to Chemical Cautery (Mylonas 2023 Review):",
        "epi_nasal_packing": "Epistaxis -- Nasal Packing for Active/Refractory Bleeding, Plus Topical Antiseptic Cream Adjunct (Tunkel 2020 AAO-HNS Guideline; Garry 2023):",
        "epi_arterial_ligation_embolization": "Epistaxis -- Endoscopic Arterial Ligation and Endovascular Embolization, Real High-Success Definitive Options for Severe/Refractory/Posterior Epistaxis (Bonnici 2023; Hoffman 2022 Meta-Analyses):",
        "di_desmopressin_central_medicines": "Diabetes Insipidus -- Desmopressin (DDAVP), Real Near-Curative Hormone-Replacement Therapy for Central Diabetes Insipidus (Fukuda 2003, Christ-Crain Nat Rev Dis Primers 2019):",
        "di_thiazide_nephrogenic_medicines": "Diabetes Insipidus -- Thiazide Diuretics (Hydrochlorothiazide), Real Paradoxical First-Line Antidiuretic Therapy for Nephrogenic Diabetes Insipidus (Jakobsson & Berg 1994, Bockenhauer & Bichet 2015):",
        "di_amiloride_lithium_medicines": "Diabetes Insipidus -- Amiloride, Real Preferred Add-On for Nephrogenic DI, Particularly Lithium-Induced NDI (Bedford 2008, Alon & Chan 1985, Kirchlechner 1999):",
        "di_nsaid_adjunct_medicines": "Diabetes Insipidus -- NSAIDs (Indomethacin), Real Adjunct to Thiazide for Nephrogenic Diabetes Insipidus (Jakobsson & Berg 1994, Knoers & Monnens 1990):",
        "di_diet_adjunct_lifestyle": "Diabetes Insipidus -- Low-Sodium/Low-Protein Diet, Real Drug-Free Adjunct Reducing Obligate Renal Solute Load (Blalock 1977):",
        "hid_spontaneous_resorption_natural_history": "Herniated Intervertebral Disc -- Spontaneous Disc Resorption / Natural History, Real First-Line 'Treatment' for the Majority:",
        "hid_conservative_management_vs_surgery_outcomes": "Herniated Intervertebral Disc -- Conservative (Non-Surgical) Management, Real Equivalent 1-Year Recovery to Early Surgery:",
        "hid_nsaids": "Herniated Intervertebral Disc -- Oral NSAIDs, Real But Small Symptomatic Benefit During the Recovery/Resorption Window:",
        "hid_muscle_relaxants": "Herniated Intervertebral Disc -- Skeletal Muscle Relaxants, Real Short-Term Benefit for Acute Painful Flares:",
        "hid_oral_glucocorticoids_sciatica": "Herniated Intervertebral Disc -- Systemic Glucocorticoids for Sciatica, Real Uncertain/Weak Evidence:",
        "hid_epidural_steroid_injection": "Herniated Intervertebral Disc -- Epidural Corticosteroid Injection, Real Modest Short-Term Benefit for Persistent Radicular Pain:",
        "hid_microdiscectomy": "Herniated Intervertebral Disc -- Microdiscectomy, Real High-Success Durable Procedure for Refractory/Severe Cases:",
        "cts_carpal_tunnel_release_surgery_open_or_endoscopic": "Carpal Tunnel Syndrome -- Carpal Tunnel Release Surgery (Open or Endoscopic), Real Closest-to-Cure Procedure for Confirmed Moderate-Severe Disease:",
        "cts_endoscopic_vs_open_release_technique_choice": "Carpal Tunnel Syndrome -- Endoscopic vs Open Release, Real Equal Cure Rate, Different Recovery/Complication Profile:",
        "cts_corticosteroid_injection_first_line_effective": "Carpal Tunnel Syndrome -- Local Corticosteroid Injection, Real Effective First-Line/Bridging Option for Mild-Moderate Disease:",
        "cts_corticosteroid_injection_vs_surgery_uncertain": "Carpal Tunnel Syndrome -- Corticosteroid Injection vs Surgery Head-to-Head, Real Honestly Uncertain Evidence:",
        "cts_wrist_night_splinting_mild_disease": "Carpal Tunnel Syndrome -- Wrist Night Splinting, Real but Weak Evidence, Reasonable First Step for Mild Disease:",
        "cts_therapeutic_ultrasound_low_quality_evidence": "Carpal Tunnel Syndrome -- Therapeutic Ultrasound, Real but Low-Quality Evidence (Other/Adjunct):",
        "cts_exercise_nerve_gliding_mobilisation_very_low_quality": "Carpal Tunnel Syndrome -- Exercise, Nerve-Gliding and Joint Mobilisation, Real but Very-Low-Quality Evidence (Other/Adjunct):",
        "cts_postsurgical_rehabilitation_no_clear_added_benefit": "Carpal Tunnel Syndrome -- Post-Surgical Rehabilitation, Real Honest Negative/Neutral Finding (No Clear Added Benefit):",
        "cts_oral_conservative_options_ineffective_or_unproven": "Carpal Tunnel Syndrome -- Diuretics, Oral Pyridoxine (Vitamin B6), Oral NSAIDs, Yoga, Laser Acupuncture, Real Honest Negative Finding (Other/Lower Priority):",
        "fm_exercise_therapy_strong_recommendation": "Fibromyalgia -- Aerobic and Aquatic Exercise Therapy, Real EULAR 2017 'Strong For' Recommendation (the Only Treatment, Drug or Non-Drug, to Receive One):",
        "fm_cognitive_behavioural_therapy_medicines": "Fibromyalgia -- Cognitive Behavioural Therapy (CBT), Real EULAR Stage-2 Psychological Therapy:",
        "fm_fda_approved_snri_medicines": "Fibromyalgia -- Duloxetine and Milnacipran, Real FDA-Approved Serotonin-Noradrenaline Reuptake Inhibitors:",
        "fm_fda_approved_alpha2delta_ligand_medicines": "Fibromyalgia -- Pregabalin, Real First FDA-Approved Fibromyalgia Drug (2007), Alpha-2-Delta Ligand:",
        "fm_other_adjunct_medicines_weaker_evidence": "Fibromyalgia -- Amitriptyline and Other Older Off-Label Agents, Real Honest Weaker/Publication-Bias-Flagged Evidence (Other/Lower Priority):",
        "ppd_neurosteroid_gabaa_modulators_brexanolone_zuranolone": "Postpartum Depression -- Brexanolone IV Infusion / Zuranolone Oral, Real Neurosteroid GABA-A Modulators Approved Specifically for PPD:",
        "ppd_ssri_first_line_pharmacotherapy": "Postpartum Depression -- Sertraline, Real First-Line SSRI Preferred in Breastfeeding:",
        "ppd_psychotherapy_cbt_ipt": "Postpartum Depression -- Cognitive Behavioral Therapy / Interpersonal Psychotherapy, Real Non-Drug Option:",
        "nph_diagnostic_prognostic_testing": "Normal Pressure Hydrocephalus -- CSF Tap Test / External Lumbar Drainage / Rout Infusion Testing, Real Diagnostic AND Prognostic Tests Before Shunt Surgery:",
        "nph_shunt_surgery": "Normal Pressure Hydrocephalus -- Ventriculoperitoneal (VP) and Lumboperitoneal (LP) Shunt With Programmable Valve, Real Closest-to-Cure Procedures:",
        "nph_no_effective_drug_therapy": "Normal Pressure Hydrocephalus -- No Proven-Effective Drug Therapy, Real Honest Negative Finding:",
        "rls_iron_repletion_medicines": "Restless Legs Syndrome -- Iron Repletion (Oral/IV) for Ferritin-Low RLS, Real Closest-to-Cure Track:",
        "rls_alpha2delta_ligands_first_line_medicines": "Restless Legs Syndrome -- Alpha-2-Delta Ligands (Gabapentin Enacarbil/Gabapentin/Pregabalin), Real Current First-Line Per 2024 AASM Guideline:",
        "rls_dopamine_agonists_augmentation_risk_medicines": "Restless Legs Syndrome -- Dopamine Agonists (Pramipexole/Ropinirole/Rotigotine), Real Short-Term Efficacy With Real Quantified Augmentation Risk, No Longer First-Line:",
        "rls_refractory_opioid_medicines": "Restless Legs Syndrome -- Prolonged-Release Oxycodone-Naloxone, Real Third-Line Option for Refractory/Augmented RLS:",
        "rls_avoid_or_caution_medicines": "Restless Legs Syndrome -- Levodopa and Benzodiazepines, Real Avoid-or-Caution Options Per Current Guideline:",
        "fn_empiric_broad_spectrum_iv_antibiotics_medicines": "Febrile Neutropenia (Chemotherapy-Induced) -- Immediate Empiric Broad-Spectrum IV Antibiotics (Piperacillin-Tazobactam/Cefepime/Meropenem), Real First-Hour Oncologic-Emergency Standard of Care:",
        "fn_mascc_low_risk_oral_outpatient_medicines": "Febrile Neutropenia (Chemotherapy-Induced) -- MASCC-Score-Guided Oral/Outpatient Antibiotic Therapy for Real Low-Risk Patients:",
        "fn_gcsf_primary_prophylaxis_medicines": "Febrile Neutropenia (Chemotherapy-Induced) -- Primary Prophylactic G-CSF (Filgrastim/Pegfilgrastim/Lenograstim) in High-Risk Chemotherapy Regimens, Real Prevention Before It Occurs:",
        "fn_gcsf_therapeutic_medicines": "Febrile Neutropenia (Chemotherapy-Induced) -- Therapeutic G-CSF Added to Antibiotics Once Febrile Neutropenia Has Occurred, Real Recovery-Speed Benefit With Honestly Reported Mixed Mortality Evidence:",
        "fn_antifungal_antiviral_escalation_medicines_other": "Febrile Neutropenia (Chemotherapy-Induced) -- Empirical/Pre-Emptive Antifungal Escalation for Persistent Fever Despite Antibiotics, Lower-Priority Other:",
        "hypopara_conventional_oral_calcium_calcitriol_medicines": "Hypoparathyroidism -- Oral Calcium + Active Vitamin D (Calcitriol), Real First-Line Conventional Therapy (Genuinely Good but Incomplete Biochemical Control):",
        "hypopara_recombinant_pth_replacement_medicines": "Hypoparathyroidism -- Recombinant/Engineered PTH Replacement (Palopegteriparatide/Yorvipath, Real Currently Approved; rhPTH[1-84]/Natpara, Real Discontinued), Real Newer Physiologic Hormone Replacement:",
        "hypopara_teriparatide_pth134_offlabel_medicines": "Hypoparathyroidism -- Teriparatide/PTH(1-34), Real Off-Label Use (FDA-Approved Indication Is Osteoporosis), Real Pump Delivery Superior to Twice-Daily Injection:",
        "hypopara_magnesium_repletion_medicines": "Hypoparathyroidism -- Magnesium Repletion for Hypomagnesemia-Induced Functional Hypoparathyroidism, Real Root-Cause-Reversing Therapy in This Specific Subset:",
        "hypopara_thiazide_diuretic_adjunct_medicines": "Hypoparathyroidism -- Thiazide Diuretics as Adjunct to Reduce Hypercalciuria on Conventional Therapy (Other/Lower Priority):",
        "hypopara_acute_iv_calcium_emergency_medicines": "Hypoparathyroidism -- IV Calcium Gluconate for Acute Severe Symptomatic Hypocalcemia/Tetany, Real Emergency Management (Not Chronic-Disease Cure):",
        "scid_hsct_matched_sibling_and_alternative_donor": "Severe Combined Immunodeficiency -- Allogeneic Hematopoietic Stem Cell Transplant (Matched Sibling or Alternative Donor), Real Definitive Cure Across All SCID Genotypes:",
        "scid_ada_gene_therapy": "Severe Combined Immunodeficiency -- Autologous Gene Therapy for ADA-SCID (Strimvelis / Lentiviral), Real Curative Alternative to Allogeneic Transplant:",
        "scid_x1_gene_therapy": "Severe Combined Immunodeficiency -- Autologous Lentiviral Gene Therapy with Low-Dose Busulfan for SCID-X1, Real Curative Option Restoring Full Lymphocyte Lineages:",
        "scid_ada_enzyme_replacement_bridge_therapy": "Severe Combined Immunodeficiency -- PEG-ADA (Pegademase) Enzyme Replacement, Real Bridge Therapy Before HSCT/Gene Therapy (Not Curative Alone):",
        "scid_supportive_and_infection_prophylaxis_medicines": "Severe Combined Immunodeficiency -- Immunoglobulin Replacement, Antimicrobial Prophylaxis and Live-Vaccine Avoidance, Real Supportive Care Alongside Definitive Therapy:",
        "cvid_ivig_replacement": "Common Variable Immunodeficiency -- Intravenous Immunoglobulin (IVIG) Replacement, Real First-Line Near-Normalizing Treatment (Busse 2002 JACI; Lucas 2010 JACI):",
        "cvid_scig_replacement": "Common Variable Immunodeficiency -- Subcutaneous Immunoglobulin (SCIG) Replacement, Real Equally-Effective Alternative Route (Gardulf 1995 Lancet; Gouilleux-Gruart 2013 Clin Exp Immunol):",
        "cvid_prophylactic_antibiotics": "Common Variable Immunodeficiency -- Prophylactic Antibiotics for Breakthrough Infections Despite Adequate Ig Replacement, Real Guideline-Recommended Adjunct (AAAAI/ACAAI Practice Parameter, Bonilla 2015; Quinti 2011 J Clin Immunol):",
        "cvid_immunosuppressants_autoimmune": "Common Variable Immunodeficiency -- Immunosuppressants for Autoimmune Complications (ITP/AIHA/Evans Syndrome), Real Adjunct Treatment (Wang & Cunningham-Rundles 2005 J Autoimmun):",
        "cvid_glild_monitoring_management": "Common Variable Immunodeficiency -- Monitoring and Management of Granulomatous-Lymphocytic Interstitial Lung Disease (GLILD), Real but Still Unproven-Optimal Treatment Area (Lamers 2021 Front Immunol; van de Ven 2020 Front Immunol):",
        "fvl_acute_vte_treatment_doacs_medicines": "Factor V Leiden Thrombophilia -- Acute-Phase Oral Anticoagulants (DOACs: Apixaban, Rivaroxaban, Dabigatran, Edoxaban) for a VTE Event in a Carrier, Real Evidence From General VTE Trials That Did Not Exclude FVL Carriers:",
        "fvl_lmwh_warfarin_bridging_medicines": "Factor V Leiden Thrombophilia -- Traditional LMWH-to-Warfarin (VKA) Bridging, Real Decades-Long Prior Standard of Care:",
        "fvl_extended_secondary_prevention_medicines": "Factor V Leiden Thrombophilia -- Extended/Indefinite Secondary Prevention After a First Unprovoked VTE (Reduced-Dose Rivaroxaban vs Aspirin):",
        "fvl_periprocedural_surgical_lmwh_prophylaxis_medicines": "Factor V Leiden Thrombophilia -- Periprocedural/Surgical Prophylactic LMWH (Enoxaparin/Dalteparin) in a Known Carrier:",
        "fvl_peripartum_lmwh_prophylaxis_medicines": "Factor V Leiden Thrombophilia -- Peripartum (Antenatal + Postnatal) Prophylactic LMWH, Real Risk-Stratified by Genotype/Personal History, Including the Real Neutral TIPPS Trial:",
        "fvl_estrogen_avoidance_counseling_other": "Factor V Leiden Thrombophilia -- Avoidance of Estrogen-Containing Contraception/HRT, Real Counselling (Other/Non-Pharmacological):",
        "aps_warfarin_secondary_thromboprophylaxis_medicines": "Antiphospholipid Syndrome -- Warfarin, Lifelong Secondary Thromboprophylaxis After Thrombotic APS (Crowther 2003, EULAR 2019):",
        "aps_lmwh_medicines": "Antiphospholipid Syndrome -- Low-Molecular-Weight Heparin, Obstetric APS Combination Therapy and Escalation for Recurrent Complications:",
        "aps_low_dose_aspirin_medicines": "Antiphospholipid Syndrome -- Low-Dose Aspirin, Primary Prevention and Obstetric APS (Real Comparator-Arm Data Included):",
        "aps_hydroxychloroquine_adjunct_medicines": "Antiphospholipid Syndrome -- Hydroxychloroquine as an Adjunct to Anticoagulation, Thrombotic Primary APS (de Carvalho 2026 Meta-Analysis):",
        "aps_doac_medicines": "Antiphospholipid Syndrome -- Direct Oral Anticoagulants (Rivaroxaban), Real Trial-Proven Inferiority in Triple-Positive APS (TRAPS Trial, Pengo 2018):",
        "aps_catastrophic_aps_acute_management_medicines": "Antiphospholipid Syndrome -- Catastrophic APS (CAPS) Acute Management: Anticoagulation + Corticosteroids + Plasma Exchange/IVIG (CAPS Registry, Cervera 2009):",
        "tth_acute_ketoprofen": "Tension-Type Headache -- Ketoprofen 25mg, Real Strongest Single-Dose NSAID Evidence for Acute Episodic Relief (Cochrane 2016):",
        "tth_acute_ibuprofen": "Tension-Type Headache -- Ibuprofen 400mg, Real Best-Studied First-Line Acute Analgesic (Cochrane 2015):",
        "tth_acute_aspirin": "Tension-Type Headache -- Aspirin 500-1000mg, Real First-Line Acute Option (Cochrane 2017):",
        "tth_acute_paracetamol": "Tension-Type Headache -- Paracetamol (Acetaminophen) 1000mg, Real but Modest Acute Effect (Cochrane 2016):",
        "tth_prophylaxis_amitriptyline": "Tension-Type Headache -- Amitriptyline 10-75mg Nightly, Real First-Line Prophylaxis for Chronic/Frequent-Episodic TTH:",
        "tth_nondrug_acupuncture": "Tension-Type Headache -- Acupuncture, Real Guideline-Recognised Non-Drug Prophylaxis (Cochrane 2016):",
        "tth_nondrug_biofeedback": "Tension-Type Headache -- EMG Biofeedback (+/- Relaxation), Real Medium-to-Large Effect for Chronic TTH:",
        "tth_nondrug_manual_osteopathic_therapy": "Tension-Type Headache -- Osteopathic Manipulative Therapy, Real Signal in a Small Pilot, Needs Replication:",
        "dlb_cholinesterase_rivastigmine": "Lewy Body Dementia -- Rivastigmine, Real First Placebo-Controlled RCT Evidence Specifically in DLB (McKeith 2000):",
        "dlb_cholinesterase_donepezil": "Lewy Body Dementia -- Donepezil, Real Dose-Dependent Cognitive/Global Benefit in a Dedicated DLB RCT (Mori 2012):",
        "dlb_cholinesterase_galantamine": "Lewy Body Dementia -- Galantamine, Real Open-Label Evidence Only, No Dedicated DLB Placebo-Controlled RCT:",
        "dlb_memantine": "Lewy Body Dementia -- Memantine, Real but Genuinely Mixed Evidence, Positive Only in the DLB Subgroup of the Larger Trial (Emre 2010):",
        "dlb_levodopa_parkinsonism": "Lewy Body Dementia -- Levodopa, Real but Reduced Motor Benefit Compared With Idiopathic Parkinson's Disease (Molloy 2005):",
        "dlb_melatonin_clonazepam_rbd": "Lewy Body Dementia -- Melatonin and/or Clonazepam, Real First-Line Options for REM Sleep Behaviour Disorder:",
        "dlb_pimavanserin_psychosis": "Lewy Body Dementia -- Pimavanserin, Real Trial Evidence and a Comparatively Favourable DLB Safety Profile for Psychosis (HARMONY):",
        "dlb_antipsychotic_avoidance_warning": "Lewy Body Dementia -- Typical and Most Atypical Antipsychotics, Real Safety Warning: Relatively Contraindicated (Severe Neuroleptic Sensitivity):",
        "an_family_based_treatment_maudsley": "Anorexia Nervosa -- Family-Based Treatment (FBT / Maudsley Approach), Real Closest-to-Cure Option for Adolescent AN (Lock 2010 RCT):",
        "an_cbte_enhanced_cbt": "Anorexia Nervosa -- Enhanced Cognitive Behavioural Therapy (CBT-E), Real Guideline Psychotherapy for Adult AN and FBT Alternative:",
        "an_nutritional_rehabilitation_refeeding": "Anorexia Nervosa -- Higher-Calorie Inpatient Nutritional Rehabilitation (Refeeding), Real Foundational Precondition for Psychotherapy:",
        "an_pharmacotherapy_olanzapine": "Anorexia Nervosa -- Olanzapine, Real Adjunctive Weight-Gain Pharmacotherapy (No Drug Is Approved Specifically for AN):",
        "an_pharmacotherapy_other_limited_evidence": "Anorexia Nervosa -- Fluoxetine and Other Medicines, Real Honest Negative/Limited Evidence for Relapse Prevention:",
        "bpd_dialectical_behavior_therapy": "Borderline Personality Disorder -- Dialectical Behavior Therapy (DBT), Real Best-Evidenced Structured Psychotherapy (Linehan RCTs):",
        "bpd_mentalization_based_therapy": "Borderline Personality Disorder -- Mentalization-Based Treatment (MBT), Real Long-Term Controlled Follow-Up Evidence (Bateman & Fonagy):",
        "bpd_transference_focused_psychotherapy": "Borderline Personality Disorder -- Transference-Focused Psychotherapy (TFP), Real RCT Evidence for Anger/Impulsivity (Clarkin 2007):",
        "bpd_symptom_targeted_pharmacotherapy": "Borderline Personality Disorder -- Symptom-Targeted Pharmacotherapy, Real Honest Note: No FDA-Approved Medication for BPD Itself:",
        "aspd_early_childhood_conduct_disorder_prevention_programs": "Antisocial Personality Disorder -- Early Childhood Conduct-Disorder Prevention (Fast Track, MST/FFT), Real Upstream Evidence -- NOT a Treatment for Adult ASPD:",
        "aspd_mood_stabilizers_antipsychotics_impulsive_aggression_symptom_targeted": "Antisocial Personality Disorder -- Symptom-Targeted Pharmacotherapy for Impulsive Aggression (Phenytoin, Fluoxetine), Real Honest Note: No Drug Treats ASPD Itself:",
        "aspd_adult_group_individual_psychotherapy_mixed_weak_evidence": "Antisocial Personality Disorder -- Adult Group/Individual Psychotherapy (CBT, DBT, Schema Therapy, Contingency Management), Real Honest Note: Very Limited Evidence (Cochrane 2020):",
        "aspd_substance_use_disorder_co_treatment": "Antisocial Personality Disorder -- Contingency Management for Comorbid Substance Use Disorder, Real Single-Trial Evidence:",
        "medicines": None,
        "ss_autologous_hsct_severe_diffuse_cutaneous": "Systemic Sclerosis -- Autologous Hematopoietic Stem-Cell Transplantation for Severe Early Diffuse Cutaneous Disease, Real Long-Term Survival Benefit (SCOT Trial, Sullivan 2018 NEJM; ASTIS Trial, van Laar 2014 JAMA):",
        "ss_ace_inhibitors_renal_crisis": "Systemic Sclerosis -- ACE Inhibitors for Scleroderma Renal Crisis, Real Life-Saving Emergency Treatment (Steen 1990 Ann Intern Med):",
        "ss_mycophenolate_cyclophosphamide_skin_lung_fibrosis": "Systemic Sclerosis -- Cyclophosphamide and Mycophenolate Mofetil for Skin/Lung Fibrosis, Real Modest Disease-Modifying Effect (Scleroderma Lung Study I, Tashkin 2006 NEJM; Scleroderma Lung Study II, Tashkin 2016 Lancet Respir Med):",
        "ss_nintedanib_ssc_ild": "Systemic Sclerosis -- Nintedanib for SSc-Associated Interstitial Lung Disease, Real Antifibrotic Slowing of FVC Decline (SENSCIS Trial, Distler 2019 NEJM):",
        "ss_calcium_channel_blockers_raynauds": "Systemic Sclerosis -- Calcium Channel Blockers for Raynaud's Phenomenon, Real Moderate Vasodilator Benefit (Thompson & Pope 2001 Arthritis Rheum Meta-Analysis):",
        "ss_endothelin_pde5_pulmonary_hypertension": "Systemic Sclerosis -- Endothelin Receptor Antagonists and PDE5 Inhibitors for Digital Ulcers and Pulmonary Arterial Hypertension, Real Vasodilator/Antiproliferative Benefit (RAPIDS-2 Trial, Matucci-Cerinic 2011 Ann Rheum Dis; SUPER-1 Trial, Galie 2005 NEJM):",
        "agn_loop_diuretic_furosemide": "Acute Glomerulonephritis -- Furosemide (Loop Diuretic) for Volume Overload, Edema, and Hypertension (Valencia-Espinoza 1990, Akeberegn 2025):",
        "agn_antihypertensive_calcium_channel_blocker": "Acute Glomerulonephritis -- Nifedipine (Calcium Channel Blocker) as Antihypertensive Adjunct (Valencia-Espinoza 1990, Akeberegn 2025):",
        "agn_supportive_care_bundle_sodium_fluid_restriction": "Acute Glomerulonephritis -- Sodium and Fluid Restriction as Part of the Standard Supportive-Care Bundle (Dhakal 2025):",
        "agn_antibiotics_gas_eradication": "Acute Glomerulonephritis -- Penicillin/Amoxicillin for Eradication of Active Group A Streptococcal Infection, Real IDSA 2012 First-Line (Shulman 2012, Pichichero 2008):",
        "agn_corticosteroid_pulse_crescentic_rpgn": "Acute Glomerulonephritis -- Pulse Corticosteroids (Methylprednisolone) for Crescentic/Rapidly Progressive Post-Streptococcal GN (Jellouli 2015):",
        "agn_cyclophosphamide_crescentic_rpgn": "Acute Glomerulonephritis -- Cyclophosphamide Added to Corticosteroids for More Severe Crescentic/RPGN Cases (Jellouli 2015):",
        "agn_temporary_dialysis_acute_kidney_injury_support": "Acute Glomerulonephritis -- Temporary (Acute) Hemodialysis for Severe Acute Kidney Injury / Crescentic Disease (Sarkissian 1997, Wong 2009, Jellouli 2015):",
        "scol_observation": "Scoliosis -- Observation (Periodic Clinical + Radiographic Follow-up), Real Standard Practice for Mild Curves:",
        "scol_bracing": "Scoliosis -- Orthotic Bracing (Boston/TLSO or Providence Night-Time Brace), Real BrAIST-Proven Best-Evidenced Non-Surgical Option for Moderate Curves:",
        "scol_exercise_schroth_psse": "Scoliosis -- Scoliosis-Specific Exercise / Schroth Method (PSSE), Real Add-On Evidence for Cobb Angle and Quality of Life:",
        "scol_surgery": "Scoliosis -- Posterior Spinal Fusion With Segmental Pedicle Screw Instrumentation, Real Definitive Option for Severe/Progressive Curves:",
        "scol_analgesia_honest_note": "Scoliosis -- Analgesics for Incidental Back Pain, Real Honest Note: NOT a Scoliosis Treatment:",
        "sp_one_session_in_vivo_exposure_therapy": "Specific Phobia -- One-Session In Vivo Exposure Treatment (Ost's OST Protocol), Real First-Line Closest-to-Cure Treatment:",
        "sp_multi_session_graduated_exposure_therapy": "Specific Phobia -- Multi-Session Graduated In Vivo Exposure Therapy (Standard CBT Protocol):",
        "sp_virtual_reality_exposure_therapy": "Specific Phobia -- Virtual Reality Exposure Therapy (VRET), Real Evidence-Equivalent Alternative to In Vivo Exposure:",
        "sp_applied_tension_technique_bii_phobia": "Specific Phobia -- Applied Tension Technique for Blood-Injection-Injury (BII) Phobia, Real Subtype-Specific First-Line Treatment:",
        "sp_d_cycloserine_augmentation_of_exposure": "Specific Phobia -- D-Cycloserine Augmentation of Exposure Therapy, Real Adjunct (Not a Standalone Medicine):",
        "sp_ssri_pharmacotherapy_limited_role": "Specific Phobia -- SSRIs (e.g. Paroxetine), Real but Very Limited Evidence, Not First-Line, Not a Substitute for Exposure Therapy:",
        "sp_benzodiazepine_caution_undermines_exposure": "Specific Phobia -- Benzodiazepines, Real Evidence They Can Undermine Exposure Therapy, Caution Advised:",
        "ptsd_prolonged_exposure_therapy": "Post-Traumatic Stress Disorder -- Prolonged Exposure (PE) Therapy, Real First-Line Trauma-Focused Psychotherapy (Foa 1999, Watts 2013 Meta-Analysis):",
        "ptsd_cognitive_processing_therapy": "Post-Traumatic Stress Disorder -- Cognitive Processing Therapy (CPT), Real First-Line Trauma-Focused Psychotherapy (Resick 2002, Watts 2013 Meta-Analysis):",
        "ptsd_emdr": "Post-Traumatic Stress Disorder -- Eye Movement Desensitization and Reprocessing (EMDR), Real First-Line Trauma-Focused Psychotherapy (Chen 2014 Meta-Analysis, Watts 2013 Meta-Analysis):",
        "ptsd_ssri_sertraline": "Post-Traumatic Stress Disorder -- Sertraline (SSRI), Real FDA-Approved First-Line Pharmacotherapy (Brady 2000 JAMA RCT):",
        "ptsd_ssri_paroxetine": "Post-Traumatic Stress Disorder -- Paroxetine (SSRI), Real FDA-Approved First-Line Pharmacotherapy (Tucker 2001, Marshall 2001 RCTs):",
        "ptsd_mdma_assisted_therapy_investigational": "Post-Traumatic Stress Disorder -- MDMA-Assisted Therapy, Real Phase 3 Trial Results but Investigational and NOT FDA-Approved (Mitchell 2021/2023 Nature Medicine, FDA Complete Response Letter 2024):",
        "ptsd_prazosin_nightmares": "Post-Traumatic Stress Disorder -- Prazosin for Nightmares, Real Mixed Evidence, Not Guideline First-Line (Raskind 2000 Case Series, Raskind 2018 NEJM Negative Trial):",
        "did_phase_oriented_trauma_therapy": "Dissociative Identity Disorder -- Phase-Oriented Trauma Therapy (ISSTD Three-Phase Model: Stabilization, Trauma Processing, Integration), Real Guideline-Recommended First-Line Approach (ISSTD Guidelines 2011, TOP DD Naturalistic Study Brand 2013/2019, Myrick 2013/2017):",
        "did_emdr_adapted": "Dissociative Identity Disorder -- EMDR Adapted for DID (Phase 2 Trauma Processing), Real Guideline-Referenced Technique but No DID-Specific RCT (ISSTD Guidelines 2011):",
        "did_medication_comorbid_symptoms": "Dissociative Identity Disorder -- Pharmacotherapy for Comorbid Depression/Anxiety/PTSD Symptoms, Real Adjunct Only, No FDA-Approved Medication for DID Itself (Gentile 2013 Clinical Review):",
        "did_hospitalization_crisis_stabilization": "Dissociative Identity Disorder -- Hospitalization / Crisis Stabilization for Severe Cases, Real Safety-Net Adjunct (Myrick 2017 TOP DD Cost Study, ISSTD Guidelines 2011):",
        "ssd_cognitive_behavioral_therapy": "Somatic Symptom Disorder -- Cognitive Behavioral Therapy Adapted for SSD (CBT-SSD), Real First-Line Best-Evidence Treatment (Maas Genannt Bermpohl 2025 Network Meta-Analysis, Kroenke 2007 Review):",
        "ssd_collaborative_care_consultation_liaison_model": "Somatic Symptom Disorder -- Collaborative Care / Consultation-Liaison Model, Real Effective Health-Systems Approach (Smith 1986 NEJM Trial, van der Feltz-Cornelis 2006 Trial):",
        "ssd_ssri_snri_comorbid_depression_anxiety": "Somatic Symptom Disorder -- SSRIs/SNRIs, Real Adjunct for Comorbid Depression/Anxiety, Not a Standalone Cure (Kroenke 2007 Review):",
        "ssd_mindfulness_based_interventions": "Somatic Symptom Disorder -- Mindfulness- and Acceptance-Based Treatment (AMBT), Real Evidence-Equivalent Alternative (Maas Genannt Bermpohl 2025 Network Meta-Analysis):",
        "ssd_regular_scheduled_physician_visits": "Somatic Symptom Disorder -- Regular Scheduled Physician Visits, Real Practice-Level Technique to Reduce Unnecessary Testing (Smith 1986 NEJM Trial):",
        "io_water_soluble_contrast_challenge": "Intestinal Obstruction -- Water-Soluble Contrast (Gastrografin) Challenge, Real Diagnostic + Mildly Therapeutic Role (Ann Surg 2022 Meta-Analysis, Br J Surg 2010):",
        "io_octreotide_corticosteroids_malignant_obstruction": "Intestinal Obstruction -- Octreotide vs Hyoscine Butylbromide and Corticosteroids for Inoperable Malignant Bowel Obstruction, Real Symptom Control (Non-Curative):",
        "io_colonic_stenting_bridge_to_surgery": "Intestinal Obstruction -- Self-Expanding Metal Stent (SEMS) Bridge-to-Surgery for Malignant Colorectal Obstruction, Real Stoma-Reduction Evidence:",
        "io_endoscopic_detorsion_volvulus": "Intestinal Obstruction -- Endoscopic Detorsion for Sigmoid/Colonic Volvulus, Real Bridge-to-Surgery (High Recurrence Without Resection):",
        "io_surgical_relief_adhesiolysis_resection": "Intestinal Obstruction -- Surgical Adhesiolysis/Resection for Complete, Strangulated, or Failed-Conservative Obstruction, Real Definitive Mechanical Relief:",
        "cll_ibrutinib_first_generation_btki": "Chronic Lymphocytic Leukemia -- Ibrutinib, Real First-in-Class Bruton Tyrosine Kinase (BTK) Inhibitor (RESONATE-2 First-Line):",
        "cll_next_generation_btki_acalabrutinib_zanubrutinib": "Chronic Lymphocytic Leukemia -- Next-Generation BTK Inhibitors (Acalabrutinib, Zanubrutinib), Real Comparable-to-Superior Efficacy With Fewer Cardiovascular Effects Than Ibrutinib:",
        "cll_venetoclax_obinutuzumab_fixed_duration": "Chronic Lymphocytic Leukemia -- Fixed-Duration Venetoclax Plus Obinutuzumab (CLL14), Real Flagship Functional-Cure Regimen via Deep Undetectable-MRD Remission and Treatment Discontinuation:",
        "cll_venetoclax_rituximab_relapsed_refractory": "Chronic Lymphocytic Leukemia -- Venetoclax Plus Rituximab (MURANO), Real Fixed-Duration Regimen for Relapsed/Refractory Disease Including High-Risk del(17p):",
        "cll_fcr_chemoimmunotherapy_ighv_mutated": "Chronic Lymphocytic Leukemia -- FCR Chemoimmunotherapy, Real Historical Standard With a Genuinely Durable Long-Term Remission Subset in IGHV-Mutated Disease:",
        "cll_allogeneic_stem_cell_transplant_high_risk": "Chronic Lymphocytic Leukemia -- Allogeneic Stem Cell Transplant, Real Lower-Priority Option for TP53-Mutated/High-Risk Disease Refractory to BTK Inhibitors and Venetoclax:",
        "thal_exa_cel_casgevy_medicines": "Beta Thalassemia Major -- Exagamglogene Autotemcel (Casgevy), Real CRISPR-Cas9 Gene-Edited Autologous Cell Therapy, Real Donor-Independent Landmark Gene Therapy:",
        "thal_beti_cel_zynteglo_medicines": "Beta Thalassemia Major -- Betibeglogene Autotemcel (Zynteglo), Real Lentiviral-Vector Gene Addition Therapy, Real Donor-Independent Landmark Gene Therapy:",
        "thal_allogeneic_hsct_procedure": "Beta Thalassemia Major -- Allogeneic Hematopoietic Stem Cell Transplant, Real Long-Established Curative Option (Lucarelli-Risk-Class Stratified):",
        "thal_regular_transfusion_therapy_medicines": "Beta Thalassemia Major -- Regular Blood Transfusion Therapy, Real Lifelong Standard of Care (Not Curative):",
        "thal_iron_chelation_medicines": "Beta Thalassemia Major -- Iron Chelation Therapy (Deferoxamine/Deferasirox/Deferiprone), Real Critical Adjunct to Transfusion Therapy:",
        "thal_luspatercept_medicines": "Beta Thalassemia Major -- Luspatercept, Real Erythroid-Maturation Agent for Transfusion-Burden Reduction (Non-Curative):",
        "hemoa_prophylactic_factor_viii_medicines": "Haemophilia A -- Prophylactic Factor VIII Replacement, Real First-Line Disease-Course-Altering Standard of Care:",
        "hemoa_emicizumab_medicines": "Haemophilia A -- Emicizumab, Real Non-Factor Bispecific-Antibody Prophylaxis (Effective Regardless of Inhibitor Status):",
        "hemoa_gene_therapy_medicines": "Haemophilia A -- Valoctocogene Roxaparvovec (Roctavian) Gene Therapy, Real Single-Infusion Potential Functional-Cure Candidate:",
        "hemoa_on_demand_factor_viii_medicines": "Haemophilia A -- On-Demand (Episodic) Factor VIII Replacement for Acute Bleeding Episodes:",
        "hemoa_inhibitor_bypassing_agents_medicines": "Haemophilia A -- Bypassing Agents for Acute Bleeding in Patients With Factor VIII Inhibitors:",
        "hemoa_immune_tolerance_induction_procedure": "Haemophilia A -- Immune Tolerance Induction, Real Protocol to Eradicate Factor VIII Inhibitors:",
        "vwd_ddavp_medicines": "Von Willebrand Disease -- Desmopressin (DDAVP), Real First-Line Functional Normalization for Type 1/DDAVP-Responsive Type 2 vWD (Castaman MCMDM-1VWD 2008, Mannucci 2001):",
        "vwd_plasma_derived_vwf_concentrate_medicines": "Von Willebrand Disease -- Plasma-Derived VWF/Factor VIII Concentrate, Real Replacement Therapy for Type 2/3 vWD and DDAVP Non-Responders (Windyga 2011):",
        "vwd_recombinant_vwf_concentrate_medicines": "Von Willebrand Disease -- Recombinant VWF Concentrate (Vonicog Alfa), Real Newer Alternative With Phase 3 Prophylaxis Data (Leebeek 2022):",
        "vwd_antifibrinolytic_medicines": "Von Willebrand Disease -- Antifibrinolytics (Tranexamic Acid, Aminocaproic Acid), Real Adjunct/Monotherapy for Mucosal and Menstrual Bleeding (Lukes 2010):",
        "vwd_hormonal_therapy_menorrhagia_medicines": "Von Willebrand Disease -- Hormonal Therapy for Menorrhagia (Combined OCPs, Levonorgestrel IUD), Real Guideline-Recommended Option (Milsom 1991, ASH/ISTH/NHF/WFH 2021):",
        "acro_transsphenoidal_surgery_procedure": "Acromegaly -- Transsphenoidal Surgery, Real First-Line and Only Potentially Curative Procedure (Remission Real Stratified by Tumor Size/Invasion):",
        "acro_preoperative_ssa_procedure_adjunct": "Acromegaly -- Preoperative Somatostatin Analog Priming Before Surgery, Real Short-Term Surgical-Outcome Adjunct:",
        "acro_first_gen_ssa_medicines": "Acromegaly -- First-Generation Somatostatin Receptor Ligands (Octreotide LAR / Lanreotide Autogel), Real First-Line Injectable Medical Therapy:",
        "acro_pasireotide_medicines": "Acromegaly -- Pasireotide LAR, Real Second-Generation Somatostatin Analog, Real Superior First-Line and Second-Line Efficacy:",
        "acro_pegvisomant_medicines": "Acromegaly -- Pegvisomant, Real GH-Receptor Antagonist With the Real Highest Single-Agent IGF-1 Normalization Rate:",
        "acro_cabergoline_medicines": "Acromegaly -- Cabergoline, Real Dopamine Agonist, Real Modest Monotherapy but Real Meaningful SRL-Adjunct Efficacy:",
        "acro_combination_ssa_pegvisomant_medicines": "Acromegaly -- Combination Somatostatin Receptor Ligand Plus Pegvisomant, Real High-Efficacy Regimen for SRL-Uncontrolled Disease:",
        "acro_stereotactic_radiosurgery_radiotherapy_procedure": "Acromegaly -- Stereotactic Radiosurgery/Radiotherapy, Real Lower-Priority Option for Refractory Disease (Real Slow Onset Over Years):",
        "acro_emerging_oral_srl_medicines_other": "Acromegaly -- Paltusotine, Real Emerging Once-Daily Oral Somatostatin Receptor 2 Agonist (Other/Newer Agent):",
        "hemochrom_phlebotomy_induction_procedure": "Hereditary Haemochromatosis -- Therapeutic Phlebotomy, Induction Phase (Real First-Line Curative-Intent Iron Depletion):",
        "hemochrom_phlebotomy_maintenance_procedure": "Hereditary Haemochromatosis -- Therapeutic Phlebotomy, Lifelong Maintenance Phase:",
        "hemochrom_iron_chelation_medicines": "Hereditary Haemochromatosis -- Iron Chelation Therapy (Deferasirox/Deferoxamine), Real Alternative When Phlebotomy Is Not Feasible:",
        "hemochrom_dietary_modification_other": "Hereditary Haemochromatosis -- Dietary Modification (Iron/Vitamin C Avoidance, Raw Shellfish/Vibrio vulnificus Risk), Real Adjunctive Measure (Other):",
        "volv_sigmoid_endoscopic_decompression_procedure": "Volvulus -- Sigmoid: Flexible Endoscopic Detorsion/Decompression, Real First-Line Bridging Procedure (Not a Cure Alone):",
        "volv_sigmoid_elective_resection_procedure": "Volvulus -- Sigmoid: Elective Resection with Primary Anastomosis After Successful Decompression, Real Definitive Recurrence-Preventing Surgery:",
        "volv_sigmoid_nonresective_alternatives_procedure": "Volvulus -- Sigmoid: Non-Resective Alternatives (Sigmoidopexy, Mesosigmoidoplasty, Percutaneous Endoscopic Sigmoidopexy) for Patients Unfit for Resection:",
        "volv_sigmoid_emergency_surgery_procedure": "Volvulus -- Sigmoid: Emergency Surgery for Ischemia/Perforation/Failed Decompression, Real Substantially Higher-Risk Surgery:",
        "volv_cecal_surgical_management_procedure": "Volvulus -- Cecal: Right Hemicolectomy, Detorsion/Cecopexy, and the Real Unreliable Endoscopic Route:",
        "volv_neonatal_midgut_ladd_procedure": "Volvulus -- Neonatal Midgut: Emergency Ladd's Procedure, Real Time-Critical Surgical Emergency:",
        "volv_perioperative_supportive_care_medicines": "Volvulus -- Real Perioperative Antibiotic Prophylaxis and Resuscitative Supportive Care (Adjunct, Not Curative of the Torsion):",
        "bprost_fluoroquinolone_regimens": "Bacterial Prostatitis -- Fluoroquinolones (Ciprofloxacin/Levofloxacin), Real Historically Preferred First-Line Class for Acute and Chronic Disease:",
        "bprost_tmp_smx_regimens": "Bacterial Prostatitis -- Trimethoprim-Sulfamethoxazole (TMP-SMX), Real Guideline-Listed Alternative:",
        "bprost_iv_to_oral_severe_acute_regimens": "Bacterial Prostatitis -- Initial IV Antibiotics for Severe/Septic Acute Disease, With Real Transition to Oral Once Clinically Stable:",
        "bprost_fosfomycin_alternative_regimens": "Bacterial Prostatitis -- Oral Fosfomycin, Real Second-Line Alternative for Acute and Chronic Disease:",
        "bprost_macrolide_atypical_pathogen_regimens": "Bacterial Prostatitis -- Azithromycin/Macrolides for Real Chlamydia-Associated Chronic Disease:",
        "bprost_beta_lactam_regimens_less_effective": "Bacterial Prostatitis -- Oral Beta-Lactams, Real Documented Lower Effectiveness (Poor Prostatic Penetration):",
        "bprost_prostatic_abscess_drainage_management_other": "Bacterial Prostatitis -- Prostatic Abscess Drainage + Antibiotics, Real Cases Not Responding to Antibiotics Alone (Other):",
        "nb_first_line_oral_antimuscarinics_medicines": "Neurogenic Bladder -- First-Line Oral Antimuscarinics (Propiverine/Oxybutynin/Tolterodine/Trospium/Solifenacin) for Neurogenic Detrusor Overactivity:",
        "nb_beta3_agonist_medicines": "Neurogenic Bladder -- Beta-3 Agonist (Mirabegron), Real Add-On or Antimuscarinic-Intolerant Option:",
        "nb_alpha1_blocker_adjunct_medicines": "Neurogenic Bladder -- Alpha-1 Blocker (Tamsulosin), Real Off-Label Adjunct for Bladder-Neck/Voiding Dysfunction:",
        "nb_intradetrusor_onabotulinumtoxina_injection_procedure": "Neurogenic Bladder -- Intradetrusor OnabotulinumtoxinA (BOTOX) Injection, Real Closest-to-Cure Option for Detrusor Overactivity After Oral Therapy Fails:",
        "nb_clean_intermittent_catheterization_procedure": "Neurogenic Bladder -- Clean Intermittent Catheterization (CIC), Real Gold-Standard Procedure for Detrusor Underactivity/Retention and Renal Protection:",
        "nb_sacral_neuromodulation_procedure": "Neurogenic Bladder -- Sacral Neuromodulation (Implanted Sacral Nerve Stimulator), Real Option for Refractory Retention/Overactivity:",
        "nb_augmentation_cystoplasty_procedure": "Neurogenic Bladder -- Augmentation Cystoplasty, Real Last-Resort Surgical Salvage After Medical Therapy Failure:",
        "emp_stage1_antibiotics_alone": "Empyema -- Antibiotics Alone, No Drainage (ACCP/Colice Stage 1, Uncomplicated Parapneumonic Effusion):",
        "emp_iv_antibiotics_plus_chest_tube_drainage": "Empyema -- IV Antibiotics + Chest Tube Drainage, Stage-Matched (ACCP/Colice Stage 2-4):",
        "emp_iterative_thoracentesis_alternative": "Empyema -- Iterative Therapeutic Thoracentesis, Chest-Tube-Sparing Alternative (Complicated Parapneumonic Effusion):",
        "emp_intrapleural_fibrinolytic_dnase": "Empyema -- Intrapleural tPA (Alteplase) + DNase (Dornase Alfa), MIST2 Regimen -- Real Medicine-Based Surgery-Avoidance for Organized/Loculated Disease:",
        "emp_vats_decortication": "Empyema -- VATS (Video-Assisted Thoracoscopic Surgery) Decortication, Failed Medical/Fibrinolytic Therapy or Organizing Empyema:",
        "emp_open_thoracotomy_decortication": "Empyema -- Open Thoracotomy + Decortication, Most Advanced/Chronic Organized Empyema:",
        "flu_vaccination_medicines": "Influenza -- Annual Vaccination (Real, Season-Dependent Effectiveness):",
        "flu_antiviral_treatment_medicines": "Influenza -- Antiviral Treatment Within the 48-Hour Window (Oseltamivir/Zanamivir/Peramivir):",
        "flu_baloxavir_medicines": "Influenza -- Baloxavir Marboxil, Single-Dose Alternative Antiviral:",
        "flu_post_exposure_prophylaxis_medicines": "Influenza -- Post-Exposure Antiviral Prophylaxis for High-Risk Household Contacts:",
        "flu_supportive_care_medicines": "Influenza -- Supportive Care for Uncomplicated Disease (Non-Curative):",
        "flu_secondary_bacterial_pneumonia_medicines": "Influenza -- Antibiotic Treatment for Secondary Bacterial Pneumonia (Complication, Not the Virus Itself):",
        "rab_wound_washing_first_aid": "Rabies -- Immediate Wound Washing/First Aid (Real Mandatory First Step, All Exposure Categories):",
        "rab_post_exposure_vaccine_medicines": "Rabies -- Post-Exposure Vaccine Series (Category II/III Core Component):",
        "rab_rabies_immunoglobulin_medicines": "Rabies -- Rabies Immunoglobulin (RIG), Category III Exposures:",
        "rab_monoclonal_antibody_rig_alternatives": "Rabies -- Monoclonal Antibody RIG Alternatives (Real Emerging Replacements):",
        "rab_pre_exposure_prophylaxis_medicines": "Rabies -- Pre-Exposure Prophylaxis (PrEP) for High-Risk Occupational Groups:",
        "rab_upstream_dog_vaccination_prevention": "Rabies -- Upstream Mass Dog Vaccination (Real Highest-Leverage Prevention Lever):",
        "rab_established_disease_treatment_attempts": "Rabies -- Established (Symptomatic) Disease Treatment Attempts (Milwaukee Protocol, Real Honestly Very Poor Success Rate):",
        "msl_vaccination_medicines": "Measles — MMR Pre-Exposure Vaccination (1-Dose vs 2-Dose Effectiveness, Herd-Immunity Threshold):",
        "msl_post_exposure_prophylaxis_medicines": "Measles — Post-Exposure Prophylaxis (MMR Vaccine Within 72h, or Immunoglobulin Within 6 Days):",
        "msl_vitamin_a_medicines": "Measles — Vitamin A Supplementation (Real WHO-Recommended, Cochrane-Reviewed Mortality Reduction):",
        "msl_supportive_care_medicines": "Measles — Supportive Care for Uncomplicated Disease (Non-Curative):",
        "msl_antiviral_investigational_medicines": "Measles — Investigational/Off-Label Antiviral (Ribavirin, Honestly Unproven):",
        "msl_complication_management_medicines": "Measles — Complication Management (Secondary Bacterial Pneumonia, Encephalitis Supportive Care):",
        "chkp_vaccination_medicines": "Chickenpox — Varicella Vaccination (1-Dose vs 2-Dose Effectiveness Against Any/Severe Disease):",
        "chkp_post_exposure_vaccination_medicines": "Chickenpox — Post-Exposure Vaccination (Within 3-5 Days of Exposure):",
        "chkp_vzig_medicines": "Chickenpox — Varicella-Zoster Immune Globulin (VariZIG), High-Risk Contacts Who Cannot Receive Live Vaccine:",
        "chkp_antiviral_treatment_medicines": "Chickenpox — Oral/IV Acyclovir & Valacyclovir for Established Disease (Honest Healthy-Child vs Higher-Risk-Group Split):",
        "chkp_supportive_care_medicines": "Chickenpox — Supportive Itch Care, Plus Aspirin/Ibuprofen Safety Warnings (Non-Curative):",
        "chkp_bacterial_superinfection_management_medicines": "Chickenpox — Bacterial Skin Superinfection Management (Complication, Not the Virus Itself):",
        "pert_dtap_primary_series_medicines": "Pertussis — DTaP Primary Pediatric Series (Real Documented Waning Over 5 Years):",
        "pert_tdap_booster_medicines": "Pertussis — Tdap Adolescent/Adult Booster (Real, Faster-Than-Tetanus/Diphtheria Waning):",
        "pert_maternal_tdap_pregnancy_medicines": "Pertussis — Maternal Tdap in Every Pregnancy (Real 'Cocooning' Strategy for Young Infants):",
        "pert_antibiotic_treatment_medicines": "Pertussis — Macrolide/TMP-SMX Antibiotic Treatment (Reduces Transmission, Honestly NOT a Cough Cure):",
        "pert_postexposure_prophylaxis_medicines": "Pertussis — Post-Exposure Antibiotic Prophylaxis for Close Contacts (Real 2023 Null-Effect Finding):",
        "pert_supportive_care_severe_infant_medicines": "Pertussis — Supportive Care for Severe Infant Disease (Non-Curative):",
        "dka_iv_fluid_resuscitation": "Diabetic Ketoacidosis -- IV Fluid Resuscitation, Real First and Most Urgent Step:",
        "dka_iv_insulin_infusion_regimens": "Diabetic Ketoacidosis -- IV Insulin Infusion Regimens, Real Cornerstone Antiketogenic Therapy:",
        "dka_potassium_repletion_protocol": "Diabetic Ketoacidosis -- Potassium Repletion Protocol, Real Critical Safety Step:",
        "dka_cerebral_edema_risk_mitigation": "Diabetic Ketoacidosis -- Cerebral Edema Risk Mitigation (Pediatric), Real Documented Safety Concern:",
        "dka_bicarbonate_controversial_role": "Diabetic Ketoacidosis -- Sodium Bicarbonate, Real Honestly Limited/Controversial Role:",
        "hfref_medicines": "HFrEF (reduced ejection fraction) — Four Pillars GDMT + add-ons:",
        "hfpef_medicines": "HFpEF (preserved ejection fraction) — genuinely different evidence:",
        "chf_mra_nonsteroidal_finerenone": "CHF — Non-Steroidal MRA (Finerenone, HFmrEF/HFpEF LVEF>=40%):",
        "chf_vericiguat": "CHF — Vericiguat (Soluble Guanylate Cyclase Stimulator):",
        "chf_omecamtiv_mecarbil": "CHF — Omecamtiv Mecarbil (Real, Honestly Marginal/Non-Approved Result):",
        "chf_gdmt_rapid_sequencing_strong_hf": "CHF — Rapid GDMT Up-Titration Strategy (STRONG-HF):",
        "chf_iv_iron_therapy": "CHF — IV Iron Repletion (Iron-Deficient HFrEF):",
        "chf_remote_hemodynamic_monitoring": "CHF — Remote Haemodynamic Monitoring Device (CardioMEMS):",
        "chf_prevention_pre_hf": "CHF — Real Primary Prevention, Before HF Ever Develops (Pre-HF/Stage A):",
        "chf_failed_or_unproven_treatments": "CHF — Failed, Neutral or Harm-Signal Treatments (Honest):",
        "chf_lifestyle_and_nonpharmacologic_measures": "CHF — Lifestyle/Non-Pharmacologic Measures (Real, Honestly Mixed Evidence):",
        "reversible_subtype_management": "Reversible-Cause Management — the real closest thing to a cure (subtype-dependent):",
        "acute_management": "Acute Management — ACLS-Driven Defibrillation, Bystander CPR/AED Programs:",
        "ablation_procedures": "Catheter Ablation — Idiopathic vs Scar-Related/Ischaemic VT:",
        "gdmt_medicines": "GDMT for the Non-Reversible Majority (same four-pillar framework as CHF/HFrEF):",
        "genotype_specific_management": "Genotype- / Syndrome-Specific Management (real guideline-directed exceptions to standard practice):",
        "antiarrhythmic_drugs": "Antiarrhythmic Drugs — VT Suppression / ICD-Shock Reduction:",
        "devices": "Device Therapy (ICD / CRT / LVAD / S-ICD / WCD / public-access AED, as applicable):",
        "supportive_care_medicines": "Supportive Care & Activity Restriction — Uncomplicated Lymphocytic/Viral Myocarditis:",
        "fulminant_mcs_devices": "Mechanical Circulatory Support — Fulminant Myocarditis (Devices):",
        "giant_cell_immunosuppression": "Combination Immunosuppression — Giant Cell Myocarditis:",
        "eosinophilic_management": "Corticosteroids + Underlying-Cause-Directed Therapy — Eosinophilic Myocarditis:",
        "ici_myocarditis_management": "Immune-Checkpoint-Inhibitor-Associated Myocarditis Management:",
        "antiviral_specific_therapy": "Antiviral-Specific Therapy (Biopsy-Confirmed Viral Genome):",
        "trial_evidence_non_gcm_immunosuppression": "Real Trial Evidence — Immunosuppression in Standard (Non-GCM, Non-ICI) Viral Myocarditis:",
        "revascularization_and_reperfusion": "Emergency Revascularization / Reperfusion — Cardiogenic Shock:",
        "vasopressors_inotropes": "Vasopressors / Inotropes — Cardiogenic Shock:",
        "mechanical_circulatory_support": "Mechanical Circulatory Support — IABP / Impella / VA-ECMO:",
        "hemodynamic_monitoring_devices": "Hemodynamic Monitoring Devices — Pulmonary Artery Catheter:",
        "shock_team_escalation_model": "Care-Delivery Model — Multidisciplinary Shock Team / Escalation Protocol:",
        "rv_infarction_specific_management": "RV-Infarction-Specific Management — Distinct Phenotype:",
        "lifestyle_modifications": "Lifestyle Modifications — Real Effect Sizes (mmHg), Not Just Qualitative Advice:",
        "first_line_drug_classes": "First-Line Drug Classes — Real Outcome-Trial Data:",
        "combination_therapy": "Combination Therapy — Which Pairing Works Best:",
        "bp_treatment_target_strategy": "BP Treatment Target Strategy — Intensive vs Standard:",
        "resistant_hypertension_management": "Resistant Hypertension Management — Best 4th-Line Add-On:",
        "device_renal_denervation": "Device Therapy — Renal Denervation (Full Trial History, Honest):",
        "hypertensive_emergency_iv_agents": "Hypertensive Emergency — Real IV Antihypertensive Agents:",
        "monitoring_devices": "Monitoring Devices — Home/Ambulatory BP Monitoring:",
        "acute_supportive_care_medicines": "Acute-Phase Supportive Care — Real Primary Management (Congestion, Hemodynamics):",
        "lvot_obstruction_specific_management": "LVOT-Obstruction-Positive Phenotype — Avoidance of Inotropes, Phenylephrine/Beta-Blockade:",
        "anticoagulation_lv_thrombus_prevention": "Anticoagulation — LV Thrombus Prevention/Treatment (Severe Apical Akinesis):",
        "secondary_prevention_medicines": "Secondary Prevention — Beta-Blockers & ACEi/ARB (Honestly Mixed Registry Evidence):",
        "complication_management": "Complication Management — QT/Torsades, Arrhythmia, Free-Wall Rupture:",
        "psychiatric_adjunct_care": "Psychiatric/Psychological Adjunct Care:",
        "telemetry_qt_monitoring_devices": "Devices — Telemetry / QT Monitoring During Acute Phase:",
        "smoking_cessation_and_lifestyle_medicines": "Smoking Cessation & Biomass-Smoke Avoidance — Real Disease-Modifying, Non-Drug Interventions (Most Impactful):",
        "inhaled_pharmacotherapy_medicines": "GOLD ABE-Group-Driven Inhaled Pharmacotherapy — Bronchodilators, ICS, Triple Therapy:",
        "oxygen_therapy_medicines": "Long-Term Oxygen Therapy (LTOT) — Real Proven Mortality Benefit in Hypoxaemic COPD:",
        "biologic_medicines": "Newer Biologic Therapy — Eosinophilic/Type-2-Inflammation Phenotype:",
        "pulmonary_rehabilitation_medicines": "Pulmonary Rehabilitation — Real, Evidence-Based, Underutilised:",
        "surgical_procedural_medicines": "Surgical / Bronchoscopic Lung Volume Reduction & Lung Transplantation:",
        "aatd_augmentation_medicines": "Alpha-1 Antitrypsin Augmentation Therapy — AATD-Specific COPD:",
        "acute_exacerbation_management_medicines": "Acute Exacerbation Management — Bronchodilators, Steroids, NIV:",
        "vaccination_medicines": "Vaccination — Real Preventive Exacerbation Reduction:",
        "medical_device_medicines": "Medical Equipment/Devices — Inhalers, Oxygen Concentrators, NIV/BiPAP, Endobronchial Valves, Peak Flow Meters, Thermoplasty Catheters:",
        "as_needed_ics_formoterol_medicines": "As-Needed ICS-Formoterol Reliever — Real, Practice-Changing GINA Shift Away From SABA-Alone:",
        "ics_controller_medicines": "Inhaled Corticosteroid (ICS) Controller Monotherapy — Low/Medium/High Dose:",
        "ics_laba_combination_medicines": "ICS-LABA Combination Controller Therapy:",
        "leukotriene_receptor_antagonist_medicines": "Leukotriene Receptor Antagonists (Montelukast):",
        "theophylline_medicines": "Theophylline — Real Older Option, Real Modern De-Emphasis:",
        "allergen_immunotherapy_medicines": "Allergen-Specific Immunotherapy — Real Disease-Modifying Potential:",
        "bronchial_thermoplasty_medicines": "Bronchial Thermoplasty — Real Device-Based Option, Niche Guideline Role:",
        "environmental_control_medicines": "Environmental Control / Trigger Avoidance — Real, Honestly-Mixed Evidence:",
        "hypersensitivity_pneumonitis_antigen_avoidance": "Hypersensitivity Pneumonitis — Antigen Avoidance, Real Disease-Modifying/Reversing Intervention (Early, Non-Fibrotic Disease):",
        "ipf_antifibrotic_therapy": "IPF Antifibrotic Therapy — Pirfenidone (ASCEND) & Nintedanib (INPULSIS-1/2):",
        "immunosuppression_ipf_vs_ctd_ild": "Immunosuppression — Real HARM in IPF (PANTHER-IPF) vs Real Benefit in CTD-ILD (SLS I/II, RECITAL):",
        "nintedanib_expanded_ppf_indication": "Nintedanib — Real Expanded Indication, Progressive Pulmonary Fibrosis (PPF) Beyond IPF (INBUILD):",
        "pirfenidone_non_ipf_ild_evidence": "Pirfenidone — Real, Honestly Inconclusive Evidence in Non-IPF Progressive Fibrosing ILD (RELIEF):",
        "supportive_care_and_comorbidity_management": "Supportive Care & Comorbidity Management — Oxygen, Pulmonary Rehabilitation, ILD-Associated Pulmonary Hypertension, GERD:",
        "lung_transplantation": "Lung Transplantation — Real Definitive Treatment for Eligible End-Stage ILD/IPF:",
        "acute_exacerbation_management": "Acute Exacerbation of IPF (AE-IPF) Management — Corticosteroids, Ventilation, Palliative Care:",
        "medical_equipment_devices": "Medical Equipment/Devices — Home Oxygen Concentrators, Pulse Oximetry, HRCT:",
        "airway_clearance_medicines": "Airway Clearance Techniques — Chest Physiotherapy, Oscillating PEP Devices, HFCWO Vest:",
        "mucoactive_therapy_medicines": "Mucoactive Nebulised Therapy — Hypertonic Saline, Dornase Alfa (Real Negative Finding), Mannitol:",
        "long_term_suppressive_antibiotic_medicines": "Long-Term Suppressive/Prophylactic Antibiotic Therapy — Macrolides & Inhaled Antibiotics:",
        "acute_exacerbation_antibiotic_therapy_medicines": "Acute Exacerbation Management — Culture-Guided Antibiotic Selection & Duration:",
        "abpa_specific_management_medicines": "ABPA-Specific Management — Real Early Treatment Preventing Progression to Fixed Bronchiectasis:",
        "novel_targeted_therapy_medicines": "Novel Targeted Anti-Inflammatory Therapy — DPP-1 Inhibition:",
        "surgical_and_embolization_medicines": "Surgical Resection & Bronchial Artery Embolization:",
        "bronchiectasis_medical_device_medicines": "Medical Equipment/Devices — PEP/HFCWO Devices, Nebulisers, Bronchial Artery Embolization Catheters:",
        "pressure_therapy_devices": "Positive Airway Pressure Therapy — CPAP, APAP, BiPAP (First-Line, Real SAVE-Trial-Honest Cardiovascular Evidence):",
        "oral_appliance_therapy": "Oral Appliance Therapy — Mandibular Advancement Devices:",
        "positional_therapy": "Positional Therapy — Positional-OSA-Subtype-Specific Devices:",
        "surgical_options": "Surgical Options — UPPP, Maxillomandibular Advancement, Hypoglossal Nerve Stimulation, Bariatric Surgery:",
        "pharmacotherapy": "Pharmacotherapy — GLP-1/GIP Agonists (Tirzepatide, Semaglutide):",
        "simple_adjunct_measures": "Simple Adjunct Measures — Alcohol/Sedative Avoidance:",
        "osa_medical_equipment_devices": "Medical Equipment/Devices — CPAP/APAP/BiPAP Machines, Oral Appliances, Hypoglossal Nerve Stimulator, Positional Therapy Devices:",
        "surgical_resection_early_stage": "Surgical Resection — Real Curative-Intent Standard, Early-Stage NSCLC (Lobectomy / Segmentectomy):",
        "sbrt_inoperable_early_stage": "Stereotactic Body Radiotherapy (SBRT) — Real Curative-Intent Alternative, Medically-Inoperable Early-Stage NSCLC:",
        "adjuvant_neoadjuvant_therapy_resectable_nsclc": "Adjuvant / Neoadjuvant / Perioperative Therapy — Resectable NSCLC (Chemotherapy, Osimertinib, Immunotherapy):",
        "targeted_therapy_driver_positive_advanced_nsclc": "Targeted Therapy — Driver-Mutation-Positive Advanced NSCLC (EGFR, ALK, ROS1, KRAS G12C):",
        "immunotherapy_advanced_nsclc_no_driver_mutation": "Immunotherapy — Advanced NSCLC Without a Targetable Driver Mutation:",
        "sclc_treatment": "Small Cell Lung Cancer (SCLC) Treatment — Platinum-Etoposide, Immunotherapy, Prophylactic Cranial Irradiation:",
        "oncologic_emergency_management": "Oncologic Emergency Management — SVC Syndrome, Spinal Cord Compression, Malignant Pleural Effusion:",
        "palliative_care_integration": "Early Palliative Care Integration — Real Survival AND Quality-of-Life Benefit:",
        "lung_cancer_medical_equipment_devices": "Medical Equipment/Devices — SBRT Delivery Systems, Endobronchial Stents, Indwelling Pleural Catheters:",
        "tension_pneumothorax_emergency_decompression": "Tension Pneumothorax — Emergency Needle Decompression + Tube Thoracostomy (Real Life-Saving, Not Optional):",
        "psp_size_severity_based_management": "Primary Spontaneous Pneumothorax — Size/Severity-Based Management (Observation, Needle Aspiration, Chest Tube):",
        "psp_conservative_management_evidence": "Real Evolving Evidence — Conservative Management of Moderate-to-Large PSP (Brown et al NEJM 2020):",
        "ssp_management": "Secondary Spontaneous Pneumothorax — More Aggressive, Lower-Threshold Management:",
        "recurrence_prevention_vats_pleurodesis": "Recurrence Prevention — VATS Bullectomy/Blebectomy + Pleurodesis vs Drainage Alone:",
        "chemical_pleurodesis_agents": "Chemical Pleurodesis Agents — Talc, Doxycycline, Autologous Blood Patch (Including Real ARDS Risk):",
        "surgical_intervention_indications": "Real Guideline-Based Indications for Surgery After a First Episode:",
        "catamenial_pneumothorax_management": "Catamenial Pneumothorax — GnRH-Agonist Hormonal Therapy + Surgical Diaphragmatic Repair:",
        "pneumothorax_analgesia": "Analgesia — Pneumothorax and Chest-Tube-Associated Pain:",
        "pneumothorax_medical_equipment_devices": "Medical Equipment/Devices — Needle Decompression Catheter, Pigtail/Chest Tube, Heimlich Valve, VATS Equipment:",
        "ards_lung_protective_ventilation_strategy": "Lung-Protective Ventilation Strategy — Low Tidal Volume (ARDSNet/ARMA), Driving Pressure:",
        "ards_peep_strategy": "PEEP Strategy — Higher vs Lower PEEP (ALVEOLI/LOVS/EXPRESS), Recruitment Maneuvers (ART Trial):",
        "ards_prone_positioning": "Prone Positioning — Moderate-Severe ARDS (PROSEVA):",
        "ards_neuromuscular_blockade": "Neuromuscular Blockade — Evidence Evolution (ACURASYS vs ROSE):",
        "ards_conservative_fluid_management": "Conservative Fluid Management (FACTT):",
        "ards_ecmo_therapy": "Extracorporeal Membrane Oxygenation (ECMO) — Severe Refractory ARDS (CESAR, EOLIA):",
        "ards_pharmacologic_therapy": "Pharmacologic Therapy — Corticosteroids, Inhaled Nitric Oxide/Prostacyclin, Statins:",
        "ards_hfno_niv_bridge_strategies": "High-Flow Nasal Oxygen & Non-Invasive Ventilation — Bridge/Avoidance Strategies:",
        "ards_rescue_therapies_refractory_hypoxemia": "Rescue Therapies for Refractory Hypoxemia — Recruitment Maneuvers, HFOV (OSCILLATE/OSCAR):",
        "ards_medical_equipment_devices": "Medical Equipment/Devices — Lung-Protective Ventilators, ECMO Circuit, Proning Equipment/Protocol:",
        "transudative_effusion_cause_directed_therapy": "Transudative Effusion — Cause-Directed Therapy (CHF/Hepatic Hydrothorax/Nephrotic Syndrome), Real Cure of the Effusion:",
        "parapneumonic_effusion_empyema_staged_management": "Parapneumonic Effusion/Empyema — ACCP/Colice-Staged Antibiotics +/- Drainage:",
        "fibrinolytic_dnase_intrapleural_therapy": "Intrapleural Fibrinolytic + DNase Therapy — Organized/Loculated Empyema (MIST2):",
        "vats_surgical_decortication": "VATS / Surgical Decortication — Fibrinopurulent and Organized-Stage Empyema:",
        "malignant_pleural_effusion_ipc_vs_pleurodesis": "Malignant Pleural Effusion — IPC vs Talc Pleurodesis (Real Definitive CONTROL, Not Cure):",
        "malignant_effusion_combined_ipc_talc_pleurodesis": "Malignant Pleural Effusion — Combined IPC + Talc Pleurodesis (IPC-PLUS):",
        "thoracentesis_diagnostic_therapeutic_safety": "Thoracentesis — Diagnostic/Therapeutic Safety (Ultrasound Guidance, Volume Limits):",
        "tuberculous_pleural_effusion_treatment": "Tuberculous Pleural Effusion — ATT +/- Adjunctive Corticosteroids:",
        "chylothorax_management": "Chylothorax Management — MCT Diet/Octreotide vs Surgical Thoracic Duct Ligation:",
        "hemothorax_management": "Hemothorax Management — Chest Tube Drainage, Surgical Exploration Criteria, Early VATS:",
        "pleural_effusion_medical_equipment_devices": "Medical Equipment/Devices — Thoracentesis Kits, Chest Tube/Pigtail Systems, Indwelling Pleural Catheter, VATS Equipment:",
        "diabetes_t2dm_first_line_pharmacotherapy": "T2DM First-Line Pharmacotherapy — Metformin (Real UKPDS Mortality Data):",
        "diabetes_t2dm_sglt2_inhibitors": "T2DM SGLT2 Inhibitors — Real Cardiovascular & Renal Outcome-Trial Data:",
        "diabetes_t2dm_glp1_receptor_agonists": "T2DM GLP-1 Receptor Agonists (incl. Dual GIP/GLP-1) — Real Weight-Loss & Cardiovascular-Outcome Data:",
        "diabetes_t2dm_dpp4_inhibitors": "T2DM DPP-4 Inhibitors — Real Cardiovascular-Neutral, Modest-Efficacy Class:",
        "diabetes_t2dm_sulfonylureas": "T2DM Sulfonylureas — Real-World Use & Hypoglycaemia-Risk Caveat:",
        "diabetes_t2dm_thiazolidinediones": "T2DM Thiazolidinediones — Pioglitazone (Real Macrovascular Signal & Side-Effect Caveats):",
        "diabetes_t1dm_insulin_basal_bolus_therapy": "T1DM Basal-Bolus Insulin Therapy — Rapid-Acting & Long-Acting Analog Insulins:",
        "diabetes_t1dm_automated_insulin_delivery_devices": "T1DM Devices — Hybrid Closed-Loop / Automated Insulin Delivery (\"Artificial Pancreas\"):",
        "diabetes_glycemic_targets_monitoring": "Glycaemic Targets & Monitoring-Driven Treatment Intensification — ADA Targets, DCCT/EDIC Legacy Effect:",
        "diabetes_dka_management": "Acute Complication Management — Diabetic Ketoacidosis (DKA):",
        "diabetes_hhs_management": "Acute Complication Management — Hyperosmolar Hyperglycaemic State (HHS):",
        "diabetes_severe_hypoglycemia_glucagon": "Severe Hypoglycaemia — Glucagon Rescue Therapy (incl. Nasal Glucagon):",
        "diabetes_nephropathy_management": "Chronic Complication Management — Diabetic Nephropathy (ACEi/ARB):",
        "diabetes_retinopathy_management": "Chronic Complication Management — Diabetic Retinopathy (Laser & Anti-VEGF):",
        "diabetes_neuropathy_pain_management": "Chronic Complication Management — Painful Diabetic Peripheral Neuropathy:",
        "diabetes_prevention_program": "T2DM Primary Prevention — Diabetes Prevention Program (DPP) Trial:",
        "diabetes_medical_devices_equipment": "Medical Equipment/Devices — CGMs, Glucometers, Insulin Pens/Pumps:",
        "thyroid_hypothyroidism_levothyroxine_replacement": "Hypothyroidism First-Line — Levothyroxine (LT4) Monotherapy, Real ATA TSH-Titration Guideline:",
        "thyroid_combination_t4_t3_therapy": "Hypothyroidism Persistent-Symptoms Add-On — Combination LT4/LT3 Therapy (Real, Honestly Limited Evidence):",
        "thyroid_hyperthyroidism_antithyroid_drugs": "Hyperthyroidism/Graves' Disease — Antithyroid Drugs (Methimazole & Propylthiouracil, Real Safety Nuances):",
        "thyroid_hyperthyroidism_radioactive_iodine_ablation": "Hyperthyroidism/Graves' Disease — Radioactive Iodine (I-131) Ablation:",
        "thyroid_hyperthyroidism_surgical_thyroidectomy": "Hyperthyroidism/Graves' Disease — Total/Near-Total Thyroidectomy:",
        "thyroid_beta_blockers_symptomatic_control": "Hyperthyroidism — Beta-Blocker Symptomatic Control (Propranolol):",
        "thyroid_graves_ophthalmopathy_management": "Graves' Ophthalmopathy — IV Glucocorticoids, Teprotumumab, Orbital Decompression:",
        "thyroid_myxedema_coma_emergency_management": "Emergency — Myxedema Coma Management:",
        "thyroid_storm_emergency_management": "Emergency — Thyroid Storm Management (Burch-Wartofsky-Scored Protocol):",
        "thyroid_subclinical_disease_management": "Subclinical Hypothyroidism/Hyperthyroidism — Evidence-Based TSH-Threshold Framework:",
        "thyroid_postpartum_and_subacute_thyroiditis_management": "Postpartum & Subacute Thyroiditis — Real Self-Limiting-Course Management:",
        "thyroid_medical_devices_equipment": "Medical Equipment/Devices — RAI Administration, Thyroidectomy Nerve Monitoring, TSH/RAIU Diagnostics:",
        "tng_observation_active_surveillance": "Thyroid Nodule/Goitre — Active Surveillance, Real Guideline-Endorsed Default (Durante 2015, ATA 2015):",
        "tng_levothyroxine_suppression_therapy": "Thyroid Nodule/Goitre — Levothyroxine Suppressive Therapy, Real But Largely Abandoned (Cochrane 2014):",
        "tng_radiofrequency_ablation": "Thyroid Nodule/Goitre — Radiofrequency Ablation (Solid Nodules), Real Definitive Non-Surgical Cure:",
        "tng_ethanol_ablation_cystic_nodules": "Thyroid Nodule/Goitre — Percutaneous Ethanol Ablation (Cystic Nodules), Real Definitive Non-Surgical Cure:",
        "tng_surgical_lobectomy_thyroidectomy": "Thyroid Nodule/Goitre — Diagnostic Lobectomy / Total Thyroidectomy, Real Definitive Surgical Resolution:",
        "tng_medical_devices_equipment": "Thyroid Nodule/Goitre — Medical Equipment/Devices: Diagnostic Ultrasound/FNA, RFA Generator/Electrode:",
        "ckd_raas_blockade_aceiarb": "CKD Renoprotection — ACE Inhibitors / ARBs (Real First Pillar):",
        "ckd_sglt2_inhibitors_renal": "CKD Renoprotection — SGLT2 Inhibitors (Real Diabetic AND Non-Diabetic CKD Benefit — DAPA-CKD / EMPA-KIDNEY):",
        "ckd_finerenone_nsmra": "CKD Renoprotection — Finerenone, Non-Steroidal MRA (FIDELIO-DKD / FIGARO-DKD):",
        "ckd_anemia_management": "Complication Management — Anemia of CKD (ESAs + Iron, Real TREAT-Trial Safety Caveat):",
        "ckd_mineral_bone_disorder_management": "Complication Management — CKD-Mineral and Bone Disorder (Phosphate Binders, Vitamin D Analogs, Calcimimetics):",
        "ckd_metabolic_acidosis_correction": "Complication Management — Metabolic Acidosis (Oral Sodium Bicarbonate):",
        "ckd_hyperkalemia_management": "Complication Management — Hyperkalemia (Potassium Binders, Real RAASi-Continuation Advance):",
        "ckd_hemodialysis_therapy": "Renal Replacement Therapy — Hemodialysis vs Peritoneal Dialysis (Real Comparative Outcomes):",
        "ckd_kidney_transplantation_immunosuppression": "Definitive Option — Kidney Transplantation, Standard Immunosuppression Regimen:",
        "ckd_dietary_lifestyle_management": "Dietary/Lifestyle Management — Protein & Sodium Restriction (Real, Honestly-Nuanced Evidence):",
        "ckd_medical_devices_equipment": "Medical Equipment/Devices — Vascular Access (AV Fistula/Graft/Catheter), PD Catheter Systems, Hemodialysis Machine:",
        "cgn_raas_blockade_aceiarb": "Chronic Glomerulonephritis — ACE Inhibitors / ARBs, Real Foundational First-Line RAAS Blockade (REIN, AIPRI):",
        "cgn_sglt2_inhibitors": "Chronic Glomerulonephritis — SGLT2 Inhibitors, Real Newer Add-On Kidney-Protective Therapy (DAPA-CKD, EMPA-KIDNEY):",
        "cgn_corticosteroid_cytotoxic_membranous": "Chronic Glomerulonephritis — Corticosteroid Plus Cytotoxic Agent (Ponticelli Regimen) for Membranous Nephropathy:",
        "cgn_rituximab_membranous": "Chronic Glomerulonephritis — Rituximab for Membranous Nephropathy, Real Guideline-Preferred Option (MENTOR Trial):",
        "cgn_iga_specific_therapy_crossref": "Chronic Glomerulonephritis — IgA Nephropathy-Specific Therapy, Cross-Referenced to This KB's Dedicated Entry:",
        "cgn_bp_control_supportive_ckd_management": "Chronic Glomerulonephritis — Blood-Pressure Control and Supportive CKD Management, Cross-Referenced:",
        "cpn_acute_infective_episode_antibiotics": "Chronic Pyelonephritis — Antibiotic Treatment of Acute Infective Episodes, Real First-Line/Alternative Regimens (Talan JAMA 2000, IDSA/ESCMID 2010):",
        "cpn_antibiotic_prophylaxis_pediatric_vur": "Chronic Pyelonephritis — Antibiotic Prophylaxis in Select Pediatric VUR Patients, Real Modest Benefit/Resistance Tradeoff (RIVUR, Swedish Reflux Trial):",
        "cpn_surgical_endoscopic_cause_correction": "Chronic Pyelonephritis — Surgical/Endoscopic Correction of Vesicoureteral Reflux or Obstruction, Cross-Referenced to curative_option:",
        "cpn_ckd_esrd_supportive_management_crossref": "Chronic Pyelonephritis — CKD/ESRD Supportive Management for Progressive Bilateral Scarring, Cross-Referenced:",
        "igan_raas_blockade_aceiarb": "IgA Nephropathy — ACE Inhibitors / ARBs, Real Foundational First-Line RAAS Blockade:",
        "igan_sglt2_inhibitors": "IgA Nephropathy — SGLT2 Inhibitors, Real Newer Add-On Kidney-Protective Therapy (DAPA-CKD IgAN Subgroup):",
        "igan_targeted_release_budesonide_nefecon": "IgA Nephropathy — Targeted-Release Budesonide (Nefecon/TARPEYO/Kinpeygo), Real Landmark Gut-Targeted Disease-Modifying Therapy (NefIgArd):",
        "igan_sparsentan_dearas": "IgA Nephropathy — Sparsentan (Filspari), Real Dual Endothelin/Angiotensin-Receptor Antagonist (PROTECT Trial):",
        "igan_systemic_corticosteroids": "IgA Nephropathy — Systemic Corticosteroids, Real Older Higher-Risk-Patient Approach (TESTING Trial, Honest Side-Effect Burden):",
        "igan_fish_oil_omega3": "IgA Nephropathy — Fish Oil / Omega-3 Fatty Acids, Real Older and Inconsistently Reproduced Evidence:",
        "igan_bp_control_supportive_ckd_management": "IgA Nephropathy — Blood-Pressure-Control Target and Supportive CKD Management, Real Foundational but Non-Curative (Other):",
        "obesity_bariatric_metabolic_surgery": "Bariatric/Metabolic Surgery — Real RYGB/Sleeve Gastrectomy Data & Current Candidacy Criteria (incl. Asian-Population BMI Threshold):",
        "obesity_glp1_dual_agonist_pharmacotherapy": "GLP-1/Dual-Agonist Pharmacotherapy — Real Semaglutide (STEP) & Tirzepatide (SURMOUNT) Trial Data:",
        "obesity_older_antiobesity_pharmacotherapy": "Older Anti-Obesity Pharmacotherapy — Orlistat, Phentermine-Topiramate, Naltrexone-Bupropion (Real, Comparatively Modest Efficacy):",
        "obesity_lifestyle_intervention": "Lifestyle Intervention — DiRECT Cross-Reference & Look AHEAD (Real Cardiovascular-Neutral Finding, Honest):",
        "obesity_metabolic_syndrome_component_management": "Metabolic Syndrome Component Management — Hypertension/Dyslipidaemia/Hyperglycaemia (Cross-Referenced):",
        "obesity_behavioral_psychological_support": "Behavioral/Psychological Support — Cognitive Behavioral Therapy (Adjunctive Role):",
        "obesity_endoscopic_bariatric_procedures": "Endoscopic Bariatric Procedures — Endoscopic Sleeve Gastroplasty (MERIT) & Intragastric Balloon:",
        "obesity_hypoventilation_syndrome_management": "Obesity Hypoventilation Syndrome (OHS) Management — Weight Loss + Positive Airway Pressure:",
        "obesity_medical_devices_equipment": "Medical Equipment/Devices — Bariatric Surgical/Robotic Platforms, Endoscopic Suturing/Balloon Devices, Body-Composition Monitoring:",
        "dyslipidemia_statin_therapy": "Statin Therapy — Real High/Moderate/Low-Intensity Framework (2018 ACC/AHA), Cross-Referenced TNT/JUPITER Data:",
        "dyslipidemia_ezetimibe_add_on_therapy": "Ezetimibe Add-On Therapy — Real IMPROVE-IT Outcome Data:",
        "dyslipidemia_pcsk9_inhibitor_therapy": "PCSK9 Inhibitors — Real Evolocumab (FOURIER) & Alirocumab (ODYSSEY Outcomes) Data:",
        "dyslipidemia_inclisiran_sirna_therapy": "Inclisiran — Real siRNA-Based Twice-Yearly PCSK9-Synthesis Silencer (ORION-10/11), CVOT-Pending:",
        "dyslipidemia_triglyceride_lowering_therapy": "Triglyceride-Lowering Therapy — Fibrates, Icosapent Ethyl (REDUCE-IT), Omega-3 (Real STRENGTH-Trial Neutral Contrast):",
        "dyslipidemia_lpa_lowering_therapy": "Lp(a)-Lowering Therapy — Real Emerging Agents (Pelacarsen, Olpasiran), Honestly Early-Phase/Mixed:",
        "dyslipidemia_fh_specific_management": "Familial Hypercholesterolemia-Specific Management — Aggressive Statin Initiation, LDL Apheresis, Lomitapide & Evinacumab (Homozygous FH):",
        "dyslipidemia_lifestyle_intervention": "Lifestyle Intervention — Real Mediterranean Diet (PREDIMED) & Exercise Lipid Effects:",
        "dyslipidemia_secondary_dyslipidemia_management": "Secondary Dyslipidemia — Treat the Underlying Cause, incl. Real CKD/Dialysis Statin-Initiation Exception:",
        "dyslipidemia_acute_severe_htg_management": "Acute Severe Hypertriglyceridemia / Pancreatitis-Risk Management — Insulin Infusion & Plasmapheresis:",
        "dyslipidemia_medical_devices": "Medical Equipment/Devices — LDL Apheresis Systems, Point-of-Care Lipid Panel Analyzers:",
        "pcos_hormonal_contraceptives_cycle_regulation_endometrial_protection": "Goal: Cycle Regulation / Endometrial Protection — Combined Hormonal Contraceptives & Cyclic Progestin Therapy:",
        "pcos_hyperandrogenism_hirsutism_acne_management": "Goal: Hyperandrogenism / Hirsutism / Acne — COCs, Spironolactone, Topical Eflornithine, Laser/Electrolysis:",
        "pcos_insulin_resistance_metabolic_management": "Goal: Insulin Resistance / Metabolic Risk — Metformin & Myo-Inositol/D-Chiro-Inositol:",
        "pcos_infertility_ovulation_induction": "Goal: Infertility / Ovulation Induction — Letrozole (PPCOS II), Clomiphene, Gonadotropins, Laparoscopic Ovarian Drilling, IVF:",
        "pcos_glp1_emerging_weight_loss_therapy": "Emerging Therapy — GLP-1/Dual-Agonist Weight-Loss Pharmacotherapy in PCOS-Specific Cohorts:",
        "pcos_lifestyle_intervention": "Foundational Therapy — Three-Component Lifestyle Intervention (Diet/Exercise/Behavioural), All Phenotypes:",
        "pcos_long_term_metabolic_surveillance": "Long-Term Metabolic Surveillance — PCOS-Specific OGTT Screening Guidance (Cross-Referenced):",
        "pcos_medical_devices_equipment": "Medical Equipment/Devices — Transvaginal/Pelvic Ultrasound, Laser Hair Removal & Electrolysis Devices:",
        "osteoporosis_calcium_vitamin_d_foundational_therapy": "Foundational Therapy — Calcium & Vitamin D Supplementation (Real, Honestly Modest Evidence):",
        "osteoporosis_bisphosphonates_first_line_therapy": "First-Line Antiresorptive Therapy — Bisphosphonates (Alendronate/Risedronate/Zoledronic Acid/Ibandronate), incl. Real ONJ/AFF Safety Caveats:",
        "osteoporosis_denosumab_rankl_inhibitor": "RANKL Inhibitor — Denosumab (FREEDOM Trial), incl. Critical Discontinuation-Rebound Caveat:",
        "osteoporosis_anabolic_bone_forming_agents": "Anabolic / Bone-Forming Agents — Teriparatide, Abaloparatide & Romosozumab (Genuinely Distinct Mechanism, Most Potent for High-Risk Patients):",
        "osteoporosis_hormone_therapy_and_serms": "Hormone Therapy & SERMs — Estrogen (Not First-Line) & Raloxifene (MORE Trial):",
        "osteoporosis_treatment_sequencing_and_drug_holiday": "Real Sequencing & Duration Guidance — Bisphosphonate Drug Holiday & Anabolic-Then-Antiresorptive Sequencing:",
        "osteoporosis_fracture_prevention_adjuncts": "Fracture-Prevention Adjuncts — Hip Protectors, Fall-Prevention Exercise, Vertebroplasty (Real Sham-Trial Finding) & Kyphoplasty:",
        "osteoporosis_medical_devices_equipment": "Medical Equipment/Devices — DXA Scanners, Vertebroplasty/Kyphoplasty Equipment, Hip Protectors:",
        "hepatitis_c_daa_pangenotypic_regimens": "Hepatitis C — Pangenotypic Direct-Acting Antiviral (DAA) Regimens, the Real Cure Standard:",
        "hepatitis_c_daa_genotype_specific_regimens": "Hepatitis C — Genotype-Specific DAA Regimens:",
        "hepatitis_c_historical_interferon_based_therapy": "Hepatitis C — Historical Interferon-Based Therapy (Real, Honestly Inferior Predecessor to DAAs):",
        "hepatitis_b_nucleos_tide_analog_therapy": "Chronic Hepatitis B — Nucleos(t)ide Analog Therapy (Real Suppression, Not Cure):",
        "hepatitis_b_pegylated_interferon_therapy": "Chronic Hepatitis B — Pegylated Interferon Alfa-2a (Real Finite-Duration Alternative):",
        "hepatitis_b_functional_cure_research": "Chronic Hepatitis B — Functional Cure Research (Real, Honestly Early-Phase):",
        "hepatitis_d_bulevirtide_and_interferon_therapy": "Hepatitis D — Bulevirtide & Pegylated Interferon:",
        "hepatitis_a_e_supportive_care_management": "Hepatitis A & E — Supportive Care (Typical) and Severe/Fulminant-Case Management:",
        "hepatitis_prevention_vaccination_and_perinatal_prophylaxis": "Prevention — Hepatitis A/B Vaccination & Perinatal HBV Transmission Prevention:",
        "hepatitis_liver_transplantation": "Liver Transplantation — End-Stage Liver Disease from Viral Hepatitis:",
        "hepatitis_medical_equipment_devices": "Medical Equipment/Devices — Liver Biopsy & FibroScan (Transient Elastography), Cross-Referenced:",
        "cirrhosis_ascites_diuretic_therapy": "Ascites — First-Line Diuretic Therapy (Spironolactone +/- Furosemide):",
        "cirrhosis_ascites_paracentesis_albumin": "Ascites — Large-Volume Paracentesis With Albumin Replacement:",
        "cirrhosis_ascites_tips": "Ascites — TIPS for Refractory Ascites:",
        "cirrhosis_variceal_bleeding_primary_prophylaxis": "Variceal Hemorrhage — Primary Prophylaxis (Nonselective Beta-Blockers / EVL):",
        "cirrhosis_variceal_bleeding_acute_management": "Variceal Hemorrhage — Acute Management (Vasoactive Drugs + Antibiotic Prophylaxis):",
        "cirrhosis_variceal_bleeding_tips_refractory": "Variceal Hemorrhage — TIPS for Refractory/Recurrent Bleeding:",
        "cirrhosis_hepatic_encephalopathy_management": "Hepatic Encephalopathy — Lactulose (First-Line) & Rifaximin (Recurrent HE Add-On):",
        "cirrhosis_sbp_treatment_and_prophylaxis": "Spontaneous Bacterial Peritonitis — Empiric Treatment & Long-Term Prophylaxis:",
        "cirrhosis_hepatorenal_syndrome_management": "Hepatorenal Syndrome — Vasoconstrictor + Albumin Therapy & Transplantation:",
        "cirrhosis_hcc_surveillance_cross_reference": "Hepatocellular Carcinoma Surveillance — Biannual Ultrasound +/- AFP (Cross-Referenced):",
        "cirrhosis_transplant_immunosuppression_cross_reference": "Liver Transplantation — Standard Immunosuppression (Cross-Referenced):",
        "cirrhosis_nutrition_lifestyle_management": "Nutrition/Lifestyle Management — Protein Intake & Vaccination:",
        "cirrhosis_medical_equipment_devices": "Medical Equipment/Devices — Paracentesis, TIPS, and Endoscopic Variceal Ligation Equipment:",
        "pud_h_pylori_eradication_first_line_regimens": "H. pylori Eradication — Real 2024 ACG-Guideline First-Line Regimens (Bismuth Quadruple, Concomitant, Sequential, Clarithromycin Triple):",
        "pud_h_pylori_rescue_second_line_therapy": "H. pylori Eradication — Real Rescue/Second-Line Therapy (Treatment-Experienced/Persistent Infection):",
        "pud_confirmation_of_cure_testing": "Confirmation of Cure — Real Post-Eradication Testing (Urea Breath Test/Stool Antigen, NOT Serology):",
        "pud_nsaid_induced_ulcer_management": "NSAID-Induced, H. pylori-Negative Ulcers — Real Distinct Management Picture (Discontinuation, PPI, Misoprostol, COX-2):",
        "pud_zollinger_ellison_syndrome_management": "Zollinger-Ellison Syndrome — Real High-Dose PPI Control & Surgical Resection:",
        "pud_acute_hemorrhage_management": "Acute Complication — Upper GI Hemorrhage Management (Endoscopic Hemostasis, IV PPI, Transfusion Strategy):",
        "pud_acute_perforation_management": "Acute Complication — Perforation Management (Graham Patch Repair, Selective Non-Operative Management):",
        "pud_gastric_outlet_obstruction_management": "Acute/Chronic Complication — Gastric Outlet Obstruction Management (Endoscopic Balloon Dilation vs Surgery):",
        "pud_surgical_options_refractory_complicated_disease": "Surgical Options — Refractory/Complicated PUD (Vagotomy/Antrectomy, Real Historical-Context Shift):",
        "pud_prevention_ppi_prophylaxis_and_icu_stress_ulcer_prophylaxis": "Prevention — PPI Prophylaxis in High-Risk NSAID Users & ICU Stress-Ulcer Prophylaxis:",
        "pud_medical_equipment_devices": "Medical Equipment/Devices — Upper GI Endoscope, Hemostasis Clips/Thermal Probes, Balloon Dilators:",
        "ag_h_pylori_eradication_regimens": "H. pylori Eradication — Real 2024 ACG-Guideline Regimens (Bismuth Quadruple, Concomitant, Clarithromycin Triple), Same Organism/Regimens as PUD:",
        "ag_removal_of_offending_agent": "Removal of Offending Agent — NSAID Discontinuation & Alcohol Cessation, Real First Curative Step:",
        "ag_acid_suppression_therapy": "Acid Suppression Therapy — PPIs, H2-Receptor Antagonists, Potassium-Competitive Acid Blockers (P-CABs), Real Gastritis-Specific Healing Rates:",
        "ag_mucoprotective_agents": "Mucoprotective Agents — Sucralfate, Rebamipide, Eupatilin & Other Real Named Agents:",
        "ag_antiemetics_and_supportive_care": "Antiemetics & Supportive Care — Symptomatic Management:",
        "ag_icu_stress_ulcer_prophylaxis": "ICU Stress-Ulcer Prophylaxis — Real Guideline-Quantified Bleeding-Risk Reduction (Prophylaxis, Not a Cure):",
        "ag_medical_equipment_devices": "Medical Equipment/Devices — Upper GI Endoscope & Biopsy Forceps for Diagnosis/H. pylori Testing:",
        "nafld_weight_loss_lifestyle_intervention": "NAFLD/MASLD — Weight Loss Through Intensive Lifestyle Intervention, Real Best-Evidenced First-Line Therapy (Vilar-Gomez 2015):",
        "nafld_bariatric_metabolic_surgery": "NAFLD/MASLD — Bariatric/Metabolic Surgery, Real Durable 5-Year Resolution in Eligible Severe Obesity (Lassailly 2020):",
        "nafld_resmetirom": "NAFLD/MASLD — Resmetirom (Rezdiffra), Real First FDA-Approved Drug for NASH/MASH With Fibrosis (MAESTRO-NASH, Harrison 2024 NEJM):",
        "nafld_semaglutide_glp1": "NAFLD/MASLD — Semaglutide (GLP-1 Receptor Agonist), Real FDA-Approved for MASH With Fibrosis (ESSENCE Trial, 2025 NEJM):",
        "nafld_pioglitazone": "NAFLD/MASLD — Pioglitazone, Real Insulin-Sensitizer Option Especially in Prediabetic/T2DM NASH (PIVENS/Cusi 2016):",
        "nafld_vitamin_e": "NAFLD/MASLD — Vitamin E, Real Antioxidant Option in Non-Diabetic, Non-Cirrhotic NASH (PIVENS Trial):",
        "ibd_5_aminosalicylate_therapy": "5-Aminosalicylates (5-ASA) — First-Line in UC, Honestly Weaker Evidence in Crohn's Disease:",
        "ibd_corticosteroids_induction_only": "Corticosteroids — Induction-Only Therapy in Both Diseases (NOT Maintenance):",
        "ibd_immunomodulators": "Immunomodulators — Thiopurines (with Mandatory TPMT Testing) & Methotrexate:",
        "ibd_biologic_therapy_anti_tnf": "Biologic Therapy — Anti-TNF Agents (Infliximab, Adalimumab, Certolizumab Pegol):",
        "ibd_biologic_therapy_anti_integrin": "Biologic Therapy — Anti-Integrin, Gut-Selective (Vedolizumab):",
        "ibd_biologic_therapy_anti_il12_23": "Biologic Therapy — Anti-IL-12/23, p40 Subunit (Ustekinumab):",
        "ibd_jak_inhibitors": "JAK Inhibitors — Tofacitinib & Upadacitinib, incl. Real Cardiovascular/Thrombosis Safety Signal:",
        "ibd_biologic_therapy_anti_il23_specific": "Biologic Therapy — Anti-IL-23-Specific, p19 Subunit (Risankizumab, Mirikizumab):",
        "ibd_top_down_vs_step_up_strategy": "Treatment Strategy — Top-Down/Early Combined Immunosuppression vs Conventional Step-Up:",
        "ibd_fistulizing_crohns_management": "Fistulizing Crohn's Disease — Anti-TNF Therapy + Surgical Seton Drainage:",
        "ibd_nutrition_therapy": "Nutrition Therapy — Exclusive Enteral Nutrition (Pediatric Crohn's Induction):",
        "ibd_acute_severe_uc_management": "Acute Severe Ulcerative Colitis — IV Steroids, Day-3 Oxford Criteria, Rescue Therapy:",
        "ibd_medical_equipment_devices": "Medical Equipment/Devices — Colonoscope, Ileostomy/Colostomy Appliances, IPAA (J-Pouch) Construction:",
        "gerd_lifestyle_modification_foundational_therapy": "Lifestyle Modification — Real Foundational, Evidence-Graded Therapy (Weight Loss, Head-of-Bed Elevation, Avoiding Late Meals):",
        "gerd_antacids": "Antacids — Real Fast-Onset, Short-Acting Symptomatic Relief Only:",
        "gerd_h2_receptor_antagonists": "H2-Receptor Antagonists — Famotidine, incl. Real Ranitidine/NDMA Withdrawal History:",
        "gerd_proton_pump_inhibitors": "Proton Pump Inhibitors — Real First-Line Erosive Esophagitis Healing, incl. Real Long-Term Safety Considerations:",
        "gerd_prokinetic_agents": "Prokinetic Agents — Metoclopramide, incl. Real Tardive-Dyskinesia Safety Caveat:",
        "gerd_potassium_competitive_acid_blockers": "Potassium-Competitive Acid Blockers (P-CABs) — Vonoprazan, Real Newer Faster/More-Potent Acid Suppression:",
        "gerd_barretts_esophagus_endoscopic_eradication_therapy": "Barrett's Esophagus Endoscopic Eradication Therapy — RFA (Real Cancer-Prevention Intervention) & EMR for Nodular Lesions:",
        "gerd_esophageal_stricture_management": "Esophageal Stricture Management — Endoscopic Dilation Combined With Acid Suppression:",
        "gerd_medical_equipment_devices": "Medical Equipment/Devices — Bravo Wireless pH Capsule, LINX Device, Barrx RFA Catheter System, Dilation Balloons/Bougies:",
        "ap_fluid_resuscitation_strategy": "Fluid Resuscitation Strategy — Real WATERFALL-Trial-Proven Moderate/Goal-Directed vs Real Disproven Aggressive Regimen:",
        "ap_analgesia": "Analgesia — Opioids (Morphine, Fentanyl, Hydromorphone) & the Real Debunked Sphincter-of-Oddi Concern:",
        "ap_nutrition_strategy": "Nutrition Strategy — Real Early Oral Feeding (24-48h) vs Real PYTHON-Trial Nasoenteric Tube Feeding Finding:",
        "ap_antibiotic_therapy": "Antibiotic Therapy — Real Targeted Therapy for Confirmed Infection vs Real Disproven Routine Prophylaxis:",
        "ap_gallstone_pancreatitis_ercp_management": "Gallstone Pancreatitis — ERCP with Sphincterotomy (Real Indications: Cholangitis/Persistent Obstruction Only):",
        "ap_gallstone_pancreatitis_cholecystectomy_timing": "Gallstone Pancreatitis — Real PONCHO-Trial Cholecystectomy Timing (Same-Admission vs Interval):",
        "ap_infected_necrosis_stepup_management": "Infected Pancreatic Necrosis — Real PANTER-Trial Step-Up Approach vs Open Necrosectomy:",
        "ap_hypertriglyceridemia_induced_pancreatitis_management": "Hypertriglyceridemia-Induced Pancreatitis — Insulin/Heparin, Real Disproven Plasmapheresis Futility, & Long-Term Lipid Control:",
        "ap_medical_equipment_devices": "Medical Equipment/Devices — Percutaneous Drainage Catheters, ERCP Duodenoscope, VARD Instrumentation, Nasoenteric Feeding Tubes, Apheresis Machine:",
        "cp_pancreatic_enzyme_replacement_therapy": "Chronic Pancreatitis — Pancreatic Enzyme Replacement Therapy (PERT), Real Near-Complete Fix for Exocrine Insufficiency (Whitcomb 2010, 2026 Meta-Analysis):",
        "cp_analgesic_step_up_ladder": "Chronic Pancreatitis — Real Escalating Analgesic Step-Up Ladder: Non-Opioids, Tramadol, Strong Opioids, Pregabalin Adjunct (Wilder-Smith 1999, Olesen 2011, Drewes 2017):",
        "cp_antioxidant_therapy": "Chronic Pancreatitis — Combination Antioxidant Supplementation, Real Adjunct Pain-Relief Evidence (Bhardwaj 2009):",
        "cp_endoscopic_and_interventional_pain_therapy": "Chronic Pancreatitis — EUS-Guided Celiac Plexus Block & Endoscopic Duct Drainage (Santosh 2009, Cahen 2007, ESCAPE 2020):",
        "cp_surgical_duct_decompression": "Chronic Pancreatitis — Real Early Surgical Duct Decompression for Refractory Pain, Closest-to-Definitive Procedure (Cahen 2007/2011, ESCAPE 2020/2025):",
        "cp_alcohol_and_smoking_cessation": "Chronic Pancreatitis — Real Alcohol Abstinence & Smoking Cessation, Disease-Progression-Slowing Evidence (Talamini 1999, Maisonneuve 2005):",
        "cp_medical_equipment_devices": "Chronic Pancreatitis — Medical Equipment/Devices: ERCP Duodenoscope, EUS Echoendoscope, Shockwave Lithotripter, Surgical Instrumentation, CGM/Insulin Pump:",
        "celiac_nutritional_deficiency_correction": "Nutritional Deficiency Correction at Diagnosis — Iron, Folate, Vitamin B12, Vitamin D/Calcium, Zinc (Cross-Referenced to Iron-Deficiency-Anaemia & Osteoporosis Entries):",
        "celiac_refractory_disease_classification_and_management": "Refractory Celiac Disease (RCD) — Type I vs Type II Classification, Corticosteroids, Immunosuppressants, Cladribine, Autologous Stem Cell Transplant, AMG 714:",
        "celiac_emerging_investigational_pharmacotherapy": "Emerging/Investigational Pharmacotherapy — Larazotide Acetate & Latiglutenase (Real, Honestly NOT GFD Replacements):",
        "celiac_dermatitis_herpetiformis_management": "Dermatitis Herpetiformis-Specific Management — Dapsone (Rapid Skin Control While GFD Takes Effect):",
        "celiac_screening_at_risk_groups": "Screening — First-Degree Relatives, Type 1 Diabetes, Autoimmune Thyroid Disease, Dermatitis Herpetiformis:",
        "celiac_dietary_counseling_and_adherence_support": "Dietary Counseling & Adherence Support — Structured Dietitian-Led Multidisciplinary Care:",
        "celiac_monitoring_and_detection_tools": "Medical Equipment/Devices & Monitoring Tools — Point-of-Care Gluten Immunogenic Peptide Testing, Portable Food Gluten Sensors, Capsule Endoscopy:",
        "stroke_iv_thrombolysis": "Acute Ischaemic Stroke — IV Thrombolysis (Alteplase/Tenecteplase, Real NINDS/ECASS III/EXTEND-IA TNK/WAKE-UP Time-Window Evidence):",
        "stroke_mechanical_thrombectomy": "Acute Ischaemic Stroke — Mechanical Thrombectomy for Large-Vessel Occlusion (Real MR CLEAN/ESCAPE/SWIFT PRIME/EXTEND-IA/REVASCAT & Extended-Window DAWN/DEFUSE 3):",
        "stroke_secondary_prevention_antiplatelet": "Secondary Prevention — Antiplatelet Therapy (Aspirin, Short-Course Dual Therapy per Real CHANCE/POINT Data):",
        "stroke_secondary_prevention_anticoagulation": "Secondary Prevention — Anticoagulation for Cardioembolic Stroke (Cross-Referenced DOAC Data + Real Post-Stroke Timing Principle):",
        "stroke_secondary_prevention_statin": "Secondary Prevention — Statin Therapy (Real SPARCL Stroke-Specific Data):",
        "stroke_blood_pressure_management": "Blood Pressure Management — Real Acute-Phase Permissive Hypertension vs Long-Term Secondary-Prevention Control:",
        "stroke_carotid_revascularization": "Carotid Revascularization — Endarterectomy (Real NASCET Data) vs Stenting (Real CREST Data):",
        "stroke_hemorrhagic_ich_management": "Haemorrhagic Stroke — Intracerebral Haemorrhage Management (Real INTERACT2 BP Control, Anticoagulation Reversal, Surgical Evacuation):",
        "stroke_sah_management": "Haemorrhagic Stroke — Subarachnoid Haemorrhage Management (Real ISAT Aneurysm-Securing Data & Nimodipine):",
        "stroke_rehabilitation": "Post-Stroke Rehabilitation — Real Early Multidisciplinary Care & AVERT-Trial Mobilisation Evidence:",
        "stroke_tia_urgent_workup": "TIA — Real ABCD2-Score-Guided Urgent Workup & Immediate Secondary Prevention:",
        "stroke_medical_devices_equipment": "Medical Equipment/Devices — Stent Retrievers, Aspiration Catheters, Carotid Stents, External Ventricular Drain:",
        "tia_urgent_evaluation_pathway": "Urgent Evaluation Pathway — Real ABCD2-Score-Guided Same-Day TIA Clinic (Real EXPRESS-Trial 80% Stroke-Risk-Reduction Data):",
        "tia_dual_antiplatelet_therapy": "Dual Antiplatelet Therapy — Real Short-Course Aspirin+Clopidogrel (CHANCE/POINT) & Aspirin+Ticagrelor (THALES):",
        "tia_statin_therapy": "High-Intensity Statin Therapy — Real SPARCL Stroke/TIA-Specific Data:",
        "tia_af_anticoagulation": "Anticoagulation for AF-Related TIA — Real DOACs (Apixaban/Rivaroxaban/Dabigatran) vs Warfarin (Real EAFT/ARISTOTLE Data):",
        "tia_carotid_revascularization": "Carotid Revascularization — Endarterectomy (Real NASCET Data) vs Stenting (Real CREST Data):",
        "tia_blood_pressure_and_risk_factor_management": "Blood Pressure Control & Lifestyle Risk-Factor Management — Real Long-Term Secondary-Prevention Cornerstone:",
        "epilepsy_first_line_focal_aeds": "First-Line AED Selection — Focal Seizures (Real SANAD/SANAD II Lamotrigine vs Levetiracetam vs Carbamazepine Data):",
        "epilepsy_first_line_generalized_aeds": "First-Line AED Selection — Generalized/Unclassifiable Seizures (Real SANAD II Valproate vs Levetiracetam Data & Critical Teratogenicity Warning):",
        "epilepsy_newer_adjunctive_aeds": "Newer/Adjunctive AEDs — Lacosamide, Perampanel, Brivaracetam, Cenobamate (Real Drug-Resistant Focal Epilepsy Trial Data):",
        "epilepsy_status_epilepticus_management": "Status Epilepticus — Real Stepwise Emergency Protocol (RAMPART First-Line, ESETT Second-Line, Third-Line Anesthetic Infusion):",
        "epilepsy_surgery": "Epilepsy Surgery — Real Curative-Intent Option for Well-Localized Drug-Resistant Focal Epilepsy (Wiebe et al NEJM 2001):",
        "epilepsy_neurostimulation_devices": "Neurostimulation — VNS, RNS, and Anterior Thalamic Nucleus DBS (Real SANTE/RNS-Pivotal/VNS Long-Term Data):",
        "epilepsy_ketogenic_diet": "Ketogenic Diet — Real Evidence-Based Non-Pharmacologic Option, Particularly Pediatric Drug-Resistant Epilepsy (Neal et al Lancet Neurology 2008):",
        "epilepsy_neurocysticercosis_specific_management": "Neurocysticercosis-Associated Epilepsy — Real India-Relevant Albendazole + Corticosteroid Treatment (Garcia et al NEJM 2004):",
        "epilepsy_sudep_prevention": "SUDEP Prevention — Real Seizure-Control-Centred Strategy & Nocturnal Supervision:",
        "epilepsy_medical_devices_equipment": "Medical Equipment/Devices — EEG/Video-EEG Monitoring, VNS/RNS/DBS Implantable Devices:",
        "pd_levodopa_carbidopa": "Parkinson's Disease — Levodopa-Carbidopa: Most Effective Symptomatic Therapy, Honeymoon Period and Real Motor-Complication Timeline (ELLDOPA, PD MED, LEAP, Ahlskog & Muenter, STRIDE-PD):",
        "pd_dopamine_agonists": "Parkinson's Disease — Dopamine Agonists (Pramipexole, Ropinirole, Rotigotine) and the Real Impulse-Control-Disorder / Withdrawal / Ergot-Valvulopathy Safety Signals:",
        "pd_mao_b_inhibitors": "Parkinson's Disease — MAO-B Inhibitors (Selegiline, Rasagiline, Safinamide) — Honest Disease-Modification Evidence (DATATOP, TEMPO, ADAGIO):",
        "pd_comt_inhibitors": "Parkinson's Disease — COMT Inhibitors (Entacapone, Opicapone, Tolcapone) for Wearing-Off, Including the STRIDE-PD Early-Start Caution:",
        "pd_amantadine_dyskinesia": "Parkinson's Disease — Amantadine (Immediate- and Extended-Release) for Levodopa-Induced Dyskinesia:",
        "pd_off_episode_rescue_and_other_adjuncts": "Parkinson's Disease — OFF-Episode Rescue and Other Adjuncts (Apomorphine Injection/Sublingual Film, Inhaled Levodopa, Istradefylline):",
        "pd_continuous_infusion_therapies": "Parkinson's Disease — Continuous Infusion Therapies (Intestinal Levodopa Gel, Subcutaneous Foslevodopa-Foscarbidopa, Apomorphine Infusion):",
        "pd_deep_brain_stimulation": "Parkinson's Disease — Deep Brain Stimulation (CSP 468, Deuschl, PD SURG, EARLYSTIM, 10-Year Outcome, Candidate Selection, Adaptive DBS):",
        "pd_acute_akinetic_crisis_phs": "Parkinson's Disease — Acute Akinetic Crisis / Parkinsonism-Hyperpyrexia Syndrome Emergency Management:",
        "pd_non_motor_constipation": "Parkinson's Disease Non-Motor — Constipation (Macrogol, Lubiprostone, Probiotic-Prebiotic Fibre):",
        "pd_non_motor_orthostatic_hypotension": "Parkinson's Disease Non-Motor — Neurogenic Orthostatic Hypotension (Droxidopa, Midodrine, Non-Drug Measures):",
        "pd_non_motor_rbd": "Parkinson's Disease Non-Motor — REM Sleep Behaviour Disorder (Clonazepam, Melatonin, Rivastigmine; AASM 2023 and Real Negative PD Melatonin Trial):",
        "pd_non_motor_psychosis_dementia": "Parkinson's Disease Non-Motor — Psychosis and Dementia (Pimavanserin, Clozapine, Rivastigmine; Avoid Dopamine-Blocking Antipsychotics):",
        "pd_exercise_and_allied_therapy": "Parkinson's Disease — Exercise, Physiotherapy, Tai Chi, Speech (LSVT LOUD) and Occupational Therapy:",
        "pd_secondary_parkinsonism_and_mimics": "Parkinson's Disease — Reversible Mimics: Drug-Induced Parkinsonism (Stop the Drug) and Normal-Pressure Hydrocephalus (Shunt):",
        "pd_disease_modification_evidence": "Parkinson's Disease — Honest Disease-Modification Trial Record (Nothing Proven):",
        "pd_medical_devices_equipment": "Medical Equipment/Devices — DBS Implantable System, Infusion Pumps, Wearable PKG Monitor and Diaries:",
        "ad_cholinesterase_inhibitors": "Alzheimer's Disease — Cholinesterase Inhibitors (Donepezil, Rivastigmine incl. Transdermal Patch, Galantamine) — Real Cochrane-Reviewed Symptomatic Benefit:",
        "ad_nmda_antagonist_memantine": "Alzheimer's Disease — Memantine (NMDA-Receptor Antagonist) Monotherapy and Combination With Donepezil:",
        "ad_anti_amyloid_lecanemab": "Alzheimer's Disease — Anti-Amyloid Monoclonal Antibody: Lecanemab (Leqembi, CLARITY-AD, ARIA/APOE4 Risk, Subcutaneous Autoinjector):",
        "ad_anti_amyloid_donanemab": "Alzheimer's Disease — Anti-Amyloid Monoclonal Antibody: Donanemab (Kisunla, TRAILBLAZER-ALZ 2, ARIA Risk):",
        "ad_anti_amyloid_aducanumab_historical": "Alzheimer's Disease — Aducanumab (Aduhelm): Historical Entry Only, Discontinued 2024:",
        "ad_bpsd_nonpharmacologic_first_line": "Alzheimer's Disease — Behavioural/Psychological Symptoms (BPSD): Non-Drug First-Line Management (the DICE Approach):",
        "ad_bpsd_ssri_management": "Alzheimer's Disease BPSD — SSRIs for Agitation/Depression (CitAD, DIADS-2), Including Real QTc and Efficacy Caveats:",
        "ad_bpsd_antipsychotics": "Alzheimer's Disease BPSD — Antipsychotics for Severe Agitation/Psychosis (Brexpiprazole FDA-Approved; Risperidone Off-Label), Including Real Boxed Mortality Warning:",
        "ad_bpsd_pimavanserin_status": "Alzheimer's Disease BPSD — Pimavanserin: Real, Honest Regulatory Rejection for This Indication:",
        "ad_bpsd_medications_to_avoid": "Alzheimer's Disease — Medications to Actively AVOID (Benzodiazepines, Anticholinergics, Beers Criteria):",
        "ad_sleep_disturbance_management": "Alzheimer's Disease — Sleep Disturbance Management (Suvorexant, Trazodone, Melatonin):",
        "ad_dysphagia_nutrition_aspiration_prevention": "Alzheimer's Disease — Dysphagia, Nutrition and Aspiration-Pneumonia Prevention (Real Feeding-Tube Evidence):",
        "ad_falls_prevention": "Alzheimer's Disease — Falls Prevention (Real, Honestly Modest Exercise-Based Evidence):",
        "ad_delirium_prevention": "Alzheimer's Disease — Delirium Prevention in Hospitalised Patients (Hospital Elder Life Program):",
        "ad_caregiver_support_and_safety_planning": "Alzheimer's Disease — Caregiver Support and Safety Planning (REACH II, Real Caregiver-Burden Data):",
        "ad_advance_care_planning_and_palliative_care": "Alzheimer's Disease — Advance Care Planning, Driving/Legal Capacity and Palliative Care in Advanced Dementia:",
        "ad_failed_or_unproven_treatments": "Alzheimer's Disease — Real Failed or Unproven Treatments (Ginkgo, NSAIDs, Estrogen, Statins, Solanezumab, Gantenerumab, Verubecestat, Semaglutide, Aducanumab):",
        "ad_medical_devices_equipment": "Medical Equipment/Devices — MRI ARIA Surveillance, Infusion Systems, Subcutaneous Autoinjector, APOE Genotyping:",
        "ms_acute_relapse_iv_high_dose_steroids": "Multiple Sclerosis — Acute Relapse Treatment: High-Dose IV/Oral Methylprednisolone (ONTT, COPOUSEP):",
        "ms_acute_relapse_plasma_exchange": "Multiple Sclerosis — Acute Relapse Treatment: Plasma Exchange (PLEX) for Steroid-Refractory Relapses (Weinshenker RCT):",
        "ms_dmt_platform_injectable_interferon_beta": "Multiple Sclerosis — Platform Injectable DMTs: Interferon Beta-1a/1b (IFNB MS Study Group, PRISMS):",
        "ms_dmt_platform_glatiramer_acetate": "Multiple Sclerosis — Platform Injectable DMT: Glatiramer Acetate (Johnson 1995 Pivotal Trial):",
        "ms_dmt_oral_moderate_teriflunomide": "Multiple Sclerosis — Oral Moderate-Efficacy DMT: Teriflunomide (TEMSO, TOWER):",
        "ms_dmt_oral_moderate_dimethyl_fumarate": "Multiple Sclerosis — Oral Moderate-Efficacy DMT: Dimethyl Fumarate (DEFINE, CONFIRM):",
        "ms_dmt_high_efficacy_fingolimod": "Multiple Sclerosis — High-Efficacy DMT: Fingolimod (FREEDOMS, TRANSFORMS):",
        "ms_dmt_high_efficacy_siponimod_spms": "Multiple Sclerosis — High-Efficacy DMT for Active Secondary Progressive MS: Siponimod (EXPAND):",
        "ms_dmt_high_efficacy_ozanimod": "Multiple Sclerosis — High-Efficacy DMT: Ozanimod (SUNBEAM, RADIANCE):",
        "ms_dmt_high_efficacy_natalizumab": "Multiple Sclerosis — High-Efficacy DMT: Natalizumab, Including Real PML/JCV Risk Data (AFFIRM):",
        "ms_dmt_high_efficacy_ocrelizumab": "Multiple Sclerosis — High-Efficacy DMT for RRMS and PPMS: Ocrelizumab (OPERA I/II, ORATORIO):",
        "ms_dmt_high_efficacy_ofatumumab": "Multiple Sclerosis — High-Efficacy DMT: Ofatumumab (ASCLEPIOS I/II):",
        "ms_dmt_high_efficacy_alemtuzumab": "Multiple Sclerosis — High-Efficacy DMT: Alemtuzumab, Including Real Secondary-Autoimmunity Risk (CARE-MS I/II):",
        "ms_dmt_high_efficacy_cladribine": "Multiple Sclerosis — High-Efficacy DMT: Cladribine Tablets (CLARITY):",
        "ms_dmt_offlabel_rituximab_india_access": "Multiple Sclerosis — Off-Label DMT and Real India Cost/Access Alternative: Rituximab:",
        "ms_symptomatic_spasticity": "Multiple Sclerosis Symptomatic Management — Spasticity (Baclofen, Tizanidine, Dantrolene, Nabiximols):",
        "ms_symptomatic_fatigue": "Multiple Sclerosis Symptomatic Management — Fatigue (Real Negative Drug Trial; See Rehabilitation/Exercise for the Real Evidence-Based Option):",
        "ms_symptomatic_bladder_dysfunction": "Multiple Sclerosis Symptomatic Management — Bladder Dysfunction (Antimuscarinics, Mirabegron):",
        "ms_symptomatic_neuropathic_pain_trigeminal_neuralgia": "Multiple Sclerosis Symptomatic Management — Neuropathic Pain and Trigeminal Neuralgia (Carbamazepine, Gabapentin):",
        "ms_symptomatic_walking_impairment": "Multiple Sclerosis Symptomatic Management — Walking Impairment: Dalfampridine (Real Modest Effect Size):",
        "ms_symptomatic_depression": "Multiple Sclerosis Symptomatic Management — Depression (SSRIs):",
        "ms_symptomatic_sexual_dysfunction": "Multiple Sclerosis Symptomatic Management — Sexual Dysfunction (Sildenafil/PDE5 Inhibitors):",
        "ms_rehabilitation_physiotherapy_occupational_therapy": "Multiple Sclerosis — Rehabilitation: Physiotherapy and Occupational Therapy (Real Cochrane-Level Evidence):",
        "ms_rehabilitation_exercise": "Multiple Sclerosis — Rehabilitation: Structured Exercise Programmes (Real Evidence for Fatigue, Mobility, Quality of Life):",
        "ms_pregnancy_and_dmt_safety": "Multiple Sclerosis — Pregnancy and Disease-Modifying Therapy Safety (Real, Drug-Specific Guidance):",
        "ms_vitamin_d_supplementation": "Multiple Sclerosis — Vitamin D Supplementation (Real Equipoise, Not a Proven Disease-Modifying Therapy):",
        "ms_failed_or_unproven_treatments": "Multiple Sclerosis — Real Failed or Unproven Treatments (High-Dose Biotin, Hyperbaric Oxygen):",
        "ms_medical_devices_equipment": "Medical Equipment/Devices — Anti-JCV Antibody Testing, MRI Surveillance, Apheresis, Subcutaneous Autoinjectors, Intrathecal Baclofen Pump:",
        "mig_acute_simple_analgesics_nsaids": "Migraine — Acute Treatment: Simple Analgesics/NSAIDs (Ibuprofen, Naproxen, Aspirin, Diclofenac):",
        "mig_acute_nsaid_triptan_combination": "Migraine — Acute Treatment: Sumatriptan-Naproxen Fixed-Dose Combination (Real Superiority Over Either Monotherapy):",
        "mig_acute_triptans": "Migraine — Acute Treatment: Triptans (Real 53-Trial Ferrari Meta-Analysis & Cardiovascular Contraindications):",
        "mig_acute_antiemetic_adjuncts": "Migraine — Acute Treatment: Antiemetic Adjuncts (Metoclopramide, Prochlorperazine) — Real Direct Headache-Relieving Effect:",
        "mig_acute_gepants": "Migraine — Acute Treatment: Gepants (Ubrogepant/Ubrelvy, Rimegepant/Nurtec) — No Vasoconstriction, Cardiovascular-Disease-Safe:",
        "mig_acute_ditans": "Migraine — Acute Treatment: Ditans (Lasmiditan/Reyvow) — Real Efficacy, Driving-Impairment Caveat & 2026 Market Withdrawal:",
        "mig_acute_ergotamine_dhe": "Migraine — Acute Treatment: Ergotamine & Dihydroergotamine (DHE) — Real Historical/Status-Migrainosus Salvage Option:",
        "mig_medication_overuse_headache_management": "Migraine — Medication-Overuse Headache: Real Withdrawal + Bridge-Therapy Management:",
        "mig_preventive_beta_blockers": "Migraine — Preventive Treatment: Beta-Blockers (Propranolol, Metoprolol) — Real Cochrane-Level Evidence:",
        "mig_preventive_antiepileptics": "Migraine — Preventive Treatment: Antiepileptics (Topiramate & Valproate, incl. Real Valproate Teratogenicity Warning):",
        "mig_preventive_tca_amitriptyline": "Migraine — Preventive Treatment: Tricyclic Antidepressant (Amitriptyline) — Real Consistent Efficacy:",
        "mig_preventive_cgrp_monoclonal_antibodies": "Migraine — Preventive Treatment: CGRP-Targeted Monoclonal Antibodies (Erenumab, Fremanezumab, Galcanezumab, Eptinezumab):",
        "mig_preventive_oral_cgrp_gepants": "Migraine — Preventive Treatment: Oral CGRP Gepants (Atogepant/Qulipta, Rimegepant) — Real Once-Daily/Every-Other-Day Prevention:",
        "mig_preventive_onabotulinumtoxina_chronic": "Migraine — Preventive Treatment: OnabotulinumtoxinA/Botox — Real PREEMPT Data, CHRONIC Migraine Only (Not Episodic):",
        "mig_preventive_candesartan": "Migraine — Preventive Treatment: Candesartan — Real Twice-Replicated Positive Trial Evidence (Tronvik 2003 & 2025):",
        "mig_preventive_flunarizine": "Migraine — Preventive Treatment: Flunarizine — Real Efficacy, Used More Outside the US:",
        "mig_neuromodulation_devices": "Migraine — Neuromodulation Devices: Cefaly, gammaCore, Nerivio (Real FDA-Cleared Trial Evidence):",
        "mig_nondrug_lifestyle_measures": "Migraine — Non-Drug Measures: Sleep Regularity, Hydration & Individualised Trigger Avoidance (Real, Honestly-Graded Evidence):",
        "mig_nondrug_cbt_biofeedback": "Migraine — Non-Drug Measures: Cognitive Behavioural Therapy & Biofeedback:",
        "mig_nondrug_supplements": "Migraine — Non-Drug Measures: Riboflavin, Magnesium & Coenzyme Q10 (Real AAN/AHS Nutraceutical Grading):",
        "mig_nondrug_acupuncture": "Migraine — Non-Drug Measures: Acupuncture (Real Cochrane-Level Evidence):",
        "mig_menstrual_migraine_management": "Migraine — Menstrual Migraine: Perimenstrual Mini-Prophylaxis (Frovatriptan, Naratriptan):",
        "mig_pregnancy_migraine_management": "Migraine — Migraine in Pregnancy: Real Safe Acute & Preventive Options:",
        "gbs_ivig_first_line_acute_treatment": "Guillain-Barré Syndrome — First-Line Acute Treatment: Intravenous Immunoglobulin (IVIG, Dutch GBS Trial):",
        "gbs_plasma_exchange_first_line_acute_treatment": "Guillain-Barré Syndrome — First-Line Acute Treatment: Plasma Exchange (French Cooperative Group):",
        "gbs_combined_ivig_plex_no_added_benefit": "Guillain-Barré Syndrome — Real Trial Finding: Combined IVIG + Plasma Exchange Adds No Benefit (PSGBS Trial):",
        "gbs_second_ivig_course_poor_prognosis_non_responders": "Guillain-Barré Syndrome — Second IVIG Course for Poor-Prognosis Patients: Real Negative/Nuanced Evidence (SID-GBS Trial):",
        "gbs_corticosteroids_real_negative_finding": "Guillain-Barré Syndrome — Corticosteroids: Real Negative Finding (Unlike CIDP):",
        "gbs_investigational_complement_inhibitor_eculizumab": "Guillain-Barré Syndrome — Investigational Therapy: Complement (C5) Inhibitor Eculizumab (Honest Phase 2/Phase 3 Evidence):",
        "gbs_supportive_mechanical_ventilation": "Guillain-Barré Syndrome — Supportive Care: Mechanical Ventilation Criteria & Management:",
        "gbs_supportive_cardiac_autonomic_monitoring": "Guillain-Barré Syndrome — Supportive Care: Cardiac & Autonomic (Dysautonomia) Monitoring:",
        "gbs_supportive_vte_prophylaxis": "Guillain-Barré Syndrome — Supportive Care: Venous Thromboembolism (VTE) Prophylaxis:",
        "gbs_supportive_pain_management": "Guillain-Barré Syndrome — Supportive Care: Pain Management (Gabapentin/Carbamazepine, Not Opioid-First):",
        "gbs_supportive_bowel_bladder_care": "Guillain-Barré Syndrome — Supportive Care: Bowel & Bladder Management:",
        "gbs_rehabilitation_early_physiotherapy": "Guillain-Barré Syndrome — Rehabilitation: Early Physiotherapy & Occupational Therapy:",
        "gbs_medical_devices_equipment": "Medical Equipment/Devices — Apheresis Machines, IVIG Infusion Pumps, Ventilators, Cardiac Telemetry, Spirometers:",
        "mg_symptomatic_acetylcholinesterase_inhibitors": "Myasthenia Gravis — Symptomatic (Not Disease-Modifying): Acetylcholinesterase Inhibitors:",
        "mg_first_line_corticosteroids": "Myasthenia Gravis — Chronic Immunosuppression: First-Line Corticosteroids:",
        "mg_steroid_sparing_azathioprine": "Myasthenia Gravis — Steroid-Sparing Agent: Azathioprine (Best Real RCT Evidence):",
        "mg_steroid_sparing_mycophenolate": "Myasthenia Gravis — Steroid-Sparing Agent: Mycophenolate Mofetil (Real Negative Primary RCT):",
        "mg_steroid_sparing_calcineurin_inhibitors": "Myasthenia Gravis — Steroid-Sparing Agents: Calcineurin Inhibitors (Cyclosporine, Tacrolimus):",
        "mg_curative_thymectomy": "Myasthenia Gravis — Thymectomy (See Curative-Intent Option Above for Full Real MGTX Trial Data):",
        "mg_biologics_complement_inhibitors": "Myasthenia Gravis — Biologics: Terminal Complement (C5) Inhibitors (Eculizumab, Ravulizumab):",
        "mg_biologics_fcrn_antagonists": "Myasthenia Gravis — Biologics: Neonatal Fc-Receptor (FcRn) Antagonists (Efgartigimod, Rozanolixizumab):",
        "mg_biologics_rituximab": "Myasthenia Gravis — Biologic: Rituximab (Particularly Strong Real Evidence in MuSK-MG):",
        "mg_acute_crisis_ivig_plex": "Myasthenia Gravis — Acute Crisis/Rapid Optimization: IVIG and Plasma Exchange:",
        "mg_myasthenic_crisis_ventilatory_support": "Medical Equipment/Devices — Ventilatory Support and Bedside Respiratory Monitoring for Myasthenic Crisis:",
        "mg_drugs_to_avoid_or_use_with_caution": "Myasthenia Gravis — Real Prescribing-Safety Guidance: Medications to Avoid or Use With Caution:",
        "mg_ocular_mg_specific_management": "Myasthenia Gravis — Ocular MG-Specific Management: Generalization-Prevention Corticosteroids:",
        "als_multidisciplinary_clinic_care": "Amyotrophic Lateral Sclerosis — Multidisciplinary ALS Clinic Care: the Single Highest-Value Intervention (Traynor 2003, Rooney 2015, Van den Berg 2005, EAN 2024):",
        "als_riluzole": "Amyotrophic Lateral Sclerosis — Riluzole (Rilutek, Generic Tablets, Tiglutik Suspension, Rilutor in India): Real Modest Survival Benefit (Bensimon 1994, Lacomblez 1996, Cochrane 2012):",
        "als_edaravone": "Amyotrophic Lateral Sclerosis — Edaravone, Intravenous and Oral (Radicava, Radicava ORS): Study 19, Real-World Data and the EMA Withdrawal:",
        "als_sodium_phenylbutyrate_taurursodiol_relyvrio_withdrawn": "Amyotrophic Lateral Sclerosis — Sodium Phenylbutyrate-Taurursodiol (Relyvrio/AMX0035): Historical Entry, Withdrawn After the Failed PHOENIX Trial:",
        "als_tofersen_sod1_als_only": "Amyotrophic Lateral Sclerosis — Tofersen (Qalsody) for SOD1-ALS Only: VALOR Data, Biomarker-Based Accelerated Approval:",
        "als_respiratory_support_niv_and_cough_augmentation": "Amyotrophic Lateral Sclerosis — Respiratory Support: Non-Invasive Ventilation (BiPAP) and Cough Augmentation (Bourke 2006, Cochrane 2017):",
        "als_invasive_ventilation_tracheostomy_and_advance_planning": "Amyotrophic Lateral Sclerosis — Invasive Ventilation via Tracheostomy: Real Outcomes and the Advance-Care-Planning Decision:",
        "als_diaphragm_pacing_real_harm_do_not_use": "Amyotrophic Lateral Sclerosis — Diaphragm Pacing: Real DiPALS Trial Showed Shorter Survival, Do Not Use:",
        "als_nutrition_gastrostomy_peg_and_diet": "Amyotrophic Lateral Sclerosis — Nutrition: Gastrostomy (PEG) Timing Controversy and Hypercaloric Diet Trials (ProGas, LIPCAL-ALS):",
        "als_symptomatic_sialorrhea": "Amyotrophic Lateral Sclerosis Symptomatic Management — Sialorrhea/Drooling (Glycopyrrolate, Amitriptyline, Botulinum Toxin, Radiotherapy):",
        "als_symptomatic_pseudobulbar_affect": "Amyotrophic Lateral Sclerosis Symptomatic Management — Pseudobulbar Affect (Dextromethorphan-Quinidine/Nuedexta):",
        "als_symptomatic_muscle_cramps": "Amyotrophic Lateral Sclerosis Symptomatic Management — Muscle Cramps (Mexiletine, Quinine Sulfate, Baclofen):",
        "als_symptomatic_spasticity": "Amyotrophic Lateral Sclerosis Symptomatic Management — Spasticity (Baclofen, Tizanidine, Gabapentin):",
        "als_symptomatic_pain_mood_sleep_and_other": "Amyotrophic Lateral Sclerosis Symptomatic Management — Pain, Depression, Anxiety, Insomnia, Fatigue, Constipation and Laryngospasm:",
        "als_communication_aac_devices": "Amyotrophic Lateral Sclerosis — Communication Support: AAC Devices, Voice Banking and Eye-Gaze Access:",
        "als_mobility_aids_exercise_and_rehabilitation": "Amyotrophic Lateral Sclerosis — Mobility Aids, Orthoses, Exercise and Physiotherapy:",
        "als_palliative_care_and_advance_care_planning": "Amyotrophic Lateral Sclerosis — Palliative Care and Advance Care Planning (Bede 2011, EAN 2024, Advance-Directive Meta-Analysis):",
        "als_failed_or_unproven_treatments": "Amyotrophic Lateral Sclerosis — Real Failed, Harmful or Unproven Treatments (Minocycline, Lithium, SAR443820, Cell-Based Therapies):",
        "als_medical_devices_equipment": "Medical Equipment/Devices — Home NIV Ventilator, Cough-Assist and Suction, Gastrostomy and Lumbar-Puncture Equipment, AAC and Mobility Equipment:",
        "bm_empiric_therapy_neonates": "Bacterial Meningitis — Empiric Antibiotics, Neonates: Ampicillin plus Gentamicin or Cefotaxime (IDSA 2004, Brouwer 2010):",
        "bm_empiric_therapy_infants_children_adults": "Bacterial Meningitis — Empiric Antibiotics, Infants/Children/Adults: Ceftriaxone or Cefotaxime, plus Vancomycin, plus Ampicillin for Listeria Risk (IDSA 2004, WHO 2025):",
        "bm_empiric_therapy_post_neurosurgical_shunt_trauma_recurrent": "Bacterial Meningitis — Empiric Antibiotics, Post-Neurosurgery/Head Trauma/CSF Shunt: Vancomycin plus Cefepime, Ceftazidime or Meropenem (IDSA 2004, IDSA 2017):",
        "bm_directed_therapy_neisseria_meningitidis": "Bacterial Meningitis — Organism-Directed Therapy: Neisseria meningitidis (Penicillin G/Ampicillin or Ceftriaxone; 5-7 Days):",
        "bm_directed_therapy_streptococcus_pneumoniae": "Bacterial Meningitis — Organism-Directed Therapy: Streptococcus pneumoniae (Susceptibility-Tiered; 10-14 Days):",
        "bm_directed_therapy_haemophilus_influenzae": "Bacterial Meningitis — Organism-Directed Therapy: Haemophilus influenzae (Ampicillin or Ceftriaxone; 7-10 Days):",
        "bm_directed_therapy_listeria_monocytogenes": "Bacterial Meningitis — Organism-Directed Therapy: Listeria monocytogenes (Ampicillin with Optional Gentamicin; 21 Days):",
        "bm_directed_therapy_group_b_streptococcus_gram_negative_staphylococcal": "Bacterial Meningitis — Organism-Directed Therapy: Group B Streptococcus, Gram-Negative Bacilli and Staphylococci:",
        "bm_timing_of_antibiotics_lumbar_puncture_and_imaging": "Bacterial Meningitis — Antibiotic Timing vs Lumbar Puncture and Imaging: Never Delay Antibiotics in an Unstable Patient (Proulx 2005, Hasbun 2001, WHO 2025):",
        "bm_duration_and_response_monitoring": "Bacterial Meningitis — Antibiotic Duration and Response Monitoring (Molyneux 2011, WHO 2025):",
        "bm_adjunctive_dexamethasone": "Bacterial Meningitis — Adjunctive Dexamethasone (de Gans 2002, Cochrane 2015, and Real Neutral/Contested Findings):",
        "bm_adjunctive_therapies_not_supported": "Bacterial Meningitis — Adjuncts That Do Not Work: Glycerol, Induced Hypothermia, Activated Protein C (Real Negative Findings):",
        "bm_fluid_management": "Bacterial Meningitis — Fluid Management: Do Not Routinely Restrict Fluids (Cochrane 2016, WHO 2025):",
        "bm_chemoprophylaxis_meningococcal_contacts": "Bacterial Meningitis — Meningococcal Contact Chemoprophylaxis and Infection Control (Rifampin, Ciprofloxacin, Ceftriaxone):",
        "bm_chemoprophylaxis_haemophilus_influenzae_type_b": "Bacterial Meningitis — Hib Contact Chemoprophylaxis (Rifampin, Red Book 2024):",
        "bm_prevention_vaccination_hib_and_pneumococcal": "Bacterial Meningitis — Primary Prevention by Vaccination: Hib and Pneumococcal Conjugate Vaccines:",
        "bm_prevention_vaccination_meningococcal": "Bacterial Meningitis — Primary Prevention by Vaccination: Meningococcal ACWY, B, A (MenAfriVac) and Men5CV Vaccines:",
        "bm_raised_intracranial_pressure_management": "Bacterial Meningitis — Raised Intracranial Pressure: Mannitol/Hypertonic Saline and ICP-Targeted Neurointensive Care (WHO 2025, Glimaker 2014):",
        "bm_hydrocephalus_management": "Bacterial Meningitis — Hydrocephalus: External Ventricular Drainage and Shunting:",
        "bm_seizure_management": "Bacterial Meningitis — Seizure Management: Benzodiazepines, Fosphenytoin/Phenytoin (AES 2016, WHO 2025):",
        "bm_cerebrovascular_complications_and_focus_control": "Bacterial Meningitis — Cerebral Venous Thrombosis, Vasculopathy and Parameningeal Focus Control (German Guideline 2023):",
        "bm_hearing_screening_and_sequelae_rehabilitation": "Bacterial Meningitis — Hearing Screening, Sequelae Follow-Up and Rehabilitation (WHO 2025):",
        "bm_medical_devices_equipment": "Medical Equipment/Devices — CT/MRI, Lumbar Puncture Set, ICP Monitor and External Ventricular Drain, Ventilator, Audiometry Equipment:",
        "tend_eccentric_loading_exercise_therapy_first_line": "Tendinitis/Tendinopathy — Progressive Heavy-Load/Eccentric Loading Exercise Therapy, Real Closest-to-Cure First-Line Option (Alfredson 1998, Jonsson & Alfredson 2005, Rompe 2007):",
        "tend_nsaids_symptomatic_limited_evidence": "Tendinitis/Tendinopathy — NSAIDs (Oral and Topical), Real but Honestly Limited Evidence for a Degenerative Not Inflammatory Process (Cochrane 2013):",
        "tend_corticosteroid_injection_short_term_relief_long_term_risk": "Tendinitis/Tendinopathy — Corticosteroid Injection, Real Short-Term Relief With Real Documented Worse Long-Term Outcome (Coombes 2010 Lancet, Bisset 2006 BMJ):",
        "tend_prp_injection_mixed_evidence": "Tendinitis/Tendinopathy — Platelet-Rich Plasma (PRP) Injection, Real Mixed Site-Dependent Evidence (Peerbooms 2010/Gosens 2011 Positive for Lateral Epicondylitis, de Vos 2010 JAMA Negative for Achilles):",
        "tend_extracorporeal_shockwave_therapy": "Tendinitis/Tendinopathy — Extracorporeal Shockwave Therapy (ESWT), Real Evidence Comparable to Eccentric Loading (Rompe 2007):",
        "gout_acute_flare_nsaids": "Gout — Acute Flare: NSAIDs (Naproxen, Indomethacin, Etoricoxib; Cochrane 2021, CONTACT, Schumacher 2002):",
        "gout_acute_flare_colchicine": "Gout — Acute Flare: Low-Dose Colchicine, 1.2 mg then 0.6 mg (AGREE Trial, Cochrane 2021):",
        "gout_acute_flare_glucocorticoids": "Gout — Acute Flare: Oral Prednisolone and Intra-Articular/Intramuscular Glucocorticoid (Janssens 2008, Rainer 2016, Xu 2016):",
        "gout_acute_flare_il1_inhibitors": "Gout — Acute Flare: IL-1 Inhibitors, Canakinumab and Anakinra (beta-RELIEVED, anaGO):",
        "gout_acute_flare_adjunct_ice": "Gout — Acute Flare: Topical Ice as an Adjunct (Schlesinger 2002):",
        "gout_ult_treat_to_target_strategy": "Gout — Urate-Lowering Therapy: Treat-to-Target Strategy, Timing and Duration (Doherty 2018, Stamp 2022, Perez-Ruiz 2011, ACR 2020):",
        "gout_ult_allopurinol": "Gout — Allopurinol: Dose Escalation and HLA-B*58:01 Hypersensitivity Screening (Stamp 2017, Hung 2005, Ko 2015):",
        "gout_ult_febuxostat": "Gout — Febuxostat: Efficacy (FACT, APEX, FOCUS) and Cardiovascular Safety (CARES, FAST, FDA Boxed Warning):",
        "gout_ult_uricosurics": "Gout — Uricosurics: Benzbromarone, Probenecid and Lesinurad (Reinders 2009, CLEAR 1/2, CRYSTAL):",
        "gout_ult_refractory_pegloticase": "Gout — Refractory Gout: Pegloticase and Pegloticase With Methotrexate (GOUT1/GOUT2, MIRROR RCT):",
        "gout_investigational_and_regional_agents": "Gout — Investigational and Regional Agents: SEL-212, Pozdeutinurad, Dotinurad (Company-Reported, Not Prescribing Options):",
        "gout_flare_prophylaxis_during_ult_initiation": "Gout — Flare Prophylaxis When Starting Urate-Lowering Therapy: Colchicine, NSAID or Low-Dose Glucocorticoid (Borstad 2004, Wortmann 2010):",
        "gout_lifestyle_diet_measures": "Gout — Diet and Lifestyle With Real Effect Sizes: Weight Loss, Alcohol, Fructose, Purines and Dairy, DASH, Cherries, Vitamin C:",
        "gout_comorbidity_and_drug_interaction_management": "Gout — Comorbidities and Drug Interactions: Losartan, Diuretics, Fenofibrate, SGLT2 Inhibitors, CKD, Azathioprine and Colchicine Interactions:",
        "gout_diagnostic_and_monitoring_devices": "Gout — Diagnostic and Monitoring Tools: Crystal Microscopy, Ultrasound, Dual-Energy CT, Serum Urate Assay:",
        "gout_tophi_and_surgical_care": "Gout — Tophus Care: Medical Dissolution and Surgical Excision (Perez-Ruiz 2002, Kirschenbaum 2022):",
        "gout_india_availability_and_access": "Gout — India Availability and Access (Allopurinol, Febuxostat, Colchicine Brands; Unverified Items Stated):",
        "gout_negative_or_neutral_evidence": "Gout — Negative/Neutral Evidence: Allopurinol for Heart/Kidney Protection Without Gout (ALL-HEART, CKD-FIX), Rilonacept:",
        "bppv_posterior_canal_repositioning_procedures": "BPPV — Posterior-Canal Repositioning Procedures (Epley & Semont) — the Real Procedural Near-Cure:",
        "bppv_horizontal_canal_repositioning_procedures": "BPPV — Horizontal (Lateral) Canal-Specific Repositioning Procedures (Different Canal, Different Maneuver):",
        "bppv_self_administered_habituation_exercises": "BPPV — Self-Administered Habituation Exercises (Real, Honestly Slower Than a Clinician-Performed Maneuver):",
        "bppv_vestibular_suppressant_medications": "BPPV — Vestibular-Suppressant Medications & Adjuncts (Real Symptomatic-Only, NOT Curative of the Underlying Otolith Displacement):",
        "bppv_recurrence_prevention_medicine": "BPPV — Real Medicine-Domain Recurrence-Prevention Intervention (Vitamin D3 Repletion):",
        "ra_strategy_treat_to_target_and_guidelines": "Rheumatoid Arthritis — Treat-to-Target Strategy (TICORA, CAMERA, tREACH, BeSt) and Guidelines (EULAR 2022/2025, ACR 2021):",
        "ra_csdmard_methotrexate": "Rheumatoid Arthritis — Methotrexate, the Anchor Conventional DMARD:",
        "ra_methotrexate_folate_and_safety_monitoring": "Rheumatoid Arthritis — Folic/Folinic Acid and Methotrexate Safety Monitoring:",
        "ra_csdmard_leflunomide": "Rheumatoid Arthritis — Leflunomide:",
        "ra_csdmard_sulfasalazine": "Rheumatoid Arthritis — Sulfasalazine:",
        "ra_csdmard_hydroxychloroquine": "Rheumatoid Arthritis — Hydroxychloroquine (with Retinal Screening):",
        "ra_csdmard_triple_therapy": "Rheumatoid Arthritis — Triple Conventional Therapy (Methotrexate + Sulfasalazine + Hydroxychloroquine):",
        "ra_glucocorticoid_bridging_cobra": "Rheumatoid Arthritis — Glucocorticoid Bridging (COBRA, CAMERA-II, Kirwan 1995):",
        "ra_glucocorticoid_low_dose_gloria_and_safety": "Rheumatoid Arthritis — Long-Term Low-Dose Prednisolone (GLORIA), Glucocorticoid Safety and Bone Protection:",
        "ra_tnf_adalimumab": "Rheumatoid Arthritis — TNF Inhibitor: Adalimumab (and Indian Biosimilars):",
        "ra_tnf_etanercept": "Rheumatoid Arthritis — TNF Inhibitor: Etanercept:",
        "ra_tnf_infliximab": "Rheumatoid Arthritis — TNF Inhibitor: Infliximab:",
        "ra_tnf_certolizumab_pegol": "Rheumatoid Arthritis — TNF Inhibitor: Certolizumab Pegol:",
        "ra_tnf_golimumab": "Rheumatoid Arthritis — TNF Inhibitor: Golimumab:",
        "ra_il6_tocilizumab": "Rheumatoid Arthritis — IL-6 Receptor Blocker: Tocilizumab:",
        "ra_il6_sarilumab": "Rheumatoid Arthritis — IL-6 Receptor Blocker: Sarilumab:",
        "ra_abatacept": "Rheumatoid Arthritis — Abatacept (T-Cell Co-Stimulation Modulator):",
        "ra_rituximab": "Rheumatoid Arthritis — Rituximab (Anti-CD20):",
        "ra_jak_tofacitinib": "Rheumatoid Arthritis — JAK Inhibitor: Tofacitinib:",
        "ra_jak_baricitinib": "Rheumatoid Arthritis — JAK Inhibitor: Baricitinib:",
        "ra_jak_upadacitinib": "Rheumatoid Arthritis — JAK Inhibitor: Upadacitinib:",
        "ra_jak_oral_surveillance_safety_signal_and_regulator_action": "Rheumatoid Arthritis — JAK-Inhibitor Class Safety: ORAL Surveillance, FDA Boxed Warning and EMA Restrictions:",
        "ra_difficult_to_treat_and_switching_strategy": "Rheumatoid Arthritis — Difficult-to-Treat RA and Choosing the Next Drug (ROC Trial):",
        "ra_nsaids_coxibs_symptomatic_only": "Rheumatoid Arthritis — NSAIDs and Coxibs (Symptomatic Only):",
        "ra_biosimilars_and_india_availability_cost": "Rheumatoid Arthritis — Biosimilars and India Availability/Cost (Honest):",
        "ra_drug_free_remission_and_tapering": "Rheumatoid Arthritis — Tapering and Drug-Free Remission:",
        "ra_nondrug_exercise_and_physiotherapy": "Rheumatoid Arthritis — Non-Drug Care: Exercise and Physiotherapy:",
        "ra_nondrug_occupational_therapy_and_hand_exercise": "Rheumatoid Arthritis — Non-Drug Care: Occupational Therapy, Joint Protection and Hand Exercises:",
        "ra_nondrug_patient_education_and_self_management": "Rheumatoid Arthritis — Non-Drug Care: Patient Education and Self-Management:",
        "ra_nondrug_lifestyle_smoking_weight_diet": "Rheumatoid Arthritis — Non-Drug Care: Smoking, Weight and Diet:",
        "ra_surgery_synovectomy_joint_replacement_and_cervical_spine": "Rheumatoid Arthritis — Surgery: Synovectomy, Joint Replacement and Cervical-Spine Fusion:",
        "ra_pretreatment_safety_screening_tb_hbv_vaccination": "Rheumatoid Arthritis — Pre-Treatment Safety Screening: TB, Hepatitis B/C and Vaccination:",
        "ra_pregnancy_and_drug_safety": "Rheumatoid Arthritis — Pregnancy, Lactation and Drug Safety:",
        "ra_failed_or_unproven_treatments": "Rheumatoid Arthritis — Failed, Modest or Unproven Treatments (Honest):",
        "ra_medical_devices_equipment": "Rheumatoid Arthritis — Devices and Equipment (Vagus-Nerve Stimulator, Retinal/Bone Screening, Splints, Prostheses):",
        "psa_strategy_ticopa_grappa_eular": "Psoriatic Arthritis — Domain-Based Treat-to-Target Strategy (TICOPA, GRAPPA 2021, EULAR 2019):",
        "psa_nsaids_symptomatic": "Psoriatic Arthritis — NSAIDs / COX-2 Inhibitors (Symptomatic Only):",
        "psa_csdmard_methotrexate_negative_trial": "Psoriatic Arthritis — Methotrexate: the Real Negative Placebo-Controlled Trial (MIPA) vs SEAM-PsA:",
        "psa_csdmard_leflunomide": "Psoriatic Arthritis — Leflunomide (TOPAS Trial):",
        "psa_csdmard_sulfasalazine": "Psoriatic Arthritis — Sulfasalazine (VA Cooperative Study):",
        "psa_apremilast_oral_pde4_inhibitor": "Psoriatic Arthritis — Apremilast (Otezla), Oral PDE4 Inhibitor (PALACE 1):",
        "psa_tnf_adalimumab": "Psoriatic Arthritis — TNF Inhibitor: Adalimumab (ADEPT):",
        "psa_tnf_etanercept": "Psoriatic Arthritis — TNF Inhibitor: Etanercept (Mease 2000, SEAM-PsA):",
        "psa_tnf_infliximab": "Psoriatic Arthritis — TNF Inhibitor: Infliximab (IMPACT):",
        "psa_tnf_golimumab": "Psoriatic Arthritis — TNF Inhibitor: Golimumab (GO-REVEAL):",
        "psa_tnf_certolizumab_pegol": "Psoriatic Arthritis — TNF Inhibitor: Certolizumab Pegol (RAPID-PsA):",
        "psa_il12_23_ustekinumab": "Psoriatic Arthritis — IL-12/23 Inhibitor: Ustekinumab (PSUMMIT 1 and 2):",
        "psa_il17_secukinumab": "Psoriatic Arthritis — IL-17A Inhibitor: Secukinumab (FUTURE 2 and Pooled FUTURE 2-5):",
        "psa_il17_ixekizumab": "Psoriatic Arthritis — IL-17A Inhibitor: Ixekizumab (SPIRIT-P1, SPIRIT-H2H Head-to-Head vs Adalimumab):",
        "psa_il17af_bimekizumab_and_pasi100_finding": "Psoriatic Arthritis — Dual IL-17A/F Inhibitor: Bimekizumab (BE OPTIMAL, BE COMPLETE) and the Real Near-Complete Skin Clearance (PASI100) Finding:",
        "psa_il23_guselkumab": "Psoriatic Arthritis — IL-23 (p19) Inhibitor: Guselkumab (DISCOVER-2):",
        "psa_il23_risankizumab": "Psoriatic Arthritis — IL-23 (p19) Inhibitor: Risankizumab (KEEPsAKE 1 and 2):",
        "psa_jak_tofacitinib": "Psoriatic Arthritis — JAK Inhibitor: Tofacitinib (OPAL Broaden):",
        "psa_jak_upadacitinib": "Psoriatic Arthritis — JAK Inhibitor: Upadacitinib (SELECT-PsA 1):",
        "psa_glucocorticoid_local_injection": "Psoriatic Arthritis — Local (Intra-Articular/Peri-Entheseal) Glucocorticoid Injection:",
        "psa_biosimilars_and_india_availability": "Psoriatic Arthritis — Biosimilar TNF Inhibitors and India Availability:",
        "psa_nondrug_exercise_lifestyle": "Psoriatic Arthritis — Non-Drug Care: Exercise and Lifestyle (Honest Limited-Evidence Review):",
        "psa_surgery_joint_replacement": "Psoriatic Arthritis — Surgery: Joint Replacement for Erosive Disease:",
        "psa_tb_and_il23_safety_screening": "Psoriatic Arthritis — TB and Hepatitis B/C Screening Before Biologic/JAK Therapy (Including Real IL-23-Inhibitor TB Data):",
        "psa_pregnancy_and_drug_safety": "Psoriatic Arthritis — Pregnancy and Antirheumatic Drug Safety:",
        "psa_failed_or_limited_evidence_treatments": "Psoriatic Arthritis — Honest List of Failed, Negative or Limited-Evidence Treatments:",
        "pso_topical_corticosteroids": "Psoriasis — Topical Corticosteroids (Potent/Superpotent), First-Line for Mild/Limited Disease:",
        "pso_topical_vitamin_d_and_fixed_combination": "Psoriasis — Topical Vitamin D Analogue / Fixed Calcipotriene-Betamethasone Combination:",
        "pso_topical_calcineurin_inhibitors": "Psoriasis — Topical Calcineurin Inhibitors (Tacrolimus), Facial/Intertriginous Disease:",
        "pso_phototherapy_narrowband_uvb": "Psoriasis — Narrowband UVB Phototherapy (Non-Drug):",
        "pso_oral_methotrexate": "Psoriasis — Oral Methotrexate (Real Head-to-Head Data via CHAMPION):",
        "pso_oral_cyclosporine": "Psoriasis — Oral Cyclosporine (Real Rapid-Onset, Not for Long-Term Continuous Use):",
        "pso_oral_apremilast": "Psoriasis — Apremilast (Otezla), Oral PDE4 Inhibitor (ESTEEM 1):",
        "pso_oral_deucravacitinib_tyk2": "Psoriasis — Deucravacitinib (Sotyktu), Oral Selective TYK2 Inhibitor (POETYK PSO-1/PSO-2):",
        "pso_tnf_inhibitors": "Psoriasis — TNF Inhibitors: Adalimumab (CHAMPION) and Etanercept (UNCOVER-3 Active Comparator):",
        "pso_il12_23_ustekinumab": "Psoriasis — IL-12/23 Inhibitor: Ustekinumab (PHOENIX 1):",
        "pso_il17_secukinumab": "Psoriasis — IL-17A Inhibitor: Secukinumab (FIXTURE and ERASURE):",
        "pso_il17_ixekizumab": "Psoriasis — IL-17A Inhibitor: Ixekizumab, Real Head-to-Head Superiority over Etanercept (UNCOVER-2/3):",
        "pso_il17af_bimekizumab_highest_pasi100": "Psoriasis — Dual IL-17A/F Inhibitor: Bimekizumab, the Real Highest Published PASI100 Rate (BE VIVID, BE READY, BE RADIANT, BE SURE):",
        "pso_il23_guselkumab": "Psoriasis — IL-23 (p19) Inhibitor: Guselkumab (VOYAGE 1 and 2):",
        "pso_il23_risankizumab": "Psoriasis — IL-23 (p19) Inhibitor: Risankizumab, Real Durable PASI100 Through 1 Year (UltIMMa-1/2, IMMhance):",
        "pso_il23_tildrakizumab": "Psoriasis — IL-23 (p19) Inhibitor: Tildrakizumab, Real but Comparatively Lower PASI100 (reSURFACE 1 and 2):",
        "ad_eczema_emollients_moisturizers": "Atopic Dermatitis — Emollients/Moisturizers, Foundational Barrier Therapy (Real Negative Evidence for Primary Prevention):",
        "ad_eczema_topical_corticosteroids": "Atopic Dermatitis — Topical Corticosteroids, Potency-Tiered First-Line for Active Flares:",
        "ad_eczema_topical_calcineurin_inhibitors": "Atopic Dermatitis — Topical Calcineurin Inhibitors: Tacrolimus vs Pimecrolimus (Real Head-to-Head Data):",
        "ad_eczema_topical_pde4_crisaborole": "Atopic Dermatitis — Crisaborole (Eucrisa), Topical PDE4 Inhibitor (ISCLA-1/ISCLA-2):",
        "ad_eczema_topical_jak_ruxolitinib": "Atopic Dermatitis — Ruxolitinib Cream (Opzelura), Topical JAK1/JAK2 Inhibitor (TRuE-AD1/TRuE-AD2):",
        "ad_eczema_il4ra_dupilumab": "Atopic Dermatitis — IL-4Rα Blocker: Dupilumab (Dupixent), the Landmark Biologic (SOLO 1/2, CHRONOS):",
        "ad_eczema_il13_tralokinumab": "Atopic Dermatitis — IL-13-Specific Biologic: Tralokinumab (Adbry), (ECZTRA 1/2):",
        "ad_eczema_il13_lebrikizumab": "Atopic Dermatitis — IL-13-Specific Biologic: Lebrikizumab (Ebglyss), (ADvocate 1/2):",
        "ad_eczema_oral_jak_upadacitinib_highest_easi100": "Atopic Dermatitis — Oral JAK1 Inhibitor: Upadacitinib (Rinvoq), the Real Highest Published EASI100 Rate (Measure Up 1/2, AD Up):",
        "ad_eczema_oral_jak_abrocitinib": "Atopic Dermatitis — Oral JAK1 Inhibitor: Abrocitinib (Cibinqo), Real Head-to-Head vs Dupilumab (JADE COMPARE):",
        "ad_eczema_oral_cyclosporine": "Atopic Dermatitis — Oral Cyclosporine, Rapid-Onset, Not for Long-Term Continuous Use:",
        "ihd_p2y12_prasugrel": "P2Y12 Inhibitor — Prasugrel (TRITON-TIMI 38):",
        "ihd_p2y12_clopidogrel_cure": "P2Y12 Inhibitor — Clopidogrel (CURE Trial):",
        "ihd_dapt_duration_strategy": "Dual Antiplatelet Therapy Duration — Standard vs Extended (DAPT Trial, PEGASUS-TIMI 54):",
        "ihd_nonstatin_ldl_lowering": "Non-Statin LDL-Lowering Add-Ons — Ezetimibe, Bempedoic Acid, Inclisiran:",
        "ihd_mra_eplerenone": "Mineralocorticoid Receptor Antagonist — Eplerenone (EPHESUS):",
        "ihd_anticoagulation_compass": "Anticoagulation Add-On — Low-Dose Rivaroxaban + Aspirin (COMPASS):",
        "ihd_fibrinolytics_when_pci_unavailable": "Fibrinolytic Therapy — When Timely Primary PCI Is Unavailable (STREAM):",
        "ihd_diabetes_obesity_cv_outcome_drugs": "Diabetes/Obesity Cardiovascular-Outcome Drugs — SGLT2i and GLP-1 RA in IHD Comorbidity (EMPA-REG, SELECT):",
        "ihd_beta_blocker_reperfusion_era_reassessment": "Real 2024 Reassessment — Beta-Blockers After MI With Preserved Ejection Fraction (REDUCE-AMI):",
        "ihd_plaque_regression_and_near_cure_evidence": "Plaque Regression & Near-Cure Evidence — Real But Modest Coronary Atheroma Shrinkage (GLAGOV, ASTEROID, REVERSAL):",
        "af_dronedarone_athena_pallas": "Atrial Fibrillation — Dronedarone: Real Benefit (ATHENA) vs Real Harm (PALLAS):",
        "af_edoxaban_engage_af": "Atrial Fibrillation — Edoxaban (ENGAGE AF-TIMI 48):",
        "af_rate_control_race2_lenient_vs_strict": "Atrial Fibrillation — Lenient vs Strict Rate Control (RACE II):",
        "af_pill_in_pocket_alboni_trial": "Atrial Fibrillation — 'Pill-in-the-Pocket' Self-Administered Cardioversion (Alboni Trial):",
        "af_dofetilide_diamond_trial": "Atrial Fibrillation — Dofetilide, Mortality-Neutral Rhythm Control (DIAMOND):",
        "af_watchman_5yr_outcomes_protect_af_prevail": "Atrial Fibrillation — Watchman LAAO 5-Year Outcomes (PROTECT AF/PREVAIL):",
        "af_pulsed_field_ablation_advent": "Atrial Fibrillation — Pulsed-Field Ablation vs Thermal Ablation (ADVENT):",
        "af_reversible_causes_hyperthyroidism_osa_alcohol": "Atrial Fibrillation — Reversible-Cause Elimination: Hyperthyroidism, OSA/CPAP, Alcohol Abstinence:",
        "af_digoxin_modern_limited_role": "Atrial Fibrillation — Digoxin, Real Modern Limited Role:",
        "af_residual_stroke_risk_ceiling_and_combination_therapy": "Atrial Fibrillation — The Real Ceiling: Residual Stroke Risk on Optimal Anticoagulation (incl. AFIRE):",
        "af_doac_vs_warfarin_india_access_cost": "Atrial Fibrillation — India-Specific Access/Cost: Warfarin vs DOACs:",
        "hcm_betablockers_pooled_metaanalysis": "HCM — Beta-Blockers: Pooled Real Gradient-Reduction Meta-Analysis (Awad 2025):",
        "hcm_ccb_pooled_metaanalysis": "HCM — Non-Dihydropyridine Calcium-Channel Blockers: Pooled Data & Verapamil Long-Term Follow-Up:",
        "hcm_disopyramide_pooled_and_longterm": "HCM — Disopyramide: Pooled Meta-Analysis & Long-Term (>=5-Year) Outcome Data:",
        "hcm_diuretics_caution_and_nonobstructive_use": "HCM — Diuretics: Real Phenotype-Dependent Use (Nonobstructive vs Obstructive Caution):",
        "hcm_mavacamten_explorer_secondary_and_complete_response": "HCM — Mavacamten: EXPLORER-HCM Secondary Endpoints & the Real 'Complete Response' Rate:",
        "hcm_mavacamten_valor_srt_avoidance": "HCM — Mavacamten: VALOR-HCM Real Reduction in Need for Septal Reduction Therapy:",
        "hcm_aficamten_sequoia_global_efficacy": "HCM — Aficamten: SEQUOIA-HCM 'Global Efficacy' Composite Analysis:",
        "hcm_icd_hcmriskscd_guided_realdata": "HCM — ICD: Real HCM Risk-SCD-Guided Primary-Prevention Event-Reduction Data:",
        "hcm_dual_chamber_pacing_realdata": "HCM — Dual-Chamber (DDD) Pacing: Real, Honestly Limited/Older Evidence:",
        "hcm_genetic_family_cascade_screening_realdata": "HCM — Genetic Testing & Family Cascade Screening: Real Prevention Within Families:",
        "hcm_gene_therapy_and_gene_editing_status": "HCM — Gene Therapy & Gene Editing: Real Early Human Safety Data vs Real Preclinical-Only Data:",
        "as_tavr_by_risk_category": "Aortic Stenosis — TAVR: Real Trial Data by Surgical-Risk Category (PARTNER 3, Evolut Low Risk, PARTNER 2):",
        "as_savr_operative_and_longterm_data": "Aortic Stenosis — SAVR: Real Operative Mortality & Long-Term Survival Data (STS Database):",
        "as_tavr_savr_durability_uncertainty": "Aortic Stenosis — TAVR vs SAVR: Real Long-Term Durability Comparison & Honest Uncertainty in Young/Low-Risk Patients:",
        "as_valve_in_valve_tavr": "Aortic Stenosis — Valve-in-Valve TAVR for Degenerated Bioprosthetic Valve:",
        "as_lpa_investigational_therapy": "Aortic Stenosis — Investigational: Lipoprotein(a)-Lowering Therapy for Calcific AS Progression (Unproven):",
        "pad_voyager_pad_post_revascularization": "Peripheral Artery Disease — Rivaroxaban + Aspirin Post-Revascularization (VOYAGER PAD):",
        "pad_pcsk9_inhibitors_fourier": "Peripheral Artery Disease — PCSK9 Inhibitor: Evolocumab (FOURIER PAD Subgroup):",
        "pad_statin_walking_distance_and_limb_outcomes": "Peripheral Artery Disease — Statins: PAD-Specific Walking-Distance and Limb-Outcome Data:",
        "pad_smoking_cessation_pharmacotherapy": "Peripheral Artery Disease — Smoking-Cessation Pharmacotherapy (EAGLES Trial):",
        "aad_iv_vasodilators_after_betablockade": "Aortic Dissection — IV Vasodilators After Adequate Beta-Blockade (Nicardipine, Sodium Nitroprusside):",
        "aad_pain_control_sympathetic_reduction": "Aortic Dissection — Pain Control as Sympathetic-Surge/BP-HR Adjunct:",
        "aad_type_a_vs_type_b_differential_management": "Type A vs Type B Dissection — Real Differential Management Pathway:",
        "aad_type_b_uncomplicated_medical_therapy_alone": "Uncomplicated Type B Dissection — Medical Therapy Alone vs Early TEVAR (ADSORB Trial):",
        "aad_nonmarfan_betablocker_uk_small_aneurysm_trial": "Chronic AAA — Beta-Blockers (Propranolol): Real Negative UK Small Aneurysm Trial Data:",
        "aad_doxycycline_mmp_inhibition": "Chronic AAA — Doxycycline (MMP Inhibition): Real Negative RCT & Cochrane Review:",
        "aad_marfan_losartan_atenolol_pediatric_and_adult_trials": "Marfan Syndrome — Losartan: Real Head-to-Head (Pediatric) & Add-On (Adult) Trial Data:",
        "aad_evar_vs_open_longterm_outcomes": "AAA Repair — EVAR vs Open: Real Long-Term (14-15 Year) Outcome Data:",
        "aad_ruptured_aaa_improve_rct_vs_registry": "Ruptured AAA — Real RCT (IMPROVE) vs Registry-Derived Outcome Comparison:",
        "aad_size_based_surgical_threshold_guidelines": "Real Guideline Diameter Thresholds for Elective Repair — Rupture Prevention Strategy:",
        "aad_screening_ultrasound_mortality_reduction": "One-Time Ultrasound Screening — Real Mortality-Reduction Trial Data:",
        "oa_guideline_framework_oarsi2019": "Osteoarthritis — OARSI 2019 Guideline Framework: Core Treatments and Where Drugs Fit:",
        "oa_topical_nsaids": "Osteoarthritis — Topical NSAIDs (Diclofenac Gel/Solution, Ketoprofen Gel), First-Line Pharmacological Treatment:",
        "oa_oral_nsaids_coxibs_efficacy": "Osteoarthritis — Oral NSAIDs and COX-2 Inhibitors: Real Efficacy (Network Meta-Analysis):",
        "oa_oral_nsaids_cv_gi_renal_safety": "Osteoarthritis — Oral NSAID/Coxib Cardiovascular, GI and Renal Safety (CNT Collaboration, PRECISION):",
        "oa_paracetamol_acetaminophen": "Osteoarthritis — Paracetamol/Acetaminophen: Honest Evidence of Minimal Benefit:",
        "oa_duloxetine": "Osteoarthritis — Duloxetine (Centrally Acting SNRI for Central-Sensitisation Pain):",
        "oa_ia_corticosteroids": "Osteoarthritis — Intra-Articular Corticosteroid Injection: Real Short-Term Relief, Real Cartilage-Loss Signal:",
        "oa_ia_hyaluronic_acid_viscosupplementation": "Osteoarthritis — Intra-Articular Hyaluronic Acid (Viscosupplementation), Honestly Controversial:",
        "oa_prp_injections": "Osteoarthritis — Platelet-Rich Plasma (PRP) Injections, Mixed/Timepoint-Dependent Evidence:",
        "oa_dmoad_sprifermin": "Osteoarthritis — DMOAD: Sprifermin (Recombinant FGF18), the FORWARD Trial:",
        "oa_dmoad_tanezumab_ngf_inhibitor": "Osteoarthritis — DMOAD: Tanezumab (Anti-NGF Antibody), Real Efficacy vs Real Joint-Destruction Risk:",
        "oa_dmoad_failed_and_investigational_2023_2026": "Osteoarthritis — DMOAD: Lorecivivint and the ADAMTS-5 Inhibitor GLPG1972, Real 2023–2025 Phase 2/3 Failures:",
        "oa_glucosamine_chondroitin": "Osteoarthritis — Glucosamine and Chondroitin Sulfate: Largely Negative Real Evidence:",
        "oa_exercise_therapy": "Osteoarthritis — Land-Based Therapeutic Exercise, Real Guideline-Core Benefit:",
        "oa_weight_loss_diet": "Osteoarthritis — Intensive Diet-Induced Weight Loss Plus Exercise (IDEA Trial):",
        "oa_total_joint_replacement": "Osteoarthritis — Total Knee/Hip Replacement: Real Long-Term Registry Outcome Data:",
        "oa_bracing_and_nondrug_devices": "Osteoarthritis — Valgus Unloader Knee Bracing, Real But Modest Effect:",
        "oa_opioids_not_recommended": "Osteoarthritis — Opioids: Real Evidence the Harm Outweighs the Benefit:",
        "sle_strategy_treat_to_target_eular2023": "Systemic Lupus Erythematosus — EULAR 2023 Treat-to-Target Strategy (Remission/LLDAS):",
        "sle_hydroxychloroquine_foundational_therapy": "Systemic Lupus Erythematosus — Hydroxychloroquine, the Foundational Therapy (LUMINA/SLICC Data):",
        "sle_hydroxychloroquine_retinal_toxicity_monitoring": "Systemic Lupus Erythematosus — Hydroxychloroquine Retinal Toxicity Monitoring (AAO 2016):",
        "sle_glucocorticoids_minimal_dose_strategy": "Systemic Lupus Erythematosus — Glucocorticoids: Real Efficacy vs Real Dose-Dependent Damage:",
        "sle_immunosuppressant_methotrexate": "Systemic Lupus Erythematosus — Methotrexate (Non-Renal, Non-CNS Disease):",
        "sle_immunosuppressant_azathioprine": "Systemic Lupus Erythematosus — Azathioprine (Maintenance, Pregnancy-Compatible):",
        "sle_immunosuppressant_mycophenolate_mofetil_lupus_nephritis": "Systemic Lupus Erythematosus — Mycophenolate Mofetil for Lupus Nephritis (ALMS Trial):",
        "sle_immunosuppressant_cyclophosphamide_euro_lupus": "Systemic Lupus Erythematosus — Cyclophosphamide, the Euro-Lupus Low-Dose Regimen:",
        "sle_biologic_belimumab": "Systemic Lupus Erythematosus — Belimumab, Non-Renal Disease (BLISS-52/BLISS-76):",
        "sle_biologic_belimumab_lupus_nephritis_bliss_ln": "Systemic Lupus Erythematosus — Belimumab in Lupus Nephritis (BLISS-LN):",
        "sle_biologic_anifrolumab": "Systemic Lupus Erythematosus — Anifrolumab (TULIP-1 Negative, TULIP-2 Positive):",
        "sle_biologic_rituximab_mixed_evidence": "Systemic Lupus Erythematosus — Rituximab: Real Negative RCTs vs Real Off-Label Use (EXPLORER/LUNAR):",
        "sle_calcineurin_inhibitor_voclosporin": "Systemic Lupus Erythematosus — Voclosporin for Lupus Nephritis (AURORA 1):",
        "sle_emerging_car_t_cell_therapy": "Systemic Lupus Erythematosus — Investigational CD19 CAR T-Cell Therapy (Real Drug-Free-Remission Signal):",
        "sle_antiphospholipid_syndrome_anticoagulation": "Systemic Lupus Erythematosus — Antiphospholipid-Syndrome-Associated Anticoagulation (Warfarin vs DOACs):",
        "sle_pregnancy_medication_safety": "Systemic Lupus Erythematosus — Medication Safety in Pregnancy and Lactation:",
        "hiv_art_first_line_medicines": "First-Line Antiretroviral Therapy (ART) — Integrase-Inhibitor-Based Single-Tablet Regimens:",
        "hiv_art_long_acting_injectable_medicines": "Long-Acting Injectable ART — Cabotegravir + Rilpivirine (Cabenuva), Treatment (Not Prevention):",
        "hiv_prep_pep_medicines": "Pre-Exposure Prophylaxis (PrEP) & Post-Exposure Prophylaxis (PEP) — Real Prevention Efficacy Data:",
        "hiv_mtct_prevention_medicines": "Prevention of Mother-to-Child Transmission (PMTCT):",
        "hiv_opportunistic_infection_prophylaxis_medicines": "Opportunistic Infection (OI) Prophylaxis by CD4 Threshold:",
        "hiv_cure_research_medicines": "Cure-Research Frontier — Latency Reversal, Gene Editing, Broadly Neutralising Antibodies (Investigational, Not Yet Curative):",
        "bc_hr_positive_endocrine_therapy": "Breast Cancer — Hormone-Receptor-Positive Disease: Endocrine Therapy (Tamoxifen, Aromatase Inhibitors):",
        "bc_hr_positive_cdk46_inhibitors": "Breast Cancer — Hormone-Receptor-Positive Disease: CDK4/6 Inhibitors (Adjuvant and Metastatic):",
        "bc_her2_positive_targeted_therapy": "Breast Cancer — HER2-Positive Disease: HER2-Targeted Therapy (Trastuzumab, Pertuzumab, T-DM1, Trastuzumab Deruxtecan):",
        "bc_triple_negative_chemo_immunotherapy": "Breast Cancer — Triple-Negative Disease: Chemotherapy Backbone + Immunotherapy (KEYNOTE-522):",
        "bc_parp_inhibitors_brca_mutated": "Breast Cancer — Germline BRCA-Mutated Disease: PARP Inhibitors (Adjuvant and Metastatic):",
        "bc_chemo_de_escalation_oncotype_dx": "Breast Cancer — Genomic-Test-Guided Chemotherapy De-Escalation (Oncotype DX / TAILORx):",
        "bc_surgery_radiation_early_stage": "Breast Cancer — Curative-Intent Surgery + Radiotherapy, Early-Stage Disease:",
        "bc_brca_risk_reducing_options": "Breast Cancer — Real Risk-Reducing Options for BRCA1/2 Mutation Carriers:",
        "mdd_strategy_stepped_sequential_care_stard": "Major Depressive Disorder — Sequential Stepped Care Strategy (STAR*D Cumulative Remission):",
        "mdd_ssri_snri_bupropion_mirtazapine_comparative_cipriani2018": "Major Depressive Disorder — SSRIs/SNRIs/Bupropion/Mirtazapine, Real Comparative Efficacy (Cipriani 2018 Network Meta-Analysis):",
        "mdd_ssri_switch_and_augmentation_stard_level2": "Major Depressive Disorder — Switch vs Augmentation After First SSRI Failure (STAR*D Level 2):",
        "mdd_atypical_antipsychotic_augmentation_treatment_resistant": "Major Depressive Disorder — Atypical Antipsychotic Augmentation (Aripiprazole and Related Agents), Treatment-Resistant Depression:",
        "mdd_esketamine_treatment_resistant_depression": "Major Depressive Disorder — Intranasal Esketamine (Spravato), Treatment-Resistant Depression:",
        "mdd_iv_ketamine_off_label": "Major Depressive Disorder — Off-Label IV Ketamine Infusion, Treatment-Resistant Depression:",
        "mdd_psilocybin_assisted_therapy_investigational": "Major Depressive Disorder — Psilocybin-Assisted Therapy (Investigational, Not FDA-Approved):",
        "mdd_electroconvulsive_therapy": "Major Depressive Disorder — Electroconvulsive Therapy (ECT), Severe/Treatment-Resistant Depression:",
        "mdd_repetitive_transcranial_magnetic_stimulation": "Major Depressive Disorder — Repetitive Transcranial Magnetic Stimulation (rTMS), FDA-Cleared:",
        "mdd_cbt_plus_medication_combination": "Major Depressive Disorder — Combining CBT with Antidepressant Medication vs Either Alone:",
        "gad_ssri_escitalopram": "Generalized Anxiety Disorder — SSRI: Escitalopram (Real Placebo-Controlled Trial):",
        "gad_ssri_paroxetine": "Generalized Anxiety Disorder — SSRI: Paroxetine (Real Response and True Remission Data):",
        "gad_ssri_sertraline": "Generalized Anxiety Disorder — SSRI: Sertraline (Real Placebo-Controlled Trial):",
        "gad_snri_venlafaxine_xr": "Generalized Anxiety Disorder — SNRI: Venlafaxine Extended-Release:",
        "gad_snri_duloxetine": "Generalized Anxiety Disorder — SNRI: Duloxetine (Real Pooled Analysis):",
        "gad_buspirone_azapirone": "Generalized Anxiety Disorder — Buspirone/Azapirones (Real Cochrane Systematic Review):",
        "gad_pregabalin": "Generalized Anxiety Disorder — Pregabalin (Real Updated Meta-Analysis):",
        "gad_cbt_psychotherapy": "Generalized Anxiety Disorder — Cognitive Behavioral Therapy (Acute Efficacy, Comparison to Medication, and Real Long-Term Durability):",
        "gad_escitalopram_long_term_relapse_prevention": "Generalized Anxiety Disorder — Escitalopram Continuation Therapy, Real Long-Term Relapse Prevention:",
        "gad_benzodiazepine_caution": "Generalized Anxiety Disorder — Benzodiazepines: Real Rapid Relief but Real Guideline Caution Against Long-Term Use:",
        "gad_beta_blocker_limited_role": "Generalized Anxiety Disorder — Beta-Blockers: Real, Honestly Limited Role (Performance/Situational Anxiety, Not True GAD):",
        "adhd_stimulant_methylphenidate": "Attention-Deficit/Hyperactivity Disorder — Stimulant: Methylphenidate (Real Cochrane Review and Head-to-Head Trial):",
        "adhd_stimulant_amphetamine": "Attention-Deficit/Hyperactivity Disorder — Stimulant: Amphetamine-Based (Lisdexamfetamine/Mixed Amphetamine Salts):",
        "adhd_nonstimulant_atomoxetine": "Attention-Deficit/Hyperactivity Disorder — Non-Stimulant: Atomoxetine (Real Placebo-Controlled and Head-to-Head Trial Data):",
        "adhd_nonstimulant_guanfacine_clonidine": "Attention-Deficit/Hyperactivity Disorder — Non-Stimulant: Guanfacine Extended-Release and Clonidine:",
        "adhd_behavioral_parent_training": "Attention-Deficit/Hyperactivity Disorder — Behavioral Parent Training / Intensive Behavioral Treatment (Real MTA Trial Data):",
        "pand_cbt_interoceptive_exposure_arntz2002": "Panic Disorder — Cognitive Therapy vs Interoceptive Exposure, Real Randomized Trial (Arntz 2002):",
        "pand_cbt_component_craske1997": "Panic Disorder — Interoceptive Exposure vs Breathing Retraining Within CBT, Real Component RCT (Craske 1997):",
        "pand_cbt_plus_medication_barlow2000": "Panic Disorder — CBT, Imipramine, or Their Combination, Real NIMH Multi-Site RCT (Barlow 2000):",
        "pand_ssri_paroxetine_ballenger1998": "Panic Disorder — SSRI: Paroxetine, Real Double-Blind Fixed-Dose Trial (Ballenger 1998):",
        "pand_ssri_sertraline_pollack1998": "Panic Disorder — SSRI: Sertraline, Real Flexible-Dose Multicenter Trial (Pollack 1998):",
        "pand_snri_venlafaxine_bradwejn2005": "Panic Disorder — SNRI: Venlafaxine Extended-Release, Real Placebo-Controlled Trial (Bradwejn 2005):",
        "pand_benzodiazepine_alprazolam_ballenger1988": "Panic Disorder — Benzodiazepine: Alprazolam, Real Rapid Relief, Large Multicenter Trial (Ballenger 1988, Cross-National 1992):",
        "pand_benzodiazepine_discontinuation_cbt_otto1993": "Panic Disorder — CBT for Benzodiazepine Discontinuation, Real Controlled Trial (Otto 1993):",
        "pand_pharmacotherapy_network_meta_cochrane2023": "Panic Disorder — Pharmacological Treatments, Real Cochrane Network Meta-Analysis (Guaiana 2023):",
        "pand_cbt_vs_pharmacotherapy_mitte2005": "Panic Disorder — CBT vs Pharmacotherapy, Real Comparative Meta-Analysis (Mitte 2005):",
        "pand_cognitive_therapy_vs_relaxation_clark1994": "Panic Disorder — Cognitive Therapy vs Applied Relaxation vs Imipramine, Real Comparative RCT (Clark 1994):",
        "pand_combined_therapy_cochrane_furukawa2007": "Panic Disorder — Combined Psychotherapy Plus Antidepressants, Real Cochrane Systematic Review (Furukawa 2007):",
        "pand_ssri_vs_tca_meta_bakker2002": "Panic Disorder — SSRIs vs TCAs, Real Meta-Analysis (Bakker 2002):",
        "agor_cbt_exposure_therapy_in_vivo_interoceptive": "Agoraphobia — Cognitive Behavioral Therapy with In-Vivo and Interoceptive Exposure (First-Line):",
        "agor_cbt_plus_medication_combination": "Agoraphobia — Combining CBT (Exposure-Based) with an Antidepressant vs Either Alone (NIMH Collaborative Trial):",
        "agor_ssri_paroxetine": "Agoraphobia — SSRI: Paroxetine (Real Placebo-Controlled Trial):",
        "agor_ssri_sertraline": "Agoraphobia — SSRI: Sertraline (Real Placebo-Controlled Trials):",
        "agor_snri_venlafaxine_er": "Agoraphobia — SNRI: Venlafaxine Extended-Release:",
        "agor_pharmacotherapy_network_meta_analysis_cochrane": "Agoraphobia — Pharmacological Treatments, Real Comparative Network Meta-Analysis (Cochrane 2023):",
        "agor_psychological_therapies_network_meta_analysis_cochrane": "Agoraphobia — Psychological Therapies, Real Comparative Network Meta-Analyses (Cochrane 2016 / 2022):",
        "agor_cbt_vs_pharmacotherapy_comparative_mitte2005": "Agoraphobia — CBT vs Pharmacotherapy vs Combination, Real Head-to-Head Meta-Analysis (Mitte 2005):",
        "agor_benzodiazepine_caution": "Agoraphobia — Benzodiazepines: Real Rapid Relief but Real Guideline Caution Against Long-Term Use:",
        "scz_first_generation_and_second_generation_antipsychotics_catie": "Schizophrenia — First- vs Second-Generation Antipsychotics, Real Comparative Effectiveness (CATIE Trial, Leucht 2009 Meta-Analysis):",
        "scz_clozapine_treatment_resistant_schizophrenia": "Schizophrenia — Clozapine for Treatment-Resistant Schizophrenia (Real Pivotal RCT and Real-World TRS Prevalence):",
        "scz_ect_augmentation_clozapine_resistant": "Schizophrenia — Electroconvulsive Therapy (ECT) Augmentation of Clozapine, Clozapine-Resistant Schizophrenia:",
        "scz_long_acting_injectable_antipsychotics": "Schizophrenia — Long-Acting Injectable (LAI) Antipsychotics, Real Relapse-Prevention Evidence:",
        "scz_xanomeline_trospium_cobenfy_novel_mechanism": "Schizophrenia — Xanomeline-Trospium (Cobenfy), Real First New-Mechanism Antipsychotic in Decades (FDA-Approved 2024):",
        "scz_cbt_and_coordinated_specialty_care_psychosocial": "Schizophrenia — CBT for Psychosis and Coordinated Specialty Care (NAVIGATE/RAISE-ETP), Real Adjunctive Evidence:",
        "sad_paliperidone_pivotal_registration_trials": "Schizoaffective Disorder — Paliperidone Extended-Release, Real Pivotal Registration Trials (First-Ever FDA Approval Specifically for Schizoaffective Disorder):",
        "sad_paliperidone_palmitate_relapse_prevention": "Schizoaffective Disorder — Paliperidone Palmitate Once-Monthly, Real Pivotal Relapse-Prevention RCT (Fu 2015):",
        "sad_other_second_generation_antipsychotics": "Schizoaffective Disorder — Other Second-Generation Antipsychotics (Risperidone), Real Honestly Mixed Head-to-Head Evidence:",
        "sad_mood_stabilizers_bipolar_type": "Schizoaffective Disorder — Lithium/Valproate for Bipolar-Type Presentation, Real Cochrane Meta-Analytic Signal:",
        "sad_antidepressants_depressive_type": "Schizoaffective Disorder — Antidepressant Add-On for Depressive-Type Presentation, Real Meta-Analytic Evidence:",
        "sad_clozapine_treatment_resistant": "Schizoaffective Disorder — Clozapine for Treatment-Resistant Illness, Real Naturalistic and Randomized Add-On Evidence:",
        "sad_cbt_and_psychosocial_adjunct": "Schizoaffective Disorder — CBT for Psychosis, Real Adjunctive Evidence (Extrapolated From Schizophrenia Trials):",
        "bd_lithium_maintenance_relapse_prevention": "Bipolar Disorder — Lithium, Gold-Standard Maintenance Relapse Prevention:",
        "bd_lithium_anti_suicide_effect": "Bipolar Disorder — Lithium, Real Distinctive Anti-Suicide Effect:",
        "bd_valproate_divalproex_acute_mania": "Bipolar Disorder — Valproate/Divalproex, Acute Mania:",
        "bd_lamotrigine_bipolar_depression_and_maintenance": "Bipolar Disorder — Lamotrigine, Bipolar Depression & Maintenance (Not Acute Mania):",
        "bd_carbamazepine_acute_mania": "Bipolar Disorder — Carbamazepine (Extended-Release), Acute Mania:",
        "bd_quetiapine_bipolar_depression_and_mania": "Bipolar Disorder — Quetiapine, Real Dual Efficacy for Both Mania and Depression:",
        "bd_atypical_antipsychotics_comparative_acute_mania": "Bipolar Disorder — Atypical Antipsychotics for Acute Mania, Real Comparative Efficacy:",
        "bd_aripiprazole_mania_head_to_head_trial": "Bipolar Disorder — Aripiprazole, Head-to-Head Trial vs Lithium and Placebo (Acute Mania):",
        "bd_lurasidone_bipolar_depression": "Bipolar Disorder — Lurasidone, FDA-Approved for Bipolar Depression (PREVAIL-1):",
        "bd_cariprazine_bipolar_depression": "Bipolar Disorder — Cariprazine, FDA-Approved for Bipolar Depression:",
        "bd_lithium_valproate_combination_therapy": "Bipolar Disorder — Lithium Plus Valproate Combination Therapy (BALANCE Trial):",
        "bd_antidepressants_bipolar_depression_caution": "Bipolar Disorder — Antidepressants in Bipolar Depression, Real Caution and Manic-Switch Risk:",
        "bd_electroconvulsive_therapy": "Bipolar Disorder — Electroconvulsive Therapy (ECT), Severe/Treatment-Resistant Episodes:",
        "crc_adjuvant_chemotherapy_stage3": "Colorectal Cancer — Adjuvant Chemotherapy, Stage III Disease (FOLFOX, Real Durable 10-Year Benefit):",
        "crc_adjuvant_chemotherapy_stage2_controversy": "Colorectal Cancer — Adjuvant Chemotherapy, Stage II Disease (Real, Honestly Marginal/Controversial Benefit):",
        "crc_metastatic_targeted_therapy_anti_vegf": "Metastatic Colorectal Cancer — Anti-VEGF Targeted Therapy (Bevacizumab):",
        "crc_metastatic_targeted_therapy_anti_egfr": "Metastatic Colorectal Cancer — Anti-EGFR Targeted Therapy (Cetuximab/Panitumumab, RAS-Status-Dependent):",
        "crc_metastatic_immunotherapy_msi_high": "Metastatic Colorectal Cancer — Immunotherapy, MSI-High/dMMR Biomarker-Defined Subgroup (Pembrolizumab):",
        "crc_metastatic_her2_targeted_therapy": "Metastatic Colorectal Cancer — HER2-Targeted Therapy (HER2-Amplified, RAS-Wild-Type Subgroup):",
        "crc_metastatic_braf_targeted_therapy": "Metastatic Colorectal Cancer — BRAF-Targeted Therapy (BRAF V600E-Mutant Subgroup):",
        "crc_screening_and_surgical_procedures": "Colorectal Cancer — Screening/Prevention and Curative-Intent Surgical Procedures (Polypectomy, Resection, Liver Metastasectomy):",
        "sep_empiric_broad_spectrum_antibiotics_timing": "Sepsis/Septic Shock — Immediate Empiric Broad-Spectrum Antibiotics, Within 1 Hour of Recognition (SSC 2026):",
        "sep_time_to_antibiotics_mortality_evidence": "Sepsis/Septic Shock — Time-to-Antibiotic Mortality Evidence (Kumar 2006, Seymour 2017, Freund 2025):",
        "sep_antimicrobial_deescalation_and_duration": "Sepsis/Septic Shock — Antimicrobial De-Escalation and Shortened Duration (SSC 2026):",
        "sep_iv_fluid_resuscitation": "Sepsis/Septic Shock — IV Crystalloid Fluid Resuscitation, 30 mL/kg Then Individualised (Real EGDT-to-Individualised Evolution):",
        "sep_vasopressors_norepinephrine_first_line": "Sepsis/Septic Shock — Norepinephrine as First-Line Vasopressor (vs Dopamine, SOAP II):",
        "sep_vasopressors_vasopressin_second_line": "Sepsis/Septic Shock — Vasopressin as Second-Line Vasopressor Add-On (VASST):",
        "sep_corticosteroids_hydrocortisone_refractory_shock": "Sepsis/Septic Shock — Hydrocortisone for Refractory Shock (Honestly Conflicting ADRENAL vs APROCCHSS):",
        "sep_source_control": "Sepsis/Septic Shock — Source Control: Drainage, Debridement or Device Removal (AbSeS Study):",
        "sep_lactate_and_perfusion_guided_resuscitation": "Sepsis/Septic Shock — Serial Lactate and Capillary-Refill-Time-Guided Resuscitation:",
        "sep_drotrecogin_alfa_xigris_withdrawn": "Sepsis/Septic Shock — Drotrecogin Alfa (Xigris), Real Failure and Market Withdrawal (Cautionary Tale):",
        "sep_bundle_compliance_and_hour1_bundle_evidence": "Sepsis/Septic Shock — Bundle-Compliance Mortality Data, Real but Honestly Contested:",
        "sep_medical_devices_equipment": "Medical Equipment/Devices — Central/Arterial Catheters, Infusion Pumps, Ventilator, Renal Replacement Therapy:",
        "chlam_doxycycline_first_line": "Chlamydia — Doxycycline 100 mg PO Twice Daily x7 Days (CDC 2021 First-Line, All Sites):",
        "chlam_azithromycin_single_dose": "Chlamydia — Azithromycin 1 g PO Single Dose (Real, Effective Alternative):",
        "chlam_alternative_regimen_levofloxacin": "Chlamydia — Levofloxacin 500 mg PO Once Daily x7 Days (Alternative Regimen):",
        "chlam_amoxicillin_and_azithromycin_pregnancy": "Chlamydia in Pregnancy — Azithromycin (Recommended) / Amoxicillin (Alternative):",
        "chlam_partner_treatment_expedited_partner_therapy": "Chlamydia — Expedited Partner Therapy (Reinfection Prevention):",
        "chlam_test_of_cure_and_retesting": "Chlamydia — Post-Treatment Retesting at ~3 Months (Real, Non-Curative but Guideline-Critical):",
        "chlam_screening_program_pid_prevention": "Chlamydia — Population Screening Programs (Pelvic Inflammatory Disease Prevention):",
        "uti_first_line_regimens_uncomplicated_cystitis": "UTI — First-Line Regimens for Uncomplicated Cystitis:",
        "uti_beta_lactam_regimens_generally_less_effective": "UTI — Beta-Lactam Regimens (Generally Less Effective):",
        "uti_fluoroquinolone_regimens": "UTI — Fluoroquinolone Regimens (Reserve/Second-Line):",
        "uti_pyelonephritis_regimens": "UTI — Pyelonephritis Regimens:",
        "uti_recurrent_uti_prevention": "UTI — Recurrent UTI Prevention:",
        "uti_vaccines": "UTI — Vaccines (Preventive, Real Evidence):",
        "uti_catheter_associated_uti_cauti_management_other": "UTI — Catheter-Associated UTI (CAUTI) Management:",
        "lep_who_mdt_paucibacillary": "Leprosy — WHO Paucibacillary (PB) MDT, 6-Month Rifampicin+Dapsone (Curative):",
        "lep_who_mdt_multibacillary": "Leprosy — WHO Multibacillary (MB) MDT, 12-Month Rifampicin+Dapsone+Clofazimine (Curative):",
        "lep_uniform_mdt_investigational": "Leprosy — Investigational Uniform 6-Month MDT (U-MDT, Not Yet WHO Global Default):",
        "lep_post_exposure_chemoprophylaxis": "Leprosy — Single-Dose Rifampicin (SDR) Post-Exposure Prophylaxis for Contacts:",
        "lep_type1_reversal_reaction_management": "Leprosy Reactions — Type 1 (Reversal) Reaction Management (Corticosteroids):",
        "lep_type2_enl_management": "Leprosy Reactions — Type 2/ENL Management (Thalidomide, Clofazimine):",
        "lep_rehabilitation_and_reconstructive_surgery_other": "Leprosy — Physiotherapy & Reconstructive Surgery for Established Nerve Damage (Not a Cure of the Infection):",
        "lep_bcg_vaccination_prevention": "Leprosy — BCG Vaccination (Partial Cross-Protective Prevention):",
        "apl_atra_ato_chemotherapy_free_regimen": "APL — ATRA + Arsenic Trioxide, Real Chemotherapy-Free Curative Regimen (Low/Intermediate-Risk):",
        "apl_atra_anthracycline_chemotherapy_high_risk": "APL — ATRA + Anthracycline (+/- Cytarabine/Arsenic Trioxide) Chemotherapy (High-Risk):",
        "apl_differentiation_syndrome_management": "APL — Differentiation Syndrome Management (Dexamethasone, Real Non-Curative but Essential):",
        "apl_relapsed_refractory_ato_salvage": "APL — Arsenic Trioxide-Based Salvage (Relapsed/Refractory):",
        "apl_coagulopathy_supportive_care_other": "APL — Coagulopathy/DIC Correction (Emergency-Phase Supportive Care):",
        "cml_imatinib_first_generation_tki": "CML — Imatinib, Real First-in-Class BCR-ABL1 Tyrosine Kinase Inhibitor (Real IRIS Trial Long-Term Flagship Result):",
        "cml_dasatinib_second_generation_tki": "CML — Dasatinib, Real Second-Generation TKI (Real First-Line Alternative & Post-Imatinib Second-Line):",
        "cml_nilotinib_second_generation_tki": "CML — Nilotinib, Real Second-Generation TKI (Real First-Line Alternative & Post-Imatinib Second-Line):",
        "cml_bosutinib_second_generation_tki": "CML — Bosutinib, Real Second-Generation TKI (Real First-Line Alternative & Post-Imatinib Second-Line):",
        "cml_ponatinib_third_generation_t315i": "CML — Ponatinib, Real Third-Generation TKI (Real T315I-Mutant & Multi-Resistant Disease):",
        "cml_asciminib_stamp_inhibitor": "CML — Asciminib, Real Novel Allosteric STAMP Inhibitor (Real Heavily Pretreated/Resistant Disease):",
        "cml_treatment_free_remission_tki_discontinuation": "CML — Treatment-Free Remission: Real TKI Discontinuation in Deep, Sustained Molecular Responders:",
        "cml_allogeneic_stem_cell_transplant_resistant_blast_crisis": "CML — Allogeneic Stem Cell Transplant, Real Lower-Priority Option for TKI-Resistant/Blast-Crisis Disease:",
        "giar_tinidazole_single_dose": "Giardiasis — Tinidazole Single Oral Dose (Real Highest Single-Dose Cure Rate):",
        "giar_metronidazole_5to7day_course": "Giardiasis — Metronidazole 5-7 Day Course (Real Classic First-Line):",
        "giar_nitazoxanide_3day_course": "Giardiasis — Nitazoxanide 3-Day Course (Broader-Spectrum, Pediatric-Friendly):",
        "giar_albendazole": "Giardiasis — Albendazole 400 mg Once Daily x5 Days (Equivalent Efficacy, Fewer Side Effects):",
        "giar_nitroimidazole_refractory_giardiasis": "Giardiasis — Real, Growing Nitroimidazole-Refractory Disease (Combination/Quinacrine Salvage Ladder):",
        "giar_other_second_line_agents": "Giardiasis — Other Second-Line Agents (Furazolidone, Paromomycin, Neomycin):",
        "giar_household_contact_treatment_consideration": "Giardiasis — Household/Close-Contact Management (Lower-Priority, Evidence-Limited):",
        "amoeb_metronidazole_tissue_active": "Amoebiasis -- Metronidazole (Real Classic First-Line Tissue-Active Agent):",
        "amoeb_tinidazole_tissue_active": "Amoebiasis -- Tinidazole (Real Cochrane-Superior Alternative Tissue-Active Agent):",
        "amoeb_paromomycin_luminal": "Amoebiasis -- Paromomycin (Real Preferred Luminal Cyst-Eradicating Agent):",
        "amoeb_diloxanide_furoate_luminal": "Amoebiasis -- Diloxanide Furoate (Real Alternative Luminal Agent, Precise US CDC Cure-Rate Data):",
        "amoeb_iodoquinol_luminal_alternative": "Amoebiasis -- Iodoquinol (Real, Less-Preferred Luminal Alternative):",
        "amoeb_nitazoxanide_broad_spectrum_alternative": "Amoebiasis -- Nitazoxanide (Real Broader-Spectrum Alternative, Intestinal Disease and Liver Abscess Trial Data):",
        "amoeb_amoebic_liver_abscess_specific_management": "Amoebiasis -- Amoebic Liver Abscess-Specific Management (Real Medicine-First, Drainage Reserved-Only):",
        "amoeb_asymptomatic_cyst_passer_management": "Amoebiasis -- Confirmed Asymptomatic E. histolytica Cyst-Passer Management (Real Luminal-Agent-Alone Pathway):",
        "trich_metronidazole_7day_women": "Trichomoniasis — Metronidazole 7-Day Course (Real CDC 2021-Preferred First-Line for Women):",
        "trich_metronidazole_single_dose_men": "Trichomoniasis — Metronidazole Single 2g Dose (Real CDC-Preferred Regimen for Men):",
        "trich_tinidazole_single_dose": "Trichomoniasis — Tinidazole Single 2g Dose (Real Alternative, Lower Resistance, Avoided in Pregnancy):",
        "trich_secnidazole_single_dose": "Trichomoniasis — Secnidazole Single 2g Dose/Solosec (Real Newer FDA-Approved Alternative):",
        "trich_metronidazole_resistant_salvage": "Trichomoniasis — Real, Documented 5-Nitroimidazole Resistance & CDC Escalation Ladder:",
        "trich_partner_treatment": "Trichomoniasis — Concurrent Partner Treatment (Real Essential, Honest Evidence Gap on Best Delivery Method):",
        "trich_pregnancy_considerations": "Trichomoniasis — Pregnancy-Specific Treatment (Real Efficacy Data & Honest Preterm-Birth Controversy):",
        "gon_first_line_ceftriaxone_monotherapy_cdc2021": "Gonorrhea — First-Line: CDC 2021 Ceftriaxone Single-Dose Monotherapy:",
        "gon_historical_dual_therapy_now_discontinued": "Gonorrhea — Historical Ceftriaxone+Azithromycin Dual Therapy (Discontinued by CDC in 2020, Still Used Elsewhere):",
        "gon_alternative_regimens_cephalosporin_allergy": "Gonorrhea — Alternative Regimens (Cephalosporin Allergy / Ceftriaxone Unavailable):",
        "gon_partner_therapy_expedited_partner_therapy": "Gonorrhea — Expedited Partner Therapy (Real Reinfection-Prevention Evidence):",
        "gon_investigational_novel_oral_antibiotics": "Gonorrhea — Investigational Novel Oral Antibiotics (Not Yet First-Line):",
        "gon_historical_obsolete_antibiotic_classes": "Gonorrhea — Historical/Obsolete Antibiotic Classes (Real Documented Resistance, No Longer Recommended):",
        "gon_gonococcal_vaccine_research_4cmenb": "Gonorrhea — Gonococcal Vaccine Research (4CMenB Cross-Protection, Real Observational-vs-RCT Reversal):",
        "conj_topical_fluoroquinolones": "Bacterial Conjunctivitis — Topical Fluoroquinolones (Moxifloxacin/Ciprofloxacin/Ofloxacin/Levofloxacin/Gatifloxacin):",
        "conj_topical_older_broad_spectrum_agents": "Bacterial Conjunctivitis — Older, Cheaper, Real Equally Effective Agents (Polymyxin B-Trimethoprim/Chloramphenicol/Erythromycin):",
        "conj_spontaneous_resolution_without_antibiotics": "Bacterial Conjunctivitis — Spontaneous Resolution Without Antibiotics (Real, Honestly Reported Self-Limited Fraction):",
        "conj_hyperacute_gonococcal_conjunctivitis_systemic_therapy": "Bacterial Conjunctivitis — Hyperacute Gonococcal Conjunctivitis, Mandatory Systemic Ceftriaxone (Adults):",
        "conj_ophthalmia_neonatorum_gonococcal_treatment": "Ophthalmia Neonatorum — Gonococcal, Mandatory Systemic Ceftriaxone:",
        "conj_ophthalmia_neonatorum_chlamydial_treatment": "Ophthalmia Neonatorum — Chlamydial, Oral Erythromycin (Real ~80% Cure, IHPS Safety Note):",
        "conj_ophthalmia_neonatorum_prevention_prophylaxis": "Ophthalmia Neonatorum — Universal Ocular Prophylaxis at Birth (Real, Honestly Mixed Evidence):",
        "conj_contact_lens_associated_conjunctivitis_pseudomonas_coverage": "Bacterial Conjunctivitis — Contact-Lens-Associated Disease, Real Pseudomonas-Covering Empirical Choice:",
        "rb_iv_systemic_chemoreduction": "Retinoblastoma — Systemic (Intravenous) Chemoreduction, the Real First-Line Globe- and Life-Preserving Backbone:",
        "rb_intra_arterial_chemotherapy": "Retinoblastoma — Intra-Arterial Chemotherapy (IAC), the Real Modern Globe-Salvage Breakthrough:",
        "rb_intravitreal_chemotherapy_vitreous_seeding": "Retinoblastoma — Intravitreal Chemotherapy for Real Vitreous Seeding:",
        "rb_focal_consolidation_therapy": "Retinoblastoma — Focal Consolidation Therapy (Laser/Cryotherapy/Plaque Brachytherapy):",
        "rb_enucleation_curative_surgery": "Retinoblastoma — Enucleation, Real Curative Surgery When the Eye Cannot Be Saved:",
        "rb_external_beam_radiotherapy_historical_and_salvage": "Retinoblastoma — External-Beam Radiotherapy (Historical/Salvage Role, Real Secondary-Malignancy Risk):",
        "os_map_chemotherapy_backbone": "Osteosarcoma — MAP Combination Chemotherapy (Methotrexate + Doxorubicin + Cisplatin), the Real Standard First-Line Systemic Backbone:",
        "os_mapie_ifosfamide_etoposide_intensification": "Osteosarcoma — MAPIE (Adding Ifosfamide + Etoposide) for Poor Responders, a Real Honestly-Reported Negative Trial:",
        "os_mifamurtide_immunomodulator": "Osteosarcoma — Mifamurtide (Liposomal MTP-PE), Real Immunomodulatory Adjunct With Mixed Trial Evidence:",
        "os_regorafenib_relapsed_metastatic": "Osteosarcoma — Regorafenib for Relapsed/Metastatic Chemotherapy-Refractory Disease, Real Multikinase-Inhibitor Option:",
        "os_limb_salvage_surgery": "Osteosarcoma — Limb-Salvage Surgery, Real Preferred Curative-Intent Local Control When Feasible:",
        "os_amputation_surgery": "Osteosarcoma — Amputation, Real Definitive Local Control When Limb-Salvage Margins Cannot Be Achieved:",
        "os_radiotherapy_limited_role": "Osteosarcoma — Radiotherapy, Real Limited Adjunct Role Given Relative Radioresistance:",
        "wilms_upfront_nephrectomy_nwts_cog_approach": "Wilms Tumour — Upfront (Primary) Radical Nephrectomy, the Real US NWTS/COG Strategy:",
        "wilms_neoadjuvant_chemotherapy_siop_approach": "Wilms Tumour — Neoadjuvant (Preoperative) Chemotherapy Then Delayed Nephrectomy, the Real European SIOP Strategy:",
        "wilms_combination_chemotherapy_backbone_stage_stratified": "Wilms Tumour — Combination Chemotherapy Backbone (Vincristine/Dactinomycin/Doxorubicin), Real Stage-and-Histology-Stratified Intensity:",
        "wilms_very_low_risk_surgery_alone_no_chemotherapy": "Wilms Tumour — Very-Low-Risk Disease, Real Surgery-Alone Strategy (Chemotherapy Omitted Entirely):",
        "wilms_radiotherapy_higher_stage_unfavorable_histology": "Wilms Tumour — Radiotherapy for Real Higher-Stage/Unfavorable-Histology Disease:",
        "wilms_anaplastic_diffuse_unfavorable_histology_intensified_chemo": "Wilms Tumour — Diffuse Anaplastic (Unfavorable) Histology, Real Intensified Multi-Agent Chemotherapy:",
        "wilms_focal_anaplastic_distinct_favorable_outcome": "Wilms Tumour — Focal Anaplastic Histology, a Real Distinctly Better-Outcome Subtype:",
        "wilms_relapsed_disease_salvage_chemotherapy": "Wilms Tumour — Relapsed Disease, Real Salvage Chemotherapy Regimens:",
        "wilms_late_effects_long_term_surveillance": "Wilms Tumour — Real Long-Term Late-Effects Surveillance in Survivors:",
        "tet_pre_exposure_vaccination_medicines": "Tetanus — PRE-EXPOSURE Vaccination (Toxoid Primary Series/Boosters + Maternal/MNTE Immunization), the Real Primary Prevention/'Cure' Strategy:",
        "tet_post_exposure_prophylaxis_medicines": "Tetanus — Post-Exposure Prophylaxis in Inadequately-Vaccinated Wound Patients (TIG + Wound Management):",
        "tet_established_disease_antitoxin_medicines": "Tetanus — Antitoxin/Immunoglobulin for ALREADY-Established Clinical Disease (Honestly More Limited Than Prophylactic Use):",
        "tet_established_disease_antibiotic_medicines": "Tetanus — Antibiotic Therapy for Established Disease (Metronidazole vs Penicillin, Genuinely Contested Evidence):",
        "tet_established_disease_supportive_icu_medicines": "Tetanus — ICU-Level Supportive Care for Spasms/Dysautonomia (Benzodiazepines, Magnesium, Neuromuscular Blockade + Ventilation):",
        "anaph_epinephrine_first_line_medicines": "Anaphylaxis — Intramuscular Epinephrine (Adrenaline), the Real First-Line, First-Dose, Life-Saving Treatment:",
        "anaph_antihistamine_adjunct_medicines": "Anaphylaxis — H1/H2 Antihistamines, Adjunct ONLY for Skin/Mucosal Symptoms (Real, Honestly NOT a Substitute for Epinephrine):",
        "anaph_corticosteroid_adjunct_medicines": "Anaphylaxis — Corticosteroids, Historical Biphasic-Prevention Rationale vs Real Modern Evidence Gap:",
        "anaph_supportive_critical_care_measures": "Anaphylaxis — Supportive Critical Care for Severe/Refractory Reactions (IV Fluids, Oxygen, Positioning, Advanced Airway):",
        "anaph_secondary_prevention_measures": "Anaphylaxis — Secondary Prevention (Allergen Avoidance + Epinephrine Auto-Injector Prescribing):",
        "diph_pre_exposure_vaccination_medicines": "Diphtheria — PRE-EXPOSURE Vaccination (Toxoid Primary Series/Decade Boosters), the Real Primary Prevention/'Cure' Strategy:",
        "diph_antitoxin_medicines": "Diphtheria — Antitoxin (DAT) for Established Disease, Real Time-Critical Neutralisation of Unbound Toxin Only:",
        "diph_antibiotic_medicines": "Diphtheria — Antibiotics (Penicillin/Erythromycin/Azithromycin), Real Distinct Adjunct That Halts Further Toxin Production:",
        "diph_airway_management_medicines": "Diphtheria — Airway Management (Intubation/Tracheostomy) for Pseudomembrane-Related Obstruction:",
        "diph_myocarditis_polyneuropathy_complication_management": "Diphtheria — Myocarditis & Polyneuropathy Complications, Why Late Antitoxin Cannot Reverse Damage Already Done:",
        "diph_cutaneous_diphtheria_management": "Diphtheria — Cutaneous Disease, Real Milder Course & Antibiotics-Centred (DAT-Sparing) Management:",
        "glau_topical_prostaglandin_analogs": "Glaucoma — Prostaglandin Analogs, Real Current First-Line Topical Therapy (Latanoprost/Bimatoprost/Travoprost):",
        "glau_topical_beta_blockers": "Glaucoma — Topical Beta-Blockers, Real Older First-Line Therapy (Timolol):",
        "glau_topical_alpha_agonists": "Glaucoma — Topical Alpha-2 Agonists (Brimonidine):",
        "glau_topical_carbonic_anhydrase_inhibitors": "Glaucoma — Topical Carbonic Anhydrase Inhibitors (Dorzolamide/Brinzolamide):",
        "glau_topical_rho_kinase_inhibitors": "Glaucoma — Rho-Kinase Inhibitors, Real Newest Topical Class (Netarsudil):",
        "glau_laser_procedures": "Glaucoma — Laser Procedures (Selective Laser Trabeculoplasty & Laser Peripheral Iridotomy):",
        "glau_incisional_and_migs_surgery": "Glaucoma — Incisional Surgery & MIGS (Trabeculectomy, iStent):",
        "amd_anti_vegf_intravitreal_injections": "Age-Related Macular Degeneration — Anti-VEGF Intravitreal Injections, Real Dramatic Vision-Preserving/Vision-Improving Therapy for Wet AMD (Ranibizumab/Aflibercept/Bevacizumab — MARINA/ANCHOR/CATT/VIEW Trials):",
        "amd_areds2_dietary_supplementation": "Age-Related Macular Degeneration — AREDS2 Dietary Supplementation, Real Proven Progression Prevention for Intermediate Dry AMD:",
        "amd_photodynamic_therapy": "Age-Related Macular Degeneration — Photodynamic Therapy with Verteporfin, Older Option Largely Superseded by Anti-VEGF:",
        "amd_low_vision_rehabilitation": "Age-Related Macular Degeneration — Low-Vision Rehabilitation, Real Functional Support for Advanced/Residual Vision Loss:",
        "cat_investigational_pharmacologic_agents_lanosterol": "Cataract — Investigational Pharmacologic Agents (Lanosterol/Oxysterols), Real Preclinical/Contested Stage, NOT a Proven Human Treatment:",
        "cat_phacoemulsification_iol": "Cataract — Phacoemulsification with Intraocular Lens (IOL) Implantation, Real Modern Surgical Standard of Care:",
        "cat_msics_lower_cost_alternative": "Cataract — Manual Small-Incision Cataract Surgery (MSICS), Real Comparably Effective Lower-Cost Alternative:",
        "cat_congenital_pediatric_cataract_surgery": "Cataract — Congenital/Paediatric Cataract Surgery, Real Distinct Amblyopia-Window-Driven Entity:",
        "cat_india_npcb_public_health_program": "Cataract — India's National Programme for Control of Blindness (NPCB and VI), Real Public Surgical-Access Infrastructure:",
        "ast_corrective_spectacle_glasses": "Astigmatism — Corrective Spectacle (Glasses) Lenses, Real Universal Non-Invasive First-Line Correction:",
        "ast_toric_contact_lenses": "Astigmatism — Toric Contact Lenses, Real Randomised-Trial-Proven Alternative to Glasses:",
        "ast_lasik_prk_refractive_surgery": "Astigmatism — LASIK/PRK Laser Refractive Surgery, Real Definitive Surgical Correction:",
        "ast_toric_iol_cataract_patients": "Astigmatism — Toric Intraocular Lens (IOL) for Astigmatism Coexisting with Cataract:",
        "ast_corneal_collagen_crosslinking_keratoconus": "Astigmatism — Corneal Collagen Cross-Linking (CXL) for Progressive Irregular Astigmatism/Keratoconus, Real Disease-Modifying (Progression-Halting) Procedure:",
        "myo_corrective_glasses_contact_lenses": "Myopia — Corrective Glasses / Contact Lenses, Real Universal First-Line Functional Correction:",
        "myo_lasik_prk_refractive_surgery": "Myopia — LASIK / PRK Refractive Surgery, Real Definitive Surgical Correction for Adult Candidates (Solomon 2009 Systematic Review):",
        "myo_low_dose_atropine_childhood_progression_control": "Myopia — Low-Dose Atropine Eye Drops, Real RCT-Proven Childhood Progression Control (ATOM2/LAMP Trials):",
        "myo_orthokeratology_progression_control": "Myopia — Orthokeratology, Real RCT-Proven Childhood Progression Control (ROMIO/HM-PRO Trials):",
        "myo_implantable_collamer_lens_high_myopia": "Myopia — Implantable Collamer Lens (ICL), Real Alternative Structural Correction for High Myopia Not Suitable for LASIK:",
        "hz_shingrix_recombinant_vaccine_medicines": "Herpes Zoster — Shingrix (Recombinant Zoster Vaccine), Real Primary Prevention/'Cure' Strategy (ZOE-50/ZOE-70):",
        "hz_shingrix_immunocompromised_medicines": "Herpes Zoster — Shingrix in Immunocompromised Adults, Real Modern Indication Expansion:",
        "hz_zostavax_live_vaccine_medicines": "Herpes Zoster — Zostavax (Live-Attenuated Vaccine), Real Lower-Efficacy Predecessor, Now Discontinued in the US:",
        "hz_oral_antiviral_72hr_treatment_medicines": "Herpes Zoster — Oral Valacyclovir/Famciclovir/Acyclovir for Established Disease, Real Strictly Time-Critical 72-Hour Window:",
        "hz_iv_acyclovir_disseminated_medicines": "Herpes Zoster — IV Acyclovir for Disseminated Disease in Immunocompromised Patients:",
        "hz_corticosteroid_adjunct_medicines": "Herpes Zoster — Oral Corticosteroids as Acute-Pain Adjunct, Real Honest Lack of Proven PHN-Prevention Benefit:",
        "hz_ophthalmicus_management_medicines": "Herpes Zoster Ophthalmicus — Real Vision-Threatening Presentation, Urgent Ophthalmology Referral:",
        "hz_phn_pain_management_medicines": "Established Postherpetic Neuralgia — Real Symptomatic (Non-Curative) Pain Management:",
        "mel_surgical_excision_early_stage": "Melanoma — Wide Local Excision, Real Curative-Intent Surgery for Early-Stage (Stage I-II) Disease:",
        "mel_sentinel_lymph_node_biopsy_staging": "Melanoma — Sentinel Lymph Node Biopsy, Real Staging/Prognostic Procedure (Honestly Not Itself Therapeutic):",
        "mel_ctla4_inhibitor_ipilimumab": "Melanoma — Ipilimumab (CTLA-4 Checkpoint Inhibitor), Advanced/Metastatic Disease:",
        "mel_pd1_inhibitor_monotherapy": "Melanoma — PD-1 Checkpoint Inhibitor Monotherapy (Nivolumab/Pembrolizumab), Advanced Disease:",
        "mel_combination_nivolumab_ipilimumab": "Melanoma — Nivolumab + Ipilimumab Combination Checkpoint Blockade, Real Headline Advanced-Disease Regimen (CheckMate 067):",
        "mel_braf_mek_targeted_therapy": "Melanoma — BRAF/MEK-Targeted Therapy (Dabrafenib+Trametinib, Vemurafenib+Cobimetinib), BRAF-V600-Mutant Disease:",
        "mel_adjuvant_therapy_high_risk_resected": "Melanoma — Adjuvant Immunotherapy/Targeted Therapy After Resection of High-Risk Stage III/IV Disease:",
        "mel_other_unresectable_intransit_therapies": "Melanoma — Other Options for Unresectable/In-Transit Disease (Talimogene Laherparepvec/T-VEC):",
        "covid_mrna_vaccine_medicines": "COVID-19 — mRNA Vaccination (Pfizer-BioNTech/Moderna), Real Original-Trial Efficacy vs Real Variant-Era Real-World Effectiveness:",
        "covid_oral_antiviral_medicines": "COVID-19 — Oral Antivirals for Early High-Risk Outpatient Treatment (Nirmatrelvir-Ritonavir/Paxlovid, Molnupiravir):",
        "covid_remdesivir_medicines": "COVID-19 — Remdesivir, Real Honest Evolution of Evidence Across Outpatient vs Hospitalized Settings:",
        "covid_dexamethasone_medicines": "COVID-19 — Dexamethasone for Hospitalized Patients Requiring Oxygen/Ventilation (RECOVERY Trial, Real First Proven Mortality-Reducing Drug):",
        "covid_immunomodulator_medicines": "COVID-19 — Tocilizumab/Baricitinib for Hyperinflammatory-Phase Hospitalized Disease:",
        "covid_monoclonal_antibody_medicines": "COVID-19 — Monoclonal Antibodies, Real Historical Efficacy Against Earlier Variants and Real Documented Loss of Activity Against Later Variants:",
        "covid_supportive_care_medicines": "COVID-19 — Supportive Care, Oxygen Therapy and Prone Positioning for Non-ICU Hospitalized Disease (Non-Curative):",
        "chole_udca_oral_dissolution_therapy_medicines": "Gallstones — Oral Bile-Acid (UDCA/CDCA) Dissolution Therapy, Real Patient-Selection-Dependent Efficacy:",
        "chole_laparoscopic_cholecystectomy_procedure": "Gallstones — Laparoscopic Cholecystectomy, Real Modern Standard-of-Care Curative Surgery:",
        "chole_open_cholecystectomy_procedure": "Gallstones — Open Cholecystectomy, Real Now-Rare Alternative for Specific Scenarios:",
        "chole_ercp_sphincterotomy_choledocholithiasis_procedure": "Gallstones — ERCP with Sphincterotomy for Common Bile Duct Stone Clearance (Choledocholithiasis):",
        "chole_iv_antibiotics_acute_cholecystitis_cholangitis_medicines": "Gallstones — IV Antibiotics for Acute Cholecystitis/Cholangitis, Real Essential but Non-Curative Adjunct:",
        "chole_percutaneous_cholecystostomy_high_risk_procedure": "Gallstones — Percutaneous Cholecystostomy, Real Bridging/Salvage Option for High-Surgical-Risk Patients:",
        "chole_timing_of_cholecystectomy_evidence": "Gallstones — Timing of Cholecystectomy for Acute Cholecystitis, Real Early-vs-Delayed Evidence:",
        "croup_oral_dexamethasone_regimens_standard_and_low_dose": "Croup — Real Flagship Single-Dose Oral Dexamethasone (Standard 0.6 mg/kg and Real Non-Inferior Low-Dose 0.15 mg/kg):",
        "croup_nebulized_budesonide_alternative": "Croup — Nebulized Budesonide, Real Alternative When the Oral Route Is Not Feasible:",
        "croup_oral_prednisolone_alternative": "Croup — Single-Dose Oral Prednisolone, Real Alternative Where Dexamethasone Is Unavailable:",
        "croup_nebulized_epinephrine_severe_stridor_at_rest": "Croup — Nebulized Epinephrine, Real Rapid but Real Temporary Bridge for Severe Stridor at Rest:",
        "croup_combination_epinephrine_corticosteroid_severe": "Croup — Combined Nebulized Epinephrine Plus Corticosteroid, Real Bridging Strategy for Severe Presentations:",
        "croup_humidified_air_mist_therapy_historical": "Croup — Humidified Air/Mist Therapy, Real Honest Negative Finding Despite Historical Use:",
        "lar_voice_rest": "Laryngitis (Acute, Adult) — Voice Rest, Real First-Line Non-Pharmacologic Measure:",
        "lar_hydration_humidification": "Laryngitis (Acute, Adult) — Hydration and Humidified Air Inhalation, Real First-Line Non-Pharmacologic Measures:",
        "lar_avoiding_irritants": "Laryngitis (Acute, Adult) — Avoidance of Tobacco Smoke and Other Laryngeal Irritants, Real Supportive Lifestyle Measure:",
        "lar_corticosteroids_professional_voice_users": "Laryngitis (Acute, Adult) — Short-Course Oral Corticosteroids for Professional Voice Users, Real But Honestly Case-Report-Level (Not RCT) Evidence:",
        "lar_gerd_reflux_treatment": "Laryngitis (Acute, Adult) — Antireflux Therapy (H2RA/PPI) When GERD/Laryngopharyngeal Reflux Is the Identified Cause, Real Honestly Non-Significant Pooled RCT Evidence (Qadeer 2006):",
        "lar_antibiotics_suspected_bacterial_superinfection_only": "Laryngitis (Acute, Adult) — Antibiotics, Real Reserved Only for Suspected Bacterial Superinfection, Not Effective as Routine Therapy (Cochrane, Reveiz 2015):",
        "bronchio_nirsevimab_prevention_medicines": "Bronchiolitis -- Nirsevimab (Beyfortus), Real Single-Dose Monoclonal-Antibody Breakthrough (MELODY/HARMONIE Trials):",
        "bronchio_palivizumab_high_risk_prevention_medicines": "Bronchiolitis -- Palivizumab (Synagis), Real Older Monthly-Dosed High-Risk-Only Monoclonal Antibody:",
        "bronchio_maternal_rsv_vaccination_medicines": "Bronchiolitis -- Maternal RSVpreF Vaccination During Pregnancy (Real Complementary Passive-Immunity Option):",
        "bronchio_bronchodilator_no_benefit_medicines": "Bronchiolitis -- Bronchodilators (Albuterol/Salbutamol), Real Cochrane-Reviewed No Proven Benefit for Established Disease:",
        "bronchio_nebulized_hypertonic_saline_medicines": "Bronchiolitis -- Nebulised Hypertonic Saline (3%), Real Mixed/Modest Low-Certainty Evidence:",
        "bronchio_corticosteroid_no_benefit_medicines": "Bronchiolitis -- Corticosteroids, Real Cochrane-Reviewed No Proven Benefit for Typical Bronchiolitis (Contrast With Asthma):",
        "bronchio_supportive_care_medicines": "Bronchiolitis -- Supportive Care: Oxygen, Hydration, Nasal Suctioning (Real Evidence-Based, Non-Curative Mainstay):",
        "vsd_expectant_management_medicines": "VSD — Serial Echocardiographic Surveillance (Watchful Waiting for Real Spontaneous Closure):",
        "vsd_heart_failure_medical_management_medicines": "VSD — Medical Management of Infant Heart-Failure Symptoms Pending Closure (Diuretics/ACE Inhibitors/Digoxin, Real Bridging Not Curative):",
        "vsd_surgical_patch_closure_medicines": "VSD — Surgical Patch Closure, Real Gold-Standard Definitive Repair:",
        "vsd_transcatheter_device_closure_medicines": "VSD — Transcatheter Device Closure, Real Growing Alternative to Open-Heart Surgery for Suitable Defects:",
        "vsd_pulmonary_artery_banding_medicines": "VSD — Pulmonary Artery Banding, Real Older Palliative Technique for Select High-Risk Scenarios:",
        "tof_curative_surgical_repair": "Tetralogy of Fallot -- Complete Surgical Repair (VSD Closure + RVOT Obstruction Relief), the Real Definitive Cure:",
        "tof_acute_tet_spell_management_medicines": "Tetralogy of Fallot -- Acute Hypercyanotic ('Tet') Spell Emergency Management (Knee-Chest, Oxygen, Morphine, Phenylephrine, Propranolol/Esmolol):",
        "tof_staged_palliation_medicines": "Tetralogy of Fallot -- Staged Palliative Shunt/Stent Procedures for High-Risk Infants (Bridge to Complete Repair, Not Definitive):",
        "tof_long_term_surveillance_and_reintervention_medicines": "Tetralogy of Fallot -- Long-Term Post-Repair Surveillance and Reintervention (Pulmonary Valve Replacement):",
        "pda_indomethacin_medicines": "PDA -- Indomethacin, Real Classic First-Line COX Inhibitor for Pharmacologic Ductal Closure:",
        "pda_ibuprofen_medicines": "PDA -- Ibuprofen, Real Equally Effective Alternative to Indomethacin With a Better Renal/GI Safety Profile:",
        "pda_paracetamol_medicines": "PDA -- Paracetamol (Acetaminophen), Real Newer Alternative Especially When COX Inhibitors Are Contraindicated:",
        "pda_transcatheter_device_closure": "PDA -- Transcatheter Device Closure, Real Modern Minimally Invasive Definitive Procedure:",
        "pda_surgical_ligation": "PDA -- Surgical Ligation/Division, Real Historical/Backup Mechanically Definitive Closure:",
        "pda_conservative_management": "PDA -- Expectant Management/Watchful Waiting for Small or Uncertain-Benefit PDAs:",
        "ibs_ibsd_rifaximin": "IBS-D -- Rifaximin, Real FDA-Approved Non-Absorbed Antibiotic (TARGET 1/2 Trials):",
        "ibs_ibsd_eluxadoline": "IBS-D -- Eluxadoline, Real Mixed Opioid-Receptor Modulator (IBS-3001/3002 Trials, Gallbladder-Absent Pancreatitis Warning):",
        "ibs_generalized_pain_antispasmodics": "IBS -- Antispasmodics (Dicyclomine/Hyoscine and Related Agents), Real Generalized Pain/Cramping Relief:",
        "ibs_ibsc_linaclotide": "IBS-C -- Linaclotide, Real Guanylate Cyclase-C Agonist (Pivotal Phase 3 Trial):",
        "ibs_ibsc_lubiprostone": "IBS-C -- Lubiprostone, Real Chloride-Channel (ClC-2) Activator (Pooled Pivotal Trial Data):",
        "ibs_neuromodulators_tca_ssri_snri": "IBS -- Low-Dose TCAs/SSRIs/SNRIs, Real Gut-Brain-Axis Pain Modulation (Distinct From Psychiatric Use):",
        "ibs_diet_low_fodmap": "IBS -- Low-FODMAP Diet, Real Substantial Non-Pharmacologic Evidence Base:",
        "ibs_psychotherapy_cbt_gut_hypnotherapy": "IBS -- Gut-Directed Psychotherapies (CBT/Gut-Hypnotherapy), Real Gut-Brain-Axis Documented Efficacy:",
        "sarc_observation_watchful_waiting_lofgren_and_stage_i": "Sarcoidosis -- Observation/Watchful Waiting, Real Default Management for Löfgren Syndrome and Asymptomatic Stage I Disease (No Medicine Needed):",
        "sarc_oral_corticosteroid_first_line_treatment": "Sarcoidosis -- Oral Corticosteroids, Real First-Line Therapy for Progressive/Symptomatic/Organ-Threatening Disease (Cochrane-Reviewed):",
        "sarc_topical_inhaled_corticosteroid_limited_role": "Sarcoidosis -- Topical/Inhaled Corticosteroids, Real But Honestly Limited Role (Skin-Limited or Adjunct Pulmonary Disease):",
        "sarc_steroid_sparing_immunosuppressant_therapy": "Sarcoidosis -- Steroid-Sparing Immunosuppressants (Methotrexate First-Line, Azathioprine/MMF/Leflunomide Alternatives):",
        "sarc_biologic_tnf_inhibitor_refractory_therapy": "Sarcoidosis -- TNF-Inhibitor Biologic Therapy (Infliximab/Adalimumab) for Refractory or Organ-Threatening Disease:",
        "sarc_cardiac_neurosarcoidosis_urgent_intensive_management": "Sarcoidosis -- Cardiac and Neurosarcoidosis, Real More Aggressive/Urgent Immunosuppression Given Organ-Threatening Potential:",
        "divert_outpatient_no_antibiotic_management_evidence": "Diverticulitis -- Real Headline Evidence Shift: Observational (No-Antibiotic) Outpatient Management for Uncomplicated Disease (AVOD/DIABOLO Trials):",
        "divert_oral_iv_antibiotic_therapy_medicines": "Diverticulitis -- Oral/IV Antibiotic Therapy, Genuinely Still Indicated for Immunocompromised, Higher-Risk, or Complicated Disease:",
        "divert_percutaneous_drainage_procedure": "Diverticulitis -- Percutaneous Image-Guided Drainage of Diverticular Abscess (Bridge/Salvage, Not Durable Cure):",
        "divert_emergency_surgery_procedure": "Diverticulitis -- Emergency Surgery for Perforation/Peritonitis (Primary Anastomosis vs Hartmann's Procedure):",
        "divert_elective_surgery_procedure": "Diverticulitis -- Elective Sigmoid Colectomy for Recurrent Disease, Real Individualized (Not Automatic-After-N-Episodes) Indication:",
        "divert_high_fiber_diet_lifestyle_medicines": "Diverticulitis -- High-Fiber Diet & Lifestyle, Real Evidence-Based Preventive 'Other' Measure:",
        "divert_prophylactic_mesalamine_declining_role_medicines": "Diverticulitis -- Long-Term Prophylactic Mesalazine/Antibiotics, Real Honestly Declining/Unsupported Role for Recurrence Prevention:",
        "stone_met_alpha_blockers_medicines": "Nephrolithiasis -- Medical Expulsive Therapy (Tamsulosin/Alpha-Blockers), Real Evidence-Evolution Story (Cochrane Meta-Analysis vs SUSPEND RCT):",
        "stone_nsaid_opioid_analgesia_medicines": "Nephrolithiasis -- NSAID/Opioid Analgesia for Acute Renal Colic, Real First-Line Pain Control (Non-Curative of the Stone):",
        "stone_shock_wave_lithotripsy_procedure": "Nephrolithiasis -- Extracorporeal Shock Wave Lithotripsy (SWL/ESWL), Real Least-Invasive First-Line Procedure:",
        "stone_ureteroscopy_laser_lithotripsy_procedure": "Nephrolithiasis -- Ureteroscopy with Holmium/Thulium-Fiber Laser Lithotripsy, Real High-Success Procedure:",
        "stone_percutaneous_nephrolithotomy_procedure": "Nephrolithiasis -- Percutaneous Nephrolithotomy (PCNL/Mini-PCNL), Real Preferred Procedure for Large/Complex Stones:",
        "stone_uric_acid_dissolution_medicines": "Nephrolithiasis -- Potassium Citrate +/- Allopurinol Urine Alkalinization, Real Genuine Medicine-Only Cure for Pure Uric Acid Stones:",
        "stone_thiazide_dietary_recurrence_prevention_medicines": "Nephrolithiasis -- Thiazide Diuretics, Potassium Citrate & Dietary/Hydration Measures, Real Recurrence Prevention in Calcium-Stone-Formers:",
        "hem_fiber_dietary_conservative_measures": "Hemorrhoids -- Dietary Fiber Supplementation, Real First-Line Conservative Measure (Grade I-II):",
        "hem_topical_corticosteroid_anesthetic_medicines": "Hemorrhoids -- Topical Corticosteroid + Local Anesthetic Combination Creams/Suppositories (Symptom Relief):",
        "hem_topical_phlebotonic_medicines": "Hemorrhoids -- Micronized Purified Flavonoid Fraction (MPFF) & Other Phlebotonics, Real Symptom/Bleeding Benefit, Not a Structural Cure:",
        "hem_office_procedures_rubber_band_ligation": "Hemorrhoids -- Rubber Band Ligation (RBL), Real First-Line Office Procedure for Grade I-III:",
        "hem_office_procedures_comparative_sclerotherapy_infrared_coagulation": "Hemorrhoids -- Injection Sclerotherapy & Infrared Coagulation, Real Alternative Office Procedures (Comparative Data vs RBL):",
        "hem_surgical_excisional_hemorrhoidectomy": "Hemorrhoids -- Excisional (Conventional) Hemorrhoidectomy, Real Gold-Standard Surgical Cure for Grade III-IV/Refractory Disease:",
        "hem_surgical_stapled_hemorrhoidopexy": "Hemorrhoids -- Stapled Hemorrhoidopexy (PPH/Longo Technique), Real Less Painful but Higher-Recurrence Alternative:",
        "hem_thrombosed_external_hemorrhoid_management": "Hemorrhoids -- Acutely Thrombosed External Hemorrhoid, Real Early Excision (48-72h) vs Conservative Management:",
        "fissure_conservative_first_line_measures": "Anal Fissure -- Dietary Fibre + Warm Sitz Baths, Real First-Line Therapy for Acute Fissure:",
        "fissure_topical_nitrate_therapy": "Anal Fissure -- Topical Glyceryl Trinitrate (GTN) 0.2-0.4%, Real Cochrane-Reviewed First-Line Topical Agent:",
        "fissure_topical_calcium_channel_blockers": "Anal Fissure -- Topical Calcium Channel Blockers (Diltiazem, Nifedipine), Real Comparable-to-Superior Efficacy vs GTN With Fewer Side Effects:",
        "fissure_botulinum_toxin_injection": "Anal Fissure -- Botulinum Toxin Injection, Real Reversible Chemical Sphincterotomy for Fissures Refractory to Topical Therapy:",
        "fissure_lateral_internal_sphincterotomy": "Anal Fissure -- Lateral Internal Sphincterotomy (LIS), Real Gold-Standard Surgical Cure With Honest Incontinence-Risk Trade-Off:",
        "fissure_medical_equipment_devices": "Anal Fissure -- Medical Equipment/Devices (Anoscope, Botulinum Toxin Injection Needle):",
        "hernia_open_lichtenstein_mesh_repair_procedure": "Inguinal Hernia -- Open Lichtenstein Tension-Free Mesh Repair, Real Modern Open Standard:",
        "hernia_laparoscopic_tep_tapp_repair_procedure": "Inguinal Hernia -- Laparoscopic TEP/TAPP Mesh Repair, Real Minimally Invasive Alternative (Bilateral/Recurrent Hernia Advantage):",
        "hernia_watchful_waiting_management": "Inguinal Hernia -- Watchful Waiting for Minimally Symptomatic/Asymptomatic Hernia, Real Evidence-Based Deferral, Not a Cure:",
        "hernia_emergency_incarcerated_strangulated_repair_procedure": "Inguinal Hernia -- Emergency Repair for Incarcerated/Strangulated Hernia, Real Higher-Risk Scenario Supporting Elective Repair First:",
        "hernia_pediatric_infant_repair_procedure": "Inguinal Hernia -- Pediatric/Infant Repair (Herniotomy), Real Distinct Urgency and Excellent Outcomes:",
        "hernia_perioperative_antibiotic_prophylaxis_analgesia_medicines": "Inguinal Hernia -- Perioperative Antibiotic Prophylaxis & Multimodal Analgesia, Real Adjunctive Not Curative of the Hernia Itself:",
        "rcc_partial_nephrectomy_nephron_sparing": "Renal Cell Carcinoma -- Partial Nephrectomy (Nephron-Sparing Surgery), Real Preferred Curative-Intent Surgery for Appropriate Localized (T1) Disease:",
        "rcc_radical_nephrectomy": "Renal Cell Carcinoma -- Radical Nephrectomy, Real Standard Curative-Intent Surgery for Larger/Complex Localized Disease:",
        "rcc_active_surveillance_small_renal_mass": "Renal Cell Carcinoma -- Active Surveillance for Real Select Small Renal Masses (<=4 cm):",
        "rcc_combination_nivolumab_ipilimumab": "Renal Cell Carcinoma -- Nivolumab + Ipilimumab Combination Checkpoint Blockade, Advanced Disease (CheckMate 214):",
        "rcc_combination_pembrolizumab_axitinib": "Renal Cell Carcinoma -- Pembrolizumab + Axitinib Combination Therapy, Advanced Disease (KEYNOTE-426):",
        "rcc_single_agent_tki_historical_comparator": "Renal Cell Carcinoma -- Single-Agent TKI Monotherapy (Sunitinib/Pazopanib), Real Older Standard/Historical Comparator:",
        "rcc_adjuvant_therapy_high_risk_resected": "Renal Cell Carcinoma -- Adjuvant Pembrolizumab, Resected High-Risk Disease (KEYNOTE-564):",
        "rcc_metastasectomy_oligometastatic": "Renal Cell Carcinoma -- Surgical Metastasectomy for Real Select Oligometastatic Disease:",
        "ras_optimal_medical_therapy_acei_arb": "Renal Artery Stenosis -- ACE-Inhibitor/ARB Optimal Medical Therapy, Real Evidence-Based First-Line Approach (Hackam 2008):",
        "ras_statin_therapy_atherosclerotic": "Renal Artery Stenosis -- Statin Therapy, Atherosclerotic Plaque Stabilization/Cardiovascular Risk Reduction:",
        "ras_antiplatelet_therapy": "Renal Artery Stenosis -- Aspirin (Antiplatelet Therapy), Atherosclerotic Secondary Prevention:",
        "ras_percutaneous_angioplasty_fmd": "Renal Artery Stenosis -- Percutaneous Angioplasty (PTA), Real Closest-to-Cure Option for Fibromuscular Dysplasia-Related Disease (Trinquart 2010):",
        "ras_surgical_revascularization_fmd": "Renal Artery Stenosis -- Surgical Revascularization, Real Highest FMD Cure Rate, Reserved for Complex Anatomy (Trinquart 2010):",
        "ras_percutaneous_angioplasty_stenting_atherosclerotic": "Renal Artery Stenosis -- Percutaneous Angioplasty with Stenting, Atherosclerotic Disease, Real NOT Superior to Medical Therapy (CORAL/ASTRAL):",
        "bph_alpha_blockers_medicines": "BPH -- Alpha-1-Blockers (Tamsulosin/Silodosin/Alfuzosin), Real Fastest-Onset Symptom Relief:",
        "bph_5_ari_medicines": "BPH -- 5-Alpha-Reductase Inhibitors (Finasteride/Dutasteride), Real Slower-Onset Disease-Modifying Therapy (PLESS/CombAT):",
        "bph_combination_therapy_medicines": "BPH -- Alpha-Blocker + 5-ARI Combination Therapy, Real Superior to Either Monotherapy (MTOPS/CombAT):",
        "bph_pde5_inhibitor_medicines": "BPH -- Tadalafil (PDE5-Inhibitor), Real Approved Specifically for BPH-LUTS With Concurrent Erectile Dysfunction:",
        "bph_turp_procedure": "BPH -- Transurethral Resection of the Prostate (TURP), Real Gold-Standard Definitive Surgical Cure:",
        "bph_minimally_invasive_procedures": "BPH -- Newer Minimally Invasive Procedures (Prostatic Urethral Lift/UroLift, Water Vapour Thermal Therapy/Rezum), Real Sexual-Function-Sparing Alternatives:",
        "bph_acute_urinary_retention_catheterization": "BPH -- Urethral Catheterisation for Acute Urinary Retention, Real Immediate Bridging Measure, Honestly Non-Curative:",
        "dn_raas_blockade_first_line": "Diabetic Nephropathy -- ACE Inhibitors/ARBs, Real Foundational First-Line RAAS Blockade (RENAAL/IDNT/Captopril Collaborative Study):",
        "dn_sglt2_inhibitors": "Diabetic Nephropathy -- SGLT2 Inhibitors, Real Second Renoprotective Pillar (CREDENCE/DAPA-CKD/EMPA-KIDNEY):",
        "dn_finerenone_nsmra": "Diabetic Nephropathy -- Finerenone, Non-Steroidal MRA, Real Third Renoprotective Pillar (FIDELIO-DKD/FIGARO-DKD/FIDELITY):",
        "dn_glp1_receptor_agonists": "Diabetic Nephropathy -- GLP-1 Receptor Agonists, Real Newest Kidney-Outcome-Proven Addition (FLOW Trial, Semaglutide):",
        "dn_combination_triple_therapy_strategy": "Diabetic Nephropathy -- Combination RAAS Blockade + SGLT2i + Finerenone (+/- GLP-1RA), Real Current Best-Practice Layered Strategy:",
        "dn_bp_glycemic_targets_supportive": "Diabetic Nephropathy -- Blood Pressure & Glycaemic Control Targets, Real Foundational Supportive Measures (Other):",
        "cah_glucocorticoid_replacement_medicines": "Congenital Adrenal Hyperplasia -- Glucocorticoid Replacement (Hydrocortisone/Prednisolone/Dexamethasone), Real Lifelong Cortisol Deficiency and Androgen-Excess Control:",
        "cah_mineralocorticoid_replacement_medicines": "Congenital Adrenal Hyperplasia -- Fludrocortisone + Sodium Chloride, Real Mandatory Salt-Wasting-Form Mineralocorticoid Replacement:",
        "cah_stress_dose_emergency_protocol_medicines": "Congenital Adrenal Hyperplasia -- Emergency Stress-Dose Hydrocortisone (Sick-Day Rules), Real Adrenal-Crisis-Preventing Protocol:",
        "cah_crf1_receptor_antagonist_adjunct_medicines": "Congenital Adrenal Hyperplasia -- Crinecerfont, Real FDA-Approved CRF1-Receptor-Antagonist Adjunct (Glucocorticoid-Dose-Sparing):",
        "cah_pregnancy_and_fertility_management_other": "Congenital Adrenal Hyperplasia -- Optimized Glucocorticoid/Mineralocorticoid Dosing for Fertility and Pregnancy (Other):",
        "cah_genital_surgery_and_psychosocial_care_other": "Congenital Adrenal Hyperplasia -- Feminizing Genitoplasty Timing and Multidisciplinary Psychosocial Support (Other):",
        "prl_cabergoline_first_line_dopamine_agonist": "Prolactinoma -- Cabergoline, Real First-Line Dopamine Agonist (Normalizes Prolactin AND Shrinks the Tumor):",
        "prl_bromocriptine_older_dopamine_agonist": "Prolactinoma -- Bromocriptine, Real Older Dopamine Agonist Still Used in Specific Situations (e.g. Imminent Pregnancy Planning):",
        "prl_dopamine_agonist_supervised_withdrawal": "Prolactinoma -- Medically Supervised Dopamine-Agonist Withdrawal, Real Chance of Durable Medication-Free Remission:",
        "prl_transsphenoidal_surgery_second_line": "Prolactinoma -- Transsphenoidal Surgery, Real Second-Line (or Select First-Line) Treatment for Resistant/Intolerant or Non-Invasive Disease:",
        "prl_radiation_therapy_refractory_other": "Prolactinoma -- Radiation Therapy (Stereotactic Radiosurgery/Fractionated), Real Lower-Priority Last Resort for Rare Refractory Disease (Other):",
        "pku_lifelong_low_phenylalanine_diet_medicines": "Phenylketonuria -- Lifelong Low-Phenylalanine Diet + Medical Formula, Real Newborn-Screening-Triggered Foundational Therapy:",
        "pku_sapropterin_bh4_medicines": "Phenylketonuria -- Sapropterin Dihydrochloride (Kuvan), Real Oral BH4 Cofactor for BH4-Responsive Patients:",
        "pku_sepiapterin_bh4_medicines": "Phenylketonuria -- Sepiapterin (Sephience), Real Next-Generation Oral BH4 Precursor (2025 Approval):",
        "pku_pegvaliase_enzyme_substitution_medicines": "Phenylketonuria -- Pegvaliase (Palynziq), Real Injectable Enzyme-Substitution Therapy for Uncontrolled Adult PKU:",
        "pku_maternal_pku_pregnancy_management_other": "Phenylketonuria -- Maternal PKU Preconception/Pregnancy Phenylalanine Control, Real Fetal-Harm-Prevention Protocol (Other):",
        "pku_lnaa_adjunct_other": "Phenylketonuria -- Large Neutral Amino Acid (LNAA) Supplementation, Real Lower-Priority Adjunct (Other):",
        "siadh_fluid_restriction_first_line": "SIADH -- Fluid Restriction, Real First-Line Non-Pharmacological Therapy (Real Precise Response-Rate Data):",
        "siadh_tolvaptan_medicines": "SIADH -- Tolvaptan (Samsca), Real Vasopressin V2-Receptor Antagonist, Real SALT-1/SALT-2 Landmark Trial Data, Hospital-Initiated REMS/Hepatotoxicity-Monitored Therapy:",
        "siadh_demeclocycline_medicines": "SIADH -- Demeclocycline, Real Older Alternative Agent (Real Nephrotoxicity/Phototoxicity-Limited, Real Slower Onset):",
        "siadh_hypertonic_saline_severe_symptomatic_procedure": "SIADH -- Hypertonic (3%) Saline for Real Severe/Symptomatic Acute Hyponatraemia, Real Correction-Rate-Limited Protocol (Osmotic Demyelination Syndrome Prevention):",
        "siadh_oral_urea_salt_tablets_other": "SIADH -- Oral Urea and Sodium Chloride Tablets, Real Additional Options for Real Chronic Long-Term Management (Other):",
        "ttp_therapeutic_plasma_exchange_procedure": "Thrombotic Thrombocytopenic Purpura -- Therapeutic Plasma Exchange (TPE), Real First-Line, Disease-Reversing Emergency Procedure (Canadian Apheresis Study Group RCT):",
        "ttp_corticosteroid_adjunct_medicines": "Thrombotic Thrombocytopenic Purpura -- High-Dose Methylprednisolone Added to Plasma Exchange, Real First Randomized Corticosteroid-Dosing Evidence:",
        "ttp_rituximab_medicines": "Thrombotic Thrombocytopenic Purpura -- Rituximab, Real Anti-CD20 Monoclonal Antibody Reducing Relapse and Mortality in Acquired TTP:",
        "ttp_caplacizumab_medicines": "Thrombotic Thrombocytopenic Purpura -- Caplacizumab, Real Newer Anti-von-Willebrand-Factor Nanobody (HERCULES Trial):",
        "ttp_recombinant_adamts13_congenital_medicines": "Thrombotic Thrombocytopenic Purpura -- Recombinant ADAMTS13 (Apadamtase Alfa), Real FDA-Approved Enzyme Replacement for Hereditary/Congenital TTP Only:",
        "rta_type1_distal_potassium_citrate_medicines": "Renal Tubular Acidosis -- Type 1 (Distal) RTA: Potassium Citrate, Real First-Line Alkali (Corrects Acidosis, Hypokalaemia, and Hypocitraturia Together):",
        "rta_type1_distal_sodium_bicarbonate_alternative_medicines": "Renal Tubular Acidosis -- Type 1 (Distal) RTA: Sodium Bicarbonate, Real Alternative Alkali (Less Preferred -- Sodium Load Worsens Hypercalciuria):",
        "rta_adv7103_extended_release_medicines": "Renal Tubular Acidosis -- ADV7103 (Sibnayal), Real Prolonged-Release Potassium Citrate/Potassium Bicarbonate Combination, EMA-Approved First-Line Option:",
        "rta_type1_potassium_supplementation_medicines": "Renal Tubular Acidosis -- Type 1/2 RTA: Additional Potassium Supplementation (Real Necessary Nuance -- Alkali Alone Can Worsen Hypokalaemia):",
        "rta_type1_thiazide_adjunct_medicines": "Renal Tubular Acidosis -- Type 1 (Distal) RTA: Thiazide Diuretics, Real Adjunct to Reduce Hypercalciuria/Nephrocalcinosis Risk:",
        "rta_type1_amiloride_refractory_adjunct_medicines": "Renal Tubular Acidosis -- Type 1 (Distal) RTA: Amiloride, Real Potassium-Sparing Adjunct for Refractory Hypokalaemia (Case-Level Evidence):",
        "rta_type2_proximal_high_dose_alkali_medicines": "Renal Tubular Acidosis -- Type 2 (Proximal) RTA: High-Dose Alkali Therapy, Real Substantially Higher Dose Than Type 1 (Ongoing Bicarbonate Wasting):",
        "rta_type2_proximal_adjunct_electrolyte_medicines": "Renal Tubular Acidosis -- Type 2 (Proximal) RTA: Adjunct Potassium/Phosphate/Sodium/Magnesium/Calcitriol Replacement (Fanconi-Syndrome-Associated Losses):",
        "rta_type4_dietary_potassium_restriction_other": "Renal Tubular Acidosis -- Type 4 (Hyperkalaemic) RTA: Dietary Potassium Restriction, Real First-Step Non-Pharmacological Measure (Other):",
        "rta_type4_loop_diuretic_medicines": "Renal Tubular Acidosis -- Type 4 (Hyperkalaemic) RTA: Loop Diuretics (Furosemide), Real Kaliuretic/Aciduric Therapy:",
        "rta_type4_potassium_binder_medicines": "Renal Tubular Acidosis -- Type 4 (Hyperkalaemic) RTA: Potassium Binders (Calcium Polystyrene Sulfonate/Patiromer/Sodium Zirconium Cyclosilicate):",
        "rta_type4_fludrocortisone_medicines": "Renal Tubular Acidosis -- Type 4 (Hyperkalaemic) RTA: Fludrocortisone, Real Mineralocorticoid Replacement for True Aldosterone Deficiency (Opposite Approach to Type 1/2):",
        "rta_type4_bicarbonate_medicines": "Renal Tubular Acidosis -- Type 4 (Hyperkalaemic) RTA: Sodium Bicarbonate for Acidosis Correction (Adjunct to Potassium-Lowering Measures):",
        "itp_iv_high_dose_corticosteroid_first_line_medicines": "Immune Thrombocytopenic Purpura -- IV High-Dose Methylprednisolone + Oral Prednisone, Real First-Line Rapid Induction Regimen (Godeau et al RCT):",
        "itp_pulsed_high_dose_dexamethasone_first_line_medicines": "Immune Thrombocytopenic Purpura -- Pulsed High-Dose Dexamethasone Monotherapy, Real Modern Guideline First-Line Regimen:",
        "itp_ivig_rapid_response_medicines": "Immune Thrombocytopenic Purpura -- Intravenous Immunoglobulin (IVIG), Real Rapid-Response Rescue Therapy:",
        "itp_romiplostim_tpo_agonist_medicines": "Immune Thrombocytopenic Purpura -- Romiplostim, Real Subcutaneous TPO-Receptor Peptide-Mimetic Agonist for Chronic ITP:",
        "itp_eltrombopag_tpo_agonist_medicines": "Immune Thrombocytopenic Purpura -- Eltrombopag, Real Oral Non-Peptide TPO-Receptor Agonist for Chronic ITP (RAISE Trial):",
        "itp_avatrombopag_tpo_agonist_medicines": "Immune Thrombocytopenic Purpura -- Avatrombopag, Real Newer Oral TPO-Receptor Agonist for Chronic ITP (ADAPT Trial):",
        "itp_rituximab_monotherapy_medicines": "Immune Thrombocytopenic Purpura -- Rituximab Monotherapy, Real Anti-CD20 B-Cell Depletion Therapy for Chronic ITP:",
        "itp_rituximab_dexamethasone_combination_medicines": "Immune Thrombocytopenic Purpura -- Rituximab + Three Cycles of Pulsed Dexamethasone, Real Intensive Combination Regimen (Leading Medical Near-Cure Candidate):",
        "itp_splenectomy_procedure": "Immune Thrombocytopenic Purpura -- Splenectomy, Real Most Durable Disease-Course-Altering Procedure:",
        "itp_fostamatinib_medicines": "Immune Thrombocytopenic Purpura -- Fostamatinib, Real Oral SYK Inhibitor for Refractory Persistent/Chronic ITP (FIT1/FIT2 Trials):",
        "aiha_corticosteroids_first_line_warm_medicines": "Autoimmune Haemolytic Anaemia -- Prednisolone/Prednisone Monotherapy, Real First-Line Warm AIHA Regimen (Birgens 2013 RCT):",
        "aiha_rituximab_warm_medicines": "Autoimmune Haemolytic Anaemia -- Rituximab Added to First-Line Corticosteroids, Real Durable-Remission-Improving Regimen for Warm AIHA (Birgens 2013 RCT, Cochrane 2021):",
        "aiha_splenectomy_warm_second_line_medicines": "Autoimmune Haemolytic Anaemia -- Splenectomy, Real Second-Line Durable Option for Relapsed/Refractory Warm AIHA:",
        "aiha_cold_agglutinin_disease_specific_medicines": "Autoimmune Haemolytic Anaemia -- Cold Agglutinin Disease Specific Therapy (Bendamustine+Rituximab, Sutimlimab), Real Options Where Steroids/Splenectomy Do Not Work Well:",
        "aiha_immunosuppressants_refractory_medicines": "Autoimmune Haemolytic Anaemia -- Azathioprine/Mycophenolate Mofetil, Real Steroid-Sparing Options for Refractory AIHA (BSH Guideline):",
        "aiha_supportive_transfusion_medicines": "Autoimmune Haemolytic Anaemia -- Cross-Matched Packed Red Blood Cell Transfusion, Real Supportive/Emergency Measure:",
        "alphathal_silent_carrier_trait_no_treatment_other": "Alpha Thalassemia -- Silent Carrier / Trait: Real, Honest 'No Treatment Needed' Category:",
        "alphathal_hbh_disease_intermittent_transfusion_medicines": "Alpha Thalassemia -- HbH Disease: Intermittent (Deletional) or Regular (Non-Deletional) Red-Cell Transfusion:",
        "alphathal_hbh_disease_iron_chelation_medicines": "Alpha Thalassemia -- HbH Disease: Iron Chelation Therapy When Transfusion-Dependent (Cross-Referenced Agents):",
        "alphathal_hbh_disease_splenectomy_procedure": "Alpha Thalassemia -- HbH Disease: Splenectomy for Severe Non-Deletional Disease, Real Selective Procedure (Not Routine):",
        "alphathal_hbh_disease_folic_acid_medicines": "Alpha Thalassemia -- HbH Disease: Folic Acid Supplementation for Chronic Haemolysis (Other, Lower Priority):",
        "alphathal_hbbarts_intrauterine_transfusion_procedure": "Alpha Thalassemia -- Hb Bart's Hydrops Fetalis: Intrauterine Transfusion, Real Disease-Course-Transforming Intervention:",
        "alphathal_hbbarts_postnatal_hsct_procedure": "Alpha Thalassemia -- Hb Bart's Hydrops Fetalis Survivors: Postnatal Allogeneic HSCT, Real Curative-Intent Option:",
        "alphathal_hbbarts_postnatal_transfusion_chelation_medicines": "Alpha Thalassemia -- Hb Bart's Hydrops Fetalis Survivors: Lifelong Transfusion + Iron Chelation (Cross-Referenced to Beta Thalassemia Major):",
        "alphathal_genetic_counseling_prenatal_screening_other": "Alpha Thalassemia -- Genetic Counselling and Prenatal/Antenatal Carrier Screening, Real Key Preventive Lever (Other/Preventive):",
        "pv_phlebotomy_procedure": "Polycythemia Vera -- Therapeutic Phlebotomy Targeting Hematocrit <45%, Real First-Line Procedure for All Risk Groups (CYTO-PV Trial):",
        "pv_low_dose_aspirin_medicines": "Polycythemia Vera -- Low-Dose Aspirin 100 mg Daily, Real First-Line Adjunct Antithrombotic Therapy for All Risk Groups (ECLAP Trial):",
        "pv_hydroxyurea_medicines": "Polycythemia Vera -- Hydroxyurea, Real First-Line Cytoreductive Agent for High-Risk Disease:",
        "pv_ruxolitinib_medicines": "Polycythemia Vera -- Ruxolitinib, Real JAK1/2 Inhibitor for Hydroxyurea-Resistant or -Intolerant Disease (RESPONSE Trial):",
        "pv_interferon_alpha_medicines": "Polycythemia Vera -- Pegylated Interferon Alpha-2a, Real Alternative Cytoreductive Option With Distinct Molecular-Response Potential (MPD-RC 112 Trial):",
        "dic_underlying_cause_treatment": "Disseminated Intravascular Coagulation -- Immediate Cause-Directed Therapy (Antibiotics/Source Control, Obstetric Delivery, ATRA/Chemotherapy), Real Guideline-Unanimous Cornerstone:",
        "dic_blood_component_replacement_medicines": "Disseminated Intravascular Coagulation -- Fresh Frozen Plasma, Cryoprecipitate/Fibrinogen Concentrate, and Platelet Transfusion, Real Guideline-Standard Supportive Replacement for Active Bleeding:",
        "dic_heparin_anticoagulation_medicines": "Disseminated Intravascular Coagulation -- Heparin (Unfractionated or LMWH: Enoxaparin/Dalteparin), Real Guideline-Recommended for Thrombosis-Predominant or Prophylactic Use:",
        "dic_recombinant_thrombomodulin_medicines": "Disseminated Intravascular Coagulation -- Recombinant Thrombomodulin (Thrombomodulin Alfa/ART-123, Recomodulin), Real Positive Japanese Phase III Trial vs Real Negative Global SCARLET Mortality RCT:",
        "dic_antithrombin_concentrate_medicines": "Disseminated Intravascular Coagulation -- Antithrombin III Concentrate (Thrombate III/ATryn), Real Negative KyberSept Overall Result With Real Post-Hoc Subgroup Signal:",
        "dic_recombinant_activated_protein_c_medicines_other": "Disseminated Intravascular Coagulation -- Recombinant Activated Protein C (Drotrecogin Alfa/Xigris), Real Negative PROWESS-SHOCK Result, Withdrawn From Market (Historical, Other):",
        "dic_tranexamic_acid_medicines_other": "Disseminated Intravascular Coagulation -- Tranexamic Acid, Real Narrow/Low-Quality Evidence Restricted to Hyperfibrinolytic-Phenotype DIC (Other):",
        "hydro_emergency_decompression_procedure": "Hydronephrosis -- Emergency/Urgent Decompression (Retrograde Double-J Ureteric Stent or Percutaneous Nephrostomy), Real First Priority for Infected or Threatened Obstruction:",
        "hydro_pyeloplasty_procedure": "Hydronephrosis -- Pyeloplasty (Open Anderson-Hynes / Laparoscopic / Robot-Assisted), Real Definitive Surgical Cure of PUJ Obstruction:",
        "hydro_empiric_antibiotic_infected_obstruction_medicines": "Hydronephrosis -- Empiric Broad-Spectrum IV Antibiotics (Ceftriaxone/Piperacillin-Tazobactam/Meropenem), Real Adjunct to Urgent Decompression for Infected Obstruction:",
        "hydro_alpha_blocker_met_medicines": "Hydronephrosis -- Alpha-1-Blocker Medical Expulsive Therapy (Tamsulosin/Alfuzosin/Silodosin) for Stone-Related Obstruction, Real Evidence-Evolution Story (Meta-Analyses vs SUSPEND RCT):",
        "hydro_nsaid_analgesia_medicines": "Hydronephrosis -- NSAID Analgesia (Diclofenac/Ketorolac/Ibuprofen) for Acute Obstructive (Renal Colic) Pain, Real Non-Curative Symptom Control:",
        "hydro_conservative_watchful_waiting_antenatal_pediatric": "Hydronephrosis -- Conservative Surveillance for Mild-to-Moderate Isolated Antenatal/Neonatal Hydronephrosis, Real Evidence-Based Non-Treatment:",
        "mf_ruxolitinib_medicines": "Myelofibrosis -- Ruxolitinib, Real First-Line JAK1/2 Inhibitor for Intermediate-2/High-Risk Disease (COMFORT-I/COMFORT-II Trials):",
        "mf_fedratinib_medicines": "Myelofibrosis -- Fedratinib, Real JAK2-Selective Inhibitor for First-Line and Ruxolitinib-Resistant/Intolerant Disease (JAKARTA/JAKARTA-2 Trials):",
        "mf_pacritinib_medicines": "Myelofibrosis -- Pacritinib, Real JAK2/IRAK1 Inhibitor for Disease With Severe Thrombocytopenia (PERSIST-2 Trial):",
        "mf_momelotinib_medicines": "Myelofibrosis -- Momelotinib, Real JAK1/JAK2/ACVR1 Inhibitor for Anaemia After Prior JAK-Inhibitor Therapy (MOMENTUM Trial):",
        "mf_danazol_supportive_medicine": "Myelofibrosis -- Danazol, Real Attenuated-Androgen Supportive Therapy for Anaemia:",
        "mf_hydroxyurea_medicine": "Myelofibrosis -- Hydroxyurea, Real Cytoreductive Medicine for Hyperproliferative Disease (Splenomegaly/Thrombocytosis/Leukocytosis):",
        "et_low_dose_aspirin_medicines": "Essential Thrombocythaemia -- Low-Dose Aspirin, Real Targeted (Not Blanket) First-Line Antiplatelet Therapy for JAK2-Positive/Cardiovascular-Risk-Factor Low-Risk Disease (Alvarez-Larran 2010 Blood):",
        "et_hydroxyurea_medicines": "Essential Thrombocythaemia -- Hydroxyurea, Real First-Line Cytoreductive Agent for High-Risk Disease (PT1 Trial, Harrison 2005 NEJM):",
        "et_anagrelide_medicines": "Essential Thrombocythaemia -- Anagrelide, Real Alternative First-/Second-Line Cytoreductive Agent, Non-Inferior in Strict WHO-Classified Disease (ANAHYDRET Trial, Gisslinger 2013 Blood):",
        "et_interferon_medicines": "Essential Thrombocythaemia -- Pegylated Interferon Alpha-2a, Real Alternative First-Line Cytoreductive Option for Younger Patients/Pregnancy Planning (MPD-RC 112 Trial):",
        "et_ruxolitinib_medicines": "Essential Thrombocythaemia -- Ruxolitinib for Hydroxyurea-Resistant/Intolerant Disease, Real Honest Non-Superiority Trial Result vs Best Available Therapy (MAJIC-ET Trial, Harrison 2017 Blood):",
        "et_allogeneic_hsct_procedure": "Essential Thrombocythaemia -- Allogeneic HSCT, The Only Real Curative Option, Reserved for Transformation to Secondary Myelofibrosis/AML (Gagelmann 2019, Kroger 2009):",
        "ch_acute_high_flow_oxygen": "Cluster Headache -- High-Flow 100% Oxygen, Real First-Line Acute Abortive Treatment (Cohen 2009 JAMA RCT):",
        "ch_acute_sumatriptan_and_triptans": "Cluster Headache -- Subcutaneous Sumatriptan and Intranasal Triptans (Zolmitriptan/Sumatriptan Nasal Spray), Real Acute Abortive Treatments:",
        "ch_prophylaxis_verapamil": "Cluster Headache -- Verapamil (High-Dose), Real First-Line Prophylaxis (Leone 2000 RCT, EFNS Guideline):",
        "ch_prophylaxis_alternatives": "Cluster Headache -- Lithium, Topiramate and Methysergide, Real Alternative Prophylactic Agents:",
        "ch_cgrp_monoclonal_antibodies": "Cluster Headache -- Galcanezumab, Real Anti-CGRP Monoclonal Antibody Proven Only for Episodic Disease (Goadsby 2019 NEJM):",
        "ch_transitional_corticosteroids": "Cluster Headache -- Oral/IV Corticosteroids, Real Bridging Therapy While Verapamil Is Titrated:",
        "ch_procedure_occipital_nerve_injection": "Cluster Headache -- Suboccipital/Greater Occipital Nerve Corticosteroid Injection, Real Randomised-Trial-Proven Transitional Procedure (Leroux 2011, Ambrosini 2005):",
        "ch_investigational_civamide": "Cluster Headache -- Intranasal Civamide, Real but Modest Investigational Prophylactic:",
        "ch_negative_and_neutral_evidence": "Cluster Headache -- Fremanezumab and Galcanezumab-in-Chronic-CH, Real Negative Trial Evidence (Honestly Reported, Not Recommended):",
        "bellspalsy_corticosteroid_medicines": "Bell's Palsy -- Oral Corticosteroid (Prednisolone/Prednisone) Within 72 Hours of Onset, Real First-Line Evidence-Based Near-Cure Treatment (Sullivan 2007 NEJM, Cochrane 2016):",
        "bellspalsy_antiviral_medicines": "Bell's Palsy -- Antiviral (Valacyclovir/Acyclovir) Added to Corticosteroid, Real Honest Modest/Inconsistent Added Benefit (Cochrane 2019):",
        "bellspalsy_eye_protection_medicines": "Bell's Palsy -- Lubricating Eye Drops/Ointment + Eye Protection, Real Essential OTC Supportive Care to Prevent Exposure Keratopathy:",
        "bellspalsy_physical_therapy_other": "Bell's Palsy -- Facial Exercises/Neuromuscular Retraining, Real Adjunct to Reduce Synkinesis and Speed Recovery in Severe/Chronic Cases (Other):",
        "vd_cholinesterase_inhibitor_galantamine": "Vascular Dementia -- Galantamine, Real Largest and Most Positive Cholinesterase-Inhibitor Trial in Probable VaD/Mixed AD+CVD (Erkinjuntti 2002 Lancet), Off-Label:",
        "vd_cholinesterase_inhibitor_donepezil": "Vascular Dementia -- Donepezil, Real Small but Inconsistent Global-Function Benefit Across Two Pivotal 24-Week RCTs (Black 2003 Stroke, Wilkinson 2003 Neurology), Off-Label:",
        "vd_cholinesterase_inhibitor_rivastigmine": "Vascular Dementia -- Rivastigmine, Real Smallest Pooled Effect Size Among Cholinesterase Inhibitors Studied, Off-Label:",
        "vd_nmda_antagonist_memantine": "Vascular Dementia -- Memantine, Real Cognitive-Score Improvement Without Significant Global-Function Benefit (MMM300/MMM500 Trials), Off-Label:",
        "vd_overall_cholinesterase_memantine_meta_analysis": "Vascular Dementia -- Pooled Meta-Analysis of All Cholinesterase Inhibitors and Memantine, Honest 'Uncertain Clinical Significance' Verdict (Kavirajan & Schneider 2007 Lancet Neurology):",
        "vd_antihypertensive_intensive_bp_control": "Vascular Dementia -- Intensive Blood Pressure Control, Real Significant MCI/Combined-Outcome Reduction (SPRINT MIND) vs Real Negative General-Population Cochrane Finding:",
        "vd_antihypertensive_secondary_prevention_poststroke": "Vascular Dementia -- Perindopril+Indapamide Post-Stroke BP Lowering, Real Significant Cognitive-Decline Reduction in Higher-Risk Population (PROGRESS Trial):",
        "vd_statin_secondary_prevention": "Vascular Dementia -- Statins, Proven for Secondary Vascular/Stroke Prevention But Real Negative Evidence for Treating Established Cognitive Decline (Cochrane 2014):",
        "vd_antiplatelet_secondary_prevention": "Vascular Dementia -- Antiplatelet Therapy (Aspirin), Proven for Secondary Stroke Prevention But Real Zero-RCT-Evidence Gap for Treating VaD Cognition (Cochrane 2000):",
        "ftd_trazodone_behavioral_symptoms": "Frontotemporal Dementia -- Trazodone, the Only Medicine With a Positive Placebo-Controlled RCT Result in FTD (Lebert 2004):",
        "ftd_ssri_citalopram_sertraline_fluoxetine": "Frontotemporal Dementia -- SSRIs (Citalopram, Sertraline, Fluoxetine) for Disinhibition, Irritability and Compulsive/Overeating Behaviour:",
        "ftd_atypical_antipsychotics_quetiapine_caution": "Frontotemporal Dementia -- Atypical Antipsychotics (Quetiapine) for Safety-Critical Aggression/Self-Harm, Real Benefit Weighed Against a Real Mortality Signal (Schneider 2005):",
        "ftd_cholinesterase_inhibitors_negative_may_worsen": "Frontotemporal Dementia -- Cholinesterase Inhibitors (Donepezil/Rivastigmine/Galantamine), Real Negative/Harmful Evidence, NOT Recommended in bvFTD (Mendez 2007):",
        "ftd_memantine_negative": "Frontotemporal Dementia -- Memantine, Real Negative Result in Two Randomised Placebo-Controlled Trials (Boxer 2013, Vercelletto 2011):",
        "ftd_paroxetine_negative": "Frontotemporal Dementia -- Paroxetine, Real Negative RCT With Objective Cognitive Worsening (Deakin 2004):",
        "ftd_grn_gene_replacement_investigational": "Frontotemporal Dementia -- GRN Gene-Replacement AAV Gene Therapy (PROCLAIM/ASPIRE-FTD/upliFT-D), Real Early-Phase Investigational Trials:",
        "ftd_latozinemab_failed_phase3_cautionary": "Frontotemporal Dementia -- Latozinemab (AL001), Real Phase 1 Biomarker Success but Real Phase 3 Clinical Trial Failure (INFRONT-3, Terminated):",
        "ftd_nonpharmacological_management": "Frontotemporal Dementia -- Non-Pharmacological Management: Caregiver Education, Structured Environment and Speech-Language Therapy:",
        "glioma_surgery_maximal_safe_resection": "Glioma (Brain Tumour) -- Maximal Safe Surgical Resection, Real Foundational Curative-Intent Step Across Grades (Brown 2016 JAMA Oncology Meta-Analysis):",
        "glioma_pcv_chemotherapy_oligodendroglioma_1p19q_codeleted": "Glioma (Brain Tumour) -- PCV Chemotherapy (Procarbazine/Lomustine/Vincristine) + Radiotherapy, Real Long-Term Survival in 1p/19q-Codeleted Oligodendroglioma (RTOG 9402, EORTC 26951):",
        "glioma_radiotherapy_temozolomide_stupp_protocol_gbm": "Glioma (Brain Tumour) -- Stupp Protocol (Radiotherapy + Temozolomide), Real Standard of Care for IDH-Wildtype Glioblastoma (Stupp 2005 NEJM, 2009 Lancet Oncology):",
        "glioma_mgmt_methylation_biomarker_temozolomide_benefit": "Glioma (Brain Tumour) -- MGMT Promoter Methylation Testing, Real Predictive Biomarker for Temozolomide Benefit (Hegi 2005 NEJM):",
        "glioma_tumor_treating_fields_optune_ef14": "Glioma (Brain Tumour) -- Tumor Treating Fields (Optune) + Maintenance Temozolomide, Real Survival Benefit in Glioblastoma (EF-14 Trial, Stupp 2017 JAMA):",
        "glioma_bevacizumab_recurrent_response_rate": "Glioma (Brain Tumour) -- Bevacizumab +/- Irinotecan, Real Objective Response Rate in Recurrent Glioblastoma (BRAIN Study, Friedman 2009):",
        "glioma_bevacizumab_newly_diagnosed_no_survival_benefit": "Glioma (Brain Tumour) -- Bevacizumab Added Upfront to Radiotherapy+Temozolomide, Real Honest Negative Overall-Survival Result (AVAglio Trial, Chinot 2014 NEJM):",
        "mng_surgical_resection": "Meningioma -- Microsurgical Resection (Simpson-Graded Extent of Removal), Real Closest-to-Cure First-Line Treatment (Simpson 1957, Gousias 2016 J Neurosurg):",
        "mng_stereotactic_radiosurgery": "Meningioma -- Stereotactic Radiosurgery (Gamma Knife/LINAC SRS) for Small/Surgically-Inaccessible WHO Grade I Tumours, Real High Long-Term Local Control (Marchetti 2020 ISRS Guideline):",
        "mng_fractionated_radiotherapy": "Meningioma -- Adjuvant Fractionated Radiotherapy for Atypical/Anaplastic (WHO Grade II/III) or Subtotally-Resected Tumours, Real NRG Oncology/RTOG 0539 Evidence:",
        "mng_watchful_waiting": "Meningioma -- Watchful Waiting With Serial MRI for Small Asymptomatic Incidental Tumours, Real Natural-History Data (Yano & Kuratsu 2006 J Neurosurg):",
        "mng_systemic_drug_therapy_no_proven_cure": "Meningioma -- Systemic Drug Therapy for Recurrent/Refractory Disease, Honestly No Proven-Effective/Curative Drug Exists (Bevacizumab, Everolimus+Octreotide, Sunitinib, Hydroxyurea):",
        "enceph_hsv_vzv_antiviral": "Encephalitis -- IV Aciclovir, Real Time-Critical Curative-Intent Antiviral for HSV/VZV Encephalitis (Whitley 1977 and 1986 NEJM Trials):",
        "enceph_hsv_adjunct_steroid_unproven": "Encephalitis -- Adjunctive Dexamethasone With Aciclovir for HSV Encephalitis, Honestly Formally Unproven (GACHE Trial):",
        "enceph_autoimmune_first_line_immunotherapy": "Encephalitis -- First-Line Immunotherapy (IV Methylprednisolone/IVIG/Plasma Exchange) for Autoimmune Anti-NMDA-Receptor Encephalitis (Titulaer 2013 Lancet Neurology):",
        "enceph_autoimmune_second_line_immunotherapy": "Encephalitis -- Second-Line Immunotherapy (Rituximab/Cyclophosphamide) for Autoimmune Encephalitis Not Responding to First-Line Treatment (Titulaer 2013):",
        "enceph_post_hsv_autoimmune_encephalitis": "Encephalitis -- Recognition and Immunotherapy of Autoimmune (Post-HSV) Encephalitis Arising After Apparent Viral Cure (Cleaver 2025 J Infect Meta-Analysis):",
        "enceph_other_viral_no_specific_antiviral_supportive": "Encephalitis -- Supportive Care Only for Japanese Encephalitis/West Nile/Enteroviral and Most Other Viral Encephalitis, Honestly No Specific Antiviral Exists:",
        "enceph_seizure_icp_icu_supportive_care": "Encephalitis -- Seizure Control, Raised-Intracranial-Pressure Management and ICU-Level Supportive Care Across All Causes:",
        "enceph_prevention_vaccination": "Encephalitis -- Vaccination as Real Primary Prevention for Vaccine-Preventable Causes (Japanese Encephalitis, Measles, Rabies):",
        "tn_first_line_carbamazepine_medicines": "Trigeminal Neuralgia -- Carbamazepine, Real First-Line AAN/EFNS Level-A Anticonvulsant (Rockliff & Davis 1966, Campbell 1966):",
        "tn_first_line_oxcarbazepine_medicines": "Trigeminal Neuralgia -- Oxcarbazepine, Real First-Line Alternative With Cleaner Tolerability (Zakrzewska & Patsalos 2002 Pain):",
        "tn_second_line_add_on_medicines": "Trigeminal Neuralgia -- Baclofen, Lamotrigine and Gabapentin, Real Second-Line/Add-On Medicines (Fromm 1984, Zakrzewska 1997, Munoz-Vendrell 2025):",
        "tn_curative_surgery_mvd_procedure": "Trigeminal Neuralgia -- Microvascular Decompression (MVD), Real Closest-to-Cure Surgical Procedure (Barker 1996 NEJM):",
        "tn_radiosurgery_gamma_knife_procedure": "Trigeminal Neuralgia -- Gamma Knife Stereotactic Radiosurgery, Real Non-Invasive Option (871-Patient Multicenter Study 2024):",
        "tn_percutaneous_rf_thermocoagulation_procedure": "Trigeminal Neuralgia -- Percutaneous Radiofrequency Thermocoagulation, Real Largest 25-Year Series (Kanpolat 2001):",
        "tn_percutaneous_balloon_compression_procedure": "Trigeminal Neuralgia -- Percutaneous Balloon Compression, Real 20-Year Review With Near-Universal Immediate Relief (Skirving & Dan 2001):",
        "tn_percutaneous_glycerol_rhizolysis_procedure": "Trigeminal Neuralgia -- Percutaneous Retrogasserian Glycerol Rhizolysis, Real Awake Chemical Ablative Option:",
        "sb_prevention_folic_acid_medicines": "Spina Bifida -- Periconceptional Folic Acid Supplementation, Real Primary Prevention Before Conception, Closest to a Real Cure for This Disease (MRC Vitamin Study 1991, CDC MMWR 2004):",
        "sb_fetal_surgery_procedure": "Spina Bifida -- Prenatal (Fetal, In-Utero) Myelomeningocele Repair, Real Best Treatment Once a Fetus Is Already Affected (MOMS Trial, Adzick 2011 NEJM):",
        "sb_postnatal_surgical_closure_procedure": "Spina Bifida -- Postnatal Surgical Closure of Myelomeningocele, Real Standard of Care When Prenatal Repair Was Not Done:",
        "sb_hydrocephalus_vp_shunt_procedure": "Spina Bifida -- Ventriculoperitoneal (VP) Shunt for Hydrocephalus, Real Standard Management With Honest Lifelong Revision Burden:",
        "sb_bladder_bowel_management_other": "Spina Bifida -- Clean Intermittent Catheterization for Neurogenic Bladder, Real Cornerstone Lifelong Management to Preserve Renal Function (Other):",
        "narc_eds_first_line_wakefulness_medicines": "Narcolepsy -- Modafinil and Armodafinil, Real AASM First-Line/Conditional Wake-Promoting Medicines for Excessive Daytime Sleepiness:",
        "narc_eds_second_line_medicines": "Narcolepsy -- Solriamfetol, Real AASM Strong-Recommendation Dopamine-Norepinephrine Reuptake Inhibitor (TONES Trials):",
        "narc_dual_eds_and_cataplexy_medicines": "Narcolepsy -- Pitolisant, Real Dual-Efficacy Histamine H3-Receptor Antagonist for Both EDS and Cataplexy (HARMONY Trials):",
        "narc_cataplexy_oxybate_medicines": "Narcolepsy -- Sodium Oxybate and Low-Sodium Oxybate (Xywav), Real AASM Strong-Recommendation Nightly Anticataplectic Medicines:",
        "narc_cataplexy_offlabel_antidepressant_medicines": "Narcolepsy -- Venlafaxine, Real Widely-Used Off-Label Anticataplectic Antidepressant (No RCT, Case-Series Evidence Only):",
        "narc_emerging_orexin_receptor_agonist_medicines": "Narcolepsy -- Oveporexton (TAK-861), Real Emerging First-in-Class Orexin Receptor-2 Agonist, Closest to Disease-Modifying (2026 Phase 3 Trials):",
        "sdh_anticoagulation_reversal_medicines": "Subdural Haematoma -- Anticoagulation Reversal Agents (Idarucizumab, Andexanet Alfa, 4-Factor PCC), Real Adjuncts Before Urgent Evacuation:",
        "sdh_mma_embolization_procedure": "Subdural Haematoma -- Middle Meningeal Artery (MMA) Embolization, Real Recurrence-Reduction Injection/Procedure (EMBOLISE/STEM Positive, MAGIC-MT/EMPROTECT Non-Significant):",
        "dys_combination_antidepressant_cbasp_keller2000": "Dysthymia (Persistent Depressive Disorder) -- Antidepressant Combined With CBASP, Real Closest-to-Cure Combination (Keller 2000 NEJM Trial):",
        "dys_cbasp_monotherapy": "Dysthymia (Persistent Depressive Disorder) -- CBASP (Cognitive Behavioral Analysis System of Psychotherapy) Alone:",
        "dys_ssri_snri_and_other_antidepressant_monotherapy_kriston2014": "Dysthymia (Persistent Depressive Disorder) -- SSRI/SNRI/MAOI Antidepressant Monotherapy, Real Comparative Efficacy (Kriston 2014 Network Meta-Analysis):",
        "dys_other_psychotherapies_ipt_generic_cbt": "Dysthymia (Persistent Depressive Disorder) -- Interpersonal Psychotherapy (IPT) and Generic Psychotherapy Alone:",
        "dys_continuation_maintenance_treatment_machmutow2019": "Dysthymia (Persistent Depressive Disorder) -- Continuation and Maintenance Antidepressant Treatment, Real Relapse Prevention (Machmutow 2019 Cochrane Review):",
        "bn_cbt_e_individual_first_line": "Bulimia Nervosa -- Enhanced/Individual Cognitive Behavioural Therapy (CBT-E), Real Gold-Standard First-Line Treatment:",
        "bn_guided_self_help_cbt": "Bulimia Nervosa -- Guided Cognitive-Behavioural Self-Help, Real Lower-Intensity Stepped-Care Option:",
        "bn_interpersonal_psychotherapy": "Bulimia Nervosa -- Interpersonal Psychotherapy (IPT), Real Slower-Acting Alternative to CBT-E:",
        "bn_family_based_treatment_adolescent": "Bulimia Nervosa -- Family-Based Treatment (FBT), Real First-Line Option for Adolescents:",
        "bn_fluoxetine_ssri_only_fda_approved": "Bulimia Nervosa -- Fluoxetine (Prozac) 60 mg/day, the ONLY Real FDA-Approved Medication for Bulimia Nervosa:",
        "bn_topiramate_second_line_offlabel": "Bulimia Nervosa -- Topiramate, Real Off-Label Second-Line Option (Randomized Placebo-Controlled Trial):",
        "bn_bupropion_contraindicated_not_recommended": "Bulimia Nervosa -- Bupropion, Real Documented CONTRAINDICATION (Seizure Risk), Not a Treatment Recommendation:",
        "bed_cbt_individual_group_first_line": "Binge Eating Disorder -- Individual/Group Cognitive Behavioural Therapy (CBT), Real Highest-Remission First-Line Treatment (Wilfley 2002, Grilo 2005):",
        "bed_guided_self_help_cbt": "Binge Eating Disorder -- Guided Self-Help CBT, Real Lower-Intensity Stepped-Care Option (Grilo & Masheb 2005):",
        "bed_interpersonal_psychotherapy": "Binge Eating Disorder -- Interpersonal Psychotherapy (IPT), Real Equally Effective Alternative to CBT (Wilfley 2002):",
        "bed_lisdexamfetamine_fda_approved": "Binge Eating Disorder -- Lisdexamfetamine (Vyvanse), the ONLY Real FDA-Approved Medication Specifically for BED (McElroy 2015, Hudson 2017):",
        "bed_ssri": "Binge Eating Disorder -- Fluoxetine (SSRI) Monotherapy, Real Honest Negative Finding vs Placebo (Grilo 2005):",
        "bed_topiramate_second_line_offlabel": "Binge Eating Disorder -- Topiramate, Real Off-Label Second-Line Option With Real Weight Loss (McElroy 2003):",
        "behd_colchicine_first_line_mucocutaneous_joint": "Behcet's Disease -- Colchicine, Real EULAR First-Line Agent for Mucocutaneous and Joint Involvement (Davatchi 2009, Yurdakul 2001):",
        "behd_tnf_inhibitors_severe_refractory_uveitis": "Behcet's Disease -- TNF Inhibitors (Infliximab, Adalimumab), Real High-Remission-Rate Therapy for Severe/Refractory Uveitis (Ohno 2019 BRIGHT, Ohno 2004, Martin-Varillas 2018):",
        "behd_interferon_alpha_severe_uveitis": "Behcet's Disease -- Interferon Alfa-2a, Real High Response Rate With Durable Drug-Free Remission in Sight-Threatening Uveitis (Kotter 2003):",
        "behd_azathioprine_eye_involvement": "Behcet's Disease -- Azathioprine, Real Landmark RCT Evidence for Eye Involvement (Yazici 1990 NEJM):",
        "behd_corticosteroids_topical_systemic": "Behcet's Disease -- Topical and Systemic Corticosteroids, Real Guideline-Standard Adjunct (EULAR 2018):",
        "ls_guideline_framework_acp2017": "Lumbar Spondylosis -- ACP 2017 Guideline Framework, Real First-Line Order of Operations for Chronic Low Back Pain (Qaseem 2017):",
        "ls_exercise_therapy": "Lumbar Spondylosis -- Structured Exercise Therapy, Real First-Line Guideline-Endorsed Treatment (Hayden 2021 Cochrane Review):",
        "ls_nsaids": "Lumbar Spondylosis -- Oral NSAIDs, Real But Small Add-On Benefit (Enthoven 2016 Cochrane Review):",
        "ls_muscle_relaxants": "Lumbar Spondylosis -- Skeletal Muscle Relaxants, Real Short-Term Benefit for Acute Exacerbations (van Tulder 2003 Cochrane Review):",
        "ls_epidural_steroid_injection_radicular_pain": "Lumbar Spondylosis -- Epidural Corticosteroid Injection, Real Modest Short-Term Benefit for Disc-Related Radicular Pain (Oliveira 2020 Cochrane Review):",
        "ls_epidural_steroid_injection_spinal_stenosis": "Lumbar Spondylosis -- Epidural Corticosteroid Injection for Spinal Stenosis, Honest Negative Trial Result (Friedly 2014 NEJM):",
        "ls_oral_glucocorticoids_sciatica": "Lumbar Spondylosis -- Systemic Glucocorticoids for Sciatica, Real But Uncertain Weak Evidence:",
        "ls_surgical_decompression_spinal_stenosis": "Lumbar Spondylosis -- Surgical Decompression for Spinal Stenosis, Real Replicated Benefit Over Nonsurgical Care (SPORT Trial, Weinstein 2008 NEJM):",
        "ls_surgical_decompression_fusion_spondylolisthesis": "Lumbar Spondylosis -- Decompression With or Without Fusion for Degenerative Spondylolisthesis, Real Substantial Benefit (SPORT Trial, Weinstein 2007 NEJM):",
        "ls_opioids_not_recommended": "Lumbar Spondylosis -- Opioids, Not Recommended as Routine or Early Therapy (ACP 2017 Guideline):",
        "burs_rest_ice_activity_modification": "Bursitis -- Rest, Ice, Activity Modification, Real First-Line Self-Limited-Resolution Track for Aseptic Bursitis:",
        "burs_nsaids": "Bursitis -- Oral NSAIDs (Naproxen/Ibuprofen), Real First-Line Adjunct for Aseptic Bursitis:",
        "burs_aspiration": "Bursitis -- Bursal Aspiration, Real Diagnostic AND Therapeutic Option, Safe in Aseptic Bursitis:",
        "burs_corticosteroid_injection": "Bursitis -- Intrabursal Corticosteroid Injection (Methylprednisolone/Triamcinolone), Real Fastest Relief for Aseptic Bursitis With a Real Quantified Complication Rate:",
        "burs_antibiotics_septic": "Bursitis -- Empirical Antibiotics for Septic Bursitis (Anti-Staphylococcal Oral/IV Agents), Real High Cure Rate:",
        "burs_surgical_bursectomy": "Bursitis -- Surgical Bursectomy (Open or Endoscopic), Real Last-Resort Option for Refractory/Failed Cases:",
        "fs_natural_history_untreated": "Frozen Shoulder -- Untreated Natural History (Pain, Stiffness, Recovery Stages), Real Self-Limited Course (Reeves 1975):",
        "fs_supervised_neglect_home_exercise": "Frozen Shoulder -- Supervised Neglect / Gentle Home Exercise Within Pain Limits, Real First-Line Conservative Track Superior to Intensive Stretching (Diercks 2004 RCT):",
        "fs_intra_articular_corticosteroid_injection": "Frozen Shoulder -- Intra-Articular Corticosteroid Injection (Triamcinolone), Real Fastest Early-Phase Pain and Disability Relief (Carette 2003 and Ryans 2005 RCTs):",
        "fs_oral_corticosteroid_short_course": "Frozen Shoulder -- Short Course Oral Prednisolone, Real Significant but Short-Lived Benefit Only to 6 Weeks (Buchbinder 2004 RCT):",
        "fs_hydrodilatation_distension_arthrography": "Frozen Shoulder -- Hydrodilatation / Arthrographic Distension (Saline + Steroid), Real Short-Term Pain/Function/Range-of-Motion Benefit (Buchbinder 2008 Cochrane Review, Elnady 2020 RCT):",
        "fs_manipulation_under_anesthesia": "Frozen Shoulder -- Manipulation Under Anesthesia, Real High Long-Term Success for Failed Conservative Treatment With an Honest Neutral RCT Against Exercise Alone (Farrell 2005, Kivimaki 2007):",
        "fs_arthroscopic_capsular_release": "Frozen Shoulder -- Arthroscopic Capsular Release, Real Durable Long-Term Option for True Refractory Cases (Le Lievre and Murrell 2012):",
        "rct_arthroscopic_repair_acute_traumatic_small_tears": "Rotator Cuff Tear -- Arthroscopic Repair for Acute Traumatic Small/Medium Tears, Real High Structural Healing and 10-Year Functional Superiority (Ranebo 2020, Moosmayer 2010/2019 RCTs):",
        "rct_subacromial_corticosteroid_injection_short_term_pain_control": "Rotator Cuff Tear -- Subacromial Corticosteroid Injection, Real Strong Short-Term Pain Relief, Honestly Not Disease-Modifying (Blair 1996 RCT, GRASP 2021 RCT):",
        "rct_arthroscopic_repair_large_tears_structural_healing": "Rotator Cuff Tear -- Arthroscopic Repair for Large Tears, Real Majority-Successful but Tear-Size-Reduced Structural Healing (Srikumaran 2020):",
        "rct_physical_therapy_traumatic_tears_avoids_surgery": "Rotator Cuff Tear -- Physiotherapy for Small/Medium Traumatic Tears, Real Surgery-Avoidance Outcome With a Real Quantified Crossover-Failure Rate (Moosmayer 2010/2019 RCT):",
        "rct_arthroscopic_repair_overall_structural_healing_metaanalysis": "Rotator Cuff Tear -- Arthroscopic Repair, Overall Structural Healing Pooled Across the Literature (Longo 2021 Systematic Review/Meta-Analysis):",
        "rct_arthroscopic_repair_massive_tears_structural_healing": "Rotator Cuff Tear -- Arthroscopic Repair for Massive Tears, Real but Reduced Structural Healing for the Hardest Tear Category (Srikumaran 2020):",
        "rct_structured_physiotherapy_degenerative_atraumatic_tears": "Rotator Cuff Tear -- Structured Physiotherapy Alone for Degenerative/Atraumatic Tears, Real Durable Non-Inferiority to Surgery Through 6.2 Years (Kukkonen 2014/2015/2021 RCT Series):",
        "rct_asymptomatic_tears_no_treatment_natural_history": "Rotator Cuff Tear -- No Treatment for Asymptomatic Tears, Real Majority-Favorable Natural-History Finding (Minagawa 2013, Yamamoto 2011):",
        "dmd_corticosteroids_daily_prednisone_deflazacort": "Duchenne Muscular Dystrophy -- Daily Oral Corticosteroids (Prednisone/Deflazacort), Real First-Line Disease-Modifying Therapy for Essentially All Patients:",
        "dmd_vamorolone": "Duchenne Muscular Dystrophy -- Vamorolone (Agamree), Real Newer Dissociative Corticosteroid With Reduced Bone/Growth Toxicity:",
        "dmd_exon_skipping_eteplirsen_exon51": "Duchenne Muscular Dystrophy -- Eteplirsen (Exondys 51), Real Exon-51-Skipping Antisense Oligonucleotide (Largest Single Mutation-Specific Subgroup):",
        "dmd_exon_skipping_golodirsen_viltolarsen_exon53": "Duchenne Muscular Dystrophy -- Golodirsen (Vyondys 53) / Viltolarsen (Viltepso), Real Exon-53-Skipping Antisense Oligonucleotides:",
        "dmd_exon_skipping_casimersen_exon45": "Duchenne Muscular Dystrophy -- Casimersen (Amondys 45), Real Exon-45-Skipping Antisense Oligonucleotide:",
        "dmd_ataluren_nonsense_mutation": "Duchenne Muscular Dystrophy -- Ataluren (Translarna), Real Ribosomal-Readthrough Drug for Nonsense-Mutation DMD (EU-Approved, Not FDA-Approved):",
        "dmd_gene_therapy_elevidys": "Duchenne Muscular Dystrophy -- Delandistrogene Moxeparvovec (Elevidys), Real Newest FDA-Approved AAV Micro-Dystrophin Gene Therapy:",
        "dmd_cardiac_ace_inhibitor_supportive": "Duchenne Muscular Dystrophy -- ACE Inhibitor / ARB for Cardiomyopathy, Real Standard-of-Care Supportive Adjunct (Does Not Treat the Underlying Muscle Disease):",
        "pf_plantar_fascia_specific_stretching_first_line": "Plantar Fasciitis -- Plantar-Fascia-Specific Stretching Exercise (DiGiovanni Protocol), Real Best-Evidenced First-Line Non-Drug Treatment:",
        "pf_corticosteroid_injection_short_term_only": "Plantar Fasciitis -- Corticosteroid Injection, Real Short-Term-Only Benefit With a Real Quantified Rupture Risk:",
        "pf_extracorporeal_shockwave_therapy": "Plantar Fasciitis -- Extracorporeal Shockwave Therapy (ESWT), Real Option for Recalcitrant Cases:",
        "pf_night_splints": "Plantar Fasciitis -- Dorsiflexion Night Splints, Real Adjunct for First-Step Morning Pain:",
        "pf_high_spontaneous_conservative_resolution_rate": "Plantar Fasciitis -- Natural History / High Resolution Rate With Simple Conservative Measures:",
        "sarc_consensus_guideline_frameworks": "Sarcopenia -- EWGSOP2 and AWGS 2019 International Consensus Frameworks, Real Diagnostic-and-Management Guidance:",
        "sarc_exercise_therapy_resistance_training": "Sarcopenia -- Progressive Resistance (Strength) Training, Real Strongest Evidence Base, First-Line Non-Drug Treatment:",
        "sarc_nutritional_interventions_protein_vitd_hmb": "Sarcopenia -- Protein Supplementation, Vitamin D Correction, and HMB, Real Nutritional Adjuncts to Exercise:",
        "sarc_hormonal_investigational_pharmacotherapy": "Sarcopenia -- Testosterone (Off-Label, Low-T Men) and Bimagrumab (Investigational, Not Approved), Real Honest Mixed/Negative Pharmacotherapy Findings:",
        "spl_adolescent_bracing_boston_brace": "Spondylolisthesis -- Modified Boston Brace for Low-Grade Isthmic Disease, Real First-Line High-Success Non-Surgical Option:",
        "spl_core_stabilization_exercise_therapy": "Spondylolisthesis -- Specific Stabilizing (Core/Motor-Control) Exercise Therapy, Real RCT-Confirmed Durable Benefit:",
        "spl_nsaids_symptomatic_analgesia": "Spondylolisthesis -- Oral NSAIDs for Symptomatic Pain Relief, Real But Non-Disease-Modifying:",
        "spl_epidural_steroid_injection_radicular_pain": "Spondylolisthesis -- Epidural Corticosteroid Injection for Radicular Leg Pain, Real Modest Short-Term Benefit:",
        "spl_posterolateral_fusion_adult_isthmic": "Spondylolisthesis -- Posterolateral Spinal Fusion for Adult Isthmic Disease, Real Superior Outcome vs Exercise Alone:",
        "spl_decompression_nonoperative_degenerative_stenosis_sport": "Spondylolisthesis -- Decompressive Laminectomy (+/- Fusion) for Degenerative Disease With Stenosis, Real SPORT-Trial Superiority to Nonoperative Care:",
        "spl_decompression_plus_fusion_vs_decompression_alone": "Spondylolisthesis -- Instrumented Fusion Added to Decompression vs Decompression Alone, Real Reoperation-Rate Reduction:",
        "om_organism_directed_empiric_and_targeted_antibiotics_first_line": "Osteomyelitis -- Organism-Directed IV/Oral Antibiotic Therapy (Empiric Then Culture-Targeted), Real First-Line Systemic Therapy:",
        "om_oral_step_down_oviva_non_inferiority": "Osteomyelitis -- IV-to-Oral Antibiotic Step-Down Strategy, Real OVIVA-Trial-Proven Non-Inferiority:",
        "om_rifampin_combination_implant_biofilm_infections": "Osteomyelitis -- Rifampin-Combination Therapy for Retained-Implant Staphylococcal Infection, Real Quantified Anti-Biofilm Benefit:",
        "om_surgical_debridement_dead_space_management_procedure": "Osteomyelitis -- Surgical Debridement of Necrotic Bone (Sequestrectomy) and Dead-Space Management, Real Second-Priority Procedure for Chronic/Necrotic Disease:",
        "om_local_antibiotic_carrier_dead_space_filler_procedure": "Osteomyelitis -- Local Antibiotic-Eluting Carrier (Bioactive Glass / Calcium Sulfate-Hydroxyapatite Beads), Real Local-Delivery Procedure Adjunct:",
        "om_pediatric_acute_hematogenous_short_course_duration": "Osteomyelitis -- Short-Course (20-Day) IV-to-Oral Therapy for Childhood Acute Haematogenous Disease, Real High-Cure Paediatric Protocol:",
        "om_vertebral_osteomyelitis_six_week_duration": "Osteomyelitis -- 6-Week (vs Traditional 12-Week) Antibiotic Duration for Pyogenic Vertebral Osteomyelitis, Real Non-Inferiority Trial Data:",
        "om_diabetic_foot_osteomyelitis_nonsurgical_antibiotic_alone": "Osteomyelitis -- Antibiotic-Alone (Nonsurgical) Therapy for Diabetic-Foot Disease, Real Option With Honestly Lower Cure Rate Than Debridement:",
        "om_amputation_last_resort_other": "Osteomyelitis -- Minor or Major Amputation, Real Last-Resort Option (Other/Lower Priority):",
        "pmr_low_dose_glucocorticoids_induction": "Polymyalgia Rheumatica -- Low-Dose Oral Prednisone/Prednisolone Induction, Real Dramatic Near-Diagnostic Response:",
        "pmr_glucocorticoid_tapering_and_treatment_duration": "Polymyalgia Rheumatica -- Glucocorticoid Tapering Strategy and Real Treatment-Duration/Discontinuation Data:",
        "pmr_intramuscular_glucocorticoid_alternative_route": "Polymyalgia Rheumatica -- Intramuscular Glucocorticoid, Real Guideline-Recognised Alternative Route:",
        "pmr_methotrexate_steroid_sparing": "Polymyalgia Rheumatica -- Methotrexate, Real Steroid-Sparing DMARD (Caporali 2004, Ferraccioli 1996, van der Veen 1996):",
        "pmr_tocilizumab_relapsing_refractory": "Polymyalgia Rheumatica -- Tocilizumab, Real Randomised-Trial Evidence for Active/Relapsing Disease:",
        "pmr_sarilumab_relapsing_refractory": "Polymyalgia Rheumatica -- Sarilumab (SAPHYR Trial), Real Evidence for Relapse During Glucocorticoid Taper:",
        "pmr_nsaids_limited_adjunct_role": "Polymyalgia Rheumatica -- NSAIDs, Real Limited/Adjunct Role Only:",
        "pmr_relapse_risk_and_glucocorticoid_toxicity_monitoring": "Polymyalgia Rheumatica -- Relapse-Risk and Glucocorticoid-Toxicity Monitoring:",
        "atr_functional_rehabilitation_early_weightbearing_nonoperative": "Achilles Tendon Rupture -- Accelerated Functional (Non-Operative) Rehabilitation With Early Weight-Bearing, Real Paradigm-Shift First-Line Option for Most Patients:",
        "atr_operative_repair_accelerated_functional_rehabilitation": "Achilles Tendon Rupture -- Operative Repair Combined With Accelerated Functional Rehabilitation, Real Lowest Re-Rupture Rate:",
        "atr_surgery_vs_nonsurgery_complication_tradeoff": "Achilles Tendon Rupture -- Surgery-vs-Non-Surgery Complication Trade-Off, Real Honest Evidence Synthesis:",
        "atr_professional_athlete_surgical_repair_return_to_play": "Achilles Tendon Rupture -- Surgical Repair in High-Demand Competitive/Professional Athletes, Real Population-Specific Evidence:",
        "atr_return_to_play_overall_outcomes": "Achilles Tendon Rupture -- Return to Play/Sport, Real Overall Outcome Across All Treatment Pathways:",
        "atr_percutaneous_vs_open_surgical_technique_choice": "Achilles Tendon Rupture -- Percutaneous/Minimally-Invasive vs Open Repair, Real Surgical Technique Choice:",
        "atr_chronic_neglected_rupture_reconstruction_fhl_transfer": "Achilles Tendon Rupture -- Chronic/Neglected Rupture Reconstruction With Flexor Hallucis Longus Transfer, Real Option for Large Tendon Gaps (Other/Lower Priority):",
        "te_eccentric_progressive_loading_exercise_first_line": "Tennis Elbow (Lateral Epicondylitis) -- Progressive Loading / Eccentric Wrist-Extensor Strengthening Exercise, Real Closest-to-Cure First-Line Option:",
        "te_corticosteroid_injection_short_term_relief_long_term_harm": "Tennis Elbow (Lateral Epicondylitis) -- Corticosteroid Injection, Real Short-Term Relief With Real Documented Worse Long-Term Outcome:",
        "te_prp_injection_positive_durable_at_this_site": "Tennis Elbow (Lateral Epicondylitis) -- Platelet-Rich Plasma (PRP) Injection, Real Genuinely Positive and Durable Evidence at This Site:",
        "te_nsaids_topical_and_oral_limited_evidence": "Tennis Elbow (Lateral Epicondylitis) -- Topical and Oral NSAIDs, Real Honestly Limited Evidence:",
        "te_extracorporeal_shockwave_therapy_conflicting_evidence": "Tennis Elbow (Lateral Epicondylitis) -- Extracorporeal Shockwave Therapy (ESWT), Real Honestly Conflicting Evidence (Other/Lower Priority):",
        "gpa_historical_untreated_natural_history": "Granulomatosis with Polyangiitis -- Untreated Natural History, Real Historical Baseline Before Immunosuppressive Therapy:",
        "gpa_induction_cyclophosphamide_glucocorticoids_fauci_nih": "Granulomatosis with Polyangiitis -- Cyclophosphamide + High-Dose Glucocorticoids, the Real Foundational NIH Induction Regimen:",
        "gpa_induction_cyclophosphamide_pulse_dosing_cyclops": "Granulomatosis with Polyangiitis -- Pulse vs Daily Oral Cyclophosphamide Dosing, Real Equivalent Remission at Lower Cumulative Dose:",
        "gpa_induction_rituximab_rave": "Granulomatosis with Polyangiitis -- Rituximab Induction, Real Non-Inferior (Superior in Relapsing Disease) Alternative to Cyclophosphamide:",
        "gpa_maintenance_azathioprine_cycazarem": "Granulomatosis with Polyangiitis -- Azathioprine Maintenance After Cyclophosphamide Induction, Real Non-Inferiority to Continued Cyclophosphamide:",
        "gpa_maintenance_rituximab_mainritsan": "Granulomatosis with Polyangiitis -- Rituximab Maintenance, Real Superiority Over Azathioprine for Preventing Major Relapse:",
        "gpa_early_nonsevere_methotrexate_noram": "Granulomatosis with Polyangiitis -- Methotrexate for Early, Non-Organ-Threatening Disease Only, Real Cyclophosphamide-Sparing Option With Its Real Relapse Caveat:",
        "gpa_glucocorticoid_dosing_plasma_exchange_pexivas": "Granulomatosis with Polyangiitis -- Reduced-Dose Glucocorticoids and Plasma Exchange, Real Non-Inferior Steroid-Sparing Dosing and Real Lack of Added Plasma-Exchange Benefit:",
        "gpa_glucocorticoid_sparing_avacopan_advocate": "Granulomatosis with Polyangiitis -- Avacopan, Real Glucocorticoid-Sparing C5a-Receptor Inhibitor Add-On:",
        "gca_immediate_high_dose_glucocorticoids_vision_preservation": "Giant Cell Arteritis -- Immediate High-Dose Glucocorticoids Started Before Biopsy, the Real Vision-Preserving Emergency Standard:",
        "gca_tocilizumab_giacta_steroid_sparing": "Giant Cell Arteritis -- Tocilizumab, the Real Steroid-Sparing Remission Breakthrough (GiACTA Trial):",
        "gca_methotrexate_adjunct": "Giant Cell Arteritis -- Methotrexate, Real Adjunctive Steroid-Sparing Option:",
        "gca_abatacept_langford": "Giant Cell Arteritis -- Abatacept, Real Phase 2 RCT-Proven Relapse Reduction:",
        "gca_sarilumab_saphyr": "Giant Cell Arteritis -- Sarilumab, Real Phase 3 Trial (Early-Terminated but Numerically Favorable):",
        "gca_leflunomide": "Giant Cell Arteritis -- Leflunomide, Real Cohort-Study Evidence With Efficacy Similar to Methotrexate:",
        "gca_low_dose_aspirin_adjunct": "Giant Cell Arteritis -- Low-Dose Aspirin, Real Adjunct for Cranial Ischemic Event Risk Reduction:",
        "gca_glucocorticoid_monotherapy_comparator": "Giant Cell Arteritis -- Prolonged Glucocorticoid Monotherapy Alone, Real Comparator Showing Why Add-On Therapy Matters (Other/Lower Priority):",
        "tak_glucocorticoid_induction": "Takayasu Arteritis -- High-Dose Glucocorticoids, Real First-Line Remission Induction:",
        "tak_conventional_steroid_sparing_agents": "Takayasu Arteritis -- Methotrexate and Azathioprine, Real Conventional Steroid-Sparing Agents:",
        "tak_biologic_agents_refractory_disease": "Takayasu Arteritis -- Tocilizumab, Anti-TNF Agents, and Abatacept (Real Negative Trial), for Glucocorticoid-Refractory/Relapsing Disease:",
        "tak_revascularization_procedures": "Takayasu Arteritis -- Surgical Bypass vs Endovascular Angioplasty/Stenting for Critical Stenosis, Real More Durable Surgical Option:",
        "pan_historical_context_pretreatment_and_corticosteroid_era": "Polyarteritis Nodosa -- Untreated Natural History and Corticosteroid Monotherapy, Real Historical Baseline Before Modern Risk-Stratified Therapy:",
        "pan_ffs0_corticosteroid_monotherapy_medicines": "Polyarteritis Nodosa -- Prednisone Monotherapy for Five-Factor-Score=0 (Non-Severe) Disease, Real High-Survival First-Line Therapy:",
        "pan_severe_ffs_ge1_cyclophosphamide_corticosteroid_medicines": "Polyarteritis Nodosa -- Cyclophosphamide + High-Dose Prednisone for Five-Factor-Score>=1 (Severe) Disease, Real Guideline-Standard Induction Therapy:",
        "pan_hbv_pan_antiviral_plasma_exchange_curative_regimen_medicines": "Polyarteritis Nodosa -- Short-Course Corticosteroids + Antiviral Therapy + Plasma Exchange for Hepatitis-B-Associated PAN, Real Trigger-Clearing Cure Regimen:",
        "pan_plasma_exchange_procedure": "Polyarteritis Nodosa -- Plasma Exchange (Plasmapheresis) as an Adjunct Procedure, Real Load-Bearing in HBV-PAN but Not Proven Superior as a Routine Addition in Classic Severe PAN:",
        "pan_maintenance_and_relapse_note": "Polyarteritis Nodosa -- Duration of Therapy and Relapse Risk, Real Contrast With ANCA-Associated Vasculitis (Fixed-Duration Induction, Not Indefinite Maintenance):",
        "pm_azathioprine_bunch_trial": "Polymyositis -- Azathioprine Added to Prednisone, Real Bunch et al. Controlled Trial and Long-Term Follow-Up:",
        "pm_ivig_refractory": "Polymyositis/Dermatomyositis -- Intravenous Immunoglobulin (IVIG) for Steroid-Refractory Disease, Real Outcome Data:",
        "pm_rituximab_rim_trial": "Polymyositis/Dermatomyositis -- Rituximab for Refractory Disease, Real RIM Trial Outcome Data:",
        "pm_diagnostic_reclassification_note": "Polymyositis -- Real Diagnostic Reclassification Caveat: Why Modern 'True PM' Prevalence and Outcome Data Differ From Older Cohorts:",
        "dm_first_line_corticosteroids": "Dermatomyositis -- First-Line Induction: Corticosteroids (Prednisone/Prednisolone, IV Methylprednisolone Pulse):",
        "dm_steroid_sparing_methotrexate": "Dermatomyositis -- Steroid-Sparing Agent: Methotrexate, Real PRINTO Randomized Trial Evidence:",
        "dm_steroid_sparing_azathioprine": "Dermatomyositis -- Steroid-Sparing Agent: Azathioprine, Real Bunch Trial and Long-Term Follow-Up:",
        "dm_steroid_sparing_mycophenolate": "Dermatomyositis -- Steroid-Sparing Agent: Mycophenolate Mofetil, Real Skin-Remission Cohort Evidence:",
        "dm_steroid_sparing_calcineurin_inhibitors": "Dermatomyositis -- Steroid-Sparing Agents: Calcineurin Inhibitors (Ciclosporin, Tacrolimus):",
        "dm_ivig": "Dermatomyositis -- Intravenous Immunoglobulin (IVIG, Octagam 10%), Real ProDERM Randomized Trial, FDA-Recognized Indication:",
        "dm_biologics_rituximab": "Dermatomyositis -- Biologic: Rituximab for Refractory Disease, Real RIM Trial Outcome Data:",
        "dm_anti_mda5_rpild_aggressive_therapy": "Dermatomyositis -- Anti-MDA5-Associated Rapidly Progressive Interstitial Lung Disease, Real Immediate Triple-Agent Combination Therapy (Much Worse Prognosis Subset):",
        "pbc_udca_first_line_medicines": "Primary Biliary Cholangitis -- Ursodeoxycholic Acid (UDCA), Real First-Line Therapy for Essentially All Patients at Diagnosis:",
        "pbc_second_line_fxr_agonist_obeticholic_acid_medicines": "Primary Biliary Cholangitis -- Obeticholic Acid (OCA), Real Second-Line FXR Agonist Add-On, Now Real Label-Restricted in Cirrhosis/Portal Hypertension:",
        "pbc_second_line_fibrates_bezafibrate_medicines": "Primary Biliary Cholangitis -- Bezafibrate, Real Off-Label but Placebo-Trial-Proven Second-Line Add-On:",
        "pbc_second_line_ppar_agonists_elafibranor_seladelpar_medicines": "Primary Biliary Cholangitis -- Elafibranor and Seladelpar, Real FDA-Approved (2024) PPAR-Agonist Second-Line Add-Ons:",
        "pbc_liver_transplantation_end_stage_disease": "Primary Biliary Cholangitis -- Liver Transplantation, Real Definitive Procedure for Decompensated Cirrhosis/End-Stage Disease:",
        "pbc_pruritus_symptom_management_medicines": "Primary Biliary Cholangitis -- Cholestyramine and Rifampicin, Real Symptomatic Management of Cholestatic Pruritus (Not Disease-Modifying):",
        "aih_corticosteroid_induction_medicines": "Autoimmune Hepatitis -- Prednisone/Prednisolone, Real First-Line Induction Therapy for Essentially All Patients at Diagnosis (Hlivko 2008, AASLD 2019/Mack 2020, EASL 2015):",
        "aih_azathioprine_maintenance_medicines": "Autoimmune Hepatitis -- Azathioprine, Real Steroid-Sparing Maintenance Agent Added to Corticosteroid Induction (Manns 2010, AASLD 2019, EASL 2015):",
        "aih_budesonide_alternative_induction_medicines": "Autoimmune Hepatitis -- Budesonide (with Azathioprine), Real Placebo/Active-Controlled-Trial-Proven Alternative Induction for Non-Cirrhotic Disease (Manns 2010 Gastroenterology):",
        "aih_mycophenolate_second_line_medicines": "Autoimmune Hepatitis -- Mycophenolate Mofetil, Real Second-Line Substitute for Azathioprine-Intolerant or Azathioprine-Refractory Patients (Hlivko 2008):",
        "aih_liver_transplantation_decompensated_medicines": "Autoimmune Hepatitis -- Liver Transplantation, Real Definitive Rescue Procedure for Decompensated Cirrhosis or Acute Liver Failure (Montano-Loza 2022, Fawzy 2024):",
        "acne_topical_retinoids": "Acne Vulgaris -- Topical Retinoids: Adapalene and Tretinoin, Real First-Line Backbone Therapy (Shalita 1996, Tu 2001):",
        "acne_benzoyl_peroxide_monotherapy": "Acne Vulgaris -- Benzoyl Peroxide Monotherapy, Real OTC Antimicrobial-Resistance-Proof Agent (Lamel 2015 Systematic Review):",
        "acne_fixed_dose_topical_combination_gels": "Acne Vulgaris -- Fixed-Dose Adapalene-Benzoyl Peroxide and Clindamycin-Benzoyl Peroxide Combination Gels (Eichenfield 2010, Lookingbill 1997, Harper 2015):",
        "acne_oral_antibiotics_with_topical_therapy": "Acne Vulgaris -- Oral Doxycycline/Minocycline Combined With Topical Therapy for Moderate-Severe Disease (Nicklas 2019, Skidmore 2003, Moore 2015):",
        "acne_hormonal_therapy_female_patients": "Acne Vulgaris -- Hormonal Therapy for Female Patients: Combined Oral Contraceptives and Spironolactone (Arowojolu 2012 Cochrane, SAFA Trial/Santer 2023 BMJ):",
        "acne_negative_or_neutral_evidence": "Acne Vulgaris -- Negative/Discouraged Practice: Antibiotic Monotherapy Without Benzoyl Peroxide (Real Resistance Risk):",
        "mcas_h1_antihistamines_second_generation": "Mast Cell Activation Syndrome -- Second-Generation Oral H1-Antihistamines: Cetirizine, Fexofenadine, Real First-Line Therapy (Canadian MCAS Guideline 2025):",
        "mcas_h2_antihistamines_combination": "Mast Cell Activation Syndrome -- H2-Antihistamine Add-On: Famotidine, Real Combination Therapy for GI-Predominant Symptoms:",
        "mcas_mast_cell_stabilizers_cromolyn_ketotifen": "Mast Cell Activation Syndrome -- Oral Mast Cell Stabilizers: Cromolyn Sodium and Ketotifen (Soter 1979 NEJM, Frieri 1990 JACI):",
        "mcas_leukotriene_receptor_antagonist_montelukast": "Mast Cell Activation Syndrome -- Leukotriene Receptor Antagonist: Montelukast:",
        "mcas_aspirin_cox_inhibition": "Mast Cell Activation Syndrome -- Aspirin for Prostaglandin D2-Mediated Flushing, Real Third-Line Option:",
        "mcas_oral_corticosteroids_short_course": "Mast Cell Activation Syndrome -- Short-Course Oral Corticosteroids, Real Rescue Option for Refractory Flares:",
        "mcas_omalizumab_refractory": "Mast Cell Activation Syndrome -- Omalizumab (Anti-IgE) for Refractory Disease, Real Fourth-Line Injectable Option (Systematic Review 2025):",
        "mcas_epinephrine_acute_anaphylactoid_episodes": "Mast Cell Activation Syndrome -- Intramuscular Epinephrine, Real Acute Rescue for Anaphylactoid Episodes:",
        "mcas_negative_or_unproven_evidence": "Mast Cell Activation Syndrome -- Negative/Unproven Evidence: Montelukast Monotherapy, Diet-Only Claims:",
        "ald_complete_abstinence": "Alcoholic Liver Disease -- Complete Alcohol Abstinence, Real Cure-Story for Early-Stage (Pure Fatty Liver) Disease (Teli 1995):",
        "ald_corticosteroids_lille_guided": "Alcoholic Liver Disease -- Prednisolone, Lille-Score-Guided, for Severe Alcoholic Hepatitis (STOPAH 2015, Louvet 2007):",
        "ald_nac_corticosteroid_combination": "Alcoholic Liver Disease -- Prednisolone + N-Acetylcysteine Combination, Real Short-Term Survival Benefit (Nguyen-Khac 2011):",
        "ald_nutritional_support": "Alcoholic Liver Disease -- Nutritional Support, Real Mortality-Halving Benefit of Hitting Caloric Target (Moreno 2016):",
        "ald_early_liver_transplant_steroid_nonresponders": "Alcoholic Liver Disease -- Early Liver Transplantation for Steroid Non-Responders, Real Dramatic Survival Gain With Strict Selection (Mathurin 2011):",
        "ald_pentoxifylline_negative_evidence": "Alcoholic Liver Disease -- Pentoxifylline, Real Negative Evidence, No Longer Recommended (STOPAH 2015):",
        "aapp_antibiotics_appac_regimen": "Acute Appendicitis -- IV Ertapenem then Oral Levofloxacin + Metronidazole (APPAC Regimen), Real Evidence-Based Antibiotics-Alone Option for Uncomplicated Disease (Salminen 2015 JAMA):",
        "aapp_antibiotics_appac2_moxifloxacin": "Acute Appendicitis -- Oral Moxifloxacin Monotherapy (APPAC II Regimen), Real Simplified All-Oral Alternative (Sippola 2021 JAMA):",
        "aapp_antibiotics_coda_regimen": "Acute Appendicitis -- 10-Day Antibiotic Course (CODA Trial Protocol), Real US Multicentre Evidence Including the Appendicolith Subgroup (Flum 2020 NEJM):",
        "aapp_iv_antibiotics_complicated_appendicitis": "Acute Appendicitis -- Broad-Spectrum IV Antibiotics for Complicated (Perforated/Gangrenous/Abscess-Forming) Disease, Real Adjunct to Surgical Source Control:",
        "aapp_laparoscopic_appendectomy": "Acute Appendicitis -- Laparoscopic Appendectomy, Real Preferred Definitive Cure (APPAC 2015 JAMA; Jaschinski 2018 Cochrane):",
        "aapp_open_appendectomy": "Acute Appendicitis -- Open Appendectomy, Real Necessary Alternative for Specific Scenarios (Jaschinski 2018 Cochrane):",
        "aapp_analgesia_supportive_care": "Acute Appendicitis -- Perioperative Analgesia and Supportive Care, Real Non-Curative Adjunct Alongside Definitive Treatment:",
        "ec_endoscopic_resection_t1a_mucosal_disease": "Oesophageal Cancer -- Endoscopic Resection (EMR/ESD), Real Leading Cure Story for T1a Mucosal Disease (Pech 2014 Gastroenterology):",
        "ec_cross_neoadjuvant_chemoradiation_plus_surgery": "Oesophageal Cancer -- CROSS-Protocol Neoadjuvant Chemoradiotherapy Plus Surgery, Real Standard of Care for Locally Advanced Resectable Disease (van Hagen 2012 NEJM, Shapiro 2015 Lancet Oncol):",
        "ec_checkmate577_adjuvant_nivolumab": "Oesophageal Cancer -- Adjuvant Nivolumab for Residual Disease After Neoadjuvant Chemoradiotherapy and Surgery (CheckMate 577, Kelly 2021 NEJM):",
        "ec_definitive_chemoradiation_unresectable_rtog8501": "Oesophageal Cancer -- Definitive Chemoradiotherapy for Unresectable Disease (RTOG 85-01, Cooper 1999 JAMA):",
        "ec_keynote590_first_line_pembrolizumab_chemotherapy": "Oesophageal Cancer -- Pembrolizumab Plus Chemotherapy, Real First-Line Standard for Advanced/Metastatic Disease (KEYNOTE-590, Sun 2021 Lancet):",
        "ec_attraction3_second_line_nivolumab": "Oesophageal Cancer -- Nivolumab, Real Second-Line Option for Advanced Squamous-Cell Carcinoma (ATTRACTION-3, Kato 2019 Lancet Oncol):",
        "aki_cause_directed_therapy_overarching": "Acute Kidney Injury -- Identification and Treatment of the Underlying Cause, Real Highest-Priority Strategy (Kaufman 1991, Liano 1996):",
        "aki_fluid_resuscitation_prerenal": "Acute Kidney Injury -- Isotonic Crystalloid Fluid Resuscitation for Pre-Renal AKI and Contrast-Induced AKI Prevention (SMART Trial; Mueller 2002):",
        "aki_nephrotoxic_agent_discontinuation": "Acute Kidney Injury -- Immediate Discontinuation of Nephrotoxic and Renally-Cleared Drugs, Real Mandatory First Step (KDIGO 2012):",
        "aki_renal_replacement_therapy_severe": "Acute Kidney Injury -- Renal Replacement Therapy (Dialysis) for Severe AKI, Real Evidence on Timing (ELAIN; AKIKI; IDEAL-ICU; STARRT-AKI):",
        "ns_corticosteroids_first_line": "Nephrotic Syndrome -- Oral Corticosteroids, Real First-Line Therapy for Minimal Change Disease (IPNA 2023):",
        "ns_calcineurin_inhibitors_srns": "Nephrotic Syndrome -- Calcineurin Inhibitors, Real Mainstay for Steroid-Resistant Disease (Cochrane 2019):",
        "ns_rituximab": "Nephrotic Syndrome -- Rituximab for Steroid-Dependent/Frequently-Relapsing Disease and Membranous Nephropathy (Iijima 2014; MENTOR 2019):",
        "ns_other_steroid_sparing_agents": "Nephrotic Syndrome -- Levamisole, Mycophenolate Mofetil, Cyclophosphamide/Chlorambucil, Real Alternative Steroid-Sparing Agents (Cochrane 2024):",
        "ns_membranous_nephropathy_alkylating_regimen": "Nephrotic Syndrome -- Cyclophosphamide/Chlorambucil + Corticosteroids for Adult Membranous Nephropathy (Cochrane 2021):",
        "ns_raas_blockade_aceiarb": "Nephrotic Syndrome -- ACE Inhibitors/ARBs, Real Adjunct Proteinuria-Reduction Therapy (GISEN/REIN 1997):",
        "ns_diuretics_edema_management": "Nephrotic Syndrome -- Loop Diuretics +/- Albumin Infusion, Real Symptomatic Edema Management:",
        "hn_raas_blockade_first_line": "Hypertensive Nephropathy -- ACE Inhibitors (Ramipril, Lisinopril), Real First-Line Blood-Pressure-Independent Renoprotection (REIN, Ruggenenti 1999; AASK, Wright 2002):",
        "hn_blood_pressure_targets": "Hypertensive Nephropathy -- Blood-Pressure-Target Strategies, Real Benefit Concentrated in Proteinuric Patients (AASK Cohort Study, Appel 2010; SPRINT, Wright 2015; REIN-2, Ruggenenti 2005):",
        "hn_add_on_and_comparator_antihypertensives": "Hypertensive Nephropathy -- Amlodipine and Metoprolol, Real Add-On/Comparator Antihypertensives (AASK, Wright 2002; Agodoa 2001):",
        "ic_hunner_lesion_fulguration_transurethral_coagulation": "Interstitial Cystitis -- Transurethral Fulguration/Coagulation of Hunner Lesions, Real Best-Responding Treatment for the Hunner-Lesion-Positive Subtype (Ko 2020 Eur Urol RCT; Ogawa 2014; Malde 2021):",
        "ic_bladder_hydrodistension_diagnostic_and_modest_therapeutic": "Interstitial Cystitis -- Cystoscopy Under Anesthesia with Hydrodistension, Real Diagnostic Step With Modest, Short-Lived Therapeutic Effect (Chen 2018 Systematic Review):",
        "ic_oral_pentosan_polysulfate_sodium": "Interstitial Cystitis -- Oral Pentosan Polysulfate Sodium, Real But Honestly Modest/Inconsistent Modern Trial Evidence (Nickel 2015 J Urol; Xie 2019; Davis 2008; Sairanen 2005):",
        "ic_intravesical_dmso_instillation": "Interstitial Cystitis -- Intravesical Dimethyl Sulfoxide (DMSO), Real Only FDA-Approved Intravesical Agent (Perez-Marrero 1988 RCT):",
        "ic_intravesical_heparin_instillation": "Interstitial Cystitis -- Intravesical Heparin Instillation, Real Glycosaminoglycan-Replacement Therapy (Parsons 1994; Nickel 2015 Can J Urol):",
        "ic_oral_amitriptyline": "Interstitial Cystitis -- Oral Amitriptyline, Real Second-Line Tricyclic With Adherence-Dependent Trial Evidence (van Ophoven 2004; Foster 2010 ICCTG):",
        "ic_oral_cyclosporine_a_refractory": "Interstitial Cystitis -- Oral Cyclosporine A, Real Most Effective Single Oral Agent in Head-to-Head Data, Reserved for Refractory Disease (Sairanen 2005; Lai 2020):",
        "cs_transsphenoidal_surgery_pituitary_cushings_disease": "Cushing's Syndrome -- Transsphenoidal Surgery, Real First-Line Genuine Cure for Pituitary Cushing's Disease (Pivonello 2015; Broersen 2018):",
        "cs_unilateral_adrenalectomy_adrenal_adenoma": "Cushing's Syndrome -- Unilateral Adrenalectomy, Real Highest-Rate Genuine Cure for Adrenal-Adenoma-Caused Disease (He 2012; Imai 1996):",
        "cs_pituitary_radiotherapy_radiosurgery": "Cushing's Syndrome -- Pituitary Radiotherapy/Stereotactic Radiosurgery, Real Second-Line Option After Failed Surgery (Gupta 2018):",
        "cs_bilateral_adrenalectomy_refractory": "Cushing's Syndrome -- Bilateral Adrenalectomy, Real Near-Complete Biochemical Control for Refractory Disease, Honestly Management Not Cure (Imai 1996):",
        "cs_steroidogenesis_inhibitor_osilodrostat": "Cushing's Syndrome -- Osilodrostat, Real Newest Highest-Response Oral Steroidogenesis Inhibitor (LINC 3, Pivonello 2020):",
        "cs_steroidogenesis_inhibitors_ketoconazole_metyrapone": "Cushing's Syndrome -- Ketoconazole and Metyrapone, Real Long-Established Oral Steroidogenesis Inhibitors (Viecceli 2023; Daniel 2015):",
        "cs_glucocorticoid_receptor_antagonist_mifepristone": "Cushing's Syndrome -- Mifepristone, Real Glucocorticoid Receptor Antagonist for Diabetes/Glucose Intolerance or Hypertension (SEISMIC, Fleseriu 2012):",
        "cs_pasireotide_persistent_recurrent": "Cushing's Syndrome -- Pasireotide, Real Pituitary-Directed Somatostatin Analog for Persistent/Recurrent Disease (Colao 2012 NEJM):",
        "tcd_lobectomy_low_risk_definitive_surgery": "Thyroid Cancer (Differentiated) -- Thyroid Lobectomy Alone, Real ATA-Recommended Definitive Cure for Low-Risk Small Tumours (Bilimoria 2007; ATA 2015 Guideline):",
        "tcd_total_thyroidectomy_higher_risk_surgery": "Thyroid Cancer (Differentiated) -- Total Thyroidectomy, Real Standard for Higher-Risk/Larger Disease (Bilimoria 2007; ATA 2015 Guideline):",
        "tcd_radioactive_iodine_ablation": "Thyroid Cancer (Differentiated) -- Postoperative Radioactive Iodine (RAI) Ablation, Real Low-Dose-Preferred Regimen (ESTIMABL, Schlumberger 2012 NEJM; HiLo, Mallick 2012 NEJM):",
        "tcd_tsh_suppression_levothyroxine": "Thyroid Cancer (Differentiated) -- Risk-Stratified TSH Suppression Therapy With Levothyroxine, Real Lifelong Adjunct (McGriff 2002; ATA 2015 Guideline):",
        "tcd_kinase_inhibitors_rai_refractory_advanced": "Thyroid Cancer (Differentiated) -- Lenvatinib and Sorafenib, Real Multikinase Inhibitors for RAI-Refractory Advanced/Metastatic Disease, Honestly Non-Curative (SELECT, Schlumberger 2015 NEJM; DECISION, Brose 2014 Lancet):",
        "men_prophylactic_total_thyroidectomy_ret_risk_stratified": "Multiple Endocrine Neoplasia -- RET-Mutation-Guided Prophylactic Total Thyroidectomy, Real Cure-by-Prevention for MEN2 Medullary Thyroid Carcinoma (Skinner 2005 NEJM; ATA MEN2 Guideline, Wells 2015):",
        "men_pheochromocytoma_cortical_sparing_adrenalectomy": "Multiple Endocrine Neoplasia -- Cortical-Sparing (Subtotal) Adrenalectomy for MEN2 Pheochromocytoma, Real Durable Local Control Without Lifelong Steroid Dependence (Castinetti 2016):",
        "men_parathyroidectomy_men1_men2a_hyperparathyroidism": "Multiple Endocrine Neoplasia -- Subtotal Parathyroidectomy for MEN1/MEN2A Primary Hyperparathyroidism, Real Best Available but Honestly Recurrence-Prone Option (Santucci 2024 Ann Surg; Thakker/English 2025 Lancet Diabetes Endocrinol):",
        "men_pancreatic_net_management_men1": "Multiple Endocrine Neoplasia -- Pancreatic Neuroendocrine Tumour Management in MEN1, Real Active Surveillance vs Surgical Resection (Thakker/English 2025 Lancet Diabetes Endocrinol):",
        "men_pituitary_tumor_management_men1": "Multiple Endocrine Neoplasia -- Pituitary Tumour (Prolactinoma) Management in MEN1, Real Dopamine Agonists First-Line (Thakker/English 2025 Lancet Diabetes Endocrinol):",
        "men_lifelong_biochemical_surveillance": "Multiple Endocrine Neoplasia -- Lifelong Annual Biochemical and Imaging Surveillance, Real Permanent Backbone of MEN1 Care and Post-Thyroidectomy MEN2 Follow-Up (Thakker 2012 MEN1 Guideline; ATA MEN2 Guideline, Wells 2015):",
        "aplas_allogeneic_hsct_sibling_vs_mud": "Aplastic Anaemia -- Allogeneic HSCT, HLA-Matched Sibling Donor vs Matched Unrelated Donor, Real Closest-to-Cure Option (Chen 2018 BBMT; BSH 2024 Guideline):",
        "aplas_atg_cyclosporine_immunosuppression": "Aplastic Anaemia -- Antithymocyte Globulin (ATG) + Cyclosporine Immunosuppression, Real Standard IST With Horse ATG Superior to Rabbit ATG (Scheinberg 2011 NEJM):",
        "aplas_eltrombopag_added_to_ist": "Aplastic Anaemia -- Eltrombopag Added to Standard ATG + Cyclosporine From Treatment Start, Real Higher-Response Guideline-Endorsed Regimen (Townsley 2017 NEJM):",
        "aplas_supportive_care": "Aplastic Anaemia -- Supportive Care (Transfusions, Growth Factors, Infection Prophylaxis), Real Non-Disease-Modifying Bridge to Definitive Therapy (BSH 2024 Guideline):",
        "phpt_parathyroidectomy_focused_mip_ioptH_guided": "Primary Hyperparathyroidism -- Focused/Minimally Invasive Parathyroidectomy (MIP) With Intraoperative PTH Monitoring, Real Definitive Cure for Single-Gland Disease (AAES Guidelines, Wilhelm 2016 JAMA Surg; Ye 2022 JBMR Meta-Analysis):",
        "phpt_parathyroidectomy_bilateral_exploration_multigland": "Primary Hyperparathyroidism -- Bilateral Neck Exploration, Real Definitive Cure for Multigland/Non-Localizing Disease (AAES Guidelines, Wilhelm 2016 JAMA Surg; Ye 2022 JBMR Meta-Analysis):",
        "phpt_cinacalcet_calcimimetic_therapy": "Primary Hyperparathyroidism -- Cinacalcet, Real Calcimimetic Medical Management for Non-Surgical Candidates, Honestly Calcium Control Not Cure (Peacock 2005 JCEM RCT; Peacock 2009/2011 JCEM Long-Term Follow-Up):",
        "phpt_bisphosphonate_bone_protection_nonsurgical": "Primary Hyperparathyroidism -- Alendronate, Real Bone-Protective Adjunct for Non-Surgical Candidates With Low Bone Mass (Khan 2004 JCEM RCT; Khan 2009 Endocr Pract):",
        "phpt_vitamin_d_repletion": "Primary Hyperparathyroidism -- Vitamin D Repletion, Real Guideline-Recommended Correction of Coexisting Deficiency (AAES Guidelines, Wilhelm 2016 JAMA Surg; Bollerslev 2011 Eur J Endocrinol):",
        "wd_dpenicillamine_chelation": "Wilson's Disease -- D-Penicillamine, Real Historic First-Line Oral Copper Chelator (AASLD 2008, EASL 2012, Lowette 2010, Weiss 2011):",
        "wd_trientine_chelation": "Wilson's Disease -- Trientine Tetrahydrochloride, Real Non-Inferior Better-Tolerated Alternative Chelator (CHELATE Trial, Schilsky 2022):",
        "wd_zinc_salts_maintenance": "Wilson's Disease -- Zinc Salts (Zinc Acetate/Sulfate), Real Anti-Absorptive Maintenance/Pre-Symptomatic Therapy (Brewer 1983, Weiss 2011):",
        "wd_liver_transplantation_fulminant_decompensated": "Wilson's Disease -- Liver Transplantation, Real Cure of the Hepatic (Not Neurologic) Disease for Fulminant/Decompensated Cases (Arnon 2011, Schilsky 2014):",
        "wd_dietary_copper_restriction_adjunct": "Wilson's Disease -- Dietary Copper Restriction, Real Adjunctive Measure Only (AASLD 2008, EASL 2012):",
        "mm_daratumumab_quadruplet_induction_regimens": "Multiple Myeloma -- Daratumumab-Based Quadruplet Induction (D-VRd/D-Rd), Real Current Best-Outcome Frontline Standard (PERSEUS, Sonneveld 2024 NEJM; GRIFFIN, Voorhees 2020 Blood; MAIA, Facon 2019 NEJM):",
        "mm_autologous_stem_cell_transplant": "Multiple Myeloma -- Autologous Stem-Cell Transplant, Real Backbone of Frontline Transplant-Eligible Therapy (PERSEUS, Sonneveld 2024 NEJM; GRIFFIN, Voorhees 2020 Blood):",
        "mm_car_t_cilta_cel": "Multiple Myeloma -- Ciltacabtagene Autoleucel (Carvykti), Real BCMA CAR-T Cell Therapy, Deepest/Longest-Durability Response in Relapsed/Refractory Disease (CARTITUDE-1, Berdeja 2021 Lancet; 5-Year Follow-Up, Jagannath 2025 JCO):",
        "mm_car_t_ide_cel": "Multiple Myeloma -- Idecabtagene Vicleucel (Abecma), Real BCMA CAR-T Cell Therapy for Relapsed/Refractory Disease (KarMMa, Munshi 2021 NEJM):",
        "mm_bispecific_teclistamab": "Multiple Myeloma -- Teclistamab (Tecvayli), Real BCMA x CD3 Bispecific Antibody, Off-the-Shelf Alternative to CAR-T (MajesTEC-1, Moreau 2022 NEJM):",
        "mm_bispecific_talquetamab": "Multiple Myeloma -- Talquetamab, Real GPRC5D x CD3 Bispecific Antibody for BCMA-Refractory Disease (MonumenTAL-1, Chari 2022 NEJM):",
        "mm_proteasome_inhibitors": "Multiple Myeloma -- Proteasome Inhibitors (Bortezomib, Carfilzomib), Real Frontline Backbone and Deeper-Response Relapsed-Disease Option (ASPIRE, Stewart 2015 NEJM):",
        "mm_immunomodulatory_drugs": "Multiple Myeloma -- Immunomodulatory Drugs (Lenalidomide, Pomalidomide), Real Frontline Backbone and Post-Lenalidomide-Failure Option (MM-003, San Miguel 2013 Lancet Oncol):",
        "mm_maintenance_therapy": "Multiple Myeloma -- Lenalidomide (+/- Daratumumab) Maintenance Therapy, Real Proven Overall-Survival Benefit (McCarthy 2017 JCO Meta-Analysis; PERSEUS, Sonneveld 2024 NEJM):",
        "cerpal_early_intensive_multidisciplinary_therapy": "Cerebral Palsy -- Early Intensive Physical/Occupational/Speech Therapy (0-2 Years, Goal-Directed, Multidomain), Real Best-Evidenced Functional-Outcome Pathway, Not a Cure (Novak 2017 JAMA Pediatr; Morgan 2021 JAMA Pediatr International Guideline):",
        "cerpal_botulinum_toxin_focal_spasticity": "Cerebral Palsy -- Botulinum Toxin Type A Focal Injection, Real AAN/CNS Level-A Spasticity Reduction, Functional Gain Not Established for Upper Limb (Delgado 2010 Neurology; Klaewkasikum 2022; Gresits 2025):",
        "cerpal_oral_antispasmodics": "Cerebral Palsy -- Oral Antispasmodics (Diazepam, Baclofen, Tizanidine, Dantrolene) for Generalized Spasticity, Real Mixed-Grade Evidence (Delgado 2010 AAN/CNS Practice Parameter):",
        "cerpal_intrathecal_baclofen_pump": "Cerebral Palsy -- Intrathecal Baclofen Pump for Severe Generalized Spasticity, Real 40.25% Spasticity Reduction With Real Complication Risk (Masrour 2024 BMC Neurology Meta-Analysis):",
        "cerpal_selective_dorsal_rhizotomy": "Cerebral Palsy -- Selective Dorsal Rhizotomy, Real Durable Permanent Spasticity Reduction in Selected Ambulant Children (McLaughlin 2002 DMCN RCT Meta-Analysis; Pereira 2026; Otero-Luis 2025):",
        "cerpal_orthopedic_surgical_management": "Cerebral Palsy -- Orthopedic Surgical Management Including Single-Event Multilevel Surgery (SEMLS), Real Gait-Kinematic Improvement, Evidence Base Lacks RCTs (McGinley 2012 DMCN; Lamberts 2016; Edwards 2018):",
        "cerpal_assistive_devices_orthotics": "Cerebral Palsy -- Assistive Devices and Ankle-Foot Orthoses, Real Gait and Motor-Function Improvement Adjunct (Lintanf 2018 Clin Rehabil Meta-Analysis; Betancourt 2019):",
        "ettr_propranolol_first_line": "Essential Tremor -- Propranolol, Real First-Line Beta-Blocker Therapy, AAN Level A Evidence (Zesiewicz 2011 AAN Guideline; Koller & Vetere-Overfield 1989 Neurology; Gorman 1986 JNNP):",
        "ettr_primidone_first_line": "Essential Tremor -- Primidone, Real First-Line Anticonvulsant Therapy, AAN Level A Evidence (Zesiewicz 2011 AAN Guideline; Koller & Vetere-Overfield 1989 Neurology; Findley 1985 JNNP):",
        "ettr_topiramate_second_line": "Essential Tremor -- Topiramate, Real Second-Line Option, AAN Level B Evidence, 208-Patient Multicenter RCT (Ondo 2006 Neurology):",
        "ettr_mrgfus_thalamotomy": "Essential Tremor -- MRI-Guided Focused Ultrasound (MRgFUS) Thalamotomy, Real FDA-Approved Durable Tremor-Suppression Procedure for Medication-Refractory Disease (Elias 2016 NEJM Pivotal RCT):",
        "ettr_deep_brain_stimulation": "Essential Tremor -- Deep Brain Stimulation (VIM Thalamus), Real Durable Tremor-Suppression Procedure With 5-Year Follow-Up Data (Schuurman 2000 NEJM; Pahwa 2006 J Neurosurg):",
        "ettr_botulinum_toxin_focal_hand_tremor": "Essential Tremor -- Botulinum Toxin Type A Injection for Focal/Hand Tremor, Real AAN Level C Evidence (Zesiewicz 2011 AAN Guideline; Jankovic 1996 Movement Disorders RCT):",
        "hd_chorea_first_line_vmat2_inhibitors": "Huntington's Disease -- Tetrabenazine and Deutetrabenazine (VMAT2 Inhibitors), Real First-Line Symptomatic Chorea Therapy, Not Curative (Huntington Study Group 2006 Neurology; Frank 2016 JAMA FIRST-HD; Deeks 2017 Drugs ARC-HD):",
        "hd_chorea_guideline_graded_alternatives": "Huntington's Disease -- AAN 2012 Guideline-Graded Alternative Chorea Options (Amantadine, Riluzole, Nabilone) and Negative-Evidence Drugs (Armstrong & Miyasaki 2012 AAN Guideline):",
        "hd_psychiatric_and_behavioural_symptom_management": "Huntington's Disease -- Antipsychotics and Antidepressants for Psychiatric/Behavioural Symptoms, Real Expert-Consensus Guidance, HD-Specific RCT Evidence Gap Stated Honestly (Anderson 2018 J Huntingtons Dis Consensus Guideline; van Duijn 2007):",
        "hd_multidisciplinary_supportive_care": "Huntington's Disease -- Multidisciplinary Physical, Speech and Swallow Supportive Care, Real Grade-A-Evidenced Motor/Gait Benefit, Not Disease-Modifying (Quinn 2020 Neurology PT Guideline; Zaidi 2023 Oral Dis):",
        "dpn_intensive_glycemic_control_medicines": "Diabetic Neuropathy -- Intensive Glycemic Control, Real Closest-to-a-Cure Prevention/Progression-Halting Approach, Not Reversal of Existing Nerve Damage (DCCT, Nathan 1993 NEJM; DCCT/EDIC, Martin 2014 Diabetes Care):",
        "dpn_first_line_gabapentinoid_medicines": "Diabetic Neuropathy -- Pregabalin and Gabapentin (Gabapentinoids), Real First-Line Symptomatic Pain Control, AAN Level A/B Evidence (Derry 2019 Cochrane; Wiffen 2017 Cochrane; Bril 2011 AAN Guideline):",
        "dpn_snri_medicines": "Diabetic Neuropathy -- Duloxetine (SNRI), Real FDA-Approved Symptomatic Pain Control, AAN Level B Evidence (Lunn 2014 Cochrane; Goldstein 2005 Pain; Bril 2011 AAN Guideline):",
        "dpn_tricyclic_antidepressant_medicines": "Diabetic Neuropathy -- Amitriptyline (Tricyclic Antidepressant), Real Long-Standing Symptomatic Pain Control, Honestly Lower-Quality Modern Trial Evidence (Max 1992 NEJM; Moore 2015 Cochrane; Bril 2011 AAN Guideline):",
        "dpn_antioxidant_medicines": "Diabetic Neuropathy -- Alpha-Lipoic Acid (Thioctic Acid), Real Antioxidant Symptomatic Therapy (Ziegler 2006 SYDNEY 2 Trial, Diabetes Care):",
        "dpn_topical_medicines": "Diabetic Neuropathy -- Topical Capsaicin, Real Modest-Effect Symptomatic Pain Control, AAN Level B Evidence (Derry 2017 Cochrane; Bril 2011 AAN Guideline):",
        "dpn_foot_care_podiatry_preventive_program": "Diabetic Neuropathy -- Structured Foot-Care Education and Podiatry Referral Program, Real Amputation-Risk-Reduction Preventive Measure, Not a Pain or Nerve-Damage Treatment (Litzelman 1993 Ann Intern Med):",
        "pn_vitamin_b12_replacement_deficiency_related": "Peripheral Neuropathy -- Vitamin B12 (Cobalamin) Replacement, Real Curative Treatment for Confirmed Deficiency-Related Neuropathy (Healton 1991 Medicine):",
        "pn_causative_agent_withdrawal_toxic_drug_induced": "Peripheral Neuropathy -- Withdrawal/Dose Reduction of the Causative Toxic Agent or Drug, Real Substantial Reversal for Toxic/Drug-Induced Neuropathy (Seretny 2014 Pain; Devadatta 1960 WHO Bulletin):",
        "pn_ivig_plasma_exchange_autoimmune_cidp": "Peripheral Neuropathy -- Intravenous Immunoglobulin (IVIG), Real Disease-Modifying (Not Curative) Treatment for Autoimmune CIDP (ICE Trial, Hughes 2008 Lancet Neurol):",
        "pn_gabapentinoids_gabapentin_symptomatic": "Peripheral Neuropathy -- Gabapentin, Real Symptomatic Neuropathic Pain Relief (Wiffen 2017 Cochrane Review):",
        "pn_gabapentinoids_pregabalin_symptomatic": "Peripheral Neuropathy -- Pregabalin, Real Symptomatic Neuropathic Pain Relief, With Honest Negative Finding in HIV Neuropathy (Derry 2019 Cochrane Review):",
        "pn_duloxetine_snri_symptomatic": "Peripheral Neuropathy -- Duloxetine (SNRI), Real Symptomatic Pain Relief in Chemotherapy-Induced Peripheral Neuropathy (Smith 2013 JAMA; Lunn 2014 Cochrane Review):",
        "pn_tricyclic_antidepressants_amitriptyline_weak_evidence": "Peripheral Neuropathy -- Amitriptyline (Tricyclic Antidepressant), Real But Honestly Weak Trial Evidence Despite Widespread First-Line Use (Moore 2015 Cochrane Review):",
        "mds_allogeneic_hsct_curative": "Myelodysplastic Syndrome -- Allogeneic Hematopoietic Stem-Cell Transplantation, Real Only Curative Option for Eligible Higher-Risk Patients (BMT CTN 1102, Nakamura 2021 JCO; Cutler 2004 Blood; Koreth 2013 JCO):",
        "mds_hypomethylating_azacitidine": "Myelodysplastic Syndrome -- Azacitidine (Hypomethylating Agent), Real Survival-Extending Standard for Higher-Risk Disease, Not Curative (AZA-001, Fenaux 2009 Lancet Oncol):",
        "mds_hypomethylating_decitabine": "Myelodysplastic Syndrome -- Decitabine (Hypomethylating Agent), Real Progression-Delaying but Overall-Survival Benefit Not Statistically Significant (Lubbert 2011 JCO):",
        "mds_lenalidomide_del5q": "Myelodysplastic Syndrome -- Lenalidomide, Real Subtype-Specific Standard for del(5q) MDS (List 2006 NEJM):",
        "mds_luspatercept_transfusion_dependent_anemia": "Myelodysplastic Syndrome -- Luspatercept, Real Newer Option for Transfusion-Dependent Lower-Risk MDS With Ring Sideroblasts (MEDALIST, Fenaux 2020 NEJM):",
        "mds_esa_erythropoiesis_stimulating_agents": "Myelodysplastic Syndrome -- Erythropoiesis-Stimulating Agents (Epoetin/Darbepoetin) +/- G-CSF, Real First-Line Anemia Management in Lower-Risk Disease (Park 2008 Blood, GFM):",
        "mds_supportive_transfusion_growth_factor_support": "Myelodysplastic Syndrome -- Supportive Transfusion, Iron Chelation and Growth Factor Support, Not Disease-Modifying:",
        "asd_early_intensive_behavioral_intervention": "Autism Spectrum Disorder -- Early Intensive Behavioral Intervention (EIBI/ABA-Based, Started Before Age 4), Real Best-Evidenced Functional-Outcome Pathway, Not a Cure (Lovaas 1987 JCCP; McEachin 1993 Am J Ment Retard; Reichow 2018 Cochrane; Virues-Ortega 2010):",
        "asd_speech_and_occupational_therapy": "Autism Spectrum Disorder -- Speech-Language/AAC and Occupational Therapy (Ayres Sensory Integration), Real But Honestly Lower-Certainty Functional Support (Sandbank 2018 Cochrane; Schaaf 2019; Case-Smith 2015):",
        "asd_medication_for_cooccurring_irritability_aggression": "Autism Spectrum Disorder -- Risperidone and Aripiprazole for Co-Occurring Irritability/Aggression Only, Real FDA-Approved Symptom Control, Not a Core-Symptom Treatment (McCracken 2002 NEJM RUPP; Marcus 2009 JAACAP; Owen 2009 Pediatrics):",
        "asd_social_skills_training": "Autism Spectrum Disorder -- Social Skills Groups and Video Modeling, Real Established/Promising Evidence-Based Practice (Reichow & Volkmar 2010 J Autism Dev Disord):",
        "asd_parent_mediated_intervention": "Autism Spectrum Disorder -- Parent-Mediated Early Intervention, Real Improvement in Parent-Child Interaction, Child-Level Gains Less Certain (Oono 2013 Cochrane):",
        "ocd_exposure_and_response_prevention_therapy": "Obsessive-Compulsive Disorder -- Exposure and Response Prevention (ERP), Real Single Most Effective First-Line Intervention (Foa 2005 Am J Psychiatry RCT):",
        "ocd_high_dose_ssris": "Obsessive-Compulsive Disorder -- High-Dose SSRIs (Fluoxetine, Sertraline, Paroxetine, Fluvoxamine, Escitalopram), Real Effective First-Line Pharmacotherapy, Dose-Dependent Efficacy (Soomro 2008 Cochrane; Bloch 2010 Mol Psychiatry; Hollander 2003):",
        "ocd_clomipramine_tricyclic": "Obsessive-Compulsive Disorder -- Clomipramine (Tricyclic Antidepressant), Real Effective Second-Line Option, More Side Effects Than SSRIs (Foa 2005 Am J Psychiatry RCT):",
        "ocd_ssri_augmentation_with_antipsychotics_refractory": "Obsessive-Compulsive Disorder -- Antipsychotic Augmentation of SSRIs (Aripiprazole, Risperidone, Quetiapine and Class) for SSRI-Refractory Disease, Real Evidence-Based Second-Line Step (Dold 2015 Meta-Analysis):",
        "ocd_deep_brain_stimulation_severe_refractory": "Obsessive-Compulsive Disorder -- Deep Brain Stimulation (Nucleus Accumbens/Internal Capsule), Real FDA Humanitarian-Device-Exemption-Approved Dramatic Symptom Reduction for Severe Treatment-Refractory Disease (Denys 2010 Arch Gen Psychiatry Sham-Controlled RCT):",
        "bdd_high_dose_ssris": "Body Dysmorphic Disorder -- High-Dose SSRIs (Fluoxetine, Sertraline, Escitalopram, Fluvoxamine, Paroxetine), Real Effective First-Line Pharmacotherapy Across the Full Insight Spectrum Including Delusional BDD (Phillips 2002 Arch Gen Psychiatry RCT; Grant & Phillips 2005):",
        "bdd_clomipramine_ssri_refractory": "Body Dysmorphic Disorder -- Clomipramine (Tricyclic Antidepressant) for SSRI-Inadequate/Intolerant Disease, Real Effective Second-Line Option Confirmed Superior to Active Comparator (Hollander 1999 Arch Gen Psychiatry Double-Blind Crossover RCT):",
        "bdd_cbt_adapted_for_bdd": "Body Dysmorphic Disorder -- Cognitive-Behavioral Therapy Specifically Adapted for BDD (CBT-BDD: Exposure, Response Prevention, Perceptual Retraining), Real First-Line Evidence-Based Psychotherapy in Adults and Adolescents (Wilhelm 2014 Behav Ther RCT; Mataix-Cols/Krebs 2015 JAACAP Pilot RCT):",
        "bdd_cosmetic_dermatologic_procedures_not_curative": "Body Dysmorphic Disorder -- Cosmetic Surgery/Dermatologic Procedures, NOT a Real Treatment, Documented to Fail to Resolve BDD and Often Worsen It Despite Patient Satisfaction With the Procedure Itself (Crerand 2006 Plast Reconstr Surg Review; Tignol 2007 Eur Psychiatry 5-Year Prospective Follow-Up):",
        "nslbp_staying_active_vs_bed_rest": "Non-Specific Low Back Pain -- Staying Active Plus Brief Education, Real First-Line Treatment; Bed Rest NOT Recommended (Malmivaara 1995 NEJM RCT, Pengel 2003 BMJ Systematic Review, Dahm 2010 Cochrane Review):",
        "nslbp_nsaids": "Non-Specific Low Back Pain -- NSAIDs, Real Small Added Analgesic Effect for Acute and Chronic Disease (van der Gaag 2020 Cochrane Review, Enthoven 2016 Cochrane Review):",
        "nslbp_exercise_therapy_chronic": "Non-Specific Low Back Pain -- Structured Exercise Therapy, Real First-Line Active Treatment for Subacute/Chronic Disease (Hayden 2021 Cochrane Review):",
        "nslbp_cbt_multidisciplinary_rehab": "Non-Specific Low Back Pain -- CBT/Behavioural Therapy and Multidisciplinary Biopsychosocial Rehabilitation, Real Modest Benefit for Chronic Disease (Henschke 2010 Cochrane Review, Kamper 2014 Cochrane Review):",
        "nslbp_spinal_manipulation": "Non-Specific Low Back Pain -- Spinal Manipulative Therapy, Real Effect Similar to Other Recommended Therapies for Chronic Disease (Rubinstein 2019 BMJ Systematic Review):",
        "nslbp_opioids_and_imaging_not_recommended": "Non-Specific Low Back Pain -- Opioids and Routine Spinal Imaging, NOT Recommended for Uncomplicated Disease (ACP 2017 Guideline, NICE NG59, Chou 2009 Lancet Meta-Analysis):",
        "pdb_zoledronic_acid_iv_first_line": "Paget's Disease of Bone -- Zoledronic Acid IV (Single 5mg Infusion), Real Highest-Rate, Most Durable Biochemical Remission, First-Line (Reid 2005 NEJM HORIZON-Comparator Trial, Hosking 2007 JBMR Extension, Singer/Endocrine Society Guideline 2014):",
        "pdb_risedronate_oral": "Paget's Disease of Bone -- Risedronate Oral (30mg/day x 60 Days), Real Guideline-Listed Oral Alternative, Lower Response/Durability Than IV Zoledronic Acid (Reid 2005 NEJM):",
        "pdb_pamidronate_iv": "Paget's Disease of Bone -- Pamidronate IV (30mg x2 Days Every 3 Months), Real Second-Line IV Option, Honestly Lower Remission Rate Than Zoledronic Acid in Head-to-Head Trial (Merlotti 2007 JBMR):",
        "pdb_calcitonin_older_less_effective": "Paget's Disease of Bone -- Calcitonin (Salmon, Injectable/Intranasal), Real Older, Least Effective Option, Reserved for Bisphosphonate-Intolerant Cases (D'Agostino 1988 Clin Orthop Relat Res):",
        "pdb_surgery_for_complications": "Paget's Disease of Bone -- Surgery (Fracture Fixation, Corrective Osteotomy, Joint Replacement), Real Standard Management for Structural Complications, Not the Underlying Disease Activity (Singer/Endocrine Society Guideline 2014, Corral-Gudino 2017 Cochrane Review):",
        "condd_multisystemic_therapy_intensive_family_community": "Conduct Disorder -- Multisystemic Therapy (MST), Real Intensive Home/Community-Based Family Therapy (Henggeler 1992 Original RCT; Curtis 2004 Meta-Analysis; Hunkin 2025 Reassessment):",
        "condd_parent_management_training": "Conduct Disorder -- Parent Management Training (PMT), Real Randomised-Trial-Supported First-Line Behavioural Treatment (Kazdin 1992 RCT; AACAP 1997 Practice Parameter):",
        "condd_functional_family_therapy": "Conduct Disorder -- Functional Family Therapy (FFT), Real Low-Certainty Signal on Offence/Placement Outcomes (Hunkin 2025 Meta-Analysis):",
        "condd_medication_for_comorbid_adhd_aggression_symptom_targeted": "Conduct Disorder -- Medication for Comorbid ADHD/Aggression Only, Symptom-Targeted, Not Curative (Connor 2002 Stimulant Meta-Analysis; Connor 2000 Clonidine Pilot RCT; Loy 2017 Cochrane Risperidone Review):",
        "condd_school_based_multicomponent_prevention_programs": "Conduct Disorder -- Fast Track School/Family Prevention Program, Real Randomised Reduction in Lifetime Conduct Disorder in High-Risk Children (Conduct Problems Prevention Research Group 2011; Dodge 2015):",
        "adj_brief_supportive_psychotherapy": "Adjustment Disorder -- Brief Supportive Psychotherapy, Real First-Line Low-Intensity Treatment (O'Donnell 2018 J Trauma Stress Systematic Review; Casey 2009 CNS Drugs Review):",
        "adj_cbt_structured": "Adjustment Disorder -- Structured Cognitive Behavioral Therapy (In-Person or Internet-Delivered), Real Best-Evidenced Psychotherapy (Cowansage 2025 Psychiatry Res Meta-Analysis of 16 RCTs; Sanz Cruces 2018 Span J Psychol RCT):",
        "adj_problem_solving_activating_therapy": "Adjustment Disorder -- Structured Problem-Solving/Activating Therapy, Real Cluster-RCT-Verified 100% 12-Month Return-to-Work Outcome (van der Klink 2003 Occup Environ Med Cluster RCT):",
        "adj_short_term_symptomatic_medication": "Adjustment Disorder -- Short-Term Symptomatic Medication for Anxiety/Sleep Only (Etifoxine, Buspirone), Real Adjunct, Not a Substitute for Psychotherapy (Stein 2015 Adv Ther RCT; Casey 2009 CNS Drugs Review):",
        "adj_psychoeducation_stress_management": "Adjustment Disorder -- Psychoeducation and Stress-Management/Relaxation Training, Real Low-Cost Adjunct (O'Donnell 2018 J Trauma Stress Review; Hsiao 2014 Gen Hosp Psychiatry RCT):",
        "ins_cbt_i": "Insomnia Disorder -- Cognitive Behavioral Therapy for Insomnia (CBT-I), Real First-Line AASM/ACP Guideline-Recommended Treatment With Durable Remission (Morin 2009 JAMA RCT; Trauer 2015 Ann Intern Med Meta-Analysis; Edinger 2021 AASM Guideline; Qaseem 2016 ACP Guideline):",
        "ins_zolpidem_z_drugs": "Insomnia Disorder -- Zolpidem and Non-Benzodiazepine Z-Drugs (Zaleplon, Eszopiclone), Real Modest-Effect Second-Line Short-Term Option, FDA-Data Meta-Analysis (Huedo-Medina 2012 BMJ):",
        "ins_dual_orexin_receptor_antagonists": "Insomnia Disorder -- Dual Orexin Receptor Antagonists (Suvorexant, Lemborexant), Real Effective Second-Line Option for Sleep Onset and Maintenance (Herring 2016 Biol Psychiatry; Michelson 2014 Lancet Neurol; Rosenberg 2019 JAMA Netw Open):",
        "ins_low_dose_doxepin": "Insomnia Disorder -- Low-Dose Doxepin (1-6mg), Real Sleep-Maintenance-Targeted Second-Line Option With Favourable Safety Profile (Krystal 2010 Sleep RCT):",
        "ins_ramelteon_melatonin_agonist": "Insomnia Disorder -- Ramelteon (Melatonin MT1/MT2 Receptor Agonist), Real Sleep-Onset-Targeted Option, No Dependence Signal (Erman 2006 Sleep Medicine RCT):",
        "ins_sleep_hygiene_stimulus_control": "Insomnia Disorder -- Stimulus Control and Sleep Restriction Therapy (Single-Component Behavioral Techniques; Sleep Hygiene Alone Not Recommended), Real AASM Guideline-Graded Adjuncts (Edinger 2021 AASM Guideline):",
        "jia_methotrexate": "Juvenile Idiopathic Arthritis -- Methotrexate, Real First-Line Conventional DMARD (Giannini 1992 NEJM USA-USSR RCT):",
        "jia_tnf_inhibitors_etanercept_adalimumab": "Juvenile Idiopathic Arthritis -- TNF Inhibitors for Polyarticular Disease: Etanercept and Adalimumab (Lovell 2000 NEJM; Lovell 2008 NEJM PRINTO/PRCSG):",
        "jia_il1_inhibitors_systemic": "Juvenile Idiopathic Arthritis -- IL-1 Inhibitors for Systemic JIA: Canakinumab and Anakinra (Ruperto 2012 NEJM; Quartier 2011 ANAJIS Trial):",
        "jia_il6_tocilizumab_systemic": "Juvenile Idiopathic Arthritis -- IL-6 Receptor Blocker for Systemic/Polyarticular JIA: Tocilizumab (De Benedetti 2012 NEJM TENDER; Yokota 2008 Lancet):",
        "jia_nsaids_symptom_control": "Juvenile Idiopathic Arthritis -- NSAIDs for Symptom Control Only, Not Disease-Modifying (Ruperto 2005 Arthritis Rheum Meloxicam vs Naproxen RCT):",
        "jia_intraarticular_corticosteroid_oligoarticular": "Juvenile Idiopathic Arthritis -- Intra-Articular Corticosteroid Injection for Oligoarticular Disease, Triamcinolone Hexacetonide Preferred (Zulian 2003 Rheumatology; Ravelli 2017 Lancet ACUTE-JIA):",
        "odd_parent_management_training": "Oppositional Defiant Disorder -- Parent Management Training (PMT), Real First-Line AACAP-Endorsed Behavioral Parent Training (Kazdin 1992 JCCP RCT; Kazdin 1997 JAACAP; Furlong 2012 Cochrane Review):",
        "odd_parent_child_interaction_therapy": "Oppositional Defiant Disorder -- Parent-Child Interaction Therapy (PCIT), Real Best-Evidence Live-Coached Dyadic Treatment, ODD-Specific RCTs (Eyberg 1995; Schuhmann 1998 JCCP RCT; Nixon 2003 JCCP RCT; Hood & Eyberg 2003 3-6yr Follow-Up):",
        "odd_problem_solving_skills_training": "Oppositional Defiant Disorder -- Problem-Solving Skills Training (PSST), Real Child-Directed Adjunct to PMT (Kazdin 1992 JCCP RCT):",
        "odd_medication_comorbid_adhd_aggression": "Oppositional Defiant Disorder -- Medication for Comorbid ADHD/Aggression Only, No FDA-Approved Drug for ODD Itself, Real Symptom-Targeted Stimulant/Non-Stimulant Therapy (AACAP Steiner 2007; MTA Swanson 2001 JAACAP):",
        "odd_school_based_intervention": "Oppositional Defiant Disorder -- School-Based/Teacher-Partnered Behavioral Intervention, Real Cross-Setting Generalization Adjunct (Webster-Stratton 2001 JCPP; Webster-Stratton 2001 JCCP Head Start RCT):",
        "cerv_physical_therapy_exercise": "Cervical Spondylosis -- Structured Exercise Therapy, Real First-Line Conservative Treatment (Gross 2015 Cochrane Review):",
        "cerv_nsaids": "Cervical Spondylosis -- Oral NSAIDs, Real Evidentiary Gap Rated 'Unclear Benefit' (Peloso 2006 Cochrane Review):",
        "cerv_cervical_traction": "Cervical Spondylosis -- Mechanical Cervical Traction, Real Honest Negative/Inconclusive Trial Evidence (Graham 2008 Cochrane Review):",
        "cerv_epidural_steroid_injection_radiculopathy": "Cervical Spondylosis -- Epidural/Transforaminal Corticosteroid Injection for Radiculopathy, Real Mixed Controlled and Uncontrolled Evidence (Anderberg 2007; Persson 2012; Peloso 2006):",
        "cerv_acdf": "Cervical Spondylosis -- Anterior Cervical Discectomy and Fusion (ACDF), Real High Short-Term Success Rate, No Added Benefit Over Physiotherapy at 2 Years in the One Real RCT (Moreland 2004; Peolsson 2013):",
        "cerv_posterior_laminectomy_laminoplasty_myelopathy": "Cervical Spondylosis -- Surgical Decompression for Degenerative Cervical Myelopathy, Real Replicated Functional and Quality-of-Life Gains (AOSpine, Badhiwala 2019):",
        "reac_nsaids_first_line_symptomatic": "Reactive Arthritis -- NSAIDs, Real First-Line Symptomatic Therapy During the Natural Resolution Window (Clegg 1996 Trial-Design Evidence):",
        "reac_antibiotics_chlamydia_triggered": "Reactive Arthritis -- Combination Antibiotics for PCR-Proven Persistent Chlamydia/C. pneumoniae-Induced Disease, Real Positive CARDINAL Trial vs Real Negative Kvien/Sieper Monotherapy Trials (Carter 2010; Kvien 2004; Sieper 1999):",
        "reac_intraarticular_corticosteroid": "Reactive Arthritis -- Intra-Articular Corticosteroid Injection for Persistent Monoarthritis/Oligoarthritis:",
        "reac_sulfasalazine_dva_trial": "Reactive Arthritis -- Sulfasalazine, Real Positive Placebo-Controlled DVA Cooperative Trial for NSAID-Refractory Disease (Clegg 1996):",
        "reac_methotrexate_chronic_disease": "Reactive Arthritis -- Methotrexate for Chronic/Relapsing Disease, Honest Extrapolation From PsA/RA Evidence (No ReA-Specific RCT):",
        "reac_tnf_inhibitor_etanercept": "Reactive Arthritis -- TNF Inhibitor Etanercept for Refractory Chronic Disease, Real Open-Label Pilot Trial (Flagg 2005):",
        "reac_topical_uveitis_and_skin_lesions": "Reactive Arthritis -- Topical Treatment for Uveitis and Keratoderma Blennorrhagicum/Circinate Balanitis Skin Lesions:",
        "gvhd_corticosteroids_firstline": "Graft-versus-Host Disease -- High-Dose Corticosteroids, Real Guideline-Standard First-Line Therapy (MacMillan 2002 BBMT, 443 Patients):",
        "gvhd_ruxolitinib_reach2_reach3": "Graft-versus-Host Disease -- Ruxolitinib, Real FDA-Approved Pivotal Trials for Steroid-Refractory Acute and Chronic Disease (REACH2 Zeiser 2020 NEJM; REACH3 Zeiser 2021 NEJM):",
        "gvhd_ecp": "Graft-versus-Host Disease -- Extracorporeal Photopheresis, Real Randomized-Trial Steroid-Sparing Option for Cutaneous Chronic GVHD (Flowers 2008 Blood RCT):",
        "gvhd_calcineurin_inhibitor_prophylaxis": "Graft-versus-Host Disease -- Calcineurin-Inhibitor-Based Prophylaxis, Real Tacrolimus vs Cyclosporine Prevention Trial (Ratanatharathorn 1998 Blood):",
        "gvhd_second_line_other_agents": "Graft-versus-Host Disease -- Ibrutinib, Real FDA-Approved Second-Line Option for Steroid-Refractory Chronic GVHD (Miklos 2017 Blood):",
        "mctd_pah_endothelin_receptor_antagonists": "Mixed Connective Tissue Disease -- Endothelin Receptor Antagonists (Bosentan, Ambrisentan) for PAH, Real Randomized-Trial Evidence Including CTD-Associated PAH (BREATHE-1, Rubin 2002 NEJM; ARIES-1/2, Galie 2008 Circulation):",
        "mctd_pah_pde5_inhibitors": "Mixed Connective Tissue Disease -- Sildenafil (PDE5 Inhibitor) for PAH, Real Randomized-Trial Evidence Including CTD-Associated PAH (SUPER-1, Galie 2005 NEJM):",
        "mctd_pah_immunosuppressive_treatment": "Mixed Connective Tissue Disease -- Glucocorticoid Plus Immunosuppressant (Cyclophosphamide) for Inflammatory-Phenotype CTD-Associated PAH Including MCTD, Real Outcome Data (Yasuoka 2018 Circ J):",
        "sjog_secretagogue_pilocarpine": "Sjogren's Syndrome -- Pilocarpine (Salagen), Real Highest-Verified-Evidence Oral Secretagogue for Dry Mouth and Dry Eye (Vivino 1999 Arch Intern Med, Papas 2004 J Clin Rheumatol, Ramos-Casals 2010 JAMA Systematic Review):",
        "sjog_secretagogue_cevimeline": "Sjogren's Syndrome -- Cevimeline (Evoxac), Real Highest-Pooled-Responder-Rate Oral Secretagogue for Dry Mouth and Dry Eye (Petrone 2002 Arthritis Rheum, Fife 2002 Arch Intern Med, Ramos-Casals 2010 JAMA Systematic Review):",
        "sjog_topical_artificial_tears_punctal_plugs": "Sjogren's Syndrome -- Artificial Tears, Topical Ocular Ciclosporine and Punctal Plugs for Keratoconjunctivitis Sicca, Real Cochrane-Reviewed Evidence, Honestly Low-Certainty for Plugs (Ervin 2017 Cochrane Review, Ramos-Casals 2010 JAMA, EULAR Ramos-Casals 2020):",
        "sjog_hydroxychloroquine_systemic": "Sjogren's Syndrome -- Hydroxychloroquine for Systemic Symptoms, Real Honest Negative Trial for Sicca Symptoms, Not Spun Positive (JOQUER, Gottenberg 2014 JAMA; EULAR Ramos-Casals 2020):",
        "sjog_rituximab_severe_extraglandular": "Sjogren's Syndrome -- Rituximab for Severe Extraglandular Disease, Real 90% Response in Vasculitis/Cryoglobulinaemia-Associated Neuropathy Subgroup, Honest Negative in Unselected Patients (AIR Registry, Mekinian 2012 Ann Rheum Dis; TEARS, Devauchelle-Pensec 2014 Ann Intern Med; TRACTISS, Bowman 2017 Arthritis Rheumatol):",
        "sjog_immunosuppressants_organ_threatening": "Sjogren's Syndrome -- Conventional Immunosuppressants (Cyclophosphamide, Azathioprine, Mycophenolate) for Organ-Threatening Systemic Disease, Real EULAR-Guideline-Endorsed, Honestly Modest Evidence Level (EULAR Ramos-Casals 2020 Ann Rheum Dis):",
        "compsyn_emergency_fasciotomy_timing_stratified": "Compartment Syndrome -- Emergency Fasciotomy, Real Timing-Stratified Outcome Data (Sheridan & Matsen 1976; Kilinc 2025 Turkey Earthquake Cohort):",
        "compsyn_removal_of_constricting_dressings_casts": "Compartment Syndrome -- Removal/Splitting of Constricting Dressings or Casts, Real First-Line Immediate Measure Pending Fasciotomy (Garfin 1981):",
        "compsyn_limb_positioning_avoid_elevation": "Compartment Syndrome -- Limb Positioning at Heart Level, Avoiding Elevation Above the Heart:",
        "compsyn_delayed_primary_closure_skin_grafting": "Compartment Syndrome -- Delayed Primary Closure of Fasciotomy Wounds (Vessel-Loop Shoelace Technique) vs Skin Grafting, Real Case-Series Outcome Data (Asgari & Spinelli 2000):",
        "compsyn_analgesia": "Compartment Syndrome -- Analgesia (Opioid and/or Regional/Epidural), Real Systematic-Review Evidence on Diagnostic Masking (Mar, Barrington, McGuirk 2009):",
        "kd_ivig_first_line_induction": "Kawasaki Disease -- High-Dose IVIG (2 g/kg, Single Infusion Within 10 Days), Real First-Line Guideline-Standard Therapy (Newburger 1986/1991 NEJM, AHA Guideline McCrindle 2017):",
        "kd_aspirin_adjunct": "Kawasaki Disease -- Aspirin, Real Guideline-Endorsed Adjunct to IVIG (High-Dose Anti-Inflammatory Then Low-Dose Antiplatelet) (Newburger 1986/1991 NEJM, AHA Guideline McCrindle 2017):",
        "kd_ivig_resistant_escalation": "Kawasaki Disease -- IVIG-Resistant/High-Risk Disease Escalation: Second IVIG Dose, Prednisolone (RAISE Trial), or Infliximab (Son 2011, Tremoulet 2014 Lancet):",
        "sebd_topical_ketoconazole_antifungal": "Seborrhoeic Dermatitis -- Topical Ketoconazole 2% (Shampoo/Cream/Gel/Foam), Real Largest-Trial First-Line Antifungal Backbone (Elewski 2007 J Drugs Dermatol, Ortonne 1992 Dermatology, Okokon 2015 Cochrane Review):",
        "sebd_topical_corticosteroids_acute_flares": "Seborrhoeic Dermatitis -- Topical Corticosteroids (Clobetasol Shampoo, Betamethasone, Mild-Potency Agents), Real Short-Course Rescue Therapy for Acute Flares (Kastarinen 2014 Cochrane Review, Reygagne 2007 Cutis):",
        "sebd_topical_calcineurin_inhibitors": "Seborrhoeic Dermatitis -- Topical Calcineurin Inhibitors (Pimecrolimus, Tacrolimus), Real Steroid-Sparing Option for Facial/Periocular Disease, Honestly Mixed ITT/PP Trial Result (Warshaw 2007 JAAD, Kastarinen 2014 Cochrane Review):",
        "sebd_selenium_sulfide_zinc_pyrithione_shampoos": "Seborrhoeic Dermatitis -- Selenium Sulfide 2.5% and Zinc Pyrithione 1% Shampoos, Real Over-the-Counter Alternative/Adjunct (Danby 1993 JAAD, Lorette 2006 Eur J Dermatol):",
        "sebd_oral_antifungals_severe_refractory": "Seborrhoeic Dermatitis -- Oral Itraconazole for Severe/Extensive/Refractory Disease, Real Open-Label Evidence With Honestly-Reported Fading Response Over Time (Kose 2005 JEADV, Shemer 2008 Isr Med Assoc J):",
        "fmf_colchicine_lifelong_therapy": "Familial Mediterranean Fever -- Lifelong Colchicine, Real First-Line Standard of Care Preventing Attacks and Amyloidosis (Zemer 1974 NEJM RCT, Zemer 1986 NEJM 1070-Patient Cohort, EULAR 2016/2024):",
        "fmf_il1_anakinra_colchicine_resistant": "Familial Mediterranean Fever -- Anakinra for Colchicine-Resistant Disease, Real Randomised Placebo-Controlled Trial (Ben-Zvi 2017 Arthritis Rheumatol):",
        "fmf_il1_canakinumab_colchicine_resistant": "Familial Mediterranean Fever -- Canakinumab for Colchicine-Resistant/Intolerant Disease, Real Phase 3 CLUSTER Trial and Real-World Cohort (De Benedetti 2018 NEJM, Karabulut 2022 Rheumatol Int):",
        "fmf_nsaids_acute_attack_symptom_relief": "Familial Mediterranean Fever -- NSAIDs for Acute-Attack Pain Relief, Real Guideline-Supported Symptomatic Adjunct (EULAR 2016/2024):",
        "pemv_rituximab_first_line_ritux3": "Pemphigus Vulgaris -- Rituximab Plus Short-Term Prednisone, Real EADV-Guideline First-Line Therapy, 89% vs 34% Complete Remission Off All Therapy at 24 Months (Ritux 3, Joly 2017 Lancet):",
        "pemv_rituximab_vs_mycophenolate_pemphix": "Pemphigus Vulgaris -- Rituximab vs Mycophenolate Mofetil Head-to-Head Trial, Real 40% vs 10% Sustained Complete Remission at Week 52 (PEMPHIX, Werth 2021 NEJM):",
        "pemv_systemic_corticosteroids_backbone": "Pemphigus Vulgaris -- Systemic Corticosteroids (Prednisone/Prednisolone), Real Historical Backbone Therapy, Honestly Inferior to Combination Therapy Alone (Ritux 3 Joly 2017 Lancet; Chams-Davatchi 2007 JAAD):",
        "pemv_azathioprine_mycophenolate_corticosteroid_sparing": "Pemphigus Vulgaris -- Azathioprine or Mycophenolate Mofetil as Corticosteroid-Sparing Agents, Real Four-Arm Randomised Trial (Chams-Davatchi 2007 JAAD):",
        "pemv_ivig_refractory_disease": "Pemphigus Vulgaris -- Rituximab Plus IVIG for Refractory Disease, Real 82% (9/11) Clinical Remission in a Treatment-Failure Cohort (Ahmed 2006 NEJM):",
        "pemv_topical_oral_mucosal_supportive_care": "Pemphigus Vulgaris -- Topical/Local Care for Oral and Mucosal Lesions, Real Guideline-Endorsed Adjunctive Supportive Therapy, Not a Substitute for Systemic Treatment (EADV S2K Guideline, Joly 2020 JEADV):",
        "bulp_high_potency_topical_corticosteroids": "Bullous Pemphigoid -- High-Potency Topical Clobetasol Propionate (Whole-Body), Real First-Line Therapy Beating Oral Corticosteroids on Survival, 76% vs 58% 1-Year Survival in Extensive Disease (Joly 2002 NEJM Landmark Trial):",
        "bulp_oral_corticosteroids_widespread_disease": "Bullous Pemphigoid -- Oral Corticosteroids (Prednisone/Prednisolone) for Widespread Disease, Real First-Line Alternative, 91% Disease Control at 3 Weeks With Higher Complication Rate (Joly 2002 NEJM, Williams 2017 Lancet BLISTER):",
        "bulp_doxycycline_niacinamide_steroid_sparing": "Bullous Pemphigoid -- Doxycycline and Nicotinamide+Tetracycline, Real Corticosteroid-Sparing/Avoiding Strategies With Significantly Fewer Severe Adverse Events (Williams 2017 Lancet BLISTER Trial, Fivenson 1994 Arch Dermatol):",
        "bulp_azathioprine_mycophenolate_steroid_sparing": "Bullous Pemphigoid -- Azathioprine or Mycophenolate Mofetil as Corticosteroid-Sparing Agents, Real Randomised Trial Data, Honestly Mixed Remission-Rate Benefit (Beissert 2007 Arch Dermatol, Guillaume 1993 Arch Dermatol):",
        "bulp_rituximab_refractory_disease": "Bullous Pemphigoid -- Rituximab for Refractory Disease Failing Conventional Therapy, Real Case-Series Evidence (Kasperkiewicz 2011 JAAD):",
        "cdd_meningococcal_vaccination": "Complement Deficiency Disorders -- Tetravalent Meningococcal Vaccination for Terminal Complement Deficiency, Real 85.7-92.5% Seroprotection Response Rate (Brodszki 2015 Vaccine, Andreoni/Densen 1993 J Infect Dis):",
        "cdd_prophylactic_antibiotics": "Complement Deficiency Disorders -- Long-Term Antibiotic Chemoprophylaxis in Terminal Complement Deficiency, Real Guideline-Endorsed Adjunct to Vaccination (Figueroa/Densen 1991 Clin Microbiol Rev):",
        "cell_empiric_oral_betalactam_nonpurulent_first_line": "Cellulitis -- Empiric Oral Beta-Lactam Therapy (Cephalexin) for Non-Purulent Cellulitis, Real First-Line Cure at 85.5% (Moran 2017 JAMA):",
        "cell_mrsa_active_antibiotics_purulent_or_risk_factor": "Cellulitis -- MRSA-Active Antibiotics (TMP-SMX/Doxycycline/Clindamycin) for Purulent Cellulitis, Abscess, or MRSA Risk Factors, Real 92.9% Cure After Drainage (Talan 2016 NEJM):",
        "cell_iv_antibiotics_severe_or_systemic_disease": "Cellulitis -- Intravenous Antibiotics (Vancomycin/Linezolid) for Severe/Systemic Disease Including Confirmed MRSA, Real 92.2% ITT Cure (Weigelt 2005 AAC):",
        "cell_incision_and_drainage_associated_abscess_procedure": "Cellulitis -- Incision and Drainage of an Associated Abscess, Real Mandatory Source-Control Procedure (Talan 2016 NEJM):",
        "cell_elevation_risk_factor_management_and_secondary_prevention": "Cellulitis -- Limb Elevation, Skin-Barrier/Oedema Risk-Factor Management, and Antibiotic Prophylaxis for Recurrence, Real 69% Recurrence-Risk Reduction (Dalal 2017 Cochrane Review):",
        "imp_topical_mupirocin_localized_first_line": "Impetigo -- Topical Mupirocin 2% Ointment for Localized/Limited Disease, Real First-Line Cure at 98% (Dagan 1992 Antimicrob Agents Chemother):",
        "imp_topical_retapamulin_alternative_including_resistant_organisms": "Impetigo -- Topical Retapamulin 1% Ointment, Real Alternative With Activity Against Resistant Organisms, 99.1% Cure vs Sodium Fusidate (Oranje 2007 Dermatology):",
        "imp_oral_antibiotics_extensive_or_bullous_disease": "Impetigo -- Oral Antibiotics (Dicloxacillin/Cephalexin) for Extensive or Bullous Disease, Real 92% Cure (Dagan 1992 Antimicrob Agents Chemother):",
        "imp_mrsa_active_oral_antibiotics_when_mrsa_suspected_or_confirmed": "Impetigo -- MRSA-Active Oral Antibiotics (Clindamycin/Doxycycline/TMP-SMX) When MRSA Is Suspected or Confirmed, Real IDSA-Endorsed Approach (Stevens 2014 IDSA Guideline):",
        "imp_gentle_debridement_and_hygiene_adjunct": "Impetigo -- Gentle Crust Removal and Hygiene Measures, Real Adjunct Not Standalone Cure (Koning 2012 Cochrane Review):",
        "ros_topical_vasoconstrictors_erythema": "Rosacea -- Topical Vasoconstrictors (Brimonidine 0.5% Gel, Oxymetazoline 1.0% Cream) for Persistent Facial Erythema, Real GRADE High/Moderate-Certainty Pivotal-Trial Evidence (Fowler 2012 Br J Dermatol; Stein-Gold 2018 REVEAL Trials):",
        "ros_topical_anti_inflammatory_papulopustular": "Rosacea -- Topical Anti-Inflammatory Agents (Ivermectin 1% Cream, Metronidazole 0.75% Gel) for Papulopustular Disease, Real GRADE High-Certainty Pivotal-Trial Evidence (Stein 2014 J Drugs Dermatol; Miyachi 2022 J Dermatol):",
        "ros_oral_doxycycline_anti_inflammatory_dose": "Rosacea -- Oral Doxycycline 40 mg Modified-Release (Anti-Inflammatory/Subantimicrobial Dose) for Moderate-to-Severe Papulopustular Disease, Real Phase III RCT Evidence (Del Rosso 2007 J Am Acad Dermatol):",
        "ros_laser_ipl_telangiectasia": "Rosacea -- Vascular Laser (KTP/PDL) and Intense Pulsed Light for Telangiectasia and Refractory Erythema, Real Split-Face RCT Evidence Including Adjunctive Topical Ivermectin (Heidemeyer 2026 J Dermatolog Treat; Nguyen 2026 JDDG Network Meta-Analysis):",
        "ros_oral_isotretinoin_severe_phymatous": "Rosacea -- Low-Dose Oral Isotretinoin for Severe, Phymatous or Treatment-Refractory Disease, Real Meta-Analysis Evidence, Off-Label (King 2025 JEADV Systematic Review/Meta-Analysis):",
        "cdd_c1_inhibitor_concentrate": "Complement Deficiency Disorders -- Nanofiltered C1-Inhibitor Concentrate for Acute Treatment and Twice-Weekly Prophylaxis of Hereditary Angioedema, Real 50.8% Attack-Rate Reduction (CHANGE Study, Zuraw 2010 NEJM):",
        "cdd_icatibant": "Complement Deficiency Disorders -- Icatibant (Bradykinin B2-Receptor Antagonist) for Acute Hereditary Angioedema Attacks, Real 2.0 vs 19.8 Hour Time-to-Relief (FAST-3, Lumry 2011 Ann Allergy Asthma Immunol):",
        "cdd_lanadelumab": "Complement Deficiency Disorders -- Lanadelumab (Anti-Plasma-Kallikrein Monoclonal Antibody) for Hereditary Angioedema Prophylaxis, Real 86.8% Attack-Rate Reduction (HELP Trial, Banerji 2018 JAMA):",
        "cdd_berotralstat": "Complement Deficiency Disorders -- Berotralstat (Oral Plasma Kallikrein Inhibitor) for Hereditary Angioedema Prophylaxis, Real 44.3% Attack-Rate Reduction at 150 mg/day (APeX-2, Zuraw 2021 JACI):",
        "em_supportive_symptomatic_care_acute": "Erythema Multiforme -- Supportive Symptomatic Care for the Acute, Self-Limited Episode, Real First-Line Approach Genuinely Curative of the Episode in the Majority of Cases (Hafsi/Badri 2024 StatPearls):",
        "em_continuous_antiviral_prophylaxis_recurrent_hsv": "Erythema Multiforme -- Continuous Oral Acyclovir/Valacyclovir Prophylaxis for Recurrent HSV-Associated Disease, Real Double-Blind Placebo-Controlled RCT, 63.6% Complete Attack Freedom (Tatnall 1995 Br J Dermatol):",
        "em_azathioprine_refractory_recurrent": "Erythema Multiforme -- Azathioprine for Acyclovir-Refractory Recurrent Disease, Real Case-Series Evidence, 100% Complete Suppression in the Most Resistant Subgroup (Schofield 1993 Br J Dermatol):",
        "em_topical_corticosteroids_symptom_relief": "Erythema Multiforme -- Topical Corticosteroids for Cutaneous Symptom Relief, Real Guideline/Expert-Consensus Supportive Measure (Sokumbi/Wetter 2012 Int J Dermatol):",
        "em_oral_antihistamines_pruritus": "Erythema Multiforme -- Oral Antihistamines for Pruritus Control, Real Guideline/Expert-Consensus Supportive Measure (Sokumbi/Wetter 2012 Int J Dermatol):",
        "em_mucosal_involvement_management_major": "Erythema Multiforme Major -- Management of Mucosal Involvement, Real Severity-Tailored Supportive Care Including Hospitalisation Where Indicated (Sokumbi/Wetter 2012 Int J Dermatol; Schofield 1993 Br J Dermatol):",
        "ak_cryotherapy_lesion_directed": "Actinic Keratosis -- Lesion-Directed Cryotherapy (Liquid Nitrogen), Real First-Line Option for Isolated Lesions, 68% Initial / 28% 12-Month Sustained Clearance (Krawtchenko 2007 Br J Dermatol RCT):",
        "ak_topical_5fu_field_therapy": "Actinic Keratosis -- Topical 5-Fluorouracil (5-FU) Field Therapy, Real High-Clearance Option for Multiple/Diffuse Lesions, 96% Initial / 33% 12-Month Sustained Field Clearance (Krawtchenko 2007 Br J Dermatol RCT):",
        "ak_topical_imiquimod_field_therapy": "Actinic Keratosis -- Topical Imiquimod 5% Field Therapy, Real Best Sustained-Clearance Field Option, 85% Initial / 73% 12-Month Sustained Field Clearance (Krawtchenko 2007 Br J Dermatol RCT):",
        "ak_photodynamic_therapy": "Actinic Keratosis -- Photodynamic Therapy (ALA/MAL-PDT), Real Highest Long-Term Complete-Clearance Risk Ratio vs Placebo (RR 8.06 ALA-PDT; Steeb 2021 JAMA Dermatol Network Meta-Analysis):",
        "ak_topical_diclofenac_gel": "Actinic Keratosis -- Topical Diclofenac 3% Gel, Real Milder Alternative for Treatment-Intolerant Patients, Only 9.3% Complete Clearance (Fariba 2006 Indian J Dermatol Venereol Leprol RCT):",
        "ak_sun_protection_prevention": "Actinic Keratosis -- Sun Protection (Broad-Spectrum SPF Sunscreen, Photoprotective Clothing), Real Essential Adjunct Reducing New-Lesion Formation and Skin-Cancer Risk (AAD Guidelines of Care, Eisen 2021 JAAD):",
        "lisc_ultrapotent_topical_corticosteroids": "Lichen Sclerosus -- Ultra-High-Potency Topical Corticosteroids (Clobetasol Propionate 0.05%), Real Guideline First-Line Therapy, 93.3% Symptom Suppression and 0% Malignant Transformation in Compliant Patients (Lee 2015 JAMA Dermatol; Renaud-Vilmer 2004 Arch Dermatol):",
        "lisc_topical_calcineurin_inhibitors": "Lichen Sclerosus -- Topical Calcineurin Inhibitors (Tacrolimus, Pimecrolimus), Real Steroid-Sparing Alternative, Head-to-Head RCT vs Clobetasol (Goldstein 2011 J Am Acad Dermatol):",
        "lisc_circumcision_male_genital_disease": "Lichen Sclerosus -- Circumcision for Male Genital Disease (Balanitis Xerotica Obliterans) Confined to the Foreskin, Real 99.1% Complete Resolution of Glanular Lesions (Kiss 2005 Pediatr Dermatol):",
        "lisc_surgical_management_scarring_complications": "Lichen Sclerosus -- Perineoplasty for Scarring Complications (Introital Stenosis), Real 90% Dyspareunia Improvement (Rouzier 2002 Am J Obstet Gynecol):",
        "lisc_malignant_transformation_surveillance": "Lichen Sclerosus -- Lifelong Malignant-Transformation Surveillance, Real Quantified and Adherence-Modifiable Oncologic Risk (Lee 2015 JAMA Dermatol; Renaud-Vilmer 2004 Arch Dermatol):",
        "ks_intralesional_corticosteroid_triamcinolone": "Keloid Scarring -- Intralesional Triamcinolone Acetonide Injection, Real First-Line Non-Surgical Therapy for Smaller Keloids, 60% Remission at 6 Months (Hietanen 2019 RCT):",
        "ks_intralesional_5_fluorouracil": "Keloid Scarring -- Intralesional 5-Fluorouracil Injection, Real Comparably-Effective Alternative With Fewer Steroid-Type Side Effects, 46% Remission at 6 Months (Hietanen 2019 RCT):",
        "ks_surgical_excision_adjuvant_radiotherapy": "Keloid Scarring -- Surgical Excision + Immediate Adjuvant Radiotherapy, Real Best-Evidence Combination, 78-93% Recurrence-Free (Miles 2021 ANZ J Surg; Peng 2025 Aesthetic Plast Surg; Wojarska 2026 Life):",
        "ks_laser_therapy_pulsed_dye_laser": "Keloid Scarring -- 585-nm Pulsed Dye Laser Therapy, Real But Low-Certainty Cochrane Evidence (Leszczynski 2022 Cochrane Review):",
        "ks_silicone_gel_sheeting_adjunct_prevention": "Keloid Scarring -- Silicone Gel Sheeting, Real Preventive Adjunct for High-Risk Wounds, Methodologically Weak Evidence Base (O'Brien 2013 Cochrane Review):",
        "vv_topical_salicylic_acid": "Verruca Vulgaris (Warts) -- Topical Salicylic Acid, Real First-Line OTC Keratolytic (Kwok 2012 Cochrane Review; Bruggink 2010 CMAJ RCT):",
        "vv_cryotherapy": "Verruca Vulgaris (Warts) -- Cryotherapy With Liquid Nitrogen, Real Clinic-Administered First-Line Procedure, 49% Cure for Common Warts at 13 Weeks (Bruggink 2010 CMAJ RCT):",
        "vv_combination_salicylic_acid_cryotherapy": "Verruca Vulgaris (Warts) -- Salicylic Acid Plus Cryotherapy Combined, Real Best-Evidence Combination Regimen (Kwok 2012 Cochrane Review):",
        "vv_immunotherapy_candida_mumps_antigen_refractory": "Verruca Vulgaris (Warts) -- Intralesional Mumps or Candida Antigen Immunotherapy for Refractory/Recalcitrant Warts, Real 74% Adult / 47% Paediatric Clearing (Johnson 2001 Arch Dermatol; Clifton 2003 Pediatr Dermatol):",
        "vv_watchful_waiting_spontaneous_resolution": "Verruca Vulgaris (Warts) -- Watchful Waiting, Real Well-Documented Spontaneous Resolution in Two-Thirds of Cases Within 2 Years (Massing & Epstein 1963 Arch Dermatol; Bruggink 2010 CMAJ RCT):",
        "oe_topical_antibiotic_ear_drops": "Otitis Externa -- Topical Antibiotic Ear Drops (Fluoroquinolone or Aminoglycoside-Based), Real Guideline First-Line Therapy, 83.9-90.9% Clinical Cure (Roland 2004 Curr Med Res Opin RCT; Rahman 2007 Clin Ther Pooled Analysis):",
        "oe_topical_antibiotic_corticosteroid_combination": "Otitis Externa -- Topical Antibiotic Plus Corticosteroid Combination (Ciprofloxacin/Dexamethasone), Real Highest Head-to-Head-RCT-Proven Cure, 90.9% Clinical Cure / 94.7% Microbiologic Eradication (Roland 2004 Curr Med Res Opin RCT; Rahman 2007 Clin Ther Pooled Analysis):",
        "oe_topical_acetic_acid_antiseptic_mild_disease": "Otitis Externa -- Topical Acetic Acid 2% for Mild Disease, Real Cochrane-Reviewed Narrower-Indication Option (Kaushik 2010 Cochrane Review):",
        "oe_ear_canal_cleaning_wick_placement": "Otitis Externa -- Aural Toilet (Ear Canal Cleaning) and Wick Placement, Real Guideline-Mandated Delivery-Enhancing Step (AAO-HNS Guideline, Rosenfeld 2014 Otolaryngol Head Neck Surg):",
        "oe_iv_antibiotics_malignant_necrotizing_otitis_externa_urgent_ent_referral": "Otitis Externa -- IV Combination Antipseudomonal Antibiotics Plus Urgent ENT Referral for Malignant/Necrotizing Otitis Externa, Real 95% Cure in Case Series, Real Historical Mortality Up to 50% Pre-Antibiotic Era (Martel 2000 Ann Otolaryngol Chir Cervicofac; Krishnamoorthy 2020 Acta Medica):",
        "ton_penicillin_amoxicillin_confirmed_strep_tonsillitis": "Tonsillitis -- Penicillin V or Amoxicillin for Confirmed Group A Streptococcus (Bacterial) Tonsillitis, Real 97.2% Bacteriologic Cure (Clegg 2006 Pediatr Infect Dis J; IDSA 2012 Shulman Guideline):",
        "ton_symptomatic_care_viral_tonsillitis": "Tonsillitis -- Supportive Symptomatic Care for Viral (Non-Bacterial) Tonsillitis, Real 82% One-Week Symptom-Free Natural History (Spinks 2021 Cochrane Review):",
        "ton_tonsillectomy_recurrent_paradise_criteria": "Tonsillitis -- Tonsillectomy for Recurrent/Chronic Disease Meeting Paradise Criteria, Real Definitive Organ-Level Cure With Modest 16.7% Episode-Reduction Trial Data (Paradise 1984 NEJM; Paradise 2002 Pediatrics; Burton 2014 Cochrane Review):",
        "ton_drainage_peritonsillar_abscess": "Tonsillitis -- Incision and Drainage (or Needle Aspiration) for Peritonsillar Abscess, Real 90% vs 53.7% Single-Procedure Success (Mansour 2019 Eur Arch Otorhinolaryngol):",
        "ton_nsaids_analgesics_symptom_relief": "Tonsillitis -- NSAIDs and Analgesics (Ibuprofen, Paracetamol) for Symptomatic Pain/Fever Relief, Real Systematic-Review Evidence, Not Curative (Thomas 2000 Br J Gen Pract):",
        "asin_symptomatic_care_for_the_viral_majority": "Acute Sinusitis -- Symptomatic Care Alone for the Viral Majority, Real 64% Cure by 14 Days and 46% by 7 Days Without Antibiotics (Lemiengre 2018 Cochrane Review; Williamson 2007 JAMA RCT):",
        "asin_first_line_antibiotic_regimens_for_true_bacterial_disease": "Acute Sinusitis -- Amoxicillin-Clavulanate (or Amoxicillin) for IDSA/AAP-Defined True Bacterial Disease, Real Antibiotic Benefit Rising to ~25 More Cured per 100 in CT-Confirmed Disease (Chow 2012 IDSA Guideline; Lemiengre 2018 Cochrane Review):",
        "asin_beta_lactam_allergy_alternatives": "Acute Sinusitis -- Doxycycline or a Respiratory Fluoroquinolone for Beta-Lactam Allergy, Real Guideline-Named Alternative Regimens (Butler/Hernandez 2025 Am Fam Physician Evidence Review):",
        "asin_intranasal_corticosteroids_adjunct": "Acute Sinusitis -- Intranasal Corticosteroids as Monotherapy or Antibiotic Adjunct, Real 73% vs 66.4% Symptom Resolution (Zalmanovici 2009 Cochrane Review):",
        "chl_cerumen_impaction_removal": "Conductive Hearing Loss -- Cerumen (Earwax) Impaction Removal (Cerumenolytics, Irrigation, Manual/Microsuction Removal), Real AAO-HNS Guideline Pathway, 75% First-Attempt Success (Schwartz 2017 AAO-HNS Guideline; Jones 2025 Trials NHS Protocol):",
        "chl_myringoplasty_tympanoplasty_tm_perforation": "Conductive Hearing Loss -- Myringoplasty/Tympanoplasty for Tympanic Membrane Perforation, Real 1070-Patient UK Prospective Multi-Surgeon Audit, 82.2% Graft Take Rate (Kotecha 1999 Clin Otolaryngol Allied Sci):",
        "chl_stapedectomy_stapedotomy_otosclerosis": "Conductive Hearing Loss -- Stapedectomy/Stapedotomy for Otosclerosis, Real 151-Case CO2-Laser Single-Surgeon Series, 95.6% Air-Bone-Gap Closure (Saerens 2021 Otol Neurotol):",
        "chl_ossiculoplasty_ossicular_chain_disruption": "Conductive Hearing Loss -- Ossiculoplasty (PORP/TORP) for Ossicular Chain Disruption, Real 292-Case Multicenter Endoscopic Series, 94.2% Prosthesis Success (Fink 2025 Eur Arch Otorhinolaryngol):",
        "chl_ventilation_tubes_ome": "Conductive Hearing Loss -- Ventilation Tubes (Grommets) for Otitis Media With Effusion, Real Cochrane Systematic Review, Honestly Modest/Uncertain Evidence (MacKeith 2023 Cochrane Review):",
        "chl_hearing_aids_bone_conduction_devices": "Conductive Hearing Loss -- Hearing Aids/Bone-Conduction Implants (Osia, Bonebridge, BAHA) for Non-Surgically-Correctable Disease, Real Prospective Outcome Data (Young 2023 Am J Otolaryngol; Boaventura 2026 Laryngoscope Investig Otolaryngol):",
        "snhl_oral_high_dose_corticosteroid": "Sensorineural Hearing Loss -- Oral High-Dose Corticosteroid (Prednisone) for Sudden SNHL, Real Guideline-Endorsed Initial Therapy Within 2 Weeks of Onset (Rauch 2011 JAMA RCT; AAO-HNS Chandrasekhar 2019 Guideline):",
        "snhl_intratympanic_corticosteroid_injection": "Sensorineural Hearing Loss -- Intratympanic Corticosteroid Injection, Real RCT-Proven Noninferior Primary Therapy and Guideline-Recommended Salvage Therapy (Rauch 2011 JAMA RCT; AAO-HNS Chandrasekhar 2019 Guideline):",
        "snhl_hearing_aids_chronic_age_related": "Sensorineural Hearing Loss -- Hearing Aids for Chronic/Age-Related (Presbycusis) SNHL, Real First-Line Non-Invasive Therapy, Cochrane-Proven Quality-of-Life Benefit (Ferguson 2017 Cochrane Review):",
        "snhl_cochlear_implantation_severe_profound": "Sensorineural Hearing Loss -- Cochlear Implantation for Severe-to-Profound SNHL, Real Dramatic Functional-Restoration Option (Boisvert 2020 PLoS One Scoping Review):",
        "snhl_hyperbaric_oxygen_therapy_adjunct": "Sensorineural Hearing Loss -- Hyperbaric Oxygen Therapy as Adjunct to Corticosteroid for Acute Sudden SNHL, Real But Modest Guideline-Listed Option (Bennett 2012 Cochrane Review):",
        "md_low_sodium_diet": "Meniere's Disease -- Low-Sodium Diet, Real First-Line Noninvasive Vertigo-Control Measure, 75% Vertigo Well Controlled in Real Cohort (Sbeih 2018 Ann Otol Rhinol Laryngol):",
        "md_diuretic_therapy_hydrochlorothiazide_triamterene": "Meniere's Disease -- Oral Diuretic Therapy (Hydrochlorothiazide/Triamterene), Real Adjunct With 79% of Studies Reporting Vertigo Improvement Despite Low-Certainty Evidence (Crowson 2016 Otolaryngol Head Neck Surg; Thirlwall 2006 Cochrane Review):",
        "md_betahistine": "Meniere's Disease -- Betahistine, Real Widely-Used Oral Vestibular Medication, Honest Negative Primary-Endpoint Result vs Placebo (Adrion 2016 BEMED Trial, BMJ):",
        "md_intratympanic_corticosteroid_injection": "Meniere's Disease -- Intratympanic Corticosteroid (Dexamethasone) Injection, Real Low/Very-Low Certainty Evidence Not Clearly Superior to Placebo (Webster 2023 Cochrane Review):",
        "md_intratympanic_gentamicin_refractory": "Meniere's Disease -- Intratympanic Gentamicin (Chemical Labyrinthectomy) for Refractory Disease, Real Highest Pooled Vertigo Control Rate of 89% With Honest Hearing-Loss Risk (Chun 2026 Laryngoscope Umbrella Review):",
        "md_endolymphatic_sac_surgery_labyrinthectomy_severe_refractory": "Meniere's Disease -- Endolymphatic Sac Surgery / Labyrinthectomy for Severe Refractory Disease, Real 75-82% Initial Vertigo Control (Endolymphatic Sac) and Effective Vertigo Control for Nonserviceable-Hearing Ears (Labyrinthectomy) (Chun 2026 Laryngoscope; Paouris 2026 Otol Neurotol):",
        "tin_cause_directed_treatment_cerumen_removal": "Tinnitus -- Cerumen Impaction Identification and Removal, Real Guideline-Endorsed Genuinely Curative Pathway for Impaction-Caused Tinnitus (AAO-HNS Cerumen Impaction Guideline, Schwartz 2017; Michaudet & Malaty, Am Fam Physician 2018):",
        "tin_cause_directed_treatment_ototoxic_medication_review": "Tinnitus -- Ototoxic Medication Review and Adjustment for Drug-Induced Tinnitus, Real AAO-HNS Guideline-Recommended Etiologic Evaluation (Tunkel 2014 Otolaryngol Head Neck Surg):",
        "tin_cognitive_behavioral_therapy": "Tinnitus -- Cognitive Behavioral Therapy (CBT), Real Cochrane-Review-Verified Best-Evidence Distress/Handicap Reduction for Chronic Idiopathic Tinnitus (Fuller 2020 Cochrane Review; Tunkel 2014 AAO-HNS Guideline):",
        "tin_sound_therapy_masking_devices": "Tinnitus -- Sound Therapy / Tinnitus Masking Devices, Real Multisite VA Randomized Trial Data, 55% Clinically Significant Improvement at 18 Months (Henry 2016 Ear Hear RCT):",
        "tin_hearing_aids_comorbid_hearing_loss": "Tinnitus -- Hearing Aid Evaluation and Fitting for Comorbid Hearing Loss, Real AAO-HNS Guideline Recommendation (Tunkel 2014 Otolaryngol Head Neck Surg):",
        "tin_tinnitus_retraining_therapy": "Tinnitus -- Tinnitus Retraining Therapy (TRT), Real Multisite VA Randomized Trial Data, 59% Clinically Significant Improvement at 18 Months (Henry 2016 Ear Hear RCT):",
        "tin_guideline_recommended_against_ineffective_treatments": "Tinnitus -- Real AAO-HNS Guideline Recommendations AGAINST Antidepressants, Anticonvulsants, Anxiolytics, Intratympanic Medications, Ginkgo Biloba/Melatonin/Zinc Supplements, and Transcranial Magnetic Stimulation for Routine Treatment (Tunkel 2014 Otolaryngol Head Neck Surg):",
        "dns_septoplasty": "Deviated Nasal Septum -- Septoplasty, Real Definitive Anatomical Cure, NAIROS Phase III RCT, 50.6% Lower/Better SNOT-22 Score Than Medical Management at 6 Months (Carrie 2024 Health Technology Assessment):",
        "dns_septorhinoplasty_combined_deformity": "Deviated Nasal Septum -- Septorhinoplasty for Combined Septal and External Nasal Deformity, Real 150-Patient Prospective Cohort, 68.0% NOSE Score Reduction at 6 Months (Topuria 2026 Am J Otolaryngol):",
        "dns_nasal_dilator_strips_conservative_adjunct": "Deviated Nasal Septum -- External Nasal Dilator Strips, Real Small-Pilot-Verified Non-Invasive Bridge Therapy, Not a Cure (Pezzoli 2026 Cureus Pilot Study):",
        "dns_intranasal_corticosteroids_symptom_management": "Deviated Nasal Septum -- Intranasal Corticosteroid Plus Saline Spray, Real Guideline-Consistent First-Line Medical Management for Mild/Non-Surgical Disease (NAIROS Comparator Arm, Carrie 2024):",
        "npc_imrt_alone_early_stage": "Nasopharyngeal Carcinoma -- Intensity-Modulated Radiotherapy (IMRT) Alone, Real Primary Curative Option for Early-Stage (T1-T2bN0-N1M0) Disease, 97.3% Real 5-Year Disease-Specific Survival (Su 2012 Int J Radiat Oncol Biol Phys):",
        "npc_concurrent_chemoradiation_locoregionally_advanced": "Nasopharyngeal Carcinoma -- Concurrent Cisplatin Chemoradiotherapy, Real Landmark Intergroup 0099-Proven Standard for Locoregionally Advanced Disease, 78% Real 3-Year Overall Survival (Al-Sarraf 1998 JCO):",
        "npc_induction_chemo_before_crt_advanced": "Nasopharyngeal Carcinoma -- Gemcitabine-Cisplatin Induction Chemotherapy Before Concurrent Chemoradiotherapy, Real Phase 3-Proven Further Survival Gain for Locoregionally Advanced Disease, 94.6% Real 3-Year Overall Survival (Zhang 2019 NEJM):",
        "npc_immunotherapy_recurrent_metastatic": "Nasopharyngeal Carcinoma -- Toripalimab Plus Gemcitabine-Cisplatin (Anti-PD-1 Immunotherapy), Real Non-Curative Survival Benefit for First-Line Recurrent/Metastatic Disease, JUPITER-02 Trial (Mai 2023 JAMA):",
        "npc_ebv_dna_surveillance": "Nasopharyngeal Carcinoma -- Plasma Epstein-Barr Virus (EBV) DNA Monitoring for Post-Treatment Surveillance/Prognostication, Real Validated Biomarker but Honest Negative Trial for EBV-DNA-Triggered Adjuvant Chemotherapy Escalation (Chan 2018 JCO):",
        "dr_intensive_glycemic_control": "Diabetic Retinopathy -- Intensive Glycaemic Control, Real Primary Prevention (DCCT 1993 NEJM; UKPDS 33 1998 Lancet):",
        "dr_anti_vegf_intravitreal_injections": "Diabetic Retinopathy -- Anti-VEGF Intravitreal Injections for Diabetic Macular Edema, Real First-Line Treatment (Ranibizumab: DRCR.net Protocol I, Elman 2010 Ophthalmology; Aflibercept: VISTA/VIVID, Korobelnik 2014 Ophthalmology):",
        "dr_panretinal_photocoagulation": "Diabetic Retinopathy -- Panretinal Photocoagulation for High-Risk Proliferative Disease, Real Standard of Care (DRS Report 8, 1981 Ophthalmology; ETDRS Report 9, 1991 Ophthalmology):",
        "dr_intravitreal_corticosteroid_implants": "Diabetic Retinopathy -- Intravitreal Corticosteroid Implants for Refractory/Chronic Diabetic Macular Edema (Fluocinolone Acetonide: FAME Study, Campochiaro 2012 Ophthalmology; Dexamethasone: MEAD Study, Boyer 2014 Ophthalmology):",
        "dr_vitrectomy": "Diabetic Retinopathy -- Pars Plana Vitrectomy for Non-Clearing Vitreous Haemorrhage/Tractional Retinal Detachment (DRVS Report 2, 1985 Arch Ophthalmol):",
        "vcn_voice_therapy": "Vocal Cord Nodules -- Structured Behavioral Voice Therapy, Real First-Line Treatment, 70%+ Nodule Elimination/Reduction and 80%+ Normal/Mild-Dysphonia Outcome (McCrory 2001; Karali 2025):",
        "vcn_voice_rest_vocal_hygiene": "Vocal Cord Nodules -- Voice Rest and Vocal Hygiene, Real Adjunct/Foundational Non-Pharmacologic Measures (Syed 2009 Clin Otolaryngol; Naunheim/Carroll 2017):",
        "vcn_microlaryngoscopic_excision_refractory": "Vocal Cord Nodules -- Microlaryngoscopic Surgical Excision for Refractory/Mature Nodules, Real High-Cure-Rate Second-Line Option, 90% Pooled Post-Operative Improvement, 100% Complete Glottal Closure in Adult Series (Wu 2023 Meta-Analysis; Caffier 2017):",
        "vcn_addressing_vocal_misuse_gerd_adjunct": "Vocal Cord Nodules -- Addressing Underlying Vocal Misuse and Comorbid Laryngopharyngeal Reflux/GERD, Real Adjunct Management (Syed 2009 Clin Otolaryngol; Stachler 2018 AAO-HNS Guideline):",
    }
    for key, label in MED_GROUP_LABELS.items():
        meds = ems.get(key)
        if not meds:
            continue
        if label:
            elements.append(Paragraph(label, subhead))
        med_list = meds if isinstance(meds, list) else [meds]
        for m in med_list:
            if not isinstance(m, dict):
                # Defensive: a small number of exhaustive_medicine_survey entries were
                # written as plain strings rather than the expected dict shape -- render
                # the text honestly instead of crashing (mirrors the curative_option
                # isinstance(co, str) defensive handling above), so no data is lost.
                elements.append(Paragraph(f"<i>{m}</i>", small_grey))
                continue
            render_medicine(m)
    if ems.get("no_new_drug_class_note"):
        elements.append(Paragraph(f"<i>{ems['no_new_drug_class_note']}</i>", small_grey))
    if ems.get("not_yet_researched_note"):
        elements.append(Paragraph(f"<i>{ems['not_yet_researched_note']}</i>", small_grey))
    if ems.get("injectable_therapy_note"):
        elements.append(Paragraph(f"<i>{ems['injectable_therapy_note']}</i>", small_grey))
    if ems.get("hiv_india_naco_context_note"):
        elements.append(Paragraph(f"<i>{ems['hiv_india_naco_context_note']}</i>", small_grey))
    aposc = ems.get("ap_severe_pancreatitis_organ_support_cross_reference")
    if isinstance(aposc, dict):
        elements.append(Paragraph("Severe Pancreatitis — ICU-Level Organ Support (Cross-Referenced, Not Re-Derived):", subhead))
        if aposc.get("note"):
            elements.append(Paragraph(aposc["note"], body))
        if aposc.get("source"):
            elements.append(Paragraph(f"Source: {cite(aposc['source'])}", cite_marker_s))
        elements.append(Spacer(1, 6))

    elements.append(PageBreak())

    # ============ SECTION 2: ALL DETAILED SYMPTOMS ============
    elements.append(Paragraph(f"&nbsp;Disease {disease_num}: {disease['name']}", disease_h))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("2. All Detailed Symptoms", section_h))

    sym = disease.get("symptoms", {})

    if sym.get("core_note"):
        elements.append(Paragraph(sym["core_note"], body))
        elements.append(Spacer(1, 6))

    # ---- Stroke-specific structured blocks ----
    # (TIME_TO_CALL_EMERGENCY_SERVICES, stroke_classification, localizing_vascular_territory_signs
    # are new key shapes not covered by any generic handler -- would otherwise be silently dropped.
    # complications is a LIST here (every other disease uses a dict), and risk_scoring_tools entries
    # (NIHSS, CHA2DS2-VASc) omit "criteria"/"confidence" -- both handled defensively further below.)
    if disease_id == "stroke":
        if sym.get("TIME_TO_CALL_EMERGENCY_SERVICES"):
            elements.append(Paragraph("FAST/BE-FAST -- 'T' = Time to call emergency services:", subhead))
            elements.append(Paragraph(sym["TIME_TO_CALL_EMERGENCY_SERVICES"], body))
            elements.append(Spacer(1, 4))

        scl = sym.get("stroke_classification")
        if scl:
            elements.append(Paragraph("Real stroke classification -- Ischaemic (TOAST) vs Haemorrhagic vs TIA:", subhead))
            if scl.get("overview"):
                elements.append(Paragraph(scl["overview"], body))
            for subtype in scl.get("ischaemic_stroke_subtypes_TOAST", []):
                elements.append(Paragraph(f"• <b>{subtype.get('subtype','')}:</b> {subtype.get('mechanism','')}", bullet))
                if subtype.get("note"):
                    elements.append(Paragraph(subtype["note"], small_grey))
            for subtype in scl.get("haemorrhagic_stroke_subtypes", []):
                elements.append(Paragraph(f"• <b>{subtype.get('subtype','')}:</b> {subtype.get('mechanism','')}", bullet))
                if subtype.get("note"):
                    elements.append(Paragraph(subtype["note"], small_grey))
            tia = scl.get("TIA_transient_ischaemic_attack")
            if tia:
                elements.append(Paragraph("TIA (Transient Ischaemic Attack) -- definition:", subhead))
                for tk in ("definition_evolution", "why_it_changed", "clinical_significance"):
                    if tia.get(tk):
                        elements.append(Paragraph(f"• <b>{tk.replace('_',' ').title()}:</b> {tia[tk]}", bullet))
                if tia.get("source"):
                    elements.append(Paragraph(f"Source: {cite(tia['source'])}", cite_marker_s))
            if scl.get("source"):
                elements.append(Paragraph(f"Confidence: {scl.get('confidence','')} | Source: {cite(scl['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        lvts = sym.get("localizing_vascular_territory_signs")
        if lvts:
            elements.append(Paragraph("Real vascular-territory localisation (predicts stroke type/territory from deficit pattern):", subhead))
            if lvts.get("note"):
                elements.append(Paragraph(lvts["note"], body))
            for terr in lvts.get("territories", []):
                elements.append(Paragraph(f"• <b>{terr.get('territory','')}:</b> {terr.get('findings','')}", bullet))
            if lvts.get("source"):
                elements.append(Paragraph(f"Source: {cite(lvts['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Viral Hepatitis-specific structured blocks ----
    # (virology_and_classification, chronic_hepatitis_b/c_natural_history, diagnostic_framework,
    # classic_symptoms, acute_liver_failure would otherwise be silently dropped or mislabeled
    # under an unrelated disease's generic heading -- see the disease_id=="viral_hepatitis" guards
    # added below at the classic_symptoms generic loop and the diagnostic_framework if/elif chain.)
    if disease_id == "viral_hepatitis":
        voc = sym.get("virology_and_classification")
        if voc:
            elements.append(Paragraph("Real virology and classification -- Hepatitis A / B / C / D / E:", subhead))
            for k, v in voc.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        dfw_vh = sym.get("diagnostic_framework")
        if dfw_vh:
            elements.append(Paragraph("Real diagnostic framework -- HBV serology interpretation, HCV testing algorithm, LFTs, fibrosis staging:", subhead))
            for k, v in dfw_vh.items():
                if k == "source":
                    continue
                render_generic_kv(k, v)
            if dfw_vh.get("source"):
                elements.append(Paragraph(f"Source: {cite(dfw_vh['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        chb = sym.get("chronic_hepatitis_b_natural_history")
        if chb:
            elements.append(Paragraph("Real Chronic Hepatitis B -- natural history (phases, seroconversion, progression):", subhead))
            for k, v in chb.items():
                if k in ("source", "source_2") or not isinstance(v, str):
                    continue
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
            srcs = "; ".join(s for s in (chb.get("source"), chb.get("source_2")) if s)
            if srcs:
                elements.append(Paragraph(f"Source: {cite(srcs)}", cite_marker_s))
            elements.append(Spacer(1, 4))

        chc = sym.get("chronic_hepatitis_c_natural_history")
        if chc:
            elements.append(Paragraph("Real Chronic Hepatitis C -- natural history and extrahepatic manifestations:", subhead))
            for k, v in chc.items():
                if k == "source" or not isinstance(v, str):
                    continue
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
            if chc.get("source"):
                elements.append(Paragraph(f"Source: {cite(chc['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        csx = sym.get("classic_symptoms")
        if isinstance(csx, dict):
            elements.append(Paragraph("Real classic symptoms -- chronic (often asymptomatic) vs acute hepatitis presentation:", subhead))
            for k, v in csx.items():
                if k == "source":
                    continue
                render_generic_kv(k, v)
            if csx.get("source"):
                elements.append(Paragraph(f"Source: {cite(csx['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        alf = sym.get("acute_liver_failure")
        if alf:
            elements.append(Paragraph("Real Acute Liver Failure (fulminant hepatitis) -- definition, mortality, causes:", subhead))
            for k, v in alf.items():
                if k == "source" or not isinstance(v, str):
                    continue
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
            if alf.get("source"):
                elements.append(Paragraph(f"Source: {cite(alf['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Cirrhosis-specific structured blocks ----
    # This entry's "symptoms" sub-object holds only etiology content (viral/alcohol/MASLD/
    # autoimmune/genetic/cardiac causes). The Child-Pugh/MELD-Na, pathophysiology, classic
    # complications/signs, risk factors, epidemiology, natural-history and red-flags content
    # for this disease was written at the TOP LEVEL of the disease dict (siblings of "symptoms"),
    # not nested inside it -- rendered here directly from `disease` (not `sym`) so it is not
    # silently dropped, exactly the kind of bug this file has hit before with other diseases.
    if disease_id == "cirrhosis":
        elements.append(Paragraph("Real etiology of cirrhosis -- chronic viral hepatitis, alcohol, MASLD, autoimmune, genetic and cardiac causes:", subhead))
        for k, v in sym.items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

        cls = disease.get("classification")
        if isinstance(cls, dict):
            elements.append(Paragraph("Real classification -- Compensated vs Decompensated Cirrhosis:", subhead))
            for k, v in cls.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        patho = disease.get("pathophysiology")
        if isinstance(patho, dict):
            elements.append(Paragraph("Real pathophysiology -- fibrosis mechanism and portal hypertension:", subhead))
            for k, v in patho.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        pss = disease.get("prognostic_scoring_systems")
        if isinstance(pss, dict):
            elements.append(Paragraph("Real prognostic scoring systems -- Child-Pugh & MELD-Na:", subhead))
            for k, v in pss.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        ccx = disease.get("classic_complications")
        if isinstance(ccx, dict):
            elements.append(Paragraph("Real classic complications -- ascites, variceal hemorrhage, hepatic encephalopathy, SBP, hepatorenal syndrome:", subhead))
            for k, v in ccx.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        ccs = disease.get("classic_clinical_signs")
        if isinstance(ccs, dict):
            elements.append(Paragraph("Real classic clinical signs:", subhead))
            for k, v in ccs.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        rrf = disease.get("real_risk_factors")
        if isinstance(rrf, dict):
            elements.append(Paragraph("Real risk factors:", subhead))
            for k, v in rrf.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        epi_c = disease.get("epidemiology")
        if isinstance(epi_c, dict):
            elements.append(Paragraph("Real epidemiology:", subhead))
            for k, v in epi_c.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        nhp = disease.get("natural_history_and_prognosis")
        if isinstance(nhp, dict):
            elements.append(Paragraph("Real natural history and prognosis:", subhead))
            for k, v in nhp.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        rfl = disease.get("red_flags")
        if isinstance(rfl, list):
            elements.append(Paragraph("Real red flags -- emergency features:", subhead))
            for item in rfl:
                if isinstance(item, str):
                    elements.append(Paragraph(f"• {item}", bullet))
            if disease.get("red_flags_source"):
                elements.append(Paragraph(f"Source: {cite(disease['red_flags_source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Epilepsy-specific structured blocks ----
    # (definition_ILAE_2014, classification_ILAE_2017_seizure_types, classification_epilepsy_syndromes,
    # etiology (dict-of-topic-dicts), diagnostic_framework (dict-of-topic-dicts) match no existing
    # handler at all and would be silently dropped; epidemiology has THREE keys (global,
    # india_specific, india_treatment_gap) but the generic "global"+"india_specific" epi8 handler
    # further below only iterates the first two, silently dropping india_treatment_gap -- so
    # epidemiology is fully rendered here instead and epi8 is explicitly skipped for this disease_id.
    # core, real_risk_factors, natural_history, and red_flags all match existing generic shapes
    # (CORE_LABELS list-of-{name,note,source}; real_risk_factors list-of-{factor,note,source};
    # natural_history dict-of-{finding,source,confidence}; red_flags list-of-strings) and are left
    # to those generic handlers.)
    if disease_id == "epilepsy":
        dfe = sym.get("definition_ILAE_2014")
        if isinstance(dfe, dict):
            elements.append(Paragraph("Real ILAE 2014 practical clinical definition of epilepsy:", subhead))
            for k in ("criteria", "recurrence_risk_basis", "resolution", "critical_distinction"):
                if dfe.get(k):
                    elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {dfe[k]}", bullet))
            if dfe.get("source"):
                elements.append(Paragraph(f"Confidence: {dfe.get('confidence', '')} | Source: {cite(dfe['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        cst = sym.get("classification_ILAE_2017_seizure_types")
        if isinstance(cst, dict):
            elements.append(Paragraph("Real ILAE 2017 operational classification of seizure types:", subhead))
            if cst.get("framework"):
                elements.append(Paragraph(cst["framework"], body))
            for cat in cst.get("three_top_level_categories", []):
                elements.append(Paragraph(f"• <b>{cat.get('category', '')}:</b> {cat.get('description', '')}", bullet))
            for k in ("focal_to_bilateral_tonic_clonic", "terminology_retired"):
                if cst.get(k):
                    elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {cst[k]}", bullet))
            if cst.get("source"):
                elements.append(Paragraph(f"Confidence: {cst.get('confidence', '')} | Source: {cite(cst['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        ces = sym.get("classification_epilepsy_syndromes")
        if isinstance(ces, dict):
            elements.append(Paragraph("Real epilepsy syndrome classification -- named syndromes:", subhead))
            if ces.get("framework_note"):
                elements.append(Paragraph(ces["framework_note"], body))
            for syn in ces.get("named_syndromes", []):
                elements.append(Paragraph(f"• <b>{syn.get('syndrome', '')}:</b> {syn.get('features', '')}", bullet))
                if syn.get("source"):
                    elements.append(Paragraph(f"Source: {cite(syn['source'])}", cite_marker_s))
            if ces.get("source"):
                elements.append(Paragraph(f"Confidence: {ces.get('confidence', '')} | Source: {cite(ces['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        etio = sym.get("etiology")
        if isinstance(etio, dict):
            elements.append(Paragraph("Real etiology -- ILAE six etiologic categories:", subhead))
            if etio.get("framework"):
                elements.append(Paragraph(etio["framework"], body))
            for k, v in etio.items():
                if k in ("framework", "cross_reference") or not isinstance(v, dict):
                    continue
                elements.append(Paragraph(k.replace("_", " ").title() + ":", body))
                if v.get("note"):
                    elements.append(Paragraph(f"• {v['note']}", bullet))
                if v.get("source"):
                    elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v['source'])}", cite_marker_s))
            if etio.get("cross_reference"):
                elements.append(Paragraph(f"<i>{etio['cross_reference']}</i>", small_grey))
            elements.append(Spacer(1, 4))

        dxf = sym.get("diagnostic_framework")
        if isinstance(dxf, dict):
            elements.append(Paragraph("Real diagnostic framework -- EEG, video-EEG/PNES, MRI:", subhead))
            for k, v in dxf.items():
                if not isinstance(v, dict):
                    continue
                elements.append(Paragraph(k.replace("_", " ").upper() + ":", body))
                for tk in ("role_and_limitation", "role", "why_it_matters"):
                    if v.get(tk):
                        elements.append(Paragraph(f"• {v[tk]}", bullet))
                if v.get("source"):
                    elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        ses = sym.get("status_epilepticus")
        if isinstance(ses, dict):
            elements.append(Paragraph("Real status epilepticus -- ILAE 2015 operational definition & mortality:", subhead))
            for k in ("operational_definition", "mortality"):
                if ses.get(k):
                    elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {ses[k]}", bullet))
            if ses.get("source"):
                elements.append(Paragraph(f"Confidence: {ses.get('confidence', '')} | Source: {cite(ses['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        epi_ep = sym.get("epidemiology")
        if isinstance(epi_ep, dict):
            elements.append(Paragraph("Real epidemiology -- Global, India-specific & India Treatment Gap:", subhead))
            for k in ("global", "india_specific", "india_treatment_gap"):
                ev = epi_ep.get(k)
                if not isinstance(ev, dict):
                    continue
                elements.append(Paragraph(k.replace("_", " ").title() + ":", body))
                if ev.get("finding"):
                    elements.append(Paragraph(f"• {ev['finding']}", bullet))
                if ev.get("source"):
                    elements.append(Paragraph(f"Confidence: {ev.get('confidence', '')} | Source: {cite(ev['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Peptic Ulcer Disease-specific structured blocks ----
    # This entry's clinical content is correctly nested entirely inside "symptoms" (unlike the
    # earlier cirrhosis bug), but it introduces several new key names (definition_and_pathophysiology,
    # etiology as a dict-of-topic-dicts, classification_gastric_vs_duodenal, classic_symptoms,
    # diagnostic_framework, epidemiology with a "global_burden"/"india_specific_data" shape) that would
    # otherwise be silently dropped (etiology, classification_gastric_vs_duodenal, definition_and_
    # pathophysiology match no existing handler at all) or mislabeled/partially dropped (classic_symptoms
    # would fall into the generic tuple-loop's "circadian pattern" GINA-asthma heading; diagnostic_framework
    # would fall into the generic "Lake Louise Criteria & Dallas Histopathological Criteria" myocarditis
    # catch-all; epidemiology's "global_burden" key would trigger a generic branch that renders global_burden
    # but silently drops india_specific_data and the source citation, since that branch expects
    # "india_burden"/"source_global"/"source_india" key names PUD does not use). Rendered explicitly here
    # instead, exactly the kind of fix this file's own header comments call for.
    if disease_id == "peptic_ulcer_disease":
        dap = sym.get("definition_and_pathophysiology")
        if isinstance(dap, dict):
            elements.append(Paragraph("Real definition and pathophysiology:", subhead))
            if dap.get("definition"):
                elements.append(Paragraph(f"<b>Definition:</b> {dap['definition']}", body))
            if dap.get("core_pathophysiologic_framework"):
                elements.append(Paragraph(f"<b>Core pathophysiologic framework:</b> {dap['core_pathophysiologic_framework']}", body))
            if dap.get("source"):
                elements.append(Paragraph(f"Source: {cite(dap['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        eti_pud = sym.get("etiology")
        if isinstance(eti_pud, dict):
            elements.append(Paragraph("Real etiology -- H. pylori, NSAIDs, Zollinger-Ellison syndrome, stress ulcers:", subhead))
            for k, v in eti_pud.items():
                render_generic_kv(k, v)
            elements.append(Spacer(1, 4))

        cgd = sym.get("classification_gastric_vs_duodenal")
        if isinstance(cgd, dict):
            elements.append(Paragraph("Real classification -- gastric vs duodenal ulcer:", subhead))
            for k, v in cgd.items():
                if k == "source" or not isinstance(v, str):
                    continue
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
            if cgd.get("source"):
                elements.append(Paragraph(f"Source: {cite(cgd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        csp = sym.get("classic_symptoms")
        if isinstance(csp, dict):
            elements.append(Paragraph("Real classic symptoms -- epigastric pain pattern and silent ulcers:", subhead))
            for k, v in csp.items():
                if k == "source" or not isinstance(v, str):
                    continue
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
            if csp.get("source"):
                elements.append(Paragraph(f"Source: {cite(csp['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        dfx_pud = sym.get("diagnostic_framework")
        if isinstance(dfx_pud, dict):
            elements.append(Paragraph("Real diagnostic framework -- upper endoscopy and H. pylori testing methods:", subhead))
            if dfx_pud.get("upper_endoscopy"):
                elements.append(Paragraph(f"<b>Upper endoscopy:</b> {dfx_pud['upper_endoscopy']}", body))
            htm = dfx_pud.get("h_pylori_testing_methods_and_comparison")
            if isinstance(htm, dict):
                elements.append(Paragraph("H. pylori testing methods and comparison:", body))
                for k, v in htm.items():
                    if k == "source" or not isinstance(v, str):
                        continue
                    elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
                if htm.get("source"):
                    elements.append(Paragraph(f"Source: {cite(htm['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        epi_pud = sym.get("epidemiology")
        if isinstance(epi_pud, dict):
            elements.append(Paragraph("Real epidemiology:", subhead))
            if epi_pud.get("global_burden"):
                elements.append(Paragraph(f"<b>Global burden:</b> {epi_pud['global_burden']}", body))
            if epi_pud.get("india_specific_data"):
                elements.append(Paragraph(f"<b>India-specific data:</b> {epi_pud['india_specific_data']}", body))
            if epi_pud.get("source"):
                elements.append(Paragraph(f"Source: {cite(epi_pud['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Inflammatory Bowel Disease (Crohn's + UC)-specific structured blocks ----
    # This entry's clinical content is correctly nested entirely inside "symptoms" (same correct
    # pattern as peptic_ulcer_disease), but it introduces several new key names
    # (definition_and_classification, classification_and_disease_activity_scoring,
    # extraintestinal_manifestations) that match NO existing handler anywhere in this file and would
    # otherwise be silently dropped entirely, plus reused generic key names (classic_symptoms,
    # diagnostic_framework, epidemiology) that would otherwise be caught and MISLABELED by unrelated
    # generic handlers (GINA asthma's "circadian pattern" heading for classic_symptoms; the
    # Lake-Louise/Dallas myocarditis catch-all for diagnostic_framework; the india_burden/source_india
    # generic epidemiology branch that does not match this entry's india_specific_data/source key
    # names) -- exactly the recurring bug class this file's own header comments warn about. Rendered
    # explicitly here instead. (complications, real_risk_factors, natural_history_and_prognosis, and
    # red_flags/red_flags_source are flat string-valued dicts/lists that already render correctly,
    # with correct real headings, through this file's existing generic handlers further below, so are
    # intentionally NOT duplicated here.)
    if disease_id == "inflammatory_bowel_disease":
        dac = sym.get("definition_and_classification")
        if isinstance(dac, dict):
            elements.append(Paragraph("Real definition and classification -- Crohn's Disease vs Ulcerative Colitis:", subhead))
            if dac.get("definition"):
                elements.append(Paragraph(dac["definition"], body))
            for dk, dlabel in (("crohns_disease_distinguishing_features", "Crohn's Disease -- distinguishing features:"),
                                ("ulcerative_colitis_distinguishing_features", "Ulcerative Colitis -- distinguishing features:")):
                sub = dac.get(dk)
                if isinstance(sub, dict):
                    elements.append(Paragraph(dlabel, body))
                    for sk, sv in sub.items():
                        if sk == "source" or not isinstance(sv, str):
                            continue
                        elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {sv}", bullet))
                    if sub.get("source"):
                        elements.append(Paragraph(f"Source: {cite(sub['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        cdas = sym.get("classification_and_disease_activity_scoring")
        if isinstance(cdas, dict):
            elements.append(Paragraph("Real classification and disease-activity scoring -- Montreal Classification, CDAI, Mayo Score:", subhead))
            for ck, clabel in (
                ("montreal_classification_crohns_disease", "Montreal Classification -- Crohn's Disease"),
                ("montreal_classification_ulcerative_colitis", "Montreal Classification -- Ulcerative Colitis"),
                ("cdai_crohns_disease_activity_index", "CDAI (Crohn's Disease Activity Index)"),
                ("mayo_score_ulcerative_colitis", "Mayo Score (Ulcerative Colitis)"),
            ):
                if isinstance(cdas.get(ck), str):
                    elements.append(Paragraph(f"<b>{clabel}:</b> {cdas[ck]}", body))
            if cdas.get("source"):
                elements.append(Paragraph(f"Source: {cite(cdas['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        csx_ibd = sym.get("classic_symptoms")
        if isinstance(csx_ibd, dict):
            elements.append(Paragraph("Real classic symptoms -- Crohn's Disease vs Ulcerative Colitis:", subhead))
            for sk, slabel in (("crohns_disease", "Crohn's Disease"), ("ulcerative_colitis", "Ulcerative Colitis")):
                if isinstance(csx_ibd.get(sk), str):
                    elements.append(Paragraph(f"<b>{slabel}:</b> {csx_ibd[sk]}", body))
            if csx_ibd.get("source"):
                elements.append(Paragraph(f"Source: {cite(csx_ibd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        eim = sym.get("extraintestinal_manifestations")
        if isinstance(eim, dict):
            elements.append(Paragraph("Real extraintestinal manifestations:", subhead))
            if eim.get("overview"):
                elements.append(Paragraph(eim["overview"], body))
            for ek, elabel in (("joint", "Joint"), ("skin", "Skin"), ("eye", "Eye"), ("hepatobiliary", "Hepatobiliary")):
                if isinstance(eim.get(ek), str):
                    elements.append(Paragraph(f"• <b>{elabel}:</b> {eim[ek]}", bullet))
            if eim.get("source"):
                elements.append(Paragraph(f"Source: {cite(eim['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        dfw_ibd = sym.get("diagnostic_framework")
        if isinstance(dfw_ibd, dict):
            elements.append(Paragraph("Real diagnostic framework -- Ileocolonoscopy, MR Enterography, Fecal Calprotectin:", subhead))
            for fk, flabel in (("gold_standard", "Gold standard"), ("mr_enterography", "MR enterography"),
                                ("fecal_calprotectin", "Fecal calprotectin")):
                if isinstance(dfw_ibd.get(fk), str):
                    elements.append(Paragraph(f"<b>{flabel}:</b> {dfw_ibd[fk]}", body))
            if dfw_ibd.get("source"):
                elements.append(Paragraph(f"Source: {cite(dfw_ibd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        epi_ibd = sym.get("epidemiology")
        if isinstance(epi_ibd, dict):
            elements.append(Paragraph("Real epidemiology:", subhead))
            if epi_ibd.get("global_burden"):
                elements.append(Paragraph(f"<b>Global burden:</b> {epi_ibd['global_burden']}", body))
            if epi_ibd.get("india_specific_data"):
                elements.append(Paragraph(f"<b>India-specific data:</b> {epi_ibd['india_specific_data']}", body))
            if epi_ibd.get("source"):
                elements.append(Paragraph(f"Source: {cite(epi_ibd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- GERD-specific structured blocks ----
    # This entry's clinical content is correctly nested entirely inside "symptoms" (same correct
    # pattern as peptic_ulcer_disease/inflammatory_bowel_disease), but it introduces a new key name
    # (definition_and_pathophysiology, which matches NO existing handler anywhere in this file and
    # would otherwise be silently dropped entirely) plus reused generic key names (classic_symptoms,
    # diagnostic_framework, complications, epidemiology) that would otherwise be caught and
    # MISLABELED or partially dropped by unrelated generic handlers exactly as documented in the
    # PUD/IBD comments above (GINA asthma's "circadian pattern" heading for classic_symptoms; the
    # Lake-Louise/Dallas myocarditis catch-all for diagnostic_framework; the generic "complications"
    # handler further below silently drops this entry's flat top-level "source" citation because it
    # only excludes -- never prints -- a top-level "source" key; the generic "global_burden" epidemiology
    # branch expects "india_burden"/"source_global"/"source_india" key names this entry does not use).
    # Rendered explicitly here instead, with matching disease_id=="gerd" guards added at each of those
    # generic handlers further below so none of this real content is silently dropped or mislabeled.
    # (real_risk_factors and natural_history_and_prognosis are flat string-valued dicts that already
    # render correctly, with correct real headings and correct source-citation printing, through this
    # file's existing generic handlers further below, so are intentionally NOT duplicated here; red_flags
    # is a plain list that also already renders correctly through the generic red_flags handler.)
    if disease_id == "gerd":
        dap_gerd = sym.get("definition_and_pathophysiology")
        if isinstance(dap_gerd, dict):
            elements.append(Paragraph("Real definition and pathophysiology:", subhead))
            for dk, dlabel in (
                ("definition", "Definition"),
                ("transient_les_relaxations_central_mechanism", "Transient LES relaxations -- central mechanism"),
                ("hiatal_hernia_contributory_role", "Hiatal hernia -- contributory role"),
                ("delayed_gastric_emptying_contributory_role", "Delayed gastric emptying -- contributory role"),
            ):
                if isinstance(dap_gerd.get(dk), str):
                    elements.append(Paragraph(f"<b>{dlabel}:</b> {dap_gerd[dk]}", body))
            if dap_gerd.get("source"):
                elements.append(Paragraph(f"Source: {cite(dap_gerd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        csx_gerd = sym.get("classic_symptoms")
        if isinstance(csx_gerd, dict):
            elements.append(Paragraph("Real classic symptoms -- Heartburn/Regurgitation, Dysphagia Red Flag, and Atypical/Extraesophageal Manifestations:", subhead))
            if isinstance(csx_gerd.get("heartburn_and_regurgitation"), str):
                elements.append(Paragraph(f"<b>Heartburn and regurgitation:</b> {csx_gerd['heartburn_and_regurgitation']}", body))
            if isinstance(csx_gerd.get("dysphagia_red_flag"), str):
                elements.append(Paragraph(f"<b>Dysphagia (red flag):</b> {csx_gerd['dysphagia_red_flag']}", body))
            aem = csx_gerd.get("atypical_extraesophageal_manifestations")
            if isinstance(aem, dict):
                elements.append(Paragraph("Atypical/extraesophageal manifestations:", body))
                for ek, elabel in (
                    ("chronic_cough", "Chronic cough"),
                    ("laryngitis_hoarseness", "Laryngitis/hoarseness"),
                    ("dental_erosion", "Dental erosion"),
                    ("asthma_exacerbation", "Asthma exacerbation"),
                ):
                    if isinstance(aem.get(ek), str):
                        elements.append(Paragraph(f"• <b>{elabel}:</b> {aem[ek]}", bullet))
                if aem.get("source"):
                    elements.append(Paragraph(f"Source: {cite(aem['source'])}", cite_marker_s))
            if csx_gerd.get("source"):
                elements.append(Paragraph(f"Source: {cite(csx_gerd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        dfw_gerd = sym.get("diagnostic_framework")
        if isinstance(dfw_gerd, dict):
            elements.append(Paragraph("Real diagnostic framework -- Empiric PPI Trial, Upper Endoscopy, Ambulatory pH-Impedance Monitoring (Lyon Consensus), and High-Resolution Manometry:", subhead))
            for fk, flabel in (
                ("empiric_ppi_trial", "Empiric PPI trial"),
                ("upper_endoscopy", "Upper endoscopy"),
                ("ambulatory_ph_monitoring_and_lyon_consensus", "Ambulatory pH monitoring and the Lyon Consensus"),
                ("high_resolution_esophageal_manometry", "High-resolution esophageal manometry"),
            ):
                if isinstance(dfw_gerd.get(fk), str):
                    elements.append(Paragraph(f"<b>{flabel}:</b> {dfw_gerd[fk]}", body))
            if dfw_gerd.get("source"):
                elements.append(Paragraph(f"Source: {cite(dfw_gerd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        comp_gerd = sym.get("complications")
        if isinstance(comp_gerd, dict):
            elements.append(Paragraph("Real complications:", subhead))
            for ck, clabel in (
                ("erosive_esophagitis", "Erosive esophagitis"),
                ("esophageal_stricture", "Esophageal stricture"),
                ("barretts_esophagus_and_progression_to_cancer", "Barrett's esophagus and progression to cancer"),
                ("boerhaave_syndrome", "Boerhaave syndrome"),
            ):
                if isinstance(comp_gerd.get(ck), str):
                    elements.append(Paragraph(f"• <b>{clabel}:</b> {comp_gerd[ck]}", bullet))
            if comp_gerd.get("source"):
                elements.append(Paragraph(f"Source: {cite(comp_gerd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        epi_gerd = sym.get("epidemiology")
        if isinstance(epi_gerd, dict):
            elements.append(Paragraph("Real epidemiology:", subhead))
            if epi_gerd.get("global_burden"):
                elements.append(Paragraph(f"<b>Global burden:</b> {epi_gerd['global_burden']}", body))
            if epi_gerd.get("india_specific_data"):
                elements.append(Paragraph(f"<b>India-specific data:</b> {epi_gerd['india_specific_data']}", body))
            if epi_gerd.get("source"):
                elements.append(Paragraph(f"Source: {cite(epi_gerd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Acute Pancreatitis-specific structured blocks ----
    # This entry's clinical content is correctly nested entirely inside "symptoms" (same correct
    # pattern as peptic_ulcer_disease/inflammatory_bowel_disease/gerd), but it introduces several new
    # key names (definition_and_pathophysiology, etiology as a dict-of-topic-dicts, classification_and_
    # severity, severity_and_prognostic_scoring_tools) that match NO existing handler anywhere in this
    # file and would otherwise be silently dropped entirely, plus reused generic key names
    # (classic_symptoms, diagnostic_framework, epidemiology) that would otherwise be caught and
    # MISLABELED by unrelated generic handlers (GINA asthma's "circadian pattern" heading for
    # classic_symptoms; the Lake-Louise/Dallas myocarditis catch-all for diagnostic_framework, which
    # also only renders dict-valued sub-keys and would silently drop this entry's string-valued
    # "lipase_vs_amylase" and top-level "source"; the generic "global_burden" epidemiology branch that
    # expects "india_burden"/"source_global"/"source_india" key names this entry does not use). Rendered
    # explicitly here instead, exactly the recurring bug class this file's own header comments warn
    # about. (complications, natural_history_and_prognosis, and red_flags/red_flags_source are
    # flat/nested string-valued dicts and a plain list respectively that already render correctly, with
    # correct real headings, through this file's existing generic handlers further below, so are
    # intentionally NOT duplicated here. risk_factors_beyond_etiology is a flat string-valued dict
    # rendered via render_flat_dict_section further below with its own unique key name -- no collision
    # risk since no other disease uses that key name.)
    if disease_id == "acute_pancreatitis":
        dap_ap = sym.get("definition_and_pathophysiology")
        if isinstance(dap_ap, dict):
            elements.append(Paragraph("Real definition and pathophysiology:", subhead))
            if dap_ap.get("definition"):
                elements.append(Paragraph(f"<b>Definition:</b> {dap_ap['definition']}", body))
            if dap_ap.get("core_pathophysiologic_framework"):
                elements.append(Paragraph(f"<b>Core pathophysiologic framework:</b> {dap_ap['core_pathophysiologic_framework']}", body))
            if dap_ap.get("source"):
                elements.append(Paragraph(f"Source: {cite(dap_ap['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        eti_ap = sym.get("etiology")
        if isinstance(eti_ap, dict):
            elements.append(Paragraph("Real etiology -- gallstones, alcohol, hypertriglyceridemia, post-ERCP, drug-induced, hyperparathyroidism/hypercalcemia, idiopathic (incl. India-specific regional data):", subhead))
            for ek, ev in eti_ap.items():
                if ek == "source":
                    continue
                label = ek.replace("_", " ").title()
                if isinstance(ev, str):
                    elements.append(Paragraph(f"• <b>{label}:</b> {ev}", bullet))
                elif isinstance(ev, dict):
                    elements.append(Paragraph(f"<b>{label}:</b>", body))
                    for sk, sv in ev.items():
                        if sk == "source" or not isinstance(sv, str):
                            continue
                        elements.append(Paragraph(f"&nbsp;&nbsp;• <b>{sk.replace('_', ' ').title()}:</b> {sv}", small_grey))
                    if ev.get("source"):
                        elements.append(Paragraph(f"&nbsp;&nbsp;Source: {cite(ev['source'])}", cite_marker_s))
            if eti_ap.get("source"):
                elements.append(Paragraph(f"Source: {cite(eti_ap['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        cas_ap = sym.get("classification_and_severity")
        if isinstance(cas_ap, dict):
            elements.append(Paragraph("Real classification -- morphologic types (interstitial edematous vs necrotizing) and revised Atlanta severity (mild/moderately severe/severe), incl. modified Marshall scoring:", subhead))
            for ck, cv in cas_ap.items():
                if not isinstance(cv, dict):
                    continue
                elements.append(Paragraph(ck.replace("_", " ").title() + ":", body))
                for sk, sv in cv.items():
                    if sk == "source" or not isinstance(sv, str):
                        continue
                    elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {sv}", bullet))
                if cv.get("source"):
                    elements.append(Paragraph(f"Source: {cite(cv['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        spst_ap = sym.get("severity_and_prognostic_scoring_tools")
        if isinstance(spst_ap, dict):
            elements.append(Paragraph("Real severity/prognostic scoring tools -- BISAP, Ranson's Criteria, APACHE II (honest bedside comparison):", subhead))
            for tk, tv in spst_ap.items():
                if not isinstance(tv, dict):
                    continue
                elements.append(Paragraph(tk.replace("_", " ").title() + ":", body))
                for sk, sv in tv.items():
                    if sk == "source" or not isinstance(sv, str):
                        continue
                    elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {sv}", bullet))
                if tv.get("source"):
                    elements.append(Paragraph(f"Source: {cite(tv['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        csx_ap = sym.get("classic_symptoms")
        if isinstance(csx_ap, dict):
            elements.append(Paragraph("Real classic symptoms -- epigastric pain pattern, Cullen's sign & Grey Turner's sign:", subhead))
            if isinstance(csx_ap.get("primary_presentation"), str):
                elements.append(Paragraph(f"<b>Primary presentation:</b> {csx_ap['primary_presentation']}", body))
            pef = csx_ap.get("physical_exam_findings_severe_disease")
            if isinstance(pef, dict):
                elements.append(Paragraph("Physical exam findings in severe disease:", body))
                for sk, sv in pef.items():
                    if sk == "source" or not isinstance(sv, str):
                        continue
                    elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {sv}", bullet))
                if pef.get("source"):
                    elements.append(Paragraph(f"Source: {cite(pef['source'])}", cite_marker_s))
            if csx_ap.get("source"):
                elements.append(Paragraph(f"Source: {cite(csx_ap['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        dfw_ap = sym.get("diagnostic_framework")
        if isinstance(dfw_ap, dict):
            elements.append(Paragraph("Real diagnostic framework -- Revised Atlanta Classification (2012) diagnostic criteria, lipase vs amylase:", subhead))
            racd = dfw_ap.get("revised_atlanta_classification_2012_diagnostic_criteria")
            if isinstance(racd, dict):
                if isinstance(racd.get("criteria"), list):
                    elements.append(Paragraph("Diagnostic criteria (>=2 of 3 required):", body))
                    for c in racd["criteria"]:
                        if isinstance(c, str):
                            elements.append(Paragraph(f"• {c}", bullet))
                if racd.get("rule"):
                    elements.append(Paragraph(f"<b>Rule:</b> {racd['rule']}", body))
                if racd.get("source"):
                    elements.append(Paragraph(f"Source: {cite(racd['source'])}", cite_marker_s))
            if isinstance(dfw_ap.get("lipase_vs_amylase"), str):
                elements.append(Paragraph(f"<b>Lipase vs amylase:</b> {dfw_ap['lipase_vs_amylase']}", body))
            if isinstance(dfw_ap.get("source"), str):
                elements.append(Paragraph(f"Source: {cite(dfw_ap['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        epi_ap = sym.get("epidemiology")
        if isinstance(epi_ap, dict):
            elements.append(Paragraph("Real epidemiology:", subhead))
            if epi_ap.get("global_burden"):
                elements.append(Paragraph(f"<b>Global burden:</b> {epi_ap['global_burden']}", body))
            if epi_ap.get("india_specific_data"):
                elements.append(Paragraph(f"<b>India-specific data:</b> {epi_ap['india_specific_data']}", body))
            if epi_ap.get("source"):
                elements.append(Paragraph(f"Source: {cite(epi_ap['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Celiac Disease-specific structured blocks ----
    # This entry's clinical content is correctly nested entirely inside "symptoms" (same correct
    # pattern as peptic_ulcer_disease/inflammatory_bowel_disease/gerd/acute_pancreatitis), but it
    # introduces several new key names (definition_and_pathophysiology, classification_spectrum,
    # associated_conditions) that match NO existing handler anywhere in this file and would otherwise
    # be silently dropped entirely, plus reused generic key names (classic_symptoms, diagnostic_framework,
    # epidemiology, complications) that would otherwise be caught and MISLABELED or partially dropped by
    # unrelated generic handlers exactly as documented in the PUD/IBD/GERD/AP comments above (GINA
    # asthma's "circadian pattern" heading for classic_symptoms; the Lake-Louise/Dallas myocarditis
    # catch-all for diagnostic_framework; the generic "global_prevalence" epidemiology branch which
    # renders this entry's real content under an unrelated "Global GBD & India INSEARCH" heading; the
    # generic "complications" handler further below which excludes but never prints a top-level "source"
    # key, silently dropping this entry's complications source citation). Rendered explicitly here
    # instead, with matching disease_id=="celiac_disease" guards added at each of those generic handlers
    # further below so none of this real content is silently dropped or mislabeled. (natural_history_and_
    # prognosis is a flat string-valued dict that already renders correctly, with a correct real heading
    # and correct source-citation printing, through this file's existing render_flat_dict_section generic
    # handler further below, so is intentionally NOT duplicated here; red_flags is a plain string-valued
    # dict that already renders correctly through the generic red_flags handler.)
    if disease_id == "celiac_disease":
        dap_cel = sym.get("definition_and_pathophysiology")
        if isinstance(dap_cel, dict):
            elements.append(Paragraph("Real definition and pathophysiology:", subhead))
            for dk, dlabel in (
                ("definition", "Definition"),
                ("hla_genetics", "HLA genetics"),
                ("trigger_and_autoimmune_mechanism", "Trigger and autoimmune mechanism"),
                ("villous_atrophy_and_malabsorption_mechanism", "Villous atrophy and malabsorption mechanism"),
            ):
                if isinstance(dap_cel.get(dk), str):
                    elements.append(Paragraph(f"<b>{dlabel}:</b> {dap_cel[dk]}", body))
            if dap_cel.get("source"):
                elements.append(Paragraph(f"Source: {cite(dap_cel['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        csp_cel = sym.get("classification_spectrum")
        if isinstance(csp_cel, dict):
            elements.append(Paragraph("Real classification spectrum -- Classic, Non-Classic/Atypical, Potential, and Silent/Subclinical Celiac Disease (Oslo definitions):", subhead))
            for ck, clabel in (
                ("classic_celiac_disease", "Classic celiac disease"),
                ("non_classic_atypical_celiac_disease", "Non-classic/atypical celiac disease"),
                ("potential_celiac_disease", "Potential celiac disease"),
                ("silent_subclinical_celiac_disease", "Silent/subclinical celiac disease"),
            ):
                if isinstance(csp_cel.get(ck), str):
                    elements.append(Paragraph(f"• <b>{clabel}:</b> {csp_cel[ck]}", bullet))
            if csp_cel.get("source"):
                elements.append(Paragraph(f"Source: {cite(csp_cel['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        csx_cel = sym.get("classic_symptoms")
        if isinstance(csx_cel, dict):
            elements.append(Paragraph("Real classic symptoms -- Classic Gastrointestinal Presentation vs Non-Classic Extraintestinal Presentation:", subhead))
            if isinstance(csx_cel.get("classic_gastrointestinal_presentation"), str):
                elements.append(Paragraph(f"<b>Classic gastrointestinal presentation:</b> {csx_cel['classic_gastrointestinal_presentation']}", body))
            ncep = csx_cel.get("non_classic_extraintestinal_presentation")
            if isinstance(ncep, dict):
                elements.append(Paragraph("Non-classic extraintestinal presentation:", body))
                for sk, sv in ncep.items():
                    if sk == "source" or not isinstance(sv, str):
                        continue
                    elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {sv}", bullet))
                if ncep.get("source"):
                    elements.append(Paragraph(f"Source: {cite(ncep['source'])}", cite_marker_s))
            if csx_cel.get("source"):
                elements.append(Paragraph(f"Source: {cite(csx_cel['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        assoc_cel = sym.get("associated_conditions")
        if isinstance(assoc_cel, dict):
            elements.append(Paragraph("Real associated conditions -- Type 1 Diabetes, Autoimmune Thyroid Disease, Down Syndrome, First-Degree Relatives:", subhead))
            for ak, alabel in (
                ("type_1_diabetes_mellitus", "Type 1 diabetes mellitus"),
                ("autoimmune_thyroid_disease", "Autoimmune thyroid disease"),
                ("down_syndrome", "Down syndrome"),
                ("first_degree_relatives", "First-degree relatives"),
            ):
                if isinstance(assoc_cel.get(ak), str):
                    elements.append(Paragraph(f"• <b>{alabel}:</b> {assoc_cel[ak]}", bullet))
            if assoc_cel.get("source"):
                elements.append(Paragraph(f"Source: {cite(assoc_cel['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        dfw_cel = sym.get("diagnostic_framework")
        if isinstance(dfw_cel, dict):
            elements.append(Paragraph("Real diagnostic framework -- Serology, Confirmatory EMA, Duodenal Biopsy (Gold Standard), ESPGHAN Biopsy-Free Pediatric Pathway, HLA Typing:", subhead))
            for fk, flabel in (
                ("critical_pretest_pitfall", "Critical pretest pitfall"),
                ("first_line_serology", "First-line serology"),
                ("confirmatory_serology_EMA", "Confirmatory serology (EMA)"),
                ("duodenal_biopsy_gold_standard", "Duodenal biopsy (gold standard)"),
                ("espghan_biopsy_free_pediatric_pathway", "ESPGHAN biopsy-free paediatric pathway"),
                ("hla_typing_role", "HLA typing -- role"),
            ):
                if isinstance(dfw_cel.get(fk), str):
                    elements.append(Paragraph(f"<b>{flabel}:</b> {dfw_cel[fk]}", body))
            if dfw_cel.get("source"):
                elements.append(Paragraph(f"Source: {cite(dfw_cel['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        comp_cel = sym.get("complications")
        if isinstance(comp_cel, dict):
            elements.append(Paragraph("Real complications -- Refractory Celiac Disease, EATL, Small Bowel Adenocarcinoma, Osteoporosis/Fracture Risk:", subhead))
            for ck, clabel in (
                ("refractory_celiac_disease", "Refractory celiac disease"),
                ("enteropathy_associated_t_cell_lymphoma_EATL", "Enteropathy-associated T-cell lymphoma (EATL)"),
                ("small_bowel_adenocarcinoma", "Small bowel adenocarcinoma"),
                ("osteoporosis_and_fracture_risk", "Osteoporosis and fracture risk"),
            ):
                if isinstance(comp_cel.get(ck), str):
                    elements.append(Paragraph(f"• <b>{clabel}:</b> {comp_cel[ck]}", bullet))
            if comp_cel.get("source"):
                elements.append(Paragraph(f"Source: {cite(comp_cel['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        epi_cel = sym.get("epidemiology")
        if isinstance(epi_cel, dict):
            elements.append(Paragraph("Real epidemiology:", subhead))
            if epi_cel.get("global_prevalence"):
                elements.append(Paragraph(f"<b>Global prevalence:</b> {epi_cel['global_prevalence']}", body))
            if epi_cel.get("india_specific_data"):
                elements.append(Paragraph(f"<b>India-specific data:</b> {epi_cel['india_specific_data']}", body))
            if epi_cel.get("source"):
                elements.append(Paragraph(f"Source: {cite(epi_cel['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Osteoporosis-specific structured blocks ----
    if disease_id == "osteoporosis":
        wdx = sym.get("who_dxa_diagnostic_criteria")
        if wdx:
            elements.append(Paragraph("Real WHO/DXA diagnostic criteria (T-score):", subhead))
            if wdx.get("definition"):
                elements.append(Paragraph(wdx["definition"], body))
            for c in wdx.get("categories", []):
                if isinstance(c, dict):
                    elements.append(Paragraph(f"• <b>{c.get('category', '')}:</b> {c.get('t_score', '')}", bullet))
            if wdx.get("t_score_vs_z_score"):
                elements.append(Paragraph(f"<b>T-score vs Z-score:</b> {wdx['t_score_vs_z_score']}", body))
            if wdx.get("source"):
                elements.append(Paragraph(f"Confidence: {wdx.get('confidence', '')} | Source: {cite(wdx['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        cps = sym.get("classification_primary_vs_secondary")
        if isinstance(cps, dict):
            elements.append(Paragraph("Real classification -- Primary (Type I/II) vs Secondary Osteoporosis:", subhead))
            for ck, cv in cps.items():
                render_generic_kv(ck, cv)
            elements.append(Spacer(1, 4))

        ccp = sym.get("core_clinical_presentation")
        if isinstance(ccp, list):
            elements.append(Paragraph("Real core clinical presentation:", subhead))
            for item in ccp:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• <b>{item.get('name', '')}:</b> {item.get('note', '')}", bullet))
                if item.get("source"):
                    elements.append(Paragraph(f"Confidence: {item.get('confidence', '')} | Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        frax = sym.get("fracture_risk_assessment_frax")
        if frax:
            elements.append(Paragraph("Real FRAX (Fracture Risk Assessment Tool):", subhead))
            for fk, flabel in (("what_it_is", "What it is"), ("inputs", "Inputs"), ("treatment_threshold", "Treatment threshold")):
                if frax.get(fk):
                    elements.append(Paragraph(f"<b>{flabel}:</b> {frax[fk]}", body))
            if frax.get("source"):
                elements.append(Paragraph(f"Confidence: {frax.get('confidence', '')} | Source: {cite(frax['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        disamb = sym.get("osteoporosis_vs_osteomalacia_disambiguation")
        if disamb:
            elements.append(Paragraph("Real disambiguation -- Osteoporosis vs Rickets/Osteomalacia:", subhead))
            if disamb.get("note"):
                elements.append(Paragraph(disamb["note"], body))
            if disamb.get("source"):
                elements.append(Paragraph(f"Confidence: {disamb.get('confidence', '')} | Source: {cite(disamb['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))
        # (natural_history is intentionally not rendered here -- it is already handled correctly,
        # with its source/confidence line, by the generic "natural_history" block further below.)

    # ---- COPD-specific (Respiratory category) structured blocks ----
    if sym.get("gold_stage_classification"):
        gsc = sym["gold_stage_classification"]
        elements.append(Paragraph("Real GOLD spirometric stage classification (1-4):", subhead))
        if gsc.get("note"):
            elements.append(Paragraph(gsc["note"], body))
        for st in gsc.get("stages", []):
            elements.append(Paragraph(
                f"• <b>{st.get('stage', '')} ({st.get('severity', '')}):</b> {st.get('fev1_pct_predicted', '')}",
                bullet))
        if gsc.get("important_caveat"):
            elements.append(Paragraph(f"<i>{gsc['important_caveat']}</i>", small_grey))
        if gsc.get("source"):
            elements.append(Paragraph(f"Confidence: {gsc.get('confidence', '')} | Source: {cite(gsc['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("assessment_tools"):
        at = sym["assessment_tools"]
        elements.append(Paragraph("Real assessment tools -- spirometry, mMRC, CAT:", subhead))
        sp = at.get("spirometry")
        if isinstance(sp, dict):
            elements.append(Paragraph(f"<b>Spirometry:</b> {sp.get('role', '')}", body))
            if sp.get("source"):
                elements.append(Paragraph(f"Source: {cite(sp['source'])}", cite_marker_s))
        mm = at.get("mmrc_dyspnoea_scale")
        if isinstance(mm, dict):
            elements.append(Paragraph("mMRC Dyspnoea Scale:", body))
            for g in mm.get("grades", []):
                elements.append(Paragraph(f"• Grade {g.get('grade', '')}: {g.get('description', '')}", bullet))
            if mm.get("clinical_use"):
                elements.append(Paragraph(mm["clinical_use"], small_grey))
            if mm.get("source"):
                elements.append(Paragraph(f"Source: {cite(mm['source'])}", cite_marker_s))
        cat = at.get("cat_copd_assessment_test")
        if isinstance(cat, dict):
            elements.append(Paragraph("CAT (COPD Assessment Test):", body))
            if cat.get("description"):
                elements.append(Paragraph(cat["description"], body))
            if cat.get("score_interpretation"):
                elements.append(Paragraph(f"Score interpretation: {cat['score_interpretation']}", small_grey))
            if cat.get("clinical_use"):
                elements.append(Paragraph(cat["clinical_use"], small_grey))
            if cat.get("source"):
                elements.append(Paragraph(f"Source: {cite(cat['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("exacerbations"):
        exa = sym["exacerbations"]
        elements.append(Paragraph("Real exacerbation definition, severity, and frequent-exacerbator phenotype:", subhead))
        if exa.get("definition"):
            elements.append(Paragraph(exa["definition"], body))
        sci = exa.get("severity_classification_by_treatment_intensity")
        if isinstance(sci, dict):
            for k in ("mild", "moderate", "severe"):
                if sci.get(k):
                    elements.append(Paragraph(f"• <b>{k.title()}:</b> {sci[k]}", bullet))
        if exa.get("source"):
            elements.append(Paragraph(f"Source: {cite(exa['source'])}", cite_marker_s))
        fep = exa.get("frequent_exacerbator_phenotype")
        if isinstance(fep, dict):
            elements.append(Paragraph("Frequent-exacerbator phenotype:", body))
            if fep.get("definition"):
                elements.append(Paragraph(f"<b>Definition:</b> {fep['definition']}", body))
            if fep.get("prognostic_significance"):
                elements.append(Paragraph(fep["prognostic_significance"], body))
            if fep.get("source"):
                elements.append(Paragraph(f"Confidence: {fep.get('confidence', '')} | Source: {cite(fep['source'])}", cite_marker_s))
        if exa.get("cross_reference"):
            elements.append(Paragraph(f"<i>{exa['cross_reference']}</i>", small_grey))
        elements.append(Spacer(1, 4))

    if sym.get("real_definition_diagnostic_criteria"):
        rdc = sym["real_definition_diagnostic_criteria"]
        elements.append(Paragraph("Real definition / diagnostic criteria:", subhead))
        if rdc.get("note"):
            elements.append(Paragraph(rdc["note"], body))
        for c in rdc.get("criteria", []):
            elements.append(Paragraph(f"• {c}", bullet))
        if rdc.get("source"):
            elements.append(Paragraph(f"Confidence: {rdc.get('confidence', '')} | Source: {cite(rdc['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("scai_shock_stage_classification"):
        scai = sym["scai_shock_stage_classification"]
        elements.append(Paragraph("Real SCAI Shock Stage Classification (A-E):", subhead))
        if scai.get("note"):
            elements.append(Paragraph(scai["note"], body))
        for st in scai.get("stages", []):
            elements.append(Paragraph(f"Stage {st.get('stage', '')} — {st.get('name', '')}:", body))
            for fk, flabel in (("physical_exam", "Physical exam"), ("biochemical", "Biochemical"),
                                ("hemodynamics", "Hemodynamics"), ("clinical_meaning", "Clinical meaning")):
                if st.get(fk):
                    elements.append(Paragraph(f"• <b>{flabel}:</b> {st[fk]}", bullet))
        for sk, slabel in (("source_original", "Source (original)"), ("source_update", "Source (update)")):
            if scai.get(sk):
                elements.append(Paragraph(f"{slabel}: {scai[sk]}", small_grey))
        if scai.get("confidence"):
            elements.append(Paragraph(f"Confidence: {scai['confidence']}", small_grey))
        elements.append(Spacer(1, 4))

    if sym.get("etiology_breakdown"):
        etb = sym["etiology_breakdown"]
        elements.append(Paragraph("Real etiology breakdown (SHOCK Trial Registry):", subhead))
        if etb.get("note"):
            elements.append(Paragraph(etb["note"], body))
        if etb.get("cohort"):
            elements.append(Paragraph(f"<b>Cohort:</b> {etb['cohort']}", body))
        for c in etb.get("causes", []):
            line = f"• <b>{c.get('cause', '')}:</b> {c.get('percent', '')}"
            if c.get("note"):
                line += f" — {c['note']}"
            elements.append(Paragraph(line, bullet))
            if c.get("in_hospital_mortality"):
                elements.append(Paragraph(f"In-hospital mortality: {c['in_hospital_mortality']}", small_grey))
        if etb.get("overall_in_hospital_mortality_this_cohort"):
            elements.append(Paragraph(f"<b>Overall in-hospital mortality (this cohort):</b> {etb['overall_in_hospital_mortality_this_cohort']}", body))
        for oc in etb.get("other_real_causes_not_quantified_in_shock_registry", []):
            if isinstance(oc, dict):
                elements.append(Paragraph(f"• <b>{oc.get('cause', '')}:</b> {oc.get('note', '')}", bullet))
                if oc.get("source"):
                    elements.append(Paragraph(f"Source: {cite(oc['source'])}", cite_marker_s))
        if etb.get("source"):
            elements.append(Paragraph(f"Source: {cite(etb['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("classic_clinical_signs"):
        elements.append(Paragraph("Real classic clinical signs:", subhead))
        for s in sym["classic_clinical_signs"]:
            if not isinstance(s, dict):
                continue
            elements.append(Paragraph(f"• <b>{s.get('sign', '')}:</b> {s.get('note', '')}", bullet))
            if s.get("source"):
                elements.append(Paragraph(f"Source: {cite(s['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("hemodynamic_classification"):
        hc = sym["hemodynamic_classification"]
        elements.append(Paragraph("Real hemodynamic classification (congestion/perfusion phenotyping):", subhead))
        if hc.get("note"):
            elements.append(Paragraph(hc["note"], body))
        for p in hc.get("profiles", []):
            elements.append(Paragraph(f"• <b>{p.get('name', '')}:</b> {p.get('hemodynamics', '')}", bullet))
            for fk, flabel in (("frequency", "Frequency"), ("clinical_picture", "Clinical picture"), ("finding", "Finding")):
                if p.get(fk):
                    elements.append(Paragraph(f"{flabel}: {p[fk]}", small_grey))
        if hc.get("source"):
            elements.append(Paragraph(f"Source: {cite(hc['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("rv_infarction_associated_cs"):
        rv = sym["rv_infarction_associated_cs"]
        elements.append(Paragraph("Real RV-infarction-associated cardiogenic shock (distinct phenotype):", subhead))
        for fk, flabel in (("note", None), ("hemodynamic_profile", "Hemodynamic profile"),
                            ("clinical_picture", "Clinical picture"), ("outcome_data", "Outcome data")):
            if rv.get(fk):
                if flabel:
                    elements.append(Paragraph(f"• <b>{flabel}:</b> {rv[fk]}", bullet))
                else:
                    elements.append(Paragraph(rv[fk], body))
        if rv.get("source"):
            elements.append(Paragraph(f"Confidence: {rv.get('confidence', '')} | Source: {cite(rv['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "incidence_ami_cs" in sym["epidemiology"]:
        epi = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology:", subhead))
        inc = epi.get("incidence_ami_cs", {})
        if inc.get("figures"):
            elements.append(Paragraph(f"• <b>Incidence:</b> {inc['figures']}", bullet))
        if epi.get("timeline_after_mi"):
            elements.append(Paragraph(f"• <b>Timeline after MI:</b> {epi['timeline_after_mi']}", bullet))
        if epi.get("reperfusion_era_evolution"):
            elements.append(Paragraph(f"• <b>Reperfusion-era evolution:</b> {epi['reperfusion_era_evolution']}", bullet))
        ohm = epi.get("overall_in_hospital_mortality")
        if isinstance(ohm, dict):
            for k, v in ohm.items():
                if isinstance(v, str):
                    elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
        elements.append(Spacer(1, 4))
    elif sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "global_and_india" in sym["epidemiology"]:
        epi3 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (global & India):", subhead))
        for item in epi3.get("global_and_india", []):
            if not isinstance(item, dict):
                continue
            elements.append(Paragraph(f"• <b>{item.get('region', '')}:</b> {item.get('finding', '')}", bullet))
            if item.get("source"):
                elements.append(Paragraph(f"Confidence: {item.get('confidence', '')} | Source: {cite(item['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))
    elif sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "global_GBD_2021" in sym["epidemiology"]:
        epi4 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global GBD 2021 & India):", subhead))
        g21 = epi4.get("global_GBD_2021", {})
        if g21.get("findings"):
            elements.append(Paragraph(f"<b>Global (GBD 2021):</b> {g21['findings']}", body))
        if g21.get("asia_specific"):
            elements.append(Paragraph(f"<b>Asia-specific:</b> {g21['asia_specific']}", body))
        if g21.get("source"):
            elements.append(Paragraph(f"Confidence: {g21.get('confidence', '')} | Source: {cite(g21['source'])}", cite_marker_s))
        ie2 = epi4.get("india_epidemiology", {})
        if ie2.get("findings"):
            elements.append(Paragraph(f"<b>India:</b> {ie2['findings']}", body))
        if ie2.get("source"):
            elements.append(Paragraph(f"Confidence: {ie2.get('confidence', '')} | Source: {cite(ie2['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))
    elif (sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "global_prevalence" in sym["epidemiology"]
          and disease_id != "celiac_disease"):
        # Celiac disease's epidemiology (global_prevalence + india_specific_data + source) is already
        # fully and correctly rendered above (Celiac Disease-specific block) with its own accurate
        # heading -- this generic branch's "India INSEARCH" heading names an unrelated asthma study and
        # would mislabel celiac's real content if not excluded here.
        epi5 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global GBD & India INSEARCH):", subhead))
        for k, v in epi5.items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))
    elif (sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "global_burden" in sym["epidemiology"]
          and isinstance(sym["epidemiology"]["global_burden"], str)
          and disease_id not in ("peptic_ulcer_disease", "inflammatory_bowel_disease", "gerd", "acute_pancreatitis", "migraine")):
        # PUD's, IBD's, and GERD's epidemiology (global_burden + india_specific_data + source) are
        # already fully and correctly rendered in their own disease-specific blocks above -- this
        # generic branch expects "india_burden"/"source_global"/"source_india" key names those entries
        # do not use, so it would otherwise silently drop india_specific_data and the source citation.
        # migraine's epidemiology also has a top-level "global_burden" key, but its VALUE is a nested
        # {finding, source, confidence} dict (not a plain string like PUD/IBD/GERD/AP use) -- without
        # the isinstance(..., str) guard and the migraine exclusion, this branch would silently
        # interpolate migraine's dict value with an f-string and print a raw Python dict repr into the
        # PDF instead of readable text. migraine's epidemiology is rendered correctly, as nested dicts,
        # in the disease_id == "migraine" block further below instead.
        epi6 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global Burden of Disease & India):", subhead))
        if epi6.get("global_burden"):
            elements.append(Paragraph(f"<b>Global:</b> {epi6['global_burden']}", body))
        if epi6.get("source_global"):
            elements.append(Paragraph(f"Source: {cite(epi6['source_global'])}", cite_marker_s))
        if epi6.get("india_burden"):
            elements.append(Paragraph(f"<b>India:</b> {epi6['india_burden']}", body))
        if epi6.get("source_india"):
            elements.append(Paragraph(f"Source: {cite(epi6['source_india'])}", cite_marker_s))
        if epi6.get("confidence") or epi6.get("confidence_note"):
            elements.append(Paragraph(
                f"Confidence: {epi6.get('confidence', '')}" + (f" -- {epi6['confidence_note']}" if epi6.get("confidence_note") else ""),
                small_grey))
        elements.append(Spacer(1, 4))
    elif sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "global_ipf" in sym["epidemiology"]:
        epi7 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global IPF & India ILD registry):", subhead))
        if epi7.get("global_ipf"):
            elements.append(Paragraph(f"<b>Global IPF:</b> {epi7['global_ipf']}", body))
        if epi7.get("india_ild"):
            elements.append(Paragraph(f"<b>India (ILD-India registry):</b> {epi7['india_ild']}", body))
        if epi7.get("source"):
            elements.append(Paragraph(f"Confidence: {epi7.get('confidence', '')} | Source: {cite(epi7['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))
    elif sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "PSP_SSP_population_incidence" in sym["epidemiology"]:
        epi10 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (PSP/SSP population incidence, India-specific):", subhead))
        if epi10.get("PSP_SSP_population_incidence"):
            render_generic_kv("PSP_SSP_population_incidence", epi10["PSP_SSP_population_incidence"])
        if epi10.get("source_general"):
            elements.append(Paragraph(f"Source: {cite(epi10['source_general'])}", cite_marker_s))
        if epi10.get("india_specific_note"):
            elements.append(Paragraph(f"<b>India-specific:</b> {epi10['india_specific_note']}", body))
        if epi10.get("source_india"):
            elements.append(Paragraph(f"Source: {cite(epi10['source_india'])}", cite_marker_s))
        elements.append(Spacer(1, 4))
    elif sym.get("epidemiology") and isinstance(sym["epidemiology"], dict) and "global_incidence" in sym["epidemiology"]:
        epi11 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (global incidence & LUNG SAFE):", subhead))
        for k, v in epi11.items():
            if k in ("source", "confidence") or not isinstance(v, str):
                continue
            elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
        if epi11.get("source"):
            elements.append(Paragraph(f"Confidence: {epi11.get('confidence', '')} | Source: {cite(epi11['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("bp_classification"):
        bpc = sym["bp_classification"]
        elements.append(Paragraph("Real BP classification — dual-guideline comparison (ACC/AHA vs ESC/ESH):", subhead))
        if bpc.get("note"):
            elements.append(Paragraph(bpc["note"], body))
        for gkey, glabel in (("acc_aha_2017", "2017 ACC/AHA Classification"), ("esc_esh_2018", "2018 ESC/ESH Classification")):
            g = bpc.get(gkey)
            if not g:
                continue
            elements.append(Paragraph(glabel + ":", body))
            for c in g.get("categories", []):
                line = f"• <b>{c.get('name', '')}:</b> systolic {c.get('systolic', '')}, diastolic {c.get('diastolic', '')}"
                if c.get("note"):
                    line += f" — {c['note']}"
                elements.append(Paragraph(line, bullet))
            if g.get("source"):
                elements.append(Paragraph(f"Confidence: {g.get('confidence', '')} | Source: {cite(g['source'])}", cite_marker_s))
        if bpc.get("key_divergence"):
            elements.append(Paragraph(f"<b>Key divergence:</b> {bpc['key_divergence']}", body))
        elements.append(Spacer(1, 4))

    if sym.get("hypertensive_crisis"):
        hc2 = sym["hypertensive_crisis"]
        elements.append(Paragraph("Real hypertensive crisis classification (urgency vs emergency):", subhead))
        if hc2.get("note"):
            elements.append(Paragraph(hc2["note"], body))
        for k, v in hc2.items():
            if k in ("note", "source") or not isinstance(v, str):
                continue
            elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
        if hc2.get("source"):
            elements.append(Paragraph(f"Source: {cite(hc2['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("kdigo_definition_and_staging"):
        kds = sym["kdigo_definition_and_staging"]
        elements.append(Paragraph("Real KDIGO definition and GFR/albuminuria staging:", subhead))
        if kds.get("definition"):
            elements.append(Paragraph(kds["definition"], body))
        if kds.get("gfr_categories"):
            elements.append(Paragraph("GFR categories (G1-G5):", body))
            for c in kds["gfr_categories"]:
                elements.append(Paragraph(
                    f"• <b>{c.get('category', '')} ({c.get('gfr_range', '')}):</b> {c.get('descriptor', '')}", bullet))
        if kds.get("albuminuria_categories"):
            elements.append(Paragraph("Albuminuria categories (A1-A3):", body))
            for c in kds["albuminuria_categories"]:
                elements.append(Paragraph(
                    f"• <b>{c.get('category', '')} ({c.get('acr_range', '')}):</b> {c.get('descriptor', '')}", bullet))
        if kds.get("heat_map_risk_stratification"):
            elements.append(Paragraph(f"<b>Combined GFR x albuminuria risk heat-map:</b> {kds['heat_map_risk_stratification']}", body))
        if kds.get("source"):
            elements.append(Paragraph(f"Confidence: {kds.get('confidence', '')} | Source: {cite(kds['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("etiology") and isinstance(sym["etiology"], dict) and "primary_essential" in sym["etiology"]:
        et = sym["etiology"]
        elements.append(Paragraph("Real etiology — primary (essential) vs secondary causes:", subhead))
        pe = et.get("primary_essential")
        if pe:
            elements.append(Paragraph(f"<b>Primary (essential):</b> {pe.get('proportion', '')} — {pe.get('note', '')}", body))
            if pe.get("source"):
                elements.append(Paragraph(f"Source: {cite(pe['source'])}", cite_marker_s))
        if et.get("secondary_causes"):
            elements.append(Paragraph("Secondary causes (real, identifiable, sometimes correctable):", subhead))
            for c in et["secondary_causes"]:
                elements.append(Paragraph(f"• <b>{c.get('cause', '')}:</b> {c.get('note', '')}", bullet))
                if c.get("source"):
                    elements.append(Paragraph(f"Source: {cite(c['source'])}", cite_marker_s))
        if et.get("red_flags_for_secondary_workup"):
            elements.append(Paragraph("Red flags prompting secondary-cause workup:", subhead))
            add_bullets(et["red_flags_for_secondary_workup"])
        if et.get("source"):
            elements.append(Paragraph(f"Confidence: {et.get('confidence', '')} | Source: {cite(et['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))
    elif disease_id == "chronic_kidney_disease" and sym.get("etiology") and isinstance(sym["etiology"], dict):
        # Guarded to CKD specifically -- this generic dict-of-dicts "etiology" shape also occurs
        # in cirrhosis (chronic_viral_hepatitis_b_c etc, rendered by the cirrhosis-specific block
        # above), which this elif was previously mislabeling as "causes of CKD" when unguarded.
        et3 = sym["etiology"]
        elements.append(Paragraph("Real etiology (causes of CKD, India-specific data where available):", subhead))
        for cause_key, cause_val in et3.items():
            if not isinstance(cause_val, dict):
                continue
            elements.append(Paragraph(cause_key.replace('_', ' ').title() + ":", body))
            for fk, fv in cause_val.items():
                if fk in ("source", "confidence"):
                    continue
                if isinstance(fv, str):
                    elements.append(Paragraph(f"• <b>{fk.replace('_', ' ').title()}:</b> {fv}", bullet))
                elif isinstance(fv, dict):
                    elements.append(Paragraph(f"• <b>{fk.replace('_', ' ').title()}:</b>", bullet))
                    for sk, sv in fv.items():
                        if sk in ("source", "confidence") or not isinstance(sv, str):
                            continue
                        elements.append(Paragraph(f"&nbsp;&nbsp;- <b>{sk.replace('_', ' ').title()}:</b> {sv}", small_grey))
                    if fv.get("source"):
                        elements.append(Paragraph(f"&nbsp;&nbsp;Confidence: {fv.get('confidence', '')} | Source: {cite(fv['source'])}", cite_marker_s))
            if cause_val.get("source"):
                elements.append(Paragraph(f"Confidence: {cause_val.get('confidence', '')} | Source: {cite(cause_val['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("hypertensive_heart_disease"):
        hhd = sym["hypertensive_heart_disease"]
        elements.append(Paragraph("Real Hypertensive Heart Disease (structural/functional cardiac changes):", subhead))
        if hhd.get("definition"):
            elements.append(Paragraph(hhd["definition"], body))
        lv = hhd.get("lv_hypertrophy")
        if isinstance(lv, dict):
            elements.append(Paragraph("LV Hypertrophy — ECG criteria:", body))
            for c in lv.get("ecg_criteria", []):
                elements.append(Paragraph(f"• <b>{c.get('name', '')}:</b> {c.get('criterion', '')}", bullet))
            if lv.get("diagnostic_accuracy_note"):
                elements.append(Paragraph(lv["diagnostic_accuracy_note"], small_grey))
            if lv.get("source"):
                elements.append(Paragraph(f"Confidence: {lv.get('confidence', '')} | Source: {cite(lv['source'])}", cite_marker_s))
        dd = hhd.get("diastolic_dysfunction_and_hfpef")
        if isinstance(dd, dict) and dd.get("note"):
            elements.append(Paragraph(dd["note"], body))
        if hhd.get("source"):
            elements.append(Paragraph(f"Source: {cite(hhd['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("hypertensive_emergency_end_organ_damage"):
        elements.append(Paragraph("Real hypertensive-emergency end-organ damage by system:", subhead))
        for o in sym["hypertensive_emergency_end_organ_damage"]:
            if not isinstance(o, dict):
                continue
            elements.append(Paragraph(f"• <b>{o.get('organ', '')}:</b> {o.get('manifestation', '')}", bullet))
            if o.get("red_flag"):
                elements.append(Paragraph(f"Red flag: {o['red_flag']}", small_grey))
            if o.get("source"):
                elements.append(Paragraph(f"Source: {cite(o['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    def render_med_topic(v, depth=0):
        # Generic recursive renderer for nested medical-topic dicts shaped like
        # {name?, note?, data?, confidence?, source?, <further nested sub-topics>}
        # (e.g. ventricular_arrhythmia_scd's structural_substrate_categories,
        # primary_electrical_disease_channelopathies, clinical_presentation,
        # epidemiology_scd, diagnostic_tools)
        if isinstance(v, str):
            elements.append(Paragraph(v, body))
            return
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    elements.append(Paragraph(f"• {item}", bullet))
                elif isinstance(item, dict):
                    render_med_topic(item, depth=depth + 1)
            return
        if isinstance(v, dict):
            if v.get("name"):
                elements.append(Paragraph(str(v["name"]), subhead if depth == 0 else body))
            if v.get("note"):
                elements.append(Paragraph(v["note"], body))
            if v.get("data"):
                elements.append(Paragraph(v["data"], body))
            for k2, v2 in v.items():
                if k2 in ("name", "note", "data", "confidence", "source"):
                    continue
                label = k2.replace("_", " ").title()
                if isinstance(v2, str):
                    elements.append(Paragraph(f"• <b>{label}:</b> {v2}", bullet))
                else:
                    elements.append(Paragraph(label + ":", body))
                    render_med_topic(v2, depth=depth + 1)
            if v.get("confidence") or v.get("source"):
                elements.append(Paragraph(
                    f"Confidence: {v.get('confidence', '')} | Source: {cite(v.get('source', ''))}", cite_marker_s))

    for topic_key, topic_heading in (
        ("structural_substrate_categories", "Real structural VT substrate categories:"),
        ("primary_electrical_disease_channelopathies", "Real primary electrical disease / channelopathies:"),
        ("clinical_presentation", "Real clinical presentation:"),
        ("epidemiology_scd", "Real sudden cardiac death epidemiology:"),
        ("diagnostic_tools", "Real diagnostic tools:"),
        ("pathophysiology_mechanisms", "Real pathophysiology -- mechanisms of pleural fluid accumulation:"),
        ("classification_transudate_vs_exudate_lights_criteria", "Real classification -- Transudate vs Exudate, Light's Criteria:"),
        ("parapneumonic_effusion_empyema_staging", "Real ACCP staging -- parapneumonic effusion to empyema:"),
        ("specific_fluid_analysis_markers", "Real specific pleural fluid analysis markers:"),
    ):
        tobj = sym.get(topic_key)
        if not tobj:
            continue
        elements.append(Paragraph(topic_heading, subhead))
        if isinstance(tobj, dict):
            if tobj.get("note"):
                elements.append(Paragraph(tobj["note"], body))
            for k, v in tobj.items():
                if k == "note":
                    continue
                elements.append(Paragraph(k.replace("_", " ").title() + ":", body))
                render_med_topic(v, depth=1)
        elements.append(Spacer(1, 4))

    CORE_LABELS = {
        "core": "Core / common symptoms:",
        "core_pediatric_rickets": "Core symptoms — Paediatric (Rickets):",
        "core_adult_osteomalacia": "Core symptoms — Adult (Osteomalacia):",
        "core_by_acs_type": "Core symptoms by type:",
        "core_by_laterality": "Core symptoms by laterality:",
        "core_triad": "Core symptom triad:",
        "core_presentation": "Core presentation:",
        "core_presentation_hypothyroidism": "Core presentation -- Hypothyroidism:",
        "core_presentation_hyperthyroidism": "Core presentation -- Hyperthyroidism (incl. Graves' Disease):",
    }
    for key, label in CORE_LABELS.items():
        if sym.get(key) and isinstance(sym[key], list):
            elements.append(Paragraph(label, subhead))
            add_bullets([f"{s['name']}" + (f" — {s['note']}" if s.get("note") else "") for s in sym[key]])
        elif sym.get(key) and isinstance(sym[key], dict):
            # Dict-shaped variant (e.g. diabetes_mellitus core_presentation: {classic_symptoms: [...], source, confidence})
            cp = sym[key]
            elements.append(Paragraph(label, subhead))
            if cp.get("note"):
                elements.append(Paragraph(cp["note"], body))
            cs = cp.get("classic_symptoms")
            if isinstance(cs, list):
                for s in cs:
                    if isinstance(s, dict):
                        elements.append(Paragraph(f"• <b>{s.get('name', '')}:</b> {s.get('note', '')}", bullet))
                    elif isinstance(s, str):
                        elements.append(Paragraph(f"• {s}", bullet))
            for ck, cv in cp.items():
                if ck in ("classic_symptoms", "note", "source", "confidence"):
                    continue
                if isinstance(cv, str):
                    elements.append(Paragraph(f"• <b>{ck.replace('_', ' ').title()}:</b> {cv}", bullet))
                elif isinstance(cv, dict):
                    # Nested sub-topic dict (e.g. dyslipidemia's core_presentation:
                    # {usually_asymptomatic: {...}, physical_signs_in_severe_or_genetic_cases: {...}})
                    elements.append(Paragraph(ck.replace('_', ' ').title() + ":", body))
                    for sk, sv in cv.items():
                        if sk in ("source", "confidence") or not isinstance(sv, str):
                            continue
                        elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {sv}", bullet))
                    if cv.get("source"):
                        elements.append(Paragraph(
                            f"Confidence: {cv.get('confidence', '')} | Source: {cite(cv['source'])}", cite_marker_s))
            if cp.get("source"):
                elements.append(Paragraph(f"Confidence: {cp.get('confidence', '')} | Source: {cite(cp['source'])}", cite_marker_s))

    _GENERIC_TEXT_KEYS = ("definition", "detail", "criteria", "meaning", "finding", "variables",
                          "strata_and_prognosis", "validation_data", "global_prevalence_incidence",
                          "proportion")

    def render_generic_kv(k, v, depth=0):
        # Flexible fallback renderer for arbitrary nested classification/tool dicts
        # (e.g. WHO 5-group classification, risk-stratification tool objects) that
        # do not match any of the more specific shapes handled elsewhere in this file.
        if isinstance(v, str):
            elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
            return
        if isinstance(v, list):
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead if depth == 0 else body))
            for item in v:
                if isinstance(item, dict):
                    label_v = (item.get("class") or item.get("name") or item.get("gene") or item.get("factor")
                               or item.get("stage") or item.get("medication_class") or "")
                    detail_v = (item.get("definition") or item.get("detail") or item.get("finding")
                                or item.get("criteria") or item.get("description") or item.get("mechanism") or "")
                    if label_v and detail_v:
                        elements.append(Paragraph(f"• <b>{label_v}:</b> {detail_v}", bullet))
                    elif detail_v:
                        elements.append(Paragraph(f"• {detail_v}", bullet))
                    if item.get("source"):
                        elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
                elif isinstance(item, str):
                    elements.append(Paragraph(f"• {item}", bullet))
            return
        if isinstance(v, dict):
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead if depth == 0 else body))
            if v.get("note"):
                elements.append(Paragraph(v["note"], body))
            for tk in _GENERIC_TEXT_KEYS:
                if isinstance(v.get(tk), str):
                    elements.append(Paragraph(f"<b>{tk.replace('_', ' ').title()}:</b> {v[tk]}", body))
            for subk, subv in v.items():
                if subk in ("note", "source", "confidence") or subk in _GENERIC_TEXT_KEYS:
                    continue
                render_generic_kv(subk, subv, depth=depth + 1)
            if v.get("confidence") or v.get("source"):
                elements.append(Paragraph(
                    f"Confidence: {v.get('confidence', '')} | Source: {cite(v.get('source', ''))}", cite_marker_s))

    if isinstance(sym.get("diagnostic_criteria_ada"), dict):
        dca = sym["diagnostic_criteria_ada"]
        elements.append(Paragraph("Real ADA diagnostic criteria (diabetes & prediabetes thresholds):", subhead))
        if dca.get("diabetes_thresholds"):
            elements.append(Paragraph("Diabetes diagnostic thresholds:", body))
            for t in dca["diabetes_thresholds"]:
                line = f"• <b>{t.get('test', '')}:</b> {t.get('threshold', '')}"
                if t.get("note"):
                    line += f" — {t['note']}"
                elements.append(Paragraph(line, bullet))
        if dca.get("confirmation_rule"):
            elements.append(Paragraph(f"<b>Confirmation rule:</b> {dca['confirmation_rule']}", body))
        if dca.get("prediabetes_thresholds"):
            elements.append(Paragraph("Prediabetes diagnostic thresholds:", body))
            for t in dca["prediabetes_thresholds"]:
                line = f"• <b>{t.get('test', '')}:</b> {t.get('threshold', '')}"
                if t.get("note"):
                    line += f" — {t['note']}"
                elements.append(Paragraph(line, bullet))
        if dca.get("source"):
            elements.append(Paragraph(f"Confidence: {dca.get('confidence', '')} | Source: {cite(dca['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("acute_complications"), dict):
        acu = sym["acute_complications"]
        elements.append(Paragraph("Real acute complications (DKA, HHS, severe hypoglycaemia):", subhead))
        for ak, aheading in (("dka", "Diabetic Ketoacidosis (DKA):"),
                              ("hhs", "Hyperosmolar Hyperglycaemic State (HHS):"),
                              ("severe_hypoglycemia", "Severe Hypoglycaemia:")):
            ablock = acu.get(ak)
            if not isinstance(ablock, dict):
                continue
            elements.append(Paragraph(aheading, body))
            for fk, flabel in (("full_name", "Also known as"), ("more_common_in", "More common in"),
                                ("diagnostic_criteria", "Diagnostic criteria"), ("definition", "Definition"),
                                ("glucose_thresholds", "Glucose thresholds"),
                                ("diagnostic_framework", "Diagnostic framework"),
                                ("mortality", "Mortality"), ("mortality_contrast", "Mortality contrast")):
                if ablock.get(fk):
                    elements.append(Paragraph(f"• <b>{flabel}:</b> {ablock[fk]}", bullet))
            if isinstance(ablock.get("severity_grading"), list):
                elements.append(Paragraph("Severity grading:", small_grey))
                for g in ablock["severity_grading"]:
                    if isinstance(g, dict):
                        elements.append(Paragraph(
                            f"• <b>{g.get('grade', '')}:</b> pH {g.get('ph', '')}, bicarbonate {g.get('bicarbonate', '')}, anion gap {g.get('anion_gap', '')}",
                            bullet))
            if ablock.get("source"):
                elements.append(Paragraph(f"Confidence: {ablock.get('confidence', '')} | Source: {cite(ablock['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("chronic_microvascular_complications"), dict):
        elements.append(Paragraph("Real chronic microvascular complications:", subhead))
        for k, v in sym["chronic_microvascular_complications"].items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("chronic_macrovascular_complications"), dict):
        cmac = sym["chronic_macrovascular_complications"]
        elements.append(Paragraph("Real chronic macrovascular complications:", subhead))
        if cmac.get("note"):
            elements.append(Paragraph(cmac["note"], body))
        for k, v in cmac.items():
            if k == "note":
                continue
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("monitoring_tools"), dict):
        elements.append(Paragraph("Real monitoring tools:", subhead))
        for k, v in sym["monitoring_tools"].items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("cardiac_manifestations"), dict):
        elements.append(Paragraph("Real cardiac manifestations (thyroid-heart interactions):", subhead))
        for k, v in sym["cardiac_manifestations"].items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if (isinstance(sym.get("epidemiology"), dict) and isinstance(sym["epidemiology"].get("global"), list)
            and isinstance(sym["epidemiology"].get("india"), list)):
        epi_thy = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global & India):", subhead))
        for item in epi_thy["global"]:
            if not isinstance(item, dict):
                continue
            elements.append(Paragraph(f"<b>Global:</b> {item.get('finding', '')}", body))
            if item.get("source"):
                elements.append(Paragraph(f"Confidence: {item.get('confidence', '')} | Source: {cite(item['source'])}", cite_marker_s))
        for item in epi_thy["india"]:
            if not isinstance(item, dict):
                continue
            elements.append(Paragraph(f"• <b>{item.get('region', '')}:</b> {item.get('finding', '')}", bullet))
            if item.get("source"):
                elements.append(Paragraph(f"Confidence: {item.get('confidence', '')} | Source: {cite(item['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if (isinstance(sym.get("epidemiology"), dict) and isinstance(sym["epidemiology"].get("global"), dict)
            and isinstance(sym["epidemiology"].get("india"), list)):
        epi_dm = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global & India):", subhead))
        g = epi_dm["global"]
        if g.get("finding"):
            elements.append(Paragraph(f"<b>Global:</b> {g['finding']}", body))
        if g.get("source"):
            elements.append(Paragraph(f"Confidence: {g.get('confidence', '')} | Source: {cite(g['source'])}", cite_marker_s))
        for item in epi_dm["india"]:
            if not isinstance(item, dict):
                continue
            label = item.get("region") or item.get("study") or ""
            finding = item.get("finding", "")
            if label or finding:
                elements.append(Paragraph(f"• <b>{label}:</b> {finding}" if label else f"• {finding}", bullet))
            if item.get("note"):
                elements.append(Paragraph(item["note"], small_grey))
            if item.get("source"):
                elements.append(Paragraph(f"Confidence: {item.get('confidence', '')} | Source: {cite(item['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    for gkey, gheading in (
        ("hemodynamic_diagnostic_definition", "Real haemodynamic diagnostic definition:"),
        ("who_group_classification", "Real WHO 5-group clinical classification:"),
        ("functional_classification", "Real WHO Functional Class:"),
        ("diagnostic_delay_and_pathway", "Real diagnostic delay and diagnostic pathway:"),
        ("risk_stratification_tools", "Real risk-stratification tools:"),
        ("gold_definition_and_diagnosis", "Real GOLD definition and diagnostic criteria:"),
        ("gold_abe_classification", "Real GOLD ABE assessment/treatment-group classification:"),
        ("phenotype_classification", "Real COPD phenotype classification (chronic bronchitis vs emphysema vs ACO):"),
        ("classic_clinical_phenotypes_pink_puffer_blue_bloater", "Classic clinical phenotypes -- Pink Puffer vs Blue Bloater (historical, with modern caveat):"),
        ("comorbidities_systemic_effects", "Real systemic effects and comorbidities of COPD:"),
        ("gina_definition_and_pathophysiology", "Real GINA definition and pathophysiology:"),
        ("inflammatory_mechanism_type2_vs_non_type2", "Real inflammatory mechanism -- Type-2 vs Non-Type-2 asthma:"),
        ("diagnostic_criteria", "Real diagnostic criteria:"),
        ("phenotype_endotype_classification", "Real phenotype / endotype classification:"),
        ("gina_severity_and_control_classification", "Real GINA severity vs control classification:"),
        ("classic_symptoms", "Real classic symptoms and circadian pattern:"),
        ("exacerbation_classification", "Real exacerbation severity classification (GINA / BTS-SIGN):"),
        ("histologic_classification", "Real histologic classification -- NSCLC subtypes and SCLC biology:"),
        ("molecular_biomarker_landscape", "Real molecular/biomarker landscape (KRAS, EGFR, ALK, ROS1, BRAF, MET, RET, NTRK, PD-L1 TPS):"),
        ("tnm_staging", "Real TNM staging (9th edition, AJCC/UICC):"),
        ("paraneoplastic_syndromes", "Real paraneoplastic syndromes:"),
        ("local_regional_complications", "Real local-regional complications (SVC syndrome, Pancoast tumour, nerve palsies):"),
        ("screening", "Real screening -- NLST and USPSTF 2021 criteria:"),
        ("classification_by_aetiology", "Real classification by aetiology -- PSP, SSP, Traumatic, Iatrogenic, Tension, Catamenial:"),
        ("tension_pneumothorax_specific_presentation", "Real tension pneumothorax -- specific presentation (obstructive shock physiology):"),
        ("diagnostic_approach", "Real diagnostic approach -- Chest X-ray, Point-of-Care Ultrasound, CT:"),
        ("size_classification_severity_grading", "Real size classification / severity grading (BTS vs ACCP criteria):"),
        ("natural_history_recurrence", "Real natural history and recurrence risk:"),
        ("classification_primary_genetic_vs_secondary", "Real classification -- Primary Genetic vs Secondary Dyslipidemia:"),
        ("lipid_panel_components_and_clinical_significance", "Real lipid panel components and clinical significance:"),
        ("diagnostic_criteria_and_screening", "Real diagnostic criteria and screening intervals:"),
    ):
        if gkey == "phenotype_classification" and disease_id == "pcos":
            # PCOS's own phenotype_classification (Rotterdam Phenotypes A-D) is unrelated to
            # COPD's chronic-bronchitis/emphysema/ACO phenotypes that this heading describes -
            # rendered separately below with its own correct heading instead.
            continue
        if gkey == "classic_symptoms" and disease_id == "viral_hepatitis":
            # Viral hepatitis' classic_symptoms (chronic-vs-acute presentation) is unrelated to
            # GINA asthma's "circadian pattern" heading this loop uses for the same key name -
            # rendered separately above (Viral Hepatitis-specific structured blocks) instead.
            continue
        if gkey == "classic_symptoms" and disease_id == "peptic_ulcer_disease":
            # PUD's classic_symptoms (epigastric pain meal-timing pattern, silent ulcers) is
            # unrelated to GINA asthma's "circadian pattern" heading this loop uses for the same
            # key name -- rendered separately above (Peptic Ulcer Disease-specific block) instead.
            continue
        if gkey == "classic_symptoms" and disease_id == "inflammatory_bowel_disease":
            # IBD's classic_symptoms (Crohn's vs UC presentation) is unrelated to GINA asthma's
            # "circadian pattern" heading this loop uses for the same key name -- rendered separately
            # above (Inflammatory Bowel Disease-specific block) instead.
            continue
        if gkey == "classic_symptoms" and disease_id == "gerd":
            # GERD's classic_symptoms (heartburn/regurgitation, dysphagia red flag, atypical/
            # extraesophageal manifestations) is unrelated to GINA asthma's "circadian pattern"
            # heading this loop uses for the same key name -- rendered separately above (GERD-specific
            # structured block) instead.
            continue
        if gkey == "classic_symptoms" and disease_id == "acute_pancreatitis":
            # Acute pancreatitis' classic_symptoms (epigastric pain pattern, Cullen's/Grey Turner's
            # signs) is unrelated to GINA asthma's "circadian pattern" heading this loop uses for the
            # same key name -- rendered separately above (Acute Pancreatitis-specific structured block)
            # instead.
            continue
        if gkey == "classic_symptoms" and disease_id == "celiac_disease":
            # Celiac disease's classic_symptoms (classic GI presentation vs non-classic extraintestinal
            # presentation) is unrelated to GINA asthma's "circadian pattern" heading this loop uses for
            # the same key name -- rendered separately above (Celiac Disease-specific structured block)
            # instead.
            continue
        if gkey == "classic_symptoms" and disease_id == "myasthenia_gravis":
            # Myasthenia gravis' classic_symptoms (core fatigable-weakness feature, ocular/bulbar/limb-
            # axial/respiratory involvement) is unrelated to GINA asthma's "circadian pattern" heading
            # this loop uses for the same key name -- rendered separately below (Myasthenia Gravis-
            # specific structured block) instead.
            continue
        gobj = sym.get(gkey)
        if not gobj or not isinstance(gobj, dict):
            # e.g. bronchiectasis' classic_symptoms is a list, not a dict -- handled separately below
            continue
        elements.append(Paragraph(gheading, subhead))
        if gobj.get("note"):
            elements.append(Paragraph(gobj["note"], body))
        for k, v in gobj.items():
            if k in ("note", "source", "confidence"):
                continue
            render_generic_kv(k, v)
        if gobj.get("source"):
            elements.append(Paragraph(f"Source: {cite(gobj['source'])}", cite_marker_s))

    if isinstance(sym.get("classic_symptoms"), list):
        elements.append(Paragraph("Real classic symptoms:", subhead))
        for item in sym["classic_symptoms"]:
            if not isinstance(item, dict):
                continue
            elements.append(Paragraph(f"• <b>{item.get('name', '')}:</b> {item.get('note', '')}", bullet))
            if item.get("source"):
                elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("pathophysiology_vicious_cycle_vortex"), dict):
        elements.append(Paragraph("Real pathophysiology — vicious cycle / vortex model:", subhead))
        for k, v in sym["pathophysiology_vicious_cycle_vortex"].items():
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(f"<b>{k.replace('_', ' ').title()}:</b> {v.get('concept', '')}", body))
            if v.get("source"):
                elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("diagnostic_criteria_HRCT"), dict):
        dhc = sym["diagnostic_criteria_HRCT"]
        elements.append(Paragraph("Real diagnostic criteria — HRCT:", subhead))
        if dhc.get("gold_standard"):
            elements.append(Paragraph(dhc["gold_standard"], body))
        if isinstance(dhc.get("original_naidich_criteria_1982"), list):
            add_bullets(dhc["original_naidich_criteria_1982"])
        if dhc.get("source"):
            elements.append(Paragraph(f"Confidence: {dhc.get('confidence', '')} | Source: {cite(dhc['source'])}", cite_marker_s))
        if dhc.get("modern_refinement_note"):
            elements.append(Paragraph(dhc["modern_refinement_note"], body))
        if dhc.get("source_2"):
            elements.append(Paragraph(f"Confidence: {dhc.get('confidence_2', '')} | Source: {cite(dhc['source_2'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("severity_prognostic_scoring_tools"), dict):
        spt = sym["severity_prognostic_scoring_tools"]
        elements.append(Paragraph("Real severity/prognostic scoring tools:", subhead))
        for k, v in spt.items():
            if k in ("comparative_note", "source", "confidence") or not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            if isinstance(v.get("components_and_points"), list):
                add_bullets(v["components_and_points"])
            if v.get("components"):
                elements.append(Paragraph(v["components"], body))
            if v.get("note"):
                elements.append(Paragraph(v["note"], body))
            if v.get("validation_data"):
                elements.append(Paragraph(v["validation_data"], body))
            if v.get("source"):
                elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v['source'])}", cite_marker_s))
        if spt.get("comparative_note"):
            elements.append(Paragraph(spt["comparative_note"], body))
        if spt.get("source"):
            elements.append(Paragraph(f"Confidence: {spt.get('confidence', '')} | Source: {cite(spt['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("microbiology"), dict):
        elements.append(Paragraph("Real microbiology:", subhead))
        for k, v in sym["microbiology"].items():
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v.get('detail', '')}", bullet))
            if v.get("source"):
                elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("exacerbation_definition"), dict):
        edf = sym["exacerbation_definition"]
        elements.append(Paragraph("Real exacerbation definition:", subhead))
        if edf.get("consensus_definition"):
            elements.append(Paragraph(edf["consensus_definition"], body))
        if edf.get("source"):
            elements.append(Paragraph(f"Confidence: {edf.get('confidence', '')} | Source: {cite(edf['source'])}", cite_marker_s))
        fep = edf.get("frequent_exacerbator_phenotype")
        if isinstance(fep, dict):
            elements.append(Paragraph("Frequent-exacerbator phenotype:", subhead))
            if fep.get("definition"):
                elements.append(Paragraph(fep["definition"], body))
            if fep.get("prognostic_significance"):
                elements.append(Paragraph(fep["prognostic_significance"], body))
            if fep.get("source"):
                elements.append(Paragraph(f"Source: {cite(fep['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if (disease_id not in ("epilepsy", "gout", "rheumatoid_arthritis") and isinstance(sym.get("epidemiology"), dict)
            and "global" in sym["epidemiology"] and "india_specific" in sym["epidemiology"]):
        # epilepsy is fully rendered (including its extra india_treatment_gap key) by the
        # disease_id == "epilepsy" block above -- excluded here to avoid a silent partial-drop
        # duplicate render of just "global"/"india_specific" with india_treatment_gap missing.
        epi8 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global & India-specific):", subhead))
        for k in ("global", "india_specific"):
            ev = epi8.get(k, {})
            if not isinstance(ev, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            # "findings" (plural, e.g. bronchiectasis) or "finding" (singular, e.g. stroke) --
            # without this fallback the singular-keyed variant is silently dropped.
            finding_text = ev.get("findings") or ev.get("finding")
            if finding_text:
                elements.append(Paragraph(finding_text, body))
            if ev.get("source"):
                elements.append(Paragraph(f"Confidence: {ev.get('confidence', '')} | Source: {cite(ev['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if isinstance(sym.get("epidemiology"), dict) and (
        "global_GLOBOCAN_2022" in sym["epidemiology"] or "india_epidemiology" in sym["epidemiology"]):
        epi9 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (GLOBOCAN 2022 & India NCRP-specific):", subhead))
        for k, v in epi9.items():
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            if v.get("findings"):
                elements.append(Paragraph(v["findings"], body))
            if v.get("source"):
                elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    specific_key = "specific_signs" if "specific_signs" in sym else "specific_diagnostic_signs"
    sds = sym.get(specific_key)

    def render_sign_item(s):
        if not isinstance(s, dict):
            return
        conf = f" [confidence: {s['confidence']}]" if s.get("confidence") else ""
        note = s.get("note") or s.get("mechanism") or ""
        note_str = f" — {note}" if note else ""
        elements.append(Paragraph(f"• {s.get('name', '')}{note_str}{conf}", bullet))
        if s.get("source"):
            elements.append(Paragraph(f"Source: {cite(s['source'])}", cite_marker_s))

    if sds:
        elements.append(Paragraph("Specific / clinical signs:", subhead))
        if isinstance(sds, list):
            for s in sds:
                render_sign_item(s)
        elif isinstance(sds, dict):
            # Grouped shape (e.g. auscultation / peripheral_signs_of_chronic_severe_AR / other_findings)
            for group_key, group_val in sds.items():
                elements.append(Paragraph(group_key.replace('_', ' ').title() + ":", subhead))
                if isinstance(group_val, list):
                    for s in group_val:
                        render_sign_item(s)
                elif isinstance(group_val, dict):
                    if group_val.get("note"):
                        elements.append(Paragraph(group_val["note"], body))
                    for s in group_val.get("signs", []):
                        render_sign_item(s)

    if sym.get("risk_scoring_tools"):
        elements.append(Paragraph("Real risk-scoring tools:", subhead))
        for rt in sym["risk_scoring_tools"]:
            # Defensive: not every tool entry has "criteria" (e.g. stroke's NIHSS/CHA2DS2-VASc
            # cross-reference entries only carry "name"/"note"/"source") -- fall back to "note"
            # rather than KeyError, which would otherwise crash PDF generation for that disease.
            detail = rt.get("criteria") or rt.get("note") or ""
            elements.append(Paragraph(f"• <b>{rt['name']}:</b> {detail}", bullet))
            conf = rt.get("confidence", "")
            src = rt.get("source", "")
            if conf or src:
                elements.append(Paragraph(f"Confidence: {conf} | Source: {cite(src)}", cite_marker_s))

    if sym.get("real_classification"):
        rc = sym["real_classification"]
        elements.append(Paragraph("Real classification:", subhead))
        for k, v in rc.items():
            elements.append(Paragraph(f"• <b>{k.replace('_',' ')}:</b> {v}", bullet))

    if sym.get("classification") and disease_id != "antiphospholipid_syndrome":
        # antiphospholipid_syndrome's classification is {summary, findings (list of str),
        # citations (list of str)} -- this generic loop below only renders string- or
        # dict-valued top-level keys as bullets/sub-sections, so a list-valued "findings"/
        # "citations" key would be silently skipped (continue). Rendered instead, correctly
        # and in full, by the antiphospholipid_syndrome-specific block further below.
        cl = sym["classification"]
        elements.append(Paragraph("Real classification:", subhead))
        if isinstance(cl, str):
            elements.append(Paragraph(cl, body))
            cl = {}
        if cl.get("note"):
            elements.append(Paragraph(cl["note"], body))
        for k, v in cl.items():
            if k == "note":
                continue
            if isinstance(v, str):
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
                continue
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            if v.get("definition"):
                elements.append(Paragraph(v["definition"], body))
            for sk, sv in v.items():
                if sk in ("definition", "source") or not isinstance(sv, str):
                    continue
                elements.append(Paragraph(f"• <b>{sk.replace('_', ' ')}:</b> {sv}", bullet))
            if v.get("epidemiology"):
                elements.append(Paragraph(v["epidemiology"], body))
            for sk, sv in v.items():
                if sk in ("definition", "source", "epidemiology") or not isinstance(sv, dict):
                    continue
                elements.append(Paragraph(sk.replace('_', ' ').title() + ":", subhead))
                for esk, esv in sv.items():
                    if esk == "source" or not isinstance(esv, str):
                        continue
                    elements.append(Paragraph(f"• <b>{esk.replace('_', ' ')}:</b> {esv}", bullet))
                if sv.get("source"):
                    elements.append(Paragraph(f"Source: {cite(sv['source'])}", cite_marker_s))
            if v.get("source"):
                elements.append(Paragraph(f"Source: {cite(v['source'])}", cite_marker_s))

    if sym.get("diagnostic_criteria_acute_pericarditis"):
        dc = sym["diagnostic_criteria_acute_pericarditis"]
        elements.append(Paragraph("Real diagnostic criteria — Acute Pericarditis (ESC 2015):", subhead))
        if dc.get("note"):
            elements.append(Paragraph(dc["note"], body))
        for c in dc.get("criteria", []):
            elements.append(Paragraph(f"• {c['item']} — prevalence: {c['prevalence']}", bullet))
        if dc.get("supporting_findings"):
            elements.append(Paragraph(dc["supporting_findings"], body))
        if dc.get("source"):
            elements.append(Paragraph(f"Source: {cite(dc['source'])}", cite_marker_s))

    def render_flat_dict_section(key, heading):
        obj = sym.get(key)
        if not obj:
            return
        elements.append(Paragraph(heading, subhead))
        if isinstance(obj, str):
            elements.append(Paragraph(obj, body))
            return
        if obj.get("note"):
            elements.append(Paragraph(obj["note"], body))
        source_lines = []
        for k, v in obj.items():
            if k == "note" or not isinstance(v, str):
                continue
            if k == "confidence" or k.startswith("source"):
                if k != "confidence":
                    source_lines.append(v)
                continue
            elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
        if obj.get("confidence") or source_lines:
            src = "; ".join(source_lines)
            elements.append(Paragraph(f"Confidence: {obj.get('confidence', '')} | Source: {cite(src)}", cite_marker_s))

    render_flat_dict_section("ecg_findings", "Real ECG findings:")
    render_flat_dict_section("cardiac_tamponade_presentation", "Real cardiac tamponade presentation:")
    render_flat_dict_section("constrictive_pericarditis_presentation", "Real constrictive pericarditis presentation:")
    render_flat_dict_section("classification_cap_hap_vap", "Real classification -- CAP vs HAP vs VAP (and retirement of HCAP):")
    render_flat_dict_section("mdr_risk_factors_hap_vap", "Real MDR-organism risk factors -- HAP/VAP:")
    render_flat_dict_section("classic_symptoms_typical_vs_atypical", "Real classic symptom pattern -- Typical vs Atypical pneumonia:")
    render_flat_dict_section("pathophysiology_natural_history", "Real pathophysiology and natural history:")
    render_flat_dict_section("drug_resistant_tb_classification", "Real drug-resistant TB classification (MDR / pre-XDR / XDR):")
    # guillain_barre_syndrome's natural_history_and_prognosis is a dict of {finding, source, confidence}
    # topic dicts (same nested shape as its definition_and_pathophysiology/diagnostic_framework), not
    # the flat string-valued shape every other disease using this key has -- render_flat_dict_section
    # only prints string-valued fields, so calling it here would print an empty heading with no body.
    # It is rendered instead in the guillain_barre_syndrome-specific block below.
    if disease_id != "guillain_barre_syndrome":
        render_flat_dict_section("natural_history_and_prognosis", "Real natural history and prognosis:")
    render_flat_dict_section("progressive_pulmonary_fibrosis_ppf", "Real progressive pulmonary fibrosis (PPF) construct:")
    render_flat_dict_section("acute_exacerbation_of_ipf", "Real acute exacerbation of IPF (AE-IPF):")
    render_flat_dict_section("real_definition_diagnostic_criteria_berlin", "Real Berlin Definition -- diagnostic criteria:")
    render_flat_dict_section("severity_classification_and_mortality_berlin", "Real Berlin Definition -- severity classification and mortality:")
    render_flat_dict_section("real_2023_2024_global_definition_update", "Real 2023/2024 New Global Definition of ARDS -- what changed:")
    render_flat_dict_section("pathophysiology_three_phase_model", "Real pathophysiology -- three-phase model (exudative/proliferative/fibrotic):")
    render_flat_dict_section("classic_clinical_presentation", "Real classic clinical presentation:")
    render_flat_dict_section("covid19_ards_data", "Real COVID-19 ARDS data:")
    render_flat_dict_section("natural_history_and_long_term_prognosis", "Real natural history and long-term prognosis (post-ICU syndrome):")
    render_flat_dict_section("cardiovascular_linkage", "Real cardiovascular risk linkage (CKD as an independent cardiovascular risk multiplier):")
    render_flat_dict_section("risk_factor_source_citations", "Real risk-factor source citations (per-claim):")
    render_flat_dict_section("risk_factors_beyond_etiology", "Real risk factors (beyond primary etiology):")
    if disease_id not in ("thyroid_disorders", "chronic_kidney_disease", "obesity_metabolic_syndrome", "dyslipidemia", "pcos", "peptic_ulcer_disease", "inflammatory_bowel_disease", "gerd", "acute_pancreatitis", "stroke", "epilepsy", "parkinsons_disease", "alzheimers_disease", "multiple_sclerosis", "migraine", "myasthenia_gravis", "amyotrophic_lateral_sclerosis", "gout", "rheumatoid_arthritis"):
        # stroke's and alzheimers_disease's epidemiology (global/india_specific, nested dicts) are
        # already fully rendered above by the disease-agnostic "global"+"india_specific" handler --
        # this flat-string-valued fallback would otherwise print an empty duplicate "Real epidemiology:"
        # heading with no content under it. multiple_sclerosis's epidemiology matches that same
        # "global"+"india_specific" handler too. migraine's epidemiology uses "global_burden"/
        # "india_specific" keys (neither the "global"/"india_specific" pair above nor the
        # "global_burden"/"india_specific_data" pair the PUD/IBD/GERD-style branches require), so it
        # matches NO generic handler and is rendered explicitly in the disease_id=="migraine" block
        # instead -- without this exclusion it would fall through to this flat-dict fallback and print
        # an empty/malformed duplicate "Real epidemiology:" heading. myasthenia_gravis's epidemiology
        # (global_burden/india_specific_data, both nested dicts) is already fully rendered above by the
        # Myasthenia Gravis-specific structured block, and would otherwise print the same empty duplicate
        # "Real epidemiology:" heading with no content under it. amyotrophic_lateral_sclerosis's
        # epidemiology (global_incidence_prevalence/regional_and_ethnic_variation/india_specific, each a
        # nested {finding, source, confidence} dict) is rendered in its own block below for the same reason.
        render_flat_dict_section("epidemiology", "Real epidemiology:")
    if disease_id == "dyslipidemia" and isinstance(sym.get("epidemiology"), dict):
        elements.append(Paragraph("Real epidemiology (India ICMR-INDIAB & South Asian lipid pattern):", subhead))
        for epi_k, epi_v in sym["epidemiology"].items():
            render_generic_kv(epi_k, epi_v)
        elements.append(Spacer(1, 4))
    if disease_id == "pcos" and isinstance(sym.get("epidemiology"), dict):
        elements.append(Paragraph("Real epidemiology (global, by diagnostic criteria, & India):", subhead))
        for epi_k, epi_v in sym["epidemiology"].items():
            render_generic_kv(epi_k, epi_v)
        elements.append(Spacer(1, 4))

    for osa_key, osa_heading in (
        ("gold_definition_and_pathophysiology", "Real definition and pathophysiology (mechanism):"),
        ("distinction_from_central_sleep_apnea", "Real distinction from Central Sleep Apnea:"),
        ("diagnostic_framework", "Real diagnostic framework -- polysomnography, AHI severity classification, home sleep apnea testing:"),
        ("screening_and_prediction_tools", "Real screening and prediction tools -- STOP-BANG questionnaire, Epworth Sleepiness Scale:"),
        ("classic_clinical_features", "Real classic clinical features:"),
        ("real_risk_factors", "Real risk factors:"),
        ("cardiovascular_and_metabolic_consequences", "Real cardiovascular and metabolic consequences:"),
        ("natural_history", "Real natural history -- untreated severe OSA mortality:"),
    ) if disease_id == "obstructive_sleep_apnea" else ():
        osa_tobj = sym.get(osa_key)
        if not osa_tobj:
            continue
        elements.append(Paragraph(osa_heading, subhead))
        if isinstance(osa_tobj, dict):
            if osa_tobj.get("definition"):
                elements.append(Paragraph(osa_tobj["definition"], body))
            if osa_tobj.get("mechanism"):
                elements.append(Paragraph(f"<b>Mechanism:</b> {osa_tobj['mechanism']}", body))
            if osa_tobj.get("note"):
                elements.append(Paragraph(osa_tobj["note"], body))
            for osk, osv in osa_tobj.items():
                if osk in ("definition", "mechanism", "note", "source", "confidence"):
                    continue
                if isinstance(osv, str):
                    elements.append(Paragraph(f"• <b>{osk.replace('_', ' ').title()}:</b> {osv}", bullet))
                else:
                    elements.append(Paragraph(osk.replace('_', ' ').title() + ":", body))
                    render_med_topic(osv, depth=1)
            if osa_tobj.get("source") or osa_tobj.get("confidence"):
                elements.append(Paragraph(
                    f"Confidence: {osa_tobj.get('confidence', '')} | Source: {cite(osa_tobj.get('source', ''))}", cite_marker_s))
        elements.append(Spacer(1, 4))

    for gen_key, gen_heading in (
        ("real_classification_framework", "Real ILD classification framework (subtypes):"),
        ("ipf_diagnostic_framework", "Real IPF diagnostic framework (UIP/HRCT pattern, MDD):"),
        ("pulmonary_function_testing", "Real pulmonary function testing pattern:"),
    ):
        gen_obj = sym.get(gen_key)
        if not gen_obj:
            continue
        elements.append(Paragraph(gen_heading, subhead))
        if gen_obj.get("note"):
            elements.append(Paragraph(gen_obj["note"], body))
        for gk, gv in gen_obj.items():
            if gk in ("note", "source", "confidence"):
                continue
            render_generic_kv(gk, gv)
        if gen_obj.get("source"):
            elements.append(Paragraph(f"Source: {cite(gen_obj['source'])}", cite_marker_s))

    if sym.get("classification_pulmonary_vs_extrapulmonary"):
        cpe = sym["classification_pulmonary_vs_extrapulmonary"]
        elements.append(Paragraph("Real classification -- Pulmonary vs Extrapulmonary TB:", subhead))
        for k, v in cpe.items():
            if k in ("confidence",) or k.startswith("source"):
                continue
            if k == "extrapulmonary_tb_major_sites" and isinstance(v, dict):
                elements.append(Paragraph("<b>Extrapulmonary TB -- major sites:</b>", body))
                for site_k, site_v in v.items():
                    if site_k.startswith("source"):
                        continue
                    elements.append(Paragraph(f"• <b>{site_k.replace('_', ' ').title()}:</b> {site_v}", bullet))
            elif isinstance(v, str):
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
        if cpe.get("confidence"):
            elements.append(Paragraph(f"Confidence: {cpe['confidence']}", small_grey))
        elements.append(Spacer(1, 4))

    for org_epi_key, org_epi_heading in (
        ("organism_epidemiology_cap", "Real organism epidemiology -- Community-Acquired Pneumonia (CAP):"),
        ("organism_epidemiology_hap_vap", "Real organism epidemiology -- Hospital-Acquired/Ventilator-Associated Pneumonia (HAP/VAP):"),
    ):
        if sym.get(org_epi_key):
            elements.append(Paragraph(org_epi_heading, subhead))
            for o in sym[org_epi_key]:
                elements.append(Paragraph(f"• <b>{o['organism']}:</b> {o['detail']}", bullet))
                if o.get("source"):
                    elements.append(Paragraph(f"Source: {cite(o['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    if sym.get("severity_assessment_tools"):
        sat = sym["severity_assessment_tools"]
        elements.append(Paragraph("Real severity-assessment/risk-scoring tools (CURB-65, PSI/PORT, IDSA/ATS 2019 severe-CAP/ICU criteria):", subhead))
        for tool_key, tool in sat.items():
            if not isinstance(tool, dict):
                continue
            elements.append(Paragraph(tool_key.replace("_", " ").upper() + ":", body))
            for fk, fv in tool.items():
                if fk in ("source", "confidence") or not isinstance(fv, str):
                    continue
                elements.append(Paragraph(f"• <b>{fk.replace('_', ' ').title()}:</b> {fv}", bullet))
            if tool.get("source"):
                elements.append(Paragraph(f"Confidence: {tool.get('confidence', '')} | Source: {cite(tool['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("virchows_triad"):
        vt = sym["virchows_triad"]
        elements.append(Paragraph("Real mechanistic framework — Virchow's Triad:", subhead))
        if vt.get("note"):
            elements.append(Paragraph(vt["note"], body))
        for vk in ("stasis", "hypercoagulability", "endothelial_injury"):
            if vt.get(vk):
                elements.append(Paragraph(f"• <b>{vk.replace('_', ' ').title()}:</b> {vt[vk]}", bullet))
        if vt.get("clinical_honesty_note"):
            elements.append(Paragraph(f"<i>{vt['clinical_honesty_note']}</i>", small_grey))
        if vt.get("source"):
            elements.append(Paragraph(f"Source: {cite(vt['source'])}", cite_marker_s))

    if sym.get("dvt_clinical_presentation"):
        dcp = sym["dvt_clinical_presentation"]
        elements.append(Paragraph("Real DVT-specific clinical signs:", subhead))
        for k, v in dcp.items():
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            if v.get("definition"):
                elements.append(Paragraph(v["definition"], body))
            for sk in ("real_diagnostic_accuracy", "clinical_features", "real_outcome_data", "management_note"):
                if v.get(sk):
                    elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {v[sk]}", bullet))
            if v.get("confidence") or v.get("source"):
                elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v.get('source', ''))}", cite_marker_s))

    if sym.get("pe_severity_stratification"):
        pss = sym["pe_severity_stratification"]
        elements.append(Paragraph("Real PE risk-stratification (2019 ESC framework):", subhead))
        if pss.get("note"):
            elements.append(Paragraph(pss["note"], body))
        for k, v in pss.items():
            if k == "note" or not isinstance(v, dict):
                continue
            elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v.get('definition', '')}", bullet))
            if v.get("real_mortality"):
                elements.append(Paragraph(f"Real mortality: {v['real_mortality']}", small_grey))
            if v.get("note"):
                elements.append(Paragraph(v["note"], small_grey))
            if v.get("source"):
                elements.append(Paragraph(f"Source: {cite(v['source'])}", cite_marker_s))

    if sym.get("clinical_prediction_rules"):
        cpr = sym["clinical_prediction_rules"]
        elements.append(Paragraph("Real clinical prediction / risk-scoring tools:", subhead))
        if cpr.get("note"):
            elements.append(Paragraph(cpr["note"], body))
        for k, v in cpr.items():
            if k == "note" or not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').upper() + ":", subhead))
            if v.get("criteria_and_points"):
                add_bullets(v["criteria_and_points"])
            if v.get("risk_classes_and_30day_mortality"):
                elements.append(Paragraph(v["risk_classes_and_30day_mortality"], body))
            if v.get("interpretation"):
                elements.append(Paragraph(f"<b>Interpretation:</b> {v['interpretation']}", body))
            if v.get("source"):
                elements.append(Paragraph(f"Source: {cite(v['source'])}", cite_marker_s))

    if sym.get("diagnostic_pathway_d_dimer"):
        ddp = sym["diagnostic_pathway_d_dimer"]
        elements.append(Paragraph("Real diagnostic pathway — D-dimer:", subhead))
        for dk in ("note", "real_performance", "clinical_use"):
            if ddp.get(dk):
                elements.append(Paragraph(ddp[dk], body))
        if ddp.get("source"):
            elements.append(Paragraph(f"Source: {cite(ddp['source'])}", cite_marker_s))

    if sym.get("natural_history") and not sym.get("real_natural_history") and disease_id not in ("myasthenia_gravis", "amyotrophic_lateral_sclerosis", "gout", "rheumatoid_arthritis", "antiphospholipid_syndrome"):
        # antiphospholipid_syndrome's natural_history is {summary, findings (list of str),
        # citations (list of str)} -- the list-valued branch below expects each list item to
        # be a dict (e.g. {population/cohort, data/finding, source}), so plain-string findings/
        # citations would be silently skipped (continue). Rendered instead, correctly and in
        # full, by the antiphospholipid_syndrome-specific block further below.
        # myasthenia_gravis's natural_history (disease_course/modern_mortality/pregnancy_and_mg/
        # transient_neonatal_myasthenia, each a {finding, source, confidence} topic dict) is already
        # fully rendered above by the Myasthenia Gravis-specific structured block with the correct
        # "Confidence: X | Source: Y" combined line format -- this generic fallback would otherwise
        # print a literal duplicate "Real natural history:" section and drop the per-topic confidence
        # field into a bare, unlabelled bullet instead.
        nh2 = sym["natural_history"]
        elements.append(Paragraph("Real natural history:", subhead))
        if isinstance(nh2, str):
            elements.append(Paragraph(nh2, body))
            nh2 = {}
        for k, v in nh2.items():
            if isinstance(v, str):
                # Plain string entry (e.g. a cross-disease distinguishing note)
                elements.append(Paragraph(f"<b>{k.replace('_', ' ').title()}:</b> {v}", body))
                continue
            if isinstance(v, list):
                # List-of-findings shape (e.g. dilated_cardiomyopathy survival/reverse-remodeling cohorts)
                elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
                for item in v:
                    if not isinstance(item, dict):
                        continue
                    label = item.get("population") or item.get("cohort") or item.get("etiology_comparison") or ""
                    detail = item.get("data") or item.get("finding") or ""
                    if label and detail:
                        elements.append(Paragraph(f"• <b>{label}:</b> {detail}", bullet))
                    elif detail:
                        elements.append(Paragraph(f"• {detail}", bullet))
                    if item.get("source"):
                        elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
                continue
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            if v.get("definition"):
                elements.append(Paragraph(v["definition"], body))
            for sk, sv in v.items():
                if sk in ("definition", "source") or not isinstance(sv, str):
                    continue
                elements.append(Paragraph(f"• <b>{sk.replace('_', ' ')}:</b> {sv}", bullet))
            if v.get("source"):
                elements.append(Paragraph(f"Source: {cite(v['source'])}", cite_marker_s))

    if disease_id == "antiphospholipid_syndrome":
        # classification, diagnostic_framework, and natural_history are each a plain
        # {summary (str), findings (list of str), citations (list of str)} dict -- none of the
        # generic key-named handlers above render that exact shape correctly (they expect
        # dict-valued or dict-of-dict-valued sub-keys, not list-of-plain-strings), so they are
        # explicitly skipped for this disease_id above and rendered here instead via
        # render_med_topic, which already handles this shape correctly (proven by
        # clinical_presentation, which uses the same shape and renders correctly through the
        # topic_key/render_med_topic loop earlier in this function).
        for aps_key, aps_heading in (
            ("classification", "Real classification:"),
            ("diagnostic_framework", "Real diagnostic framework:"),
            ("natural_history", "Real natural history:"),
        ):
            aps_obj = sym.get(aps_key)
            if not aps_obj:
                continue
            elements.append(Paragraph(aps_heading, subhead))
            if isinstance(aps_obj, dict):
                for k, v in aps_obj.items():
                    elements.append(Paragraph(k.replace("_", " ").title() + ":", body))
                    render_med_topic(v, depth=1)
            else:
                render_med_topic(aps_obj, depth=0)
            elements.append(Spacer(1, 4))

    if sym.get("acute_vs_subacute_presentation"):
        avs = sym["acute_vs_subacute_presentation"]
        elements.append(Paragraph("Real acute vs subacute presentation:", subhead))
        if avs.get("note"):
            elements.append(Paragraph(avs["note"], body))
        if avs.get("acute"):
            elements.append(Paragraph(f"• <b>Acute:</b> {avs['acute']}", bullet))
        if avs.get("subacute"):
            elements.append(Paragraph(f"• <b>Subacute:</b> {avs['subacute']}", bullet))
        if avs.get("source"):
            elements.append(Paragraph(f"Source: {cite(avs['source'])}", cite_marker_s))

    if sym.get("organism_epidemiology"):
        elements.append(Paragraph("Real organism epidemiology:", subhead))
        for o in sym["organism_epidemiology"]:
            elements.append(Paragraph(f"• <b>{o['organism']}:</b> {o['detail']}", bullet))
            if o.get("source"):
                elements.append(Paragraph(f"Source: {cite(o['source'])}", cite_marker_s))

    if sym.get("modified_duke_criteria"):
        mdc = sym["modified_duke_criteria"]
        elements.append(Paragraph("Real diagnostic framework — Modified Duke Criteria:", subhead))
        if mdc.get("note"):
            elements.append(Paragraph(mdc["note"], body))
        if mdc.get("diagnostic_categories"):
            elements.append(Paragraph(f"<b>Diagnostic categories:</b> {mdc['diagnostic_categories']}", body))
        if mdc.get("major_criteria"):
            elements.append(Paragraph("Major criteria:", subhead))
            add_bullets(mdc["major_criteria"])
        if mdc.get("minor_criteria"):
            elements.append(Paragraph("Minor criteria:", subhead))
            add_bullets(mdc["minor_criteria"])
        if mdc.get("history"):
            elements.append(Paragraph("Real history of the criteria:", subhead))
            for h in mdc["history"]:
                elements.append(Paragraph(f"• <b>{h['version']}:</b> {h['detail']}", bullet))
                if h.get("source"):
                    elements.append(Paragraph(f"Source: {cite(h['source'])}", cite_marker_s))
        if mdc.get("source"):
            elements.append(Paragraph(f"Confidence: {mdc.get('confidence', '')} | Source: {cite(mdc['source'])}", cite_marker_s))

    if sym.get("embolic_complications"):
        ec2 = sym["embolic_complications"]
        elements.append(Paragraph("Real embolic complications:", subhead))
        if ec2.get("note"):
            elements.append(Paragraph(ec2["note"], body))
        if ec2.get("overall_incidence"):
            elements.append(Paragraph(f"<b>Overall incidence:</b> {ec2['overall_incidence']}", body))
        if ec2.get("vegetation_predictors"):
            elements.append(Paragraph(f"<b>Vegetation predictors:</b> {ec2['vegetation_predictors']}", body))
        for c in ec2.get("complications", []):
            elements.append(Paragraph(f"• <b>{c['name']}:</b> {c['data']}", bullet))
            if c.get("source"):
                elements.append(Paragraph(f"Source: {cite(c['source'])}", cite_marker_s))

    if sym.get("etiology_classification"):
        ec = sym["etiology_classification"]
        elements.append(Paragraph("Real etiology classification:", subhead))
        if ec.get("note"):
            elements.append(Paragraph(ec["note"], body))
        for k, v in ec.items():
            if k in ("note", "confidence") or k.startswith("source"):
                continue
            if isinstance(v, str):
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
                continue
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            if v.get("definition"):
                elements.append(Paragraph(v["definition"], body))
            if v.get("detail"):
                elements.append(Paragraph(v["detail"], body))
            if v.get("proportion"):
                elements.append(Paragraph(f"<b>Proportion:</b> {v['proportion']}", body))
            if v.get("subtypes"):
                elements.append(Paragraph("Subtypes:", subhead))
                for stk, stv in v["subtypes"].items():
                    if not isinstance(stv, dict):
                        continue
                    elements.append(Paragraph(f"• <b>{stk.replace('_', ' ').title()}:</b> {stv.get('definition', '')}", bullet))
                    if stv.get("source"):
                        elements.append(Paragraph(f"Source: {cite(stv['source'])}", cite_marker_s))
            if v.get("causes"):
                add_bullets(v["causes"])
            if v.get("source"):
                elements.append(Paragraph(f"Confidence: {v.get('confidence', '')} | Source: {cite(v['source'])}", cite_marker_s))
        if ec.get("source"):
            elements.append(Paragraph(f"Confidence: {ec.get('confidence', '')} | Source: {cite(ec['source'])}", cite_marker_s))

    for acute_key in ("acute_MR_presentation", "acute_AR_presentation"):
        amp = sym.get(acute_key)
        if not amp:
            continue
        elements.append(Paragraph("Acute presentation (real):", subhead))
        for k, v in amp.items():
            if k in ("source", "confidence") or not isinstance(v, str):
                continue
            elements.append(Paragraph(v, body))
        if amp.get("source"):
            elements.append(Paragraph(f"Confidence: {amp.get('confidence', '')} | Source: {cite(amp['source'])}", cite_marker_s))

    if sym.get("india_epidemiology"):
        ie = sym["india_epidemiology"]
        elements.append(Paragraph("India epidemiology (real):", subhead))
        if ie.get("note"):
            elements.append(Paragraph(ie["note"], body))
        if ie.get("findings"):
            add_bullets(ie["findings"])
        if ie.get("source"):
            elements.append(Paragraph(f"Confidence: {ie.get('confidence', '')} | Source: {cite(ie['source'])}", cite_marker_s))

    if sym.get("real_genetics"):
        rg = sym["real_genetics"]
        elements.append(Paragraph("Real genetics:", subhead))
        if isinstance(rg.get("genes"), list):
            # Gene-list shape (e.g. dilated_cardiomyopathy): one entry per gene with its own data/source
            if rg.get("prevalence_overview"):
                elements.append(Paragraph(rg["prevalence_overview"], body))
            for g in rg["genes"]:
                elements.append(Paragraph(f"• <b>{g.get('gene', '')}</b> — {g.get('proportion', '')}", bullet))
                if g.get("genotype_phenotype"):
                    elements.append(Paragraph(g["genotype_phenotype"], body))
                if g.get("source"):
                    elements.append(Paragraph(f"Confidence: {g.get('confidence', '')} | Source: {cite(g['source'])}", cite_marker_s))
        else:
            # Original flat shape
            add_bullets([f"Prevalence: {rg['prevalence']}", f"Inheritance: {rg['inheritance']}",
                         f"Genes: {rg['genes']}", f"Implication: {rg['implication']}"])
            elements.append(Paragraph(f"Confidence: {rg['confidence']} | Source: {cite(rg['source'])}", cite_marker_s))

    if sym.get("sudden_cardiac_death_risk_stratification"):
        scd = sym["sudden_cardiac_death_risk_stratification"]
        elements.append(Paragraph("Real sudden cardiac death risk stratification:", subhead))
        if scd.get("note"):
            elements.append(Paragraph(scd["note"], body))
        lrt = scd.get("lmna_risk_vta_tool")
        if lrt:
            elements.append(Paragraph(f"Real risk tool: {lrt['name']}", subhead))
            add_bullets([f"Input: {v}" for v in lrt.get("input_variables", [])])
            if lrt.get("worked_examples"):
                elements.append(Paragraph(lrt["worked_examples"], body))
            if lrt.get("icd_threshold"):
                elements.append(Paragraph(f"<b>ICD threshold:</b> {lrt['icd_threshold']}", body))
            elements.append(Paragraph(f"Confidence: {lrt.get('confidence', '')} | Source: {cite(lrt.get('source', ''))}", cite_marker_s))

    if sym.get("thromboembolism_risk"):
        ter = sym["thromboembolism_risk"]
        elements.append(Paragraph("Real thromboembolism risk:", subhead))
        elements.append(Paragraph(ter.get("finding", ""), body))
        elements.append(Paragraph(f"Confidence: {ter.get('confidence', '')} | Source: {cite(ter.get('source', ''))}", cite_marker_s))

    if sym.get("real_etiology_classification"):
        rec = sym["real_etiology_classification"]
        elements.append(Paragraph("Real etiology classification:", subhead))
        if rec.get("note"):
            elements.append(Paragraph(rec["note"], body))
        for cat in rec.get("categories", []):
            elements.append(Paragraph(f"• <b>{cat.get('name', '')}</b>", bullet))
            elements.append(Paragraph(cat.get("data", ""), body))
            elements.append(Paragraph(f"Confidence: {cat.get('confidence', '')} | Source: {cite(cat.get('source', ''))}", cite_marker_s))

    if sym.get("india_specific_epidemiology"):
        ise = sym["india_specific_epidemiology"]
        elements.append(Paragraph("India-specific epidemiology (real):", subhead))
        for k, v in ise.items():
            if k in ("confidence", "source") or not isinstance(v, str):
                continue
            elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
        if ise.get("source"):
            elements.append(Paragraph(f"Confidence: {ise.get('confidence', '')} | Source: {cite(ise['source'])}", cite_marker_s))

    if sym.get("sudden_cardiac_death_risk_tool"):
        rt = sym["sudden_cardiac_death_risk_tool"]
        elements.append(Paragraph(f"Real risk tool: {rt['name']}", subhead))
        elements.append(Paragraph(rt["note"], body))
        add_bullets([f"Input: {v}" for v in rt["input_variables"]])
        if rt.get("icd_thresholds"):
            add_bullets([f"{k.replace('_',' ')}: {v}" for k, v in rt["icd_thresholds"].items()])
        elements.append(Paragraph(f"Confidence: {rt['confidence']} | Source: {cite(rt['source'])}", cite_marker_s))

    if sym.get("real_risk_factors"):
        elements.append(Paragraph("Real risk factors:", subhead))
        rf_items = sym["real_risk_factors"]
        if isinstance(rf_items, dict):
            for k, v in rf_items.items():
                if k == "source" or not isinstance(v, str):
                    continue
                elements.append(Paragraph(f"• <b>{k.replace('_', ' ').title()}:</b> {v}", bullet))
            if rf_items.get("source"):
                elements.append(Paragraph(f"Source: {cite(rf_items['source'])}", cite_marker_s))
        elif rf_items and isinstance(rf_items[0], dict):
            for rf in rf_items:
                rf_label = rf.get("factor") or rf.get("name", "")
                rf_detail = rf.get("detail") or rf.get("note", "")
                elements.append(Paragraph(f"• <b>{rf_label}:</b> {rf_detail}", bullet))
                if rf.get("virchow_link"):
                    elements.append(Paragraph(f"Virchow's triad link: {rf['virchow_link']}", small_grey))
                if rf.get("source"):
                    elements.append(Paragraph(f"Source: {cite(rf['source'])}", cite_marker_s))
        else:
            add_bullets(rf_items)

    if sym.get("acs_spectrum_staging"):
        elements.append(Paragraph("Real acute-spectrum staging:", subhead))
        elements.append(Paragraph(sym["acs_spectrum_staging"], body))

    if sym.get("real_natural_history"):
        nh = sym["real_natural_history"]
        elements.append(Paragraph("Real natural history:", subhead))
        if "asymptomatic_latent_period" in nh:
            elements.append(Paragraph(f"Asymptomatic latent period: {nh['asymptomatic_latent_period']}", body))
            elements.append(Paragraph("Life expectancy after symptom onset (untreated): " +
                                       ", ".join(f"{k.replace('_',' ')}: {v}" for k, v in nh["life_expectancy_after_symptom_onset_untreated"].items()), body))
            elements.append(Paragraph(f"Mortality if untreated: {nh['mortality_if_untreated']}", body))
            elements.append(Paragraph(f"Confidence: {nh['confidence']} | Source: {cite(nh['source'])}", cite_marker_s))
        else:
            if nh.get("note"):
                elements.append(Paragraph(nh["note"], body))
            for key, val in nh.items():
                if key == "note" or not isinstance(val, dict):
                    continue
                if val.get("finding"):
                    elements.append(Paragraph(f"• <b>{key.replace('_', ' ')}:</b> {val['finding']}", bullet))
                elif val.get("stages"):
                    elements.append(Paragraph(key.replace('_', ' ').title() + ":", subhead))
                    if val.get("note"):
                        elements.append(Paragraph(val["note"], body))
                    elements.append(Paragraph(val["stages"], body))
                if val.get("source"):
                    elements.append(Paragraph(f"Source: {cite(val['source'])}", cite_marker_s))

    if sym.get("echo_severity_grading"):
        esg = sym["echo_severity_grading"]
        elements.append(Paragraph("Real echocardiographic severity grading:", subhead))
        if esg.get("note"):
            elements.append(Paragraph(esg["note"], body))
        grades = esg.get("grades") or esg.get("grades_primary_MR") or []
        add_bullets([f"{g['name']}: {g['criteria']}" for g in grades])
        if esg.get("secondary_MR_severe_revised_threshold"):
            rt = esg["secondary_MR_severe_revised_threshold"]
            elements.append(Paragraph(f"<b>Secondary MR revised severe threshold:</b> {rt['criteria']}", body))
            elements.append(Paragraph(rt.get("note", ""), small_grey))
            if rt.get("source"):
                elements.append(Paragraph(f"Source: {cite(rt['source'])}", cite_marker_s))
        # TR-specific 5-tier (mild/moderate/severe/massive/torrential) shape
        if esg.get("vena_contracta_width_cutoffs_cm"):
            vc = esg["vena_contracta_width_cutoffs_cm"]
            elements.append(Paragraph("Vena contracta width cutoffs (5-tier grading):", subhead))
            add_bullets([f"{k.replace('_', ' ').title()}: {v}" for k, v in vc.items()
                         if k not in ("source", "confidence") and isinstance(v, str)])
            if vc.get("source"):
                elements.append(Paragraph(f"Confidence: {vc.get('confidence', '')} | Source: {cite(vc['source'])}", cite_marker_s))
        if esg.get("supportive_qualitative_sign_of_severe_TR"):
            sq = esg["supportive_qualitative_sign_of_severe_TR"]
            elements.append(Paragraph(f"<b>Supportive sign:</b> {sq.get('finding', '')}", body))
            elements.append(Paragraph(f"Confidence: {sq.get('confidence', '')} | Source: {cite(sq.get('source', ''))}", cite_marker_s))
        if esg.get("prognostic_significance_of_the_new_grades"):
            pg = esg["prognostic_significance_of_the_new_grades"]
            elements.append(Paragraph(f"<b>Prognostic significance:</b> {pg.get('finding', '')}", body))
            if pg.get("source"):
                elements.append(Paragraph(f"Source: {cite(pg['source'])}", cite_marker_s))
        if esg.get("caveat"):
            elements.append(Paragraph(f"<i>Caveat: {esg['caveat']}</i>", small_grey))
        if esg.get("source"):
            elements.append(Paragraph(f"Source: {cite(esg['source'])}", cite_marker_s))
        if esg.get("source_for_traditional_3_tier_grading"):
            elements.append(Paragraph(f"Source (traditional 3-tier grading): {esg['source_for_traditional_3_tier_grading']}", small_grey))
        if esg.get("source_for_massive_torrential_extension"):
            elements.append(Paragraph(f"Source (massive/torrential extension): {esg['source_for_massive_torrential_extension']}", small_grey))

    if sym.get("ef_based_classification"):
        efc = sym["ef_based_classification"]
        elements.append(Paragraph("Real ejection-fraction classification:", subhead))
        add_bullets([f"{c['name']}: {c['ef']}" for c in efc["categories"]])
        elements.append(Paragraph(f"<i>{efc['note']}</i>", small_grey))

    if sym.get("staged_severity_model"):
        ssm = sym["staged_severity_model"]
        elements.append(Paragraph("Real staged severity model:", subhead))
        for st in ssm["stages"]:
            elements.append(Paragraph(
                f"• <b>Stage {st['stage']} — {st['name']}:</b> {st['criteria']} → {st['symptoms']}", bullet))
        elements.append(Paragraph(f"Source: {cite(ssm['source'])} | Confidence: {ssm['confidence']}", cite_marker_s))

    if sym.get("additional_real_findings"):
        elements.append(Paragraph("Additional real findings (population-specific / systemic):", subhead))
        for f in sym["additional_real_findings"]:
            elements.append(Paragraph(f"• <b>[{f['category']}]</b> {f['finding']}", bullet))
            elements.append(Paragraph(f"Confidence: {f['confidence']} | Source: {cite(f['source'])}", cite_marker_s))

    if sym.get("diagnostic_frameworks"):
        dfws = sym["diagnostic_frameworks"]
        elements.append(Paragraph("Real diagnostic frameworks (Takotsubo vs ACS):", subhead))
        if dfws.get("note"):
            elements.append(Paragraph(dfws["note"], body))
        its = dfws.get("intertak_diagnostic_score")
        if its:
            elements.append(Paragraph(its.get("name", "InterTAK Diagnostic Score"), subhead))
            if its.get("purpose"):
                elements.append(Paragraph(its["purpose"], body))
            for c in its.get("components_and_points", []):
                elements.append(Paragraph(f"• {c.get('variable', '')}: {c.get('points', '')} points", bullet))
            if its.get("max_score"):
                elements.append(Paragraph(f"<b>Max score:</b> {its['max_score']}", body))
            if its.get("interpretation"):
                elements.append(Paragraph(f"<b>Interpretation:</b> {its['interpretation']}", body))
            if its.get("source"):
                elements.append(Paragraph(f"Confidence: {its.get('confidence', '')} | Source: {cite(its['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))
        for extra_key in ("mayo_clinic_criteria",):
            crit = dfws.get(extra_key)
            if not crit:
                continue
            elements.append(Paragraph(crit.get("name", extra_key.replace('_', ' ').title()), subhead))
            for c in crit.get("criteria", []):
                elements.append(Paragraph(f"• {c}", bullet))
            if crit.get("note"):
                elements.append(Paragraph(crit["note"], small_grey))
            if crit.get("source"):
                elements.append(Paragraph(f"Confidence: {crit.get('confidence', '')} | Source: {cite(crit['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("ballooning_patterns"):
        bp = sym["ballooning_patterns"]
        elements.append(Paragraph("Real ballooning-pattern classification (echocardiographic/angiographic):", subhead))
        if bp.get("note"):
            elements.append(Paragraph(bp["note"], body))
        for p in bp.get("patterns", []):
            elements.append(Paragraph(f"• <b>{p.get('name', '')}</b> ({p.get('frequency', '')}): {p.get('note', '')}", bullet))
        if bp.get("source"):
            elements.append(Paragraph(f"Confidence: {bp.get('confidence', '')} | Source: {cite(bp['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("ecg_changes"):
        ecg = sym["ecg_changes"]
        elements.append(Paragraph("Real ECG evolution:", subhead))
        if ecg.get("note"):
            elements.append(Paragraph(ecg["note"], body))
        for f in ecg.get("findings", []):
            elements.append(Paragraph(f"• {f}", bullet))
        if ecg.get("source"):
            elements.append(Paragraph(f"Confidence: {ecg.get('confidence', '')} | Source: {cite(ecg['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    render_flat_dict_section("biomarker_pattern", "Real biomarker pattern (troponin-echo mismatch, natriuretic peptides):")

    if isinstance(sym.get("complications"), list):
        # Stroke's complications is a LIST of {name, note, source, confidence} dicts, unlike every
        # other disease's dict-of-topics shape below -- the dict-shaped handler's comps.items() would
        # crash on a list, so it is rendered separately here instead.
        elements.append(Paragraph("Real complications:", subhead))
        for comp in sym["complications"]:
            elements.append(Paragraph(f"• <b>{comp.get('name', '')}:</b> {comp.get('note', '')}", bullet))
            if comp.get("source"):
                elements.append(Paragraph(f"Confidence: {comp.get('confidence', '')} | Source: {cite(comp['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("complications") and disease_id not in ("gerd", "celiac_disease") and isinstance(sym["complications"], dict):
        # GERD's and celiac disease's complications (flat string-valued dicts with a top-level "source"
        # key) are already fully rendered above (GERD-specific / Celiac Disease-specific structured
        # blocks) with their source citations printed -- this generic handler below excludes but never
        # prints a top-level "source" key, so it would otherwise silently drop that source citation.
        comps = sym["complications"]
        elements.append(Paragraph("Real complications:", subhead))
        for ck, cv in comps.items():
            if ck in ("confidence", "source"):
                continue
            if isinstance(cv, str):
                elements.append(Paragraph(f"• <b>{ck.replace('_', ' ').title()}:</b> {cv}", bullet))
                continue
            if not isinstance(cv, dict):
                continue
            elements.append(Paragraph(ck.replace('_', ' ').title() + ":", body))
            for fk, fv in cv.items():
                if fk in ("source", "confidence") or not isinstance(fv, str):
                    continue
                elements.append(Paragraph(f"• <b>{fk.replace('_', ' ').title()}:</b> {fv}", bullet))
            if cv.get("source"):
                elements.append(Paragraph(f"Confidence: {cv.get('confidence', '')} | Source: {cite(cv['source'])}", cite_marker_s))
        if comps.get("confidence"):
            elements.append(Paragraph(f"Overall confidence: {comps['confidence']}", small_grey))
        elements.append(Spacer(1, 4))

    if sym.get("pathophysiology"):
        elements.append(Paragraph("Real pathophysiology:", subhead))
        render_generic_kv("pathophysiology", sym["pathophysiology"], depth=1)
        elements.append(Spacer(1, 4))

    if sym.get("latency_period"):
        elements.append(Paragraph("Real latency period:", subhead))
        render_generic_kv("latency_period", sym["latency_period"], depth=1)
        elements.append(Spacer(1, 4))

    if sym.get("major_manifestations"):
        elements.append(Paragraph("Real major manifestations (detail):", subhead))
        for mk, mv in sym["major_manifestations"].items():
            render_generic_kv(mk, mv, depth=1)
        elements.append(Spacer(1, 4))

    # ---- Parkinson's disease-specific structured blocks ----
    # parkinsons_disease's symptoms object introduces key names/shapes that no earlier handler covers:
    # definition_and_pathophysiology (dict of {finding, source, confidence} topic dicts),
    # diagnostic_framework (dict of topic dicts with string, list and nested-dict fields -- would otherwise
    # fall into the generic "Lake Louise Criteria & Dallas Histopathological Criteria" myocarditis catch-all
    # and be mislabeled and partially dropped), non_motor_symptoms_and_prodromal_phase (string + list of
    # {name, note, source} + nested dict), staging_hoehn_and_yahr (string + list of stages),
    # classification_of_parkinsonism (strings + nested dicts), acute_akinetic_crisis_parkinsonism_
    # hyperpyrexia_syndrome (flat string fields), epidemiology's regional_and_ethnic_variation (the
    # disease-agnostic global+india_specific handler renders only those two keys), and the per-feature
    # "source" strings inside "core" (the disease-agnostic core handler prints name/note only).
    # Rendered explicitly here with one recursive renderer so no leaf value can be silently dropped.
    if disease_id == "parkinsons_disease":
        def _pd_title(k):
            return str(k).replace("_", " ").strip()

        def _pd_esc(txt):
            # Bare "&" immediately followed by a letter (e.g. "H&Y") is otherwise parsed by reportlab as the
            # start of an XML entity and rendered as "H&Y;" -- escape it so the source text prints exactly.
            return re.sub(r"&(?![A-Za-z]+;|#[0-9]+;|amp;)", "&amp;", txt) if isinstance(txt, str) else txt

        def _pd_render(v, depth=0):
            if isinstance(v, str):
                elements.append(Paragraph(_pd_esc(v), body))
                return
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        elements.append(Paragraph(f"• {_pd_esc(item)}", bullet))
                    elif isinstance(item, dict):
                        nm = item.get("name") or item.get("stage") or item.get("label") or ""
                        if nm:
                            elements.append(Paragraph(f"<b>{_pd_esc(nm)}</b>", body))
                        _pd_render({ik: iv for ik, iv in item.items() if ik not in ("name", "stage", "label")}, depth + 1)
                return
            if isinstance(v, dict):
                tail = []
                for k2, v2 in v.items():
                    if k2 in ("source", "confidence") and isinstance(v2, str):
                        tail.append((k2, v2))
                        continue
                    if isinstance(v2, str):
                        if k2 in ("finding", "description", "note", "definition"):
                            elements.append(Paragraph(_pd_esc(v2), body))
                        else:
                            elements.append(Paragraph(f"<b>{_pd_title(k2).capitalize()}:</b> {_pd_esc(v2)}", body))
                    else:
                        elements.append(Paragraph(f"<b>{_pd_title(k2).capitalize()}:</b>", body))
                        _pd_render(v2, depth + 1)
                if tail:
                    conf = next((t[1] for t in tail if t[0] == "confidence"), "")
                    src = next((t[1] for t in tail if t[0] == "source"), "")
                    line = " | ".join(x for x in (f"Confidence: {conf}" if conf else "", f"Source: {cite(src)}" if src else "") if x)
                    elements.append(Paragraph(_pd_esc(line), small_grey))

        for pd_key, pd_heading in (
            ("definition_and_pathophysiology", "Real definition and pathophysiology -- alpha-synuclein/Lewy pathology, nigral neuron loss, basal ganglia circuit, Braak staging, non-dopaminergic features:"),
            ("diagnostic_framework", "Real diagnostic framework -- clinical diagnosis, MDS 2015 criteria, UK Brain Bank criteria, DaTscan, levodopa response, alpha-synuclein seed amplification assay:"),
            ("non_motor_symptoms_and_prodromal_phase", "Real non-motor symptoms and the prodromal phase of Parkinson's disease:"),
            ("staging_hoehn_and_yahr", "Real staging -- Hoehn and Yahr scale:"),
            ("classification_of_parkinsonism", "Real classification of parkinsonism -- idiopathic PD vs secondary parkinsonism vs atypical (Parkinson-plus) syndromes:"),
            ("acute_akinetic_crisis_parkinsonism_hyperpyrexia_syndrome", "Real acute akinetic crisis / parkinsonism-hyperpyrexia syndrome (symptom-side description):"),
        ):
            pd_obj = sym.get(pd_key)
            if pd_obj:
                elements.append(Paragraph(pd_heading, subhead))
                for k3, v3 in pd_obj.items() if isinstance(pd_obj, dict) and pd_key in ("definition_and_pathophysiology", "diagnostic_framework", "non_motor_symptoms_and_prodromal_phase", "classification_of_parkinsonism") else [(None, pd_obj)]:
                    if k3 is not None:
                        if isinstance(v3, str):
                            elements.append(Paragraph(f"<b>{_pd_title(k3).capitalize()}:</b> {_pd_esc(v3)}", body))
                            continue
                        elements.append(Paragraph(f"<b>{_pd_title(k3).capitalize()}</b>", subhead))
                    _pd_render(v3)
                elements.append(Spacer(1, 4))

        pd_epi = sym.get("epidemiology")
        if isinstance(pd_epi, dict):
            pd_epi_rest = {k4: v4 for k4, v4 in pd_epi.items() if k4 not in ("global", "india_specific")}
            if pd_epi_rest:
                elements.append(Paragraph("Real epidemiology -- regional/ethnic variation and other epidemiology detail:", subhead))
                for k4, v4 in pd_epi_rest.items():
                    if isinstance(v4, str):
                        elements.append(Paragraph(f"<b>{_pd_title(k4).capitalize()}:</b> {_pd_esc(v4)}", body))
                    else:
                        elements.append(Paragraph(f"<b>{_pd_title(k4).capitalize()}</b>", subhead))
                        _pd_render(v4)
                elements.append(Spacer(1, 4))

        pd_core = sym.get("core")
        if isinstance(pd_core, list):
            elements.append(Paragraph("Real source citations for each core feature:", subhead))
            for ci in pd_core:
                if isinstance(ci, dict) and ci.get("source"):
                    elements.append(Paragraph(f"<b>{_pd_esc(ci.get('name', ''))}:</b> {_pd_esc(ci['source'])}", small_grey))
            elements.append(Spacer(1, 4))

    # ---- Alzheimer's disease-specific structured blocks ----
    # alzheimers_disease's symptoms object introduces key names/shapes that no earlier handler covers
    # correctly: definition_and_pathophysiology (dict of topic dicts, some with list/nested-dict fields
    # e.g. amyloid_cascade_hypothesis_debate), diagnostic_framework (would otherwise fall into the
    # generic Lake-Louise-Dallas myocarditis catch-all below and be mislabeled), staging (matches no
    # generic handler), atypical_variants (list of {name, note, source} -- distinct from "core", which
    # the disease-agnostic CORE_LABELS handler already renders correctly), behavioral_and_psychological_
    # symptoms_of_dementia_bpsd (dict with "framing" string + "features" list), late_stage_and_functional_
    # decline (dict of topic dicts), differential_dementias_and_reversible_causes (dict of topic dicts,
    # matches no generic handler), epidemiology (uses "global"/"india_specific" keys, NOT the "global"/
    # "india" pair the disease-agnostic epidemiology handler requires, so that handler silently skips it --
    # rendered explicitly here instead), and prevention_and_lifestyle_clinical_course_evidence /
    # clinical_takeaway (both disease-specific key names, no generic handler). ("core", "red_flags" and
    # "real_risk_factors" already match existing generic handlers correctly and are NOT re-rendered here
    # to avoid duplication; "natural_history" matches the generic natural_history fallback further below.)
    if disease_id == "alzheimers_disease":
        def _ad_title(k):
            return str(k).replace("_", " ").strip().capitalize()

        def _ad_render(v, depth=0):
            if isinstance(v, str):
                elements.append(Paragraph(v, body))
                return
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        elements.append(Paragraph(f"• {item}", bullet))
                    elif isinstance(item, dict):
                        nm = item.get("name") or item.get("factor") or item.get("point") or ""
                        if nm:
                            elements.append(Paragraph(f"<b>{nm}</b>", body))
                        _ad_render({ik: iv for ik, iv in item.items() if ik not in ("name", "factor", "point")}, depth + 1)
                return
            if isinstance(v, dict):
                tail = []
                for k2, v2 in v.items():
                    if k2 in ("source", "confidence") and isinstance(v2, str):
                        tail.append((k2, v2))
                        continue
                    if isinstance(v2, str):
                        if k2 in ("finding", "framing", "note", "definition", "why"):
                            elements.append(Paragraph(v2, body))
                        else:
                            elements.append(Paragraph(f"<b>{_ad_title(k2)}:</b> {v2}", body))
                    else:
                        elements.append(Paragraph(f"<b>{_ad_title(k2)}</b>", subhead if depth == 0 else body))
                        _ad_render(v2, depth + 1)
                if tail:
                    conf = next((t[1] for t in tail if t[0] == "confidence"), "")
                    src = next((t[1] for t in tail if t[0] == "source"), "")
                    line = " | ".join(x for x in (f"Confidence: {conf}" if conf else "", f"Source: {cite(src)}" if src else "") if x)
                    if line:
                        elements.append(Paragraph(line, cite_marker_s))

        for ad_key, ad_heading in (
            ("definition_and_pathophysiology", "Real definition and pathophysiology -- amyloid-beta plaques, tau neurofibrillary tangles, cholinergic deficit, synaptic loss, neuroinflammation/TREM2, and the honest amyloid-cascade-hypothesis debate:"),
            ("diagnostic_framework", "Real diagnostic framework -- NIA-AA 2011 criteria, 2024 biological-vs-clinical-biological definition debate, DSM-5, CSF/PET/plasma p-tau217 biomarkers, MRI, MMSE/MoCA, autopsy gold standard:"),
            ("staging", "Real staging -- preclinical AD, MCI due to AD and conversion rates, CDR scale, GDS/FAST stages, mild/moderate/severe clinical staging:"),
            ("atypical_variants", "Real atypical variants -- posterior cortical atrophy (visual variant) and logopenic variant primary progressive aphasia (language variant):"),
            ("behavioral_and_psychological_symptoms_of_dementia_bpsd", "Real behavioural and psychological symptoms of dementia (BPSD) -- Cache County Study prevalence data:"),
            ("late_stage_and_functional_decline", "Real late-stage and functional decline -- ADL loss, dysphagia/aspiration pneumonia, immobility and terminal decline:"),
            ("differential_dementias_and_reversible_causes", "Real differential diagnosis -- vascular dementia, dementia with Lewy bodies, frontotemporal dementia, mixed dementia, and reversible/treatable mimics requiring standard work-up:"),
            ("prevention_and_lifestyle_clinical_course_evidence", "Real prevention/lifestyle trial evidence affecting clinical course -- FINGER, US POINTER, SPRINT MIND:"),
            ("clinical_takeaway", "Real clinical takeaway:"),
        ):
            ad_obj = sym.get(ad_key)
            if not ad_obj:
                continue
            elements.append(Paragraph(ad_heading, subhead))
            if ad_key == "behavioral_and_psychological_symptoms_of_dementia_bpsd" and isinstance(ad_obj, dict):
                if ad_obj.get("framing"):
                    elements.append(Paragraph(ad_obj["framing"], body))
                for feat in ad_obj.get("features", []):
                    if not isinstance(feat, dict):
                        continue
                    elements.append(Paragraph(f"• <b>{feat.get('name', '')}:</b> {feat.get('note', '')}", bullet))
                    if feat.get("source"):
                        elements.append(Paragraph(f"Source: {cite(feat['source'])}", cite_marker_s))
            elif isinstance(ad_obj, dict):
                for k3, v3 in ad_obj.items():
                    if isinstance(v3, str):
                        elements.append(Paragraph(f"<b>{_ad_title(k3)}:</b> {v3}", body))
                        continue
                    elements.append(Paragraph(f"<b>{_ad_title(k3)}</b>", body))
                    _ad_render(v3, depth=1)
            else:
                _ad_render(ad_obj)
            elements.append(Spacer(1, 4))

        # epidemiology (global/india_specific) is already correctly rendered, with the right
        # heading, by the disease-agnostic epidemiology handler further below (matches on the
        # "global"+"india_specific" key pair) -- not re-rendered here to avoid duplication.

        ad_core = sym.get("core")
        if isinstance(ad_core, list):
            elements.append(Paragraph("Real source citations for each core feature:", subhead))
            for ci in ad_core:
                if isinstance(ci, dict) and ci.get("source"):
                    elements.append(Paragraph(f"<b>{ci.get('name', '')}:</b> {ci['source']}", small_grey))
            elements.append(Spacer(1, 4))

    # ---- Multiple sclerosis-specific structured blocks ----
    # multiple_sclerosis's symptoms object introduces key names/shapes that no earlier handler covers:
    # definition_and_pathophysiology (dict of {finding, source, confidence} topic dicts -- same shape as
    # PD/AD but a disease-agnostic handler does not exist for this key, so without a dedicated block it
    # would be silently dropped entirely), diagnostic_framework (dict of {finding, source, confidence}
    # topic dicts -- would otherwise fall into the generic Lake-Louise-Dallas myocarditis catch-all below
    # and be mislabeled), disease_course_classification_lublin_2013 (list of {phenotype, note, source} --
    # matches no generic handler), relapse_and_pseudorelapse (dict of two {finding, source} topic dicts --
    # matches no generic handler), and clinical_takeaway (list of {point, why, source} -- disease-specific
    # key name, no generic handler). ("core", "red_flags", "real_risk_factors", "epidemiology" and
    # "natural_history" already match existing generic handlers correctly -- epidemiology matches the
    # "global"+"india_specific" disease-agnostic handler further below, natural_history matches the
    # generic natural_history fallback further below -- and are NOT re-rendered here to avoid
    # duplication, except "core" sources specifically, which the generic CORE_LABELS handler prints
    # without their per-item "source" field and are added back here, matching the AD/PD pattern.)
    if disease_id == "multiple_sclerosis":
        def _ms_title(k):
            return str(k).replace("_", " ").strip().capitalize()

        for ms_key, ms_heading in (
            ("definition_and_pathophysiology", "Real definition and pathophysiology -- immune-mediated demyelination, autoimmune relapse mechanism, mechanism of progression, EBV as a likely necessary cause, and HLA-DRB1*15:01 genetic risk:"),
            ("diagnostic_framework", "Real diagnostic framework -- 2017/2024 McDonald criteria, MRI dissemination in space/time, CSF oligoclonal bands, optic nerve VEP, and NMOSD/MOGAD differential diagnosis:"),
        ):
            ms_obj = sym.get(ms_key)
            if not isinstance(ms_obj, dict):
                continue
            elements.append(Paragraph(ms_heading, subhead))
            for k3, v3 in ms_obj.items():
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_ms_title(k3)}</b>", body))
                if v3.get("finding"):
                    elements.append(Paragraph(v3["finding"], body))
                if v3.get("source"):
                    elements.append(Paragraph(f"Confidence: {v3.get('confidence', '')} | Source: {cite(v3['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        dcc = sym.get("disease_course_classification_lublin_2013")
        if isinstance(dcc, list):
            elements.append(Paragraph("Real disease course classification -- Lublin 2013 revisions (CIS, RIS, RRMS, SPMS, PPMS):", subhead))
            for phen in dcc:
                if not isinstance(phen, dict):
                    continue
                elements.append(Paragraph(f"• <b>{phen.get('phenotype', '')}:</b> {phen.get('note', '')}", bullet))
                if phen.get("source"):
                    elements.append(Paragraph(f"Source: {cite(phen['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        rap = sym.get("relapse_and_pseudorelapse")
        if isinstance(rap, dict):
            elements.append(Paragraph("Real relapse vs pseudorelapse:", subhead))
            for k3, v3 in rap.items():
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_ms_title(k3)}:</b>", body))
                if v3.get("finding"):
                    elements.append(Paragraph(v3["finding"], body))
                if v3.get("source"):
                    elements.append(Paragraph(f"Source: {cite(v3['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        ms_core = sym.get("core")
        if isinstance(ms_core, list):
            elements.append(Paragraph("Real source citations for each core feature:", subhead))
            for ci in ms_core:
                if isinstance(ci, dict) and ci.get("source"):
                    elements.append(Paragraph(f"<b>{ci.get('name', '')}:</b> {ci['source']}", small_grey))
            elements.append(Spacer(1, 4))

        ct = sym.get("clinical_takeaway")
        if isinstance(ct, list) and ct and isinstance(ct[0], dict) and "point" in ct[0]:
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            for item in ct:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• {item.get('point', '')}", bullet))
                if item.get("why"):
                    elements.append(Paragraph(item["why"], body))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Migraine-specific structured blocks ----
    # migraine's symptoms object introduces key names/shapes that no earlier handler covers:
    # definition_and_pathophysiology and clinical_phases_of_an_attack (dicts of {finding, source,
    # confidence} topic dicts -- same shape as MS/PD/AD but under disease-specific key names with no
    # generic handler); diagnostic_framework_ichd3 (NOT the plain "diagnostic_framework" key other
    # diseases use, so it deliberately does NOT fall into the Jones-Criteria/TSH/Lake-Louise-Dallas
    # generic chain below -- it needs its own heading here or it would be silently dropped);
    # red_flags_secondary_headache (distinct from the generic "red_flags" key -- would otherwise be
    # silently dropped, not merely mislabeled); migraine_subtypes and differential_diagnosis (dicts of
    # topic dicts, some entries omitting "confidence" -- handled defensively); risk_factors_and_triggers
    # (disease-specific key name, NOT the generic "real_risk_factors" this file uses elsewhere);
    # epidemiology (uses "global_burden"/"india_specific" keys -- NOT the "global"/"india_specific" pair
    # the disease-agnostic epi8 handler above requires, and NOT the "global_burden"/"india_specific_data"
    # pair the PUD/IBD/GERD-style flat-string branches require either, so it is added to the flat
    # render_flat_dict_section exclusion list further above and rendered explicitly here instead);
    # natural_history_and_comorbidities (disease-specific key name, not the generic "natural_history"
    # fallback); and clinical_takeaway (list of {point, why, source} -- same shape as MS's, rendered
    # with its own heading here since this block is independent of the disease_id=="multiple_sclerosis"
    # guard above).
    if disease_id == "migraine":
        def _mig_title(k):
            return str(k).replace("_", " ").strip().capitalize()

        for mig_key, mig_heading in (
            ("definition_and_pathophysiology", "Real definition and pathophysiology -- trigeminovascular activation, CGRP's role, cortical spreading depression/aura, neurogenic inflammation, and the real FHM channelopathy genetics:"),
            ("diagnostic_framework_ichd3", "Real diagnostic framework -- ICHD-3 criteria for migraine without aura, migraine with aura, chronic migraine, and medication-overuse headache:"),
            ("red_flags_secondary_headache", "Real red flags for secondary headache -- the SNNOOP10 mnemonic and specific urgent scenarios:"),
            ("clinical_phases_of_an_attack", "Real clinical phases of a migraine attack -- premonitory, aura, headache and postdrome:"),
            ("migraine_subtypes", "Real migraine subtypes -- with/without aura, chronic, hemiplegic, vestibular, menstrual, and paediatric migraine:"),
            ("differential_diagnosis", "Real differential diagnosis -- tension-type headache, cluster headache, and secondary-headache exclusion:"),
            ("risk_factors_and_triggers", "Real risk factors and triggers -- genetics, sex/hormonal factors, common triggers (with an honest evidence caveat), obesity and medication overuse as chronification drivers:"),
            ("epidemiology", "Real epidemiology -- Global Burden of Disease 2021 & India-specific community studies:"),
            ("natural_history_and_comorbidities", "Real natural history and comorbidities -- episodic-to-chronic transition, psychiatric comorbidity, migraine-with-aura stroke risk, and change with menopause:"),
        ):
            mig_obj = sym.get(mig_key)
            if not isinstance(mig_obj, dict):
                continue
            elements.append(Paragraph(mig_heading, subhead))
            for k3, v3 in mig_obj.items():
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_mig_title(k3)}</b>", body))
                if v3.get("finding"):
                    elements.append(Paragraph(v3["finding"], body))
                if v3.get("source"):
                    conf = v3.get("confidence", "")
                    conf_line = f"Confidence: {conf} | Source: {cite(v3['source'])}" if conf else f"Source: {cite(v3['source'])}"
                    elements.append(Paragraph(conf_line, cite_marker_s))
            elements.append(Spacer(1, 4))

        mig_ct = sym.get("clinical_takeaway")
        if isinstance(mig_ct, list) and mig_ct and isinstance(mig_ct[0], dict) and "point" in mig_ct[0]:
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            for item in mig_ct:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• {item.get('point', '')}", bullet))
                if item.get("why"):
                    elements.append(Paragraph(item["why"], body))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Guillain-Barré Syndrome-specific structured blocks ----
    # guillain_barre_syndrome's symptoms object reuses "definition_and_pathophysiology" and
    # "diagnostic_framework" (same dict-of-{finding,source,confidence} shape as MS/PD/AD, but under
    # this disease_id they would otherwise fall into the Lake-Louise-Dallas myocarditis catch-all
    # further below and be mislabeled/have their confidence field dropped -- guarded out of that chain
    # below), and introduces disease-specific key names with no generic handler at all (would be
    # silently dropped without a dedicated block): subtypes_and_variants, core_symptoms_and_progression,
    # risk_factors_and_epidemiology (NOT the generic "real_risk_factors" key), EMERGENCY_red_flags (a
    # list of plain strings -- distinct from the generic "red_flags" key so it does NOT render via that
    # handler), differential_diagnosis (a LIST of {condition, distinguishing_features, source} dicts --
    # a different shape from migraine's dict-of-topics use of the same key name, so migraine's
    # disease_id-gated handling above does not apply here), and natural_history_and_prognosis (a dict of
    # {finding, source, confidence} topic dicts, NOT the flat string-valued shape every other disease
    # using this key has -- guarded out of the generic render_flat_dict_section call above). ("core" and
    # "clinical_takeaway" match the same shapes MS/migraine already use and are rendered the same way.)
    if disease_id == "guillain_barre_syndrome":
        def _gbs_title(k):
            return str(k).replace("_", " ").strip().capitalize()

        def _gbs_topic_dict_section(gbs_key, gbs_heading):
            gbs_obj = sym.get(gbs_key)
            if not isinstance(gbs_obj, dict):
                return
            elements.append(Paragraph(gbs_heading, subhead))
            for k3, v3 in gbs_obj.items():
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_gbs_title(k3)}</b>", body))
                if v3.get("finding"):
                    elements.append(Paragraph(v3["finding"], body))
                if v3.get("source"):
                    conf = v3.get("confidence", "")
                    conf_line = f"Confidence: {conf} | Source: {cite(v3['source'])}" if conf else f"Source: {cite(v3['source'])}"
                    elements.append(Paragraph(conf_line, cite_marker_s))
            elements.append(Spacer(1, 4))

        _gbs_topic_dict_section("definition_and_pathophysiology", "Real definition and pathophysiology -- molecular mimicry, Campylobacter/CMV/Zika/EBV triggers, honestly-reported post-COVID-19/post-vaccination signal, and demyelinating vs axonal subtypes:")
        _gbs_topic_dict_section("diagnostic_framework", "Real diagnostic framework -- NINDS/Asbury-Cornblath clinical criteria, Brighton Collaboration certainty levels, CSF albuminocytologic dissociation, nerve conduction studies, and MRI findings:")
        _gbs_topic_dict_section("subtypes_and_variants", "Real subtypes and variants -- AIDP, AMAN/AMSAN, Miller Fisher syndrome, Bickerstaff brainstem encephalitis, and pharyngeal-cervical-brachial variant:")
        _gbs_topic_dict_section("core_symptoms_and_progression", "Real core symptoms and progression -- ascending weakness timeline, cranial nerve/facial involvement, autonomic dysfunction, pain, and respiratory muscle weakness:")
        _gbs_topic_dict_section("risk_factors_and_epidemiology", "Real risk factors and epidemiology -- age/sex patterns, preceding-infection timeline, global incidence, India-specific data, and vaccination as a minor contributor:")
        _gbs_topic_dict_section("natural_history_and_prognosis", "Real natural history and prognosis -- disease course, mortality, residual disability, EGOS/EGRIS prognostic scoring, and relapse/CIDP-conversion:")

        gbs_rf = sym.get("EMERGENCY_red_flags")
        if isinstance(gbs_rf, list) and gbs_rf:
            elements.append(Paragraph("RED FLAGS — escalate to a real doctor / ICU immediately:", subhead))
            rf_style = ParagraphStyle("gbs_rf", parent=bullet, textColor=CORAL)
            for rf in gbs_rf:
                if isinstance(rf, str):
                    elements.append(Paragraph(f"• {rf}", rf_style))
            elements.append(Spacer(1, 4))

        gbs_dd = sym.get("differential_diagnosis")
        if isinstance(gbs_dd, list) and gbs_dd:
            elements.append(Paragraph("Real differential diagnosis:", subhead))
            for item in gbs_dd:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• <b>{item.get('condition', '')}:</b> {item.get('distinguishing_features', '')}", bullet))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        gbs_core = sym.get("core")
        if isinstance(gbs_core, list):
            elements.append(Paragraph("Real source citations for each core feature:", subhead))
            for ci in gbs_core:
                if isinstance(ci, dict) and ci.get("source"):
                    elements.append(Paragraph(f"<b>{ci.get('name', '')}:</b> {ci['source']}", small_grey))
            elements.append(Spacer(1, 4))

        gbs_ct = sym.get("clinical_takeaway")
        if isinstance(gbs_ct, list) and gbs_ct and isinstance(gbs_ct[0], dict) and "point" in gbs_ct[0]:
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            for item in gbs_ct:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• {item.get('point', '')}", bullet))
                if item.get("why"):
                    elements.append(Paragraph(item["why"], body))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Bacterial Meningitis-specific structured blocks ----
    # bacterial_meningitis's symptoms object reuses the same dict-of-{finding, source, confidence}
    # topic shape as GBS for definition_and_pathophysiology, diagnostic_framework,
    # core_symptoms_and_progression and risk_factors_and_epidemiology, and adds
    # EMERGENCY_time_critical_evidence in the same shape (no generic handler at all -- would be silently
    # dropped). EMERGENCY_red_flags is a list of plain strings (distinct from the generic "red_flags"
    # key), differential_diagnosis a LIST of {condition, distinguishing_features, source} dicts and
    # clinical_takeaway a list of {point, why, source} dicts; none has a generic handler under this
    # disease_id, and diagnostic_framework would otherwise fall into the Lake-Louise-Dallas myocarditis
    # catch-all below (guarded out there). "complications" is rendered by the generic "Real
    # complications" handler above and is not repeated here.
    if disease_id == "bacterial_meningitis":
        def _bm_title(k):
            return str(k).replace("_", " ").strip().capitalize()

        def _bm_topic_dict_section(bm_key, bm_heading):
            bm_obj = sym.get(bm_key)
            if not isinstance(bm_obj, dict):
                return
            elements.append(Paragraph(bm_heading, subhead))
            for k3, v3 in bm_obj.items():
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_bm_title(k3)}</b>", body))
                if v3.get("finding"):
                    elements.append(Paragraph(v3["finding"], body))
                if v3.get("source"):
                    conf = v3.get("confidence", "")
                    conf_line = f"Confidence: {conf} | Source: {cite(v3['source'])}" if conf else f"Source: {cite(v3['source'])}"
                    elements.append(Paragraph(conf_line, cite_marker_s))
            elements.append(Spacer(1, 4))

        _bm_topic_dict_section("definition_and_pathophysiology", "Real definition and pathophysiology -- causative organisms by age, post-vaccination epidemiologic shift, routes of CNS invasion, and the inflammatory cascade driving raised ICP:")
        _bm_topic_dict_section("EMERGENCY_time_critical_evidence", "Real time-critical evidence -- door-to-antibiotic time and outcome, and speed of meningococcal progression:")
        _bm_topic_dict_section("diagnostic_framework", "Real diagnostic framework -- classic triad sensitivity, meningeal signs, CSF patterns (bacterial, viral, tuberculous), CSF lactate, Gram stain/culture, PCR, CT-before-LP indications and LP contraindications:")
        _bm_topic_dict_section("core_symptoms_and_progression", "Real core symptoms and progression -- adult symptom frequencies, altered consciousness and seizures, infant/child presentation, meningococcal rash, and atypical presentations:")
        _bm_topic_dict_section("risk_factors_and_epidemiology", "Real risk factors and epidemiology -- age extremes, immunocompromise/asplenia/complement deficiency, crowding, vaccination status, CSF leak, global burden and India-specific data:")

        bm_rf = sym.get("EMERGENCY_red_flags")
        if isinstance(bm_rf, list) and bm_rf:
            elements.append(Paragraph("RED FLAGS — escalate to a real doctor / emergency department immediately:", subhead))
            rf_style = ParagraphStyle("bm_rf", parent=bullet, textColor=CORAL)
            for rf in bm_rf:
                if isinstance(rf, str):
                    elements.append(Paragraph(f"• {rf}", rf_style))
            elements.append(Spacer(1, 4))

        bm_dd = sym.get("differential_diagnosis")
        if isinstance(bm_dd, list) and bm_dd:
            elements.append(Paragraph("Real differential diagnosis:", subhead))
            for item in bm_dd:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• <b>{item.get('condition', '')}:</b> {item.get('distinguishing_features', '')}", bullet))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        bm_ct = sym.get("clinical_takeaway")
        if isinstance(bm_ct, list) and bm_ct and isinstance(bm_ct[0], dict) and "point" in bm_ct[0]:
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            for item in bm_ct:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• {item.get('point', '')}", bullet))
                if item.get("why"):
                    elements.append(Paragraph(item["why"], body))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Myasthenia Gravis-specific structured blocks ----
    # myasthenia_gravis's symptoms object reuses "definition_and_pathophysiology" and
    # "diagnostic_framework" (same dict-of-{finding,source,confidence} topic shape as MS/PD/AD/GBS,
    # but under this disease_id they would otherwise fall into the Lake-Louise-Dallas myocarditis
    # catch-all further below and be mislabeled/have their confidence field dropped -- guarded out of
    # that chain below), reuses "classic_symptoms" (guarded out of the GINA-asthma "circadian pattern"
    # generic loop above), and reuses "differential_diagnosis", "risk_factors", "epidemiology" (a
    # "global_burden"/"india_specific_data" shape matching PUD/IBD/GERD/celiac_disease's shape but
    # NOT gated to those disease_ids, so it would otherwise be silently dropped) and "natural_history"
    # with no generic disease-agnostic handler matching this exact dict-of-topic-dicts shape for any of
    # them under this disease_id. It also introduces "classification_mgfa" and "myasthenic_crisis_detail",
    # disease-specific key names with no generic handler at all (would be silently dropped without a
    # dedicated block). "clinical_takeaway" here is a single flat {finding, source, confidence} dict,
    # NOT the list-of-{point, why, source} shape migraine/GBS use for the same key name, so it needs its
    # own simple rendering rather than either of those generic list-based handlers.
    if disease_id == "myasthenia_gravis":
        def _mg_title(k):
            return str(k).replace("_", " ").strip().capitalize()

        def _mg_topic_dict_section(mg_key, mg_heading):
            mg_obj = sym.get(mg_key)
            if not isinstance(mg_obj, dict):
                return
            elements.append(Paragraph(mg_heading, subhead))
            for k3, v3 in mg_obj.items():
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_mg_title(k3)}</b>", body))
                if v3.get("finding"):
                    elements.append(Paragraph(v3["finding"], body))
                if v3.get("source"):
                    conf = v3.get("confidence", "")
                    conf_line = f"Confidence: {conf} | Source: {cite(v3['source'])}" if conf else f"Source: {cite(v3['source'])}"
                    elements.append(Paragraph(conf_line, cite_marker_s))
            elements.append(Spacer(1, 4))

        _mg_topic_dict_section("definition_and_pathophysiology", "Real definition and pathophysiology -- AChR antibody-mediated postsynaptic damage, the MuSK-antibody subtype, LRP4/seronegative MG, and the role of the thymus:")
        _mg_topic_dict_section("diagnostic_framework", "Real diagnostic framework -- bedside clinical tests, AChR/MuSK/LRP4 serologic antibody testing, repetitive nerve stimulation, single-fiber EMG, the edrophonium (Tensilon) test, and thymoma imaging screening:")
        _mg_topic_dict_section("classification_mgfa", "Real classification -- MGFA clinical classes, ocular vs generalized MG, and the MuSK-vs-AChR clinical pattern:")
        _mg_topic_dict_section("classic_symptoms", "Real classic symptoms -- the core fatigable-weakness feature, ocular, bulbar, limb/axial, and respiratory involvement:")
        _mg_topic_dict_section("myasthenic_crisis_detail", "Real myasthenic crisis -- definition and frequency, precipitating factors, medications that worsen MG, and bedside respiratory monitoring:")
        _mg_topic_dict_section("differential_diagnosis", "Real differential diagnosis -- Lambert-Eaton myasthenic syndrome, botulism, Guillain-Barre syndrome/Miller Fisher syndrome, and thyroid eye disease/other ptosis-diplopia causes:")
        _mg_topic_dict_section("risk_factors", "Real risk factors -- age/sex bimodal pattern and autoimmune/thymic comorbidity:")
        _mg_topic_dict_section("epidemiology", "Real epidemiology -- global burden and India-specific data:")
        _mg_topic_dict_section("natural_history", "Real natural history -- disease course, modern mortality, pregnancy and MG, and transient neonatal myasthenia:")

        mg_ct = sym.get("clinical_takeaway")
        if isinstance(mg_ct, dict) and mg_ct.get("finding"):
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            elements.append(Paragraph(mg_ct["finding"], body))
            if mg_ct.get("source"):
                conf = mg_ct.get("confidence", "")
                conf_line = f"Confidence: {conf} | Source: {cite(mg_ct['source'])}" if conf else f"Source: {cite(mg_ct['source'])}"
                elements.append(Paragraph(conf_line, cite_marker_s))
            elements.append(Spacer(1, 4))

    # ---- Amyotrophic Lateral Sclerosis-specific structured blocks ----
    # amyotrophic_lateral_sclerosis's symptoms object reuses "definition_and_pathophysiology",
    # "diagnostic_framework" (same dict-of-{finding|framework, source, confidence} topic shape as
    # MS/PD/AD/GBS/MG, plus a "categories" list and "performance_note" string on some topics, but under
    # this disease_id they would otherwise fall into the Lake-Louise-Dallas myocarditis catch-all below
    # and be mislabeled -- guarded out of that chain below), "natural_history" and "epidemiology"
    # (global_incidence_prevalence/regional_and_ethnic_variation/india_specific -- matches none of the
    # generic "global"/"india_specific" or "global_burden"/"india_specific_data" pairs, so it would
    # otherwise print an empty heading). It also introduces "classic_symptoms_and_progression" (a single
    # flat {finding, source, confidence} dict), "motor_neuron_disease_variants" (framework/source plus a
    # list of {variant, features, prognosis, source}) and a "differential_diagnosis" shaped as
    # {framework, source, conditions:[{condition, how_it_mimics, distinguishing_features, treatable,
    # source, confidence}]} -- none has a generic handler under this disease_id, so all would be silently
    # dropped without this block. "core" renders through the generic handler (its per-feature source is
    # listed below, as for guillain_barre_syndrome), and "red_flags"/"real_risk_factors" render
    # correctly through the existing generic handlers; "clinical_takeaway" is the list-of-{point, why,
    # source} shape rendered here.
    if disease_id == "amyotrophic_lateral_sclerosis":
        def _als_title(k):
            return str(k).replace("_", " ").strip().capitalize()

        def _als_conf_source(obj):
            if obj.get("source"):
                conf = obj.get("confidence", "")
                conf_line = f"Confidence: {conf} | Source: {cite(obj['source'])}" if conf else f"Source: {cite(obj['source'])}"
                elements.append(Paragraph(conf_line, cite_marker_s))

        def _als_topic_dict_section(als_key, als_heading):
            als_obj = sym.get(als_key)
            if not isinstance(als_obj, dict):
                return
            elements.append(Paragraph(als_heading, subhead))
            for k3, v3 in als_obj.items():
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_als_title(k3)}</b>", body))
                for fk in ("finding", "framework"):
                    if v3.get(fk):
                        elements.append(Paragraph(v3[fk], body))
                for cat in v3.get("categories", []):
                    elements.append(Paragraph(f"• {cat}", bullet))
                if v3.get("performance_note"):
                    elements.append(Paragraph(f"<b>Performance note:</b> {v3['performance_note']}", body))
                _als_conf_source(v3)
            elements.append(Spacer(1, 4))

        _als_topic_dict_section("definition_and_pathophysiology", "Real definition and pathophysiology -- upper and lower motor neuron degeneration, TDP-43 proteinopathy, genetics (C9orf72, SOD1, TARDBP, FUS), glutamate excitotoxicity and the ALS-FTD spectrum:")
        _als_topic_dict_section("diagnostic_framework", "Real diagnostic framework -- clinical diagnosis, revised El Escorial, Awaji and Gold Coast criteria, EMG, neuroimaging, genetic testing and exclusion of mimics:")

        als_classic = sym.get("classic_symptoms_and_progression")
        if isinstance(als_classic, dict) and als_classic.get("finding"):
            elements.append(Paragraph("Real classic symptoms and progression -- regional onset and contiguous spread:", subhead))
            elements.append(Paragraph(als_classic["finding"], body))
            _als_conf_source(als_classic)
            elements.append(Spacer(1, 4))

        als_var = sym.get("motor_neuron_disease_variants")
        if isinstance(als_var, dict):
            elements.append(Paragraph("Real motor neuron disease variants -- classic ALS, progressive bulbar palsy, progressive muscular atrophy, primary lateral sclerosis and related phenotypes:", subhead))
            if als_var.get("framework"):
                elements.append(Paragraph(als_var["framework"], body))
            for item in als_var.get("variants", []):
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• <b>{item.get('variant', '')}:</b> {item.get('features', '')}", bullet))
                if item.get("prognosis"):
                    elements.append(Paragraph(f"Prognosis: {item['prognosis']}", small_grey))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            if als_var.get("source"):
                elements.append(Paragraph(f"Source: {cite(als_var['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        als_dd = sym.get("differential_diagnosis")
        if isinstance(als_dd, dict):
            elements.append(Paragraph("Real differential diagnosis -- ALS mimics and how to tell them apart:", subhead))
            if als_dd.get("framework"):
                elements.append(Paragraph(als_dd["framework"], body))
            for item in als_dd.get("conditions", []):
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• <b>{item.get('condition', '')}:</b> {item.get('how_it_mimics', '')}", bullet))
                if item.get("distinguishing_features"):
                    elements.append(Paragraph(f"Distinguishing features: {item['distinguishing_features']}", body))
                if item.get("treatable"):
                    elements.append(Paragraph(f"Treatable: {item['treatable']}", body))
                _als_conf_source(item)
            if als_dd.get("source"):
                elements.append(Paragraph(f"Source: {cite(als_dd['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        _als_topic_dict_section("epidemiology", "Real epidemiology -- global incidence and prevalence, regional and ethnic variation, and India-specific data:")
        _als_topic_dict_section("natural_history", "Real natural history -- median survival, bulbar versus limb onset, prognostic factors, respiratory failure and caregiver burden:")

        als_core = sym.get("core")
        if isinstance(als_core, list):
            elements.append(Paragraph("Real source citations for each core feature:", subhead))
            for ci in als_core:
                if isinstance(ci, dict) and ci.get("source"):
                    elements.append(Paragraph(f"<b>{ci.get('name', '')}:</b> {ci['source']}", small_grey))
            elements.append(Spacer(1, 4))

        als_ct = sym.get("clinical_takeaway")
        if isinstance(als_ct, list) and als_ct and isinstance(als_ct[0], dict) and "point" in als_ct[0]:
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            for item in als_ct:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• {item.get('point', '')}", bullet))
                if item.get("why"):
                    elements.append(Paragraph(item["why"], body))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ============ GOUT-SPECIFIC SYMPTOMS BLOCK ============
    # gout's symptoms object reuses generic key names ("definition_and_pathophysiology",
    # "diagnostic_framework", "epidemiology", "natural_history", "differential_diagnosis",
    # "clinical_takeaway", "core", "red_flags", "real_risk_factors") whose sub-structure is a set of
    # {finding, source, confidence} topic dicts. Without a dedicated block the generic handlers built
    # for other diseases would (a) print diagnostic_framework under the myocarditis "Lake Louise Criteria
    # & Dallas Histopathological Criteria" heading, (b) render only "global" and "india_specific" of the
    # epidemiology dict and silently drop "united_states" and "china_regional_comparator", (c) print
    # natural_history sub-topics as bare "finding:"/"confidence:" bullets and (d) drop
    # definition_and_pathophysiology, clinical_stages, atypical_presentations_and_special_settings,
    # differential_diagnosis, pharmacogenetics_hla_b5801_and_allopurinol, comorbidities and
    # clinical_takeaway entirely. Every key is rendered here under its own correct heading with the
    # cite() pattern (never raw source text); the generic handlers above/below are guarded with
    # disease_id != "gout". "core", "red_flags" and "real_risk_factors" already match existing
    # generic handlers correctly and are NOT re-rendered here, except that core's per-item sources
    # (dropped by the generic core handler) are printed below as cite() markers.
    if disease_id == "gout":
        _GT_TOKENS = {"msu": "MSU", "urat1": "URAT1", "glut9": "GLUT9", "abcg2": "ABCG2", "nlrp3": "NLRP3",
                      "il1b": "IL-1 beta", "acr": "ACR", "eular": "EULAR", "ct": "CT", "gwas": "GWAS",
                      "ckd": "CKD", "cppd": "CPPD", "nets": "NETs", "hla": "HLA"}

        def _gt_title(k):
            k = str(k).replace("6_8_mg_dl", "6.8 mg/dL").replace("b5801", "B*58:01")
            toks = [(_GT_TOKENS.get(t) or t) for t in k.replace("_", " ").split()]
            txt = " ".join(toks).strip()
            return txt[:1].upper() + txt[1:]

        def _gt_conf_source(obj):
            if isinstance(obj, dict) and obj.get("source"):
                conf = obj.get("confidence", "")
                line = f"Confidence: {conf} | Source: {cite(obj['source'])}" if conf else f"Source: {cite(obj['source'])}"
                elements.append(Paragraph(line, cite_marker_s))

        def _gt_topic_dict_section(gt_key, gt_heading):
            gt_obj = sym.get(gt_key)
            if not isinstance(gt_obj, dict):
                return
            elements.append(Paragraph(gt_heading, subhead))
            for k3, v3 in gt_obj.items():
                if isinstance(v3, str):
                    elements.append(Paragraph(f"<b>{_gt_title(k3)}:</b> {v3}", body))
                    continue
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_gt_title(k3)}</b>", body))
                for fk, fv in v3.items():
                    if fk in ("source", "confidence"):
                        continue
                    if isinstance(fv, str):
                        elements.append(Paragraph(fv if fk in ("finding", "framework") else f"<b>{_gt_title(fk)}:</b> {fv}", body))
                    elif isinstance(fv, list):
                        for li in fv:
                            if isinstance(li, str):
                                elements.append(Paragraph(f"• {li}", bullet))
                _gt_conf_source(v3)
            elements.append(Spacer(1, 4))

        _gt_topic_dict_section("definition_and_pathophysiology", "Real definition and pathophysiology -- urate solubility, purine metabolism and uricase loss, urate transporters, genetics, MSU crystal formation, NLRP3/IL-1 beta flare initiation and spontaneous resolution:")
        _gt_topic_dict_section("clinical_stages", "Real clinical stages -- asymptomatic hyperuricaemia, acute flare, intercritical period and chronic tophaceous gout:")

        gt_core = sym.get("core")
        if isinstance(gt_core, list):
            elements.append(Paragraph("Real source citations for each core feature:", subhead))
            for ci in gt_core:
                if isinstance(ci, dict) and ci.get("source"):
                    elements.append(Paragraph(f"<b>{ci.get('name', '')}:</b> Source: {cite(ci['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        gt_atyp = sym.get("atypical_presentations_and_special_settings")
        if isinstance(gt_atyp, list):
            elements.append(Paragraph("Real atypical presentations and special settings:", subhead))
            for item in gt_atyp:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• <b>{item.get('name', '')}:</b> {item.get('note', '')}", bullet))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        _gt_topic_dict_section("diagnostic_framework", "Real diagnostic framework -- clinical diagnosis, synovial fluid MSU crystals (gold standard), ACR/EULAR 2015 classification criteria, dual-energy CT, ultrasound, serum urate limits and radiographs:")
        _gt_topic_dict_section("differential_diagnosis", "Real differential diagnosis -- septic arthritis (must be excluded), CPPD (pseudogout), rheumatoid arthritis, cellulitis, reactive arthritis and trauma:")
        _gt_topic_dict_section("pharmacogenetics_hla_b5801_and_allopurinol", "Real pharmacogenetics -- HLA-B*58:01 and allopurinol severe cutaneous adverse reactions, screening evidence and India-specific gap:")
        _gt_topic_dict_section("comorbidities", "Real comorbidities -- cardiovascular disease, mortality, kidney disease and stones, hypertension, metabolic syndrome and diabetes:")
        _gt_topic_dict_section("epidemiology", "Real epidemiology -- global, United States, China (regional comparator) and India-specific:")
        _gt_topic_dict_section("natural_history", "Real natural history -- progression from hyperuricaemia, flare recurrence, crystal burden, transplant/CKD course, mortality and the treatment gap:")

        gt_ct = sym.get("clinical_takeaway")
        if isinstance(gt_ct, list) and gt_ct and isinstance(gt_ct[0], dict) and "point" in gt_ct[0]:
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            for item in gt_ct:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• {item.get('point', '')}", bullet))
                if item.get("why"):
                    elements.append(Paragraph(item["why"], body))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    # ============ RHEUMATOID-ARTHRITIS-SPECIFIC SYMPTOMS BLOCK ============
    # rheumatoid_arthritis's symptoms object reuses generic key names ("definition_and_pathophysiology",
    # "diagnostic_framework", "epidemiology", "natural_history", "differential_diagnosis",
    # "clinical_takeaway", "core", "red_flags", "real_risk_factors") plus RA-specific keys
    # ("disease_activity_measures", "extra_articular_disease"). Without a dedicated block the generic
    # handlers built for other diseases would (a) print diagnostic_framework under the myocarditis
    # "Lake Louise Criteria & Dallas Histopathological Criteria" heading, (b) render only "global" and
    # "india_specific" of the epidemiology dict and silently drop the other three topics, (c) print
    # natural_history sub-topics as bare "finding:"/"confidence:" bullets, (d) print red_flags with the raw
    # inline "[Source: ...]" text instead of cite() markers, and (e) drop definition_and_pathophysiology,
    # disease_activity_measures, extra_articular_disease, differential_diagnosis and clinical_takeaway
    # entirely. Every key is rendered here under its own correct heading with the cite() pattern (never raw
    # source text); the generic handlers above/below are guarded with disease_id != "rheumatoid_arthritis".
    # "real_risk_factors" already matches the existing generic handler correctly and is not re-rendered;
    # "core" renders through the generic handler and its per-item sources (dropped there) are printed below.
    if disease_id == "rheumatoid_arthritis":
        _RA_TOKENS = {"acr": "ACR", "eular": "EULAR", "hla": "HLA", "drb1": "DRB1", "ccp": "CCP", "rf": "RF",
                      "esr": "ESR", "crp": "CRP", "ra": "RA", "mri": "MRI", "das28": "DAS28", "cdai": "CDAI",
                      "sdai": "SDAI", "tnf": "TNF", "il6": "IL-6", "il1": "IL-1", "exra": "ExRA", "ild": "ILD"}

        def _ra_title(k):
            toks = [(_RA_TOKENS.get(t) or t) for t in str(k).replace("_", " ").split()]
            txt = " ".join(toks).strip()
            return txt[:1].upper() + txt[1:]

        def _ra_conf_source(obj):
            if isinstance(obj, dict) and obj.get("source"):
                conf = obj.get("confidence", "")
                line = f"Confidence: {conf} | Source: {cite(obj['source'])}" if conf else f"Source: {cite(obj['source'])}"
                elements.append(Paragraph(line, cite_marker_s))

        def _ra_topic_dict_section(ra_key, ra_heading):
            ra_obj = sym.get(ra_key)
            if not isinstance(ra_obj, dict):
                return
            elements.append(Paragraph(ra_heading, subhead))
            for k3, v3 in ra_obj.items():
                if isinstance(v3, str):
                    elements.append(Paragraph(f"<b>{_ra_title(k3)}:</b> {v3}", body))
                    continue
                if not isinstance(v3, dict):
                    continue
                elements.append(Paragraph(f"<b>{_ra_title(k3)}</b>", body))
                for fk, fv in v3.items():
                    if fk in ("source", "confidence"):
                        continue
                    if isinstance(fv, str):
                        elements.append(Paragraph(fv if fk in ("finding", "framework") else f"<b>{_ra_title(fk)}:</b> {fv}", body))
                    elif isinstance(fv, list):
                        for li in fv:
                            if isinstance(li, str):
                                elements.append(Paragraph(f"• {li}", bullet))
                _ra_conf_source(v3)
            elements.append(Spacer(1, 4))

        _ra_topic_dict_section("definition_and_pathophysiology", "Real definition and pathophysiology -- synovitis, citrullination and autoantibodies (RF, anti-CCP), HLA-DRB1 shared epitope, the TNF/IL-6/IL-1 cytokine axis, pannus and bone erosion, and the preclinical phase:")

        ra_core = sym.get("core")
        if isinstance(ra_core, list):
            elements.append(Paragraph("Real source citations for each core feature:", subhead))
            for ci in ra_core:
                if isinstance(ci, dict) and ci.get("source"):
                    elements.append(Paragraph(f"<b>{ci.get('name', '')}:</b> Source: {cite(ci['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        _ra_topic_dict_section("diagnostic_framework", "Real diagnostic framework -- clinical diagnosis versus classification, ACR/EULAR 2010 and ACR 1987 criteria, anti-CCP/RF accuracy, ESR/CRP pitfalls, radiographs, ultrasound/MRI, seronegative RA and the early-referral rule:")
        _ra_topic_dict_section("disease_activity_measures", "Real disease-activity measures -- DAS28, CDAI, SDAI and the ACR/EULAR remission definitions:")

        ra_exra = sym.get("extra_articular_disease")
        if isinstance(ra_exra, list):
            elements.append(Paragraph("Real extra-articular disease -- nodules, interstitial lung disease, vasculitis, eye, heart, Felty's syndrome and other systemic manifestations:", subhead))
            for item in ra_exra:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• <b>{item.get('name', '')}:</b> {item.get('note', '')}", bullet))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

        _ra_topic_dict_section("differential_diagnosis", "Real differential diagnosis -- osteoarthritis, psoriatic arthritis, lupus, gout/CPPD, chikungunya and other viral arthritis (India-relevant), polymyalgia rheumatica, reactive arthritis and the discriminating work-up:")
        _ra_topic_dict_section("epidemiology", "Real epidemiology -- global burden, incidence and sex ratio, prevalence by method and setting, and India-specific data and registry status:")
        _ra_topic_dict_section("natural_history", "Real natural history -- erosions, the window of opportunity, remission and flares, disability and work, prognostic factors, mortality and cardiovascular risk:")

        ra_rf = sym.get("red_flags")
        if isinstance(ra_rf, list) and ra_rf:
            elements.append(Paragraph("RED FLAGS — escalate to a real doctor immediately:", subhead))
            ra_rf_style = ParagraphStyle("rf_ra", parent=bullet, textColor=CORAL)
            for rf in ra_rf:
                if not isinstance(rf, str):
                    continue
                m_src = re.search(r"\s*\[Source:\s*(.*)\]\s*$", rf, flags=re.S)
                rf_text = rf[:m_src.start()] if m_src else rf
                elements.append(Paragraph(f"• {rf_text}", ra_rf_style))
                if m_src:
                    elements.append(Paragraph(f"Source: {cite(m_src.group(1).strip())}", cite_marker_s))
            elements.append(Spacer(1, 4))

        ra_ct = sym.get("clinical_takeaway")
        if isinstance(ra_ct, list) and ra_ct and isinstance(ra_ct[0], dict) and "point" in ra_ct[0]:
            elements.append(Paragraph("Real clinical takeaway:", subhead))
            for item in ra_ct:
                if not isinstance(item, dict):
                    continue
                elements.append(Paragraph(f"• {item.get('point', '')}", bullet))
                if item.get("why"):
                    elements.append(Paragraph(item["why"], body))
                if item.get("source"):
                    elements.append(Paragraph(f"Source: {cite(item['source'])}", cite_marker_s))
            elements.append(Spacer(1, 4))

    dfw = sym.get("diagnostic_framework")
    if dfw and disease_id == "viral_hepatitis":
        # Already fully rendered above (Viral Hepatitis-specific structured blocks) with its own
        # correct heading -- must NOT fall into the Jones-Criteria/TSH/Lake-Louise-Dallas chain
        # below, which would mislabel it and silently drop its string-valued fields (the catch-all
        # `elif dfw:` branch only renders dict-valued sub-keys).
        pass
    elif dfw and disease_id == "peptic_ulcer_disease":
        # Already fully rendered above (Peptic Ulcer Disease-specific block) with its own correct
        # heading -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below.
        pass
    elif dfw and disease_id == "inflammatory_bowel_disease":
        # Already fully rendered above (Inflammatory Bowel Disease-specific block) with its own
        # correct heading -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below.
        pass
    elif dfw and disease_id == "gerd":
        # Already fully rendered above (GERD-specific structured block) with its own correct heading
        # (empiric PPI trial / upper endoscopy / Lyon Consensus pH-impedance monitoring / HRM) -- must
        # NOT fall into the Lake-Louise-Dallas myocarditis catch-all below.
        pass
    elif dfw and disease_id == "acute_pancreatitis":
        # Already fully rendered above (Acute Pancreatitis-specific structured block) with its own
        # correct heading (Revised Atlanta Classification 2012 diagnostic criteria, lipase vs amylase)
        # -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below, which would also
        # silently drop this entry's string-valued "lipase_vs_amylase" and top-level "source" fields.
        pass
    elif dfw and disease_id == "celiac_disease":
        # Already fully rendered above (Celiac Disease-specific structured block) with its own correct
        # heading (serology, confirmatory EMA, duodenal biopsy, ESPGHAN biopsy-free pathway, HLA typing)
        # -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below, which would mislabel
        # it and silently drop its string-valued fields.
        pass
    elif dfw and disease_id == "parkinsons_disease":
        # Already fully rendered by the Parkinson's-disease-specific block directly above with its own
        # correct heading -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below, which
        # would mislabel it under a myocarditis heading and drop its string-valued and list-valued fields.
        pass
    elif dfw and disease_id == "alzheimers_disease":
        # Already fully rendered above (Alzheimer's disease-specific block) with its own correct
        # heading (NIA-AA 2011 criteria, 2024 biological-vs-clinical-biological debate, DSM-5, CSF/PET/
        # plasma p-tau217 biomarkers, MRI, MMSE/MoCA, autopsy gold standard) -- must NOT fall into the
        # Lake-Louise-Dallas myocarditis catch-all below, which would mislabel it and silently drop its
        # string-valued fields.
        pass
    elif dfw and disease_id == "epilepsy":
        # Already fully rendered above (Epilepsy-specific structured block) with its own correct
        # heading (EEG, video-EEG/PNES, MRI brain) -- must NOT fall into the Lake-Louise-Dallas
        # myocarditis catch-all below, which would mislabel it as "Lake Louise Criteria & Dallas
        # Histopathological Criteria" and duplicate the content under the wrong heading.
        pass
    elif dfw and disease_id == "multiple_sclerosis":
        # Already fully rendered above (Multiple Sclerosis-specific structured block) with its own
        # correct heading (McDonald criteria, MRI dissemination, CSF oligoclonal bands, VEP, NMOSD/
        # MOGAD differential) -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below,
        # which would mislabel it and drop the per-topic confidence field.
        pass
    elif dfw and disease_id == "guillain_barre_syndrome":
        # Already fully rendered above (Guillain-Barré Syndrome-specific structured block) with its own
        # correct heading (NINDS/Asbury-Cornblath criteria, Brighton Collaboration levels, CSF
        # albuminocytologic dissociation, nerve conduction studies, MRI) -- must NOT fall into the
        # Lake-Louise-Dallas myocarditis catch-all below, which would mislabel it and drop the per-topic
        # confidence field.
        pass
    elif dfw and disease_id == "bacterial_meningitis":
        # Already fully rendered above (Bacterial Meningitis-specific structured block) with its own
        # correct heading (classic triad sensitivity, CSF patterns, Gram stain/culture, PCR, CT-before-LP
        # indications) -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below, which
        # would mislabel it and drop the per-topic confidence field.
        pass
    elif dfw and disease_id == "myasthenia_gravis":
        # Already fully rendered above (Myasthenia Gravis-specific structured block) with its own
        # correct heading (bedside clinical tests, AChR/MuSK/LRP4 serology, repetitive nerve
        # stimulation, single-fiber EMG, edrophonium/Tensilon test, thymoma imaging) -- must NOT fall
        # into the Lake-Louise-Dallas myocarditis catch-all below, which would mislabel it and drop the
        # per-topic confidence field.
        pass
    elif dfw and disease_id == "amyotrophic_lateral_sclerosis":
        # Already fully rendered above (Amyotrophic Lateral Sclerosis-specific structured block) with
        # its own correct heading (clinical diagnosis, revised El Escorial, Awaji and Gold Coast
        # criteria, EMG, neuroimaging, genetic testing, mimics) -- must NOT fall into the
        # Lake-Louise-Dallas myocarditis catch-all below, which would mislabel it and drop the
        # per-topic confidence field and the criteria category lists.
        pass
    elif dfw and disease_id == "rheumatoid_arthritis":
        # Already fully rendered above (Rheumatoid-Arthritis-specific structured block) with its own
        # correct heading (clinical diagnosis vs classification, ACR/EULAR 2010 and 1987 criteria, anti-CCP/RF
        # accuracy, ESR/CRP pitfalls, radiographs, ultrasound/MRI, seronegative RA, early-referral rule) --
        # must NOT fall into the Lake-Louise-Dallas myocarditis catch-all below, which would mislabel it.
        pass
    elif dfw and disease_id == "gout":
        # Already fully rendered above (Gout-specific structured block) with its own correct heading
        # (clinical diagnosis, synovial fluid MSU crystals, ACR/EULAR 2015 criteria, DECT, ultrasound,
        # serum urate limits, radiographs, comorbidity assessment) -- must NOT fall into the
        # Lake-Louise-Dallas myocarditis catch-all below, which would mislabel it.
        pass
    elif dfw and "jones_criteria_2015_revision" in dfw:
        # Jones Criteria (2015 revision) + WHF 2012 echocardiographic-carditis shape
        # (acute_rheumatic_fever) -- distinct from the Lake Louise/Dallas shape below
        elements.append(Paragraph("Real diagnostic framework - Jones Criteria (2015 revision) & WHF 2012 Echocardiographic Criteria:", subhead))
        for k, v in dfw.items():
            render_generic_kv(k, v, depth=0)
        elements.append(Spacer(1, 4))
    elif dfw and "tsh_first_line" in dfw:
        elements.append(Paragraph("Real diagnostic framework -- TSH, Free T4/T3, Thyroid Autoantibodies, RAIU Scan:", subhead))
        for k, v in dfw.items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))
    elif dfw and disease_id == "antiphospholipid_syndrome":
        # Rendered instead, correctly and in full (its {summary, findings (list of str),
        # citations (list of str)} shape), by the antiphospholipid_syndrome-specific block
        # further below -- must NOT fall into the Lake-Louise-Dallas myocarditis catch-all
        # below, which expects dict-valued sub-keys and would silently drop this shape entirely
        # (list-valued "findings"/"citations" both fail its `isinstance(v, dict)` check).
        pass
    elif dfw and isinstance(dfw, str):
        elements.append(Paragraph("Real diagnostic framework:", subhead))
        elements.append(Paragraph(dfw, body))
    elif dfw:
        elements.append(Paragraph("Real diagnostic framework - Lake Louise Criteria & Dallas Histopathological Criteria:", subhead))
        for k, v in dfw.items():
            if not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            for sk, sv in v.items():
                if sk == "source" or not isinstance(sv, str):
                    continue
                elements.append(Paragraph(sv, body))
            if v.get("source"):
                elements.append(Paragraph(f"Source: {cite(v['source'])}", cite_marker_s))

    if sym.get("clinical_classification_phenotypes"):
        ccp = sym["clinical_classification_phenotypes"]
        elements.append(Paragraph("Real clinical classification - phenotypes by tempo/severity:", subhead))
        if ccp.get("note"):
            elements.append(Paragraph(ccp["note"], body))
        for k, v in ccp.items():
            if k == "note" or not isinstance(v, dict):
                continue
            elements.append(Paragraph(k.replace('_', ' ').title() + ":", subhead))
            for sk, sv in v.items():
                if sk == "source" or not isinstance(sv, str):
                    continue
                elements.append(Paragraph(f"• <b>{sk.replace('_', ' ').title()}:</b> {sv}", bullet))
            if v.get("source"):
                elements.append(Paragraph(f"Source: {cite(v['source'])}", cite_marker_s))

    if sym.get("differential_giant_cell_myocarditis_vs_cardiac_sarcoidosis"):
        render_flat_dict_section("differential_giant_cell_myocarditis_vs_cardiac_sarcoidosis",
                                  "Differential: Giant Cell Myocarditis vs Cardiac Sarcoidosis (real):")

    if sym.get("sudden_cardiac_death_in_athletes"):
        scda = sym["sudden_cardiac_death_in_athletes"]
        elements.append(Paragraph("Real data - Sudden Cardiac Death in Athletes (myocarditis as a cause):", subhead))
        if scda.get("data"):
            elements.append(Paragraph(scda["data"], body))
        if scda.get("source"):
            elements.append(Paragraph(f"Source: {cite(scda['source'])}", cite_marker_s))

    sg = sym.get("severity_gradient")
    if sg:
        if isinstance(sg, list):
            elements.append(Paragraph("<b>Severity gradient:</b>", body))
            add_bullets(sg)
        else:
            elements.append(Paragraph(f"<b>Severity gradient:</b> {sg}", body))

    if sym.get("red_flags") and disease_id != "rheumatoid_arthritis":
        elements.append(Paragraph("RED FLAGS — escalate to a real doctor immediately:", subhead))
        rf_data = sym["red_flags"]
        rf_style = ParagraphStyle("rf", parent=bullet, textColor=CORAL)
        if isinstance(rf_data, dict):
            for rfk, rfv in rf_data.items():
                if rfk in ("source", "confidence") or not isinstance(rfv, str):
                    continue
                elements.append(Paragraph(f"• <b>{rfk.replace('_', ' ').title()}:</b> {rfv}", rf_style))
            if rf_data.get("source"):
                elements.append(Paragraph(f"Confidence: {rf_data.get('confidence', '')} | Source: {cite(rf_data['source'])}", cite_marker_s))
        else:
            for rf in rf_data:
                elements.append(Paragraph(f"• {rf}", rf_style))
            if sym.get("red_flags_source"):
                elements.append(Paragraph(f"Source: {cite(sym['red_flags_source'])}", cite_marker_s))

    if sym.get("asthma_copd_overlap_cross_reference"):
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"<i>Asthma-COPD Overlap cross-reference: {sym['asthma_copd_overlap_cross_reference']}</i>", small_grey))

    # ---- Obesity/Metabolic Syndrome-specific structured blocks ----
    if isinstance(sym.get("core_presentation"), dict) and isinstance(sym["core_presentation"].get("acanthosis_nigricans"), dict):
        an = sym["core_presentation"]["acanthosis_nigricans"]
        elements.append(Paragraph("Core presentation -- Acanthosis Nigricans (real insulin-resistance marker):", subhead))
        if an.get("finding"):
            elements.append(Paragraph(an["finding"], body))
        if an.get("source"):
            elements.append(Paragraph(f"Confidence: {an.get('confidence', '')} | Source: {cite(an['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    # ---- PCOS-specific structured blocks ----
    # (diagnostic_criteria and pathophysiology are already rendered generically above with
    # correct disease-agnostic headings ("Real diagnostic criteria:" / "Real pathophysiology:"),
    # so are not repeated here to avoid duplication.)
    if disease_id == "pcos":
        if sym.get("phenotype_classification"):
            render_generic_kv("Real Rotterdam phenotype classification (Phenotypes A-D)", sym["phenotype_classification"])
            elements.append(Spacer(1, 4))
        if sym.get("diagnostic_workup"):
            render_generic_kv("diagnostic_workup", sym["diagnostic_workup"])
            elements.append(Spacer(1, 4))
        if isinstance(sym.get("associated_long_term_risks_cross_reference"), list):
            elements.append(Paragraph("Real associated long-term risks (cross-referenced to other entries in this knowledge base):", subhead))
            add_bullets(sym["associated_long_term_risks_cross_reference"])
            elements.append(Spacer(1, 4))

    if sym.get("classification_bmi"):
        elements.append(Paragraph("Real BMI classification (WHO Standard & Asia-Pacific):", subhead))
        for k, v in sym["classification_bmi"].items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if sym.get("waist_circumference_thresholds"):
        elements.append(Paragraph("Real waist circumference thresholds (Western NCEP-ATP-III & India/Asian-specific):", subhead))
        for k, v in sym["waist_circumference_thresholds"].items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if sym.get("metabolic_syndrome_diagnostic_criteria"):
        elements.append(Paragraph("Real metabolic syndrome diagnostic criteria (NCEP ATP III / IDF):", subhead))
        for k, v in sym["metabolic_syndrome_diagnostic_criteria"].items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if sym.get("etiological_classification"):
        elements.append(Paragraph("Real etiological classification:", subhead))
        for k, v in sym["etiological_classification"].items():
            render_generic_kv(k, v)
        elements.append(Spacer(1, 4))

    if sym.get("associated_comorbidities_cross_reference") and isinstance(sym["associated_comorbidities_cross_reference"], list):
        elements.append(Paragraph("Real associated comorbidities (cross-referenced to other entries in this knowledge base):", subhead))
        add_bullets(sym["associated_comorbidities_cross_reference"])
        elements.append(Spacer(1, 4))

    if (disease_id != "osteoporosis" and sym.get("epidemiology") and isinstance(sym["epidemiology"], dict)
            and "global" in sym["epidemiology"] and "india" in sym["epidemiology"]):
        epi5 = sym["epidemiology"]
        elements.append(Paragraph("Real epidemiology (Global & India):", subhead))
        for ek, elabel in (("global", "Global"), ("india", "India")):
            blk = epi5.get(ek, {})
            if not isinstance(blk, dict):
                continue
            if blk.get("finding"):
                elements.append(Paragraph(f"<b>{elabel}:</b> {blk['finding']}", body))
            if blk.get("double_burden_note"):
                elements.append(Paragraph(blk["double_burden_note"], body))
            if blk.get("source"):
                elements.append(Paragraph(f"Confidence: {blk.get('confidence', '')} | Source: {cite(blk['source'])}", cite_marker_s))
        elements.append(Spacer(1, 4))

    if sym.get("not_included_no_real_evidence"):
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<i>{sym['not_included_no_real_evidence']}</i>", small_grey))

    render_references()
    elements.append(PageBreak())

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         topMargin=1.4 * cm, bottomMargin=1.4 * cm,
                         leftMargin=1.6 * cm, rightMargin=1.6 * cm)
doc.build(elements)
print(f"Wrote {OUT_PDF}")
