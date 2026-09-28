/**
 * Personalized Today's Nutrition Target
 * Combines: AI Model (deficiency probability) + Layer 6 (RDA) → today's target
 *
 * Medical basis: Therapeutic Repletion Dose (WHO/ICMR-NIN clinical nutrition)
 * Deficient person needs RDA × multiplier to replete stores faster.
 * All targets capped at UL (Upper Tolerable Limit) to prevent toxicity.
 *
 * Sources:
 *  - ICMR-NIN 2020 UL values
 *  - IOM/USDA DRI Tolerable Upper Intake Levels
 *  - WHO/FAO 2004 safe upper limits
 */

import { DailyRequirements } from "./layer6-rda-calculator";

export type DeficiencyLevel = "normal" | "mild" | "moderate" | "severe";

export interface NutrientDeficiency {
  probability: number;   // 0–1 from AI model
  deficient:   boolean;
  threshold:   number;
}

// Upper Tolerable Limits (UL) per day — ICMR-NIN 2020 + IOM DRI
// null = no established UL (safe at high dietary intake)
const UL: Record<string, number | null> = {
  vitamin_a_ug:   3000,    // µg RAE — teratogenic above UL
  vitamin_d_ug:   100,     // µg (4000 IU)
  vitamin_e_mg:   1000,    // mg
  vitamin_k_ug:   null,    // no UL
  vitamin_c_mg:   2000,    // mg
  vitamin_b1_mg:  null,
  vitamin_b2_mg:  null,
  vitamin_b3_mg:  35,      // mg (niacin flush / liver toxicity above UL)
  vitamin_b6_mg:  100,     // mg (neuropathy above UL)
  vitamin_b12_ug: null,
  folate_ug:      1000,    // µg DFE (masks B12 deficiency above UL)
  calcium_mg:     2500,
  phosphorus_mg:  4000,
  magnesium_mg:   350,     // supplemental only (food has no UL)
  iron_mg:        45,      // mg
  zinc_mg:        40,      // mg
  selenium_ug:    400,     // µg
  copper_mg:      10,      // mg
  potassium_mg:   4700,    // WHO safe upper limit (kidney toxicity above)
  iodine_ug:      1100,    // µg
  omega3_mg:      3000,    // mg (EPA+DHA; ALA has no UL)
  protein_g:      null,
  carbs_g:        null,
  fat_g:          null,
  fiber_g:        null,
};

// Severity multipliers (therapeutic repletion — medical literature)
const MULTIPLIER: Record<DeficiencyLevel, number> = {
  normal:   1.0,   // maintain RDA
  mild:     1.5,   // 50% more — replete over 4-6 weeks
  moderate: 2.0,   // double — replete over 2-4 weeks
  severe:   2.5,   // 2.5× — aggressive repletion (supplement often needed)
};

export function getDeficiencyLevel(
  probability: number,
  threshold: number,
): DeficiencyLevel {
  if (probability < threshold)        return "normal";
  if (probability < 0.70)             return "mild";
  if (probability < 0.85)             return "moderate";
  return "severe";
}

export interface NutrientTarget {
  rda:              number;   // Layer 6 standard requirement
  target:           number;   // today's personalized target (after multiplier + UL cap)
  deficiency_level: DeficiencyLevel;
  probability:      number;
  multiplier:       number;
  capped_at_ul:     boolean;
  needs_supplement: boolean;  // true if severe and UL cap prevents reaching repletion dose
  unit:             string;
}

export interface PersonalizedTargets {
  calories_kcal:  number;
  protein_g:      NutrientTarget;
  carbs_g:        NutrientTarget;
  fat_g:          NutrientTarget;
  fiber_g:        NutrientTarget;
  vitamin_a_ug:   NutrientTarget;
  vitamin_d_ug:   NutrientTarget;
  vitamin_e_mg:   NutrientTarget;
  vitamin_k_ug:   NutrientTarget;
  vitamin_c_mg:   NutrientTarget;
  vitamin_b1_mg:  NutrientTarget;
  vitamin_b2_mg:  NutrientTarget;
  vitamin_b3_mg:  NutrientTarget;
  vitamin_b6_mg:  NutrientTarget;
  vitamin_b12_ug: NutrientTarget;
  folate_ug:      NutrientTarget;
  calcium_mg:     NutrientTarget;
  phosphorus_mg:  NutrientTarget;
  magnesium_mg:   NutrientTarget;
  iron_mg:        NutrientTarget;
  zinc_mg:        NutrientTarget;
  selenium_ug:    NutrientTarget;
  copper_mg:      NutrientTarget;
  potassium_mg:   NutrientTarget;
  iodine_ug:      NutrientTarget;
  omega3_mg:      NutrientTarget;
}

const UNITS: Record<string, string> = {
  protein_g: "g", carbs_g: "g", fat_g: "g", fiber_g: "g",
  vitamin_a_ug: "µg RAE", vitamin_d_ug: "µg", vitamin_e_mg: "mg",
  vitamin_k_ug: "µg", vitamin_c_mg: "mg", vitamin_b1_mg: "mg",
  vitamin_b2_mg: "mg", vitamin_b3_mg: "mg NE", vitamin_b6_mg: "mg",
  vitamin_b12_ug: "µg", folate_ug: "µg DFE", calcium_mg: "mg",
  phosphorus_mg: "mg", magnesium_mg: "mg", iron_mg: "mg",
  zinc_mg: "mg", selenium_ug: "µg", copper_mg: "mg",
  potassium_mg: "mg", iodine_ug: "µg", omega3_mg: "mg",
};

