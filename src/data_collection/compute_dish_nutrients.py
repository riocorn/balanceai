"""
Step 0c: Compute per-100g-as-served nutrient profile for every dish in the
breakfast/lunch/dinner catalogs (572 dishes), using:
  1. STATE_MULT retention + weight-change factors (exact same table/formula as
     frontend/src/lib/comprehensive-food-db.ts's generateItems()) to convert each
     resolved ingredient's raw per-100g value into its as-cooked per-100g value.
  2. A mass-weighted blend across a dish's resolved ingredients — weight reflects
     typical proportion-of-dish-weight by ingredient category (staples/veg/dal/meat
     dominate; oil is a moderate contributor; spices are trace quantities) — grounded
     in standard Indian recipe convention, not a guess per individual dish.
  3. A per-lunch/dish-category default cooking state (dal -> "cooked (curry)",
     roti -> "roasted", rice -> "boiled", sabzi -> "cooked (curry)", non-veg curry ->
     "cooked (curry)", kadhi -> "cooked (curry)", soup/stew -> "boiled", salad -> "raw").

This is a mass-weighted-average approximation, not a lab measurement — it is the
correct place to be approximate, because Step 3 (the day-level portion optimizer)
solves for exact serving GRAMS against the person's real target; getting the
per-100g profile in the right ballpark (via real ingredient data + real cooking-loss
physics) is what matters, not simulating an exact untested recipe.
"""
import json
import glob
from pathlib import Path

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")
MASTER = json.loads((DATA_DIR / "ingredient_master.json").read_text())
INGREDIENTS = MASTER["ingredients"]
ALIAS = MASTER["alias_map"]
ZERO = set(MASTER["zero_contribution"])

N_KEYS = ["iron", "vitamin_b12", "vitamin_d", "calcium", "magnesium", "zinc", "vitamin_c",
          "vitamin_a", "folate", "omega3", "selenium", "vitamin_b6", "potassium", "phosphorus",
          "vitamin_b1", "vitamin_b2", "vitamin_b3", "vitamin_e", "iodine", "copper", "manganese",
          "chromium", "vitamin_k", "vitamin_b5", "vitamin_b7"]
MACRO_KEYS = ["protein", "fiber", "energy"]
ALL_KEYS = N_KEYS + MACRO_KEYS

