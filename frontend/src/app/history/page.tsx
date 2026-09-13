"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  PlusCircle, BarChart2, Clock, TrendingUp, TrendingDown,
  Minus, Lightbulb, AlertTriangle,
} from "lucide-react";
import AppShell from "@/components/app/AppShell";
import { HistorySkeleton } from "@/components/app/Skeleton";
import HistoryCard from "@/components/app/HistoryCard";
import TrendChart from "@/components/app/TrendChart";
import {
  getAllAnalyses, scoreColor, computeScoreLabel, getTopDeficiencies,
  type AnalysisEntry,
} from "@/lib/db";
import { DEFICIENCY_LABELS } from "@/lib/api";

const RANGE_OPTIONS = ["30", "60", "90", "all"] as const;
type Range = typeof RANGE_OPTIONS[number];

function groupByMonth(entries: AnalysisEntry[]): Array<{ label: string; items: AnalysisEntry[] }> {
  const map = new Map<string, AnalysisEntry[]>();
  entries.forEach((e) => {
    const key = new Date(e.date).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(e);
  });
  return Array.from(map.entries()).map(([label, items]) => ({ label, items }));
}

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<AnalysisEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"timeline" | "analytics">("timeline");
  const [range, setRange] = useState<Range>("30");

  useEffect(() => {
    getAllAnalyses().then((data) => { setAnalyses(data); setLoading(false); });
  }, []);

  const handleDelete = (id: number) => setAnalyses((prev) => prev.filter((a) => a.id !== id));

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

  const topDeficiencies = useMemo(() => getTopDeficiencies(analyses, 8), [analyses]);
  const groups = useMemo(() => groupByMonth(analyses), [analyses]);

  const avgScore = useMemo(() => {
    if (!filteredAnalyses.length) return null;
    return Math.round(filteredAnalyses.reduce((s, a) => s + a.score, 0) / filteredAnalyses.length);
  }, [filteredAnalyses]);

  const scoreTrend = useMemo(() => {
    if (filteredAnalyses.length < 2) return null;
    const recent = filteredAnalyses.slice(0, Math.ceil(filteredAnalyses.length / 2));
    const older = filteredAnalyses.slice(Math.ceil(filteredAnalyses.length / 2));
    const recentAvg = recent.reduce((s, a) => s + a.score, 0) / recent.length;
    const olderAvg = older.reduce((s, a) => s + a.score, 0) / older.length;
    return Math.round(recentAvg - olderAvg);
  }, [filteredAnalyses]);

  const insights = useMemo(() => {
    const out: string[] = [];
    if (topDeficiencies[0]) {
      out.push(`${DEFICIENCY_LABELS[topDeficiencies[0].deficiency] || topDeficiencies[0].deficiency} ${topDeficiencies[0].count} baar flagged — sabse zyada concern`);
    }
    if (scoreTrend !== null && scoreTrend > 3) out.push(`Score last period se ${scoreTrend} points improve hua — great progress!`);
    if (scoreTrend !== null && scoreTrend < -3) out.push(`Score ${Math.abs(scoreTrend)} points gira — aaj analyze karo`);
    if (analyses.length > 0 && avgScore !== null) {
      const label = computeScoreLabel(avgScore);
      out.push(`Average score: ${avgScore}/100 (${label})`);
    }
    const highRiskAll = analyses.flatMap((a) => a.high_risk);
    const highCounts: Record<string, number> = {};
    highRiskAll.forEach((d) => { highCounts[d] = (highCounts[d] || 0) + 1; });
    const topHigh = Object.entries(highCounts).sort((a, b) => b[1] - a[1])[0];
    if (topHigh && topHigh[1] > 1) {
      out.push(`${DEFICIENCY_LABELS[topHigh[0]] || topHigh[0]} ${topHigh[1]} baar high risk raha`);
    }
    return out.slice(0, 3);
  }, [topDeficiencies, scoreTrend, analyses, avgScore]);

  if (loading) {
    return (
      <AppShell>
        <HistorySkeleton />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="px-5 sm:px-8 py-8 space-y-6 max-w-5xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold mb-0.5" style={{ color: "rgba(255,255,255,0.35)" }}>
              {analyses.length} total analyses
            </p>
            <h1 className="font-display font-bold text-2xl" style={{ color: "rgba(255,255,255,0.9)" }}>
              History
            </h1>
          </div>
          <Link href="/analyze">
            <button
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-black"
              style={{ background: "#00d97e" }}
            >
              <PlusCircle className="w-4 h-4" />
              New Analysis
            </button>
          </Link>
        </motion.div>

        {/* Tab toggle */}
        <motion.div
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
          className="flex gap-1 p-1 rounded-xl w-fit"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          {(["timeline", "analytics"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all"
              style={{
                background: tab === t ? "rgba(0,217,126,0.12)" : "transparent",
                color: tab === t ? "#00d97e" : "rgba(255,255,255,0.4)",
                border: tab === t ? "1px solid rgba(0,217,126,0.25)" : "1px solid transparent",
              }}
            >
              {t === "timeline" ? <Clock className="w-3.5 h-3.5" /> : <BarChart2 className="w-3.5 h-3.5" />}
              {t}
            </button>
          ))}
        </motion.div>

        {/* Empty state */}
        {analyses.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 text-3xl"
              style={{ background: "rgba(0,217,126,0.08)", border: "1px solid rgba(0,217,126,0.15)" }}
            >
              📊
            </div>
            <p className="font-semibold mb-2" style={{ color: "rgba(255,255,255,0.7)" }}>Abhi tak koi analysis nahi</p>
            <p className="text-sm mb-6" style={{ color: "rgba(255,255,255,0.35)" }}>Pehla analysis karo — history yahin dikhegi</p>
            <Link href="/analyze">
              <button
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-black"
                style={{ background: "#00d97e" }}
              >
                <PlusCircle className="w-4 h-4" /> Analyze Karo
              </button>
            </Link>
          </div>
        )}

        <AnimatePresence mode="wait">
          {/* ── TIMELINE TAB ── */}
          {tab === "timeline" && analyses.length > 0 && (
            <motion.div
              key="timeline"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 12 }}
              className="space-y-6"
            >
              {groups.map(({ label, items }, gi) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: gi * 0.06 }}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.3)" }}>
                      {label}
                    </p>
                    <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.05)" }} />
                    <p className="text-xs" style={{ color: "rgba(255,255,255,0.2)" }}>{items.length} entries</p>
                  </div>
                  <div className="space-y-2">
                    {items.map((entry) => (
                      <HistoryCard key={entry.id} entry={entry} onDelete={handleDelete} />
                    ))}
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}

          {/* ── ANALYTICS TAB ── */}
          {tab === "analytics" && analyses.length > 0 && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }}
              className="space-y-5"
            >
              {/* Range + stat pills */}
              <div className="flex flex-wrap items-center gap-3">
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

                {avgScore !== null && (
                  <div
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold"
                    style={{ background: `${scoreColor(avgScore)}12`, color: scoreColor(avgScore), border: `1px solid ${scoreColor(avgScore)}25` }}
                  >
                    Avg: {avgScore}/100
                  </div>
                )}

                {scoreTrend !== null && (
                  <div
                    className="flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-lg"
                    style={{
                      background: scoreTrend > 0 ? "rgba(34,197,94,0.08)" : scoreTrend < 0 ? "rgba(239,68,68,0.08)" : "rgba(255,255,255,0.04)",
                      color: scoreTrend > 0 ? "#22c55e" : scoreTrend < 0 ? "#ef4444" : "rgba(255,255,255,0.3)",
                    }}
                  >
                    {scoreTrend > 0 ? <TrendingUp className="w-3 h-3" /> : scoreTrend < 0 ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                    {scoreTrend > 0 ? `+${scoreTrend}` : scoreTrend} trend
                  </div>
                )}
              </div>

              {/* Score trend chart */}
              <div
                className="rounded-2xl p-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <p className="text-sm font-semibold mb-4" style={{ color: "rgba(255,255,255,0.7)" }}>Score Trend</p>
                <TrendChart data={chartData} height={180} />
              </div>

              {/* AI Insights */}
              {insights.length > 0 && (
                <div
                  className="rounded-2xl p-5"
                  style={{ background: "rgba(0,217,126,0.04)", border: "1px solid rgba(0,217,126,0.1)" }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="w-4 h-4" style={{ color: "#00d97e" }} />
                    <p className="text-sm font-semibold" style={{ color: "#00d97e" }}>AI Insights</p>
                  </div>
                  <div className="space-y-2">
                    {insights.map((ins, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ background: "#00d97e" }} />
                        <p className="text-sm" style={{ color: "rgba(255,255,255,0.7)" }}>{ins}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Nutrient frequency */}
              {topDeficiencies.length > 0 && (
                <div
                  className="rounded-2xl p-5"
                  style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
                >
                  <div className="flex items-center gap-2 mb-4">
                    <AlertTriangle className="w-4 h-4" style={{ color: "#f59e0b" }} />
                    <p className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.7)" }}>
                      Deficiency Frequency (all time)
                    </p>
                  </div>
                  <div className="space-y-3">
                    {topDeficiencies.map((d, i) => {
                      const color = d.avgProb > 0.7 ? "#ef4444" : d.avgProb > 0.5 ? "#f59e0b" : "#22c55e";
                      const maxCount = topDeficiencies[0].count;
                      return (
                        <motion.div
                          key={d.deficiency}
                          initial={{ opacity: 0, x: -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.04 }}
                          className="flex items-center gap-3"
                        >
                          <p className="text-xs font-medium w-36 shrink-0 truncate" style={{ color: "rgba(255,255,255,0.75)" }}>
                            {DEFICIENCY_LABELS[d.deficiency] || d.deficiency}
                          </p>
                          <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{ background: color }}
                              initial={{ width: 0 }}
                              animate={{ width: `${(d.count / maxCount) * 100}%` }}
                              transition={{ delay: 0.15 + i * 0.04, duration: 0.5, ease: "easeOut" }}
                            />
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-xs font-bold" style={{ color, minWidth: 16, textAlign: "right" }}>
                              {d.count}×
                            </span>
                            <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                              {Math.round(d.avgProb * 100)}%
                            </span>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Score distribution */}
              <div
                className="rounded-2xl p-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <p className="text-sm font-semibold mb-4" style={{ color: "rgba(255,255,255,0.7)" }}>Score Distribution</p>
                <ScoreDistribution analyses={filteredAnalyses} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AppShell>
  );
}

function ScoreDistribution({ analyses }: { analyses: AnalysisEntry[] }) {
  const buckets = useMemo(() => {
    const b = [
      { label: "0–39", color: "#ef4444", count: 0 },
      { label: "40–69", color: "#f59e0b", count: 0 },
      { label: "70–100", color: "#22c55e", count: 0 },
    ];
    analyses.forEach((a) => {
      if (a.score < 40) b[0].count++;
      else if (a.score < 70) b[1].count++;
      else b[2].count++;
    });
    return b;
  }, [analyses]);

  const max = Math.max(...buckets.map((b) => b.count), 1);

  return (
    <div className="flex items-end gap-4 h-28">
      {buckets.map((b, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1.5">
          <span className="text-xs font-bold" style={{ color: b.color }}>{b.count}</span>
          <div className="w-full rounded-t-lg overflow-hidden" style={{ height: 80, background: "rgba(255,255,255,0.04)" }}>
            <motion.div
              className="w-full rounded-t-lg"
              style={{ background: `${b.color}40`, borderTop: `2px solid ${b.color}` }}
              initial={{ height: 0 }}
              animate={{ height: `${(b.count / max) * 100}%` }}
              transition={{ delay: 0.1 + i * 0.08, duration: 0.5, ease: "easeOut" }}
            />
          </div>
          <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>{b.label}</span>
        </div>
      ))}
    </div>
  );
}
