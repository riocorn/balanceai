/**
 * Layer 6 — Personalized Daily Nutrition & Calorie Requirements
 *
 * Sources:
 *  - ICMR-NIN 2020 "Nutrient Requirements for Indians" (primary)
 *  - WHO/FAO 2004 "Vitamin and Mineral Requirements in Human Nutrition"
 *  - IOM/USDA DRI 2019-2023
 *  - Mifflin-St Jeor equation for BMR
 */

export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "very_active";
export type Gender        = "male" | "female";
export type LifeStage     = "normal" | "pregnant" | "lactating";

export interface RDAInput {
  age:            number;
  gender:         Gender;
  weight_kg:      number;
  height_cm:      number;
  activity_level: ActivityLevel;
  life_stage:     LifeStage;
}

export interface DailyRequirements {
  // Energy
  bmr_kcal:       number;
  tdee_kcal:      number;

  // Macros
  protein_g:      number;
  carbs_g:        number;
  fat_g:          number;
  fiber_g:        number;
  water_ml:       number;

  // Fat-soluble vitamins
  vitamin_a_ug:   number;   // µg RAE
  vitamin_d_ug:   number;   // µg  (× 40 = IU)
  vitamin_d_iu:   number;   // IU
  vitamin_e_mg:   number;   // mg α-TE
  vitamin_k_ug:   number;   // µg

  // Water-soluble vitamins
  vitamin_c_mg:   number;
  vitamin_b1_mg:  number;
  vitamin_b2_mg:  number;
  vitamin_b3_mg:  number;   // mg NE
  vitamin_b6_mg:  number;
  vitamin_b12_ug: number;   // µg
  folate_ug:      number;   // µg DFE

  // Minerals
  calcium_mg:     number;
  phosphorus_mg:  number;
  magnesium_mg:   number;
  iron_mg:        number;
  zinc_mg:        number;
  selenium_ug:    number;
  copper_mg:      number;
  potassium_mg:   number;
  iodine_ug:      number;

  // Omega-3
  omega3_mg:      number;

  notes:          string[];
}

// Physical Activity Level multipliers (Mifflin-St Jeor × PAL)
const PAL: Record<ActivityLevel, number> = {
  sedentary:   1.20,
  light:       1.375,
  moderate:    1.55,
  active:      1.725,
  very_active: 1.90,
};

const PROTEIN_PER_KG: Record<ActivityLevel, number> = {
  sedentary:   0.80,
  light:       0.90,
  moderate:    1.00,
  active:      1.20,
  very_active: 1.50,
};

