/**
 * BalanceAI 5-Layer Nutrient Fusion Engine
 *
 * Fuses signals from all 5 data layers to produce a definitive per-nutrient
 * status (DEFICIENT / ADEQUATE / EXCESS / UNKNOWN) with confidence scores.
 *
 * Layer weights (reliability tier):
 *   Layer 2 — Blood test:    0.90  (lab values, clinical ground truth)
 *   Layer 3 — Symptoms:      0.60  (Bayesian cluster scoring, validated proxies)
 *   Layer 5 — Food log:      0.55  (actual 7-day intake vs ICMR-NIN RDA)
 *   Layer 1 — Health history: 0.40 (3-month event signals, broader/softer)
 *   Layer 4 — Visual signs:  0.25  (55-68% accuracy CNN, tiebreaker only)
 *
 * Score space: −1.0 (strong EXCESS) … 0 (ADEQUATE) … +1.0 (strong DEFICIENT)
 * Thresholds: score > 0.30 → DEFICIENT | score < −0.25 → EXCESS | else ADEQUATE
 */

import { NUTRIENT_DAILY, NUTRIENT_UNITS } from "./food-db";
import { BIOMARKER_MAP, type BloodValues } from "./blood-biomarker-map";
import { computeSymptomClusters, type SymptomLog, DISEASE_CLUSTERS } from "./symptom-disease-map";
import type { ImageAnalysisResult } from "./api";
import type { MealPhotoEntry } from "./db";
import type { UserProfile } from "./db";

// ── Types ─────────────────────────────────────────────────────────────────────

export type NutrientStatus = "deficient" | "adequate" | "excess" | "unknown";

export interface LayerEvidence {
  layer: "blood" | "symptoms" | "food_log" | "history" | "visual" | "ml";
  signal: number;   // -1 to +1
  weight: number;
  detail: string;   // human-readable reason
}

export interface MLPrediction {
  probability: number;
  deficient: boolean;
  threshold: number;
}

export interface NutrientResult {
  nutrient: string;
  label: string;
  unit: string;
  status: NutrientStatus;
  score: number;           // weighted fusion score, -1 to +1
  confidence: number;      // 0–1, how certain we are (considers data completeness)
  severity: "severe" | "moderate" | "mild" | "none";
  evidence: LayerEvidence[];
  rda_pct?: number;        // % of RDA from food log (if available)
}

export interface FusionInput {
  healthHistory: string[];
  bloodValues: BloodValues;
  gender: "male" | "female" | "other" | "";
  symptomLog: SymptomLog;
  imageResults: Record<string, ImageAnalysisResult>;
  mealPhotos: MealPhotoEntry[];
  profile?: UserProfile | null;
  mlPredictions?: Record<string, MLPrediction>;
}

export interface FusionResult {
  nutrients: NutrientResult[];
  deficient: NutrientResult[];        // status === "deficient", sorted by confidence × score
  excess: NutrientResult[];           // status === "excess"
  adequate: NutrientResult[];         // status === "adequate"
  unknown: NutrientResult[];          // no data at all
  topDeficiencies: string[];          // nutrient keys, top 8 by severity
  dataCompleteness: number;           // 0–1: fraction of layers that had data
  layerCoverage: Record<string, boolean>;  // which layers contributed anything
}

// ── Constants ──────────────────────────────────────────────────────────────────

const LAYER_WEIGHTS = {
  blood:   0.90,
  ml:      0.70,   // XGBoost NHANES-2017 (n=5856, mean AUC 0.873)
  symptoms: 0.60,
  food_log: 0.55,
  history:  0.40,
  visual:   0.25,
} as const;

// Score thresholds
const DEFICIENT_THRESHOLD = 0.30;
const EXCESS_THRESHOLD    = -0.25;

// Severity bands (for deficiency)
const SEVERE_THRESHOLD   = 0.70;
const MODERATE_THRESHOLD = 0.45;
const MILD_THRESHOLD     = 0.30;

