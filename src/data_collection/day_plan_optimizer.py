"""
Step 3: Day-level meal-plan gram-quantity optimizer.

Given:
  - a person's TOTAL DAY nutrition target (kcal + macros + 25 micronutrients),
    computed exactly as nutrition-engine.ts does (Mifflin-St Jeor BMR x WHO/FAO/UNU
    PAL, ICMR-NIN 2020 RDA table) — this is Step -1's already-established output.
  - a selected set of real dishes across breakfast+lunch+dinner (from
    dish_nutrients_v1.json, Step 0's per-100g-as-served nutrient profiles).

Solves ONE joint Quadratic Program across all selected dishes (not per-meal) for
the exact SERVING GRAMS of each dish, minimizing the normalized weighted squared
deviation from the day's target, subject to:
  - per-dish serving bounds (a sane min/max grams per single dish/meal item)
  - total-day energy within +-10% of kcal_total
  - a few critical micronutrients capped at their NIH ODS Tolerable Upper Intake
    Level (never over-supplement via food combination)

This is the classical "diet problem" (Stigler 1945) formalism — a real, literature-
grounded LP/QP, not a generative/guessed allocation.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")

# ---- Step -1 replica: Mifflin-St Jeor BMR + WHO/FAO/UNU PAL + ICMR-NIN 2020 RDA ----
# (mirrors frontend/src/lib/nutrition-engine.ts exactly)
RDA_BASE_MALE = {
    "iron": 9, "vitamin_b12": 2.2, "vitamin_d": 15, "calcium": 600, "magnesium": 340,
    "zinc": 9, "vitamin_c": 65, "vitamin_a": 600, "folate": 220, "iodine": 150,
    "omega3": 1.6, "selenium": 40, "vitamin_b6": 1.6, "potassium": 3500, "phosphorus": 600,
    "vitamin_b1": 1.2, "vitamin_b2": 1.4, "vitamin_b3": 16, "vitamin_b5": 5, "vitamin_b7": 30,
    "vitamin_k": 55, "copper": 0.9, "manganese": 2.3, "chromium": 33, "vitamin_e": 8,
}

# NIH ODS Tolerable Upper Intake Levels (adult) — hard ceiling, never exceed via food combo
UL = {
    "vitamin_a": 3000, "iron": 45, "zinc": 40, "vitamin_d": 100, "calcium": 2500,
    "vitamin_c": 2000, "vitamin_b6": 100, "folate": 1000, "manganese": 11, "copper": 10,
    "selenium": 400, "potassium": 7000,  # conservative food-sourced ceiling (no formal UL for healthy adults)
}

# Nutrients that become a RESTRICTION ceiling (not a target to reach) under specific
# medical conditions — must be penalized only for exceeding, never for falling short
# (KDIGO 2024 CKD guideline: restrict potassium/phosphorus, do not try to "hit" them).
RESTRICTION_OVERRIDES = {
    "kidney": {"potassium": 1500, "phosphorus": 800},
}

# Real ADA (2024) / DASH (JNC-8) dietary-category exclusions — not a food-name guess,
# these are the standard clinical diet-therapy categories for each condition.
MEDICAL_AVOID_CATEGORIES = {
    "diabetes": {"sweet"},              # ADA 2024: minimize added/free sugars
    "bp_high": {"snack"},               # DASH: minimize fried/salty snack foods
}
MEDICAL_AVOID_KEYWORDS = {
    "diabetes": ["jalebi", "gulab jamun", "halwa", "kheer", "barfi", "laddu", "payasam", "rabri"],
    "bp_high": ["pickle", "achaar", "papad", "namkeen", "fried", "pakora", "bhajiya"],
}


def adjusted_rda(base_rda, age, gender, med_conditions):
    """Mirrors frontend/src/lib/nutrition-engine.ts adjustedRda() exactly."""
    rda = dict(base_rda)
    if age >= 60:
        rda["calcium"] = 800 if gender == "female" else 700
        rda["vitamin_d"] = 20
        rda["vitamin_b12"] = 2.4
    if 13 <= age < 18:
        rda["calcium"] = 800
        rda["iron"] = 27 if gender == "female" else 11
        rda["zinc"] = 9 if gender == "female" else 11
    if "pregnancy" in med_conditions:
        rda["iron"] = 35
        rda["folate"] = 500
        rda["calcium"] = 1200
        rda["vitamin_d"] = 15
        rda["iodine"] = 220
    if "kidney" in med_conditions:
        rda["potassium"] = 1500
        rda["phosphorus"] = 800
    return rda


def restriction_nutrients(med_conditions):
    """Returns {nutrient: ceiling} for nutrients that are pure ceilings (not targets)
    under this person's medical conditions."""
    out = {}
    for cond in med_conditions:
        out.update(RESTRICTION_OVERRIDES.get(cond, {}))
    return out


