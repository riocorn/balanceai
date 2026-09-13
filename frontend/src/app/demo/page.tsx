"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Leaf, Play, Loader2, ArrowRight } from "lucide-react";
import { DEFICIENCY_LABELS } from "@/lib/api";
import { scoreColor } from "@/lib/db";

const DEMO_RESULT = [
  { deficiency: "vitamin_d", probability: 0.91, risk_level: "high" },
  { deficiency: "iron", probability: 0.78, risk_level: "high" },
  { deficiency: "vitamin_b12", probability: 0.65, risk_level: "high" },
  { deficiency: "magnesium", probability: 0.55, risk_level: "medium" },
  { deficiency: "omega3", probability: 0.52, risk_level: "medium" },
  { deficiency: "zinc", probability: 0.42, risk_level: "medium" },
  { deficiency: "folate", probability: 0.38, risk_level: "medium" },
  { deficiency: "calcium", probability: 0.25, risk_level: "low" },
  { deficiency: "vitamin_c", probability: 0.18, risk_level: "low" },
  { deficiency: "iodine", probability: 0.12, risk_level: "low" },
];

const DEMO_DIET = [
  { meal: "Breakfast", emoji: "🌅", foods: ["Ragi idli x3", "Methi-aaloo sabzi", "Amla murabba", "Doodh 1 glass"] },
  { meal: "Lunch",     emoji: "☀️", foods: ["Masoor dal (iron kadai)", "Brown rice", "Palak sabzi", "Nimbu paani"] },
  { meal: "Snacks",    emoji: "🍎", foods: ["Bhune chane + akhrot", "Dried apricot 3-4 pcs"] },
  { meal: "Dinner",    emoji: "🌙", foods: ["Bajra roti x2", "Egg bhurji / Paneer", "Salad", "Til-jaggery ladoo x1"] },
];

const SCORE = 42;

const STEPS = [
  "Symptoms analyse ho rahi hain...",
  "25 nutrients check ho rahe hain...",
  "State data (Delhi) match ho raha hai...",
  "AI model running...",
  "Diet plan generate ho raha hai...",
];