export function calculateDailyRequirements(input: RDAInput): DailyRequirements {
  const { age, gender, weight_kg, height_cm, activity_level, life_stage } = input;
  const notes: string[] = [];

  // ── BMR: Mifflin-St Jeor ─────────────────────────────────────────────────
  const bmr = gender === "male"
    ? 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    : 10 * weight_kg + 6.25 * height_cm - 5 * age - 161;

  let tdee = bmr * PAL[activity_level];
  if (life_stage === "pregnant")  { tdee += 350; notes.push("Pregnancy: +350 kcal/day"); }
  if (life_stage === "lactating") { tdee += 600; notes.push("Lactation: +600 kcal/day"); }

  // ── Protein ──────────────────────────────────────────────────────────────
  let protein_g_per_kg = PROTEIN_PER_KG[activity_level];
  if (age >= 60) { protein_g_per_kg = Math.max(protein_g_per_kg, 1.10); notes.push("Age ≥60: min 1.1g/kg protein"); }
  if (life_stage === "pregnant")  protein_g_per_kg += 0.25;
  if (life_stage === "lactating") protein_g_per_kg += 0.30;
  const protein_g = weight_kg * protein_g_per_kg;

  // ── Carbs & Fat (ICMR-NIN AMDR: 60% carbs, 27% fat) ─────────────────────
  const remaining = tdee - protein_g * 4;
  const carbs_g   = (remaining * 0.60) / 4;
  const fat_g     = (remaining * 0.27) / 9;

  // ── Fiber (ICMR-NIN: 40g per 2000 kcal) ─────────────────────────────────
  const fiber_g = Math.min(Math.round(40 * tdee / 2000 * 10) / 10, 50);

  // ── Water (35ml/kg + activity bonus) ─────────────────────────────────────
  const water_ml = weight_kg * 35 + (["active","very_active"].includes(activity_level) ? 500 : 0);

  // ── Vitamin A (µg RAE) — ICMR-NIN 2020 ──────────────────────────────────
  let vitamin_a_ug = 600;
  if (life_stage === "pregnant")  vitamin_a_ug = 800;
  if (life_stage === "lactating") vitamin_a_ug = 950;

  // ── Vitamin D (µg) — 15µg (600 IU) for adults, 20µg (800 IU) for ≥60 ───
  let vitamin_d_ug = 15;
  if (age >= 60) { vitamin_d_ug = 20; notes.push("Age ≥60: Vit D 20µg (800 IU)"); }

  // ── Vitamin E (mg α-TE) ───────────────────────────────────────────────────
  let vitamin_e_mg = gender === "male" ? 10 : 8;
  if (["active","very_active"].includes(activity_level)) vitamin_e_mg += 2;

  // ── Vitamin K (µg) ────────────────────────────────────────────────────────
  let vitamin_k_ug = gender === "male" ? 65 : 55;
  if (age >= 60) vitamin_k_ug += 10;

  // ── Vitamin C (mg) — ICMR-NIN 2020 ───────────────────────────────────────
  let vitamin_c_mg = 65;
  if (life_stage === "pregnant")  vitamin_c_mg = 80;
  if (life_stage === "lactating") vitamin_c_mg = 115;
  if (["active","very_active"].includes(activity_level)) vitamin_c_mg += 15;

  // ── B vitamins ────────────────────────────────────────────────────────────
  const vitamin_b1_mg  = Math.max(0.5 * tdee / 1000, gender === "female" ? 1.0 : 1.2);
  const vitamin_b2_mg  = Math.max(0.6 * tdee / 1000, gender === "female" ? 1.1 : 1.4);
  const vitamin_b3_mg  = Math.max(6.6 * tdee / 1000, gender === "female" ? 11 : 14);

  let vitamin_b6_mg = age >= 51 ? 1.7 : 1.6;
  if (life_stage === "pregnant")  vitamin_b6_mg = 2.2;
  if (life_stage === "lactating") vitamin_b6_mg = 2.0;

  let vitamin_b12_ug = 1.2;
  if (age >= 60) { vitamin_b12_ug = 2.0; notes.push("Age ≥60: B12 2.0µg (reduced absorption)"); }
  if (life_stage === "pregnant")  vitamin_b12_ug = 1.9;
  if (life_stage === "lactating") vitamin_b12_ug = 2.0;

  let folate_ug = 200;
  if (life_stage === "pregnant")  folate_ug = 500;
  if (life_stage === "lactating") folate_ug = 300;

  // ── Calcium (mg) — ICMR-NIN 2020 ─────────────────────────────────────────
  let calcium_mg = age <= 18 ? 1000 : age <= 50 ? 800 : 1000;
  if (life_stage === "pregnant" || life_stage === "lactating") calcium_mg = 1200;

  // ── Phosphorus (mg) ───────────────────────────────────────────────────────
  const phosphorus_mg = life_stage === "normal" ? 800 : 1200;

  // ── Magnesium (mg) ────────────────────────────────────────────────────────
  let magnesium_mg = gender === "male" ? 340 : 310;
  if (age >= 30) magnesium_mg += 10;
  if (life_stage !== "normal") magnesium_mg += 50;
  if (["active","very_active"].includes(activity_level)) magnesium_mg += 30;

  // ── Iron (mg) — ICMR-NIN 2020 (non-heme dominant Indian diet) ────────────
  let iron_mg: number;
  if (gender === "male") {
    iron_mg = age >= 60 ? 11 : 17;
  } else {
    if (life_stage === "pregnant")       iron_mg = 35;
    else if (life_stage === "lactating") iron_mg = 21;
    else if (age <= 50)                  iron_mg = 21;
    else                                 iron_mg = 11;
    if (["active","very_active"].includes(activity_level) && age <= 50) {
      iron_mg += 3;
      notes.push("High activity female: +3mg iron (sweat/endurance losses)");
    }
  }

  // ── Zinc (mg) — ICMR-NIN 2020 (higher due to phytate in Indian diet) ────
  let zinc_mg = gender === "male" ? 12 : 10;
  if (life_stage !== "normal") zinc_mg += 4;
  if (["active","very_active"].includes(activity_level)) zinc_mg += 1.5;

  // ── Selenium (µg) ─────────────────────────────────────────────────────────
  let selenium_ug = 40;
  if (life_stage === "pregnant")  selenium_ug = 65;
  if (life_stage === "lactating") selenium_ug = 75;

  // ── Copper (mg) — ICMR-NIN 2020 ──────────────────────────────────────────
  const copper_mg = life_stage === "normal" ? 2.0 : 2.5;

  // ── Potassium (mg) — WHO 2012 ─────────────────────────────────────────────
  const potassium_mg = ["active","very_active"].includes(activity_level) ? 4000 : 3500;

  // ── Iodine (µg) ───────────────────────────────────────────────────────────
  const iodine_ug = life_stage === "normal" ? 150 : 200;

  // ── Omega-3 (mg) — ICMR-NIN 2020 ALA + WHO EPA/DHA ───────────────────────
  let omega3_mg = (gender === "male" ? 1600 : 1100) + 400;
  if (life_stage !== "normal") omega3_mg = 2600;
  if (["active","very_active"].includes(activity_level)) omega3_mg += 200;

  const r = (v: number, d = 1) => Math.round(v * 10 ** d) / 10 ** d;

  return {
    bmr_kcal:       r(bmr),
    tdee_kcal:      r(tdee),
    protein_g:      r(protein_g),
    carbs_g:        r(carbs_g),
    fat_g:          r(fat_g),
    fiber_g,
    water_ml:       Math.round(water_ml),
    vitamin_a_ug,
    vitamin_d_ug,
    vitamin_d_iu:   vitamin_d_ug * 40,
    vitamin_e_mg,
    vitamin_k_ug,
    vitamin_c_mg,
    vitamin_b1_mg:  r(vitamin_b1_mg, 2),
    vitamin_b2_mg:  r(vitamin_b2_mg, 2),
    vitamin_b3_mg:  r(vitamin_b3_mg),
    vitamin_b6_mg,
    vitamin_b12_ug,
    folate_ug,
    calcium_mg,
    phosphorus_mg,
    magnesium_mg,
    iron_mg,
    zinc_mg,
    selenium_ug,
    copper_mg,
    potassium_mg,
    iodine_ug,
    omega3_mg,
    notes,
  };
}

