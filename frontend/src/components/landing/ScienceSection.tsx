"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { FlaskConical, Database, BrainCircuit, ShieldCheck } from "lucide-react";

const METRICS = [
  { value: "0.998", label: "AUC-ROC Score",       sub: "Validation dataset" },
  { value: "0.974", label: "Average Precision",    sub: "25-class detection"  },
  { value: "53K+",  label: "Training Samples",     sub: "NHANES + ICMR data"  },
  { value: "154",   label: "Input Features",       sub: "Symptoms, diet, visual" },
];

const PILLARS = [
  {
    icon: Database,
    title: "NHANES & ICMR Data",
    desc: "US National Health & Nutrition Examination Survey + Indian Council of Medical Research datasets pe trained. Real patient data.",
  },
  {
    icon: BrainCircuit,
    title: "Multi-modal AI Fusion",
    desc: "Text symptoms (NLP) + visual signs (CNN) + diet history — teen sources ko fuse karke final prediction banega.",
  },
  {
    icon: FlaskConical,
    title: "Traditional Medicine Integration",
    desc: "Ayurvedic remedies aur AYUSH guidelines ko modern nutrition science ke saath integrate kiya gaya hai.",
  },
  {
    icon: ShieldCheck,
    title: "Clinically Informed Design",
    desc: "Recommendations WHO, ICMR, aur FSSAI nutrient guidelines ke anusaar hain. Medical disclaimer always visible.",
  },
];

export default function ScienceSection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      id="science"
      ref={ref}
      className="relative py-28 px-5 sm:px-8 overflow-hidden"
      style={{ background: "#07070e" }}
    >
      {/* Decorative circle */}
      <div
        className="absolute -left-32 top-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full pointer-events-none"
        style={{
          border: "1px solid rgba(0,217,126,0.05)",
          background: "radial-gradient(circle, rgba(0,217,126,0.025) 0%, transparent 70%)",
        }}
      />

      <div className="relative max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          {/* Left */}
          <motion.div
            initial={{ opacity: 0, x: -24 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="land-label mb-4">Science</p>
            <h2 className="land-h2 mb-6">
              Real Research.
              <br />
              <span style={{ color: "#00d97e" }}>Real Numbers.</span>
            </h2>
            <p className="text-base leading-relaxed mb-10" style={{ color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-inter)" }}>
              BalanceAI sirf ek chatbot nahi — yeh ek clinical-grade AI system hai jo published
              research aur government health data pe trained hai. IIT Mandi ke AI Research Lab
              ki ongoing guidance mein develop ho raha hai.
            </p>

            {/* IIT badge */}
            <div
              className="inline-flex items-center gap-3 px-5 py-3 rounded-xl"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs"
                style={{ background: "rgba(0,217,126,0.12)", color: "#00d97e", border: "1px solid rgba(0,217,126,0.2)" }}
              >
                IIT
              </div>
              <div>
                <div className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.85)" }}>
                  IIT Mandi — AI Research Lab
                </div>
                <div className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
                  Himachal Pradesh · Est. 2009
                </div>
              </div>
            </div>
          </motion.div>

          {/* Right: Metrics + pillars */}
          <motion.div
            initial={{ opacity: 0, x: 24 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.65, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="flex flex-col gap-5"
          >
            {/* Metric row */}
            <div className="grid grid-cols-2 gap-3">
              {METRICS.map((m, i) => (
                <motion.div
                  key={m.label}
                  initial={{ opacity: 0, y: 12 }}
                  animate={inView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: 0.2 + i * 0.1 }}
                  className="rounded-xl p-4"
                  style={{
                    background: "rgba(0,217,126,0.04)",
                    border: "1px solid rgba(0,217,126,0.12)",
                  }}
                >
                  <div className="text-2xl font-bold font-display mb-0.5" style={{ color: "#00d97e" }}>
                    {m.value}
                  </div>
                  <div className="text-xs font-semibold mb-0.5" style={{ color: "rgba(255,255,255,0.75)" }}>
                    {m.label}
                  </div>
                  <div className="text-[10px]" style={{ color: "rgba(255,255,255,0.35)" }}>
                    {m.sub}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Pillars */}
            <div className="grid grid-cols-1 gap-3">
              {PILLARS.map((p, i) => {
                const Icon = p.icon;
                return (
                  <motion.div
                    key={p.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={inView ? { opacity: 1, y: 0 } : {}}
                    transition={{ delay: 0.4 + i * 0.1 }}
                    className="flex items-start gap-4 p-4 rounded-xl"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.06)",
                    }}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{ background: "rgba(0,217,126,0.1)", border: "1px solid rgba(0,217,126,0.15)" }}
                    >
                      <Icon className="w-4 h-4" style={{ color: "#00d97e" }} />
                    </div>
                    <div>
                      <div className="text-sm font-semibold mb-1" style={{ color: "rgba(255,255,255,0.85)" }}>
                        {p.title}
                      </div>
                      <div className="text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.4)", fontFamily: "var(--font-inter)" }}>
                        {p.desc}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
