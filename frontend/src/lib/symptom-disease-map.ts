/**
 * Layer 3 — Last 7 Days Symptoms → Disease-Probability → Nutrition-Gap Inference
 *
 * Built after reading all 20 BalanceAI Disease↔Nutrition Deep Map PDF groups
 * (200 diseases, ICMR-NIN / WHO / NEJM / Lancet / GBD sourced nutrient-causation
 * percentages), then cross-checked against the exact "20 Disease Clusters" table,
 * Scoring Algorithm, Red Flags and UI Design drafted earlier for this same Layer
 * (symptom phrasing + nutrient lists below match that table 1:1; a handful of
 * symptoms it referenced — memory loss, restless legs, poor balance, poor sleep,
 * salt cravings, acne, irregular periods, loss of taste/smell, easy bruising,
 * blurred vision, dental sensitivity — were added to the taxonomy for fidelity).
 *
 * Two facts from the 200-disease corpus shaped the rest of the design:
 *   1. It is a NUTRITION-CAUSATION map, not a symptom map — it has no per-disease
 *      "presenting symptoms" column, so clinical symptomatology came from
 *      standard medical knowledge, cross-checked against nutrient-contribution %.
 *   2. The corpus has ZERO infectious diseases (no typhoid/dengue/malaria) —
 *      nutrition doesn't cause these, so they can't be nutrition-scored. They're
 *      handled as pattern matches on the 7-day fever/rash/joint-pain/chills data
 *      that route to "get tested", never as a diet-fixable deficiency.
 *
 * Scoring (7-day temporal + severity Bayesian-style weighting):
 *   freq score   : never=0, sometimes(1-2 days)=0.3, often(3-5 days)=0.7, daily(6-7 days)=1.0
 *   severity mult: mild=0.7, moderate=1.0, severe=1.3
 *   per-symptom  : freq * severityMult (0 if not logged)
 *   cluster_score: sum(per-symptom scores for symptoms in cluster) / cluster.symptomIds.length
 *   confidence   : score > 0.70 => high | > 0.50 => medium | > 0.30 => low | else not shown
 *
 * Red flags are a separate static yes/no checklist (not frequency-scored) — these
 * are absolute "see a doctor now" signs, not something to infer from chip combos.
 */

export type SymptomFreq = "never" | "sometimes" | "often" | "daily";
export type SymptomSeverity = "mild" | "moderate" | "severe";

export interface SymptomEntry {
  freq: SymptomFreq;
  severity: SymptomSeverity;
}

export type SymptomLog = Record<string, SymptomEntry>;

export const FREQ_OPTIONS: { value: SymptomFreq; label: string }[] = [
  { value: "never",     label: "Never" },
  { value: "sometimes", label: "Sometimes (1-2 days)" },
  { value: "often",     label: "Often (3-5 days)" },
  { value: "daily",     label: "Daily (6-7 days)" },
];

export const SEVERITY_OPTIONS: { value: SymptomSeverity; label: string }[] = [
  { value: "mild",     label: "Mild" },
  { value: "moderate", label: "Moderate" },
  { value: "severe",   label: "Severe" },
];

const FREQ_SCORE: Record<SymptomFreq, number> = {
  never: 0, sometimes: 0.3, often: 0.7, daily: 1.0,
};
const SEVERITY_MULT: Record<SymptomSeverity, number> = {
  mild: 0.7, moderate: 1.0, severe: 1.3,
};

export interface SymptomDef {
  id: string;
  label: string;
}
export interface SymptomCategory {
  id: string;
  label: string;
  symptoms: SymptomDef[];
}

