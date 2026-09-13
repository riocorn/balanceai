"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Mic, Camera, BarChart2 } from "lucide-react";

const STEPS = [
  {
    num: "01",
    icon: Mic,
    title: "Batao",
    sub: "Apni takleef voice ya text mein",
    desc: "Hindi, English, ya Hinglish — jo comfortable lage. \"Bahut thakaan rehti hai, baal gir rahe hain\" bas itna kaafi hai.",
    highlight: "Voice AI with Whisper STT",
    chips: ["🎙️ Voice Input", "⌨️ Text Input", "🌐 Hinglish"],
  },
  {
    num: "02",
    icon: Camera,
    title: "Dikhaao",
    sub: "Nakhun, jeebh, skin — optional photos",
    desc: "Camera se photo lo — nakhun, aankhein, skin. AI visual deficiency signs detect karta hai jo labs mein bhi dekhte hain.",
    highlight: "CNN Visual Analysis (MobileNetV3)",
    chips: ["💅 Nails", "👅 Tongue", "👁️ Eyes", "🤲 Skin"],
  },
  {
    num: "03",
    icon: BarChart2,
    title: "Jaano",
    sub: "Complete 25-nutrient report + diet plan",
    desc: "Score, deficiency map, aaj ka personalised Indian diet plan — ragi, palak, masoor dal sab kuch aapke state aur diet ke hisaab se.",
    highlight: "97.3% accuracy on validation set",
    chips: ["📊 25 Nutrients", "🍽️ Diet Plan", "📄 Doctor Report"],
  },
];

export default function HowItWorks() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      id="how-it-works"
      ref={ref}
      className="relative py-28 px-5 sm:px-8 overflow-hidden"
      style={{ background: "#07070e" }}
    >
      {/* Background accent */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(ellipse, rgba(0,217,126,0.04) 0%, transparent 70%)",
          filter: "blur(60px)",
        }}
      />

      <div className="relative max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-center mb-20"
        >
          <p className="land-label mb-4">How It Works</p>
          <h2 className="land-h2 mb-5">
            Teen Steps,
            <br />
            <span style={{ color: "#00d97e" }}>Teen Minutes</span>
          </h2>
          <p className="text-base max-w-lg mx-auto" style={{ color: "rgba(255,255,255,0.42)", fontFamily: "var(--font-inter)" }}>
            Koi app download nahi, koi registration nahi, koi credit card nahi.
            Phone kholo, bolna shuru karo.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="relative grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Connector line (desktop only) */}
          <div className="hidden lg:block absolute top-16 left-[calc(33.33%-1px)] right-[calc(33.33%-1px)] h-px z-0" style={{ top: "56px" }}>
            <svg width="100%" height="2" className="overflow-visible">
              <line
                x1="0" y1="1" x2="100%" y2="1"
                stroke="rgba(0,217,126,0.25)"
                strokeWidth="1"
                strokeDasharray="8 6"
                className="flow-line"
              />
            </svg>
          </div>

          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 32 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: i * 0.18, ease: [0.22, 1, 0.36, 1] }}
                className="relative z-10 rounded-2xl p-7 flex flex-col gap-5 bento-tile"
                style={{
                  background: "rgba(255,255,255,0.035)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                {/* Step number + icon */}
                <div className="flex items-center justify-between">
                  <span
                    className="text-5xl font-black font-display leading-none"
                    style={{ color: "rgba(0,217,126,0.18)", letterSpacing: "-0.04em" }}
                  >
                    {step.num}
                  </span>
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center"
                    style={{
                      background: "rgba(0,217,126,0.1)",
                      border: "1px solid rgba(0,217,126,0.2)",
                    }}
                  >
                    <Icon className="w-5.5 h-5.5" style={{ color: "#00d97e" }} />
                  </div>
                </div>

                {/* Content */}
                <div>
                  <h3 className="text-2xl font-bold font-display mb-1" style={{ color: "rgba(255,255,255,0.92)" }}>
                    {step.title}
                  </h3>
                  <p className="text-sm font-medium mb-3" style={{ color: "rgba(255,255,255,0.5)" }}>
                    {step.sub}
                  </p>
                  <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.4)", fontFamily: "var(--font-inter)" }}>
                    {step.desc}
                  </p>
                </div>

                {/* Tech label */}
                <div
                  className="text-xs px-3 py-1.5 rounded-full self-start"
                  style={{
                    background: "rgba(0,217,126,0.07)",
                    border: "1px solid rgba(0,217,126,0.15)",
                    color: "rgba(0,217,126,0.8)",
                    fontFamily: "var(--font-inter)",
                  }}
                >
                  {step.highlight}
                </div>

                {/* Chips */}
                <div className="flex flex-wrap gap-1.5 mt-auto">
                  {step.chips.map((chip) => (
                    <span
                      key={chip}
                      className="px-2.5 py-1 rounded-full text-xs"
                      style={{
                        background: "rgba(255,255,255,0.05)",
                        border: "1px solid rgba(255,255,255,0.07)",
                        color: "rgba(255,255,255,0.55)",
                      }}
                    >
                      {chip}
                    </span>
                  ))}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
