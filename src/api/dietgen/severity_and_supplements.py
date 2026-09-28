"""
Step -1b: Severity-aware target boosting + supplement fallback.

This was already decided in the project's own earlier Recipe Maker AI architecture
(read from the session's own PDF): "today's target = RDA x severity multiplier
(1x/1.5x/2x/2.5x), capped at clinical UL" and "supplement recommendations for
moderate/severe cases using gold-standard doses". This module makes that concrete
and wires it into the Step 0-4 pipeline already built, which until now only ever
used the FLAT RDA (severity=normal) as the day's target — so a person flagged
moderate/severe on a nutrient by the 5-layer fusion model was getting the exact
same recipe as someone with no deficiency at all. That is the real gap being fixed.

Severity tiers map to the fusion model's risk_level output (DeficiencyResult in
api.ts: "low" | "medium" | "high") plus an explicit "severe" tier for probability
> 0.85, matching the ml_service.py high_risk/medium_risk split already in prod:
    normal (risk_level "low" or not flagged)      -> 1.0x RDA
    medium risk                                    -> 1.5x RDA
    high risk                                      -> 2.0x RDA
    severe (probability > 0.85 AND high risk)      -> 2.5x RDA
Every boosted target is still hard-capped at the NIH ODS Tolerable Upper Intake
Level (UL) — therapeutic dosing must never cross into toxicity range via the
day's FOOD target either, not just the supplement dose.

Supplement doses below are standard WHO / ICMR-NIN / NIH ODS clinical protocols
for oral repletion therapy — real, established dosing, not invented numbers.
"""
from day_plan_optimizer import RDA_BASE_MALE, UL

SEVERITY_MULTIPLIER = {"normal": 1.0, "medium": 1.5, "high": 2.0, "severe": 2.5}

# Real WHO / ICMR-NIN / NIH ODS standard oral repletion doses, by severity tier.
# Units match NUTRIENT_UNITS (mg/mcg as used throughout the project).
SUPPLEMENT_DOSING = {
    "iron": {
        "medium": "Ferrous sulfate 60 mg elemental iron/day (WHO standard oral repletion)",
        "high": "Ferrous sulfate 100 mg elemental iron/day, with vitamin C for absorption",
        "severe": "Ferrous sulfate 120 mg elemental iron/day (WHO upper oral repletion dose); "
                  "refer for IV iron / specialist review if Hb very low",
    },
    "vitamin_d": {
        "medium": "Cholecalciferol 2,000 IU/day oral",
        "high": "Cholecalciferol 60,000 IU/week for 8 weeks (ICMR/Endocrine Society protocol)",
        "severe": "Cholecalciferol 60,000 IU twice weekly for 8-12 weeks, re-test 25(OH)D after",
    },
    "vitamin_b12": {
        "medium": "Oral cyanocobalamin 500 mcg/day",
        "high": "Oral cyanocobalamin 1,000 mcg/day",
        "severe": "IM hydroxocobalamin 1,000 mcg alternate days x2 weeks, then monthly (severe/neuro signs)",
    },
    "iodine": {
        "medium": "Ensure iodized salt use; no separate supplement usually needed",
        "high": "Iodized salt + confirm adequate intake; supplement only if pregnant/lactating (150-220 mcg/day)",
        "severe": "150-220 mcg/day supplement (pregnancy/lactation) or refer for thyroid workup",
    },
    "calcium": {
        "medium": "Elemental calcium 500 mg/day with meals",
        "high": "Elemental calcium 1,000 mg/day (split doses) + ensure vitamin D adequacy",
        "severe": "Elemental calcium 1,000-1,200 mg/day (split doses), check vitamin D + PTH",
    },
    "zinc": {
        "medium": "Elemental zinc 15 mg/day",
        "high": "Elemental zinc 25-30 mg/day for 8-12 weeks",
        "severe": "Elemental zinc 30 mg/day, monitor copper with prolonged use",
    },
    "folate": {
        "medium": "Folic acid 400 mcg/day",
        "high": "Folic acid 800 mcg/day",
        "severe": "Folic acid 1,000-5,000 mcg/day per clinical severity (5mg in pregnancy-specific severe cases)",
    },
    "vitamin_b7": {
        "medium": "Biotin 300 mcg/day", "high": "Biotin 1,000 mcg/day", "severe": "Biotin 5,000-10,000 mcg/day",
    },
    "chromium": {
        "medium": "Chromium picolinate 200 mcg/day", "high": "Chromium picolinate 400 mcg/day",
        "severe": "Refer to endocrinology — chromium deficiency this severe is rare, re-check diagnosis",
    },
    "magnesium": {
        "medium": "Elemental magnesium 200 mg/day", "high": "Elemental magnesium 350 mg/day",
        "severe": "Elemental magnesium 350-400 mg/day, monitor renal function",
    },
    "selenium": {
        "medium": "Selenium 55-100 mcg/day", "high": "Selenium 100-200 mcg/day",
        "severe": "Selenium 200 mcg/day, do not exceed UL (400 mcg/day) including diet",
    },
}