export default function DemoPage() {
  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [progress, setProgress] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);

  const runDemo = async () => {
    setPhase("running");
    for (let i = 0; i <= 10; i++) {
      await new Promise((r) => setTimeout(r, 220));
      setProgress(i * 10);
      setStepIdx(Math.min(Math.floor(i / 2), STEPS.length - 1));
    }
    setPhase("done");
  };

  const color = scoreColor(SCORE);

  return (
    <div className="min-h-screen" style={{ background: "#06060a" }}>
      <div className="max-w-2xl mx-auto px-5 py-8 space-y-6">

        {/* Top bar */}
        <div className="flex items-center justify-between">
          <Link href="/">
            <div
              className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-xl cursor-pointer transition-colors"
              style={{ color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Wapas
            </div>
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#00d97e] flex items-center justify-center">
              <Leaf className="w-3.5 h-3.5 text-black" />
            </div>
            <span className="font-bold text-sm text-white font-display">BalanceAI</span>
            <span
              className="text-[10px] font-bold px-2 py-0.5 rounded-full"
              style={{ background: "rgba(0,217,126,0.1)", color: "#00d97e", border: "1px solid rgba(0,217,126,0.2)" }}
            >
              LIVE DEMO
            </span>
          </div>
        </div>

        <AnimatePresence mode="wait">

          {/* INTRO */}
          {phase === "intro" && (
            <motion.div key="intro" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest mb-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                  Demo Patient
                </p>
                <h1 className="font-display font-bold text-2xl mb-4" style={{ color: "rgba(255,255,255,0.9)" }}>
                  Radha, 28 — Delhi
                </h1>
                <div
                  className="rounded-2xl p-5"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
                >
                  <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.65)" }}>
                    Ghar mein baith ke kaam karti hai. Roz bahut thakaan mehsoos hoti hai, baal gir rahe hain, haath-pair mein jhanjhanahat hoti hai, ratko neend nahi aati.
                  </p>
                  <div className="flex gap-2 mt-3">
                    {["📍 Delhi", "🥗 Vegetarian", "💼 Work from home"].map((tag) => (
                      <span
                        key={tag}
                        className="text-xs px-2.5 py-1 rounded-lg font-medium"
                        style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)" }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <button
                onClick={runDemo}
                className="w-full flex items-center justify-center gap-2.5 py-4 rounded-2xl text-base font-bold text-black"
                style={{ background: "#00d97e", boxShadow: "0 0 32px rgba(0,217,126,0.3)" }}
              >
                <Play className="w-5 h-5" /> Demo Chalao
              </button>
            </motion.div>
          )}

          {/* RUNNING */}
          {phase === "running" && (
            <motion.div key="running" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="py-16 flex flex-col items-center gap-6">
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center"
                style={{ background: "rgba(0,217,126,0.08)", border: "1px solid rgba(0,217,126,0.2)" }}
              >
                <Loader2 className="w-9 h-9 animate-spin" style={{ color: "#00d97e" }} />
              </div>
              <div className="text-center">
                <p className="font-bold text-lg mb-1" style={{ color: "rgba(255,255,255,0.9)" }}>
                  AI Analysis
                </p>
                <AnimatePresence mode="wait">
                  <motion.p
                    key={stepIdx}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="text-sm"
                    style={{ color: "rgba(255,255,255,0.4)" }}
                  >
                    {STEPS[stepIdx]}
                  </motion.p>
                </AnimatePresence>
              </div>
              <div className="w-full max-w-xs">
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: "#00d97e" }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.18 }}
                  />
                </div>
                <p className="text-xs mt-2 text-right" style={{ color: "rgba(255,255,255,0.25)" }}>{progress}%</p>
              </div>
            </motion.div>
          )}

          {/* DONE */}
          {phase === "done" && (
            <motion.div key="done" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">

              {/* Score */}
              <div
                className="rounded-2xl p-6 flex items-center justify-between"
                style={{ background: "rgba(255,255,255,0.04)", border: `1px solid ${color}25` }}
              >
                <div>
                  <p className="text-xs mb-1" style={{ color: "rgba(255,255,255,0.35)" }}>Nutrition Score</p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-6xl font-black font-display" style={{ color }}>{SCORE}</span>
                    <span className="text-lg" style={{ color: "rgba(255,255,255,0.3)" }}>/100</span>
                  </div>
                  <span
                    className="text-xs font-bold px-2.5 py-1 rounded-full mt-2 inline-block"
                    style={{ background: `${color}12`, color, border: `1px solid ${color}30` }}
                  >
                    Needs Attention
                  </span>
                </div>
                <div className="space-y-1.5 text-right text-xs">
                  <p style={{ color: "#ef4444" }}>⚠ 3 high risk</p>
                  <p style={{ color: "#f59e0b" }}>⚠ 4 medium risk</p>
                  <p style={{ color: "#22c55e" }}>✓ 18 nutrients ok</p>
                </div>
              </div>

              {/* Deficiency bars */}
              <div
                className="rounded-2xl p-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <p className="text-sm font-semibold mb-4" style={{ color: "rgba(255,255,255,0.7)" }}>
                  Deficiency Analysis
                </p>
                <div className="space-y-3">
                  {DEMO_RESULT.slice(0, 7).map((d, i) => {
                    const c = d.risk_level === "high" ? "#ef4444" : d.risk_level === "medium" ? "#f59e0b" : "#22c55e";
                    return (
                      <motion.div
                        key={d.deficiency}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.05 }}
                        className="flex items-center gap-3"
                      >
                        <p className="text-xs w-28 shrink-0" style={{ color: "rgba(255,255,255,0.6)" }}>
                          {DEFICIENCY_LABELS[d.deficiency] || d.deficiency}
                        </p>
                        <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                          <motion.div
                            className="h-full rounded-full"
                            style={{ background: c }}
                            initial={{ width: 0 }}
                            animate={{ width: `${d.probability * 100}%` }}
                            transition={{ delay: i * 0.05 + 0.1, duration: 0.5 }}
                          />
                        </div>
                        <span className="text-[10px] font-bold w-8 text-right" style={{ color: c }}>
                          {Math.round(d.probability * 100)}%
                        </span>
                      </motion.div>
                    );
                  })}
                </div>
              </div>

              {/* Diet plan */}
              <div
                className="rounded-2xl p-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <p className="text-sm font-semibold mb-4" style={{ color: "rgba(255,255,255,0.7)" }}>
                  🍽️ Aaj ka Diet Plan
                </p>
                <div className="space-y-3">
                  {DEMO_DIET.map((m) => (
                    <div key={m.meal}>
                      <p className="text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                        {m.emoji} {m.meal}
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {m.foods.map((f) => (
                          <span
                            key={f}
                            className="text-xs px-2.5 py-1 rounded-lg"
                            style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.6)" }}
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div
                  className="mt-4 p-3 rounded-xl text-xs"
                  style={{ background: "rgba(0,217,126,0.06)", border: "1px solid rgba(0,217,126,0.12)", color: "rgba(0,217,126,0.8)" }}
                >
                  💡 Masoor dal iron kadai mein paka — free mein 5–20mg iron milta hai
                </div>
              </div>

              <Link href="/analyze">
                <div
                  className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl text-base font-bold text-black cursor-pointer"
                  style={{ background: "#00d97e", boxShadow: "0 0 32px rgba(0,217,126,0.25)" }}
                >
                  Apna Analysis Karo <ArrowRight className="w-5 h-5" />
                </div>
              </Link>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
}
