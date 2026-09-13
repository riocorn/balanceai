"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  TrendingUp, TrendingDown, Minus, AlertTriangle,
  CheckCircle2, Download, RefreshCw, LayoutDashboard,
  ChevronDown, Loader2, Calendar, MapPin, Leaf, Share2,
} from "lucide-react";
import AppShell from "@/components/app/AppShell";
import ScoreRing from "@/components/app/ScoreRing";
import BodyHeatmap from "@/components/app/BodyHeatmap";
import Confetti from "@/components/app/Confetti";
import ShareCard from "@/components/app/ShareCard";
import { getAllAnalyses, scoreColor, computeScoreLabel } from "@/lib/db";
import { DEFICIENCY_LABELS, type AnalysisResult, type DeficiencyResult, type Recommendation } from "@/lib/api";
import { generatePDF } from "@/lib/pdf";
import { getRecipesForDeficiency, NUTRIENT_UNITS, type FoodItem } from "@/lib/food-db";
import { RECIPE_DB } from "@/lib/recipe-db";
import type { MealPlan, PortionedItem } from "@/lib/diet-engine";

const MEAL_ICON: Record<string, string> = {
  breakfast: "🌅", lunch: "☀️", snacks: "🍎", dinner: "🌙",
};
const MEAL_LABEL: Record<string, string> = {
  breakfast: "Breakfast", lunch: "Lunch", snacks: "Snacks", dinner: "Dinner",
};

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<(AnalysisResult & { imageResults?: Record<string, unknown> }) | null>(null);
  const [prevScore, setPrevScore] = useState<number | null>(null);
  const [confetti, setConfetti] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [analyzeDate] = useState(() => new Date().toLocaleDateString("en-IN", {
    weekday: "short", day: "numeric", month: "long",
  }));

  useEffect(() => {
    const raw = sessionStorage.getItem("balanceai_result");
    if (!raw) { router.push("/analyze"); return; }
    try {
      const parsed = JSON.parse(raw);
      setResult(parsed);
      const sc = parsed.balance_score?.overall_score ?? 0;
      if (sc >= 70) setTimeout(() => setConfetti(true), 1000);

      const mpRaw = sessionStorage.getItem("balanceai_meal_plan");
      if (mpRaw) {
        try { setMealPlan(JSON.parse(mpRaw)); } catch { /* ignore */ }
      }
    } catch { router.push("/analyze"); }

    getAllAnalyses().then((list) => {
      if (list.length >= 2) setPrevScore(list[1].score);
    });
  }, [router]);

  if (!result) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-screen">
          <div className="w-10 h-10 border-2 border-[#00d97e] border-t-transparent rounded-full animate-spin" />
        </div>
      </AppShell>
    );
  }

  const {
    deficiency_predictions: preds = [],
    balance_score,
    recommendations = [],
    diet_plan,
    alerts = [],
  } = result;

  const score = balance_score?.overall_score ?? 0;
  const high = balance_score?.high_risk_deficiencies ?? [];
  const medium = balance_score?.medium_risk_deficiencies ?? [];
  const delta = prevScore !== null ? score - prevScore : null;
  const color = scoreColor(score);

  const sortedPreds = [...preds].sort((a, b) => {
    const O: Record<string, number> = { high: 0, medium: 1, low: 2 };
    return O[a.risk_level] - O[b.risk_level];
  });

  const topConcerns = sortedPreds
    .filter((p) => p.risk_level !== "low")
    .slice(0, 3)
    .map((p) => DEFICIENCY_LABELS[p.deficiency] || p.deficiency);

  const handlePDF = async () => {
    setPdfLoading(true);
    try {
      await generatePDF({
        score,
        score_label: computeScoreLabel(score),
        predictions: preds,
        diet_plan: diet_plan ?? {},
        recommendations,
        alerts: alerts as string[],
        date: new Date().toLocaleDateString("en-IN"),
      });
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <AppShell>
      {confetti && <Confetti />}
      <div className="px-5 sm:px-8 py-8 space-y-8 max-w-6xl mx-auto">

        {/* ── Hero: Score + Body Heatmap ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {/* Score card */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl p-6 flex flex-col items-center gap-5"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
          >
            <ScoreRing score={score} size={172} />

            {/* Delta */}
            {delta !== null && (
              <div className="flex items-center gap-1.5 text-sm">
                {delta > 0 ? (
                  <><TrendingUp className="w-4 h-4 text-green-400" /><span style={{ color: "#22c55e" }}>+{delta} from last time</span></>
                ) : delta < 0 ? (
                  <><TrendingDown className="w-4 h-4 text-red-400" /><span style={{ color: "#ef4444" }}>{delta} from last time</span></>
                ) : (
                  <><Minus className="w-4 h-4" style={{ color: "rgba(255,255,255,0.3)" }} /><span style={{ color: "rgba(255,255,255,0.3)" }}>No change</span></>
                )}
              </div>
            )}

            {/* Meta */}
            <div className="flex items-center gap-4 text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {analyzeDate}
              </span>
              <span className="flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full" style={{ background: `${color}12`, color }}>
                <Leaf className="w-3 h-3" />
                {high.length > 0 ? `${high.length} high risk` : medium.length > 0 ? `${medium.length} medium risk` : "Looks good"}
              </span>
            </div>

            {/* Alerts */}
            {alerts.length > 0 && (
              <div className="w-full space-y-2">
                {(alerts as string[]).map((a, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 px-3 py-2.5 rounded-xl text-xs"
                    style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }}
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <span style={{ color: "rgba(255,255,255,0.75)" }}>{typeof a === "string" ? a : (a as any)?.message}</span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Body heatmap */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 }}
          >
            <BodyHeatmap predictions={preds} />
          </motion.div>
        </div>

        {/* ── Top concerns summary ── */}
        {topConcerns.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="rounded-xl px-4 py-3 flex items-center gap-3 flex-wrap"
            style={{ background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.15)" }}
          >
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <p className="text-sm" style={{ color: "rgba(255,255,255,0.7)" }}>
              <span style={{ color: "#ef4444", fontWeight: 600 }}>Focus karo: </span>
              {topConcerns.join(", ")}
            </p>
          </motion.div>
        )}

        {/* ── Deficiency Analysis ── */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>
            Deficiency Analysis — {preds.length} Nutrients
          </p>
          <div className="space-y-2">
            {sortedPreds.map((pred, i) => (
              <DeficiencyCard
                key={pred.deficiency}
                pred={pred}
                rec={recommendations.find((r) => r.deficiency === pred.deficiency)}
                expanded={expanded === pred.deficiency}
                onToggle={() => setExpanded(expanded === pred.deficiency ? null : pred.deficiency)}
                index={i}
              />
            ))}
          </div>
        </motion.div>

        {/* ── Generated Meal Plan from RECIPE_DB ── */}
        {mealPlan && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28 }}
          >
            {/* Header + daily totals */}
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.3)" }}>
                🍽️ Aaj ka Personalized Diet Plan
              </p>
              {mealPlan.targets && (
                <div className="flex gap-3 text-[10px] font-semibold" style={{ color: "rgba(255,255,255,0.35)" }}>
                  <span>{mealPlan.targets.kcal_total} kcal</span>
                  <span>P: {mealPlan.targets.protein_g}g</span>
                  <span>C: {mealPlan.targets.carb_g}g</span>
                  <span>F: {mealPlan.targets.fat_g}g</span>
                </div>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(["breakfast", "lunch", "snacks", "dinner"] as const).map((meal, i) => {
                const items = mealPlan[meal] as PortionedItem[];
                if (!items || items.length === 0) return null;
                const icons: Record<string, string> = { breakfast: "🌅", lunch: "☀️", snacks: "🍎", dinner: "🌙" };
                const labels: Record<string, string> = { breakfast: "Breakfast", lunch: "Lunch", snacks: "Snacks", dinner: "Dinner" };
                const mealKcal = items.reduce((s, r) => s + (r.kcal ?? 0), 0);
                return (
                  <motion.div
                    key={meal}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.28 + i * 0.06 }}
                    className="rounded-xl p-4"
                    style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-xs font-semibold" style={{ color: "rgba(255,255,255,0.5)" }}>
                        {icons[meal]} {labels[meal]}
                      </p>
                      <span className="text-[10px] font-semibold" style={{ color: "rgba(0,217,126,0.6)" }}>~{mealKcal} kcal</span>
                    </div>
                    <div className="space-y-2.5">
                      {items.map((r: PortionedItem, idx: number) => (
                        <div key={idx} className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.85)" }}>{r.name}</p>
                            {r.serving_desc && (
                              <p className="text-[11px] font-semibold mt-0.5" style={{ color: "#00d97e" }}>{r.serving_desc}</p>
                            )}
                            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                              {r.state ? `${r.state} · ` : ""}{r.category}{r.kcal ? ` · ${r.kcal} kcal` : ""}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ── Action bar ── */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="rounded-2xl p-5 flex flex-wrap items-center gap-3"
          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div className="flex items-center gap-2 text-sm mr-auto" style={{ color: "#22c55e" }}>
            <CheckCircle2 className="w-4 h-4" />
            Dashboard mein save ho gaya
          </div>

          <button
            onClick={() => setShowShare(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
            style={{ background: "rgba(129,140,248,0.08)", color: "#818cf8", border: "1px solid rgba(129,140,248,0.2)" }}
          >
            <Share2 className="w-4 h-4" /> Share
          </button>

          <button
            onClick={handlePDF}
            disabled={pdfLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
            style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.7)", border: "1px solid rgba(255,255,255,0.09)" }}
          >
            {pdfLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            PDF Report
          </button>

          <Link href="/dashboard">
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-black"
              style={{ background: "#00d97e" }}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
          </Link>

          <Link href="/analyze">
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
              style={{ background: "rgba(255,255,255,0.04)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Re-analyze
            </button>
          </Link>
        </motion.div>

        <p className="text-center text-xs pb-4" style={{ color: "rgba(255,255,255,0.2)" }}>
          Ye medical diagnosis nahi hai • Serious symptoms mein doctor se zaroor milein
        </p>
      </div>

      <AnimatePresence>
        {showShare && result && (
          <ShareCard
            analysis={{
              id: 0,
              timestamp: Date.now(),
              date: new Date(),
              score: result.balance_score?.overall_score ?? 0,
              score_label: computeScoreLabel(result.balance_score?.overall_score ?? 0),
              predictions: result.deficiency_predictions,
              high_risk: result.deficiency_predictions.filter((p) => p.risk_level === "high").map((p) => p.deficiency),
              medium_risk: result.deficiency_predictions.filter((p) => p.risk_level === "medium").map((p) => p.deficiency),
              diet_plan: result.diet_plan ?? {},
              recommendations: result.recommendations ?? [],
              alerts: result.alerts ?? [],
              symptoms_text: "",
              selected_symptoms: [],
              state: "",
              is_vegetarian: false,
              kitchen_items: [],
              medical_conditions: [],
            }}
            onClose={() => setShowShare(false)}
          />
        )}
      </AnimatePresence>
    </AppShell>
  );
}

// ── Deficiency Card ─────────────────────────────────────────

interface DCProps {
  pred: DeficiencyResult;
  rec?: Recommendation;
  expanded: boolean;
  onToggle: () => void;
  index: number;
  userState?: string;
}

function DeficiencyCard({ pred, rec, expanded, onToggle, index, userState }: DCProps) {
  const c = pred.risk_level === "high" ? "#ef4444" : pred.risk_level === "medium" ? "#f59e0b" : "#22c55e";
  const pct = Math.round(pred.probability * 100);
  const label = DEFICIENCY_LABELS[pred.deficiency] || pred.deficiency;
  const riskLabel = pred.risk_level === "high" ? "High Risk" : pred.risk_level === "medium" ? "Medium Risk" : "Low Risk";

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.025 }}
      className="rounded-xl overflow-hidden"
      style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${c}18` }}
    >
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer"
        onClick={onToggle}
        style={{ borderBottom: expanded ? `1px solid ${c}12` : "none" }}
      >
        <div className="w-1 self-stretch rounded-full shrink-0" style={{ background: c }} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.85)" }}>{label}</p>
          <p className="text-[10px] mt-0.5 font-semibold uppercase tracking-wide" style={{ color: `${c}99` }}>
            {riskLabel}
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-20 h-1.5 rounded-full overflow-hidden hidden sm:block" style={{ background: "rgba(255,255,255,0.06)" }}>
            <div className="h-full rounded-full" style={{ width: `${pct}%`, background: c }} />
          </div>
          <span className="text-sm font-bold w-10 text-right" style={{ color: c }}>{pct}%</span>
          <ChevronDown
            className="w-4 h-4 transition-transform duration-200"
            style={{ color: "rgba(255,255,255,0.25)", transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}
          />
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
          >
            <div className="px-4 py-4 ml-4 space-y-3">
              {rec?.foods && rec.foods.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
                    Khaane mein shamil karo
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {rec.foods.slice(0, 8).map((f, i) => (
                      <span
                        key={i}
                        className="text-xs px-2.5 py-1 rounded-full"
                        style={{ background: `${c}0d`, border: `1px solid ${c}22`, color: `${c}cc` }}
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {rec?.traditional_remedy && (
                <div
                  className="flex items-start gap-2 px-3 py-2.5 rounded-lg"
                  style={{ background: "rgba(0,217,126,0.06)", border: "1px solid rgba(0,217,126,0.12)" }}
                >
                  <span>🌿</span>
                  <p className="text-xs" style={{ color: "rgba(0,217,126,0.85)" }}>{rec.traditional_remedy}</p>
                </div>
              )}
              {!rec && (
                <p className="text-xs" style={{ color: "rgba(255,255,255,0.25)" }}>
                  Iske liye koi specific recommendation nahi mila
                </p>
              )}
              {(() => {
                const topRecipes = getRecipesForDeficiency(pred.deficiency, userState, 5, RECIPE_DB);
                if (topRecipes.length === 0) return null;
                return (
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
                      🍽️ IFCT2017 Recipes{userState ? ` (${userState})` : ""}
                    </p>
                    <div className="space-y-1.5">
                      {topRecipes.map((r) => (
                        <div
                          key={r.id}
                          className="flex items-center justify-between px-3 py-2 rounded-lg"
                          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
                        >
                          <div>
                            <p className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.8)" }}>{r.name}</p>
                            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                              {r.state} · {r.category} · {r.serving}
                            </p>
                          </div>
                          <span
                            className="text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 ml-3"
                            style={{ background: `${c}12`, color: `${c}cc` }}
                          >
                            {(r.nutrients[pred.deficiency] ?? 0).toFixed(1)} {NUTRIENT_UNITS[pred.deficiency] ?? ""}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Meal Card ───────────────────────────────────────────────

function MealCard({ meal, foods, delay }: { meal: string; foods: string[]; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="rounded-xl p-4"
      style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
    >
      <p className="text-xs font-semibold uppercase tracking-widest mb-2.5" style={{ color: "rgba(255,255,255,0.4)" }}>
        {MEAL_ICON[meal] || "🍽️"} {MEAL_LABEL[meal] || meal}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {(Array.isArray(foods) ? foods : []).map((f, i) => (
          <span
            key={i}
            className="text-xs px-2.5 py-1 rounded-full"
            style={{
              background: "rgba(0,217,126,0.07)",
              border: "1px solid rgba(0,217,126,0.12)",
              color: "rgba(0,217,126,0.8)",
            }}
          >
            {f}
          </span>
        ))}
      </div>
    </motion.div>
  );
}
