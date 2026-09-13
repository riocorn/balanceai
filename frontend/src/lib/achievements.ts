import type { AnalysisEntry, UserProfile } from "@/lib/db";

export interface Achievement {
  id: string;
  title: string;
  desc: string;
  icon: string;
  color: string;
}

export const ACHIEVEMENTS: Achievement[] = [
  { id: "first_analysis", title: "Pehla Kadam",    desc: "Pehla analysis complete kiya",           icon: "🌱", color: "#22c55e" },
  { id: "streak_3",       title: "Teesra Din",      desc: "3 din lagataar analyze kiya",            icon: "🔥", color: "#f59e0b" },
  { id: "streak_7",       title: "Health Warrior",  desc: "7 din ka streak achieve kiya",           icon: "⚔️", color: "#ef4444" },
  { id: "score_80",       title: "Champion",        desc: "Score 80 ya usse zyada hasil kiya",      icon: "🏆", color: "#fbbf24" },
  { id: "analyses_10",    title: "Dedicated",       desc: "10 analyses complete kiye",              icon: "💎", color: "#818cf8" },
  { id: "improving",      title: "On The Rise",     desc: "4 baar lagataar score improve hua",      icon: "📈", color: "#00d97e" },
  { id: "balanced",       title: "Balanced",        desc: "5 baar score 70+ aaya",                  icon: "⚖️", color: "#34d399" },
  { id: "explorer",       title: "Explorer",        desc: "Voice + camera + symptoms — sab use kiya", icon: "🗺️", color: "#a78bfa" },
];

export function checkNewAchievements(
  analyses: AnalysisEntry[],
  profile: UserProfile,
): Achievement[] {
  const unlocked = new Set(profile.unlocked_achievements ?? []);
  const earned: Achievement[] = [];

  const check = (id: string, cond: boolean) => {
    if (cond && !unlocked.has(id)) {
      const badge = ACHIEVEMENTS.find((a) => a.id === id);
      if (badge) earned.push(badge);
    }
  };

  check("first_analysis", analyses.length >= 1);
  check("streak_3",       profile.streak >= 3);
  check("streak_7",       profile.streak >= 7);
  check("score_80",       analyses.some((a) => a.score >= 80));
  check("analyses_10",    profile.total_analyses >= 10);
  check("balanced",       analyses.filter((a) => a.score >= 70).length >= 5);

  if (analyses.length >= 4) {
    const [a, b, c, d] = analyses;
    check("improving", a.score > b.score && b.score > c.score && c.score > d.score);
  }

  const hasVoice    = analyses.some((a) => a.symptoms_text.length > 0);
  const hasCamera   = analyses.some((a) => a.image_results && Object.keys(a.image_results).length > 0);
  const hasSymptoms = analyses.some((a) => a.selected_symptoms.length > 0);
  check("explorer", hasVoice && hasCamera && hasSymptoms);

  return earned;
}
