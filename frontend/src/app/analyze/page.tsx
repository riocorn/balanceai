"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Camera, ClipboardList, ArrowRight, ArrowLeft, Loader2, Check, HeartPulse, UtensilsCrossed } from "lucide-react";
import AppShell from "@/components/app/AppShell";
import dynamic from "next/dynamic";
const VoiceRecorder = dynamic(() => import("@/components/VoiceRecorder"), { ssr: false });
import CameraCapture from "@/components/CameraCapture";
import { SYMPTOM_OPTIONS, SYMPTOM_LABELS, analyzeText, analyzeImage } from "@/lib/api";
import {
  saveAnalysis, computeScoreLabel, getAllAnalyses, getOrCreateProfile, unlockAchievements,
  type UserProfile,
} from "@/lib/db";
import { checkNewAchievements } from "@/lib/achievements";
import { toast } from "@/lib/toast";
import { generateDietPlan } from "@/lib/diet-engine";
import { RECIPE_DB } from "@/lib/recipe-db";
import { calculateNutritionTargets, type TodayActivity, type FeelingToday } from "@/lib/nutrition-engine";

const STATES = [
  "Delhi", "UP", "Punjab", "Haryana", "Rajasthan", "MP", "Bihar",
  "Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "Kerala",
  "West Bengal", "Odisha", "Assam", "Telangana", "Andhra Pradesh",
];

const STEPS = [
  { id: "symptoms", icon: Mic,             label: "Symptoms" },
  { id: "camera",   icon: Camera,          label: "Photos"   },
  { id: "medical",  icon: HeartPulse,      label: "History"  },
  { id: "kitchen",  icon: UtensilsCrossed, label: "Kitchen"  },
  { id: "details",  icon: ClipboardList,   label: "Details"  },
];

const MEDICAL_OPTIONS = [
  { id: "diabetes",     label: "Diabetes / Sugar" },
  { id: "bp_high",      label: "High BP" },
  { id: "thyroid",      label: "Thyroid" },
  { id: "pregnancy",    label: "Pregnancy / Breastfeeding" },
  { id: "kidney",       label: "Kidney Disease" },
  { id: "cholesterol",  label: "High Cholesterol" },
  { id: "anemia",       label: "Anaemia" },
  { id: "pcod",         label: "PCOD / PCOS" },
];

const KITCHEN_CHIPS = [
  "Atta", "Chawal", "Dal (moong)", "Dal (masoor)", "Dal (chana)", "Rajma",
  "Palak", "Methi", "Aloo", "Tamatar", "Pyaaz", "Lahsun", "Adrak",
  "Dahi", "Doodh", "Paneer", "Ghee", "Tel",
  "Egg", "Chicken", "Fish", "Mutton",
  "Mango", "Banana", "Papaya", "Amla", "Orange",
  "Akhrot", "Badam", "Til", "Flaxseed", "Pumpkin seeds",
  "Oats", "Bajra", "Ragi", "Brown rice",
];

