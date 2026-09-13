import axios from "axios";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export interface DeficiencyResult {
  deficiency: string;
  probability: number;
  confidence: number;
  risk_level: "high" | "medium" | "low";
}

export interface BalanceScore {
  overall_score: number;
  high_risk_deficiencies: string[];
  medium_risk_deficiencies: string[];
  low_risk_deficiencies: string[];
}

export interface Recommendation {
  deficiency: string;
  foods: string[];
  traditional_remedy?: string;
}

export interface AnalysisResult {
  deficiency_predictions: DeficiencyResult[];
  balance_score: BalanceScore;
  recommendations: Recommendation[];
  diet_plan?: Record<string, string[]>;
  alerts?: string[];
}

// ── Rule-based local fallback (when backend is down) ──────────
const SYMPTOM_DEFICIENCY_MAP: Record<string, string[]> = {
  fatigue:              ["iron", "vitamin_b12", "vitamin_d", "magnesium"],
  hair_loss:            ["iron", "zinc", "vitamin_d", "vitamin_b7"],
  brittle_nails:        ["iron", "zinc", "calcium", "vitamin_b7"],
  bone_pain:            ["calcium", "vitamin_d", "magnesium"],
  muscle_cramps:        ["magnesium", "calcium", "potassium"],
  depression:           ["vitamin_d", "vitamin_b12", "magnesium", "omega3"],
  memory_issues:        ["vitamin_b12", "omega3", "magnesium", "vitamin_b6"],
  dry_skin:             ["vitamin_a", "vitamin_e", "omega3"],
  mouth_ulcers:         ["iron", "folate", "vitamin_b12", "vitamin_c"],
  bleeding_gums:        ["vitamin_c", "vitamin_k"],
  night_blindness:      ["vitamin_a"],
  numbness_tingling:    ["vitamin_b12", "vitamin_b1", "magnesium"],
  breathlessness:       ["iron", "vitamin_b12"],
  weight_gain:          ["vitamin_d", "chromium", "magnesium"],
  frequent_infections:  ["vitamin_c", "zinc", "vitamin_d", "selenium"],
  slow_wound_healing:   ["zinc", "vitamin_c", "vitamin_a"],
  insomnia:             ["magnesium", "vitamin_d", "vitamin_b6"],
  anxiety:              ["magnesium", "vitamin_b6", "omega3"],
  loss_of_appetite:     ["zinc", "vitamin_b1", "folate"],
  brain_fog:            ["vitamin_b12", "iron", "omega3", "vitamin_d"],
};

const TEXT_KEYWORD_MAP: Record<string, string[]> = {
  thakan: ["iron", "vitamin_b12", "vitamin_d"],
  baal:   ["iron", "zinc", "vitamin_d"],
  nakhun: ["iron", "zinc", "calcium"],
  haddi:  ["calcium", "vitamin_d"],
  neend:  ["magnesium", "vitamin_d"],
  yaadas: ["vitamin_b12", "omega3"],
  anemia: ["iron", "folate", "vitamin_b12"],
  weak:   ["iron", "vitamin_d", "magnesium"],
  tired:  ["iron", "vitamin_b12", "vitamin_d"],
  hair:   ["iron", "zinc", "vitamin_d"],
  nail:   ["iron", "zinc", "calcium"],
  bone:   ["calcium", "vitamin_d"],
  skin:   ["vitamin_a", "vitamin_e", "omega3"],
  mood:   ["vitamin_d", "vitamin_b12", "magnesium"],
  stress: ["magnesium", "vitamin_b6", "omega3"],
};

function localAnalyze(voiceText: string, symptoms: string[]): AnalysisResult {
  const counts: Record<string, number> = {};

  // Count from symptoms
  for (const sym of symptoms) {
    const defs = SYMPTOM_DEFICIENCY_MAP[sym] ?? [];
    defs.forEach((d, i) => { counts[d] = (counts[d] ?? 0) + (4 - i); });
  }

  // Count from text keywords
  const lowerText = voiceText.toLowerCase();
  for (const [kw, defs] of Object.entries(TEXT_KEYWORD_MAP)) {
    if (lowerText.includes(kw)) {
      defs.forEach((d, i) => { counts[d] = (counts[d] ?? 0) + (3 - i); });
    }
  }

  // Default if nothing detected
  if (Object.keys(counts).length === 0) {
    ["vitamin_d", "iron", "vitamin_b12", "magnesium", "zinc"].forEach((d, i) => {
      counts[d] = 5 - i;
    });
  }

  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const maxScore = sorted[0]?.[1] ?? 1;

  const predictions: DeficiencyResult[] = sorted.map(([def, score]) => {
    const prob = Math.min(0.95, score / maxScore * 0.85 + 0.1);
    const risk_level: "high" | "medium" | "low" =
      prob >= 0.65 ? "high" : prob >= 0.4 ? "medium" : "low";
    return { deficiency: def, probability: prob, confidence: prob * 0.9, risk_level };
  });

  const high = predictions.filter((p) => p.risk_level === "high").map((p) => p.deficiency);
  const med  = predictions.filter((p) => p.risk_level === "medium").map((p) => p.deficiency);
  const low  = predictions.filter((p) => p.risk_level === "low").map((p) => p.deficiency);
  const overall_score = Math.max(10, 100 - high.length * 18 - med.length * 8);

  const recommendations: Recommendation[] = high.slice(0, 5).map((def) => {
    const foodMap: Record<string, string[]> = {
      iron: ["Palak", "Rajma", "Chana", "Kala chana", "Bajra roti"],
      vitamin_b12: ["Dahi", "Doodh", "Paneer", "Anda (egg)", "Chicken"],
      vitamin_d: ["Dhoop (sunlight) 20 min", "Fatty fish", "Fortified milk", "Mushroom"],
      zinc: ["Kaju", "Kela", "Dahi", "Anda", "Til"],
      calcium: ["Doodh", "Dahi", "Paneer", "Ragi", "Til"],
      magnesium: ["Akhrot", "Badam", "Pumpkin seeds", "Palak", "Brown rice"],
      vitamin_c: ["Amla", "Nimbu", "Orange", "Guava", "Capsicum"],
      vitamin_a: ["Gajar", "Aam", "Papaya", "Pumpkin", "Ghee"],
      omega3: ["Flaxseed (alsi)", "Akhrot", "Fish", "Chia seeds"],
      folate: ["Hara dhaniya", "Paalak", "Rajma", "Moong dal"],
      vitamin_k: ["Hara patta sabzi", "Palak", "Methi", "Broccoli"],
      potassium: ["Kela", "Coconut water", "Potato", "Rajma"],
      selenium: ["Brazil nuts", "Anda", "Fish", "Brown rice"],
      vitamin_b7: ["Anda", "Badam", "Moong dal", "Banana"],
      vitamin_b6: ["Kela", "Anda", "Chicken", "Matar"],
    };
    return { deficiency: def, foods: foodMap[def] ?? ["Balanced diet lo"] };
  });

  return {
    deficiency_predictions: predictions,
    balance_score: { overall_score, high_risk_deficiencies: high, medium_risk_deficiencies: med, low_risk_deficiencies: low },
    recommendations,
    diet_plan: {},
    alerts: high.length > 3 ? ["Multiple deficiencies detected — doctor se milna recommended hai"] : [],
  };
}

