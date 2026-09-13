import json
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ROOT = Path("/home/abhay/Downloads/medical/balanceai")
DATA = json.loads((ROOT / "data/recipe_nutrient_database.json").read_text())
OUT_PDF = ROOT / "data/BalanceAI_800_Recipe_Nutrient_Map.pdf"

GREEN = colors.HexColor("#00a86b")
DARK = colors.HexColor("#0d1b1e")
LIGHT = colors.HexColor("#eafaf3")

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=GREEN, fontSize=20)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=DARK, spaceBefore=10)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=7.5, textColor=colors.grey)
state_hdr = ParagraphStyle("st", parent=styles["Heading3"], textColor=GREEN, fontSize=11, spaceBefore=8)

NUTRIENT_25 = DATA["nutrient_fields"]
SHORT = {
    "vitamin_d":"D","iron":"Fe","vitamin_b12":"B12","zinc":"Zn","calcium":"Ca",
    "magnesium":"Mg","vitamin_c":"C","vitamin_a":"A","folate":"B9","iodine":"I",
    "omega3":"O3","selenium":"Se","vitamin_b6":"B6","potassium":"K","copper":"Cu",
    "vitamin_e":"E","vitamin_b1":"B1","vitamin_b2":"B2","vitamin_b3":"B3",
    "vitamin_b5":"B5","vitamin_b7":"B7","vitamin_k":"K1","phosphorus":"P",
    "manganese":"Mn","chromium":"Cr",
}

recipes = DATA["recipes"]
by_state = {}
for r in recipes:
    by_state.setdefault(r["state"], []).append(r)

elements = []
elements.append(Paragraph("BalanceAI — Full Indian Recipe -> 25-Nutrient Database", h1))
elements.append(Paragraph(
    f"Complete listing: all {DATA['total_entries']} state-linked food/recipe entries across "
    f"{DATA['states']} states, every one of the 25 tracked nutrients, per 100g.", body))
elements.append(Spacer(1, 8))
elements.append(Paragraph("Methodology &amp; Data Sourcing", h2))
elements.append(Paragraph(DATA["source_note"], body))
elements.append(Paragraph(
    f"<b>{DATA['direct_usda_match']}</b> direct USDA SR Legacy matches, "
    f"<b>{DATA['template_decomposed']}</b> composite dishes decomposed into real base "
    f"ingredients at household weights and summed, "
    f"<b>{DATA['fallback_generic_template']}</b> exotic/regional items used a generic "
    f"template (flagged in the Method column below, not hidden).", body))
elements.append(Spacer(1, 4))
elements.append(Paragraph(
    "Units: Ca/Mg/K/P/Fe/Zn/Cu/Mn/C/E/B1-B3/B6 = mg, D = IU, B7/B9/B12/A/Se/I/B5/K1 = mcg, O3 = g.",
    small))
elements.append(PageBreak())

nutrient_cols = list(NUTRIENT_25)
header = ["Item", "Cat"] + [SHORT[n] for n in nutrient_cols] + ["Method"]
col_widths = [3.0*cm, 0.9*cm] + [0.68*cm] * len(nutrient_cols) + [2.6*cm]

CAT_SHORT = {"common_dishes": "Dish", "common_proteins": "Prot", "common_vegetables": "Veg",
             "common_fruits": "Fruit", "dairy": "Dairy"}

for state in sorted(by_state.keys()):
    items = by_state[state]
    elements.append(Paragraph(f"{state.replace('_', ' ')}  ({len(items)} entries)", state_hdr))
    rows = [header]
    for it in items:
        nvals = [f"{it['nutrients_per_100g'].get(n, 0):.1f}" for n in nutrient_cols]
        method_short = it["method"].split(" (")[0]
        rows.append([it["item"].replace("_", " ")[:20], CAT_SHORT.get(it["category"], "?")]
                    + nvals + [method_short])
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 5.4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("ALIGN", (1, 0), (-2, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6))

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=landscape(A4),
                         topMargin=1.1*cm, bottomMargin=1.1*cm,
                         leftMargin=0.9*cm, rightMargin=0.9*cm)
doc.build(elements)
print(f"PDF saved: {OUT_PDF}")
