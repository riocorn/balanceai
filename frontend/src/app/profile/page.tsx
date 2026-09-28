"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Edit2, Check, X, Download, Flame, BarChart2, TrendingUp, Star } from "lucide-react";
import AppShell from "@/components/app/AppShell";
import { getOrCreateProfile, updateProfile, getAllAnalyses, scoreColor, type UserProfile, type AnalysisEntry } from "@/lib/db";
import { ACHIEVEMENTS } from "@/lib/achievements";
import { requestNotificationPermission, scheduleDailyReminder, isNotificationsSupported } from "@/lib/notifications";
import { toast } from "@/lib/toast";

const GOAL_LABELS: Record<string, string> = {
  energy:     "⚡ Thakaan kam karo",
  immunity:   "🛡️ Immunity badhao",
  hair_nails: "✨ Baal & nakhun",
  sleep:      "🌙 Neend theek karo",
  weight:     "⚖️ Weight manage",
  general:    "💚 General health",
};

const GENDER_LABELS: Record<string, string> = {
  male: "Male", female: "Female", other: "Other",
};

function avatarGradient(name: string): string {
  const colors = [
    ["#1d5c3d", "#06b6d4"],
    ["#818cf8", "#a78bfa"],
    ["#f59e0b", "#ef4444"],
    ["#34d399", "#10b981"],
    ["#f472b6", "#ec4899"],
  ];
  const idx = (name.charCodeAt(0) || 0) % colors.length;
  return `linear-gradient(135deg, ${colors[idx][0]}, ${colors[idx][1]})`;
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function ProfilePage() {
  const [profile,   setProfile]   = useState<UserProfile | null>(null);
  const [analyses,  setAnalyses]  = useState<AnalysisEntry[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [editing,   setEditing]   = useState(false);
  const [editName,  setEditName]  = useState("");
  const [editAge,   setEditAge]   = useState("");
  const [saving,    setSaving]    = useState(false);
  const [notifEnabled, setNotifEnabled] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setNotifEnabled(Notification?.permission === "granted");
    }
    Promise.all([getOrCreateProfile(), getAllAnalyses()]).then(([p, a]) => {
      setProfile(p);
      setAnalyses(a);
      setEditName(p.name);
      setEditAge(p.age?.toString() ?? "");
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    await updateProfile({ name: editName.trim() || "User", age: editAge ? parseInt(editAge) : undefined });
    const p = await getOrCreateProfile();
    setProfile(p);
    setSaving(false);
    setEditing(false);
  };

  const handleExportCSV = () => {
    if (!analyses.length) return;
    const rows = [
      ["Date", "Score", "Label", "High Risk", "Medium Risk", "State", "Vegetarian"],
      ...analyses.map((a) => [
        new Date(a.date).toLocaleDateString("en-IN"),
        a.score,
        a.score_label,
        a.high_risk.join("; "),
        a.medium_risk.join("; "),
        a.state || "",
        a.is_vegetarian ? "Yes" : "No",
      ]),
    ];
    const csv = rows.map((r) => r.map(String).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "balanceai_data.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading || !profile) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-screen">
          <div className="w-10 h-10 border-2 border-[#00d97e] border-t-transparent rounded-full animate-spin" />
        </div>
      </AppShell>
    );
  }

  const avgScore  = analyses.length ? Math.round(analyses.reduce((s, a) => s + a.score, 0) / analyses.length) : 0;
  const bestScore = analyses.length ? Math.max(...analyses.map((a) => a.score)) : 0;
  const unlocked  = new Set(profile.unlocked_achievements ?? []);

  const stats = [
    { label: "Total Analyses", value: profile.total_analyses, icon: BarChart2, color: "#818cf8" },
    { label: "Current Streak", value: `${profile.streak}d`, icon: Flame, color: "#f59e0b" },
    { label: "Best Score",     value: bestScore, icon: Star, color: "#fbbf24" },
    { label: "Avg Score",      value: avgScore,  icon: TrendingUp, color: scoreColor(avgScore) },
  ];

  return (
    <AppShell>
      <div className="px-5 sm:px-8 py-8 space-y-6 max-w-5xl mx-auto">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display font-bold text-2xl" style={{ color: "#1a1a1a" }}>
            Profile
          </h1>
        </motion.div>

        {/* Avatar + Name card */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-2xl p-6 flex items-center gap-5"
          style={{ background: "#f8f9f8", border: "1px solid #e4e7e2" }}
        >
          <div
            className="w-20 h-20 rounded-2xl flex items-center justify-center text-2xl font-black shrink-0"
            style={{ background: avatarGradient(profile.name || "U"), color: "#fff" }}
          >
            {initials(profile.name || "U")}
          </div>

          <div className="flex-1 min-w-0">
            {editing ? (
              <div className="space-y-2">
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Your name"
                  className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                  style={{ background: "#e4e7e2", border: "1px solid #c4cdd6", color: "#1a1a1a" }}
                />
                <input
                  type="number"
                  value={editAge}
                  onChange={(e) => setEditAge(e.target.value)}
                  placeholder="Age"
                  min={10} max={100}
                  className="w-24 px-3 py-2 rounded-lg text-sm outline-none"
                  style={{ background: "#e4e7e2", border: "1px solid #c4cdd6", color: "#1a1a1a" }}
                />
                <div className="flex gap-2">
                  <button onClick={handleSave} disabled={saving} className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-black" style={{ background: "#1d5c3d" }}>
                    <Check className="w-3 h-3" /> {saving ? "Saving..." : "Save"}
                  </button>
                  <button onClick={() => setEditing(false)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium" style={{ background: "#e9ece9", color: "#5a6571" }}>
                    <X className="w-3 h-3" /> Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="text-lg font-bold" style={{ color: "#1a1a1a" }}>
                    {profile.name || "User"}
                  </h2>
                  <button
                    onClick={() => setEditing(true)}
                    className="p-1 rounded-lg"
                    style={{ color: "#9aa5ae" }}
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <p className="text-sm" style={{ color: "#9aa5ae" }}>
                  {[profile.age && `${profile.age} yrs`, profile.gender && GENDER_LABELS[profile.gender]]
                    .filter(Boolean).join("  ·  ") || "Profile incomplete"}
                </p>
                {profile.goals && profile.goals.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {profile.goals.map((g) => (
                      <span
                        key={g}
                        className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                        style={{ background: "#eef7f2", border: "1px solid #eef7f2", color: "#1d5c3d" }}
                      >
                        {GOAL_LABELS[g] || g}
                      </span>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </motion.div>

        {/* Stats grid */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-3"
        >
          {stats.map((s, i) => (
            <div
              key={s.label}
              className="rounded-xl p-4 flex flex-col items-center gap-1.5"
              style={{ background: "#f8f9f8", border: "1px solid #e4e7e2" }}
            >
              <s.icon className="w-4 h-4" style={{ color: s.color }} />
              <p className="text-xl font-black font-display" style={{ color: s.color }}>{s.value}</p>
              <p className="text-[10px] text-center" style={{ color: "#9aa5ae" }}>{s.label}</p>
            </div>
          ))}
        </motion.div>

        {/* Achievements */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#9aa5ae" }}>
            Achievements ({unlocked.size}/{ACHIEVEMENTS.length})
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {ACHIEVEMENTS.map((a, i) => {
              const done = unlocked.has(a.id);
              return (
                <motion.div
                  key={a.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.15 + i * 0.04 }}
                  className="rounded-xl p-3.5 flex flex-col items-center gap-1.5 text-center"
                  style={{
                    background: done ? `${a.color}0d` : "#ffffff",
                    border: done ? `1px solid ${a.color}30` : "1px solid #e9ece9",
                    opacity: done ? 1 : 0.45,
                  }}
                >
                  <span className="text-2xl" style={{ filter: done ? "none" : "grayscale(100%)" }}>
                    {a.icon}
                  </span>
                  <p className="text-xs font-bold" style={{ color: done ? a.color : "#5a6571" }}>
                    {a.title}
                  </p>
                  <p className="text-[9px]" style={{ color: "#9aa5ae" }}>
                    {a.desc}
                  </p>
                  {done && (
                    <span className="text-[9px] font-bold uppercase tracking-wider" style={{ color: a.color }}>
                      ✓ Unlocked
                    </span>
                  )}
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Daily Reminder */}
        {isNotificationsSupported() && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28 }}
            className="rounded-xl p-4 flex items-center justify-between"
            style={{ background: "#ffffff", border: "1px solid #e9ece9" }}
          >
            <div>
              <p className="text-sm font-medium" style={{ color: "#2d3748" }}>Daily Reminder</p>
              <p className="text-xs" style={{ color: "#9aa5ae" }}>
                Roz subah 9 baje analysis reminder
              </p>
            </div>
            <button
              onClick={async () => {
                const granted = await requestNotificationPermission();
                if (granted) {
                  scheduleDailyReminder();
                  setNotifEnabled(true);
                  toast.success("Reminder set ho gaya! Roz subah 9 baje.");
                } else {
                  toast.warning("Notification permission denied hai.");
                }
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{
                background: notifEnabled ? "#eef7f2" : "#f5f5f3",
                border: notifEnabled ? "1px solid #b6ddc9" : "1px solid #e4e7e2",
                color: notifEnabled ? "#1d5c3d" : "#9aa5ae",
              }}
            >
              {notifEnabled ? "✓ On" : "Enable"}
            </button>
          </motion.div>
        )}

        {/* Export */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-xl p-4 flex items-center justify-between"
          style={{ background: "#ffffff", border: "1px solid #e9ece9" }}
        >
          <div>
            <p className="text-sm font-medium" style={{ color: "#2d3748" }}>Export Data</p>
            <p className="text-xs" style={{ color: "#9aa5ae" }}>
              Saare analyses ka CSV download karo
            </p>
          </div>
          <button
            onClick={handleExportCSV}
            disabled={!analyses.length}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all"
            style={{
              background: analyses.length ? "#eef7f2" : "#f8f9f8",
              border: analyses.length ? "1px solid #b6ddc9" : "1px solid #e4e7e2",
              color: analyses.length ? "#1d5c3d" : "#9aa5ae",
            }}
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </motion.div>
      </div>
    </AppShell>
  );
}
