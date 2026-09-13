"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Plus, X, BookOpen, Flame } from "lucide-react";
import AppShell from "@/components/app/AppShell";
import { getAllAnalyses, type AnalysisEntry } from "@/lib/db";
import {
  FOOD_DB, searchFoods, NUTRIENT_DAILY, NUTRIENT_UNITS,
  type FoodItem,
} from "@/lib/food-db";
import { RECIPE_DB } from "@/lib/recipe-db";
import { DEFICIENCY_LABELS } from "@/lib/api";

interface LogEntry {
  food: FoodItem;
  qty: number;
}

const FOCUS_NUTRIENTS = ["iron", "vitamin_b12", "vitamin_d", "calcium", "zinc", "omega3", "folate", "magnesium"];

const MEAL_SLOTS = ["Breakfast", "Lunch", "Snacks", "Dinner"];
const MEAL_EMOJIS: Record<string, string> = { Breakfast: "🌅", Lunch: "☀️", Snacks: "🍎", Dinner: "🌙" };

function NutrientBar({
  nutrient, covered, daily, isDeficient,
}: { nutrient: string; covered: number; daily: number; isDeficient: boolean }) {
  const pct = Math.min((covered / daily) * 100, 100);
  const color = isDeficient
    ? (pct < 33 ? "#ef4444" : pct < 66 ? "#f59e0b" : "#22c55e")
    : (pct < 33 ? "rgba(255,255,255,0.2)" : "#22c55e");

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-medium" style={{ color: isDeficient ? "rgba(255,255,255,0.75)" : "rgba(255,255,255,0.45)" }}>
          {DEFICIENCY_LABELS[nutrient] || nutrient}
          {isDeficient && <span className="ml-1 text-[9px] font-bold" style={{ color: "#ef4444" }}>● risk</span>}
        </span>
        <span className="text-[10px] font-bold" style={{ color }}>
          {covered.toFixed(1)}/{daily}{NUTRIENT_UNITS[nutrient]}
        </span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4 }}
        />
      </div>
    </div>
  );
}

