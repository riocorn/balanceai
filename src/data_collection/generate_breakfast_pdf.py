"""
BalanceAI — India Breakfast Dish Compendium PDF
Compiles all 6 regional breakfast-research JSON files (data/breakfast_research/*.json)
into one PDF: every dish, states, diet, full ingredients, and full preparation method.
Seed data for the AI Recipe Generator's template corpus.
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
RESEARCH_DIR = ROOT / "data" / "breakfast_research"
OUT_PDF = ROOT / "data" / "BalanceAI_India_Breakfast_Compendium.pdf"

REGION_ORDER = ["north.json", "south.json", "east.json", "west.json", "northeast.json", "central_islands.json"]

GREEN = colors.HexColor("#1d5c3d")
DARK = colors.HexColor("#0d1b1e")
LIGHT = colors.HexColor("#eef7f2")
BORDER = colors.HexColor("#e4e7e2")
AMBER = colors.HexColor("#b45309")

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=GREEN, fontSize=20)
h2 = ParagraphStyle("h2", parent=styles["Heading1"], textColor=colors.white, fontSize=16,
                     spaceBefore=0, spaceAfter=0, backColor=GREEN, borderPadding=8)
h3 = ParagraphStyle("h3", parent=styles["Heading2"], textColor=DARK, fontSize=13, spaceBefore=14, spaceAfter=2)
dish_name = ParagraphStyle("dishname", parent=styles["Heading3"], textColor=GREEN, fontSize=12, spaceBefore=10, spaceAfter=1)
meta = ParagraphStyle("meta", parent=styles["BodyText"], fontSize=8.5, textColor=colors.grey, spaceAfter=3)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
label = ParagraphStyle("label", parent=styles["BodyText"], fontSize=9, textColor=DARK, spaceBefore=4, fontName="Helvetica-Bold")
step = ParagraphStyle("step", parent=styles["BodyText"], fontSize=9, leading=12.5, leftIndent=10)

DIET_COLOR = {"veg": GREEN, "vegan": GREEN, "eggetarian": AMBER, "non_veg": colors.HexColor("#b91c1c")}

elements = []
elements.append(Paragraph("BalanceAI — India Breakfast Dish Compendium", h1))
elements.append(Paragraph(
    "Complete state-by-state research of traditional Indian breakfast dishes — every dish with "
    "its state(s) of origin, diet type, full ingredient list, and complete step-by-step preparation "
    "method. Seed corpus for the AI Recipe Generator (Recipe Maker AI's template + slot-substitution "
    "engine).", body,
))
elements.append(Spacer(1, 6))

# Load all regions, compute totals
all_data = []
total_dishes = 0
for fname in REGION_ORDER:
    d = json.loads((RESEARCH_DIR / fname).read_text())
    all_data.append(d)
    total_dishes += len(d["dishes"])

elements.append(Paragraph(
    f"<b>{total_dishes} dishes</b> across <b>{sum(len(d['states_covered']) for d in all_data)} states/UTs</b> "
    f"(all 28 states + 8 union territories of India), organized by region.", body,
))
elements.append(Spacer(1, 10))

# Summary table
summary_rows = [["Region", "States/UTs Covered", "Dishes"]]
for d in all_data:
    states_cell = Paragraph(", ".join(d["states_covered"]), ParagraphStyle("statecell", parent=body, fontSize=8, leading=10))
    summary_rows.append([d["region"], states_cell, str(len(d["dishes"]))])
t = Table(summary_rows, colWidths=[3.2 * cm, 11.5 * cm, 2 * cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), GREEN),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
elements.append(t)
elements.append(PageBreak())

for region_data in all_data:
    region_name = region_data["region"]
    elements.append(Paragraph(f"&nbsp;{region_name} India — {len(region_data['dishes'])} dishes", h2))
    elements.append(Spacer(1, 4))
    if region_data.get("note"):
        elements.append(Paragraph(f"<i>{region_data['note']}</i>",
                                   ParagraphStyle("note", parent=body, fontSize=8, textColor=colors.grey)))
        elements.append(Spacer(1, 6))

    for dish in region_data["dishes"]:
        name = dish.get("name", "")
        local = dish.get("local_name", "")
        diet = dish.get("diet", "veg")
        dstates = ", ".join(dish.get("states", []))
        ingredients = ", ".join(dish.get("ingredients", []))
        desc = dish.get("description", "")
        method = dish.get("method", [])

        title_txt = f"{name}" + (f"  <font size=9 color='#6b7280'>({local})</font>" if local and local != name else "")
        elements.append(Paragraph(title_txt, dish_name))
        elements.append(Paragraph(
            f"<font color='{DIET_COLOR.get(diet, GREEN).hexval()}'><b>{diet.upper()}</b></font> &nbsp;|&nbsp; States: {dstates}",
            meta,
        ))
        if desc:
            elements.append(Paragraph(desc, body))
        if ingredients:
            elements.append(Paragraph("Ingredients:", label))
            elements.append(Paragraph(ingredients, body))
        if method:
            elements.append(Paragraph("Method:", label))
            items = [ListItem(Paragraph(s, step), leftIndent=12) for s in method]
            elements.append(ListFlowable(items, bulletType="1", start=1, leftIndent=14, bulletFontSize=9))
        elements.append(Spacer(1, 6))

    elements.append(PageBreak())

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                         topMargin=1.6 * cm, bottomMargin=1.6 * cm)
doc.build(elements)
print(f"Total dishes: {total_dishes}")
print(f"PDF saved -> {OUT_PDF}")