export async function analyzeText(payload: {
  voice_text: string;
  state?: string;
  is_vegetarian?: boolean;
  _symptoms?: string[];
}): Promise<AnalysisResult> {
  try {
    const { data } = await api.post("/checkin/text", payload, { timeout: 5000 });
    return data;
  } catch {
    return localAnalyze(payload.voice_text, payload._symptoms ?? []);
  }
}

export async function analyzeImage(
  imageFile: File,
  modality: "nail" | "tongue" | "skin" | "eye"
): Promise<Record<string, number>> {
  const form = new FormData();
  form.append("image", imageFile);
  const { data } = await api.post(`/checkin/camera/${modality}`, form);
  return data;
}

export async function analyzeVoice(audioBlob: Blob, state?: string): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("audio", audioBlob, "recording.webm");
  if (state) form.append("state", state);
  const { data } = await api.post("/checkin/voice", form);
  return data;
}

export async function predictOnly(payload: {
  symptoms: string[];
  diet: Record<string, number | string>;
  visual_signs?: string[];
  state?: string;
  is_vegetarian?: boolean;
}): Promise<AnalysisResult> {
  const { data } = await api.post("/checkin/predict-only", payload);
  return data;
}

export const DEFICIENCY_LABELS: Record<string, string> = {
  vitamin_d: "Vitamin D",
  iron: "Iron",
  vitamin_b12: "Vitamin B12",
  zinc: "Zinc",
  calcium: "Calcium",
  magnesium: "Magnesium",
  vitamin_c: "Vitamin C",
  vitamin_a: "Vitamin A",
  folate: "Folate",
  iodine: "Iodine",
  omega3: "Omega-3",
  selenium: "Selenium",
  vitamin_b6: "Vitamin B6",
  potassium: "Potassium",
  copper: "Copper",
  vitamin_e: "Vitamin E",
  vitamin_b1: "Vitamin B1",
  vitamin_b2: "Vitamin B2",
  vitamin_b3: "Vitamin B3",
  vitamin_b5: "Vitamin B5",
  vitamin_b7: "Biotin (B7)",
  vitamin_k: "Vitamin K",
  phosphorus: "Phosphorus",
  manganese: "Manganese",
  chromium: "Chromium",
};

export const SYMPTOM_OPTIONS = [
  "fatigue", "hair_loss", "brittle_nails", "bone_pain", "muscle_cramps",
  "depression", "memory_issues", "dry_skin", "mouth_ulcers", "bleeding_gums",
  "night_blindness", "numbness_tingling", "breathlessness", "weight_gain",
  "frequent_infections", "slow_wound_healing", "insomnia", "anxiety",
  "loss_of_appetite", "brain_fog",
];

export const SYMPTOM_LABELS: Record<string, string> = {
  fatigue: "Thakaan / Fatigue",
  hair_loss: "Baal girna / Hair Loss",
  brittle_nails: "Nakhun toote / Brittle Nails",
  bone_pain: "Haddi dard / Bone Pain",
  muscle_cramps: "Maansapeshiyon mein dard / Muscle Cramps",
  depression: "Udaasi / Depression",
  memory_issues: "Yaadash kamzor / Memory Issues",
  dry_skin: "Sookhi twacha / Dry Skin",
  mouth_ulcers: "Munh ke chhale / Mouth Ulcers",
  bleeding_gums: "Masude se khoon / Bleeding Gums",
  night_blindness: "Raat ko nahi dikhta / Night Blindness",
  numbness_tingling: "Jhanjhanahat / Numbness",
  breathlessness: "Saansi failna / Breathlessness",
  weight_gain: "Wajan badhna / Weight Gain",
  frequent_infections: "Baar baar bimaar / Frequent Illness",
  slow_wound_healing: "Ghav dheere bharti / Slow Healing",
  insomnia: "Neend nahi / Insomnia",
  anxiety: "Ghabrahat / Anxiety",
  loss_of_appetite: "Bhoukh nahi / Loss of Appetite",
  brain_fog: "Dimag mein bhaari / Brain Fog",
};
