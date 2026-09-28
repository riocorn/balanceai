"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  Leaf, Heart,
  Download, RefreshCw, LayoutDashboard, Share2, CheckCircle2, Loader2,
} from "lucide-react";
import { DEFICIENCY_LABELS, type AnalysisResult } from "@/lib/api";
import { NUTRIENT_UNITS, NUTRIENT_DAILY } from "@/lib/food-db";
import { getAllAnalyses, computeScoreLabel } from "@/lib/db";
import type { FusionResult, NutrientResult } from "@/lib/nutrient-fusion-engine";
import { generatePDF } from "@/lib/pdf";
import ShareCard from "@/components/app/ShareCard";
import Confetti from "@/components/app/Confetti";
import type { MealPlan, PortionedItem } from "@/lib/diet-engine";

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<(AnalysisResult & { imageResults?: Record<string, unknown> }) | null>(null);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [fusion, setFusion] = useState<FusionResult | null>(null);
  const [confetti, setConfetti] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const raw = sessionStorage.getItem("balanceai_result");
    if (!raw) { router.push("/analyze"); return; }
    try {
      const parsed = JSON.parse(raw);
      setResult(parsed);
      const sc = parsed.balance_score?.overall_score ?? 0;
      const mpRaw = sessionStorage.getItem("balanceai_meal_plan");
      if (mpRaw) { try { setMealPlan(JSON.parse(mpRaw)); } catch { } }
      const frRaw = sessionStorage.getItem("balanceai_fusion");
      if (frRaw) { try { setFusion(JSON.parse(frRaw)); } catch { } }
      // Show "Hold on..." for 2s then reveal cards — mirrors balance.it behavior
      setTimeout(() => {
        setProcessing(false);
        if (sc >= 70) setConfetti(true);
      }, 2000);
    } catch { router.push("/analyze"); }
  }, [router]);

  const handlePDF = async () => {
    if (!result) return;
    setPdfLoading(true);
    try {
      await generatePDF({
        score: result.balance_score?.overall_score ?? 0,
        score_label: computeScoreLabel(result.balance_score?.overall_score ?? 0),
        predictions: result.deficiency_predictions ?? [],
        diet_plan: result.diet_plan ?? {},
        recommendations: result.recommendations ?? [],
        alerts: (result.alerts ?? []) as string[],
        date: new Date().toLocaleDateString("en-IN"),
      });
    } finally { setPdfLoading(false); }
  };

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#f7f5ef" }}>
        <div className="w-10 h-10 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: "#1d5c3d", borderTopColor: "transparent" }} />
      </div>
    );
  }

  const { deficiency_predictions: preds = [] } = result;

  const allMealItems: PortionedItem[] = mealPlan ? [
    ...(mealPlan.breakfast ?? []),
    ...(mealPlan.lunch ?? []),
    ...(mealPlan.snacks ?? []),
    ...(mealPlan.dinner ?? []),
  ] : [];

  const mealSections = mealPlan ? (["breakfast", "lunch", "snacks", "dinner"] as const).filter(
    (m) => (mealPlan[m] as PortionedItem[])?.length > 0
  ) : [];

  // 1 combination = full day (breakfast + lunch + dinner)
  const totalKcal = Math.round(allMealItems.reduce((s, r) => s + (r.kcal ?? 0), 0));

  // Compute nutrient totals across all meals
  const mealTotals: Record<string, number> = {};
  allMealItems.forEach((item) => {
    Object.entries(item.nutrients_total ?? {}).forEach(([k, v]) => {
      mealTotals[k] = (mealTotals[k] ?? 0) + (v as number);
    });
  });

  // Count nutrients under 90% of daily requirement = deficiency gaps (shown red like balance.it)
  const deficiencyCount = Object.keys(NUTRIENT_DAILY).filter((key) => {
    const amount = mealTotals[key] ?? 0;
    const req = mealPlan?.targets?.rda?.[key] ?? NUTRIENT_DAILY[key] ?? 0;
    return req > 0 && amount < req * 0.9;
  }).length;

  const ingredientLine =
    allMealItems.slice(0, 3).map((it) => it.name).join(" | ") +
    (allMealItems.length > 3 ? "... combo" : " combo");

  return (
    <div className="min-h-screen" style={{ background: "#f2efe8" }}>
      {confetti && <Confetti />}

      {/* ── NAV ── */}
      <nav style={{ background: "#ffffff", borderBottom: "1px solid #e4e7e2" }}>
        <div className="max-w-5xl mx-auto px-5 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Leaf className="w-5 h-5" style={{ color: "#1d5c3d" }} />
            <span className="font-bold text-base" style={{ color: "#1d5c3d" }}>BalanceAI</span>
          </Link>
          <div className="flex items-center gap-6 text-sm font-medium" style={{ color: "#3d5249" }}>
            <Link href="/dashboard" className="hover:text-[#1d5c3d] transition-colors">Dashboard</Link>
            <Link href="/analyze" className="hover:text-[#1d5c3d] transition-colors">Analyse</Link>
          </div>
        </div>
      </nav>

      {/* ── HERO — balance.it exact layout ── */}
      <div style={{ background: "#ffffff" }}>
        <div className="max-w-3xl mx-auto px-5 text-center" style={{ paddingTop: "4rem", paddingBottom: "3rem" }}>
          <AnimatePresence mode="wait">
            {processing ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <h1 className="font-bold leading-tight mb-8" style={{ color: "#1d5c3d", fontSize: "clamp(2.2rem,5.5vw,3.5rem)" }}>
                  Hold on, we are trying<br />some things for you…
                </h1>
                <div className="flex justify-center">
                  <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: "#1d5c3d", borderTopColor: "transparent" }} />
                </div>
              </motion.div>
            ) : (
              <motion.div key="ready" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <h1 className="font-bold leading-tight mb-6" style={{ color: "#1d5c3d", fontSize: "clamp(2.2rem,5.5vw,3.5rem)" }}>
                  1 custom meal plan, created just for you
                </h1>
                <p className="text-sm mb-8 mx-auto" style={{ color: "#3d5249", maxWidth: "560px" }}>
                  Here are a few options we think you&apos;ll love. Feel free to adjust and swap ingredients to get it just right.
                </p>
                <div className="flex items-center justify-center gap-4 flex-wrap">
                  <Link href="/analyze">
                    <button
                      className="px-8 py-3 text-sm font-bold uppercase tracking-widest transition-all hover:bg-[#1d5c3d] hover:text-white"
                      style={{ border: "2px solid #1d5c3d", color: "#1d5c3d", background: "transparent", borderRadius: "6px" }}
                    >
                      Change Ingredients
                    </button>
                  </Link>
                  <button
                    className="px-6 py-3 text-sm font-medium"
                    style={{ border: "1.5px solid #1d5c3d", color: "#1d5c3d", background: "transparent", borderRadius: "6px" }}
                  >
                    <span className="font-semibold">Filter:</span> Show meals with any nutrition goal (1 plan)
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ── COMBINATION CARDS — only after processing done ── */}
      {!processing && <div style={{ background: "#ebebeb" }}>
      <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">
        {allMealItems.length === 0 && (
          <p className="text-center py-16 text-sm" style={{ color: "#9aa5ae" }}>
            No meal plan generated. Go back and select ingredients.
          </p>
        )}
        {allMealItems.length > 0 && (
          <CombinationCard
            number={1}
            ingredientLine={ingredientLine}
            mealSections={mealSections}
            mealPlan={mealPlan!}
            totalItems={allMealItems.length}
            kcal={totalKcal}
            deficiencyCount={deficiencyCount}
            delay={0}
          />
        )}

        {/* Bottom buttons — CHANGE INGREDIENTS + SHOW MORE RECIPES like balance.it */}
        <div className="flex items-center justify-center gap-5 pt-4 pb-6 flex-wrap">
          <Link href="/analyze">
            <button
              className="px-10 py-3 text-sm font-bold uppercase tracking-widest transition-all hover:bg-[#1d5c3d] hover:text-white"
              style={{ border: "2px solid #1d5c3d", color: "#1d5c3d", background: "transparent", borderRadius: "6px" }}
            >
              Change Ingredients
            </button>
          </Link>
          <button
            className="px-10 py-3 text-sm font-bold uppercase tracking-widest"
            style={{ background: "#e8b96b", color: "#1d5c3d", borderRadius: "6px", border: "none" }}
          >
            Show More Recipes
          </button>
        </div>
      </div>
      </div>}

      {/* ── 5-LAYER FUSION: 25 Nutrient Status Panel ── */}
      {!processing && fusion && <FusionStatusPanel fusion={fusion} />}

      {/* ── NUTRIENT PROFILE ── */}
      {!processing && mealPlan && <NutrientProfile mealPlan={mealPlan} />}

      {/* ── ACTION BAR ── */}
      <div className="max-w-3xl mx-auto px-4 pb-6">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="rounded-2xl p-5 flex flex-wrap items-center gap-3"
          style={{ background: "#ffffff", border: "1px solid #e4e7e2" }}
        >
          <div className="flex items-center gap-2 text-sm mr-auto" style={{ color: "#16a34a" }}>
            <CheckCircle2 className="w-4 h-4" />
            Dashboard mein save ho gaya
          </div>

          <button
            onClick={() => setShowShare(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
            style={{ background: "rgba(129,140,248,0.08)", color: "#818cf8", border: "1px solid rgba(129,140,248,0.2)" }}
          >
            <Share2 className="w-4 h-4" /> Share
          </button>

          <button
            onClick={handlePDF}
            disabled={pdfLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
            style={{ background: "#e9ece9", color: "#5a6571", border: "1px solid rgba(255,255,255,0.09)" }}
          >
            {pdfLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            PDF Report
          </button>

          <Link href="/dashboard">
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
              style={{ background: "#1d5c3d", color: "#ffffff" }}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
          </Link>

          <Link href="/analyze">
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
              style={{ background: "#f8f9f8", color: "#5a6571", border: "1px solid #e4e7e2" }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Re-analyze
            </button>
          </Link>
        </motion.div>
      </div>

      <p className="text-center text-xs pb-8" style={{ color: "#9aa5ae" }}>
        Ye medical diagnosis nahi hai • Serious symptoms mein doctor se zaroor milein
      </p>

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
    </div>
  );
}

// ── Combination Card — exact balance.it layout ──────────────────────────────

function CombinationCard({
  number, ingredientLine, mealSections, mealPlan, totalItems, kcal, deficiencyCount, delay,
}: {
  number: number; ingredientLine: string;
  mealSections: readonly ("breakfast" | "lunch" | "snacks" | "dinner")[];
  mealPlan: MealPlan;
  totalItems: number; kcal: number; deficiencyCount: number; delay: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const [favorited, setFavorited] = useState(false);
  const mealLabel: Record<string, string> = { breakfast: "Breakfast", lunch: "Lunch", snacks: "Snacks", dinner: "Dinner" };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="rounded-2xl overflow-hidden"
      style={{ background: "#ffffff", border: "1px solid #e4e7e2", boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}
    >
      <div className="px-6 pt-6 pb-5">

        {/* Header: badge + title + heart */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-3 min-w-0">
            <span
              className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold shrink-0"
              style={{ border: "1.5px solid #d0d5cf", color: "#5a6571" }}
            >
              {number}
            </span>
            <h3 className="font-bold text-lg leading-snug" style={{ color: "#1a1a1a" }}>
              Recommended Alternative Combination {number}
            </h3>
          </div>
          <button onClick={() => setFavorited((f) => !f)} className="ml-3 shrink-0 pt-0.5" aria-label="Save">
            <Heart
              className="w-6 h-6 transition-colors"
              style={favorited ? { fill: "#1d5c3d", color: "#1d5c3d" } : { color: "#c8d0cb" }}
            />
          </button>
        </div>

        {/* Subtitle — centered like balance.it */}
        <p className="text-sm text-center mb-5" style={{ color: "#5a6571" }}>
          <strong>This recipe uses:</strong> {ingredientLine}
        </p>

        {/* Divider */}
        <div style={{ borderTop: "1px solid #e4e7e2", marginBottom: "1.25rem" }} />

        {/* 3-column stats — exact balance.it text + proportions */}
        <div className="grid grid-cols-3 text-center" style={{ borderBottom: "1px solid #e4e7e2", paddingBottom: "1.25rem" }}>

          {/* Col 1 */}
          <div className="px-3" style={{ borderRight: "1px solid #e4e7e2" }}>
            <p className="text-sm mb-2" style={{ color: "#8a9a8e" }}>requires</p>
            <p className="font-bold" style={{ color: "#1a1a1a", fontSize: "2.5rem", lineHeight: 1 }}>
              {totalItems}
            </p>
            <p className="text-sm mt-1 mb-3" style={{ color: "#5a6571" }}>daily food items</p>
            <button className="text-[11px] font-semibold uppercase tracking-wide underline" style={{ color: "#1d5c3d" }}>
              LEARN MORE
            </button>
          </div>

          {/* Col 2 */}
          <div className="px-3" style={{ borderRight: "1px solid #e4e7e2" }}>
            <p className="text-sm mb-2 leading-tight" style={{ color: "#8a9a8e" }}>
              BalanceAI daily<br />caloric target
            </p>
            <p className="font-bold" style={{ color: "#1d5c3d", fontSize: "2.5rem", lineHeight: 1 }}>
              {kcal}<span style={{ fontSize: "1.1rem" }}>/day</span>
            </p>
            <p className="text-sm mt-1 mb-3" style={{ color: "#5a6571" }}>for your daily meals</p>
            <button className="text-[11px] font-semibold uppercase tracking-wide underline" style={{ color: "#1d5c3d" }}>
              ADJUST RECIPE
            </button>
          </div>

          {/* Col 3 */}
          <div className="px-3">
            <p className="text-sm mb-2" style={{ color: "#8a9a8e" }}>recipe would have</p>
            <p className="font-bold" style={{ color: "#ef4444", fontSize: "2.5rem", lineHeight: 1 }}>
              {deficiencyCount}
            </p>
            <p className="text-sm mt-1 mb-3" style={{ color: "#5a6571" }}>
              nutrient gaps<br />in this plan
            </p>
            <button className="text-[11px] font-semibold uppercase tracking-wide underline" style={{ color: "#1d5c3d" }}>
              SEE NUTRITIONAL PROFILE
            </button>
          </div>
        </div>

        {/* Action buttons — same proportions as balance.it */}
        <div className="flex gap-3 mt-4">
          <button
            onClick={() => setExpanded((e) => !e)}
            className="py-3 text-sm font-bold transition-colors"
            style={{ flex: "3", background: "#1d5c3d", color: "#ffffff", borderRadius: "6px" }}
          >
            {expanded ? "HIDE RECIPE" : "VIEW RECIPE"}
          </button>
          <button
            className="py-3 text-sm font-bold transition-colors"
            style={{ flex: "2", background: "transparent", color: "#1d5c3d", border: "1.5px solid #1d5c3d", borderRadius: "6px" }}
          >
            SEE NUTRIENTS
          </button>
        </div>
      </div>

      {/* Expanded: breakfast + lunch + dinner sections */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            style={{ overflow: "hidden" }}
          >
            <div className="px-6 pb-6" style={{ background: "#f8f9f6", borderTop: "1px solid #e4e7e2" }}>
              {mealSections.map((meal) => {
                const items = (mealPlan[meal] as PortionedItem[]) ?? [];
                return (
                  <div key={meal} className="pt-4">
                    <p className="text-xs font-bold uppercase tracking-widest pb-3" style={{ color: "#8a9a8e" }}>
                      {mealLabel[meal]}
                    </p>
                    <div className="space-y-3">
                      {items.map((r, idx) => (
                        <div key={idx} className="flex items-start justify-between gap-3 text-sm">
                          <span style={{ color: "#1a1a1a" }}>{r.name}</span>
                          <span className="font-bold text-right shrink-0" style={{ color: "#1d5c3d" }}>
                            {r.serving_desc ?? `${r.grams}g`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Nutrient Profile ─────────────────────────────────────────────────────────

function NutrientProfile({ mealPlan }: { mealPlan: MealPlan }) {
  const targets = mealPlan.targets;
  const allItems: PortionedItem[] = [
    ...(mealPlan.breakfast ?? []), ...(mealPlan.lunch ?? []),
    ...(mealPlan.snacks ?? []), ...(mealPlan.dinner ?? []),
  ];

  const totals: Record<string, number> = {};
  allItems.forEach((item) => {
    Object.entries(item.nutrients_total ?? {}).forEach(([k, v]) => {
      totals[k] = (totals[k] ?? 0) + (v as number);
    });
  });

  const proteinKcal = (targets?.protein_g ?? 0) * 4;
  const fatKcal = (targets?.fat_g ?? 0) * 9;
  const carbKcal = (targets?.carb_g ?? 0) * 4;
  const totalMacroKcal = proteinKcal + fatKcal + carbKcal || 1;
  const proteinPct = Math.round((proteinKcal / totalMacroKcal) * 100);
  const fatPct = Math.round((fatKcal / totalMacroKcal) * 100);
  const carbPct = Math.max(0, 100 - proteinPct - fatPct);

  const nutrientRows = Object.keys(DEFICIENCY_LABELS)
    .map((key) => {
      const amount = totals[key] ?? 0;
      const requirement = targets?.rda?.[key] ?? NUTRIENT_DAILY[key] ?? 0;
      if (requirement <= 0) return null;
      const pct = Math.round((amount / requirement) * 100);
      return { key, amount, requirement, pct };
    })
    .filter((r): r is { key: string; amount: number; requirement: number; pct: number } => r !== null)
    .sort((a, b) => a.pct - b.pct);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.32 }}
      className="max-w-3xl mx-auto px-4 pb-6"
    >
      <div className="rounded-2xl p-5" style={{ background: "#ffffff", border: "1px solid #e4e7e2" }}>
        <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "#9aa5ae" }}>
          Nutrient Profile
        </p>

        <div className="mb-6">
          <div className="flex items-center gap-5 mb-2 flex-wrap text-xs font-medium">
            <span className="flex items-center gap-1.5" style={{ color: "#1a1a1a" }}>
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: "#1d5c3d" }} />
              Protein calories: {proteinPct}%
            </span>
            <span className="flex items-center gap-1.5" style={{ color: "#1a1a1a" }}>
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: "#d4a043" }} />
              Fat calories: {fatPct}%
            </span>
            <span className="flex items-center gap-1.5" style={{ color: "#1a1a1a" }}>
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: "#c7c7c7" }} />
              Carbohydrate calories: {carbPct}%
            </span>
          </div>
          <div className="w-full h-3 rounded-full overflow-hidden flex" style={{ background: "#e9ece9" }}>
            <div style={{ width: `${proteinPct}%`, background: "#1d5c3d" }} />
            <div style={{ width: `${fatPct}%`, background: "#d4a043" }} />
            <div style={{ width: `${carbPct}%`, background: "#c7c7c7" }} />
          </div>
          <p className="text-xs mt-3" style={{ color: "#9aa5ae" }}>
            Total calories: <strong style={{ color: "#1a1a1a" }}>{targets?.kcal_total ?? 0} kcal/day</strong>
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: "1px solid #e4e7e2" }}>
                <th className="text-left py-2 pr-3 font-semibold" style={{ color: "#5a6571" }}>Nutrient</th>
                <th className="text-right py-2 pr-3 font-semibold" style={{ color: "#5a6571" }}>Requirement</th>
                <th className="text-right py-2 pr-3 font-semibold" style={{ color: "#5a6571" }}>Amount</th>
                <th className="text-right py-2 font-semibold" style={{ color: "#5a6571" }}>% of Requirement</th>
              </tr>
            </thead>
            <tbody>
              {nutrientRows.map((row) => {
                const unit = NUTRIENT_UNITS[row.key] ?? "";
                const color = row.pct >= 100 ? "#16a34a" : row.pct >= 60 ? "#f59e0b" : "#ef4444";
                return (
                  <tr key={row.key} style={{ borderBottom: "1px solid #f1f2f0" }}>
                    <td className="py-2 pr-3" style={{ color: "#1a1a1a" }}>{DEFICIENCY_LABELS[row.key]}</td>
                    <td className="py-2 pr-3 text-right" style={{ color: "#5a6571" }}>
                      {row.requirement.toFixed(row.requirement < 10 ? 2 : 0)} {unit}
                    </td>
                    <td className="py-2 pr-3 text-right" style={{ color: "#5a6571" }}>
                      {row.amount.toFixed(row.amount < 10 ? 2 : 0)} {unit}
                    </td>
                    <td className="py-2 text-right font-bold" style={{ color }}>{row.pct}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}

// ── FusionStatusPanel — 25-Nutrient AI Status Board ──────────────────────────

const STATUS_CONFIG = {
  deficient: { label: "DEFICIENT", bg: "#fef2f2", border: "#fca5a5", text: "#dc2626", dot: "#ef4444" },
  excess:    { label: "EXCESS",    bg: "#fffbeb", border: "#fcd34d", text: "#b45309", dot: "#f59e0b" },
  adequate:  { label: "ADEQUATE",  bg: "#f0fdf4", border: "#86efac", text: "#16a34a", dot: "#22c55e" },
  unknown:   { label: "UNKNOWN",   bg: "#f9fafb", border: "#e5e7eb", text: "#9ca3af", dot: "#d1d5db" },
} as const;

const SEVERITY_BADGE: Record<string, string> = {
  severe:   "SEVERE",
  moderate: "MOD",
  mild:     "MILD",
  none:     "",
};

function FusionStatusPanel({ fusion }: { fusion: FusionResult }) {
  const [tab, setTab] = useState<"all" | "deficient" | "excess" | "adequate">("deficient");
  const [expanded, setExpanded] = useState<string | null>(null);

  const tabs = [
    { id: "deficient" as const, label: `Deficient (${fusion.deficient.length})`, color: "#dc2626" },
    { id: "excess"    as const, label: `Excess (${fusion.excess.length})`,       color: "#b45309" },
    { id: "adequate"  as const, label: `Adequate (${fusion.adequate.length})`,   color: "#16a34a" },
    { id: "all"       as const, label: `All 25`,                                  color: "#1d5c3d" },
  ];

  const rows: NutrientResult[] =
    tab === "all"       ? fusion.nutrients :
    tab === "deficient" ? fusion.deficient :
    tab === "excess"    ? fusion.excess    :
    fusion.adequate;

  const layerLabel: Record<string, string> = {
    blood:    "Blood Test",
    ml:       "XGBoost ML",
    symptoms: "Symptoms",
    food_log: "Food Log",
    history:  "History",
    visual:   "Visual",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.18 }}
      className="max-w-3xl mx-auto px-4 pb-6"
    >
      <div className="rounded-2xl overflow-hidden" style={{ background: "#ffffff", border: "1px solid #e4e7e2" }}>

        {/* Header */}
        <div className="px-5 pt-5 pb-4" style={{ borderBottom: "1px solid #e4e7e2" }}>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest mb-0.5" style={{ color: "#9aa5ae" }}>
                5-Layer AI Fusion · 25 Nutrients
              </p>
              <h2 className="text-base font-bold" style={{ color: "#1a1a1a" }}>
                Complete Nutrition Status Report
              </h2>
            </div>
            <div className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full" style={{ background: "#f0fdf4", border: "1px solid #86efac" }}>
              <span className="font-semibold" style={{ color: "#16a34a" }}>
                {Math.round(fusion.dataCompleteness * 100)}%
              </span>
              <span style={{ color: "#5a6571" }}>data coverage</span>
            </div>
          </div>

          {/* Layer coverage chips */}
          <div className="flex flex-wrap gap-1.5 mt-3">
            {Object.entries(fusion.layerCoverage).map(([layer, has]) => (
              <span
                key={layer}
                className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                style={{
                  background: has ? "#f0fdf4" : "#f3f4f6",
                  color:      has ? "#16a34a" : "#9ca3af",
                  border:     `1px solid ${has ? "#86efac" : "#e5e7eb"}`,
                }}
              >
                {layerLabel[layer] ?? layer} {has ? "✓" : "—"}
              </span>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b" style={{ borderColor: "#e4e7e2" }}>
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className="flex-1 py-2.5 text-xs font-semibold transition-colors"
              style={{
                color:       tab === t.id ? t.color : "#9aa5ae",
                borderBottom: tab === t.id ? `2px solid ${t.color}` : "2px solid transparent",
                background:  "transparent",
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Nutrient rows */}
        <div className="divide-y divide-[#f1f2f0]">
          {rows.length === 0 && (
            <p className="text-center py-8 text-sm" style={{ color: "#9aa5ae" }}>
              No nutrients in this category
            </p>
          )}
          {rows.map((r) => {
            const cfg = STATUS_CONFIG[r.status];
            const isOpen = expanded === r.nutrient;
            const sevBadge = SEVERITY_BADGE[r.severity];
            return (
              <div key={r.nutrient} style={{ borderBottom: "1px solid #f1f2f0" }}>
                <button
                  onClick={() => setExpanded(isOpen ? null : r.nutrient)}
                  className="w-full px-5 py-3 flex items-center gap-3 text-left"
                >
                  {/* Status dot */}
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: cfg.dot }} />

                  {/* Name */}
                  <span className="flex-1 text-sm font-medium" style={{ color: "#1a1a1a" }}>
                    {r.label}
                    <span className="ml-1 text-xs font-normal" style={{ color: "#9aa5ae" }}>{r.unit}</span>
                  </span>

                  {/* Severity badge (only for deficient) */}
                  {sevBadge && (
                    <span
                      className="text-[9px] font-bold px-1.5 py-0.5 rounded"
                      style={{ background: "#fef2f2", color: "#dc2626", border: "1px solid #fca5a5" }}
                    >
                      {sevBadge}
                    </span>
                  )}

                  {/* RDA % bar (food log data) */}
                  {r.rda_pct !== undefined && (
                    <div className="w-16 shrink-0">
                      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "#e9ece9" }}>
                        <div
                          style={{
                            width: `${Math.min(100, r.rda_pct)}%`,
                            height: "100%",
                            background: r.rda_pct >= 90 ? "#22c55e" : r.rda_pct >= 60 ? "#f59e0b" : "#ef4444",
                          }}
                        />
                      </div>
                      <p className="text-[9px] text-right mt-0.5" style={{ color: "#9aa5ae" }}>{Math.round(r.rda_pct)}% RDA</p>
                    </div>
                  )}

                  {/* Status pill */}
                  <span
                    className="text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0"
                    style={{ background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}` }}
                  >
                    {cfg.label}
                  </span>

                  {/* Confidence */}
                  <span className="text-[10px] w-8 text-right shrink-0" style={{ color: "#9aa5ae" }}>
                    {r.evidence.length > 0 ? `${Math.round(r.confidence * 100)}%` : "—"}
                  </span>

                  {/* Chevron */}
                  {r.evidence.length > 0 && (
                    <span className="text-xs shrink-0" style={{ color: "#9aa5ae" }}>{isOpen ? "▲" : "▼"}</span>
                  )}
                </button>

                {/* Evidence detail */}
                {isOpen && r.evidence.length > 0 && (
                  <div className="px-5 pb-3 space-y-1">
                    {r.evidence.map((ev, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs">
                        <span
                          className="shrink-0 mt-0.5 text-[9px] font-bold px-1.5 py-0.5 rounded"
                          style={{ background: "#f0fdf4", color: "#16a34a", border: "1px solid #86efac" }}
                        >
                          {layerLabel[ev.layer] ?? ev.layer}
                        </span>
                        <span style={{ color: "#5a6571" }}>{ev.detail}</span>
                        <span className="ml-auto shrink-0 font-semibold" style={{ color: ev.signal > 0 ? "#dc2626" : ev.signal < 0 ? "#b45309" : "#16a34a" }}>
                          {ev.signal > 0 ? "↑" : ev.signal < 0 ? "↓" : "="}{Math.abs(ev.signal).toFixed(2)}
                        </span>
                      </div>
                    ))}
                    <div className="flex gap-3 pt-1">
                      <span className="text-[10px]" style={{ color: "#9aa5ae" }}>
                        Fusion score: <strong style={{ color: "#1a1a1a" }}>{r.score.toFixed(3)}</strong>
                      </span>
                      <span className="text-[10px]" style={{ color: "#9aa5ae" }}>
                        Confidence: <strong style={{ color: "#1a1a1a" }}>{Math.round(r.confidence * 100)}%</strong>
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer note */}
        <div className="px-5 py-3" style={{ borderTop: "1px solid #e4e7e2", background: "#fafbfa" }}>
          <p className="text-[10px]" style={{ color: "#9aa5ae" }}>
            AI fusion from 6 layers: Blood (0.90) · XGBoost ML (0.70) · Symptoms (0.60) · Food Log (0.55) · 3-month History (0.40) · Visual (0.25) · ICMR-NIN RDA reference
          </p>
        </div>
      </div>
    </motion.div>
  );
}