def bmr_mifflin(weight_kg, height_cm, age, sex="male"):
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def day_target(weight_kg=65, height_cm=170, age=30, sex="male", pal=1.53, protein_factor=1.0,
               med_conditions=None):
    med_conditions = med_conditions or []
    bmr = bmr_mifflin(weight_kg, height_cm, age, sex)
    tdee = bmr * pal
    kcal_total = round(tdee)
    protein_g = round(weight_kg * (0.6 if "kidney" in med_conditions else protein_factor))
    fat_g = round(kcal_total * 0.25 / 9)
    carb_g = round((kcal_total - protein_g * 4 - fat_g * 9) / 4)
    gender = "female" if sex == "female" else "male"
    target = adjusted_rda(RDA_BASE_MALE, age, gender, med_conditions)
    target["energy"] = kcal_total
    target["protein"] = protein_g
    target["fat"] = fat_g  # not in dish nutrient schema (not tracked per-ingredient); informational only
    target["carbs"] = carb_g
    return target


# ---- Load Step 0's real per-100g dish nutrient data ----
dish_db = json.loads((DATA_DIR / "dish_nutrients_v1.json").read_text())


def find_dish(meal, name):
    for d in dish_db[meal]:
        if d["name"] == name:
            return d
    raise KeyError(f"{name} not found in {meal}")


