"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Leaf, TrendingUp, Users, Globe, Mail } from "lucide-react";

const TRACTION = [
  { icon: Users,     value: "2.4L+", label: "Monthly Active Users (projected Y1)" },
  { icon: Globe,     value: "28",    label: "Indian States Covered" },
  { icon: TrendingUp,value: "91%",   label: "Model Accuracy on Blind Test Set" },
];

const ROADMAP = [
  { q: "Q1 2025", text: "Free consumer app · India launch",     done: true  },
  { q: "Q2 2025", text: "Hospital API integration pilot",        done: true  },
  { q: "Q3 2025", text: "10L user milestone · Vernacular voice", done: false },
  { q: "Q4 2025", text: "Series A · Southeast Asia expansion",   done: false },
];

export default function InvestorSection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-28 px-5 sm:px-8 overflow-hidden"
      style={{ background: "#050508", borderTop: "1px solid rgba(255,255,255,0.05)" }}
    >
      {/* Green glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at 50% 0%, rgba(0,217,126,0.08) 0%, transparent 70%)",
        }}
      />

      <div className="max-w-5xl mx-auto relative z-10">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="flex justify-center mb-8"
        >
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold"
            style={{
              background: "rgba(0,217,126,0.08)",
              border: "1px solid rgba(0,217,126,0.2)",
              color: "#00d97e",
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#00d97e] animate-pulse" />
            Seed Round Open · ₹40L Target
          </div>
        </motion.div>

        {/* Heading */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.05, duration: 0.6 }}
          className="text-center mb-14"
        >
          <h2 className="land-h2 mb-4">
            Building the
            <span style={{ color: "#00d97e" }}> Nutrition OS</span>
            <br />
            for 1.4 Billion Indians
          </h2>
          <p className="text-base max-w-2xl mx-auto" style={{ color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-inter)" }}>
            India's nutrition deficiency burden costs ₹2.5 lakh crore annually in lost productivity.
            We're building the infrastructure to detect, track, and fix it — at zero cost to users.
          </p>
        </motion.div>

        {/* Traction */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-14">
          {TRACTION.map((t, i) => (
            <motion.div
              key={t.label}
              initial={{ opacity: 0, y: 16 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.1 + i * 0.07, duration: 0.5 }}
              className="rounded-2xl p-6 text-center"
              style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <t.icon className="w-5 h-5 mx-auto mb-3" style={{ color: "#00d97e" }} />
              <div className="text-3xl font-black font-display mb-1" style={{ color: "rgba(255,255,255,0.9)" }}>
                {t.value}
              </div>
              <p className="text-xs" style={{ color: "rgba(255,255,255,0.35)" }}>{t.label}</p>
            </motion.div>
          ))}
        </div>

        {/* Roadmap */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.25, duration: 0.6 }}
          className="rounded-2xl p-6 mb-10"
          style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}
        >
          <p className="text-xs font-bold uppercase tracking-widest mb-5" style={{ color: "rgba(255,255,255,0.3)" }}>
            Roadmap
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {ROADMAP.map((r, i) => (
              <div key={r.q} className="relative">
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold"
                    style={{
                      background: r.done ? "#00d97e" : "rgba(255,255,255,0.08)",
                      color: r.done ? "#000" : "rgba(255,255,255,0.3)",
                    }}
                  >
                    {r.done ? "✓" : i + 1}
                  </div>
                  <span className="text-[10px] font-bold" style={{ color: r.done ? "#00d97e" : "rgba(255,255,255,0.3)" }}>
                    {r.q}
                  </span>
                </div>
                <p className="text-xs leading-snug pl-7" style={{ color: r.done ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.3)" }}>
                  {r.text}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="mailto:balanceai@iitmandi.ac.in?subject=Investment Interest - BalanceAI"
            className="flex items-center gap-2.5 px-7 py-3.5 rounded-xl font-semibold text-sm text-black"
            style={{ background: "#00d97e", boxShadow: "0 0 32px rgba(0,217,126,0.2)" }}
          >
            <Mail className="w-4 h-4" /> Investor Inquiry
          </a>
          <a
            href="/enterprise"
            className="flex items-center gap-2.5 px-7 py-3.5 rounded-xl font-semibold text-sm"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: "rgba(255,255,255,0.65)",
            }}
          >
            <Leaf className="w-4 h-4" /> Hospital / Enterprise
          </a>
        </motion.div>

        {/* Fine print */}
        <p className="text-center text-xs mt-6" style={{ color: "rgba(255,255,255,0.18)" }}>
          IIT Mandi AI Research Lab · Seed round in progress · DPIIT Startup India registered
        </p>
      </div>
    </section>
  );
}
