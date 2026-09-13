"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { TrendingDown, IndianRupee, Clock } from "lucide-react";

const PROBLEMS = [
  {
    icon: TrendingDown,
    stat: "73%",
    unit: "",
    title: "Indians are Vitamin D Deficient",
    desc: "ICMR ke data ke hisaab se — har teesr Indian kami se jhelh raha hai, bina jaane.",
    color: "#ef4444",
  },
  {
    icon: IndianRupee,
    stat: "5,000",
    unit: "₹+",
    title: "Full Nutrition Blood Panel Cost",
    desc: "Ek complete micronutrient test India mein 3,000–8,000 rupaye ka padta hai.",
    color: "#f59e0b",
  },
  {
    icon: Clock,
    stat: "3–7",
    unit: " days",
    title: "Wait Time for Lab Reports",
    desc: "Blood test ke baad bhi hafte bhar ka wait. BalanceAI: 2 minute mein result.",
    color: "#6366f1",
  },
];

export default function ProblemSection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-28 px-5 sm:px-8"
      style={{ background: "var(--land-bg)" }}
    >
      {/* Top border line */}
      <div className="max-w-7xl mx-auto">
        <div
          className="w-full h-px mb-20"
          style={{ background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)" }}
        />

        {/* Section label */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <p className="land-label mb-4">The Problem</p>
          <h2 className="land-h2 mb-5">
            India ka Nutrition Crisis,
            <br />
            <span style={{ color: "rgba(255,255,255,0.45)" }}>Jo Dikh nahi Raha</span>
          </h2>
          <p className="text-base max-w-xl mx-auto" style={{ color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-inter)" }}>
            Deficiency symptoms generic hote hain — thakaan, baal jhadte hain, neend nahi aati.
            Log samajhte hain "stress hai" — asli kami pata hi nahi chalta.
          </p>
        </motion.div>

        {/* Problem cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {PROBLEMS.map((p, i) => {
            const Icon = p.icon;
            return (
              <motion.div
                key={p.title}
                initial={{ opacity: 0, y: 28 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: i * 0.15, ease: [0.22, 1, 0.36, 1] }}
                className="relative rounded-2xl p-7 bento-tile cursor-default overflow-hidden"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.07)",
                }}
              >
                {/* Background glow */}
                <div
                  className="absolute top-0 right-0 w-40 h-40 rounded-full pointer-events-none"
                  style={{
                    background: `radial-gradient(circle, ${p.color}12 0%, transparent 70%)`,
                    filter: "blur(30px)",
                  }}
                />

                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center mb-5"
                  style={{ background: `${p.color}18`, border: `1px solid ${p.color}30` }}
                >
                  <Icon className="w-5 h-5" style={{ color: p.color }} />
                </div>

                <div className="flex items-baseline gap-1 mb-3">
                  <span
                    className="text-5xl font-bold font-display"
                    style={{ color: p.color }}
                  >
                    {p.stat}
                  </span>
                  <span className="text-2xl font-bold" style={{ color: p.color, opacity: 0.8 }}>
                    {p.unit}
                  </span>
                </div>

                <h3 className="text-sm font-semibold mb-2" style={{ color: "rgba(255,255,255,0.9)" }}>
                  {p.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.42)", fontFamily: "var(--font-inter)" }}>
                  {p.desc}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* Resolution arrow */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ delay: 0.8 }}
          className="flex flex-col items-center mt-20 gap-3"
        >
          <div
            className="text-sm font-semibold"
            style={{ color: "rgba(255,255,255,0.3)" }}
          >
            Iska solution?
          </div>
          <div
            className="flex items-center gap-3 px-5 py-2.5 rounded-full"
            style={{
              background: "rgba(0,217,126,0.08)",
              border: "1px solid rgba(0,217,126,0.2)",
            }}
          >
            <span className="w-2 h-2 rounded-full" style={{ background: "#00d97e" }} />
            <span className="text-sm font-semibold" style={{ color: "#00d97e" }}>
              BalanceAI — 2 minute, ₹0, koi blood test nahi
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
