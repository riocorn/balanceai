/**
 * Layer 2 — Blood Test (Full Body Checkup ₹500 package)
 * Tests: CBC, Blood Sugar, Lipid Profile, LFT, KFT, Thyroid, Urine Routine
 * Reference: ICMR-NIN 2020, WHO, AIIMS clinical guidelines
 */

export interface BiomarkerDef {
  label: string;
  unit: string;
  low?: number;
  high?: number;
  nutrients_low: string[];
  nutrients_high: string[];
  note_low?: string;
  note_high?: string;
}

export const BIOMARKER_MAP: Record<string, BiomarkerDef> = {

  // ── CBC ───────────────────────────────────────────────────────────────────

  hemoglobin: {
    label: "Hemoglobin",
    unit: "g/dL",
    low: 12,                        // <12 women, <13 men
    nutrients_low: ["iron", "vitamin_b12", "folate", "copper", "vitamin_b6"],
    nutrients_high: [],
    note_low: "Anaemia — boost iron, B12, folate",
  },
  mcv: {
    label: "MCV",
    unit: "fL",
    low: 80,                        // <80 = microcytic → iron deficiency
    high: 100,                      // >100 = macrocytic → B12 or folate
    nutrients_low: ["iron", "copper", "vitamin_b6"],
    nutrients_high: ["vitamin_b12", "folate"],
    note_low: "Microcytic anemia — iron deficiency likely",
    note_high: "Macrocytic anemia — B12 or folate deficiency",
  },
  mch: {
    label: "MCH",
    unit: "pg",
    low: 27,                        // <27 = iron deficiency
    high: 34,                       // >34 = B12/folate deficiency
    nutrients_low: ["iron"],
    nutrients_high: ["vitamin_b12", "folate"],
    note_low: "Hypochromic — iron deficiency",
    note_high: "Hyperchromic — B12 or folate deficiency",
  },
  mchc: {
    label: "MCHC",
    unit: "g/dL",
    low: 32,
    nutrients_low: ["iron"],
    nutrients_high: [],
    note_low: "Iron deficiency pattern",
  },
  wbc: {
    label: "WBC Count",
    unit: "cells/µL",
    low: 4000,
    nutrients_low: ["zinc", "selenium", "vitamin_c", "vitamin_d", "vitamin_b12", "folate"],
    nutrients_high: [],
    note_low: "Low immunity — boost zinc, selenium, vitamin C, D",
  },
  platelets: {
    label: "Platelet Count",
    unit: "lakh/µL",
    low: 1.5,
    nutrients_low: ["vitamin_c", "vitamin_k", "folate", "vitamin_b12"],
    nutrients_high: [],
    note_low: "Low platelets — boost vitamin C, K, folate",
  },

  // ── Blood Sugar ───────────────────────────────────────────────────────────

  fasting_glucose: {
    label: "Fasting Blood Glucose",
    unit: "mg/dL",
    high: 100,
    nutrients_low: ["magnesium", "chromium", "zinc", "vitamin_b1", "vitamin_b3"],
    nutrients_high: [],
    note_high: "Elevated fasting glucose — boost magnesium, chromium, zinc",
  },
  hba1c: {
    label: "HbA1c",
    unit: "%",
    high: 5.7,
    nutrients_low: ["magnesium", "chromium", "zinc", "vitamin_d", "vitamin_b1", "vitamin_b3", "vitamin_b6"],
    nutrients_high: [],
    note_high: "Pre-diabetes / diabetes — boost magnesium, chromium, B vitamins",
  },

  // ── Lipid Profile ─────────────────────────────────────────────────────────

  total_cholesterol: {
    label: "Total Cholesterol",
    unit: "mg/dL",
    high: 200,
    nutrients_low: ["omega3", "vitamin_b3", "fiber", "vitamin_e"],
    nutrients_high: [],
    note_high: "High cholesterol — boost omega-3, niacin (B3), fiber",
  },
  hdl: {
    label: "HDL Cholesterol",
    unit: "mg/dL",
    low: 40,                        // <40 men, <50 women
    nutrients_low: ["omega3", "vitamin_b3", "vitamin_e"],
    nutrients_high: [],
    note_low: "Low HDL — boost omega-3, niacin, vitamin E",
  },
  ldl: {
    label: "LDL Cholesterol",
    unit: "mg/dL",
    high: 130,
    nutrients_low: ["omega3", "fiber", "vitamin_e", "vitamin_b3"],
    nutrients_high: [],
    note_high: "High LDL — boost omega-3, fiber, reduce saturated fat",
  },
  triglycerides: {
    label: "Triglycerides",
    unit: "mg/dL",
    high: 150,
    nutrients_low: ["omega3", "vitamin_b3", "fiber"],
    nutrients_high: [],
    note_high: "High TG — boost omega-3, reduce refined carbs/sugar",
  },
  vldl: {
    label: "VLDL Cholesterol",
    unit: "mg/dL",
    high: 30,
    nutrients_low: ["omega3", "vitamin_b3"],
    nutrients_high: [],
    note_high: "High VLDL — boost omega-3, niacin",
  },

  // ── Liver Function (LFT) ──────────────────────────────────────────────────

  sgpt: {
    label: "SGPT / ALT",
    unit: "U/L",
    high: 40,
    nutrients_low: ["vitamin_e", "selenium", "vitamin_c", "vitamin_b6", "magnesium"],
    nutrients_high: [],
    note_high: "Liver stress — affects vitamin A, D, E, K storage; boost antioxidants",
  },
  sgot: {
    label: "SGOT / AST",
    unit: "U/L",
    high: 40,
    nutrients_low: ["vitamin_b6", "vitamin_e", "selenium", "magnesium"],
    nutrients_high: [],
    note_high: "Liver stress — B6 is cofactor for AST; boost B6, antioxidants",
  },
  alp: {
    label: "ALP (Alkaline Phosphatase)",
    unit: "U/L",
    high: 120,
    nutrients_low: ["zinc", "vitamin_d", "magnesium"],
    nutrients_high: [],
    note_high: "ALP elevated — zinc-dependent enzyme; suggests zinc or vitamin D deficiency",
  },
  bilirubin_total: {
    label: "Total Bilirubin",
    unit: "mg/dL",
    high: 1.2,
    nutrients_low: ["vitamin_e", "vitamin_c", "selenium"],
    nutrients_high: [],
    note_high: "Elevated bilirubin — liver/bile stress; boost antioxidants",
  },
  albumin: {
    label: "Serum Albumin",
    unit: "g/dL",
    low: 3.5,
    nutrients_low: ["protein", "zinc", "vitamin_c"],
    nutrients_high: [],
    note_low: "Low albumin — poor protein/zinc status",
  },
  total_protein: {
    label: "Total Protein",
    unit: "g/dL",
    low: 6.0,
    nutrients_low: ["protein", "zinc", "vitamin_b6"],
    nutrients_high: [],
    note_low: "Low total protein — boost protein, zinc",
  },

  // ── Kidney Function (KFT) ─────────────────────────────────────────────────

  creatinine: {
    label: "Serum Creatinine",
    unit: "mg/dL",
    high: 1.2,                      // >1.2F / >1.4M = kidney concern
    nutrients_low: ["vitamin_d", "calcium", "phosphorus"],
    nutrients_high: [],
    note_high: "Kidney stress — affects Vitamin D activation; monitor calcium, phosphorus",
  },
  urea: {
    label: "Blood Urea",
    unit: "mg/dL",
    high: 40,
    nutrients_low: ["vitamin_d", "calcium"],
    nutrients_high: [],
    note_high: "Elevated urea — kidney filtering stress; monitor electrolytes",
  },
  uric_acid: {
    label: "Uric Acid",
    unit: "mg/dL",
    high: 7.0,                      // >7 men, >6 women
    nutrients_low: ["vitamin_c", "omega3"],
    nutrients_high: [],
    note_high: "High uric acid — boost vitamin C, reduce purines",
  },

  // ── Thyroid ───────────────────────────────────────────────────────────────

  tsh: {
    label: "TSH (Thyroid)",
    unit: "mIU/L",
    low: 0.5,                       // <0.5 = hyperthyroid
    high: 4.5,                      // >4.5 = hypothyroid
    nutrients_low: ["iodine", "selenium", "zinc", "iron", "vitamin_d"],
    nutrients_high: [],
    note_low: "Hyperthyroid — excess iodine possible",
    note_high: "Hypothyroid pattern — boost iodine, selenium, zinc",
  },
};

