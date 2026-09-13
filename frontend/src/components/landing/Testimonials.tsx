"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Quote } from "lucide-react";

const TESTIMONIALS = [
  {
    name: "Priya Sharma",
    role: "Software Engineer · Delhi",
    avatar: "PS",
    color: "#00d97e",
    text: "3 mahine se thakaan rehti thi. BalanceAI ne Vitamin D aur Iron ki kami pakdi. Doc ne confirm kiya. Ab bahut better feel ho raha hai!",
    score: 82,
  },
  {
    name: "Rajesh Kumar",
    role: "Farmer · Uttar Pradesh",
    avatar: "RK",
    color: "#f59e0b",
    text: "Pehle blood test ke liye sheher jaana padta tha, 500 rupaye खर्च होते थे. Yeh free hai aur Hindi mein bolta hai. Bahut achha hai.",
    score: 65,
  },
  {
    name: "Dr. Meera Nair",
    role: "Medical Student · Kerala",
    avatar: "MN",
    color: "#818cf8",
    text: "AI recommendations ICMR guidelines se match karti hain. Students ke liye awareness ke liye bahut useful tool hai before actual lab work.",
    score: 91,
  },
  {
    name: "Ananya Gupta",
    role: "Homemaker · Punjab",
    avatar: "AG",
    color: "#22c55e",
    text: "Ghar pe baithe diet plan mil gaya. Ragi, bajra recommend kiya — jo hamare yahan asaani se milta hai. Practical advice hai yeh.",
    score: 74,
  },
  {
    name: "Vikram Patel",
    role: "IT Professional · Gujarat",
    avatar: "VP",
    color: "#38bdf8",
    text: "Voice mein bola aur Hinglish perfectly samajh gaya. Photo bhi liya nakhun ka — sach mein Iron deficiency nikli. Impressive accuracy.",
    score: 78,
  },
  {
    name: "Sunita Devi",
    role: "Teacher · Bihar",
    avatar: "SD",
    color: "#f472b6",
    text: "Mujhe lagta tha sirf educated log AI use kar sakte hain. Lekin yeh itna easy hai ki main bhi daily use karti hoon apne students ke saath.",
    score: 69,
  },
];

const DOUBLED = [...TESTIMONIALS, ...TESTIMONIALS];

export default function Testimonials() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-28 overflow-hidden"
      style={{ background: "#07070e" }}
    >
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <p className="land-label mb-4">Testimonials</p>
          <h2 className="land-h2 mb-5">
            Log Bol Rahe Hain
          </h2>
          <p className="text-base" style={{ color: "rgba(255,255,255,0.4)", fontFamily: "var(--font-inter)" }}>
            Real users, real results — across India
          </p>
        </motion.div>
      </div>

      {/* Scrolling ticker */}
      <div className="ticker-wrap">
        <div className="ticker-inner">
          {DOUBLED.map((t, i) => (
            <div
              key={i}
              className="flex-shrink-0 w-80 mx-3 rounded-2xl p-6 flex flex-col gap-4"
              style={{
                background: "rgba(255,255,255,0.035)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              <Quote className="w-5 h-5 opacity-20" style={{ color: t.color }} />

              <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.65)", fontFamily: "var(--font-inter)" }}>
                {t.text}
              </p>

              <div className="flex items-center justify-between mt-auto">
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold"
                    style={{ background: `${t.color}20`, color: t.color, border: `1px solid ${t.color}30` }}
                  >
                    {t.avatar}
                  </div>
                  <div>
                    <div className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.85)" }}>
                      {t.name}
                    </div>
                    <div className="text-xs" style={{ color: "rgba(255,255,255,0.38)" }}>
                      {t.role}
                    </div>
                  </div>
                </div>
                <div
                  className="text-xs font-bold px-2.5 py-1 rounded-full"
                  style={{
                    background: `${t.color}15`,
                    border: `1px solid ${t.color}25`,
                    color: t.color,
                  }}
                >
                  {t.score}/100
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Left/right edge fade */}
      <div
        className="absolute top-0 left-0 bottom-0 w-24 pointer-events-none z-10"
        style={{ background: "linear-gradient(to right, #07070e, transparent)" }}
      />
      <div
        className="absolute top-0 right-0 bottom-0 w-24 pointer-events-none z-10"
        style={{ background: "linear-gradient(to left, #07070e, transparent)" }}
      />
    </section>
  );
}
