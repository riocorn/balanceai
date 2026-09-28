import { api } from "@/lib/api";

export interface MatchResult {
  ai_mode: "local_llm" | "embedding_fallback" | "keyword_fallback";
  disease_id: string | null;
  confidence: number;
  explanation: string;
  possible_emergency?: boolean;
  hard_emergency_flag?: boolean;
}

export interface MedicineCard {
  name: string;
  type: string;
  mechanism: string;
  effectiveness_pct: number | null;
}

export interface CurativeOption {
  name: string;
  note: string;
}

export interface MedicinePayload {
  found: boolean;
  id: string;
  name: string;
  category: string;
  doctor_approval_required: boolean;
  emergency_override_rule: string | null;
  curability_note: string | null;
  exhaustive_medicine_survey_note: string | null;
  curative_option: CurativeOption | null;
  medicines: MedicineCard[];
}

export async function matchSymptoms(text: string): Promise<MatchResult> {
  const { data } = await api.post("/pharmacy/match", { text });
  return data;
}

export async function getMedicineDetail(diseaseId: string): Promise<MedicinePayload> {
  const { data } = await api.get(`/pharmacy/medicine/${diseaseId}`);
  return data;
}

export async function getWhatsappLink(payload: {
  disease_id: string;
  disease_name: string;
  medicine_names: string[];
  patient_text?: string;
}): Promise<string> {
  const { data } = await api.post("/pharmacy/whatsapp-link", payload);
  return data.link;
}
