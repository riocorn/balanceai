"use client";

import { useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import AppShell from "@/components/app/AppShell";
import { getAllAnalyses, type AnalysisEntry } from "@/lib/db";
import { DEFICIENCY_LABELS } from "@/lib/api";
import {
  NATIONAL_PREVALENCE, STATE_PREVALENCE, DEFICIENCY_DESCRIPTIONS,
  getSeasonalTip, getStateData,
} from "@/lib/india-data";

const TOP_DEFICIENCIES = ["iron", "omega3", "vitamin_b12", "calcium", "vitamin_d", "zinc", "folate", "vitamin_a"];

const RISK_COLORS = ["#ef4444", "#f97316", "#f59e0b", "#eab308", "#22c55e", "#10b981", "#06b6d4", "#818cf8"];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="px-3 py-2 rounded-xl text-xs" style={{ background: "rgba(6,6,10,0.95)", border: "1px solid #e4e7e2" }}>
      <p style={{ color: "#5a6571", marginBottom: 2 }}>{label}</p>
      <p style={{ color: "#1d5c3d", fontWeight: 700 }}>{payload[0]?.value}% prevalence</p>
    </div>
  );
};

export default function InsightsPage() {
  const [analyses, setAnalyses] = useState<AnalysisEntry[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [selected, setSelected] = useState<string>("iron");

  useEffect(() => {
    getAllAnalyses().then((a) => { setAnalyses(a); setLoading(false); });
  }, []);

  const userState = useMemo(() => {
    const counts: Record<string, number> = {};
    analyses.forEach((a) => { if (a.state) counts[a.state] = (counts[a.state] || 0) + 1; });
    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
  }, [analyses]);

  const stateData = useMemo(() => userState ? getStateData(userState) : null, [userState]);

  const nationalChartData = useMemo(() =>
    TOP_DEFICIENCIES.map((key) => ({
      name: DEFICIENCY_LABELS[key] || key,
      key,
      value: NATIONAL_PREVALENCE[key] ?? 0,
    })).sort((a, b) => b.value - a.value),
  []);

  const comparisonData = useMemo(() => {
    if (!stateData) return [];
    return TOP_DEFICIENCIES.map((key) => ({
      name: (DEFICIENCY_LABELS[key] || key).split(" ")[0],
      key,
      national: NATIONAL_PREVALENCE[key] ?? 0,
      state: stateData[key] ?? NATIONAL_PREVALENCE[key] ?? 0,
    })).sort((a, b) => b.state - a.state);
  }, [stateData]);

  const seasonalTip = useMemo(() => getSeasonalTip(), []);

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-screen">
          <div className="w-10 h-10 border-2 border-[#00d97e] border-t-transparent rounded-full animate-spin" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="px-5 sm:px-8 py-8 space-y-8 max-w-5xl mx-auto">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <p className="text-sm font-semibold mb-0.5" style={{ color: "#9aa5ae" }}>
            India Nutrition Data
          </p>
          <h1 className="font-display font-bold text-2xl" style={{ color: "#1a1a1a" }}>
            Insights
          </h1>
        </motion.div>

        {/* Seasonal tip */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-2xl p-5"
          style={{ background: "#eef7f2", border: "1px solid #eef7f2" }}
        >
          <div className="flex items-start gap-3">
            <span className="text-2xl shrink-0">🌡️</span>
            <div>
              <p className="text-sm font-bold mb-1" style={{ color: "#1d5c3d" }}>
                {seasonalTip.title}
              </p>
              <p className="text-sm" style={{ color: "#5a6571" }}>
                {seasonalTip.tip}
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {seasonalTip.deficiencies.map((d) => (
                  <span
                    key={d}
                    className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                    style={{ background: "#eef7f2", color: "#1d5c3d", border: "1px solid #b6ddc9" }}
                  >
                    {DEFICIENCY_LABELS[d] || d}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* National prevalence chart */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl p-5"
          style={{ background: "#f8f9f8", border: "1px solid #e4e7e2" }}
        >
          <p className="text-sm font-semibold mb-1" style={{ color: "#5a6571" }}>
            India Deficiency Prevalence
          </p>
          <p className="text-xs mb-5" style={{ color: "#9aa5ae" }}>
            % population affected — NFHS-5, NNMB 2012
          </p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={nationalChartData} layout="vertical" margin={{ top: 0, right: 48, left: 0, bottom: 0 }}>
              <XAxis type="number" domain={[0, 80]} tick={{ fill: "#9aa5ae", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: "#5a6571", fontSize: 10 }} axisLine={false} tickLine={false} width={80} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "#ffffff" }} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={18}>
                {nationalChartData.map((_, i) => (
                  <Cell key={i} fill={RISK_COLORS[i % RISK_COLORS.length]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* State comparison */}
        {stateData && userState && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="rounded-2xl p-5"
            style={{ background: "#f8f9f8", border: "1px solid #e4e7e2" }}
          >
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-semibold" style={{ color: "#5a6571" }}>
                {userState} vs National Average
              </p>
              <span
                className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                style={{ background: "rgba(129,140,248,0.1)", color: "#818cf8", border: "1px solid rgba(129,140,248,0.25)" }}
              >
                YOUR STATE
              </span>
            </div>
            <p className="text-xs mb-5" style={{ color: "#9aa5ae" }}>
              Deficiency prevalence (%) in your state
            </p>

            <div className="space-y-3">
              {comparisonData.slice(0, 6).map((d, i) => (
                <motion.div
                  key={d.key}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.05 }}
                >
                  <div className="flex items-center gap-3 mb-1.5">
                    <p className="text-xs font-medium w-24 shrink-0" style={{ color: "#5a6571" }}>
                      {DEFICIENCY_LABELS[d.key] || d.key}
                    </p>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "#e9ece9" }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(d.state / 80) * 100}%` }}
                            transition={{ delay: 0.2 + i * 0.05, duration: 0.5 }}
                            className="h-full rounded-full"
                            style={{ background: "#818cf8" }}
                          />
                        </div>
                        <span className="text-[10px] font-bold w-8 text-right" style={{ color: "#818cf8" }}>{d.state}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: "#f8f9f8" }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(d.national / 80) * 100}%` }}
                            transition={{ delay: 0.25 + i * 0.05, duration: 0.5 }}
                            className="h-full rounded-full"
                            style={{ background: "#9aa5ae" }}
                          />
                        </div>
                        <span className="text-[10px] w-8 text-right" style={{ color: "#9aa5ae" }}>{d.national}%</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-1.5 rounded-full" style={{ background: "#818cf8" }} />
                <span className="text-[10px]" style={{ color: "#9aa5ae" }}>{userState}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-1 rounded-full" style={{ background: "#9aa5ae" }} />
                <span className="text-[10px]" style={{ color: "#9aa5ae" }}>National avg</span>
              </div>
            </div>
          </motion.div>
        )}

        {!userState && (
          <div
            className="rounded-xl p-4 text-center text-sm"
            style={{ background: "#ffffff", border: "1px dashed #e4e7e2", color: "#9aa5ae" }}
          >
            Apna state select karo analysis mein — state-wise comparison dikhega
          </div>
        )}

        {/* Deficiency info cards */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#9aa5ae" }}>
            About Top Deficiencies
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {TOP_DEFICIENCIES.slice(0, 6).map((key, i) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.05 }}
                className="rounded-xl p-4"
                style={{ background: "#ffffff", border: "1px solid #e9ece9" }}
              >
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold" style={{ color: "#1a1a1a" }}>
                    {DEFICIENCY_LABELS[key] || key}
                  </p>
                  <span
                    className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                    style={{ background: `${RISK_COLORS[i]}18`, color: RISK_COLORS[i] }}
                  >
                    {NATIONAL_PREVALENCE[key]}%
                  </span>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "#9aa5ae" }}>
                  {DEFICIENCY_DESCRIPTIONS[key]}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <p className="text-xs text-center pb-4" style={{ color: "#9aa5ae" }}>
          Data source: NFHS-5 (2019-21), NNMB 2012, ICMR RDA Guidelines
        </p>
      </div>
    </AppShell>
  );
}
