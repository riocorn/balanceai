"""
BalanceAI Sense — Device Design Document (v2)
Compiles all 8 engineering-literature-survey JSON files (4 initial + 4 gap-closing)
into one document: the corrected device architecture, what changed from v1 and why,
each design decision's real published evidence, and honest open risks.
"""
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ROOT = Path("/home/abhay/Downloads/medical/balanceai")
SRC_DIR = ROOT / "data" / "device_engineering_survey"
OUT_PDF = ROOT / "data" / "BalanceAI_Sense_Device_Design.pdf"

GREEN = colors.HexColor("#1d5c3d")
DARK = colors.HexColor("#0d1b1e")
LIGHT = colors.HexColor("#eef7f2")
BORDER = colors.HexColor("#e4e7e2")
AMBER = colors.HexColor("#b45309")
RED = colors.HexColor("#b91c1c")

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=GREEN, fontSize=20)
h2 = ParagraphStyle("h2", parent=styles["Heading1"], textColor=colors.white, fontSize=15,
                     backColor=GREEN, borderPadding=7)
h3 = ParagraphStyle("h3", parent=styles["Heading2"], textColor=DARK, fontSize=12.5, spaceBefore=12, spaceAfter=3)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8.5, leading=11.5, textColor=colors.HexColor("#374151"))
cite = ParagraphStyle("cite", parent=styles["BodyText"], fontSize=7.8, leading=10, textColor=colors.HexColor("#6b7280"), leftIndent=10)
riskstyle = ParagraphStyle("risk", parent=styles["BodyText"], fontSize=9, leading=12.5, textColor=RED, leftIndent=6)
rec = ParagraphStyle("rec", parent=styles["BodyText"], fontSize=9, leading=12.5, textColor=colors.HexColor("#065f46"), leftIndent=6)
changed = ParagraphStyle("changed", parent=styles["BodyText"], fontSize=9.3, leading=13, textColor=colors.HexColor("#92400e"), leftIndent=6)
cell_style = ParagraphStyle("cell", parent=body, fontSize=7.6, leading=9.8)
hdr_style = ParagraphStyle("hdr", parent=cell_style, textColor=colors.white, fontName="Helvetica-Bold")

def P(txt, style=cell_style):
    return Paragraph(txt.replace("\n", "<br/>"), style)

elements = []
elements.append(Paragraph("BalanceAI Sense — Device Design (v2)", h1))
elements.append(Paragraph(
    "A handheld, multi-probe device covering real, evidence-grounded non-invasive sensing for as "
    "many nutrients as current published science actually supports — corrected after a second, "
    "gap-closing literature pass. Every claim below is either a real citation or an explicit "
    "extrapolation flagged as such.", body,
))
elements.append(Spacer(1, 10))

# ── What changed from v1 ──
elements.append(Paragraph("What Changed From v1 — Corrections From Deeper Research", h3))
changes = [
    "Sweat module downgraded from an assumed “13 simultaneous channels” to the real published "
    "ceiling of 4-5. No device anywhere has demonstrated 13 at once — v1's claim did not survive scrutiny.",
    "Sweat module is now two real, independently-proven pieces, not one imagined 13-channel array: "
    "(a) a real 4-channel colorimetric chip already demonstrated together — Vitamin C, Calcium, Zinc, "
    "Iron (Kim et al.) — and (b) Folate (B9), added as a 5th channel using separate real electrochemical "
    "sensor evidence (r=0.849 sweat-serum) — this combination itself is not yet published, flagged as extrapolation.",
    "B1, B2, Vitamin D, Magnesium, Potassium, Vitamin E, B6, Copper move OUT of the v1 hardware claim "
    "— each has real individual sensing research, but not proven in combination with the others at the "
    "4-5 channel ceiling. They fall back to AI-estimation for v1, real hardware candidates for v2/v3.",
    "New real addition: Iodine, via a smartphone-camera-readable urinary colorimetric paper strip — "
    "found in the second-pass search. Output is categorical (deficient/adequate/excess), not a continuous "
    "number, and the strip has a documented contamination-artifact risk.",
    "Dilution-normalization method corrected: the real B9 paper used real-time pH + ionic-strength "
    "monitoring, not a separate Na/Cl reference channel as v1 assumed. This is validated for exactly "
    "one vitamin (B9) — not confirmed for Vitamin C/Calcium/Zinc/Iron in the same session.",
    "Vitamin K stays finger-transmission-only, now for a stronger reason: reflective PPG has a real, "
    "documented higher noise floor, and Vitamin K's APG math (a second derivative of the pulse wave) "
    "amplifies that noise — not just “unproven,” genuinely riskier by mechanism.",
    "Wescor's 15 µL minimum sweat volume spec: verified correct via a peer-reviewed source (was "
    "flagged as a possible unit error in v1; it was not an error).",
    "Repeat weekly use on the same skin site: real long-term precedent found — home hyperhidrosis "
    "iontophoresis is used for years (avg 14 months) with no long-term skin damage. Our device's real "
    "exposure (5-6 min, once every 5-7 days) is smaller on every axis than this precedent.",
]
for c in changes:
    elements.append(Paragraph(f"&#8226; {c}", changed))
elements.append(Spacer(1, 10))

