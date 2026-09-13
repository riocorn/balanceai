/**
 * Sources:
 *  BMR   — Mifflin-St Jeor (1990), Am J Clin Nutr 51:241-247
 *  PAL   — WHO/FAO/UNU (2004), Human Energy Requirements
 *  RDA   — ICMR-NIN (2020), Recommended Dietary Allowances & EAR for Indians
 *  Macros— ICMR-NIN (2020), Dietary Guidelines for Indians
 *  Med   — ADA (2024) diabetes; JNC-8 / DASH hypertension; KDIGO (2024) CKD;
 *           ESHRE (2023) PCOD; WHO antenatal care for pregnancy
 */

import type { UserProfile } from "./db";

export type Occupation = "sedentary" | "moderate" | "heavy";
export type TodayActivity =
  | "rest"
  | "light_walk"    // <30 min walk
  | "walk_30_60"    // 30-60 min walk
  | "walk_60plus"   // >60 min walk
  | "yoga"
  | "gym_light"     // weights/cardio <45 min
  | "gym_heavy"     // intense >45 min
  | "run_30"        // running ~30 min
  | "run_60plus"
  | "heavy_labor";  // manual/construction work

export type FeelingToday = "normal" | "tired" | "very_tired" | "sick" | "stressed";

export interface NutritionTargets {
  kcal_total: number;
  protein_g: number;
  carb_g: number;
  fat_g: number;
  fiber_g: number;
  // per-meal kcal budget
  meal_kcal: { breakfast: number; lunch: number; snacks: number; dinner: number };
  // micronutrient RDAs adjusted for this person (mg or mcg as per NUTRIENT_UNITS)
  rda: Record<string, number>;
  // flags for recipe selection
  low_gi_priority: boolean;
  easy_digest: boolean;
  dash_mode: boolean;
}

// ── BMR (Mifflin-St Jeor 1990) ──────────────────────────────
function bmr(weight_kg: number, height_cm: number, age: number, gender: string): number {
  const base = 10 * weight_kg + 6.25 * height_cm - 5 * age;
  return gender === "female" ? base - 161 : base + 5;
}

// ── PAL (WHO/FAO/UNU 2004 — Table 5.2) ─────────────────────
const PAL: Record<Occupation, number> = {
  sedentary: 1.53,
  moderate:  1.76,
  heavy:     2.25,
};

// ── Extra kcal from today's activity (per 70 kg ref; scaled by weight) ──
const ACTIVITY_KCAL_70KG: Record<TodayActivity, number> = {
  rest:        0,
  light_walk:  80,
  walk_30_60:  180,
  walk_60plus: 300,
  yoga:        150,
  gym_light:   250,
  gym_heavy:   420,
  run_30:      320,
  run_60plus:  580,
  heavy_labor: 500,
};

// ── ICMR-NIN 2020 RDA table (sedentary adult reference, 60 kg woman / 65 kg man) ──
// Keys match NUTRIENT_DAILY in food-db.ts
const RDA_BASE_MALE: Record<string, number> = {
  iron: 9,          // mg  (ICMR 2020, sedentary adult male)
  vitamin_b12: 2.2, // mcg
  vitamin_d: 15,    // mcg (600 IU)
  calcium: 600,     // mg  (ICMR 2020)
  magnesium: 340,   // mg
  zinc: 9,          // mg
  vitamin_c: 65,    // mg
  vitamin_a: 600,   // mcg RAE
  folate: 220,      // mcg DFE
  iodine: 150,      // mcg
  omega3: 1.6,      // g
  selenium: 40,     // mcg
  vitamin_b6: 1.6,  // mg
  potassium: 3500,  // mg
  phosphorus: 600,  // mg
  vitamin_b1: 1.2,  // mg
  vitamin_b2: 1.4,  // mg
  vitamin_b3: 16,   // mg NE
  vitamin_b5: 5,    // mg
  vitamin_b7: 30,   // mcg
  vitamin_k: 55,    // mcg
  copper: 0.9,      // mg
  manganese: 2.3,   // mg
  chromium: 33,     // mcg
  vitamin_e: 8,     // mg
};