function makeTarget(
  key: string,
  rda: number,
  deficiencies: Record<string, NutrientDeficiency>,
): NutrientTarget {
  const def  = deficiencies[key];
  const prob = def?.probability ?? 0;
  const thr  = def?.threshold  ?? 0.5;

  const level      = getDeficiencyLevel(prob, thr);
  const multiplier = MULTIPLIER[level];
  const ideal      = rda * multiplier;
  const ul         = UL[key] ?? null;
  const capped     = ul !== null && ideal > ul;
  const target     = capped ? ul : ideal;

  // If severe but UL prevents reaching full repletion dose → recommend supplement
  const needs_supplement = level === "severe" && capped;

  return {
    rda:              Math.round(rda * 10) / 10,
    target:           Math.round(target * 10) / 10,
    deficiency_level: level,
    probability:      Math.round(prob * 1000) / 1000,
    multiplier,
    capped_at_ul:     capped,
    needs_supplement,
    unit:             UNITS[key] ?? "",
  };
}

// AI model nutrient key → target key mapping
const AI_TO_TARGET: Record<string, string> = {
  iron:        "iron_mg",
  calcium:     "calcium_mg",
  vitamin_d:   "vitamin_d_ug",
  folate:      "folate_ug",
  vitamin_b12: "vitamin_b12_ug",
  vitamin_c:   "vitamin_c_mg",
  vitamin_a:   "vitamin_a_ug",
  vitamin_e:   "vitamin_e_mg",
  vitamin_k:   "vitamin_k_ug",
  vitamin_b1:  "vitamin_b1_mg",
  vitamin_b2:  "vitamin_b2_mg",
  vitamin_b3:  "vitamin_b3_mg",
  vitamin_b6:  "vitamin_b6_mg",
  magnesium:   "magnesium_mg",
  zinc:        "zinc_mg",
  selenium:    "selenium_ug",
  copper:      "copper_mg",
  potassium:   "potassium_mg",
  phosphorus:  "phosphorus_mg",
  omega3:      "omega3_mg",
  iodine:      "iodine_ug",
};

export function calculatePersonalizedTargets(
  rda:         DailyRequirements,
  deficiencies: Record<string, NutrientDeficiency>,   // from AI model
): PersonalizedTargets {

  // Remap AI keys to target keys
  const mapped: Record<string, NutrientDeficiency> = {};
  for (const [aiKey, targetKey] of Object.entries(AI_TO_TARGET)) {
    if (deficiencies[aiKey]) mapped[targetKey] = deficiencies[aiKey];
  }

  const t = (key: string, rda_val: number) => makeTarget(key, rda_val, mapped);

  return {
    calories_kcal:  rda.tdee_kcal,
    protein_g:      t("protein_g",      rda.protein_g),
    carbs_g:        t("carbs_g",         rda.carbs_g),
    fat_g:          t("fat_g",           rda.fat_g),
    fiber_g:        t("fiber_g",         rda.fiber_g),
    vitamin_a_ug:   t("vitamin_a_ug",    rda.vitamin_a_ug),
    vitamin_d_ug:   t("vitamin_d_ug",    rda.vitamin_d_ug),
    vitamin_e_mg:   t("vitamin_e_mg",    rda.vitamin_e_mg),
    vitamin_k_ug:   t("vitamin_k_ug",    rda.vitamin_k_ug),
    vitamin_c_mg:   t("vitamin_c_mg",    rda.vitamin_c_mg),
    vitamin_b1_mg:  t("vitamin_b1_mg",   rda.vitamin_b1_mg),
    vitamin_b2_mg:  t("vitamin_b2_mg",   rda.vitamin_b2_mg),
    vitamin_b3_mg:  t("vitamin_b3_mg",   rda.vitamin_b3_mg),
    vitamin_b6_mg:  t("vitamin_b6_mg",   rda.vitamin_b6_mg),
    vitamin_b12_ug: t("vitamin_b12_ug",  rda.vitamin_b12_ug),
    folate_ug:      t("folate_ug",        rda.folate_ug),
    calcium_mg:     t("calcium_mg",       rda.calcium_mg),
    phosphorus_mg:  t("phosphorus_mg",    rda.phosphorus_mg),
    magnesium_mg:   t("magnesium_mg",     rda.magnesium_mg),
    iron_mg:        t("iron_mg",          rda.iron_mg),
    zinc_mg:        t("zinc_mg",          rda.zinc_mg),
    selenium_ug:    t("selenium_ug",      rda.selenium_ug),
    copper_mg:      t("copper_mg",        rda.copper_mg),
    potassium_mg:   t("potassium_mg",     rda.potassium_mg),
    iodine_ug:      t("iodine_ug",        rda.iodine_ug),
    omega3_mg:      t("omega3_mg",        rda.omega3_mg),
  };
}

// Summary helpers
export function getSupplement_flags(targets: PersonalizedTargets): string[] {
  return Object.entries(targets)
    .filter(([k, v]) => k !== "calories_kcal" && (v as NutrientTarget).needs_supplement)
    .map(([k]) => k);
}

export function getDeficientNutrients(targets: PersonalizedTargets): {
  key: string; level: DeficiencyLevel; target: number; unit: string
}[] {
  return Object.entries(targets)
    .filter(([k, v]) => k !== "calories_kcal" && (v as NutrientTarget).deficiency_level !== "normal")
    .map(([k, v]) => {
      const t = v as NutrientTarget;
      return { key: k, level: t.deficiency_level, target: t.target, unit: t.unit };
    })
    .sort((a, b) => {
      const order = { severe: 0, moderate: 1, mild: 2, normal: 3 };
      return order[a.level] - order[b.level];
    });
}
