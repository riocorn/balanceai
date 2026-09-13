"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { PlusCircle, AlertTriangle, CheckCircle2, Flame, Calendar, TrendingUp, TrendingDown, Minus } from "lucide-react";
import AppShell from "@/components/app/AppShell";
import { DashboardSkeleton } from "@/components/app/Skeleton";
import ScoreRing from "@/components/app/ScoreRing";
import StreakCalendar from "@/components/app/StreakCalendar";
import TrendChart from "@/components/app/TrendChart";
import {
  getAllAnalyses, getOrCreateProfile,
  scoreColor, computeScoreLabel, getTopDeficiencies,
  type AnalysisEntry, type UserProfile,
} from "@/lib/db";
import { DEFICIENCY_LABELS } from "@/lib/api";

const RANGE_OPTIONS = ["30", "60", "90", "all"] as const;
type Range = typeof RANGE_OPTIONS[number];

const MEAL_ICONS: Record<string, string> = {
  breakfast: "🌅", lunch: "☀️", snacks: "🍎", dinner: "🌙",
};

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<AnalysisEntry[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<Range>("30");

  useEffect(() => {
    Promise.all([getAllAnalyses(), getOrCreateProfile()]).then(([data, prof]) => {
      setAnalyses(data);
      setProfile(prof);
      setLoading(false);
    });
  }, []);

  const latest = analyses[0];
  const previous = analyses[1];
  const scoreDelta = latest && previous ? latest.score - previous.score : null;

  const filteredAnalyses = useMemo(() => {
    if (range === "all") return analyses;
    const days = parseInt(range);
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    return analyses.filter((a) => a.timestamp > cutoff);
  }, [analyses, range]);

  const chartData = useMemo(() =>
    filteredAnalyses.slice().reverse().map((a) => ({
      date: new Date(a.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
      score: a.score,
    })), [filteredAnalyses]);

  const topDeficiencies = useMemo(() => getTopDeficiencies(analyses, 5), [analyses]);

  if (loading) {
    return (
      <AppShell>
        <DashboardSkeleton />
      </AppShell>
    );
  }

  if (analyses.length === 0) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
          <div
            className="w-20 h-20 rounded-3xl flex items-center justify-center mb-6 text-4xl"
            style={{ background: "rgba(0,217,126,0.08)", border: "1px solid rgba(0,217,126,0.15)" }}
          >
            🌱
          </div>
          <h2 className="land-h3 mb-3" style={{ color: "rgba(255,255,255,0.85)" }}>
            Pehla Analysis Karo
          </h2>
          <p className="text-sm mb-8 max-w-sm" style={{ color: "rgba(255,255,255,0.4)" }}>
            Apna pehla nutrition analysis complete karo — dashboard automatically populate ho jaayega.
          </p>
          <Link href="/analyze">
            <button
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-black text-sm glow-btn"
              style={{ background: "#00d97e" }}
            >
              <PlusCircle className="w-4 h-4" />
              Abhi Analysis Karo
            </button>
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="px-5 sm:px-8 py-8 space-y-6 max-w-6xl mx-auto">
        {/* Page header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <p className="text-sm font-semibold mb-0.5" style={{ color: "rgba(255,255,255,0.35)" }}>
            {new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}
          </p>
          <h1 className="font-display font-bold text-2xl" style={{ color: "rgba(255,255,255,0.9)" }}>
            Health Dashboard
          </h1>
        </motion.div>

        {/* Row 1: Score + Trend chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Score card */}
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
            className="rounded-2xl p-6 flex flex-col items-center gap-4"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
          >
            <ScoreRing score={latest.score} />

            {/* Delta vs previous */}
            {scoreDelta !== null && (
              <div className="flex items-center gap-1.5 text-sm">
                {scoreDelta > 0 ? (
                  <><TrendingUp className="w-4 h-4 text-green-400" /><span style={{ color: "#22c55e" }}>+{scoreDelta} vs last</span></>
                ) : scoreDelta < 0 ? (
                  <><TrendingDown className="w-4 h-4 text-red-400" /><span style={{ color: "#ef4444" }}>{scoreDelta} vs last</span></>
                ) : (
                  <><Minus className="w-4 h-4" style={{ color: "rgba(255,255,255,0.3)" }} /><span style={{ color: "rgba(255,255,255,0.3)" }}>No change</span></>
                )}
              </div>
            )}

            <Link href="/analyze" className="w-full">
              <button
                className="w-full py-2.5 rounded-xl text-sm font-semibold text-black transition-all"
                style={{ background: "#00d97e" }}
              >
                Re-analyze
              </button>
            </Link>
          </motion.div>

          {/* Trend chart */}
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="lg:col-span-2 rounded-2xl p-5"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
          >
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.7)" }}>Score Trend</p>
              <div className="flex gap-1">
                {RANGE_OPTIONS.map((r) => (
                  <button
                    key={r}
                    onClick={() => setRange(r)}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium transition-all"
                    style={{
                      background: range === r ? "rgba(0,217,126,0.15)" : "rgba(255,255,255,0.04)",
                      color: range === r ? "#00d97e" : "rgba(255,255,255,0.4)",
                      border: range === r ? "1px solid rgba(0,217,126,0.3)" : "1px solid transparent",
                    }}
                  >
                    {r === "all" ? "All" : `${r}d`}
                  </button>
                ))}
              </div>
            </div>
            <TrendChart data={chartData} height={160} />
          </motion.div>
        </div>

        {/* Row 2: Streak + Calendar */}
        <motion.div
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="rounded-2xl p-5"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl"
                style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.15)" }}
              >
                <Flame className="w-4 h-4" style={{ color: "#f59e0b" }} />
                <span className="text-sm font-bold" style={{ color: "#f59e0b" }}>
                  {profile?.streak ?? 0} day streak
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-xs" style={{ color: "rgba(255,255,255,0.35)" }}>
                <Calendar className="w-3.5 h-3.5" />
                {profile?.total_analyses ?? 0} total analyses
              </div>
            </div>
            <span className="text-xs" style={{ color: "rgba(255,255,255,0.25)" }}>Last 26 weeks</span>
          </div>
          <StreakCalendar analyses={analyses} weeks={26} />
        </motion.div>

        {/* Row 3: Top deficiencies */}
        <motion.div
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
        >
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>
            Frequent Deficiencies (all time)
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {topDeficiencies.map((d, i) => {
              const color = d.avgProb > 0.7 ? "#ef4444" : d.avgProb > 0.5 ? "#f59e0b" : "#22c55e";
              return (
                <motion.div
                  key={d.deficiency}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                  className="rounded-xl p-3.5 flex flex-col gap-1.5"
                  style={{ background: `${color}0a`, border: `1px solid ${color}20` }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: `${color}99` }}>
                      {d.count}× flagged
                    </span>
                    <AlertTriangle className="w-3 h-3" style={{ color }} />
                  </div>
                  <p className="text-xs font-semibold leading-tight" style={{ color: "rgba(255,255,255,0.85)" }}>
                    {DEFICIENCY_LABELS[d.deficiency] || d.deficiency}
                  </p>
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.07)" }}>
                    <div className="h-full rounded-full" style={{ width: `${d.avgProb * 100}%`, background: color }} />
                  </div>
                </motion.div>
              );
            })}
            {topDeficiencies.length === 0 && (
              <div
                className="col-span-full py-8 text-center text-sm rounded-xl"
                style={{ color: "rgba(255,255,255,0.25)", border: "1px dashed rgba(255,255,255,0.06)" }}
              >
                Enough data ke baad trends dikhenge
              </div>
            )}
          </div>
        </motion.div>

        {/* Row 4: Diet plan + Recent analyses */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Diet plan */}
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
            className="rounded-2xl p-5"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
          >
            <p className="text-sm font-semibold mb-4" style={{ color: "rgba(255,255,255,0.7)" }}>
              🍽️ Aaj ka Diet Plan
            </p>
            {latest.diet_plan && Object.keys(latest.diet_plan).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(latest.diet_plan).map(([meal, foods]) => (
                  <div key={meal}>
                    <p className="text-xs font-medium capitalize mb-1.5" style={{ color: "rgba(255,255,255,0.4)" }}>
                      {MEAL_ICONS[meal] || "🍽️"} {meal}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {(Array.isArray(foods) ? foods : []).slice(0, 4).map((f: string, i: number) => (
                        <span
                          key={i}
                          className="text-xs px-2.5 py-1 rounded-full"
                          style={{ background: "rgba(0,217,126,0.07)", border: "1px solid rgba(0,217,126,0.12)", color: "rgba(0,217,126,0.8)" }}
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm" style={{ color: "rgba(255,255,255,0.3)" }}>
                Diet plan ke liye analyze karo
              </p>
            )}
          </motion.div>

          {/* Recent analyses */}
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            className="rounded-2xl p-5"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
          >
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.7)" }}>Recent Analyses</p>
              <Link href="/history">
                <span className="text-xs" style={{ color: "#00d97e" }}>View all →</span>
              </Link>
            </div>
            <div className="space-y-2">
              {analyses.slice(0, 5).map((a, i) => {
                const color = scoreColor(a.score);
                const dateStr = new Date(a.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
                return (
                  <div
                    key={a.id ?? i}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors"
                    style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}
                  >
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                      style={{ background: `${color}10` }}
                    >
                      <span className="text-sm font-bold font-display" style={{ color }}>{a.score}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.75)" }}>
                        {a.score_label}
                      </p>
                      <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                        {dateStr}{a.state ? ` · ${a.state}` : ""}
                      </p>
                    </div>
                    {a.high_risk.length > 0 && (
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" style={{ color: "#ef4444" }} />
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>
      </div>
    </AppShell>
  );
}