const RDA_BASE_FEMALE: Record<string, number> = {
  ...RDA_BASE_MALE,
  iron: 21,         // mg  (ICMR 2020, premenopausal woman — higher due to menstrual loss)
  calcium: 600,
  folate: 220,
  vitamin_b1: 1.0,
  vitamin_b2: 1.1,
  vitamin_b3: 12,
  iodine: 150,
  selenium: 40,
};

// Age & physiological adjustments (ICMR-NIN 2020)
function adjustedRda(
  base: Record<string, number>,
  age: number,
  gender: string,
  medConditions: string[],
): Record<string, number> {
  const rda = { ...base };

  // Senior (≥60 yrs): more Ca, D, B12 (ICMR 2020 Table 3)
  if (age >= 60) {
    rda.calcium    = gender === "female" ? 800 : 700;
    rda.vitamin_d  = 20;   // mcg (800 IU) — ICMR elderly recommendation
    rda.vitamin_b12 = 2.4;
  }

  // Teen (13-17): growth demands (ICMR 2020)
  if (age >= 13 && age < 18) {
    rda.calcium = 800;
    rda.iron    = gender === "female" ? 27 : 11;
    rda.zinc    = gender === "female" ? 9 : 11;
  }

  // Medical adjustments
  if (medConditions.includes("pregnancy")) {
    rda.iron    = 35;   // mg  (ICMR 2020 pregnancy)
    rda.folate  = 500;  // mcg
    rda.calcium = 1200; // mg
    rda.vitamin_d = 15;
    rda.iodine  = 220;
  }
  if (medConditions.includes("kidney")) {
    rda.potassium  = 1500; // mg — restriction (KDIGO 2024)
    rda.phosphorus = 800;  // mg
  }

  return rda;
}

// ── Macro targets (ICMR-NIN 2020 + medical adjustments) ─────
function macroTargets(
  kcal: number,
  weight_kg: number,
  occupation: Occupation,
  medConditions: string[],
): { protein_g: number; carb_g: number; fat_g: number; fiber_g: number } {
  // Protein: 0.8 g/kg (sed), 1.0 (mod), 1.2 (heavy) — ICMR 2020
  const protFactor = occupation === "heavy" ? 1.2 : occupation === "moderate" ? 1.0 : 0.8;
  let protein_g = Math.round(weight_kg * protFactor);

  // CKD: protein restriction 0.6 g/kg (KDIGO 2024)
  if (medConditions.includes("kidney")) protein_g = Math.round(weight_kg * 0.6);

  // Fat: 20-30% energy (ICMR 2020); use 25%
  const fat_g = Math.round((kcal * 0.25) / 9);

  // Carbs: remainder
  const carb_g = Math.round((kcal - protein_g * 4 - fat_g * 9) / 4);

  // Fiber: 40g/day (ICMR 2020) — reduce to 25g if sick/CKD
  const fiber_g = medConditions.includes("kidney") ? 25 : 40;

  return { protein_g, carb_g, fat_g, fiber_g };
}

// ── Meal kcal distribution (standard Indian pattern) ────────
function mealBudget(kcal: number): NutritionTargets["meal_kcal"] {
  return {
    breakfast: Math.round(kcal * 0.25),
    lunch:     Math.round(kcal * 0.35),
    snacks:    Math.round(kcal * 0.15),
    dinner:    Math.round(kcal * 0.25),
  };
}

// ── Feeling adjustments ──────────────────────────────────────
function feelingAdjust(
  kcal: number,
  feeling: FeelingToday,
): { kcal: number; low_gi_priority: boolean; easy_digest: boolean } {
  if (feeling === "sick")      return { kcal: Math.round(kcal * 0.80), low_gi_priority: true,  easy_digest: true  };
  if (feeling === "very_tired") return { kcal: Math.round(kcal * 1.05), low_gi_priority: false, easy_digest: false };
  if (feeling === "tired")     return { kcal,                           low_gi_priority: false, easy_digest: false };
  if (feeling === "stressed")  return { kcal,                           low_gi_priority: true,  easy_digest: false };
  return { kcal, low_gi_priority: false, easy_digest: false };
}

