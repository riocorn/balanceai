"""
Extends the hand-verified lunch categorization (169 dishes, 12 categories) to ALL
572 dishes (breakfast + lunch + dinner) using name/description keyword rules plus
the diet field — needed so compute_dish_nutrients.py picks the right cooking state
for every dish, not just lunch ones (previous default incorrectly treated all
non-lunch-categorized dishes as generic "sabzi").
"""
import json
import re
import glob
from pathlib import Path

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")

# reuse the same hand-verified lunch category assignments (region, name) -> category
LUNCH_CAT_BY_NAME = {}
for f in glob.glob(str(DATA_DIR / "lunch_categories" / "*.json")):
    cat = Path(f).stem
    d = json.loads(Path(f).read_text())
    for dish in d["dishes"]:
        LUNCH_CAT_BY_NAME[(dish["region"], dish["name"])] = cat

ROTI_KEYWORDS = ["roti", "paratha", "parantha", "parotta", "naan", "kulcha", "puri", "poori",
                  "luchi", "chapati", "chapatti", "bhakri", "poli", "thalipeeth", "litti",
                  "thepla", "dhebra", "khambir", "phulka", "kachori", "obbattu", "bobbatlu",
                  "faraa", "idiyappam", "appam", "dosa", "uttapam", "chilla", "cheela",
                  "cheeла", "puttu", "idli"]
DAL_KEYWORDS = ["dal ", "dal(", "dhal", "sambar", "rasam", "amti", "varan", "huli", "dalma",
                 "parippu", "pappu", "chole", "rajma", "ghugni", "cholar dal"]
KADHI_KEYWORDS = ["kadhi", "kaalan", "kalan"]
RICE_KEYWORDS = ["biryani", "pulao", "khichdi", "bath ", "bhaat", "chawal", "poha", "upma",
                  "pongal", "tehri", "rice", "kanji", "congee"]
SOUP_KEYWORDS = ["soup", "thukpa", "jhol", "shorba", "stew"]
SWEET_KEYWORDS = ["kheer", "halwa", "payasam", "laddu", "barfi", "gulab jamun", "jalebi",
                   "kesari", "sheera", "phirni", "rabri"]
SNACK_KEYWORDS = ["pakora", "bhaji ", "vada", "bonda", "cutlet", "chaat", "bhel", "sev",
                    "namkeen", "mathri", "chikki", "dhokla", "khandvi", "handvo"]


def keyword_match(text, kw_list):
    # word-boundary regex, not naive substring — plain "in" matching let "puri" match
    # inside "Manipuri"/"Kolhapuri" (verified real bug: "Kanghou (Manipuri Stir-fried
    # Vegetables)" got miscategorized as a "roti" dish via this exact false positive)
    return any(re.search(r"\b" + re.escape(kw.strip()) + r"\b", text) for kw in kw_list)


def categorize(dish):
    text = " ".join([dish.get("name", ""), dish.get("local_name", ""), dish.get("description", "")]).lower()
    diet = (dish.get("diet") or "").lower()
    if keyword_match(text, ROTI_KEYWORDS):
        return "roti"
    if keyword_match(text, KADHI_KEYWORDS):
        return "kadhi"
    if keyword_match(text, SWEET_KEYWORDS):
        return "sweet"
    if keyword_match(text, SOUP_KEYWORDS):
        return "soup_stew"
    if keyword_match(text, SNACK_KEYWORDS):
        return "snack"
    if keyword_match(text, DAL_KEYWORDS):
        return "dal"
    if keyword_match(text, RICE_KEYWORDS):
        return "rice"
    if "non" in diet and "veg" in diet or diet == "non-veg" or diet == "non_veg":
        return "non_veg_curry"
    # fall back: vegetable-forward gravy vs dry — default to veg_curry (gravy), the
    # safer generic bucket for an unclassified veg dish, rather than "sabzi" (dry)
    return "veg_curry"


def main():
    full_cat = dict(LUNCH_CAT_BY_NAME)
    counts = {"reused_lunch": len(LUNCH_CAT_BY_NAME), "auto_categorized": 0}
    for meal, subdir in [("breakfast", "breakfast_research"), ("lunch", "lunch_research"), ("dinner", "dinner_research")]:
        for f in glob.glob(str(DATA_DIR / subdir / "*.json")):
            if "thali_types" in f:
                continue
            d = json.loads(Path(f).read_text())
            region = d["region"]
            for dish in d["dishes"]:
                key = (region, dish["name"])
                if key in full_cat:
                    continue
                full_cat[key] = categorize(dish)
                counts["auto_categorized"] += 1

    out = {f"{r}|||{n}": c for (r, n), c in full_cat.items()}
    (DATA_DIR / "all_meal_categories.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(counts)
    print("Total categorized:", len(full_cat))


if __name__ == "__main__":
    main()