export default function AnalyzePage() {
  const router = useRouter();
  const [step, setStep]   = useState(0);
  const [loading, setLoading] = useState(false);
  const [voiceTab, setVoiceTab] = useState<"voice" | "text">("voice");

  const [voiceText,         setVoiceText]         = useState("");
  const [selectedSymptoms,  setSelectedSymptoms]  = useState<string[]>([]);
  const [capturedImages,    setCapturedImages]    = useState<Record<string, File>>({});
  const [state,             setState_]            = useState("");
  const [isVeg,             setIsVeg]             = useState(false);
  const [medConditions,     setMedConditions]     = useState<string[]>([]);
  const [kitchenItems,      setKitchenItems]      = useState<string[]>([]);
  const [kitchenInput,      setKitchenInput]      = useState("");
  const [todayActivity,     setTodayActivity]     = useState<TodayActivity>("light_walk");
  const [feelingToday,      setFeelingToday]      = useState<FeelingToday>("normal");
  const [weightKg,          setWeightKg]          = useState("");
  const [heightCm,          setHeightCm]          = useState("");

  const toggleSymptom = (s: string) =>
    setSelectedSymptoms((p) => p.includes(s) ? p.filter((x) => x !== s) : [...p, s]);

  const handleCapture = (mod: string, file: File) =>
    setCapturedImages((p) => ({ ...p, [mod]: file }));

  const toggleMed = (s: string) =>
    setMedConditions((p) => p.includes(s) ? p.filter((x) => x !== s) : [...p, s]);

  const toggleKitchen = (s: string) =>
    setKitchenItems((p) => p.includes(s) ? p.filter((x) => x !== s) : [...p, s]);

  const addCustomKitchen = () => {
    const items = kitchenInput.split(/[,،]/g).map((s) => s.trim()).filter(Boolean);
    setKitchenItems((p) => [...new Set([...p, ...items])]);
    setKitchenInput("");
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const [allAnalysesPre, profile] = await Promise.all([getAllAnalyses(), getOrCreateProfile()]);

      const historyContext = allAnalysesPre.slice(0, 3)
        .flatMap((a) => a.high_risk)
        .filter((v, i, arr) => arr.indexOf(v) === i)
        .slice(0, 5)
        .join(", ");

      const medContext = medConditions.length > 0
        ? `Medical conditions: ${medConditions.join(", ")}.`
        : "";

      const ageContext = profile.age ? `Age: ${profile.age}.` : "";
      const genderContext = profile.gender ? `Gender: ${profile.gender}.` : "";

      const symptomStr = [
        voiceText,
        selectedSymptoms.map((s) => SYMPTOM_LABELS[s] || s).join(", "),
        medContext,
        ageContext,
        genderContext,
        historyContext ? `Previously deficient in: ${historyContext}.` : "",
      ].filter(Boolean).join(" ");

      const result = await analyzeText({
        voice_text: symptomStr || "general health checkup",
        state: state || undefined,
        is_vegetarian: isVeg,
        _symptoms: selectedSymptoms,
      });

      const imageResults: Record<string, Record<string, number>> = {};
      await Promise.allSettled(
        Object.entries(capturedImages).map(async ([mod, file]) => {
          const r = await analyzeImage(file, mod as any);
          imageResults[mod] = r;
        })
      );

      const score = result.balance_score?.overall_score ?? 0;
      const highRisk = result.balance_score?.high_risk_deficiencies ?? [];
      const medRisk = result.balance_score?.medium_risk_deficiencies ?? [];
      const allDeficiencies = [...highRisk, ...medRisk];

      // Merge one-time weight/height into profile for this run (don't persist yet)
      const effectiveProfile = {
        ...profile,
        weight_kg: weightKg ? parseFloat(weightKg) : profile.weight_kg,
        height_cm: heightCm ? parseFloat(heightCm) : profile.height_cm,
      };
      const occupation = profile.occupation ?? "sedentary";
      const nutritionTargets = calculateNutritionTargets(
        effectiveProfile, occupation, todayActivity, feelingToday, medConditions,
      );

      const generatedMealPlan = generateDietPlan(
        RECIPE_DB, allDeficiencies, kitchenItems, state, isVeg, medConditions, profile, nutritionTargets,
      );

      await saveAnalysis({
        timestamp: Date.now(),
        date: new Date(),
        score,
        score_label: computeScoreLabel(score),
        predictions: result.deficiency_predictions ?? [],
        high_risk: highRisk,
        medium_risk: medRisk,
        diet_plan: result.diet_plan ?? {},
        recommendations: result.recommendations ?? [],
        alerts: result.alerts ?? [],
        symptoms_text: symptomStr,
        selected_symptoms: selectedSymptoms,
        state: state || "",
        is_vegetarian: isVeg,
        image_results: imageResults,
        kitchen_items: kitchenItems,
        medical_conditions: medConditions,
      });

      sessionStorage.setItem("balanceai_meal_plan", JSON.stringify(generatedMealPlan));

      // Check achievements
      const allAnalyses = await getAllAnalyses();
      const newBadges = checkNewAchievements(allAnalyses, profile);
      if (newBadges.length > 0) {
        await unlockAchievements(newBadges.map((b) => b.id));
        sessionStorage.setItem("pending_achievement", JSON.stringify(newBadges[0]));
      }

      sessionStorage.setItem("balanceai_result", JSON.stringify({ ...result, imageResults }));
      router.push("/results");
    } catch {
      toast.error("Analysis mein error aaya. API server check karo.");
      setLoading(false);
    }
  };

  const canProceed = [
    voiceText.length > 3 || selectedSymptoms.length > 0,
    true,
    true,
    kitchenItems.length > 0,
    true,
  ];

  return (
    <AppShell>
      <div className="px-5 sm:px-8 py-8 max-w-2xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <p className="text-sm font-semibold mb-0.5" style={{ color: "rgba(255,255,255,0.35)" }}>
            Step {step + 1} of {STEPS.length}
          </p>
          <h1 className="font-display font-bold text-2xl" style={{ color: "rgba(255,255,255,0.9)" }}>
            New Analysis
          </h1>
        </motion.div>

        {/* Step indicators */}
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-2 flex-1">
              <button
                onClick={() => i < step && setStep(i)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition-all"
                style={{
                  background: i === step
                    ? "rgba(0,217,126,0.12)"
                    : i < step
                    ? "rgba(0,217,126,0.07)"
                    : "rgba(255,255,255,0.04)",
                  color: i === step
                    ? "#00d97e"
                    : i < step
                    ? "rgba(0,217,126,0.7)"
                    : "rgba(255,255,255,0.3)",
                  border: i === step
                    ? "1px solid rgba(0,217,126,0.3)"
                    : i < step
                    ? "1px solid rgba(0,217,126,0.15)"
                    : "1px solid rgba(255,255,255,0.06)",
                  cursor: i < step ? "pointer" : "default",
                }}
              >
                {i < step
                  ? <Check className="w-3 h-3" />
                  : <s.icon className="w-3 h-3" />}
                {s.label}
              </button>
              {i < STEPS.length - 1 && (
                <div
                  className="h-px flex-1 transition-all"
                  style={{ background: i < step ? "rgba(0,217,126,0.3)" : "rgba(255,255,255,0.07)" }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            transition={{ duration: 0.18 }}
          >

            {/* ── STEP 0: Symptoms ── */}
            {step === 0 && (
              <div
                className="rounded-2xl p-5 space-y-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Mic className="w-4 h-4" style={{ color: "#00d97e" }} />
                    <h2 className="font-semibold text-base" style={{ color: "rgba(255,255,255,0.9)" }}>
                      Apni takleef batao
                    </h2>
                  </div>
                  <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Voice ya text mein — Hindi ya English mein
                  </p>
                </div>

                {/* Voice / Text toggle */}
                <div
                  className="flex gap-1 p-1 rounded-xl"
                  style={{ background: "rgba(255,255,255,0.05)" }}
                >
                  {(["voice", "text"] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setVoiceTab(t)}
                      className="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                      style={{
                        background: voiceTab === t ? "rgba(0,217,126,0.12)" : "transparent",
                        color: voiceTab === t ? "#00d97e" : "rgba(255,255,255,0.4)",
                        border: voiceTab === t ? "1px solid rgba(0,217,126,0.25)" : "1px solid transparent",
                      }}
                    >
                      {t === "voice" ? "🎙️ Voice" : "⌨️ Type"}
                    </button>
                  ))}
                </div>

                {voiceTab === "voice" ? (
                  <div>
                    <VoiceRecorder
                      onTranscript={(t) => setVoiceText((p) => p ? `${p} ${t}` : t)}
                      placeholder="Mic dabao — Hindi ya English mein bolein"
                    />
                    {voiceText && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="mt-3 p-3 rounded-xl text-sm"
                        style={{ background: "rgba(0,217,126,0.06)", border: "1px solid rgba(0,217,126,0.15)" }}
                      >
                        <p className="text-xs mb-1" style={{ color: "rgba(0,217,126,0.6)" }}>Transcribed:</p>
                        <p style={{ color: "rgba(255,255,255,0.8)" }}>{voiceText}</p>
                      </motion.div>
                    )}
                  </div>
                ) : (
                  <textarea
                    value={voiceText}
                    onChange={(e) => setVoiceText(e.target.value)}
                    placeholder="Jaise: mujhe bahut thakaan rehti hai, baal gir rahe hain, raat ko neend nahi aati..."
                    rows={4}
                    className="w-full px-4 py-3 rounded-xl text-sm outline-none resize-none"
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid rgba(255,255,255,0.09)",
                      color: "rgba(255,255,255,0.85)",
                    }}
                  />
                )}

                {/* Symptom chips */}
                <div>
                  <p className="text-xs font-medium mb-3" style={{ color: "rgba(255,255,255,0.45)" }}>
                    Ya yahan se select karo:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {SYMPTOM_OPTIONS.map((s) => {
                      const sel = selectedSymptoms.includes(s);
                      return (
                        <button
                          key={s}
                          onClick={() => toggleSymptom(s)}
                          className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                          style={{
                            background: sel ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.04)",
                            border: sel ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.08)",
                            color: sel ? "#00d97e" : "rgba(255,255,255,0.55)",
                          }}
                        >
                          {SYMPTOM_LABELS[s]?.split(" / ")[1] || SYMPTOM_LABELS[s] || s}
                        </button>
                      );
                    })}
                  </div>
                  {selectedSymptoms.length > 0 && (
                    <p className="text-xs mt-2" style={{ color: "#00d97e" }}>
                      {selectedSymptoms.length} selected
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* ── STEP 1: Camera ── */}
            {step === 1 && (
              <div
                className="rounded-2xl p-5 space-y-4"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Camera className="w-4 h-4" style={{ color: "#00d97e" }} />
                    <h2 className="font-semibold text-base" style={{ color: "rgba(255,255,255,0.9)" }}>
                      Visual signs
                    </h2>
                    <span
                      className="text-[10px] px-2 py-0.5 rounded-full font-semibold ml-1"
                      style={{ background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.4)" }}
                    >
                      OPTIONAL
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Nakhun, jeebh, skin ka photo lo — AI deficiency signs detect karega.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {(["nail", "tongue", "skin", "eye"] as const).map((mod) => (
                    <div
                      key={mod}
                      className="rounded-xl overflow-hidden"
                      style={{
                        border: capturedImages[mod]
                          ? "1px solid rgba(0,217,126,0.3)"
                          : "1px solid rgba(255,255,255,0.07)",
                        background: "rgba(255,255,255,0.02)",
                      }}
                    >
                      <CameraCapture
                        modality={mod}
                        onCapture={(f) => handleCapture(mod, f)}
                        captured={!!capturedImages[mod]}
                      />
                    </div>
                  ))}
                </div>
                {Object.keys(capturedImages).length > 0 && (
                  <p className="text-xs text-center" style={{ color: "#00d97e" }}>
                    ✓ {Object.keys(capturedImages).length} photo{Object.keys(capturedImages).length > 1 ? "s" : ""} captured
                  </p>
                )}
              </div>
            )}

            {/* ── STEP 2: Medical History ── */}
            {step === 2 && (
              <div
                className="rounded-2xl p-5 space-y-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <HeartPulse className="w-4 h-4" style={{ color: "#00d97e" }} />
                    <h2 className="font-semibold text-base" style={{ color: "rgba(255,255,255,0.9)" }}>
                      Medical history
                    </h2>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold ml-1" style={{ background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.4)" }}>OPTIONAL</span>
                  </div>
                  <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Agar koi bimari hai to batao — diet plan uske hisaab se adjust hoga
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {MEDICAL_OPTIONS.map((opt) => {
                    const sel = medConditions.includes(opt.id);
                    return (
                      <button
                        key={opt.id}
                        onClick={() => toggleMed(opt.id)}
                        className="px-3 py-2 rounded-xl text-xs font-medium transition-all"
                        style={{
                          background: sel ? "rgba(239,68,68,0.1)" : "rgba(255,255,255,0.04)",
                          border: sel ? "1px solid rgba(239,68,68,0.3)" : "1px solid rgba(255,255,255,0.08)",
                          color: sel ? "#ef4444" : "rgba(255,255,255,0.55)",
                        }}
                      >
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
                {medConditions.length === 0 && (
                  <p className="text-xs" style={{ color: "rgba(255,255,255,0.25)" }}>Koi select nahi kiya → normal diet plan milega</p>
                )}
              </div>
            )}

            {/* ── STEP 3: Kitchen Items ── */}
            {step === 3 && (
              <div
                className="rounded-2xl p-5 space-y-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <UtensilsCrossed className="w-4 h-4" style={{ color: "#00d97e" }} />
                    <h2 className="font-semibold text-base" style={{ color: "rgba(255,255,255,0.9)" }}>
                      Kitchen mein kya kya hai?
                    </h2>
                  </div>
                  <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Jo available hai wo select karo — diet plan sirf unhi cheezein se banega
                  </p>
                </div>

                {/* Custom input */}
                <div className="flex gap-2">
                  <input
                    value={kitchenInput}
                    onChange={(e) => setKitchenInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addCustomKitchen()}
                    placeholder="Koi aur item type karo (comma se alag karo)..."
                    className="flex-1 px-3 py-2.5 rounded-xl text-sm outline-none"
                    style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)", color: "rgba(255,255,255,0.85)" }}
                  />
                  <button
                    onClick={addCustomKitchen}
                    className="px-4 py-2.5 rounded-xl text-sm font-semibold"
                    style={{ background: "rgba(0,217,126,0.15)", color: "#00d97e", border: "1px solid rgba(0,217,126,0.25)" }}
                  >
                    Add
                  </button>
                </div>

                <div className="flex flex-wrap gap-2">
                  {KITCHEN_CHIPS.map((item) => {
                    const sel = kitchenItems.includes(item);
                    return (
                      <button
                        key={item}
                        onClick={() => toggleKitchen(item)}
                        className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                        style={{
                          background: sel ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.04)",
                          border: sel ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.08)",
                          color: sel ? "#00d97e" : "rgba(255,255,255,0.55)",
                        }}
                      >
                        {item}
                      </button>
                    );
                  })}
                </div>

                {kitchenItems.length > 0 && (
                  <div className="rounded-xl p-3" style={{ background: "rgba(0,217,126,0.05)", border: "1px solid rgba(0,217,126,0.12)" }}>
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: "rgba(0,217,126,0.5)" }}>
                      Selected ({kitchenItems.length})
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {kitchenItems.map((k) => (
                        <span
                          key={k}
                          className="text-xs px-2 py-0.5 rounded-full cursor-pointer"
                          style={{ background: "rgba(0,217,126,0.1)", color: "#00d97e", border: "1px solid rgba(0,217,126,0.2)" }}
                          onClick={() => toggleKitchen(k)}
                        >
                          {k} ✕
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── STEP 4: Details ── */}
            {step === 4 && (
              <div
                className="rounded-2xl p-5 space-y-5"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <ClipboardList className="w-4 h-4" style={{ color: "#00d97e" }} />
                    <h2 className="font-semibold text-base" style={{ color: "rgba(255,255,255,0.9)" }}>
                      Thodi aur jaankari
                    </h2>
                  </div>
                  <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Better personalization ke liye
                  </p>
                </div>

                {/* Weight + Height */}
                <div className="grid grid-cols-2 gap-3">
                  {([ { label: "Weight (kg)", val: weightKg, set: setWeightKg, ph: "e.g. 65" },
                       { label: "Height (cm)", val: heightCm, set: setHeightCm, ph: "e.g. 165" },
                  ] as const).map((f) => (
                    <div key={f.label}>
                      <p className="text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>{f.label}</p>
                      <input
                        type="number"
                        value={f.val}
                        onChange={(e) => f.set(e.target.value)}
                        placeholder={f.ph}
                        className="w-full px-3 py-2 rounded-xl text-sm outline-none"
                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)", color: "rgba(255,255,255,0.85)" }}
                      />
                    </div>
                  ))}
                </div>

                {/* Today's activity */}
                <div>
                  <p className="text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>
                    Aaj kya kiya? (Activity)
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {([
                      { v: "rest",        l: "😴 Rest" },
                      { v: "light_walk",  l: "🚶 Walk <30min" },
                      { v: "walk_30_60",  l: "🚶 Walk 30-60min" },
                      { v: "walk_60plus", l: "🚶 Walk >60min" },
                      { v: "yoga",        l: "🧘 Yoga" },
                      { v: "gym_light",   l: "💪 Gym (light)" },
                      { v: "gym_heavy",   l: "💪 Gym (heavy)" },
                      { v: "run_30",      l: "🏃 Run ~30min" },
                      { v: "run_60plus",  l: "🏃 Run >60min" },
                      { v: "heavy_labor", l: "⛏️ Heavy work" },
                    ] as const).map(({ v, l }) => (
                      <button
                        key={v}
                        onClick={() => setTodayActivity(v)}
                        className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                        style={{
                          background: todayActivity === v ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.04)",
                          border: todayActivity === v ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.07)",
                          color: todayActivity === v ? "#00d97e" : "rgba(255,255,255,0.5)",
                        }}
                      >
                        {l}
                      </button>
                    ))}
                  </div>
                </div>

                {/* How are you feeling */}
                <div>
                  <p className="text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>
                    Aaj kaisa feel ho raha hai?
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {([
                      { v: "normal",    l: "😊 Normal" },
                      { v: "tired",     l: "😴 Thaka hua" },
                      { v: "very_tired", l: "😩 Bahut thaka" },
                      { v: "sick",      l: "🤒 Bimaar" },
                      { v: "stressed",  l: "😰 Stressed" },
                    ] as const).map(({ v, l }) => (
                      <button
                        key={v}
                        onClick={() => setFeelingToday(v)}
                        className="px-3 py-2 rounded-xl text-xs font-medium transition-all"
                        style={{
                          background: feelingToday === v ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.04)",
                          border: feelingToday === v ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.07)",
                          color: feelingToday === v ? "#00d97e" : "rgba(255,255,255,0.5)",
                        }}
                      >
                        {l}
                      </button>
                    ))}
                  </div>
                </div>

                {/* State picker */}
                <div>
                  <p className="text-xs font-semibold mb-2.5 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>
                    Aapka state
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {STATES.map((s) => (
                      <button
                        key={s}
                        onClick={() => setState_(state === s ? "" : s)}
                        className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                        style={{
                          background: state === s ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.04)",
                          border: state === s ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.07)",
                          color: state === s ? "#00d97e" : "rgba(255,255,255,0.5)",
                        }}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Diet toggle */}
                <div>
                  <p className="text-xs font-semibold mb-2.5 uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.35)" }}>
                    Diet type
                  </p>
                  <div className="flex gap-3">
                    {[
                      { label: "🥗 Vegetarian", val: true  },
                      { label: "🍗 Non-Veg",    val: false },
                    ].map((opt) => (
                      <button
                        key={String(opt.val)}
                        onClick={() => setIsVeg(opt.val)}
                        className="flex-1 py-3 rounded-xl text-sm font-semibold transition-all"
                        style={{
                          background: isVeg === opt.val ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.04)",
                          border: isVeg === opt.val ? "1px solid rgba(0,217,126,0.3)" : "1px solid rgba(255,255,255,0.07)",
                          color: isVeg === opt.val ? "#00d97e" : "rgba(255,255,255,0.5)",
                        }}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Summary */}
                <div
                  className="rounded-xl p-4 space-y-1.5 text-sm"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
                >
                  <p className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
                    Summary
                  </p>
                  {voiceText && (
                    <p style={{ color: "rgba(255,255,255,0.65)" }}>🎙️ {voiceText.slice(0, 80)}{voiceText.length > 80 ? "..." : ""}</p>
                  )}
                  {selectedSymptoms.length > 0 && (
                    <p style={{ color: "rgba(255,255,255,0.65)" }}>✓ {selectedSymptoms.length} symptoms selected</p>
                  )}
                  {Object.keys(capturedImages).length > 0 && (
                    <p style={{ color: "rgba(255,255,255,0.65)" }}>📸 {Object.keys(capturedImages).join(", ")} photos</p>
                  )}
                  {state && <p style={{ color: "rgba(255,255,255,0.65)" }}>📍 {state}</p>}
                  <p style={{ color: "rgba(255,255,255,0.65)" }}>{isVeg ? "🥗 Vegetarian" : "🍗 Non-Veg"}</p>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex gap-3 mt-6">
          {step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              className="flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium transition-all"
              style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.08)" }}
            >
              <ArrowLeft className="w-4 h-4" /> Wapas
            </button>
          )}

          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={!canProceed[step]}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all"
              style={{
                background: canProceed[step] ? "#00d97e" : "rgba(0,217,126,0.25)",
                color: canProceed[step] ? "#000" : "rgba(0,217,126,0.5)",
                cursor: canProceed[step] ? "pointer" : "not-allowed",
              }}
            >
              Aage <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-bold transition-all"
              style={{
                background: loading ? "rgba(0,217,126,0.3)" : "#00d97e",
                color: loading ? "rgba(0,217,126,0.6)" : "#000",
                boxShadow: loading ? "none" : "0 0 24px rgba(0,217,126,0.3)",
              }}
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</>
              ) : (
                <>Analysis Shuru Karo <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          )}
        </div>

        <p className="text-center text-xs mt-4" style={{ color: "rgba(255,255,255,0.2)" }}>
          Ye medical diagnosis nahi hai — doctor ki jagah use mat karo
        </p>
      </div>
    </AppShell>
  );
}