// ── Activity level labels (for UI) ────────────────────────────────────────────
export const ACTIVITY_LABELS: Record<ActivityLevel, { label: string; desc: string }> = {
  sedentary:   { label: "Sedentary",     desc: "Desk job, no exercise" },
  light:       { label: "Light",         desc: "Light exercise 1-3 days/week" },
  moderate:    { label: "Moderate",      desc: "Exercise 3-5 days/week" },
  active:      { label: "Active",        desc: "Hard exercise 6-7 days/week" },
  very_active: { label: "Very Active",   desc: "Physical labour / 2× daily training" },
};

// ── Nutrient display metadata (unit, display name) ────────────────────────────
export const NUTRIENT_META: Record<string, { label: string; unit: string; source: string }> = {
  protein_g:      { label: "Protein",      unit: "g",   source: "ICMR-NIN 2020" },
  carbs_g:        { label: "Carbohydrates",unit: "g",   source: "ICMR-NIN 2020" },
  fat_g:          { label: "Total Fat",    unit: "g",   source: "ICMR-NIN 2020" },
  fiber_g:        { label: "Dietary Fiber",unit: "g",   source: "ICMR-NIN 2020" },
  calcium_mg:     { label: "Calcium",      unit: "mg",  source: "ICMR-NIN 2020" },
  iron_mg:        { label: "Iron",         unit: "mg",  source: "ICMR-NIN 2020" },
  magnesium_mg:   { label: "Magnesium",    unit: "mg",  source: "ICMR-NIN 2020" },
  zinc_mg:        { label: "Zinc",         unit: "mg",  source: "ICMR-NIN 2020" },
  selenium_ug:    { label: "Selenium",     unit: "µg",  source: "ICMR-NIN 2020" },
  copper_mg:      { label: "Copper",       unit: "mg",  source: "ICMR-NIN 2020" },
  potassium_mg:   { label: "Potassium",    unit: "mg",  source: "WHO 2012" },
  phosphorus_mg:  { label: "Phosphorus",   unit: "mg",  source: "ICMR-NIN 2020" },
  iodine_ug:      { label: "Iodine",       unit: "µg",  source: "WHO/ICMR-NIN" },
  vitamin_a_ug:   { label: "Vitamin A",    unit: "µg RAE", source: "ICMR-NIN 2020" },
  vitamin_d_ug:   { label: "Vitamin D",    unit: "µg",  source: "WHO/ICMR-NIN" },
  vitamin_d_iu:   { label: "Vitamin D",    unit: "IU",  source: "WHO/ICMR-NIN" },
  vitamin_e_mg:   { label: "Vitamin E",    unit: "mg",  source: "ICMR-NIN 2020" },
  vitamin_k_ug:   { label: "Vitamin K",    unit: "µg",  source: "ICMR-NIN 2020" },
  vitamin_c_mg:   { label: "Vitamin C",    unit: "mg",  source: "ICMR-NIN 2020" },
  vitamin_b1_mg:  { label: "Vitamin B1 (Thiamine)",   unit: "mg", source: "ICMR-NIN 2020" },
  vitamin_b2_mg:  { label: "Vitamin B2 (Riboflavin)", unit: "mg", source: "ICMR-NIN 2020" },
  vitamin_b3_mg:  { label: "Vitamin B3 (Niacin)",     unit: "mg NE", source: "ICMR-NIN 2020" },
  vitamin_b6_mg:  { label: "Vitamin B6",  unit: "mg",  source: "ICMR-NIN 2020" },
  vitamin_b12_ug: { label: "Vitamin B12", unit: "µg",  source: "ICMR-NIN 2020" },
  folate_ug:      { label: "Folate",       unit: "µg DFE", source: "ICMR-NIN 2020" },
  omega3_mg:      { label: "Omega-3",      unit: "mg",  source: "ICMR-NIN 2020 + WHO" },
};
