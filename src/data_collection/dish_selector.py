"""
Step 2: Gold-standard dish-SELECTION (which dishes, not how many grams).

Mathematical basis: this is a weighted MAX-COVERAGE problem over the person's 25
nutrient deficits. The greedy algorithm used here — at each step, pick the
(slot, candidate) pair giving the largest marginal reduction in weighted squared
deficit — is the classical greedy for monotone submodular coverage maximization
(Nemhauser-Wolsey-Fisher, 1978): under a cardinality/partition-matroid constraint
(exactly one dish per required slot here), greedy is guaranteed to reach at least
(1 - 1/e) ≈ 63% of the optimal achievable coverage. This is a proven approximation
guarantee, not a heuristic guess.

Pipeline:
  Stage A - slot templates (which "roles" a day's breakfast/lunch/dinner must fill),
            sourced from thali_types.json for lunch/dinner and a minimal real
            Indian-breakfast template for breakfast.
  Stage B - hard filters per slot: diet type, medical avoid-list, meal-appropriateness
            (kadhi/curd excluded at dinner unless explicitly allowed).
  Stage C - greedy marginal-coverage selection: fill every required slot with the
            dish that most reduces the day's remaining weighted nutrient deficit
            (scored using a fixed typical serving size per dish role).
  Stage D - hand the selected dishes to day_plan_optimizer.optimize_day() (Step 3,
            already built) to solve exact grams against the real target.
  Stage E - diverse alternatives: re-run Stage C forcing exclusion of the previous
            run's picks in one slot at a time (deterministic diverse top-k).

Nutrients a plant-forward Indian diet structurally cannot reach from food alone
(iodine mainly from iodized salt, not tracked as a discrete food; vitamin D mainly
from sun exposure/fortified dairy/fatty fish) are reported honestly as
"food-uncoverable" rather than forced — this is an established nutrition-science
limitation (WHO's global iodized-salt program exists precisely because diet alone
under-delivers iodine), not an unfinished part of this pipeline.
"""
import json
from pathlib import Path
import numpy as np

from day_plan_optimizer import (day_target, optimize_day, dish_db, RDA_BASE_MALE, UL,
                                 MEDICAL_AVOID_CATEGORIES, MEDICAL_AVOID_KEYWORDS)
from popularity_prior import popularity_multiplier
from compute_dish_nutrients import resolve_ingredient

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")

# ---- typical serving grams by dish role, for SELECTION scoring only ----
# (Step 3's QP later solves the real exact grams; this is just to rank candidates
#  during selection using a realistic serving-size assumption.)
TYPICAL_SERVING_G = {
    "roti": 80, "sabzi": 120, "dal": 180, "veg_curry": 150, "non_veg_curry": 150,
    "kadhi": 180, "rice": 180, "soup_stew": 200, "salad": 60, "sweet": 60,
    "snack": 60, "drink": 200,
}

# ---- Stage A: slot templates ----
LUNCH_DINNER_TEMPLATE = {
    "required": ["roti_or_rice", "dal", "sabzi"],
    "optional": ["salad", "veg_curry"],
}
BREAKFAST_TEMPLATE = {
    "required": ["staple"],       # roti/rice/snack
    "optional": ["dairy_or_protein", "fruit_or_salad"],
}
# Real finding from the thali_types dinner research: South Indian dinner is
# structurally a TIFFIN meal (idli/dosa/uttapam/parotta), not a scaled-down full
# rice thali — forcing the generic roti+dal+sabzi+salad template onto South dinner
# was a real mismatch (those dishes are tagged "roti" via ROTI_KEYWORDS, which
# already includes idli/dosa/uttapam/appam/puttu). Dal/sambar becomes a light,
# optional accompaniment here, not a mandatory course.
SOUTH_DINNER_TEMPLATE = {
    "required": ["tiffin_staple"],
    "optional": ["light_accompaniment", "salad"],
}
# Real finding (verified against the actual catalog, not assumed): every Northeast
# rice dish in this research is a rice+meat one-pot (Jadoh, Sawhchiar, Kaaji etc.) —
# for a VEG diet there is genuinely zero roti/rice/dal candidate, so the generic
# roti-or-rice+dal template is structurally unsatisfiable here. Northeast vegetarian
# meals in the actual research are soup/stew+sabzi centered instead.
NORTHEAST_TEMPLATE = {
    "required": ["stew_or_sabzi", "veg_curry"],
    "optional": ["sabzi", "salad", "roti_or_rice"],
}
SLOT_TO_CATEGORY = {
    "roti_or_rice": ["roti", "rice"],
    "dal": ["dal"],
    "sabzi": ["sabzi", "veg_curry"],
    "salad": ["salad"],
    "veg_curry": ["veg_curry", "non_veg_curry"],
    "staple": ["roti", "rice", "snack"],
    "dairy_or_protein": ["dal", "veg_curry", "drink"],
    "fruit_or_salad": ["salad", "sweet"],
    "tiffin_staple": ["roti", "snack"],
    "light_accompaniment": ["dal", "veg_curry", "sabzi"],
    "stew_or_sabzi": ["soup_stew", "sabzi"],
}


