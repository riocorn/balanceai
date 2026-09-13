"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Mic, Camera, Dna, UtensilsCrossed, BarChart3, Lock } from "lucide-react";

const FEATURES = [
  {
    icon: Mic,
    title: "Hinglish Voice AI",
    desc: "\"Bahut thakaan rehti hai\" — bas bol do. AI Hinglish, Hindi, English sab samajhta hai. Whisper model se 95%+ accuracy.",
    size: "large",
    accent: "#00d97e",
    tag: "Offline STT",
    preview: (
      <div className="mt-5 rounded-xl p-3.5 flex flex-col gap-2.5" style={{ background: "rgba(0,217,126,0.05)", border: "1px solid rgba(0,217,126,0.1)" }}>
        {["Bahut thakaan rehti hai...", "Baal gir rahe hain...", "Haath mein jhanjhanahat..."].map((t, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#00d97e", opacity: 1 - i * 0.25 }} />
            <span className="text-xs" style={{ color: "rgba(255,255,255,0.5)" }}>{t}</span>
          </div>
        ))}
      </div>
    ),
  },
  {
    icon: Camera,
    title: "Visual Deficiency Scan",
    desc: "Nakhun ka rang, jeebh ki texture, skin ka pattern — CNN model se deficiency signs detect hote hain.",
    size: "normal",
    accent: "#818cf8",
    tag: "MobileNetV3 CNN",
    preview: (
      <div className="mt-4 grid grid-cols-2 gap-2">
        {["💅 Nails", "👅 Tongue", "👁️ Eyes", "🤲 Skin"].map((m) => (
          <div key={m} className="rounded-lg py-2 text-center text-xs" style={{ background: "rgba(129,140,248,0.08)", border: "1px solid rgba(129,140,248,0.12)", color: "rgba(255,255,255,0.5)" }}>
            {m}
          </div>
        ))}
      </div>
    ),
  },
  {
    icon: Dna,
    title: "25 Nutrients Mapped",
    desc: "Vitamin D, Iron, B12, Zinc, Omega-3, Magnesium aur 19 aur — ek complete nutritional fingerprint.",
    size: "normal",
    accent: "#f59e0b",
    tag: "154-feature model",
    preview: (
      <div className="mt-4 flex flex-col gap-1.5">
        {[["Vitamin D", 91, "#ef4444"], ["Iron", 78, "#ef4444"], ["B12", 65, "#f59e0b"], ["Magnesium", 55, "#f59e0b"]].map(([n, v, c]) => (
          <div key={String(n)} className="flex items-center gap-2">
            <span className="text-[10px] w-20 flex-shrink-0" style={{ color: "rgba(255,255,255,0.45)" }}>{n}</span>
            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.07)" }}>
              <div className="h-full rounded-full" style={{ width: `${v}%`, background: String(c) }} />
            </div>
            <span className="text-[10px] w-7 text-right" style={{ color: String(c) }}>{v}%</span>
          </div>
        ))}
      </div>
    ),
  },
  {
    icon: UtensilsCrossed,
    title: "Smart Indian Diet Plan",
    desc: "Ragi roti, masoor dal, palak subzi — aapke state, season, aur deficiency ke hisaab se personalised daily meal plan.",
    size: "wide",
    accent: "#22c55e",
    tag: "State + Season aware",
    preview: (
      <div className="mt-4 grid grid-cols-4 gap-2">
        {[["🌅", "Breakfast", "Ragi idli, Methi subzi"], ["☀️", "Lunch", "Masoor dal, Brown rice"], ["🍎", "Snack", "Bhune chane, Akhrot"], ["🌙", "Dinner", "Bajra roti, Palak"]].map(([e, m, f]) => (
          <div key={String(m)} className="rounded-xl p-2.5 flex flex-col gap-1" style={{ background: "rgba(34,197,94,0.05)", border: "1px solid rgba(34,197,94,0.1)" }}>
            <span className="text-base">{String(e)}</span>
            <span className="text-[9px] font-semibold uppercase tracking-wide" style={{ color: "rgba(34,197,94,0.7)" }}>{String(m)}</span>
            <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.4)" }}>{String(f)}</span>
          </div>
        ))}
      </div>
    ),
  },
  {
    icon: BarChart3,
    title: "Health History & Trends",
    desc: "Roz ka score, nutrient trends, symptom improvement — 90-din ka progress ek jagah.",
    size: "normal",
    accent: "#38bdf8",
    tag: "IndexedDB offline",
    preview: (
      <div className="mt-4 flex items-end gap-1 h-16">
        {[40, 45, 52, 48, 58, 65, 62, 70, 74, 72, 78, 82].map((v, i) => (
          <div key={i} className="flex-1 rounded-t" style={{ height: `${(v / 82) * 100}%`, background: `rgba(56,189,248,${0.2 + (i / 14)})` }} />
        ))}
      </div>
    ),
  },
  {
    icon: Lock,
    title: "100% Private & Offline",
    desc: "Koi data cloud pe nahi jaata. Sab kuch aapke device pe. Internet ke bina bhi kaam karta hai — rural India ke liye bhi.",
    size: "normal",
    accent: "#a78bfa",
    tag: "Device-first",
    preview: (
      <div className="mt-4 flex flex-col gap-2">
        {["✓ No server upload", "✓ Works without internet", "✓ No account needed"].map((t) => (
          <div key={t} className="text-xs flex items-center gap-2" style={{ color: "rgba(167,139,250,0.8)" }}>
            {t}
          </div>
        ))}
      </div>
    ),
  },
];

export default function FeatureBento() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      id="features"
      ref={ref}
      className="relative py-28 px-5 sm:px-8"
      style={{ background: "var(--land-bg)" }}
    >
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <p className="land-label mb-4">Features</p>
          <h2 className="land-h2 mb-5">
            Ek Tool,
            <br />
            <span style={{ color: "rgba(255,255,255,0.4)" }}>Saare Answers</span>
          </h2>
        </motion.div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 auto-rows-auto">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            const isWide = f.size === "wide";
            const isLarge = f.size === "large";

            return (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 28 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] }}
                className={`relative rounded-2xl p-6 bento-tile overflow-hidden ${
                  isWide ? "md:col-span-2 xl:col-span-2" : ""
                } ${isLarge ? "xl:row-span-2" : ""}`}
                style={{
                  background: "rgba(255,255,255,0.035)",
                  border: "1px solid rgba(255,255,255,0.07)",
                }}
              >
                {/* Accent glow top-right */}
                <div
                  className="absolute -top-10 -right-10 w-36 h-36 rounded-full pointer-events-none"
                  style={{
                    background: `radial-gradient(circle, ${f.accent}14 0%, transparent 70%)`,
                    filter: "blur(20px)",
                  }}
                />

                {/* Icon + tag */}
                <div className="flex items-start justify-between mb-4 relative z-10">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ background: `${f.accent}18`, border: `1px solid ${f.accent}28` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: f.accent }} />
                  </div>
                  <span
                    className="px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider"
                    style={{
                      background: `${f.accent}10`,
                      border: `1px solid ${f.accent}20`,
                      color: f.accent,
                    }}
                  >
                    {f.tag}
                  </span>
                </div>

                <h3 className="land-h3 mb-2 relative z-10">{f.title}</h3>
                <p className="text-sm leading-relaxed relative z-10" style={{ color: "rgba(255,255,255,0.42)", fontFamily: "var(--font-inter)" }}>
                  {f.desc}
                </p>

                <div className="relative z-10">{f.preview}</div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
