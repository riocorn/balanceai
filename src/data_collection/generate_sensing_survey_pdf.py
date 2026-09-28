"""
BalanceAI — Non-Invasive Micronutrient Sensing: Literature Survey
Compiles all 5 research-group JSON files into one PDF: for each of the 25
tracked nutrients, whether a real published non-invasive/minimally-invasive
sensing method exists, its accuracy/correlation-to-serum, development stage,
and citations. Honest tiering — no fabricated or exaggerated claims.
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
SRC_DIR = ROOT / "data" / "sensing_literature_survey"
OUT_PDF = ROOT / "data" / "BalanceAI_NonInvasive_Sensing_Literature_Survey.pdf"

GROUP_FILES = ["fat_soluble_vitamins.json", "b_vitamins_1.json", "b_vitamins_2_and_c.json",
               "macrominerals.json", "trace_minerals_omega3.json"]

GREEN = colors.HexColor("#1d5c3d")
DARK = colors.HexColor("#0d1b1e")
LIGHT = colors.HexColor("#eef7f2")
BORDER = colors.HexColor("#e4e7e2")
AMBER = colors.HexColor("#b45309")
RED = colors.HexColor("#b91c1c")

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=GREEN, fontSize=19)
h2 = ParagraphStyle("h2", parent=styles["Heading1"], textColor=colors.white, fontSize=15,
                     backColor=GREEN, borderPadding=7)
nutrient_h = ParagraphStyle("nh", parent=styles["Heading3"], textColor=DARK, fontSize=12, spaceBefore=12, spaceAfter=2)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.3, leading=12.5)
small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8.3, leading=11, textColor=colors.HexColor("#4b5563"))
cite = ParagraphStyle("cite", parent=styles["BodyText"], fontSize=7.8, leading=10, textColor=colors.HexColor("#6b7280"), leftIndent=10)

STATUS_COLOR = {True: GREEN, False: RED}

elements = []
elements.append(Paragraph("Non-Invasive Micronutrient Sensing — Literature Survey", h1))
elements.append(Paragraph(
    "For each of the 25 nutrients BalanceAI tracks: does real published research demonstrate a "
    "non-invasive or minimally-invasive (sweat, saliva, urine, optical, interstitial fluid) sensing "
    "method with any demonstrated link to actual serum/blood status? Real accuracy numbers, "
    "development stage, and citations where they exist — explicit “no research found” where "
    "they don't. No fabricated or extrapolated claims.", body,
))
elements.append(Spacer(1, 10))

all_data = []
for fname in GROUP_FILES:
    all_data.append(json.loads((SRC_DIR / fname).read_text()))

all_nutrients = [n for g in all_data for n in g["nutrients"]]
has_method = [n for n in all_nutrients if n.get("has_noninvasive_method")]
no_method = [n for n in all_nutrients if not n.get("has_noninvasive_method")]

elements.append(Paragraph(
    f"<b>{len(has_method)} of {len(all_nutrients)}</b> nutrients have at least some published non-invasive "
    f"sensing research. <b>{len(no_method)}</b> have none found after systematic search.", body,
))
elements.append(Spacer(1, 8))

# Summary table
summary_rows = [["Nutrient", "Non-Invasive Research?", "Group"]]
for g in all_data:
    for n in g["nutrients"]:
        status = "Yes" if n.get("has_noninvasive_method") else "No"
        summary_rows.append([n["nutrient"], status, g["group"]])
t = Table(summary_rows, colWidths=[5.5 * cm, 3.5 * cm, 8.2 * cm])
tstyle = [
    ("BACKGROUND", (0, 0), (-1, 0), GREEN),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]
for i, row in enumerate(summary_rows[1:], start=1):
    color = colors.HexColor("#eef7f2") if row[1] == "Yes" else colors.HexColor("#fef2f2")
    tstyle.append(("BACKGROUND", (0, i), (-1, i), color))
t.setStyle(TableStyle(tstyle))
elements.append(t)
elements.append(PageBreak())

for g in all_data:
    elements.append(Paragraph(f"&nbsp;{g['group']}", h2))
    elements.append(Spacer(1, 6))
    for n in g["nutrients"]:
        status_txt = "HAS RESEARCH" if n.get("has_noninvasive_method") else "NO RESEARCH FOUND"
        elements.append(Paragraph(
            f"{n['nutrient']} &nbsp; <font size=8 color='{STATUS_COLOR[n.get('has_noninvasive_method', False)].hexval()}'><b>[{status_txt}]</b></font>",
            nutrient_h,
        ))
        if n.get("summary"):
            elements.append(Paragraph(n["summary"], body))
        for f in n.get("findings", []):
            line = f"<b>{f.get('modality','')}</b>"
            if f.get("accuracy_or_correlation"):
                line += f" — {f['accuracy_or_correlation']}"
            if f.get("stage"):
                line += f" &nbsp;[{f['stage']}]"
            elements.append(Paragraph(f"&bull; {line}", small))
            if f.get("citation_title"):
                cite_txt = f.get("citation_title", "")
                if f.get("citation_url"):
                    cite_txt = f'<link href="{f["citation_url"]}">{cite_txt}</link>'
                elements.append(Paragraph(cite_txt, cite))
    elements.append(PageBreak())

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                         topMargin=1.6 * cm, bottomMargin=1.6 * cm)
doc.build(elements)
print(f"Nutrients with research: {len(has_method)} / {len(all_nutrients)}")
print(f"PDF saved -> {OUT_PDF}")
