"""
Step 0a: Parse the frontend's comprehensive-food-db.ts (138 base ingredients,
ICMR-NIN 2017 / USDA sourced, per-100g raw nutrients across 25 nutrients) into
a JSON lookup table usable by the backend nutrient-tagging pipeline.
"""
import json
import re
from pathlib import Path

SRC = Path("/home/abhay/Downloads/medical/balanceai/frontend/src/lib/comprehensive-food-db.ts")
OUT = Path("/home/abhay/Downloads/medical/balanceai/data/ingredient_master.json")

text = SRC.read_text()

N_KEYS = ["iron", "vitamin_b12", "vitamin_d", "calcium", "magnesium", "zinc", "vitamin_c",
          "vitamin_a", "folate", "omega3", "selenium", "vitamin_b6", "potassium", "phosphorus",
          "vitamin_b1", "vitamin_b2", "vitamin_b3", "vitamin_e", "iodine", "copper", "manganese",
          "chromium", "vitamin_k", "vitamin_b5", "vitamin_b7"]
EXTRA_KEYS = ["protein", "fiber", "energy"]  # prot, fiber, kcal — appended in that order
ALL_KEYS = N_KEYS + EXTRA_KEYS  # 28 positional args to n(...)

# Grab category array names + their body text
cat_blocks = re.findall(r'const ([A-Z_]+): BaseFoodData\[\] = \[(.*?)\n\];', text, re.S)

# within a category block, split into individual `{ id:"..." ... }` entries
entry_re = re.compile(
    r'id:"(?P<id>[^"]+)".*?category:"(?P<category>[^"]+)".*?'
    r'baseNutrients:\s*n\((?P<args>[^)]*)\).*?'
    r'states:\[(?P<states>[^\]]*)\].*?'
    r'serving100g:"(?P<serving>[^"]*)"',
    re.S,
)

ingredients = {}
for cat_name, block in cat_blocks:
    # split on '},\n  {' boundaries roughly by finding each id: occurrence start
    starts = [m.start() for m in re.finditer(r'\{\s*\n?\s*id:"', block)]
    starts.append(len(block))
    for i in range(len(starts) - 1):
        chunk = block[starts[i]:starts[i + 1]]
        m = entry_re.search(chunk)
        if not m:
            continue
        args_raw = m.group("args")
        args = [a.strip() for a in args_raw.split(",")] if args_raw.strip() else []
        vals = []
        for a in args:
            try:
                vals.append(float(a))
            except ValueError:
                vals.append(0.0)
        while len(vals) < len(ALL_KEYS):
            vals.append(0.0)
        nutrients = {k: v for k, v in zip(ALL_KEYS, vals) if v > 0}
        states = [s.strip().strip('"') for s in m.group("states").split(",") if s.strip()]
        ingredients[m.group("id")] = {
            "category": m.group("category"),
            "per_100g_raw": nutrients,
            "states": states,
            "serving100g": m.group("serving"),
            "source_category_array": cat_name,
        }

OUT.write_text(json.dumps({"count": len(ingredients), "ingredients": ingredients}, indent=2, ensure_ascii=False))
print(f"Parsed {len(ingredients)} ingredients -> {OUT}")

# sanity spot-check
for sample_id in ["moong_dal", "masoor_dal"]:
    if sample_id in ingredients:
        print(sample_id, "->", ingredients[sample_id]["per_100g_raw"])