# Exact copy of STATE_MULT from comprehensive-food-db.ts (29 cols: 25 micronutrients +
# protein, fiber, energy, weight-change-factor)
STATE_MULT = {
    "raw":             [1.0]*29,
    "soaked 4hr":      [1.0,1.0,1.0,1.0,1.0,1.1,1.0,1.0,1.0,1.0,1.0,1.0,0.9,1.0,1.0,1.0,1.0,1.0,0.95,1.05,1.0,1.0,1.0,0.95,1.0,1.0,1.0,0.95,1.3],
    "soaked overnight":[1.2,1.0,1.0,0.9,0.9,1.3,1.1,1.0,1.1,1.0,1.0,1.0,0.85,0.9,1.0,1.0,1.0,1.0,0.9,1.1,1.0,1.0,1.0,0.9,0.95,1.0,1.0,0.9,1.4],
    "sprouted":        [1.5,1.0,1.0,0.85,0.9,1.4,4.0,1.2,2.0,1.1,1.0,1.3,0.8,0.85,1.5,1.3,1.2,1.0,0.85,1.2,1.1,1.0,1.0,1.3,1.2,1.0,1.0,0.8,1.6],
    "boiled":          [0.85,1.0,1.0,0.9,0.85,0.85,0.5,0.85,0.6,0.9,0.85,0.75,0.75,0.85,0.7,0.75,0.75,0.85,0.75,0.85,0.85,0.85,0.85,0.75,0.85,0.9,0.9,0.85,2.5],
    "pressure cooked": [0.85,1.0,1.0,0.88,0.85,0.85,0.45,0.8,0.55,0.9,0.82,0.7,0.72,0.82,0.65,0.7,0.7,0.8,0.72,0.82,0.82,0.82,0.8,0.7,0.8,0.88,0.88,0.85,2.4],
    "roasted":         [0.95,1.0,1.0,1.0,0.95,0.95,0.4,0.9,0.85,0.88,0.9,0.85,0.9,0.95,0.8,0.85,0.85,0.82,0.9,0.95,0.95,0.95,0.85,0.85,0.88,1.0,0.95,1.1,0.85],
    "steamed":         [0.9,1.0,1.0,0.95,0.9,0.9,0.7,0.9,0.75,0.95,0.9,0.85,0.88,0.9,0.8,0.85,0.85,0.9,0.85,0.9,0.9,0.9,0.9,0.85,0.88,0.95,0.95,0.9,1.2],
    "cooked (curry)":  [0.88,1.0,1.0,0.88,0.85,0.85,0.45,0.85,0.6,0.9,0.85,0.75,0.72,0.85,0.7,0.75,0.75,0.85,0.72,0.85,0.85,0.85,0.83,0.7,0.83,0.9,0.9,0.87,2.2],
    # thin stew/soup-style dal prep (sambar/rasam/huli) — same cooking method as
    # "cooked (curry)" but far more water-diluted (real recipe ratio ~1 part dal :
    # 6-10 parts water+vegetables, vs a thick dal's ~1:3-4). wtFactor=5.0 reproduces
    # real published sambar/rasam energy density (~60-90 kcal/100g) as a sanity check
    # (raw toor dal 343kcal/100g / 5.0 ~= 69kcal/100g), instead of a thick-dal 2.2x
    # factor that was overestimating these dishes as ~2.3x too energy-dense.
    "thin stew":       [0.85,1.0,1.0,0.85,0.82,0.82,0.4,0.82,0.55,0.87,0.82,0.7,0.68,0.82,0.65,0.7,0.7,0.82,0.68,0.82,0.82,0.82,0.8,0.65,0.8,0.87,0.87,0.85,5.0],
    "dry roasted":     [1.0,1.0,1.0,1.0,1.0,1.0,0.5,0.95,0.9,0.9,0.95,0.9,0.95,1.0,0.85,0.9,0.9,0.88,0.95,1.0,1.0,1.0,0.92,0.9,0.92,1.0,1.0,1.05,0.9],
}

CATEGORY_MASS_WEIGHT = {
    "Dal": 10, "Vegetable": 10, "Grain": 10, "Meat": 10, "Dairy": 8, "Fruit": 8,
    "Nuts": 3, "Dry Fruits": 2, "Sweetener": 2, "Oil": 1.5, "Spice": 0.3, "Condiment": 0.5,
}

LUNCH_CATEGORY_STATE = {
    "roti": "roasted", "sabzi": "cooked (curry)", "dal": "cooked (curry)",
    "veg_curry": "cooked (curry)", "non_veg_curry": "cooked (curry)", "kadhi": "cooked (curry)",
    "rice": "boiled", "soup_stew": "thin stew", "salad": "raw", "sweet": "cooked (curry)",
    "snack": "roasted", "drink": "raw", "dal_thin": "thin stew",
}


def resolve_ingredient(token):
    norm = token.strip().lower().replace(" ", "_")
    if norm in INGREDIENTS:
        return norm
    if norm in ALIAS:
        return ALIAS[norm]
    if norm in ZERO:
        return None
    return None  # unresolved/missing


def served_100g(ingredient_id, state):
    """Replicates generateItems() from comprehensive-food-db.ts exactly."""
    ing = INGREDIENTS[ingredient_id]
    base = ing["per_100g_raw"]
    mult = STATE_MULT.get(state, STATE_MULT["raw"])
    scaled = {}
    for i, k in enumerate(N_KEYS):
        v = base.get(k, 0) * mult[i]
        if v > 0:
            scaled[k] = v
    for i, k in enumerate(MACRO_KEYS):
        v = base.get(k, 0) * mult[25 + i]
        if v > 0:
            scaled[k] = v
    wt = mult[28]
    if wt > 1.1:
        scaled = {k: v / wt for k, v in scaled.items()}
    return scaled


