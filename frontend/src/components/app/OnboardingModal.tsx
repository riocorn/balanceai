"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Check, X } from "lucide-react";
import { updateProfile } from "@/lib/db";

const GOAL_OPTIONS = [
  { id: "energy",     label: "Thakaan kam karo",    emoji: "⚡" },
  { id: "immunity",   label: "Immunity badhao",      emoji: "🛡️" },
  { id: "hair_nails", label: "Baal & nakhun",        emoji: "✨" },
  { id: "sleep",      label: "Neend theek karo",     emoji: "🌙" },
  { id: "weight",     label: "Weight manage",        emoji: "⚖️" },
  { id: "general",    label: "General health",       emoji: "💚" },
];

const GENDER_OPTIONS = [
  { id: "male",   label: "Male"   },
  { id: "female", label: "Female" },
  { id: "other",  label: "Other"  },
];

interface Props {
  onComplete: () => void;
}

export default function OnboardingModal({ onComplete }: Props) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [goals, setGoals] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const toggleGoal = (id: string) =>
    setGoals((p) => (p.includes(id) ? p.filter((g) => g !== id) : [...p, id]));

  const handleFinish = async () => {
    setSaving(true);
    await updateProfile({
      name: name.trim() || "User",
      age: age ? parseInt(age) : undefined,
      gender: gender as any || undefined,
      goals,
    });
    setSaving(false);
    onComplete();
  };

  const canNext = [
    name.trim().length >= 2,
    !!gender,
    goals.length >= 1,
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(12px)" }}
    >
      <motion.div
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-md rounded-3xl overflow-hidden"
        style={{ background: "#0e0e16", border: "1px solid rgba(255,255,255,0.08)" }}
      >
        {/* Progress dots */}
        <div className="flex items-center gap-1.5 px-6 pt-5 pb-1">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-1 rounded-full transition-all duration-300"
              style={{
                width: i === step ? 24 : 8,
                background: i <= step ? "#00d97e" : "rgba(255,255,255,0.1)",
              }}
            />
          ))}
        </div>

        <AnimatePresence mode="wait">
          {/* Step 0: Name */}
          {step === 0 && (
            <motion.div
              key="s0"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="px-6 py-6"
            >
              <p className="text-3xl mb-1">👋</p>
              <h2 className="text-xl font-bold mb-1" style={{ color: "rgba(255,255,255,0.9)" }}>
                Namaste!
              </h2>
              <p className="text-sm mb-6" style={{ color: "rgba(255,255,255,0.4)" }}>
                BalanceAI mein aapka swagat hai. Pehle kuch basic baatein.
              </p>
              <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>
                Aapka naam
              </label>
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && canNext[0] && setStep(1)}
                placeholder="Apna naam likhein..."
                className="w-full px-4 py-3 rounded-xl text-sm outline-none"
                style={{
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "rgba(255,255,255,0.9)",
                }}
              />
            </motion.div>
          )}

          {/* Step 1: Age + Gender */}
          {step === 1 && (
            <motion.div
              key="s1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="px-6 py-6"
            >
              <h2 className="text-xl font-bold mb-1" style={{ color: "rgba(255,255,255,0.9)" }}>
                Thoda aur jaano
              </h2>
              <p className="text-sm mb-5" style={{ color: "rgba(255,255,255,0.4)" }}>
                Better personalization ke liye
              </p>

              <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>
                Aayu (optional)
              </label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="Years"
                min={10} max={100}
                className="w-28 px-4 py-3 rounded-xl text-sm outline-none mb-5"
                style={{
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "rgba(255,255,255,0.9)",
                }}
              />

              <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>
                Gender
              </label>
              <div className="flex gap-2">
                {GENDER_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setGender(opt.id)}
                    className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all"
                    style={{
                      background: gender === opt.id ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.05)",
                      border: gender === opt.id ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.08)",
                      color: gender === opt.id ? "#00d97e" : "rgba(255,255,255,0.55)",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Step 2: Goals */}
          {step === 2 && (
            <motion.div
              key="s2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="px-6 py-6"
            >
              <h2 className="text-xl font-bold mb-1" style={{ color: "rgba(255,255,255,0.9)" }}>
                Aapka goal kya hai?
              </h2>
              <p className="text-sm mb-5" style={{ color: "rgba(255,255,255,0.4)" }}>
                Ek ya zyada select karo
              </p>
              <div className="grid grid-cols-2 gap-2">
                {GOAL_OPTIONS.map((g) => {
                  const sel = goals.includes(g.id);
                  return (
                    <button
                      key={g.id}
                      onClick={() => toggleGoal(g.id)}
                      className="flex items-center gap-2 px-3 py-3 rounded-xl text-left text-sm transition-all"
                      style={{
                        background: sel ? "rgba(0,217,126,0.1)" : "rgba(255,255,255,0.04)",
                        border: sel ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.07)",
                        color: sel ? "#00d97e" : "rgba(255,255,255,0.6)",
                      }}
                    >
                      <span>{g.emoji}</span>
                      <span className="font-medium text-xs">{g.label}</span>
                      {sel && <Check className="w-3 h-3 ml-auto shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* Step 3: Done */}
          {step === 3 && (
            <motion.div
              key="s3"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="px-6 py-8 flex flex-col items-center text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 18, delay: 0.1 }}
                className="w-20 h-20 rounded-full flex items-center justify-center mb-5 text-4xl"
                style={{ background: "rgba(0,217,126,0.12)", border: "2px solid rgba(0,217,126,0.3)" }}
              >
                ✅
              </motion.div>
              <h2 className="text-2xl font-bold mb-2" style={{ color: "rgba(255,255,255,0.92)" }}>
                Shuruaat acchi rahi!
              </h2>
              <p className="text-sm mb-1" style={{ color: "rgba(255,255,255,0.4)" }}>
                Namaste, <span style={{ color: "#00d97e", fontWeight: 600 }}>{name}</span>!
              </p>
              <p className="text-sm mb-8" style={{ color: "rgba(255,255,255,0.35)" }}>
                Ab apna pehla analysis karo — BalanceAI aapke liye personalized plan tayaar karega.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer buttons */}
        <div className="px-6 pb-6 flex gap-3">
          {step < 3 && step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              className="px-4 py-3 rounded-xl text-sm font-medium"
              style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.08)" }}
            >
              Back
            </button>
          )}

          {step < 2 && (
            <button
              onClick={() => setStep(step + 1)}
              disabled={!canNext[step]}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-black transition-all"
              style={{ background: canNext[step] ? "#00d97e" : "rgba(0,217,126,0.3)", cursor: canNext[step] ? "pointer" : "not-allowed" }}
            >
              Aage <ArrowRight className="w-4 h-4" />
            </button>
          )}

          {step === 2 && (
            <button
              onClick={() => setStep(3)}
              disabled={!canNext[2]}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-black transition-all"
              style={{ background: canNext[2] ? "#00d97e" : "rgba(0,217,126,0.3)", cursor: canNext[2] ? "pointer" : "not-allowed" }}
            >
              Continue <ArrowRight className="w-4 h-4" />
            </button>
          )}

          {step === 3 && (
            <button
              onClick={handleFinish}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-black"
              style={{ background: "#00d97e" }}
            >
              {saving ? "Saving..." : "Analysis Shuru Karo →"}
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