// Nutrient display labels (extends food-db subset with all 25)
const NUTRIENT_LABELS: Record<string, string> = {
  iron:        "Iron",
  vitamin_b12: "Vitamin B12",
  vitamin_d:   "Vitamin D",
  calcium:     "Calcium",
  zinc:        "Zinc",
  omega3:      "Omega-3",
  folate:      "Folate",
  vitamin_a:   "Vitamin A",
  magnesium:   "Magnesium",
  vitamin_c:   "Vitamin C",
  iodine:      "Iodine",
  selenium:    "Selenium",
  vitamin_b6:  "Vitamin B6",
  potassium:   "Potassium",
  copper:      "Copper",
  vitamin_e:   "Vitamin E",
  vitamin_b1:  "Vitamin B1 (Thiamin)",
  vitamin_b2:  "Vitamin B2 (Riboflavin)",
  vitamin_b3:  "Vitamin B3 (Niacin)",
  vitamin_b5:  "Vitamin B5 (Pantothenic Acid)",
  vitamin_b7:  "Vitamin B7 (Biotin)",
  vitamin_k:   "Vitamin K",
  phosphorus:  "Phosphorus",
  manganese:   "Manganese",
  chromium:    "Chromium",
};

// History chip → nutrient signals (positional priority weights)
const HISTORY_TO_NUTRIENTS: Record<string, string[]> = {
  "Viral Fever":               ["zinc", "vitamin_c", "vitamin_a", "selenium", "vitamin_d"],
  "Cold / Cough (Recurrent)":  ["vitamin_c", "zinc", "vitamin_d", "vitamin_a", "selenium"],
  "Food Poisoning / Diarrhea": ["zinc", "potassium", "folate", "vitamin_b12", "magnesium"],
  "Typhoid":                   ["zinc", "vitamin_c", "iron", "vitamin_a"],
  "Dengue":                    ["vitamin_c", "folate", "zinc", "iron", "vitamin_k"],
  "UTI (Urine Infection)":     ["vitamin_c", "vitamin_a", "zinc"],
  "Jaundice":                  ["vitamin_k", "vitamin_e", "selenium", "zinc", "vitamin_b12"],
  "Malaria":                   ["iron", "folate", "zinc", "vitamin_b12", "vitamin_c"],
  "Weakness / Fatigue":        ["iron", "vitamin_b12", "vitamin_d", "magnesium", "folate"],
  "Hair Fall":                 ["iron", "zinc", "vitamin_b7", "folate", "vitamin_d"],
  "Joint / Bone Pain":         ["vitamin_d", "calcium", "omega3", "magnesium", "vitamin_k"],
  "Muscle Cramps":             ["magnesium", "potassium", "calcium", "vitamin_d"],
  "Bleeding Gums":             ["vitamin_c", "vitamin_k", "calcium", "zinc"],
  "Mouth Ulcers":              ["vitamin_b12", "folate", "iron", "zinc", "vitamin_c"],
  "Breathlessness":            ["iron", "vitamin_b12", "vitamin_d", "omega3"],
  "Skin Rashes / Dryness":     ["zinc", "vitamin_a", "omega3", "vitamin_e", "vitamin_c"],
  "Eye Problems":              ["vitamin_a", "vitamin_c", "vitamin_e", "zinc", "omega3"],
  "Sleep Problems":            ["magnesium", "vitamin_b6", "vitamin_d", "vitamin_b3"],
  "Mood Swings / Anxiety":     ["omega3", "magnesium", "vitamin_b12", "folate", "vitamin_d", "zinc"],
  "Brain Fog / Poor Focus":    ["omega3", "vitamin_b12", "folate", "vitamin_d", "zinc"],
};

// Position → signal weight within a chip's nutrient list
const HISTORY_POSITION_WEIGHTS = [0.7, 0.55, 0.40, 0.30, 0.22, 0.15];

// Nutrient → position-within-cluster weight (first = primary driver)
const CLUSTER_POSITION_WEIGHTS = [1.0, 0.70, 0.50, 0.35, 0.25];

// ── Layer-specific signal computations ────────────────────────────────────────