// ── Main export ──────────────────────────────────────────────
export function calculateNutritionTargets(
  profile: UserProfile,
  occupation: Occupation,
  todayActivity: TodayActivity,
  feelingToday: FeelingToday,
  medConditions: string[],
): NutritionTargets {
  const age    = profile.age    ?? 30;
  const gender = profile.gender ?? "male";
  const weight = profile.weight_kg ?? 60;
  const height = profile.height_cm ?? 165;

  // BMR (Mifflin-St Jeor 1990)
  const bmrVal = bmr(weight, height, age, gender);

  // TDEE = BMR × PAL
  const pal = PAL[occupation];
  let tdee = bmrVal * pal;

  // Add today's activity (scaled from 70kg reference)
  const actKcal = ACTIVITY_KCAL_70KG[todayActivity] * (weight / 70);
  tdee += actKcal;

  // Feeling adjustment
  const { kcal, low_gi_priority, easy_digest } = feelingAdjust(tdee, feelingToday);
  const kcal_total = Math.round(kcal);

  // Macros
  const { protein_g, carb_g, fat_g, fiber_g } = macroTargets(
    kcal_total, weight, occupation, medConditions,
  );

  // RDA for this person
  const baseRda = gender === "female" ? RDA_BASE_FEMALE : RDA_BASE_MALE;
  const rda = adjustedRda(baseRda, age, gender, medConditions);

  // DASH mode: hypertension
  const dash_mode = medConditions.includes("bp_high");

  return {
    kcal_total,
    protein_g,
    carb_g,
    fat_g,
    fiber_g,
    meal_kcal: mealBudget(kcal_total),
    rda,
    low_gi_priority,
    easy_digest,
    dash_mode,
  };
}

// ── Serving size helpers (IFCT2017 portions) ─────────────────
export interface PortionedItem {
  name: string;
  state?: string;
  category: string;
  grams: number;
  serving_desc: string;
  kcal: number;
  nutrients_total: Record<string, number>;
}

// kcal per 100g for common recipe categories (IFCT2017 averages)
const KCAL_PER_100G: Record<string, number> = {
  Dish: 120, Protein: 180, Vegetable: 35, Fruit: 55,
  Dairy: 100, Grain: 340, Snack: 380, Beverage: 50,
  "Common Proteins": 180, "Common Fruits": 55,
  "Common Vegetables": 35, "Common Dishes": 120,
};

// Standard serving units for common categories
const SERVING_UNIT: Record<string, { unit: string; grams: number }> = {
  Grain:     { unit: "roti/piece", grams: 35  }, // 1 roti ≈ 35g (30g atta)
  Dish:      { unit: "katori",     grams: 150 },
  Vegetable: { unit: "katori",     grams: 150 },
  Dairy:     { unit: "katori",     grams: 150 },
  Protein:   { unit: "piece/100g", grams: 100 },
  Fruit:     { unit: "piece",      grams: 100 },
  Snack:     { unit: "handful",    grams: 30  },
  Beverage:  { unit: "glass",      grams: 240 },
};

import type { FoodItem } from "./food-db";

export function portionItem(
  recipe: FoodItem,
  kcal_budget: number,
  n_items_in_meal: number,
): PortionedItem {
  const cat = recipe.category;
  const kcal_per_100 = KCAL_PER_100G[cat] ?? 100;
  const unit_info = SERVING_UNIT[cat] ?? { unit: "katori", grams: 100 };

  // Target grams = kcal_budget / n_items / kcal_per_100 * 100
  // Clamped to reasonable range
  const raw_grams = Math.round((kcal_budget / n_items_in_meal / kcal_per_100) * 100);
  const grams = Math.max(50, Math.min(raw_grams, 300));

  // Express as serving units
  const pieces = Math.max(1, Math.round(grams / unit_info.grams));
  const serving_desc =
    cat === "Grain"
      ? `${pieces} roti (${grams}g)`
      : cat === "Dairy" && recipe.name.toLowerCase().includes("doodh")
      ? `${Math.round(grams / 240)} glass (${grams}ml)`
      : `${(grams / unit_info.grams).toFixed(1)} ${unit_info.unit} (${grams}g)`;

  // Scale nutrients
  const nutrients_total: Record<string, number> = {};
  for (const [k, v] of Object.entries(recipe.nutrients)) {
    nutrients_total[k] = parseFloat(((v as number) * grams / 100).toFixed(2));
  }

  const kcal = Math.round(kcal_per_100 * grams / 100);

  return {
    name: recipe.name,
    state: recipe.state,
    category: cat,
    grams,
    serving_desc,
    kcal,
    nutrients_total,
  };
}