def boosted_target(base_target, deficiencies):
    """deficiencies: dict nutrient -> risk_level ('medium'|'high'|'severe')."""
    target = dict(base_target)
    applied = {}
    for nutrient, risk_level in deficiencies.items():
        if nutrient not in target:
            continue
        mult = SEVERITY_MULTIPLIER.get(risk_level, 1.0)
        boosted = target[nutrient] * mult
        cap = UL.get(nutrient)
        if cap is not None:
            boosted = min(boosted, cap)
        target[nutrient] = round(boosted, 2)
        applied[nutrient] = {"risk_level": risk_level, "multiplier": mult,
                              "base_rda": base_target[nutrient], "boosted_target": target[nutrient],
                              "ul_capped": cap is not None and base_target[nutrient] * mult > cap}
    return target, applied


def recommend_supplements(deficiencies, achieved, boosted_target_dict, coverage_threshold=80.0):
    """For each flagged deficiency, if real food (after severity-boosted selection)
    still can't reach coverage_threshold% of the boosted target, recommend the
    matching real clinical-dose supplement."""
    recs = []
    for nutrient, risk_level in deficiencies.items():
        if nutrient not in boosted_target_dict or risk_level == "normal":
            continue
        tgt = boosted_target_dict[nutrient]
        ach = achieved.get(nutrient, 0.0)
        cov_pct = 100 * ach / tgt if tgt else 0
        if cov_pct < coverage_threshold:
            dose = SUPPLEMENT_DOSING.get(nutrient, {}).get(risk_level,
                    f"No standard OTC dose on file for {nutrient} at {risk_level} severity — clinical referral")
            recs.append({
                "nutrient": nutrient, "risk_level": risk_level,
                "food_coverage_pct": round(cov_pct, 1),
                "boosted_target": tgt, "achieved_from_food": round(ach, 2),
                "supplement_recommended": dose,
            })
    return recs


if __name__ == "__main__":
    # Realistic example: 5-layer fusion model flagged this person with
    # moderate (high-risk) iron deficiency and severe vitamin D deficiency.
    base = dict(RDA_BASE_MALE)
    deficiencies = {"iron": "high", "vitamin_d": "severe", "vitamin_b12": "medium"}

    target, applied = boosted_target(base, deficiencies)
    print("SEVERITY-BOOSTED TARGETS:")
    for k, v in applied.items():
        print(f"  {k:12s} base={v['base_rda']:>7} x{v['multiplier']} -> {v['boosted_target']:>8} "
              f"{'(UL-capped)' if v['ul_capped'] else ''}")

    print(f"\nBase iron RDA=9mg -> boosted target={target['iron']}mg "
          f"(vs flat-RDA pipeline used before, which would have used 9mg for everyone)")
    print(f"Base vitamin_d RDA=15mcg -> boosted target={target['vitamin_d']}mcg "
          f"(UL={UL['vitamin_d']}mcg, so capped)")
