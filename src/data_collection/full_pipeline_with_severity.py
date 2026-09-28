"""
Full pipeline, severity-aware: Step -1b (boosted target) -> Step 2 (dish selection)
-> Step 3 (exact grams) -> supplement fallback for whatever food still can't cover.

This is the concrete fix for: "severe and moderate case ko tu identify hi nahi kar
raha — unke liye recipe kuch alag hoga, supplement bhi recommend honge" — the
recipe (dish selection + grams) now actually changes based on how severe each
flagged deficiency is, and a real supplement is recommended wherever food alone
(even after severity-boosting) can't close the gap.
"""
import json
from pathlib import Path

from day_plan_optimizer import day_target, optimize_day, RDA_BASE_MALE, restriction_nutrients
from dish_selector import greedy_select_day, food_uncoverable
from severity_and_supplements import boosted_target, recommend_supplements

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")


def run(region, diet, deficiencies, weight_kg=65, height_cm=170, age=30, sex="male", pal=1.53,
        med_conditions=None, recent_dishes=None):
    med_conditions = med_conditions or []
    recent_dishes = recent_dishes or set()
    base = day_target(weight_kg, height_cm, age, sex, pal, med_conditions=med_conditions)
    target, applied = boosted_target(base, deficiencies)
    # keep energy/protein/fat/carbs unboosted (severity boosting is micronutrient-only)
    for k in ("energy", "protein", "fat", "carbs"):
        target[k] = base[k]
    # restriction ceilings (e.g. kidney -> potassium/phosphorus) must never be boosted
    # upward by a deficiency flag — they stay at the medically-restricted value
    for k in restriction_nutrients(med_conditions):
        target[k] = base[k]

    restriction = restriction_nutrients(med_conditions)
    gaps = food_uncoverable(region, diet, target)
    chosen, _, forced_repeats = greedy_select_day(region, diet, target, med_conditions=med_conditions, restriction=restriction, recent_dishes=recent_dishes)
    selected = [(meal, name) for (meal, slot), name in chosen.items()]
    result = optimize_day(selected, target, med_conditions=med_conditions)

    supplements = recommend_supplements(deficiencies, result["achieved"], target)

    return {
        "base_rda": base, "severity_applied": applied, "boosted_target": target,
        "food_uncoverable_nutrients": gaps,
        "selected_dishes": {f"{m}|{s}": n for (m, s), n in chosen.items()},
        "grams": {f"{m}|{n}": g for (m, n), g in result["grams"].items()},
        "achieved": result["achieved"], "coverage_pct": result["coverage_pct"],
        "solver_success": result["success"], "supplement_recommendations": supplements,
        "forced_repeats": forced_repeats,
    }


if __name__ == "__main__":
    region, diet = "North", "veg"
    deficiencies = {"iron": "high", "vitamin_d": "severe", "vitamin_b12": "medium"}

    print(f"=== BASELINE (no deficiency, flat RDA) ===")
    baseline = run(region, diet, {})
    print("Iron dish/grams for dal slot:", baseline["selected_dishes"].get("lunch|dal"),
          "->", [v for k, v in baseline["grams"].items() if "Dal" in k or "dal" in k.lower()])
    print("Iron coverage:", baseline["coverage_pct"].get("iron"), "%")

    print(f"\n=== SEVERITY CASE (iron=high, vitamin_d=severe, b12=medium) ===")
    result = run(region, diet, deficiencies)
    print("Boosted targets:")
    for k, v in result["severity_applied"].items():
        print(f"  {k}: RDA {v['base_rda']} -> target {v['boosted_target']} ({v['risk_level']}, x{v['multiplier']})")

    print("\nSelected dishes:")
    for slot, name in result["selected_dishes"].items():
        print(f"  {slot:25s} -> {name}")

    print("\nGrams:")
    for k, g in result["grams"].items():
        print(f"  {k:45s} {g}g")

    print("\nAchieved vs boosted target (key nutrients):")
    for n in ["iron", "vitamin_d", "vitamin_b12"]:
        cov = result["coverage_pct"].get(n, 0)
        print(f"  {n:12s} achieved={result['achieved'].get(n)} target={result['boosted_target'][n]} coverage={cov}%")

    print(f"\n=== MEDICAL CASE: diabetes + kidney patient (no deficiencies flagged) ===")
    med_result = run(region, diet, {}, med_conditions=["diabetes", "kidney"])
    print("Potassium target (should be restricted to 1500mg, not 3500mg RDA):",
          med_result["boosted_target"]["potassium"])
    print("Phosphorus target (should be restricted to 800mg):", med_result["boosted_target"]["phosphorus"])
    print("Protein target (kidney -> 0.6g/kg = 39g for 65kg):", med_result["boosted_target"]["protein"])
    print("Potassium ACHIEVED (must be <= 1500):", med_result["achieved"].get("potassium"))
    print("Phosphorus ACHIEVED (must be <= 800):", med_result["achieved"].get("phosphorus"))
    print("Selected dishes (no 'sweet' category should appear for diabetes):")
    for slot, name in med_result["selected_dishes"].items():
        print(f"  {slot:25s} -> {name}")

    print("\n=== SUPPLEMENT RECOMMENDATIONS ===")
    if result["supplement_recommendations"]:
        for rec in result["supplement_recommendations"]:
            print(f"  {rec['nutrient']} ({rec['risk_level']} risk): food gave {rec['food_coverage_pct']}% of "
                  f"boosted target -> {rec['supplement_recommended']}")
    else:
        print("  None needed — food alone reached target for all flagged deficiencies.")

    print(f"\nCOMPARISON: baseline recipe used {baseline['selected_dishes'].get('lunch|dal')} for lunch dal slot; "
          f"severity-case recipe used {result['selected_dishes'].get('lunch|dal')} "
          f"({'SAME dish, different grams' if baseline['selected_dishes'].get('lunch|dal') == result['selected_dishes'].get('lunch|dal') else 'DIFFERENT dish selected'})")

    OUT = DATA_DIR / "day_plan_severity_example.json"
    OUT.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nSaved -> {OUT}")
