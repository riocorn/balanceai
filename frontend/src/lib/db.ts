import Dexie, { type Table } from "dexie";

export interface AnalysisEntry {
  id?: number;
  timestamp: number;
  date: Date;
  score: number;
  score_label: "Good" | "Needs Attention" | "Action Required";

  predictions: Array<{
    deficiency: string;
    probability: number;
    confidence: number;
    risk_level: "high" | "medium" | "low";
  }>;
  high_risk: string[];
  medium_risk: string[];

  diet_plan: Record<string, string[]>;
  recommendations: Array<{
    deficiency: string;
    foods: string[];
    traditional_remedy?: string;
  }>;
  alerts: string[];

  symptoms_text: string;
  selected_symptoms: string[];
  state: string;
  is_vegetarian: boolean;
  image_results?: Record<string, unknown>;
  kitchen_items: string[];
  medical_conditions: string[];
  // Layer 1 (3-month health history chips) and Layer 2 (blood test values) —
  // saved with each analysis so they show up in the 3-month medical history view.
  health_history?: string[];
  blood_values?: Record<string, number | undefined>;
}

export interface MealPhotoEntry {
  id?: number;
  date: string;    // YYYY-MM-DD
  meal: "Breakfast" | "Lunch" | "Snacks" | "Dinner";
  timestamp: number;
  image: Blob;
  food_name?: string;
  confidence?: number;
  assumed_portion_g?: number;
  standard_portion_g?: number;
  portion_personalized?: boolean;
  kcal?: number;
  nutrients?: Record<string, number>;
  note?: string;
}

export interface PharmacyOrderItem {
  disease_id: string;
  disease_name: string;
  name: string;
  effectiveness_pct: number | null;
}

export interface PharmacyOrder {
  id?: number;
  order_ref: string;
  timestamp: number;
  items: PharmacyOrderItem[];
  address: { name: string; phone: string; pincode: string; line: string };
  payment_method: "cod" | "upi" | "card";
  doctor_verified: boolean;
  status: "placed";
}

export interface UserProfile {
  id?: number;
  name: string;
  streak: number;
  last_checkin_date: string; // YYYY-MM-DD
  total_analyses: number;
  age?: number;
  gender?: "male" | "female" | "other";
  weight_kg?: number;
  height_cm?: number;
  occupation?: "sedentary" | "moderate" | "heavy";
  goals?: string[];
  unlocked_achievements?: string[];
}

class BalanceAIDatabase extends Dexie {
  analyses!: Table<AnalysisEntry>;
  profile!: Table<UserProfile>;
  mealPhotos!: Table<MealPhotoEntry>;
  pharmacyOrders!: Table<PharmacyOrder>;

  constructor() {
    super("balanceai_v1");
    this.version(1).stores({
      analyses: "++id, timestamp, score",
      profile: "++id",
    });
    this.version(2).stores({
      analyses: "++id, timestamp, score",
      profile: "++id",
      mealPhotos: "++id, date, meal, timestamp",
    });
    this.version(3).stores({
      analyses: "++id, timestamp, score",
      profile: "++id",
      mealPhotos: "++id, date, meal, timestamp",
      pharmacyOrders: "++id, order_ref, timestamp",
    });
  }
}

export const db = new BalanceAIDatabase();

// ── retention windows (per the 6-layer architecture: Layer 1 medical history
// is a 3-month rolling window, Layer 5 food photo log is a 7-day rolling window) ──
const MEDICAL_HISTORY_DAYS = 90;
const FOOD_HISTORY_DAYS = 7;
const DAY_MS = 86_400_000;

async function _pruneOldAnalyses(): Promise<void> {
  const cutoff = Date.now() - MEDICAL_HISTORY_DAYS * DAY_MS;
  await db.analyses.where("timestamp").below(cutoff).delete();
}

async function _pruneOldMealPhotos(): Promise<void> {
  const cutoff = _dateStr(new Date(Date.now() - FOOD_HISTORY_DAYS * DAY_MS));
  await db.mealPhotos.where("date").below(cutoff).delete();
}

// ── helpers ──────────────────────────────────────────────

export async function saveAnalysis(
  entry: Omit<AnalysisEntry, "id">
): Promise<number> {
  const id = await db.analyses.add(entry);
  await _upsertStreak();
  await _pruneOldAnalyses();
  return id as number;
}

export async function getAllAnalyses(): Promise<AnalysisEntry[]> {
  await _pruneOldAnalyses();
  return db.analyses.orderBy("timestamp").reverse().toArray();
}

export async function getRecentAnalyses(n = 5): Promise<AnalysisEntry[]> {
  await _pruneOldAnalyses();
  return db.analyses.orderBy("timestamp").reverse().limit(n).toArray();
}

export async function deleteAnalysis(id: number): Promise<void> {
  await db.analyses.delete(id);
}

// ── meal photo log (Layer 5 — one photo per meal slot per day) ────────────