// ── BalanceAI Panel — full body checkup ₹500 package ─────────────────────────
export const BALANCEAI_PANEL_TESTS = [
  // CBC
  { test: "CBC — Hemoglobin",          why: "Iron, B12, anaemia status",          biomarker: "hemoglobin",       category: "CBC" },
  { test: "CBC — MCV",                 why: "Iron vs B12/Folate anemia type",     biomarker: "mcv",              category: "CBC" },
  { test: "CBC — MCH",                 why: "Iron deficiency confirmation",        biomarker: "mch",              category: "CBC" },
  { test: "CBC — MCHC",               why: "Iron deficiency pattern",             biomarker: "mchc",             category: "CBC" },
  { test: "CBC — WBC Count",           why: "Immunity: zinc, selenium, vitamin C", biomarker: "wbc",             category: "CBC" },
  { test: "CBC — Platelet Count",      why: "Vitamin C, K, folate status",        biomarker: "platelets",        category: "CBC" },
  // Blood Sugar
  { test: "Fasting Blood Glucose",     why: "Chromium, magnesium, zinc signal",   biomarker: "fasting_glucose",  category: "Blood Sugar" },
  { test: "HbA1c",                     why: "3-month glucose — B vitamins, Mg",   biomarker: "hba1c",            category: "Blood Sugar" },
  // Lipid Profile
  { test: "Total Cholesterol",         why: "Omega-3, niacin (B3) status",        biomarker: "total_cholesterol",category: "Lipid Profile" },
  { test: "HDL Cholesterol",           why: "Omega-3, vitamin E signal",          biomarker: "hdl",              category: "Lipid Profile" },
  { test: "LDL Cholesterol",           why: "Omega-3, fiber needed",              biomarker: "ldl",              category: "Lipid Profile" },
  { test: "Triglycerides",             why: "Omega-3, niacin, refined carbs",     biomarker: "triglycerides",    category: "Lipid Profile" },
  { test: "VLDL Cholesterol",          why: "Omega-3, niacin status",             biomarker: "vldl",             category: "Lipid Profile" },
  // LFT
  { test: "SGPT / ALT",               why: "Liver — vitamin D/E/K metabolism",   biomarker: "sgpt",             category: "LFT" },
  { test: "SGOT / AST",               why: "B6, selenium, liver stress",          biomarker: "sgot",             category: "LFT" },
  { test: "ALP",                       why: "Zinc, vitamin D — bone/liver",       biomarker: "alp",              category: "LFT" },
  { test: "Total Bilirubin",           why: "Vitamin E, C antioxidant need",      biomarker: "bilirubin_total",  category: "LFT" },
  { test: "Serum Albumin",             why: "Protein, zinc nutrition status",     biomarker: "albumin",          category: "LFT" },
  { test: "Total Protein",             why: "Overall protein/zinc status",        biomarker: "total_protein",    category: "LFT" },
  // KFT
  { test: "Serum Creatinine",          why: "Vitamin D activation, phosphorus",   biomarker: "creatinine",       category: "KFT" },
  { test: "Blood Urea",                why: "Kidney stress — vitamin D, calcium", biomarker: "urea",             category: "KFT" },
  { test: "Uric Acid",                 why: "Vitamin C, omega-3 need",            biomarker: "uric_acid",        category: "KFT" },
  // Thyroid
  { test: "TSH (Thyroid)",             why: "Iodine, selenium, zinc status",      biomarker: "tsh",              category: "Thyroid" },
];

