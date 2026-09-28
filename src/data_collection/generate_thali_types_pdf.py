"""
BalanceAI — India Thali Types Compendium PDF
Compiles the LUNCH and DINNER thali-structure research
(data/lunch_research/thali_types.json + data/dinner_research/thali_types.json)
into one PDF: every regional plate type, its core/optional slots, serving style,
and the ICMR-NIN 2020 official standard-plate numbers for both meals.
"""
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, ListFlowable, ListItem)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ROOT = Path("/home/abhay/Downloads/medical/balanceai")
LUNCH_JSON = ROOT / "data" / "lunch_research" / "thali_types.json"
DINNER_JSON = ROOT / "data" / "dinner_research" / "thali_types.json"
OUT_PDF = ROOT / "data" / "BalanceAI_India_Thali_Types_Compendium.pdf"

GREEN = colors.HexColor("#1d5c3d")
DARK = colors.HexColor("#0d1b1e")
LIGHT = colors.HexColor("#eef7f2")
BORDER = colors.HexColor("#e4e7e2")
AMBER = colors.HexColor("#b45309")

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=GREEN, fontSize=20)
h2 = ParagraphStyle("h2", parent=styles["Heading1"], textColor=colors.white, fontSize=16,
                     spaceBefore=0, spaceAfter=0, backColor=GREEN, borderPadding=8)
plate_name = ParagraphStyle("platename", parent=styles["Heading3"], textColor=GREEN, fontSize=13, spaceBefore=12, spaceAfter=1)
meta = ParagraphStyle("meta", parent=styles["BodyText"], fontSize=8.5, textColor=colors.grey, spaceAfter=3)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
label = ParagraphStyle("label", parent=styles["BodyText"], fontSize=9, textColor=DARK, spaceBefore=4, fontName="Helvetica-Bold")
note_style = ParagraphStyle("note", parent=body, fontSize=8, textColor=colors.grey)

elements = []
elements.append(Paragraph("BalanceAI — India Thali Types Compendium", h1))
elements.append(Paragraph(
    "How a real Indian lunch and dinner plate is actually structured, region by region — "
    "the food-category slots that appear on it (core vs optional), serving style, and how dinner "
    "differs from lunch. Includes the ICMR-NIN 2020 official standard-plate gram values for both meals.",
    body,
))
elements.append(Spacer(1, 10))


def render_icmr_table(icmr, meal_label):
    elements.append(Paragraph(f"ICMR-NIN 2020 Standard Plate — {meal_label}", label))
    elements.append(Paragraph(f"<i>Source: {icmr.get('source','')}</i>", note_style))
    rows = [["Group", "Man", "Woman"]]
    man = icmr.get("sedentary_man_lunch") or icmr.get("sedentary_man") or {}
    woman = icmr.get("sedentary_woman_lunch") or icmr.get("sedentary_woman") or {}
    # pair up "_g"/"_form" keys generically
    keys = [k[:-2] for k in man.keys() if k.endswith("_g")]
    for k in keys:
        g = man.get(f"{k}_g", "")
        form = man.get(f"{k}_form", "")
        gw = woman.get(f"{k}_g", "")
        formw = woman.get(f"{k}_form", "")
        label_txt = k.replace("_", " ").title()
        rows.append([label_txt, f"{g}g ({form})" if form else f"{g}g", f"{gw}g ({formw})" if formw else f"{gw}g"])
    t = Table(rows, colWidths=[3.5 * cm, 6.5 * cm, 6.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))


def render_plate_type(p, meal):
    elements.append(Paragraph(p["name"], plate_name))
    elements.append(Paragraph(f"<b>Region:</b> {p.get('region','')} &nbsp;|&nbsp; <b>Serving style:</b> {p.get('serving_style','')}", meta))
    if p.get("description"):
        elements.append(Paragraph(p["description"], body))
    core = ", ".join(p.get("core_slots", []))
    opt = ", ".join(p.get("optional_slots", []))
    if core:
        elements.append(Paragraph(f"<b>Core slots:</b> {core}", body))
    if opt:
        elements.append(Paragraph(f"<b>Optional slots:</b> {opt}", body))
    if meal == "dinner" and p.get("difference_from_lunch"):
        elements.append(Paragraph(f"<b>Vs. lunch:</b> {p['difference_from_lunch']}", body))
    if p.get("verified"):
        elements.append(Paragraph(f"<i>{p['verified'].replace('_',' ')}</i>", note_style))
    elements.append(Spacer(1, 6))


# ---- LUNCH ----
lunch = json.loads(LUNCH_JSON.read_text())
elements.append(Paragraph("&nbsp;Lunch Thali Types", h2))
elements.append(Spacer(1, 6))
if lunch.get("note"):
    elements.append(Paragraph(f"<i>{lunch['note']}</i>", note_style))
    elements.append(Spacer(1, 6))
render_icmr_table(lunch.get("icmr_standard_plate", {}), "Lunch")
for p in lunch.get("thali_types", []):
    render_plate_type(p, "lunch")
elements.append(PageBreak())

# ---- DINNER ----
dinner = json.loads(DINNER_JSON.read_text())
elements.append(Paragraph("&nbsp;Dinner Thali Types", h2))
elements.append(Spacer(1, 6))
if dinner.get("note"):
    elements.append(Paragraph(f"<i>{dinner['note']}</i>", note_style))
    elements.append(Spacer(1, 6))
render_icmr_table(dinner.get("icmr_standard_plate_dinner", {}), "Dinner")
for p in dinner.get("dinner_types", []):
    render_plate_type(p, "dinner")

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                         topMargin=1.6 * cm, bottomMargin=1.6 * cm)
doc.build(elements)
print(f"Lunch types: {len(lunch.get('thali_types', []))}, Dinner types: {len(dinner.get('dinner_types', []))}")
print(f"PDF saved -> {OUT_PDF}")