export async function saveMealPhoto(entry: Omit<MealPhotoEntry, "id">): Promise<number> {
  // One photo per (date, meal) — replace if the user retakes it today.
  const existing = await db.mealPhotos.where({ date: entry.date, meal: entry.meal }).first();
  let id: number;
  if (existing?.id) {
    await db.mealPhotos.update(existing.id, entry);
    id = existing.id;
  } else {
    id = (await db.mealPhotos.add(entry)) as number;
  }
  await _pruneOldMealPhotos();
  return id;
}

export async function getMealPhotosForDate(date: string): Promise<MealPhotoEntry[]> {
  await _pruneOldMealPhotos();
  return db.mealPhotos.where("date").equals(date).toArray();
}

// `days` here only limits how many distinct dates to RETURN (for paging the UI) —
// it can never exceed FOOD_HISTORY_DAYS, since anything older is actually deleted.
export async function getMealPhotoHistory(days = FOOD_HISTORY_DAYS): Promise<Record<string, MealPhotoEntry[]>> {
  await _pruneOldMealPhotos();
  days = Math.min(days, FOOD_HISTORY_DAYS);
  const all = await db.mealPhotos.orderBy("timestamp").reverse().toArray();
  const byDate: Record<string, MealPhotoEntry[]> = {};
  for (const entry of all) {
    (byDate[entry.date] ??= []).push(entry);
  }
  const dates = Object.keys(byDate).sort((a, b) => (a < b ? 1 : -1)).slice(0, days);
  const limited: Record<string, MealPhotoEntry[]> = {};
  for (const d of dates) limited[d] = byDate[d];
  return limited;
}

export async function deleteMealPhoto(id: number): Promise<void> {
  await db.mealPhotos.delete(id);
}

export function todayDateStr(): string {
  return _dateStr(new Date());
}

export async function getOrCreateProfile(): Promise<UserProfile> {
  const p = await db.profile.get(1);
  if (p) return p;
  await db.profile.put({
    id: 1, name: "", streak: 0, last_checkin_date: "",
    total_analyses: 0, goals: [], unlocked_achievements: [],
  });
  return (await db.profile.get(1))!;
}

export async function updateProfile(updates: Partial<Omit<UserProfile, "id">>): Promise<void> {
  await getOrCreateProfile();
  await db.profile.update(1, updates);
}

export async function unlockAchievements(ids: string[]): Promise<void> {
  if (!ids.length) return;
  const p = await getOrCreateProfile();
  const existing = p.unlocked_achievements ?? [];
  await db.profile.update(1, {
    unlocked_achievements: [...new Set([...existing, ...ids])],
  });
}

async function _upsertStreak(): Promise<void> {
  const p = await getOrCreateProfile();
  const today = _dateStr(new Date());
  const yesterday = _dateStr(new Date(Date.now() - 86_400_000));

  let streak = 1;
  if (p.last_checkin_date === today) {
    streak = p.streak;
  } else if (p.last_checkin_date === yesterday) {
    streak = p.streak + 1;
  }

  await db.profile.update(1, {
    streak,
    last_checkin_date: today,
    total_analyses: p.total_analyses + 1,
  });
}

export async function placePharmacyOrder(order: Omit<PharmacyOrder, "id">): Promise<number> {
  return (await db.pharmacyOrders.add(order)) as number;
}

export async function getPharmacyOrders(): Promise<PharmacyOrder[]> {
  return db.pharmacyOrders.orderBy("timestamp").reverse().toArray();
}

function _dateStr(d: Date): string {
  return d.toISOString().split("T")[0];
}

// ── derived stats ─────────────────────────────────────────

export function computeScoreLabel(score: number): AnalysisEntry["score_label"] {
  if (score >= 70) return "Good";
  if (score >= 40) return "Needs Attention";
  return "Action Required";
}

export function scoreColor(score: number): string {
  if (score >= 70) return "#22c55e";
  if (score >= 40) return "#f59e0b";
  return "#ef4444";
}

export function getTopDeficiencies(
  analyses: AnalysisEntry[],
  top = 6
): Array<{ deficiency: string; count: number; avgProb: number }> {
  const counts: Record<string, { count: number; totalProb: number }> = {};
  analyses.forEach((a) => {
    a.predictions
      .filter((p) => p.risk_level !== "low")
      .forEach((p) => {
        if (!counts[p.deficiency]) counts[p.deficiency] = { count: 0, totalProb: 0 };
        counts[p.deficiency].count++;
        counts[p.deficiency].totalProb += p.probability;
      });
  });
  return Object.entries(counts)
    .map(([deficiency, { count, totalProb }]) => ({
      deficiency,
      count,
      avgProb: totalProb / count,
    }))
    .sort((a, b) => b.count - a.count || b.avgProb - a.avgProb)
    .slice(0, top);
}

export function buildHeatmapData(
  analyses: AnalysisEntry[]
): Map<string, number> {
  const map = new Map<string, number>();
  analyses.forEach((a) => {
    const key = _dateStr(new Date(a.date));
    const existing = map.get(key);
    if (existing === undefined || a.score > existing) map.set(key, a.score);
  });
  return map;
}
