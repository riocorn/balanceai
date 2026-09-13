"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const INDIA_STATS = [
  {
    stat: "68%",
    desc: "Indian children under 5 are anaemic",
    source: "NFHS-5, 2021",
    color: "#ef4444",
    icon: "🩸",
  },
  {
    stat: "76%",
    desc: "Urban Indians are Vitamin D deficient",
    source: "AIIMS Study, 2020",
    color: "#f59e0b",
    icon: "☀️",
  },
  {
    stat: "47%",
    desc: "Indian women have B12 deficiency",
    source: "ICMR, 2019",
    color: "#818cf8",
    icon: "🧬",
  },
  {
    stat: "₹80,000",
    desc: "Avg cost of nutrition tests in India",
    source: "Hospital Survey, 2023",
    color: "#06b6d4",
    icon: "💊",
  },
];

const BARS = [
  { label: "Iron",       pct: 58, color: "#ef4444" },
  { label: "Vitamin D",  pct: 76, color: "#f59e0b" },
  { label: "B12",        pct: 47, color: "#818cf8" },
  { label: "Calcium",    pct: 44, color: "#06b6d4" },
  { label: "Omega-3",    pct: 62, color: "#22c55e" },
  { label: "Zinc",       pct: 36, color: "#f472b6" },
];

export default function ImpactSection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-28 px-5 sm:px-8 overflow-hidden"
      style={{ background: "var(--land-bg)" }}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 900px 600px at 80% 50%, rgba(239,68,68,0.04) 0%, transparent 70%)",
        }}
      />

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "rgba(239,68,68,0.7)" }}>
            The Problem is Real
          </p>
          <h2 className="land-h2 mb-4">
            India Mein Nutrition Crisis
            <br />
            <span style={{ color: "#ef4444" }}>Silent Hai — Dangerous Nahi</span>
          </h2>
          <p className="text-base max-w-xl mx-auto" style={{ color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-inter)" }}>
            Most Indians never get tested. By the time symptoms show, deficiency is severe.
            BalanceAI detects it in 2 minutes — before the damage.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-start">
          {/* Left: stat cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {INDIA_STATS.map((s, i) => (
              <motion.div
                key={s.stat}
                initial={{ opacity: 0, y: 16 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="rounded-2xl p-5"
                style={{
                  background: `${s.color}08`,
                  border: `1px solid ${s.color}20`,
                }}
              >
                <div className="text-2xl mb-2">{s.icon}</div>
                <div className="text-3xl font-black font-display mb-1" style={{ color: s.color }}>
                  {s.stat}
                </div>
                <p className="text-sm mb-2 leading-snug" style={{ color: "rgba(255,255,255,0.7)" }}>
                  {s.desc}
                </p>
                <p className="text-[10px] font-semibold" style={{ color: "rgba(255,255,255,0.25)" }}>
                  {s.source}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Right: deficiency prevalence bars */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="rounded-2xl p-6"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
          >
            <p className="text-sm font-semibold mb-1" style={{ color: "rgba(255,255,255,0.75)" }}>
              % Indians Deficient
            </p>
            <p className="text-xs mb-6" style={{ color: "rgba(255,255,255,0.3)" }}>
              Based on NFHS-5, ICMR, NNMB 2012 data
            </p>
            <div className="space-y-4">
              {BARS.map((b, i) => (
                <div key={b.label}>
                  <div className="flex justify-between mb-1.5">
                    <span className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.65)" }}>{b.label}</span>
                    <span className="text-xs font-bold" style={{ color: b.color }}>{b.pct}%</span>
                  </div>
                  <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: b.color }}
                      initial={{ width: 0 }}
                      animate={inView ? { width: `${b.pct}%` } : {}}
                      transition={{ delay: 0.3 + i * 0.07, duration: 0.7, ease: "easeOut" }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div
              className="mt-6 p-3 rounded-xl text-xs"
              style={{ background: "rgba(0,217,126,0.05)", border: "1px solid rgba(0,217,126,0.1)", color: "rgba(0,217,126,0.7)" }}
            >
              💡 BalanceAI can detect all 6 of these — free, in 2 minutes
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