export const SYMPTOM_CATEGORIES: SymptomCategory[] = [
  {
    id: "general", label: "General / Energy",
    symptoms: [
      { id: "fatigue",          label: "Fatigue / constant tiredness" },
      { id: "weakness",         label: "Body weakness" },
      { id: "weight_loss",      label: "Unintentional weight loss" },
      { id: "weight_gain",      label: "Unexplained weight gain" },
      { id: "poor_appetite",    label: "Poor appetite" },
      { id: "salt_cravings",    label: "Salt cravings" },
      { id: "irregular_periods",label: "Irregular periods (if applicable)" },
    ],
  },
  {
    id: "skin_hair", label: "Skin, Hair & Nails",
    symptoms: [
      { id: "hair_fall",      label: "Excess hair fall" },
      { id: "dry_skin",       label: "Dry / rough skin" },
      { id: "pale_skin",      label: "Pale skin / pale eyelids" },
      { id: "brittle_nails",  label: "Brittle or spoon-shaped nails" },
      { id: "slow_healing",   label: "Slow wound healing" },
      { id: "acne",           label: "Acne / adult breakouts" },
      { id: "easy_bruising",  label: "Easy bruising" },
    ],
  },
  {
    id: "mouth_eyes", label: "Mouth & Eyes",
    symptoms: [
      { id: "mouth_ulcers",     label: "Mouth ulcers / cracked lip corners" },
      { id: "bleeding_gums",    label: "Bleeding gums" },
      { id: "night_blindness",  label: "Night blindness / dry eyes" },
      { id: "sore_tongue",      label: "Sore / swollen tongue" },
      { id: "frequent_styes",   label: "Frequent styes / eye infections" },
      { id: "taste_smell_loss", label: "Loss of taste or smell" },
      { id: "blurred_vision",   label: "Blurred vision" },
      { id: "dental_sensitivity",label: "Tooth / dental sensitivity" },
    ],
  },
  {
    id: "digestive", label: "Digestive",
    symptoms: [
      { id: "constipation",   label: "Constipation" },
      { id: "diarrhoea",      label: "Diarrhoea / loose motions" },
      { id: "bloating",       label: "Bloating / excess gas" },
      { id: "abdominal_pain", label: "Abdominal pain" },
      { id: "nausea",         label: "Nausea / vomiting" },
    ],
  },
  {
    id: "musculoskeletal", label: "Muscles, Bones & Joints",
    symptoms: [
      { id: "joint_pain",      label: "Joint pain" },
      { id: "muscle_cramps",   label: "Muscle cramps" },
      { id: "bone_pain",       label: "Bone pain" },
      { id: "back_pain",       label: "Back pain" },
      { id: "muscle_weakness", label: "Muscle weakness" },
      { id: "restless_legs",   label: "Restless legs (especially at night)" },
    ],
  },
  {
    id: "neuro_mental", label: "Neurological & Mental",
    symptoms: [
      { id: "headache",       label: "Headache" },
      { id: "dizziness",      label: "Dizziness" },
      { id: "numbness",       label: "Numbness / tingling in hands-feet" },
      { id: "concentration",  label: "Difficulty concentrating / brain fog" },
      { id: "mood_swings",    label: "Mood swings / irritability / low mood" },
      { id: "memory_issues",  label: "Memory issues / forgetfulness" },
      { id: "poor_balance",   label: "Poor balance / unsteadiness" },
      { id: "poor_sleep",     label: "Poor sleep / insomnia" },
    ],
  },
  {
    id: "cardio_resp", label: "Heart & Breathing",
    symptoms: [
      { id: "palpitations",     label: "Palpitations (racing heartbeat)" },
      { id: "breathlessness",   label: "Breathlessness on exertion" },
      { id: "chest_discomfort", label: "Chest discomfort" },
      { id: "leg_swelling",     label: "Swelling in legs / feet" },
      { id: "cold_extremities", label: "Cold hands / feet" },
    ],
  },
  {
    id: "infection_fever", label: "Fever & Infection",
    symptoms: [
      { id: "fever",               label: "Fever" },
      { id: "chills_sweats",       label: "Chills with sweating episodes" },
      { id: "rash",                label: "Skin rash" },
      { id: "frequent_infections", label: "Frequent infections / slow recovery" },
      { id: "excess_thirst",       label: "Excessive thirst & urination" },
    ],
  },
];

export const ALL_SYMPTOM_IDS: string[] = SYMPTOM_CATEGORIES.flatMap((c) => c.symptoms.map((s) => s.id));

export interface DiseaseCluster {
  id: string;
  name: string;
  symptomIds: string[];
  nutrients: string[];
}