export default function DiaryPage() {
  const [analysis, setAnalysis] = useState<AnalysisEntry | null>(null);
  const [logs, setLogs] = useState<Record<string, LogEntry[]>>({ Breakfast: [], Lunch: [], Snacks: [], Dinner: [] });
  const [activeMeal, setActiveMeal] = useState("Breakfast");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<FoodItem[]>([]);
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    getAllAnalyses().then((a) => setAnalysis(a[0] ?? null));
  }, []);

  useEffect(() => {
    if (query.length > 0) setResults(searchFoods(query, RECIPE_DB));
    else setResults([]);
  }, [query]);

  const addFood = (food: FoodItem) => {
    setLogs((prev) => ({
      ...prev,
      [activeMeal]: [...(prev[activeMeal] || []), { food, qty: 1 }],
    }));
    setQuery("");
    setResults([]);
    setShowSearch(false);
  };

  const removeFood = (meal: string, idx: number) => {
    setLogs((prev) => ({ ...prev, [meal]: prev[meal].filter((_, i) => i !== idx) }));
  };

  const allEntries = Object.values(logs).flat();

  const totals = useMemo(() => {
    const t: Record<string, number> = {};
    allEntries.forEach(({ food, qty }) => {
      Object.entries(food.nutrients).forEach(([k, v]) => {
        t[k] = (t[k] ?? 0) + (v ?? 0) * qty;
      });
    });
    return t;
  }, [allEntries]);

  const deficientNutrients = new Set([
    ...(analysis?.high_risk ?? []),
    ...(analysis?.medium_risk ?? []),
  ]);

  const focusNutrients = FOCUS_NUTRIENTS.filter(
    (n) => deficientNutrients.has(n) || allEntries.length > 0
  ).slice(0, 6);

  const coveragePct = focusNutrients.length > 0
    ? Math.round(
        focusNutrients.reduce((sum, n) => sum + Math.min(((totals[n] ?? 0) / (NUTRIENT_DAILY[n] ?? 1)) * 100, 100), 0) /
        focusNutrients.length
      )
    : 0;

  return (
    <AppShell>
      <div className="px-4 sm:px-8 py-8 max-w-3xl mx-auto space-y-6">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <p className="text-xs font-semibold uppercase tracking-widest mb-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>
            Today
          </p>
          <div className="flex items-center justify-between">
            <h1 className="font-display font-bold text-2xl" style={{ color: "rgba(255,255,255,0.9)" }}>
              Food Diary
            </h1>
            <BookOpen className="w-5 h-5" style={{ color: "rgba(255,255,255,0.25)" }} />
          </div>
        </motion.div>

        {/* Coverage ring */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-2xl p-5 flex items-center gap-5"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div className="relative w-20 h-20 shrink-0">
            <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
              <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              <circle
                cx="40" cy="40" r="32" fill="none"
                stroke={coveragePct > 60 ? "#00d97e" : coveragePct > 30 ? "#f59e0b" : "#ef4444"}
                strokeWidth="8" strokeLinecap="round"
                strokeDasharray={`${coveragePct * 2.01} 201`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-lg font-black font-display" style={{ color: coveragePct > 60 ? "#00d97e" : "#f59e0b" }}>
                {coveragePct}%
              </span>
            </div>
          </div>
          <div>
            <p className="text-sm font-bold mb-0.5" style={{ color: "rgba(255,255,255,0.85)" }}>
              Daily Nutrient Coverage
            </p>
            <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
              {allEntries.length === 0
                ? "Khaana log karo — gap track hoga"
                : coveragePct < 40 ? "Aur khaana chahiye — gap hai"
                : coveragePct < 70 ? "Acha jaa raha hai — thoda aur"
                : "Excellent! Aaj ka nutrition great hai"}
            </p>
            {analysis && deficientNutrients.size > 0 && (
              <p className="text-[10px] mt-1" style={{ color: "rgba(255,255,255,0.25)" }}>
                Focus: {[...deficientNutrients].slice(0, 3).map((d) => DEFICIENCY_LABELS[d] || d).join(", ")}
              </p>
            )}
          </div>
        </motion.div>

        {/* Nutrient bars */}
        {focusNutrients.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-2xl p-5"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
          >
            <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "rgba(255,255,255,0.3)" }}>
              Today's Nutrient Status
            </p>
            <div className="space-y-3">
              {focusNutrients.map((n) => (
                <NutrientBar
                  key={n}
                  nutrient={n}
                  covered={totals[n] ?? 0}
                  daily={NUTRIENT_DAILY[n]}
                  isDeficient={deficientNutrients.has(n)}
                />
              ))}
            </div>
          </motion.div>
        )}

        {/* Meal slots */}
        <div className="space-y-4">
          {MEAL_SLOTS.map((meal) => (
            <motion.div
              key={meal}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="rounded-2xl p-4"
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.75)" }}>
                  {MEAL_EMOJIS[meal]} {meal}
                </p>
                <button
                  onClick={() => { setActiveMeal(meal); setShowSearch(true); inputFocus(); }}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium"
                  style={{ background: "rgba(0,217,126,0.08)", border: "1px solid rgba(0,217,126,0.15)", color: "#00d97e" }}
                >
                  <Plus className="w-3 h-3" /> Add
                </button>
              </div>

              {logs[meal].length === 0 ? (
                <p className="text-xs" style={{ color: "rgba(255,255,255,0.2)" }}>Kuch add nahi kiya abhi</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {logs[meal].map((e, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg"
                      style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.65)" }}
                    >
                      {e.food.name}
                      {e.food.hindi && <span style={{ color: "rgba(255,255,255,0.3)" }}>({e.food.hindi})</span>}
                      <button onClick={() => removeFood(meal, i)} style={{ color: "rgba(255,255,255,0.25)" }}>
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Search overlay */}
        <AnimatePresence>
          {showSearch && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex flex-col"
              style={{ background: "rgba(6,6,10,0.96)" }}
            >
              <div className="max-w-lg mx-auto w-full px-4 pt-8 pb-4 flex-1 flex flex-col">
                <div className="flex items-center gap-3 mb-5">
                  <p className="text-sm font-bold flex-1" style={{ color: "rgba(255,255,255,0.85)" }}>
                    {MEAL_EMOJIS[activeMeal]} {activeMeal} mein add karo
                  </p>
                  <button
                    onClick={() => { setShowSearch(false); setQuery(""); }}
                    style={{ color: "rgba(255,255,255,0.4)" }}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl mb-4"
                  style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)" }}
                >
                  <Search className="w-4 h-4 shrink-0" style={{ color: "rgba(255,255,255,0.3)" }} />
                  <input
                    id="diary-search"
                    autoFocus
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Dal, roti, palak... ya Hindi mein"
                    className="flex-1 bg-transparent text-sm outline-none"
                    style={{ color: "rgba(255,255,255,0.85)" }}
                  />
                </div>

                <div className="flex-1 overflow-y-auto space-y-2">
                  {(results.length > 0 ? results : query.length === 0 ? [...FOOD_DB, ...RECIPE_DB].slice(0, 10) : []).map((food) => (
                    <button
                      key={food.id}
                      onClick={() => addFood(food)}
                      className="w-full flex items-center justify-between p-3 rounded-xl text-left"
                      style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                      <div>
                        <p className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.85)" }}>
                          {food.name}
                          {food.hindi && <span className="ml-2 text-xs" style={{ color: "rgba(255,255,255,0.35)" }}>{food.hindi}</span>}
                        </p>
                        <p className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                          {food.serving} · {food.category}
                        </p>
                      </div>
                      <div className="flex gap-1.5 shrink-0 ml-2">
                        {Object.entries(food.nutrients)
                          .filter(([k, v]) => (v ?? 0) > 0 && deficientNutrients.has(k))
                          .slice(0, 2)
                          .map(([k]) => (
                            <span
                              key={k}
                              className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                              style={{ background: "rgba(0,217,126,0.1)", color: "#00d97e" }}
                            >
                              {(DEFICIENCY_LABELS[k] || k).split(" ")[0]}
                            </span>
                          ))}
                      </div>
                    </button>
                  ))}
                  {query.length > 0 && results.length === 0 && (
                    <p className="text-center text-sm py-8" style={{ color: "rgba(255,255,255,0.3)" }}>
                      Koi food nahi mila "{query}"
                    </p>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <p className="text-xs text-center pb-4" style={{ color: "rgba(255,255,255,0.2)" }}>
          Data ICMR Indian food composition tables se hai
        </p>
      </div>
    </AppShell>
  );
}

function inputFocus() {
  setTimeout(() => document.getElementById("diary-search")?.focus(), 100);
}