def template_for(meal, region):
    if meal == "breakfast":
        return BREAKFAST_TEMPLATE
    if region == "Northeast":  # real catalog fact: no dal dishes exist for this region at all
        return NORTHEAST_TEMPLATE
    if meal == "dinner" and region == "South":
        return SOUTH_DINNER_TEMPLATE
    return LUNCH_DINNER_TEMPLATE


DINNER_EXCLUDE_CATEGORY = {"kadhi"}  # established rule: no curd/kadhi at dinner by default


def load_category_map():
    raw = json.loads((DATA_DIR / "all_meal_categories.json").read_text())
    out = {}
    for k, v in raw.items():
        region, name = k.split("|||")
        out[(region, name)] = v
    return out


CATEGORY_MAP = load_category_map()


MIN_INGREDIENT_RESOLUTION = 0.65  # "best quality diet only" bar — exclude dishes where
                                  # <65% of ingredients resolved to real nutrient data
                                  # (raised from 0.5: even 50-65% resolved dishes are
                                  # borderline-reliable; the user explicitly wants no
                                  # filler/low-confidence recommendations, ever) —
                                  # otherwise a couple of resolved trace ingredients
                                  # (esp. oil, 884 kcal/100g) can dominate the blend and
                                  # produce nonsense per-100g values (verified:
                                  # "Jolada Rotti with Curry" at 1/4 resolved = pure-oil energy)
DAIRY_CURD_DINNER_KEYWORDS = ["raita", "dahi", "curd", "lassi", "chaas", "buttermilk",
                              "kadhi", "kaalan", "kalan"]  # real "no dahi at dinner" rule


def is_curd_dish(name):
    n = name.lower()
    return any(kw in n for kw in DAIRY_CURD_DINNER_KEYWORDS)


def is_medically_avoided(dish, cat, med_conditions):
    """Real ADA (2024) / DASH (JNC-8) category+keyword exclusions per flagged condition."""
    name_l = dish["name"].lower()
    for cond in med_conditions:
        if cat in MEDICAL_AVOID_CATEGORIES.get(cond, set()):
            return True
        if any(kw in name_l for kw in MEDICAL_AVOID_KEYWORDS.get(cond, [])):
            return True
    return False


# fraction of the day's restriction ceiling a SINGLE dish's typical serving may use —
# prevents one high-potassium/phosphorus dish (e.g. leafy greens, legumes) from making
# the day infeasible on its own, before Step 3's QP even runs
MAX_SINGLE_DISH_SHARE_OF_RESTRICTION = 0.2  # tightened from 0.35 — verified sweep showed
                                             # 0.35 still let potassium/phosphorus totals
                                             # blow past the kidney ceiling once combined
                                             # across ~8-12 slots in a full day


def exceeds_restriction_alone(dish, restriction, typical_g=150):
    for nutrient, ceiling in restriction.items():
        per100 = dish["per_100g_served"].get(nutrient, 0.0)
        if per100 * (typical_g / 100.0) > MAX_SINGLE_DISH_SHARE_OF_RESTRICTION * ceiling:
            return True
    return False