def dish_default_state(ingredient_id, dish_category):
    """An ingredient's own valid-states list constrains which cooking state applies."""
    ing = INGREDIENTS[ingredient_id]
    preferred = LUNCH_CATEGORY_STATE.get(dish_category, "cooked (curry)")
    if preferred == "thin stew":
        # a real, always-valid override — any legume/vegetable ingredient can be
        # cooked into a thin/watery stew, this isn't gated by the ingredient's own
        # states list (which predates this category)
        return "thin stew"
    if preferred in ing["states"]:
        return preferred
    # fallback: use whichever non-raw cooked state is available, else raw
    for fallback in ["cooked (curry)", "boiled", "roasted", "steamed", "raw"]:
        if fallback in ing["states"]:
            return fallback
    return "raw"


def compute_dish_nutrients(dish, dish_category):
    resolved = []
    for tok in dish.get("ingredients", []):
        iid = resolve_ingredient(tok)
        if iid is None:
            continue
        cat = INGREDIENTS[iid].get("category", "Vegetable")
        weight = CATEGORY_MASS_WEIGHT.get(cat, 3)
        state = dish_default_state(iid, dish_category)
        nutrients = served_100g(iid, state)
        resolved.append((weight, nutrients))

    total_weight = sum(w for w, _ in resolved)
    if total_weight == 0:
        return None, 0, len(dish.get("ingredients", []))

    blended = {}
    for w, nutrients in resolved:
        for k, v in nutrients.items():
            blended[k] = blended.get(k, 0) + (w / total_weight) * v

    return {k: round(v, 3) for k, v in blended.items()}, len(resolved), len(dish.get("ingredients", []))


THIN_DAL_KEYWORDS = ["sambar", "rasam", "huli", "dalma", "saaru", "charu", "pappu charu",
                      "pulusu", "kuzhambu", "vatha kuzhambu"]


def effective_dish_category(dish, cat):
    if cat in ("dal", "veg_curry") and any(kw in dish["name"].lower() for kw in THIN_DAL_KEYWORDS):
        return "dal_thin"
    return cat


def main():
    # full (region, name) -> dish-role-category map covering all 572 dishes:
    # 169 hand-verified lunch categories + 403 breakfast/dinner auto-categorized
    # (see categorize_all_meals.py)
    raw_map = json.loads((DATA_DIR / "all_meal_categories.json").read_text())
    lunch_cat_by_name = {}
    for k, v in raw_map.items():
        region, name = k.split("|||")
        lunch_cat_by_name[(region, name)] = v

    out = {"breakfast": [], "lunch": [], "dinner": []}
    stats = {"total": 0, "resolved_ok": 0, "zero_ingredients": 0}

    for meal, subdir in [("breakfast", "breakfast_research"), ("lunch", "lunch_research"), ("dinner", "dinner_research")]:
        for f in glob.glob(str(DATA_DIR / subdir / "*.json")):
            if "thali_types" in f:
                continue
            d = json.loads(Path(f).read_text())
            region = d["region"]
            for dish in d["dishes"]:
                stats["total"] += 1
                cat = lunch_cat_by_name.get((region, dish["name"]), "veg_curry")
                eff_cat = effective_dish_category(dish, cat)
                nutrients, n_resolved, n_total = compute_dish_nutrients(dish, eff_cat)
                if nutrients is None:
                    stats["zero_ingredients"] += 1
                    continue
                stats["resolved_ok"] += 1
                out[meal].append({
                    "name": dish["name"], "region": region, "diet": dish.get("diet"),
                    "dish_category": cat, "ingredients_resolved": f"{n_resolved}/{n_total}",
                    "ingredients": dish.get("ingredients", []),
                    "per_100g_served": nutrients,
                })

    OUT_PATH = DATA_DIR / "dish_nutrients_v1.json"
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Total dishes: {stats['total']}, nutrients computed: {stats['resolved_ok']}, "
          f"zero-ingredient-resolved (skipped): {stats['zero_ingredients']}")
    print(f"Saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