/** Layer 2: Blood test signals */
function computeBloodSignals(
  bloodValues: BloodValues,
  gender: string,
): Record<string, { signal: number; detail: string }> {
  const out: Record<string, { signal: number; detail: string }> = {};

  for (const [key, def] of Object.entries(BIOMARKER_MAP)) {
    const val = bloodValues[key];
    if (val === undefined || val === null) continue;

    let low = def.low;
    if (key === "hemoglobin" && gender === "male") low = 13;
    if (key === "hdl"        && gender === "female") low = 50;

    // LOW trigger → deficiency signal for nutrients_low
    if (low !== undefined && val < low) {
      // Severity: how far below threshold — 0% below = 0.35, 30%+ below = 1.0
      const severity = Math.min(1.0, 0.35 + ((low - val) / (0.30 * low)) * 0.65);
      for (let i = 0; i < def.nutrients_low.length; i++) {
        const n = def.nutrients_low[i];
        const posW = i === 0 ? 1.0 : i === 1 ? 0.75 : 0.5;
        const sig = severity * posW;
        if ((out[n]?.signal ?? 0) < sig) {
          out[n] = {
            signal: sig,
            detail: `${def.label} low (${val} ${def.unit}): ${def.note_low ?? "deficiency indicated"}`,
          };
        }
      }
    }

    // HIGH trigger → deficiency signal for nutrients_low (compensatory needs)
    if (def.high !== undefined && val > def.high) {
      const severity = Math.min(1.0, 0.35 + ((val - def.high) / (0.30 * def.high)) * 0.65);
      for (let i = 0; i < def.nutrients_low.length; i++) {
        const n = def.nutrients_low[i];
        const posW = i === 0 ? 1.0 : i === 1 ? 0.75 : 0.5;
        const sig = severity * posW;
        if ((out[n]?.signal ?? 0) < sig) {
          out[n] = {
            signal: sig,
            detail: `${def.label} high (${val} ${def.unit}): ${def.note_high ?? "compensatory need"}`,
          };
        }
      }
    }

    // EXCESS detection: iron excess (high ferritin), vitamin D toxicity (>100 ng/mL)
    if (key === "ferritin" && val > 300) {
      out["iron"] = { signal: -0.7, detail: `Ferritin very high (${val} ng/mL) — iron excess/overload` };
    }
    if (key === "vitamin_d" && val > 100) {
      out["vitamin_d"] = { signal: -0.6, detail: `Vitamin D very high (${val} ng/mL) — possible toxicity` };
    }
  }

  return out;
}

/** Layer 3: Symptom cluster signals — per-nutrient weighted score */
function computeSymptomSignals(symptomLog: SymptomLog): Record<string, { signal: number; detail: string }> {
  const out: Record<string, { signal: number; detail: string }> = {};
  const clusters = computeSymptomClusters(symptomLog);

  for (const result of clusters) {
    const { cluster, score } = result;
    // Cluster score is already 0–1.3 range; cap at 1.0 for signal
    const clusterSignal = Math.min(1.0, score);

    for (let i = 0; i < cluster.nutrients.length; i++) {
      const n = cluster.nutrients[i];
      const posW = CLUSTER_POSITION_WEIGHTS[i] ?? 0.15;
      const sig = clusterSignal * posW;

      if ((out[n]?.signal ?? 0) < sig) {
        out[n] = {
          signal: sig,
          detail: `${cluster.name} cluster (score ${score.toFixed(2)}): ${n} implicated`,
        };
      }
    }
  }

  return out;
}