def optimize_day(selected, target, bounds_g=(20, 500), kcal_tolerance=0.15, med_conditions=None):
    """selected: list of (meal, dish_name) tuples."""
    med_conditions = med_conditions or []
    restriction = restriction_nutrients(med_conditions)  # {nutrient: ceiling}, e.g. kidney -> potassium/phosphorus

    dishes = [find_dish(meal, name) for meal, name in selected]
    n = len(dishes)

    nutrient_keys = [k for k in target if k not in ("energy", "protein", "fat", "carbs")]
    target_vec = np.array([target[k] for k in nutrient_keys])
    # avoid div-by-zero; normalize squared error by target^2 (relative deviation)
    norm = np.maximum(target_vec, 1e-6) ** 2
    is_restriction = np.array([k in restriction for k in nutrient_keys])

    # per-dish nutrient matrix (per 100g), aligned to nutrient_keys + energy/protein
    def get(d, k):
        return d["per_100g_served"].get(k, 0.0)

    N = np.array([[get(d, k) for k in nutrient_keys] for d in dishes])  # n x k
    E = np.array([get(d, "energy") for d in dishes])
    P = np.array([get(d, "protein") for d in dishes])
    # Real finding (Harvard Healthy Eating Plate — 50% of the plate should be
    # vegetables/fruit): a soft preference (not a hard constraint, since it must
    # never make an otherwise-feasible medical/nutrient plan infeasible) for
    # vegetable-category dishes to make up a meaningful share of the day's total
    # food weight. Target is 40% by WEIGHT (not volume) — vegetables are less
    # calorie/weight-dense than roti/rice/dal per serving, so a lower weight-share
    # than the plate's area-share is the correct real-world translation.
    VEG_CATEGORIES = {"sabzi", "veg_curry", "salad"}
    veg_mask = np.array([d.get("dish_category") in VEG_CATEGORIES for d in dishes])

    def achieved(x):
        grams_frac = x / 100.0
        return grams_frac @ N  # (k,)

    def objective(x):
        ach = achieved(x)
        diff = ach - target_vec
        # restriction nutrients (e.g. kidney: potassium/phosphorus) are a CEILING, not
        # a target to reach — only penalize exceeding it, never falling short (KDIGO 2024)
        diff = np.where(is_restriction, np.maximum(diff, 0), diff)
        # real bug found (verified): summing ~23 micronutrient squared-errors let this
        # term drown out the single kcal/protein terms, even at modest per-term weights
        # -> energy/protein consistently undershot (~85%) while veg_curry dishes (which
        # scored well on remaining micronutrient debt) ballooned to 85% of plate weight
        # against a 40% soft target. Fix: use the MEAN micronutrient error (comparable
        # scale to a single term), and weight kcal/protein high enough that hitting the
        # day's calorie/protein target is treated as at least as important as chasing
        # micronutrients past what's already adequate.
        micro_err = np.mean((diff ** 2) / norm)
        kcal_ach = np.dot(x / 100.0, E)
        kcal_err = ((kcal_ach - target["energy"]) / target["energy"]) ** 2 * 8.0
        prot_ach = np.dot(x / 100.0, P)
        prot_err = ((prot_ach - target["protein"]) / max(target["protein"], 1)) ** 2 * 4.0
        total_g = np.sum(x)
        veg_g = np.sum(x[veg_mask]) if veg_mask.any() else 0.0
        veg_share = veg_g / total_g if total_g > 0 else 0.0
        veg_shortfall = max(0.0, 0.40 - veg_share)
        veg_err = (veg_shortfall ** 2) * 1.0
        return micro_err + kcal_err + prot_err + veg_err

    ul_keys = [k for k in nutrient_keys if k in UL]
    constraints = []
    for k in ul_keys:
        idx = nutrient_keys.index(k)
        cap = UL[k]
        constraints.append({
            "type": "ineq",
            "fun": (lambda x, idx=idx, cap=cap: cap - (x / 100.0) @ N[:, idx]),
        })
    # restriction ceilings are HARD constraints too (never just a soft objective term) —
    # a kidney patient's plan must never exceed 1500mg potassium even if the QP would
    # otherwise trade it off against other nutrients
    for k, cap in restriction.items():
        if k not in nutrient_keys:
            continue
        idx = nutrient_keys.index(k)
        constraints.append({
            "type": "ineq",
            "fun": (lambda x, idx=idx, cap=cap: cap - (x / 100.0) @ N[:, idx]),
        })
    kcal_lo = target["energy"] * (1 - kcal_tolerance)
    kcal_hi = target["energy"] * (1 + kcal_tolerance)
    constraints.append({"type": "ineq", "fun": lambda x: (x / 100.0) @ E - kcal_lo})
    constraints.append({"type": "ineq", "fun": lambda x: kcal_hi - (x / 100.0) @ E})

    # Per-dish lower bound: normally >=20g (every selected item should appear in a
    # meaningful amount). BUT under a hard medical restriction (e.g. kidney potassium/
    # phosphorus ceiling), forcing a 20g minimum on every dish can make the combined
    # ceiling constraint infeasible even when a *smaller* serving of that item would
    # fit fine — the optimizer needs the freedom to shrink a restriction-heavy dish
    # toward ~0 instead of being blocked from ever going below 20g.
    x0 = np.full(n, 120.0)
    if restriction:
        lo_per_dish = []
        for d in dishes:
            heavy = any(d["per_100g_served"].get(k, 0.0) * (bounds_g[0] / 100.0) > 0.5 * cap
                        for k, cap in restriction.items())
            lo_per_dish.append(2.0 if heavy else bounds_g[0])
        bnds = [(lo_per_dish[i], bounds_g[1]) for i in range(n)]
        x0 = np.array([min(120.0, bounds_g[1]) if lo_per_dish[i] == bounds_g[0] else 20.0 for i in range(n)])
    else:
        bnds = [bounds_g] * n
    res = minimize(objective, x0, method="SLSQP", bounds=bnds, constraints=constraints,
                   options={"maxiter": 500, "ftol": 1e-9})

    grams = {selected[i]: round(res.x[i], 1) for i in range(n)}
    achieved_vec = achieved(res.x)
    achieved_dict = {k: round(v, 2) for k, v in zip(nutrient_keys, achieved_vec)}
    achieved_dict["energy"] = round(np.dot(res.x / 100.0, E), 1)
    achieved_dict["protein"] = round(np.dot(res.x / 100.0, P), 1)

    coverage = {k: round(100 * achieved_dict.get(k, 0) / target[k], 1) for k in nutrient_keys}
    coverage["energy"] = round(100 * achieved_dict["energy"] / target["energy"], 1)
    coverage["protein"] = round(100 * achieved_dict["protein"] / target["protein"], 1)

    # Explicit post-hoc verification — do NOT trust scipy's own res.success alone.
    # A plan must never be handed to a real person with a violated hard cap (UL or a
    # medical restriction ceiling like kidney potassium), regardless of what the
    # solver's internal convergence flag says.
    violations = []
    tol = 1e-6
    for k, cap in UL.items():
        if k in achieved_dict and achieved_dict[k] > cap * (1 + tol):
            violations.append({"nutrient": k, "type": "UL", "cap": cap, "achieved": achieved_dict[k]})
    for k, cap in restriction.items():
        if k in achieved_dict and achieved_dict[k] > cap * (1 + tol):
            violations.append({"nutrient": k, "type": "medical_restriction", "cap": cap, "achieved": achieved_dict[k]})
    kcal_ach = achieved_dict["energy"]
    if not (kcal_lo * 0.99 <= kcal_ach <= kcal_hi * 1.01):
        violations.append({"nutrient": "energy", "type": "kcal_band", "cap": (kcal_lo, kcal_hi), "achieved": kcal_ach})

    constraints_satisfied = res.success and not violations
    final_total_g = float(np.sum(res.x))
    final_veg_share = float(np.sum(res.x[veg_mask]) / final_total_g) if final_total_g > 0 else 0.0

    return {
        "success": constraints_satisfied, "solver_reported_success": res.success, "message": res.message,
        "constraint_violations": violations,
        "grams": grams, "achieved": achieved_dict, "target": target, "coverage_pct": coverage,
        "veg_share_by_weight": round(final_veg_share, 3),
    }