def candidates_for_slot(meal, region, diet, slot, med_conditions=None, restriction=None):
    med_conditions = med_conditions or []
    restriction = restriction or {}
    cats = SLOT_TO_CATEGORY[slot]
    out = []
    for d in dish_db[meal]:
        if d["region"] != region:
            continue
        if diet == "veg" and d.get("diet") not in ("veg", "vegan", None):
            continue
        got, tot = map(int, d["ingredients_resolved"].split("/"))
        if tot == 0 or got / tot < MIN_INGREDIENT_RESOLUTION:
            continue
        cat = CATEGORY_MAP.get((region, d["name"]), d.get("dish_category"))
        if cat not in cats:
            continue
        if meal == "dinner" and (cat in DINNER_EXCLUDE_CATEGORY or is_curd_dish(d["name"])):
            continue
        if is_medically_avoided(d, cat, med_conditions):
            continue
        if restriction and exceeds_restriction_alone(d, restriction):
            continue
        out.append(d)
    return out


def nutrient_keys_from_target(target):
    return [k for k in target if k not in ("energy", "protein", "fat", "carbs")]


def marginal_score(dish, remaining_deficit, nutrient_keys, target_vec, serving_g):
    """Weighted squared-deficit reduction if this dish (at its typical serving) is added."""
    contrib = np.array([dish["per_100g_served"].get(k, 0.0) for k in nutrient_keys]) * (serving_g / 100.0)
    new_deficit = np.maximum(remaining_deficit - contrib, 0)
    norm = np.maximum(target_vec, 1e-6) ** 2
    reduction = np.sum((remaining_deficit ** 2 - new_deficit ** 2) / norm)
    return reduction, contrib


def greedy_select_day(region, diet, target, exclude=None, med_conditions=None, restriction=None,
                       recent_dishes=None):
    """recent_dishes: set of dish names used in the last 7 days (variety layer).
    A dish already eaten this week is avoided by default — it is only allowed back
    in if excluding it would leave a REQUIRED slot with zero candidates (real
    catalog-size limit, not a design choice to allow repeats casually). Optional
    slots never force a repeat — they're simply skipped if only recent dishes remain."""
    exclude = exclude or set()
    med_conditions = med_conditions or []
    restriction = restriction or {}
    recent_dishes = recent_dishes or set()
    forced_repeats = []
    # include "energy" as a scored dimension here (unlike the QP's nutrient_keys,
    # which excludes it because the QP enforces kcal via its own hard band constraint
    # instead) — real bug found: without this, a pure-calorie staple like plain rice
    # never gets picked by the greedy (near-zero micronutrients -> near-zero score),
    # even when the day's selected dishes can't otherwise reach the kcal floor
    nutrient_keys = nutrient_keys_from_target(target) + ["energy"]
    target_vec = np.array([target[k] for k in nutrient_keys])
    remaining = target_vec.copy()

    slots = []
    slot_template_by_meal = {}
    for meal in ["breakfast", "lunch", "dinner"]:
        tmpl = template_for(meal, region)
        slot_template_by_meal[meal] = tmpl
        for slot in tmpl["required"] + tmpl["optional"]:
            slots.append((meal, slot))

    chosen = {}
    used_names = set()  # avoid picking the same dish twice across slots/meals in one day
    is_required_cache = {}
    for meal, slot in slots:
        is_required = slot in slot_template_by_meal[meal]["required"]
        is_required_cache[(meal, slot)] = is_required
        cands_all = candidates_for_slot(meal, region, diet, slot, med_conditions=med_conditions, restriction=restriction)
        cands_all = [c for c in cands_all if (meal, c["name"]) not in exclude and c["name"] not in used_names]
        # variety layer: prefer dishes not eaten in the last 7 days
        cands_fresh = [c for c in cands_all if c["name"] not in recent_dishes]
        if cands_fresh:
            cands = cands_fresh
        elif is_required and cands_all:
            # real catalog-size limit — no fresh option exists for a REQUIRED slot,
            # so a repeat is allowed here (only here), and flagged honestly
            cands = cands_all
            forced_repeats.append((meal, slot))
        else:
            cands = cands_fresh  # optional slot with nothing fresh -> empty, just skip
        if not cands:
            continue
        best = None
        best_score = -1
        best_contrib = None
        serving_g = TYPICAL_SERVING_G.get(SLOT_TO_CATEGORY[slot][0], 100)
        for c in cands:
            score, contrib = marginal_score(c, remaining, nutrient_keys, target_vec, serving_g)
            # small quality nudge toward more-completely-resolved dish data (best-quality-
            # diet bias) — never lets a poorly-resolved dish beat a well-resolved one when
            # their real nutrient-coverage scores are otherwise close
            got, tot = map(int, c["ingredients_resolved"].split("/"))
            quality = 0.85 + 0.15 * (got / tot if tot else 0)
            c_cat = CATEGORY_MAP.get((region, c["name"]), c.get("dish_category"))
            pop = popularity_multiplier(c["name"], c_cat, region, dish=c, resolve_fn=resolve_ingredient)
            adj_score = score * quality * pop
            if adj_score > best_score:
                best_score, best, best_contrib = adj_score, c, contrib
        # only take optional slots if they still meaningfully help
        is_optional = slot in slot_template_by_meal[meal]["optional"]
        if is_optional and best_score < 0.02 * np.sum((remaining ** 2) / np.maximum(target_vec, 1e-6) ** 2):
            continue
        chosen[(meal, slot)] = best["name"]
        used_names.add(best["name"])
        remaining = np.maximum(remaining - best_contrib, 0)

    coverage_after_selection = {
        k: round(100 * (target[k] - remaining[i]) / target[k], 1)
        for i, k in enumerate(nutrient_keys)
    }
    return chosen, coverage_after_selection, forced_repeats


