"""
Broader verification sweep: run the full severity+medical-aware pipeline across
every region that has dinner data (North/South/Northeast — East/West/Central&Islands
dinner research intentionally not done, existing data judged sufficient), both diet
types, and several medical-condition combinations. Reports real pass/fail counts,
not just a single happy-path example.
"""
import json
from pathlib import Path
from full_pipeline_with_severity import run

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")

REGIONS = ["North", "South", "Northeast"]  # only regions with dinner data
DIETS = ["veg", "non-veg"]
MED_CONDITION_SETS = [
    [], ["diabetes"], ["kidney"], ["bp_high"], ["diabetes", "kidney"], ["pregnancy"],
]
DEFICIENCY_SETS = [
    {}, {"iron": "high"}, {"vitamin_d": "severe"}, {"iron": "high", "vitamin_b12": "medium"},
]


def check_result(result, med_conditions):
    issues = []
    if not result["solver_success"]:
        issues.append("solver_did_not_converge_or_violated_constraints")
    # verify restriction ceilings genuinely respected
    if "kidney" in med_conditions:
        if result["achieved"].get("potassium", 0) > 1500 * 1.01:
            issues.append(f"POTASSIUM_CEILING_VIOLATED={result['achieved'].get('potassium')}")
        if result["achieved"].get("phosphorus", 0) > 800 * 1.01:
            issues.append(f"PHOSPHORUS_CEILING_VIOLATED={result['achieved'].get('phosphorus')}")
    # verify no sweet-category dish leaked in for diabetes (spot check by name)
    if "diabetes" in med_conditions:
        from day_plan_optimizer import MEDICAL_AVOID_KEYWORDS
        for name in result["selected_dishes"].values():
            if any(kw in name.lower() for kw in MEDICAL_AVOID_KEYWORDS["diabetes"]):
                issues.append(f"DIABETES_AVOID_LEAK={name}")
    # dinner should never contain a curd/kadhi dish
    from dish_selector import is_curd_dish
    for slot_key, name in result["selected_dishes"].items():
        if slot_key.startswith("dinner|") and is_curd_dish(name):
            issues.append(f"DAHI_AT_DINNER_LEAK={name}")
    return issues


def main():
    total, passed = 0, 0
    all_issues = []
    for region in REGIONS:
        for diet in DIETS:
            for med in MED_CONDITION_SETS:
                for defs in DEFICIENCY_SETS:
                    total += 1
                    try:
                        result = run(region, diet, defs, med_conditions=med)
                        issues = check_result(result, med)
                    except Exception as e:
                        issues = [f"EXCEPTION: {type(e).__name__}: {e}"]
                    if issues:
                        all_issues.append({
                            "region": region, "diet": diet, "med_conditions": med,
                            "deficiencies": defs, "issues": issues,
                        })
                    else:
                        passed += 1

    print(f"Total scenarios tested: {total}")
    print(f"Passed clean: {passed} ({100*passed/total:.1f}%)")
    print(f"Failed/flagged: {len(all_issues)}")
    for item in all_issues:
        print(f"  FAIL: region={item['region']} diet={item['diet']} med={item['med_conditions']} "
              f"deficiencies={item['deficiencies']} -> {item['issues']}")

    (DATA_DIR / "test_sweep_results.json").write_text(json.dumps({
        "total": total, "passed": passed, "failures": all_issues,
    }, indent=2, default=str))
    print(f"\nSaved -> {DATA_DIR / 'test_sweep_results.json'}")


if __name__ == "__main__":
    main()
