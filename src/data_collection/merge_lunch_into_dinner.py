"""
Merges shared-appropriate LUNCH dishes into the DINNER region files.
Real Indian dietary pattern: dal, sabzi, roti, veg curry, non-veg curry, rice,
soup/stew and salad are commonly eaten at BOTH lunch and dinner. Kadhi/curd-based
curries, sweets, snacks and drinks are excluded here (lunch-leaning / occasional-
dinner-exception items, kept out of the default merge).
Only adds dishes not already present (by name) in the target dinner file.
"""
import json
from pathlib import Path

LUNCH_CAT_DIR = Path("/home/abhay/Downloads/medical/balanceai/data/lunch_categories")
DINNER_DIR = Path("/home/abhay/Downloads/medical/balanceai/data/dinner_research")

MERGE_CATEGORIES = ["dal", "sabzi", "roti", "veg_curry", "non_veg_curry", "rice", "soup_stew", "salad"]
REGION_FILE = {"North": "north.json", "South": "south.json", "East": "east.json",
               "West": "west.json", "Northeast": "northeast.json", "Central and Islands": "central_islands.json"}

# Collect lunch dishes per region, tagged with their lunch category
lunch_by_region = {}
for cat in MERGE_CATEGORIES:
    d = json.loads((LUNCH_CAT_DIR / f"{cat}.json").read_text())
    for dish in d["dishes"]:
        region = dish["region"]
        lunch_by_region.setdefault(region, []).append({**dish, "lunch_category": cat})

for region, fname in REGION_FILE.items():
    dinner_path = DINNER_DIR / fname
    if not dinner_path.exists():
        continue  # dinner research not done yet for this region
    dinner_data = json.loads(dinner_path.read_text())
    existing_names = {d["name"] for d in dinner_data["dishes"]}
    lunch_dishes = lunch_by_region.get(region, [])

    added = 0
    for dish in lunch_dishes:
        if dish["name"] in existing_names:
            continue
        entry = {k: v for k, v in dish.items() if k not in ("region", "lunch_category")}
        entry["also_lunch"] = True
        entry["source"] = f"merged from lunch ({dish['lunch_category']} category) — commonly eaten at dinner too"
        dinner_data["dishes"].append(entry)
        existing_names.add(dish["name"])
        added += 1

    merge_note = (f" [{added} dal/sabzi/roti/veg-curry/non-veg-curry/rice/soup/salad dishes merged in "
                  f"from the lunch research — these are commonly eaten at both meals; kadhi/curd curries, "
                  f"sweets, snacks and drinks were deliberately left out of this merge as lunch-leaning "
                  f"or occasional-dinner items.]")
    dinner_data["note"] = (dinner_data.get("note") or "") + merge_note

    dinner_path.write_text(json.dumps(dinner_data, indent=2, ensure_ascii=False))
    print(f"{region}: +{added} merged, total now {len(dinner_data['dishes'])}")