// The 20 Disease Clusters — symptom phrasing + nutrient lists match the
// original design table exactly (nutrient names mapped to this codebase's
// 25-nutrient keys, e.g. "B12" -> "vitamin_b12", "vit_d" -> "vitamin_d").
export const DISEASE_CLUSTERS: DiseaseCluster[] = [
  {
    id: "iron_deficiency_anaemia", name: "Iron Deficiency Anaemia",
    symptomIds: ["fatigue", "pale_skin", "palpitations", "breathlessness"],
    nutrients: ["iron", "vitamin_c", "folate"],
  },
  {
    id: "b12_folate_deficiency", name: "B12 / Folate Deficiency",
    symptomIds: ["numbness", "memory_issues", "sore_tongue", "mood_swings"],
    nutrients: ["vitamin_b12", "folate", "iron"],
  },
  {
    id: "vitamin_d_deficiency", name: "Vitamin D Deficiency",
    symptomIds: ["bone_pain", "muscle_weakness", "mood_swings", "frequent_infections"],
    nutrients: ["vitamin_d", "calcium", "magnesium"],
  },
  {
    id: "magnesium_deficiency", name: "Magnesium Deficiency",
    symptomIds: ["muscle_cramps", "poor_sleep", "mood_swings", "restless_legs"],
    nutrients: ["magnesium", "calcium", "potassium"],
  },
  {
    id: "zinc_deficiency", name: "Zinc Deficiency",
    symptomIds: ["taste_smell_loss", "slow_healing", "frequent_infections"],
    nutrients: ["zinc", "vitamin_a", "selenium"],
  },
  {
    id: "hypothyroid_signal", name: "Hypothyroid Signal",
    symptomIds: ["weight_gain", "cold_extremities", "constipation", "hair_fall"],
    nutrients: ["iodine", "selenium", "zinc"],
  },
  {
    id: "vitamin_a_deficiency", name: "Vitamin A Deficiency",
    symptomIds: ["night_blindness", "frequent_infections", "dry_skin"],
    nutrients: ["vitamin_a", "zinc"],
  },
  {
    id: "vitamin_c_deficiency", name: "Vitamin C Deficiency",
    symptomIds: ["bleeding_gums", "easy_bruising", "slow_healing"],
    nutrients: ["vitamin_c", "iron"],
  },
  {
    id: "omega3_depression", name: "Omega-3 / Depression",
    symptomIds: ["mood_swings", "dry_skin", "concentration"],
    nutrients: ["omega3", "vitamin_b12", "vitamin_d", "magnesium"],
  },
  {
    id: "pre_diabetes_signal", name: "Pre-Diabetes Signal",
    symptomIds: ["excess_thirst", "blurred_vision", "fatigue"],
    nutrients: ["chromium", "magnesium", "zinc", "fiber"],
  },
  {
    id: "calcium_bone", name: "Calcium / Bone",
    symptomIds: ["bone_pain", "muscle_cramps", "dental_sensitivity", "brittle_nails"],
    nutrients: ["calcium", "vitamin_d", "vitamin_k"],
  },
  {
    id: "b_vitamin_complex", name: "B-Vitamin Complex",
    symptomIds: ["mouth_ulcers", "rash", "numbness", "fatigue"],
    nutrients: ["vitamin_b1", "vitamin_b2", "vitamin_b3", "vitamin_b6"],
  },
  {
    id: "gut_malabsorption", name: "Gut / Malabsorption",
    symptomIds: ["bloating", "diarrhoea", "weight_loss", "fatigue"],
    nutrients: ["zinc", "vitamin_b12", "iron", "vitamin_d"],
  },
  {
    id: "chronic_inflammation", name: "Chronic Inflammation",
    symptomIds: ["joint_pain", "fatigue", "frequent_infections", "concentration"],
    nutrients: ["omega3", "vitamin_d", "vitamin_c", "selenium"],
  },
  {
    id: "protein_deficiency", name: "Protein Deficiency",
    symptomIds: ["hair_fall", "muscle_weakness", "leg_swelling"],
    nutrients: ["protein", "zinc", "vitamin_c"],
  },
  {
    id: "cardiovascular_risk", name: "Cardiovascular Risk",
    symptomIds: ["headache", "palpitations", "breathlessness", "cold_extremities"],
    nutrients: ["potassium", "magnesium", "omega3"],
  },
  {
    id: "adrenal_stress", name: "Adrenal / Stress",
    symptomIds: ["fatigue", "mood_swings", "poor_sleep", "salt_cravings", "frequent_infections"],
    nutrients: ["vitamin_c", "vitamin_b5", "magnesium", "zinc"],
  },
  {
    id: "neuropathy", name: "Neuropathy",
    symptomIds: ["numbness", "poor_balance", "memory_issues", "weakness"],
    nutrients: ["vitamin_b12", "vitamin_b1", "vitamin_b6", "omega3"],
  },
  {
    id: "female_hormonal", name: "Female Hormonal",
    symptomIds: ["irregular_periods", "weight_gain", "hair_fall", "acne"],
    nutrients: ["magnesium", "vitamin_d", "zinc", "iron"],
  },
  {
    id: "liver_vitk", name: "Liver / Vit K",
    symptomIds: ["easy_bruising", "bleeding_gums", "nausea", "poor_appetite"],
    nutrients: ["vitamin_k", "selenium", "zinc"],
  },
];

export interface ClusterResult {
  cluster: DiseaseCluster;
  score: number;
  confidence: "low" | "medium" | "high";
  matchedSymptoms: string[];
}