# ── Architecture overview ──
elements.append(Paragraph("Device Architecture (v2) — 4 Modules, 1 Housing", h3))
arch_rows = [
    [P("Module", hdr_style), P("Nutrients Covered", hdr_style), P("Mechanism", hdr_style), P("Session Time", hdr_style)],
    [P("Sweat module — Tier 0\n(proven together)"), P("Vitamin C, Calcium, Zinc, Iron (4)"),
     P("Iontophoretic induction (1.5mA, 5 min,\nreal CF-testing spec) + 4-channel\ncolorimetric microfluidic chip (Kim et al.)"), P("~5-6 min")],
    [P("Sweat module — Tier 1\n(strong evidence, unproven combo)"), P("Folate / B9 (1)"),
     P("Electrochemical channel added to the same\nsample; pH + ionic-strength normalization\n(validated for B9 only)"), P("(same session)")],
    [P("Optical module\n(shared chip, 2 openings)"), P("Vitamin A (flat window, reflectance)\nVitamin K (finger slot, transmission) (2)"),
     P("One optoelectronic chip (410-940nm) drives\nboth: flat contact pad for reflectance,\nfinger-insertion slot for PPG/APG (kept separate—\nreflection mode unproven + noisier for VitK math)"), P("~45 sec")],
    [P("Strip-read module"), P("Phosphorus, Iodine (2)"),
     P("Two disposable colorimetric strips (saliva,\nurine), same optical module reads both\nafter their reaction time; Iodine = categorical result"), P("~2 min")],
]
t = Table(arch_rows, colWidths=[3.0*cm, 4.6*cm, 6.7*cm, 2.0*cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), GREEN), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 7.6),
    ("GRID", (0,0), (-1,-1), 0.5, BORDER), ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
]))
elements.append(t)
elements.append(Spacer(1, 6))
elements.append(Paragraph(
    "<b>Real-hardware total: 9 nutrients</b> (Vitamin C, Calcium, Zinc, Iron, Folate, Vitamin A, "
    "Vitamin K, Phosphorus, Iodine) — down from v1's overstated 17, but every one of these 9 now "
    "has a real citation with no unproven combination assumed beyond the single Tier-1 addition. "
    "<b>Remaining 16 nutrients are AI-estimated</b>, with confidence boosted for correlated pairs where "
    "real evidence supports it (Iron↔B12 co-occurrence is the strongest: 22.6% in Indian adolescent "
    "studies — and Iron is one of our real-measured 9, so it can genuinely inform B12's estimate).", body,
))
elements.append(Spacer(1, 6))
elements.append(Paragraph(
    "Not continuously worn — handheld, used once every 5-7 days (~9 min total session: skin touch "
    "→ finger slot → two strips). All readings sync to the app, which fuses real + AI-estimated "
    "nutrients into one report, always labeling which is which.", small,
))
elements.append(PageBreak())

# ── Permanent dead ends (nowhere in the world) ──
elements.append(Paragraph("Confirmed Dead Ends — No Research Found Anywhere, Even After a Second Pass", h3))
elements.append(Paragraph(
    "Niacin (B3), Pantothenic Acid (B5), Biotin (B7), Manganese, Chromium — genuinely zero published "
    "non-invasive sensing research exists for these 5, confirmed by two independent search passes. "
    "B3/B5 have a specific reason: their chemistry is “not electroactive,” so standard sensor designs "
    "cannot target them at all, not just “not yet built.”", body,
))
elements.append(Spacer(1, 4))
elements.append(Paragraph(
    "Two nutrients have real but non-consumer options, noted for v3+, not this device: <b>Vitamin B12</b> "
    "— a real 13C-propionate breath test exists (measures B12-dependent enzyme activity), but needs a "
    "swallowed tracer and clinical/research equipment. <b>Selenium</b> — hair ICP-MS analysis is a real, "
    "used lab method with moderate serum correlation, but it's a mail-in lab test, not point-of-care, "
    "and has no established clinical reference range.", body,
))
elements.append(PageBreak())

GROUP_ORDER = ["iontophoresis.json", "multi_analyte_sweat.json", "dual_mode_optical.json", "nutrient_correlations.json",
               "scaling_multi_analyte.json", "repeat_use_safety.json", "vitk_reflection_and_specs.json", "dead_ends_second_pass.json"]

for fname in GROUP_ORDER:
    path = SRC_DIR / fname
    if not path.exists():
        continue
    d = json.loads(path.read_text())
    elements.append(Paragraph(f"&nbsp;{d['topic']}", h2))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Evidence", h3))
    for f in d.get("findings", []):
        conf_color = {"established": GREEN, "emerging": AMBER, "uncertain": RED}.get(f.get("confidence",""), DARK)
        elements.append(Paragraph(
            f"&bull; {f.get('claim','')} <font size=7 color='{conf_color.hexval()}'>[{f.get('confidence','')}]</font>",
            small,
        ))
        if f.get("evidence"):
            elements.append(Paragraph(f.get("evidence",""), cite))
        if f.get("citation_title"):
            ct = f["citation_title"]
            if f.get("citation_url"):
                ct = f'<link href="{f["citation_url"]}">{ct}</link>'
            elements.append(Paragraph(ct, cite))

    if d.get("design_recommendations"):
        elements.append(Paragraph("Design Recommendations", h3))
        for r in d["design_recommendations"]:
            elements.append(Paragraph(f"&#10003; {r}", rec))

    if d.get("open_risks"):
        elements.append(Paragraph("Open Risks", h3))
        for rk in d["open_risks"]:
            elements.append(Paragraph(f"&#9888; {rk}", riskstyle))

    elements.append(PageBreak())

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.6*cm, bottomMargin=1.6*cm)
doc.build(elements)
print(f"PDF saved -> {OUT_PDF}")
