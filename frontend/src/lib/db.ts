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

  constructor() {
    super("balanceai_v1");
    this.version(1).stores({
      analyses: "++id, timestamp, score",
      profile: "++id",
    });
  }
}

export const db = new BalanceAIDatabase();

// ── helpers ──────────────────────────────────────────────

export async function saveAnalysis(
  entry: Omit<AnalysisEntry, "id">
): Promise<number> {
  const id = await db.analyses.add(entry);
  await _upsertStreak();
  return id as number;
}

export async function getAllAnalyses(): Promise<AnalysisEntry[]> {
  return db.analyses.orderBy("timestamp").reverse().toArray();
}

export async function getRecentAnalyses(n = 5): Promise<AnalysisEntry[]> {
  return db.analyses.orderBy("timestamp").reverse().limit(n).toArray();
}

export async function deleteAnalysis(id: number): Promise<void> {
  await db.analyses.delete(id);
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