function symptomScore(entry: SymptomEntry | undefined): number {
  if (!entry) return 0;
  return FREQ_SCORE[entry.freq] * SEVERITY_MULT[entry.severity];
}

export function computeSymptomClusters(log: SymptomLog): ClusterResult[] {
  const results: ClusterResult[] = [];
  for (const cluster of DISEASE_CLUSTERS) {
    let total = 0;
    const matched: string[] = [];
    for (const sid of cluster.symptomIds) {
      const s = symptomScore(log[sid]);
      total += s;
      if (s > 0) matched.push(sid);
    }
    const score = total / cluster.symptomIds.length;
    if (score <= 0.30) continue;
    const confidence: ClusterResult["confidence"] =
      score > 0.70 ? "high" : score > 0.50 ? "medium" : "low";
    results.push({ cluster, score, confidence, matchedSymptoms: matched });
  }
  return results.sort((a, b) => b.score - a.score);
}

// Nutrients to feed into generateDietPlan's `deficiencies` array — top clusters only.
export function getSymptomDeficiencies(log: SymptomLog, topN = 4): string[] {
  const top = computeSymptomClusters(log).slice(0, topN);
  const defs = new Set<string>();
  for (const r of top) for (const n of r.cluster.nutrients) defs.add(n);
  return [...defs];
}

// ── Static Red Flags checklist (doctor NOW, not nutrition) ─────────────────
// These are absolute emergency/urgent-referral signs — a plain yes/no checklist,
// never inferred from frequency chips.
export interface RedFlagSymptom {
  id: string;
  label: string;
}
export const RED_FLAG_SYMPTOMS: RedFlagSymptom[] = [
  { id: "chest_pain",        label: "Chest pain" },
  { id: "sudden_severe_headache", label: "Sudden, severe headache (worst of your life)" },
  { id: "blood_in_stool_urine",   label: "Blood in stool or urine" },
  { id: "yellowing_skin",    label: "Yellowing of skin or eyes (jaundice)" },
  { id: "one_sided_numbness",label: "Sudden one-sided numbness or weakness" },
  { id: "high_fever_3days",  label: "High fever for more than 3 days" },
  { id: "unintentional_weight_loss", label: "Significant unintentional weight loss" },
];

export function checkStaticRedFlags(checked: Record<string, boolean>): string[] {
  return RED_FLAG_SYMPTOMS
    .filter((f) => checked[f.id])
    .map((f) => `${f.label} — see a doctor now, this cannot be fixed by nutrition alone.`);
}

// ── Indian infectious-disease pattern matches (from the 7-day symptom log) ──
// The 200-disease nutrition corpus has NO infectious diseases (they aren't
// nutrition-caused) — these patterns route to "get tested", not to a diet fix.
const isFreq = (log: SymptomLog, id: string, mins: SymptomFreq[]) =>
  !!log[id] && mins.includes(log[id].freq);
const logged = (log: SymptomLog, id: string) => !!log[id] && log[id].freq !== "never";

export interface InfectionPatternRule {
  id: string;
  message: string;
  check: (log: SymptomLog) => boolean;
}

export const INFECTION_PATTERN_RULES: InfectionPatternRule[] = [
  {
    id: "dengue_pattern",
    message: "Fever with joint pain, rash and bleeding gums — this pattern is common in dengue in India. Get a platelet count checked urgently; nutrition cannot treat this.",
    check: (log) => ["fever", "joint_pain", "rash", "bleeding_gums"].filter((id) => logged(log, id)).length >= 3,
  },
  {
    id: "malaria_pattern",
    message: "Cyclical fever with chills and sweating episodes — this pattern is common in malaria in India. Get a blood smear/RDT test done promptly.",
    check: (log) => isFreq(log, "fever", ["often", "daily"]) && logged(log, "chills_sweats"),
  },
  {
    id: "typhoid_pattern",
    message: "Prolonged fever most of the week with abdominal pain and poor appetite — this pattern is common in typhoid in India. Get a blood culture/Widal test done.",
    check: (log) => isFreq(log, "fever", ["often", "daily"]) && logged(log, "abdominal_pain") && isFreq(log, "poor_appetite", ["often", "daily"]),
  },
  {
    id: "chronic_fever",
    message: "Daily fever for most of the week — do not self-manage with diet alone. See a doctor for a fever work-up.",
    check: (log) => isFreq(log, "fever", ["daily"]),
  },
];

export function checkInfectionPatterns(log: SymptomLog): string[] {
  return INFECTION_PATTERN_RULES.filter((r) => r.check(log)).map((r) => r.message);
}