/** Layer 5: Food photo log — intake vs RDA */
function computeFoodSignals(
  mealPhotos: MealPhotoEntry[],
  profile?: UserProfile | null,
): Record<string, { signal: number; rdaPct: number; detail: string }> {
  if (mealPhotos.length === 0) return {};

  // Group by date, sum nutrients per day
  const byDate: Record<string, Record<string, number>> = {};
  for (const entry of mealPhotos) {
    if (!entry.nutrients) continue;
    const day = entry.date;
    if (!byDate[day]) byDate[day] = {};
    for (const [n, v] of Object.entries(entry.nutrients)) {
      byDate[day][n] = (byDate[day][n] ?? 0) + v;
    }
  }

  const days = Object.keys(byDate);
  if (days.length < 2) return {}; // need at least 2 days for a signal

  // Daily averages
  const dailyAvg: Record<string, number> = {};
  for (const dayNutrients of Object.values(byDate)) {
    for (const [n, v] of Object.entries(dayNutrients)) {
      dailyAvg[n] = (dailyAvg[n] ?? 0) + v / days.length;
    }
  }

  // Profile-based RDA adjustment
  const age    = profile?.age ?? 30;
  const female = (profile?.gender ?? "") === "female";

  const out: Record<string, { signal: number; rdaPct: number; detail: string }> = {};

  for (const [n, rda] of Object.entries(NUTRIENT_DAILY)) {
    const actual = dailyAvg[n] ?? 0;
    if (actual === 0) continue;

    // Simple gender/age RDA adjustment for key nutrients
    let adjustedRda = rda;
    if (n === "iron")     adjustedRda = female ? (age < 50 ? 29 : 17) : 17;
    if (n === "calcium")  adjustedRda = age >= 60 ? 1200 : 1000;
    if (n === "vitamin_d") adjustedRda = age >= 60 ? 20 : 15;
    if (n === "folate")   adjustedRda = female && age < 50 ? 400 : 300;

    const rdaPct = (actual / adjustedRda) * 100;

    // Map RDA% to signal [-1, +1]
    // < 50% → strong deficient (+0.8 to +1.0)
    // 50-70% → moderate (+0.5 to +0.8)
    // 70-90% → mild (+0.1 to +0.5)
    // 90-110% → adequate (0)
    // 110-150% → mild excess (-0.1 to -0.3)
    // >150% → excess (-0.3 to -0.7)
    // >300% → strong excess (-0.7 to -1.0)
    let signal: number;
    if (rdaPct < 50)       signal = 0.80 + (1 - rdaPct / 50) * 0.20;
    else if (rdaPct < 70)  signal = 0.50 + ((70 - rdaPct) / 20) * 0.30;
    else if (rdaPct < 90)  signal = 0.10 + ((90 - rdaPct) / 20) * 0.40;
    else if (rdaPct < 110) signal = 0;
    else if (rdaPct < 150) signal = -0.10 - ((rdaPct - 110) / 40) * 0.20;
    else if (rdaPct < 300) signal = -0.30 - ((rdaPct - 150) / 150) * 0.40;
    else                   signal = -0.70 - Math.min(0.30, (rdaPct - 300) / 500);

    signal = Math.max(-1, Math.min(1, signal));

    out[n] = {
      signal,
      rdaPct,
      detail: `Food log: avg ${actual.toFixed(1)} ${NUTRIENT_UNITS[n] ?? ""}/day = ${rdaPct.toFixed(0)}% of RDA (${days.length} days)`,
    };
  }

  return out;
}

/** Layer 1: Health history chip signals */
function computeHistorySignals(healthHistory: string[]): Record<string, { signal: number; detail: string }> {
  if (healthHistory.length === 0) return {};

  const accumulated: Record<string, { total: number; chips: string[] }> = {};

  for (const chip of healthHistory) {
    const nutrients = HISTORY_TO_NUTRIENTS[chip] ?? [];
    for (let i = 0; i < nutrients.length; i++) {
      const n = nutrients[i];
      const sig = HISTORY_POSITION_WEIGHTS[i] ?? 0.10;
      if (!accumulated[n]) accumulated[n] = { total: 0, chips: [] };
      accumulated[n].total = Math.min(1.0, accumulated[n].total + sig);
      accumulated[n].chips.push(chip);
    }
  }

  const out: Record<string, { signal: number; detail: string }> = {};
  for (const [n, { total, chips }] of Object.entries(accumulated)) {
    out[n] = {
      signal: total,
      detail: `Health history: ${chips.join(", ")} → ${n} depleted`,
    };
  }
  return out;
}