export interface BloodValues {
  [biomarker: string]: number | undefined;
}

export function parseBiomarkerDeficiencies(
  values: BloodValues,
  gender: "male" | "female" | "other" | "" = "",
): string[] {
  const defs = new Set<string>();

  for (const [key, def] of Object.entries(BIOMARKER_MAP)) {
    const val = values[key];
    if (val === undefined || val === null) continue;

    let low  = def.low;
    let high = def.high;

    // Gender-adjusted thresholds
    if (key === "hemoglobin" && gender === "male") low  = 13;
    if (key === "hdl"        && gender === "female") low = 50;
    if (key === "creatinine" && gender === "male")  high = 1.4;
    if (key === "uric_acid"  && gender === "female") high = 6.0;

    if (low  !== undefined && val < low)  def.nutrients_low.forEach(n => defs.add(n));
    if (high !== undefined && val > high) {
      // For markers where high = deficiency signal, nutrients_low = deficient nutrients
      def.nutrients_low.forEach(n => defs.add(n));
      // For MCV/MCH high → macrocytic = B12/folate deficiency
      def.nutrients_high.forEach(n => defs.add(n));
    }
  }

  return Array.from(defs);
}

export function getBiomarkerAlerts(
  values: BloodValues,
  gender: "male" | "female" | "other" | "" = "",
): { key: string; label: string; value: number; unit: string; status: "low" | "high" | "ok"; note: string }[] {
  const alerts = [];

  for (const [key, def] of Object.entries(BIOMARKER_MAP)) {
    const val = values[key];
    if (val === undefined || val === null) continue;

    let low  = def.low;
    let high = def.high;
    if (key === "hemoglobin" && gender === "male")  low  = 13;
    if (key === "hdl"        && gender === "female") low  = 50;
    if (key === "creatinine" && gender === "male")  high = 1.4;
    if (key === "uric_acid"  && gender === "female") high = 6.0;

    if (low !== undefined && val < low) {
      alerts.push({ key, label: def.label, value: val, unit: def.unit, status: "low" as const, note: def.note_low ?? "" });
    } else if (high !== undefined && val > high) {
      alerts.push({ key, label: def.label, value: val, unit: def.unit, status: "high" as const, note: def.note_high ?? "" });
    } else {
      alerts.push({ key, label: def.label, value: val, unit: def.unit, status: "ok" as const, note: "" });
    }
  }

  return alerts;
}