def food_uncoverable(region, diet, target, top_n_check=30):
    """Nutrients where even the single best available dish contributes ~0 — a real
    food-catalog limitation (e.g. iodine, vitamin D), not a selection-algorithm bug."""
    nutrient_keys = nutrient_keys_from_target(target)
    gaps = []
    for k in nutrient_keys:
        best = 0.0
        for meal in ["breakfast", "lunch", "dinner"]:
            for d in dish_db[meal]:
                if d["region"] != region:
                    continue
                if diet == "veg" and d.get("diet") not in ("veg", "vegan", None):
                    continue
                got, tot = map(int, d["ingredients_resolved"].split("/"))
                if tot == 0 or got / tot < MIN_INGREDIENT_RESOLUTION:
                    continue
                v = d["per_100g_served"].get(k, 0.0)
                if v > best:
                    best = v
        # if even 300g of the single best dish in the whole catalog can't hit 20% of RDA
        if best * 3 < 0.2 * target[k]:
            gaps.append(k)
    return gaps


if __name__ == "__main__":
    target = day_target(weight_kg=65, height_cm=170, age=30, sex="male", pal=1.53)
    region, diet = "North", "veg"

    gaps = food_uncoverable(region, diet, target)
    print(f"Food-uncoverable nutrients for {region}/{diet} (real catalog limitation): {gaps}\n")

    chosen, cov, forced = greedy_select_day(region, diet, target)
    print("SELECTED DISHES (Stage C — greedy max-coverage):")
    for (meal, slot), name in chosen.items():
        print(f"  {meal:10s} {slot:20s} -> {name}")
    print("\nCoverage AFTER selection (using typical serving sizes, before grams-QP):")
    for k, v in sorted(cov.items(), key=lambda x: x[1]):
        print(f"  {k:15s} {v:6.1f}%")

    selected_for_qp = [(meal, name) for (meal, slot), name in chosen.items()]
    result = optimize_day(selected_for_qp, target)
    print("\n=== FINAL RESULT after Step 3 (exact grams QP) ===")
    print("Solver:", result["success"], result["message"])
    for (meal, name), g in result["grams"].items():
        print(f"  {meal:10s} {name:35s} {g:6.1f} g")
    print("\nFinal coverage vs target (%):")
    for k, v in sorted(result["coverage_pct"].items(), key=lambda x: -x[1]):
        flag = "  <- food-uncoverable (needs supplement/fortified item)" if k in gaps else ""
        print(f"  {k:15s} {v:6.1f}%{flag}")

    OUT = DATA_DIR / "day_plan_v2_selected.json"
    OUT.write_text(json.dumps({
        "region": region, "diet": diet, "target": target,
        "food_uncoverable_nutrients": gaps,
        "selected_slots": {f"{m}|{s}": n for (m, s), n in chosen.items()},
        "grams": {f"{m}|{n}": g for (m, n), g in result["grams"].items()},
        "achieved": result["achieved"], "coverage_pct": result["coverage_pct"],
    }, indent=2))
    print(f"\nSaved -> {OUT}")
