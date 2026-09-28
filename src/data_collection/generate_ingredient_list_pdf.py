"""
BalanceAI — Total Ingredient List PDF
Full master ingredient database used by the Recipe Maker AI pipeline's
seasonal-availability filter (Step 2 of the 4-step pipeline).
Source: src/api/seasonal_ingredients.py (INGREDIENTS dict)
"""
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ROOT = Path("/home/abhay/Downloads/medical/balanceai")
sys.path.insert(0, str(ROOT / "src" / "api"))
from seasonal_ingredients import INGREDIENTS  # noqa: E402

OUT_PDF = ROOT / "data" / "BalanceAI_Ingredient_Master_List.pdf"

GREEN = colors.HexColor("#1d5c3d")
DARK = colors.HexColor("#0d1b1e")
LIGHT = colors.HexColor("#eef7f2")
BORDER = colors.HexColor("#e4e7e2")

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=GREEN, fontSize=20)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=DARK, spaceBefore=14, spaceAfter=4)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
cell = ParagraphStyle("cell", parent=styles["BodyText"], fontSize=8.5, leading=11)

# Category boundaries exactly as grouped in seasonal_ingredients.py (by source order,
# since one ingredient's `seasons` can combine multiple named lists — e.g. SUMMER + MONSOON —
# so category is which section of the file it's declared in, not a derived season match).
CATEGORY_IDS = {
    "Always Available (Staples)": [
        "rice", "wheat_flour", "toor_dal", "moong_dal", "chana_dal", "urad_dal", "rajma",
        "chickpea", "onion", "garlic", "ginger", "tomato", "potato", "milk", "curd", "paneer",
        "egg", "ghee", "oil", "cumin", "mustard_seeds", "turmeric", "coriander_pwd", "chili_pwd",
        "garam_masala", "coriander_leaves", "salt", "black_pepper", "cardamom", "cooking_oil",
        "saffron", "jaggery", "sugar", "banana", "papaya", "lemon", "green_chili", "curry_leaves",
        "poha", "semolina", "besan", "oats", "peanut", "sesame", "sesame_seeds", "sunflower_seeds",
        "pumpkin_seeds", "flaxseeds", "chia_seeds", "almonds", "walnuts", "cashews", "pistachios",
        "coconut", "coconut_dried", "tamarind", "dry_fruits", "chicken", "mutton", "fish_dried",
    ],
    "Summer": [
        "raw_mango", "mango", "watermelon", "muskmelon", "cucumber", "bottle_gourd",
        "ridge_gourd", "bitter_gourd", "drumstick", "jackfruit_raw", "kokum", "mint",
        "rose_water", "sattu", "lychee", "tinda", "parwal", "raw_banana", "tender_coconut",
    ],
    "Monsoon": [
        "corn", "jamun", "arbi", "cluster_beans", "flat_beans", "pear", "peach", "fresh_fish",
        "yam", "elephant_yam", "bamboo_shoots", "tulsi",
    ],
    "Autumn / Post-Monsoon": [
        "pomegranate", "guava", "sweet_potato", "beetroot", "carrot", "cauliflower", "apple", "fig",
    ],
    "Winter": [
        "mustard_greens", "methi_leaves", "spinach", "peas", "radish", "turnip", "cabbage",
        "orange", "strawberry", "amla", "dates", "til_seeds", "green_garlic", "bathua",
        "sarson_oil", "broccoli", "knol_khol",
    ],
    "Spring": ["spring_onion", "new_potato"],
}

REGION_LABELS = {
    "north": "North", "south": "South", "east": "East",
    "northeast": "Northeast", "west": "West", "central": "Central",
}


def region_str(regions) -> str:
    if regions == "all":
        return "All India"
    return ", ".join(REGION_LABELS.get(r, r) for r in regions)


def season_str(seasons) -> str:
    if seasons == "all":
        return "Year-round"
    return ", ".join(dict.fromkeys(seasons))  # dedupe, keep order


elements = []
elements.append(Paragraph("BalanceAI — Total Ingredient List", h1))
elements.append(Paragraph(
    f"Master ingredient database ({len(INGREDIENTS)} ingredients) used by the Recipe Maker AI "
    f"4-step pipeline's seasonal-availability filter — every ingredient any generated recipe "
    f"set can draw from, grouped by category with season and region availability.",
    body,
))
elements.append(Spacer(1, 10))

# Cross-check: every listed id must exist in INGREDIENTS, and every INGREDIENTS
# entry must be covered by exactly one category — catches drift if the source
# file is edited later without updating this script.
listed_ids = [i for ids in CATEGORY_IDS.values() for i in ids]
missing_from_source = [i for i in listed_ids if i not in INGREDIENTS]
uncategorized = [i for i in INGREDIENTS if i not in listed_ids]
if missing_from_source or uncategorized:
    elements.append(Paragraph(
        f"<b>Data check:</b> {len(missing_from_source)} listed ingredient(s) not found in source; "
        f"{len(uncategorized)} source ingredient(s) uncategorized: {', '.join(uncategorized) or 'none'}.",
        ParagraphStyle("warn", parent=body, textColor=colors.red),
    ))
    elements.append(Spacer(1, 8))

table_style = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), GREEN),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
])

for category, ids in CATEGORY_IDS.items():
    present_ids = [i for i in ids if i in INGREDIENTS]
    elements.append(Paragraph(f"{category}  ({len(present_ids)} ingredients)", h2))
    rows = [["Ingredient", "Regions", "Season Availability"]]
    for ing_id in present_ids:
        data = INGREDIENTS[ing_id]
        rows.append([
            Paragraph(data["name"], cell),
            Paragraph(region_str(data["regions"]), cell),
            Paragraph(season_str(data["seasons"]), cell),
        ])
    t = Table(rows, colWidths=[6.5 * cm, 4.5 * cm, 6.5 * cm])
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 8))

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                         topMargin=1.6 * cm, bottomMargin=1.6 * cm)
doc.build(elements)
print(f"Total ingredients: {len(INGREDIENTS)}")
print(f"Categorized: {len(listed_ids)}")
print(f"PDF saved -> {OUT_PDF}")