/** Layer 4: Visual signs (nail/tongue/skin CNN) */
function computeVisualSignals(
  imageResults: Record<string, ImageAnalysisResult>,
): Record<string, { signal: number; detail: string }> {
  const out: Record<string, { signal: number; detail: string }> = {};

  for (const [modality, result] of Object.entries(imageResults)) {
    if (!result?.available || !result.nutrients?.length) continue;
    const confidence = result.confidence ?? 0;
    if (confidence < 0.40) continue;

    for (const n of result.nutrients) {
      if ((out[n]?.signal ?? 0) < confidence) {
        out[n] = {
          signal: confidence,
          detail: `${modality} visual sign: ${result.top_prediction?.class ?? "?"} (${(confidence * 100).toFixed(0)}% confidence)`,
        };
      }
    }
  }

  return out;
}

// ── Main fusion function ──────────────────────────────────────────────────────

export function runNutrientFusion(input: FusionInput): FusionResult {
  const {
    healthHistory,
    bloodValues,
    gender,
    symptomLog,
    imageResults,
    mealPhotos,
    profile,
    mlPredictions,
  } = input;

  // Compute per-layer signals
  const bloodSigs   = computeBloodSignals(bloodValues, gender);
  const symptomSigs = computeSymptomSignals(symptomLog);
  const foodSigs    = computeFoodSignals(mealPhotos, profile);
  const historySigs = computeHistorySignals(healthHistory);
  const visualSigs  = computeVisualSignals(imageResults);

  // Track which layers had ANY data
  const layerCoverage = {
    blood:    Object.keys(bloodSigs).length > 0,
    ml:       mlPredictions != null && Object.keys(mlPredictions).length > 0,
    symptoms: Object.keys(symptomSigs).length > 0,
    food_log: Object.keys(foodSigs).length > 0,
    history:  Object.keys(historySigs).length > 0,
    visual:   Object.keys(visualSigs).length > 0,
  };
  const activeLayers = Object.values(layerCoverage).filter(Boolean).length;
  const dataCompleteness = activeLayers / 6;

  // Fuse per nutrient
  const ALL_NUTRIENTS = Object.keys(NUTRIENT_DAILY);
  const nutrients: NutrientResult[] = [];

  for (const n of ALL_NUTRIENTS) {
    const evidence: LayerEvidence[] = [];
    let weightedSum = 0;
    let weightSum   = 0;
    let rdaPct: number | undefined;

    // Layer 2 — Blood (highest authority)
    if (bloodSigs[n]) {
      const { signal, detail } = bloodSigs[n];
      evidence.push({ layer: "blood", signal, weight: LAYER_WEIGHTS.blood, detail });
      weightedSum += signal * LAYER_WEIGHTS.blood;
      weightSum   += LAYER_WEIGHTS.blood;
    }

    // Layer ML — XGBoost (NHANES 2017-2018, n=5856, mean AUC 0.873)
    if (mlPredictions && mlPredictions[n]) {
      const ml = mlPredictions[n];
      // Convert probability to signal: prob maps [threshold..1] → [0..+1] (deficiency direction only)
      const mlSignal = ml.deficient
        ? Math.min(1.0, (ml.probability - ml.threshold) / (1 - ml.threshold) * 1.2)
        : -(ml.probability < ml.threshold * 0.5 ? 0.3 : 0.1);  // low prob → slight adequate signal
      const detail = `XGBoost: ${(ml.probability * 100).toFixed(0)}% deficiency probability (threshold ${(ml.threshold * 100).toFixed(0)}%)`;
      evidence.push({ layer: "ml", signal: mlSignal, weight: LAYER_WEIGHTS.ml, detail });
      weightedSum += mlSignal * LAYER_WEIGHTS.ml;
      weightSum   += LAYER_WEIGHTS.ml;
    }

    // Layer 3 — Symptoms
    if (symptomSigs[n]) {
      const { signal, detail } = symptomSigs[n];
      evidence.push({ layer: "symptoms", signal, weight: LAYER_WEIGHTS.symptoms, detail });
      weightedSum += signal * LAYER_WEIGHTS.symptoms;
      weightSum   += LAYER_WEIGHTS.symptoms;
    }

    // Layer 5 — Food log
    if (foodSigs[n]) {
      const foodEntry = foodSigs[n];
      const { signal, detail } = foodEntry;
      rdaPct = foodEntry.rdaPct;
      evidence.push({ layer: "food_log", signal, weight: LAYER_WEIGHTS.food_log, detail });
      weightedSum += signal * LAYER_WEIGHTS.food_log;
      weightSum   += LAYER_WEIGHTS.food_log;
    }

    // Layer 1 — History
    if (historySigs[n]) {
      const { signal, detail } = historySigs[n];
      evidence.push({ layer: "history", signal, weight: LAYER_WEIGHTS.history, detail });
      weightedSum += signal * LAYER_WEIGHTS.history;
      weightSum   += LAYER_WEIGHTS.history;
    }

    // Layer 4 — Visual
    if (visualSigs[n]) {
      const { signal, detail } = visualSigs[n];
      evidence.push({ layer: "visual", signal, weight: LAYER_WEIGHTS.visual, detail });
      weightedSum += signal * LAYER_WEIGHTS.visual;
      weightSum   += LAYER_WEIGHTS.visual;
    }

    if (evidence.length === 0) {
      nutrients.push({
        nutrient: n,
        label: NUTRIENT_LABELS[n] ?? n,
        unit: NUTRIENT_UNITS[n] ?? "",
        status: "unknown",
        score: 0,
        confidence: 0,
        severity: "none",
        evidence: [],
        rda_pct: rdaPct,
      });
      continue;
    }

    const score = weightedSum / weightSum;

    // Confidence: weighted coverage fraction × signal strength
    const maxWeight = Object.values(LAYER_WEIGHTS).reduce((a, b) => a + b, 0);
    const coverage  = weightSum / maxWeight;
    const confidence = Math.min(1.0, coverage * Math.abs(score) * 2.5);

    let status: NutrientStatus;
    if      (score > DEFICIENT_THRESHOLD) status = "deficient";
    else if (score < EXCESS_THRESHOLD)    status = "excess";
    else                                  status = "adequate";

    let severity: NutrientResult["severity"];
    if (status === "deficient") {
      if      (score >= SEVERE_THRESHOLD)   severity = "severe";
      else if (score >= MODERATE_THRESHOLD) severity = "moderate";
      else                                  severity = "mild";
    } else {
      severity = "none";
    }

    nutrients.push({
      nutrient: n,
      label: NUTRIENT_LABELS[n] ?? n,
      unit: NUTRIENT_UNITS[n] ?? "",
      status,
      score,
      confidence,
      severity,
      evidence,
      rda_pct: rdaPct,
    });
  }

  // Categorise and sort
  const deficient = nutrients
    .filter((r) => r.status === "deficient")
    .sort((a, b) => b.score * b.confidence - a.score * a.confidence);

  const excess = nutrients
    .filter((r) => r.status === "excess")
    .sort((a, b) => a.score - b.score);

  const adequate = nutrients.filter((r) => r.status === "adequate");
  const unknown  = nutrients.filter((r) => r.status === "unknown");

  const topDeficiencies = deficient.slice(0, 8).map((r) => r.nutrient);

  return { nutrients, deficient, excess, adequate, unknown, topDeficiencies, dataCompleteness, layerCoverage };
}

// ── Utility: convert FusionResult back to the flat deficiency list ─────────────
// For backward compatibility with generateDietPlan()
export function fusionToDeficiencyList(fusion: FusionResult): string[] {
  return fusion.topDeficiencies;
}

// ── Utility: which layer contributed most to a nutrient's status ──────────────
export function primaryEvidenceLayer(result: NutrientResult): string {
  if (result.evidence.length === 0) return "none";
  const top = [...result.evidence].sort((a, b) => Math.abs(b.signal * b.weight) - Math.abs(a.signal * a.weight))[0];
  return top.layer;
}
