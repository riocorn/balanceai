"""
Splits the 169 lunch-compendium dishes into two category files:
  - rotiyan.json  : bread/flatbread family (roti, paratha, naan, puri, bhakri, etc.)
  - sabjiyan.json : vegetable dish/curry family (sabzi, bhaji, torkari, poriyal, etc.)
Classification is keyword-based against dish name + local_name + description,
grounded in standard Indian culinary terminology (not per-dish guessing).
Dishes matching neither (dal, rice, non-veg curry, dairy, sweets, snacks, drinks)
are left out of both files and listed separately for visibility.
"""
import json
import re
from pathlib import Path

RESEARCH_DIR = Path("/home/abhay/Downloads/medical/balanceai/data/lunch_research")
OUT_DIR = RESEARCH_DIR.parent / "lunch_categories"
OUT_DIR.mkdir(exist_ok=True)

REGION_ORDER = ["north.json", "south.json", "east.json", "west.json", "northeast.json", "central_islands.json"]

ROTI_KEYWORDS = [
    "roti", "paratha", "parantha", "parotta", "naan", "kulcha", "puri", "poori", "luchi",
    "chapati", "chapatti", "bhakri", "poli", "thalipeeth", "litti", "thepla", "dhebra",
    "roomali", "phulka", "akki roti", "jolada rotti", "rumali", "makki", "bajra roti",
    "jowar roti", "ragi roti", "sattu paratha", "missi roti", "kachori", "puran poli",
    "obbattu", "bobbatlu",
]

SABZI_KEYWORDS = [
    "sabzi", "sabji", "sabzee", "bhaji", "torkari", "tarkari", "palya", "poriyal",
    "thoran", "kootu", "avial", "chorchori", "shukto", "undhiyu", "umbadiyu", "bharta",
    "baingan", "aloo gobi", "aloo dum", "bhindi", "gobi", "saag", "khatta", "olan",
    "pachadi", "korola", "bagara baingan", "achaar", "ghanta", "chana bhaji", "yam achaar",
    "dubki kadhi",
]

EXCLUDE_HINTS = ["dal", "kadhi chawal", "khichdi", "biryani", "pulao", "curry rice", "fish curry",
                 "meat", "chicken", "mutton", "pork", "prawn", "tuna", "kheer", "payasam", "lassi"]


def has_kw(text, keywords):
    for k in keywords:
        if re.search(r"\b" + re.escape(k) + r"\b", text):
            return True
    return False


def classify(dish):
    text = " ".join([dish.get("name", ""), dish.get("local_name", ""), dish.get("description", "")]).lower()
    is_roti = has_kw(text, ROTI_KEYWORDS)
    is_sabzi = has_kw(text, SABZI_KEYWORDS)
    # a stuffed/vegetable-filled flatbread is roti-family, not sabzi, even if it names a vegetable
    if is_roti:
        return "roti"
    if is_sabzi:
        return "sabzi"
    return None


rotiyan, sabjiyan, unclassified = [], [], []

for fname in REGION_ORDER:
    d = json.loads((RESEARCH_DIR / fname).read_text())
    region = d["region"]
    for dish in d["dishes"]:
        cat = classify(dish)
        entry = {**dish, "region": region}
        if cat == "roti":
            rotiyan.append(entry)
        elif cat == "sabzi":
            sabjiyan.append(entry)
        else:
            unclassified.append(entry)

(OUT_DIR / "rotiyan.json").write_text(
    json.dumps({"category": "Rotiyan (Breads/Flatbreads)", "count": len(rotiyan), "dishes": rotiyan}, indent=2, ensure_ascii=False)
)
(OUT_DIR / "sabjiyan.json").write_text(
    json.dumps({"category": "Sabjiyan (Vegetable Dishes)", "count": len(sabjiyan), "dishes": sabjiyan}, indent=2, ensure_ascii=False)
)
(OUT_DIR / "unclassified.json").write_text(
    json.dumps({"category": "Unclassified (dal/rice/non-veg/dairy/sweets/snacks/drinks)", "count": len(unclassified),
                "dishes": unclassified}, indent=2, ensure_ascii=False)
)

print(f"Rotiyan: {len(rotiyan)}")
print(f"Sabjiyan: {len(sabjiyan)}")
print(f"Unclassified: {len(unclassified)}")
print(f"Total: {len(rotiyan) + len(sabjiyan) + len(unclassified)}")