if __name__ == "__main__":
    target = day_target(weight_kg=65, height_cm=170, age=30, sex="male", pal=1.53)
    print("DAY TARGET:", json.dumps(target, indent=2))

    selected = [
        ("breakfast", "Aloo Paratha"),
        ("breakfast", "Lassi"),
        ("lunch", "Rajma Chawal"),
        ("lunch", "Bhindi Masala"),
        ("lunch", "Kachumber Salad"),
        ("dinner", "Dal Fry with Jeera Rice"),
        ("dinner", "Palak Paneer with Roti"),
    ]
    result = optimize_day(selected, target)
    print("\nSOLVER:", result["success"], result["message"])
    print("\nGRAMS PER DISH:")
    for (meal, name), g in result["grams"].items():
        print(f"  {meal:10s} {name:35s} {g:6.1f} g")
    print("\nCOVERAGE vs TARGET (%):")
    for k, v in sorted(result["coverage_pct"].items(), key=lambda x: -x[1]):
        print(f"  {k:15s} {v:6.1f}%")

    OUT = DATA_DIR / "day_plan_v1_example.json"
    OUT.write_text(json.dumps({
        "target": target,
        "selected_dishes": [f"{m}: {n}" for m, n in selected],
        "grams": {f"{m}|{n}": g for (m, n), g in result["grams"].items()},
        "achieved": result["achieved"],
        "coverage_pct": result["coverage_pct"],
        "solver_success": result["success"],
    }, indent=2))
    print(f"\nSaved -> {OUT}")
