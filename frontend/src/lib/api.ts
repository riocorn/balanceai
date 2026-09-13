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

export async function analyzeText(payload: {
  voice_text: string;
  state?: string;
  is_vegetarian?: boolean;
}): Promise<AnalysisResult> {
  const { data } = await api.post("/checkin/text", payload);
  return data;
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
