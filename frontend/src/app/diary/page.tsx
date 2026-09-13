"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Plus, X, Send, Leaf, ChevronRight, Sparkles } from "lucide-react";
import AppShell from "@/components/app/AppShell";
import { getAllAnalyses, getOrCreateProfile, type AnalysisEntry } from "@/lib/db";
import { searchFoods, NUTRIENT_DAILY, NUTRIENT_UNITS, type FoodItem } from "@/lib/food-db";
import { RECIPE_DB } from "@/lib/recipe-db";
import { DEFICIENCY_LABELS } from "@/lib/api";

interface LogEntry { food: FoodItem; qty: number; }
interface ChatMsg   { role: "user" | "ai"; text: string; }

const MEAL_SLOTS  = ["Breakfast", "Lunch", "Snacks", "Dinner"];
const MEAL_EMOJI: Record<string, string> = { Breakfast: "🌅", Lunch: "☀️", Snacks: "🍎", Dinner: "🌙" };

// ── Seasonal recipes for September (post-monsoon India) ───────
// Seasonal produce: lauki, tinda, turai, karela, pumpkin, pomegranate, guava, banana, papaya
const SEASONAL_MONTH_RECIPES: Record<string, string[]> = {
  default:          ["Lauki Dal","Tinda Sabzi","Moong Dal Khichdi","Banana Oats Porridge","Guava Chaat","Pumpkin Sabzi","Palak Dal","Sprouts Salad"],
  Punjab:           ["Sarson Da Saag","Makki Di Roti","Lassi","Bajra Khichdi","Amritsari Dal","Aloo Gobhi","Guava Chaat","Gajar Halwa"],
  "Uttar Pradesh":  ["Dal Baati","Tehri","Moong Dal","Lauki Kofta","Kaddu Ki Sabzi","Aloo Roti","Palak Paneer","Boondi Raita"],
  Maharashtra:      ["Zunka Bhakar","Varan Bhat","Solkadhi","Pitla","Amti Dal","Kanda Poha","Puran Poli","Thalipeeth"],
  "West Bengal":    ["Khichuri","Aloo Posto","Cholar Dal","Shukto","Luchi","Begun Bhaja","Mishti Doi","Sandesh"],
  Rajasthan:        ["Dal Baati Churma","Gatte Ki Sabzi","Bajre Ki Roti","Ker Sangri","Laal Maas","Mohan Maas","Rabdi","Churma"],
  Kerala:           ["Avial","Sambar","Puttu Kadala","Erissery","Olan","Thoran","Fish Curry","Appam"],
  Karnataka:        ["Bisi Bele Bath","Ragi Mudde","Rasam","Kosambari","Vangi Bath","Neer Dosa","Akki Roti","Gojju"],
  "Tamil Nadu":     ["Sambar Rice","Rasam Rice","Kootu","Poriyal","Kuzhambu","Idli Sambar","Pongal","Avial"],
  Gujarat:          ["Thepla","Undhiyu","Khakhra","Dhokla","Kadhi","Dal Dhokli","Sev Tamatar","Bajri Rotla"],
  Delhi:            ["Chole Bhature","Dal Makhani","Paneer Tikka","Rajma Chawal","Butter Chicken","Nihari","Kulcha","Kheer"],
  Haryana:          ["Bajra Roti","Kachri Ki Sabzi","Methi Paratha","Hara Dhania Chutney","Bathua Raita","Singri Sabzi","Dal Tadka","Lassi"],
  Bihar:            ["Litti Chokha","Sattu Paratha","Dal Pithi","Thekua","Khaja","Khichdi","Kadhi Bari","Chura Dahi"],
  Odisha:           ["Dalma","Pakhala Bhata","Saga Bhaja","Chungdi Malai","Mudhi Mansa","Besara","Rasabali","Chhena Poda"],
  Assam:            ["Masor Tenga","Khar","Aloo Pitika","Duck Curry","Pitha","Til Pitha","Bamboo Shoot Curry","Ou Tenga Dal"],
};

function getSeasonalRecipes(userState: string): string[] {
  const stateKey = Object.keys(SEASONAL_MONTH_RECIPES).find(
    (k) => k !== "default" && (userState?.toLowerCase().includes(k.toLowerCase()) || k.toLowerCase().includes(userState?.toLowerCase()))
  );
  return SEASONAL_MONTH_RECIPES[stateKey ?? "default"];
}

// ── AI Chat Engine ────────────────────────────────────────────
function getAIReply(
  msg: string,
  logs: Record<string, LogEntry[]>,
  deficiencies: Set<string>,
  totals: Record<string, number>,
): string {
  const m = msg.toLowerCase();
  const allEntries = Object.values(logs).flat();
  const totalKcal  = Math.round(Object.values(logs).flat().reduce((s, e) => s + (e.food.nutrients.vitamin_c ?? 0) * 0, 0));

  // What did I eat today
  if (m.includes("kya khaya") || m.includes("aaj khaya") || m.includes("today") || m.includes("log")) {
    const names = allEntries.map((e) => e.food.name).join(", ");
    if (!names) return "Abhi kuch log nahi kiya. Breakfast se shuru karo — Breakfast slot mein + dabao!";
    return `Aaj aapne log kiya: ${names}. Nutrition analysis upar dikh raha hai! 💪`;
  }

  // Iron related
  if (m.includes("iron") || m.includes("khoon") || m.includes("anemia") || m.includes("thakaan") || m.includes("thakan")) {
    const covered = ((totals.iron ?? 0) / (NUTRIENT_DAILY.iron ?? 18)) * 100;
    return `Aapka iron ${Math.round(covered)}% cover hua hai aaj. Iron ke liye: Palak, Rajma, Kala Chana, Bajra roti, Amla. Khane ke saath nimbu paani piyo — Vitamin C iron absorption 2-3x badhata hai! 🍋`;
  }

  // Calcium / bones
  if (m.includes("calcium") || m.includes("haddi") || m.includes("bones") || m.includes("doodh")) {
    return `Calcium ke liye: Doodh (300mg/glass), Dahi (200mg), Paneer, Ragi roti, Til. Roz subah 1 glass doodh + ek katori dahi lunch mein try karo. Dhoop bhi zaroor lena — Vitamin D calcium absorb karata hai! ☀️`;
  }

  // Vitamin D
  if (m.includes("vitamin d") || m.includes("dhoop") || m.includes("sunlight")) {
    return `Vitamin D ke liye: 20-30 minute subah ki dhoop (9-11 AM), Fatty fish, Fortified milk, Mushroom (dhoop mein rakhe). Khane se zyada dhoop se milta hai — roz morning walk zaroor karo! 🌞`;
  }

  // Protein
  if (m.includes("protein") || m.includes("muscle") || m.includes("muscles") || m.includes("maansapeshi")) {
    const covered = ((totals.vitamin_b12 ?? 0) / (NUTRIENT_DAILY.vitamin_b12 ?? 2.4)) * 100;
    return `Protein ke liye: Dal (har meal mein), Rajma-Chana, Paneer, Dahi, Anda, Chicken. Roz weight x 0.8-1g protein chahiye. Ek katori dal + ek cup dahi = ~20g protein aasaani se! 💪`;
  }

  // What to eat / recommendations
  if (m.includes("kya khana") || m.includes("kya khau") || m.includes("suggest") || m.includes("batao") || m.includes("recommend") || m.includes("plan")) {
    const defList = [...deficiencies].slice(0, 3).map((d) => DEFICIENCY_LABELS[d] || d).join(", ");
    if (defList) {
      return `Tumhari deficiencies ke hisaab se (${defList}), aaj try karo:\n• Breakfast: Palak ka paratha + Dahi\n• Lunch: Dal + Brown rice + Salad\n• Snacks: Guava ya Amla\n• Dinner: Khichdi + Lauki sabzi\n\nUpar seasonal recipes bhi hain — unhe diary mein add karo! 🌿`;
    }
    return "Aaj ke liye:\n• Breakfast: Poha + Dahi\n• Lunch: Dal + Roti + Sabzi + Salad\n• Snacks: Fruit ya roasted chana\n• Dinner: Khichdi ya Dal + Roti + Light sabzi\n\nSimple, balanced Indian thali = best nutrition! 🍽️";
  }

  // Weight loss
  if (m.includes("weight") || m.includes("wajan") || m.includes("fat") || m.includes("diet")) {
    return `Weight ke liye:\n• Refined carbs kam karo (maida, white rice)\n• Dal-sabzi-roti balanced thali khao\n• Raat ka khana 8 baje se pehle\n• Dinner light rakho — khichdi ya dal roti best\n• Paani 8-10 glass\n• Walk 30 min daily\n\nCrash diet mat karo — khaana sirf sahi select karo! 🥗`;
  }

  // Dinner specific
  if (m.includes("dinner") || m.includes("raat") || m.includes("night")) {
    return `Dinner ke liye best options:\n• Dal + Roti (2) + Light sabzi (lauki/tinda/turai)\n• Moong dal khichdi — easiest to digest\n• Palak dal + Bajra roti\n• Sabzi + 2 roti\n\n❌ Avoid: Dahi, heavy fried food, biryani at night — digestion slow hoti hai! 🌙`;
  }

  // Default
  return `Aapki baat samajh gaya! Kuch specific puchna hai? Jaise:\n• "Aaj kya khaya?"\n• "Iron kaise badhau?"\n• "Dinner mein kya khau?"\n• "Weight loss ke liye kya khau?"\n\nMain aapki diet ke hisaab se personalized jawab dunga! 😊`;
}

// ── Nutrient bar ──────────────────────────────────────────────
function NutrientBar({ nutrient, covered, daily, isDeficient }: {
  nutrient: string; covered: number; daily: number; isDeficient: boolean;
}) {
  const pct   = Math.min((covered / daily) * 100, 100);
  const color = pct < 33 ? "#ef4444" : pct < 66 ? "#f59e0b" : "#00d97e";
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-medium" style={{ color: isDeficient ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.5)" }}>
          {DEFICIENCY_LABELS[nutrient] || nutrient}
          {isDeficient && <span className="ml-1 text-[9px] font-bold" style={{ color: "#ef4444" }}>●</span>}
        </span>
        <span className="text-[10px] font-bold" style={{ color }}>
          {covered.toFixed(1)}/{daily}{NUTRIENT_UNITS[nutrient]}
        </span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <motion.div className="h-full rounded-full" style={{ background: color }} animate={{ width: `${pct}%` }} transition={{ duration: 0.4 }} />
      </div>
    </div>
  );
}

const FOCUS_NUTRIENTS = ["iron","vitamin_b12","vitamin_d","calcium","zinc","omega3","folate","magnesium","vitamin_c","vitamin_a"];

export default function DiaryPage() {
  const [analysis,    setAnalysis]    = useState<AnalysisEntry | null>(null);
  const [userState,   setUserState]   = useState("");
  const [logs,        setLogs]        = useState<Record<string, LogEntry[]>>({ Breakfast: [], Lunch: [], Snacks: [], Dinner: [] });
  const [activeMeal,  setActiveMeal]  = useState("Breakfast");
  const [query,       setQuery]       = useState("");
  const [searchRes,   setSearchRes]   = useState<FoodItem[]>([]);
  const [showSearch,  setShowSearch]  = useState(false);
  const [chatMsgs,    setChatMsgs]    = useState<ChatMsg[]>([
    { role: "ai", text: "Namaste! 🌿 Main BalanceAI hoon. Aaj kya log kiya? Kuch puchna ho toh type karo — jaise 'aaj kya khaya', 'iron kaise badhau', 'dinner mein kya khau'!" }
  ]);
  const [chatInput,   setChatInput]   = useState("");
  const [aiTyping,    setAiTyping]    = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([getAllAnalyses(), getOrCreateProfile()]).then(([analyses, profile]) => {
      setAnalysis(analyses[0] ?? null);
      setUserState(profile.name ? "" : ""); // profile might have state info
      // Try to get state from last analysis
      if (analyses[0]?.state) setUserState(analyses[0].state);
    });
  }, []);

  // Fuzzy search
  useEffect(() => {
    if (query.length > 0) setSearchRes(searchFoods(query, RECIPE_DB));
    else setSearchRes([]);
  }, [query]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatMsgs]);

  const addFood = (food: FoodItem) => {
    setLogs((prev) => ({ ...prev, [activeMeal]: [...prev[activeMeal], { food, qty: 1 }] }));
    setQuery(""); setSearchRes([]); setShowSearch(false);
  };

  const removeFood = (meal: string, idx: number) =>
    setLogs((prev) => ({ ...prev, [meal]: prev[meal].filter((_, i) => i !== idx) }));

  const allEntries = useMemo(() => Object.values(logs).flat(), [logs]);

  const totals = useMemo(() => {
    const t: Record<string, number> = {};
    allEntries.forEach(({ food, qty }) =>
      Object.entries(food.nutrients).forEach(([k, v]) => { t[k] = (t[k] ?? 0) + (v ?? 0) * qty; })
    );
    return t;
  }, [allEntries]);

  const deficientSet = useMemo(() => new Set([
    ...(analysis?.high_risk ?? []),
    ...(analysis?.medium_risk ?? []),
  ]), [analysis]);

  const focusNutrients = FOCUS_NUTRIENTS.filter((n) => deficientSet.has(n) || allEntries.length > 0).slice(0, 6);

  const coveragePct = focusNutrients.length > 0
    ? Math.round(
        focusNutrients.reduce((s, n) => s + Math.min(((totals[n] ?? 0) / (NUTRIENT_DAILY[n] ?? 1)) * 100, 100), 0) /
        focusNutrients.length
      )
    : 0;

  // Experience narrative
  const experience = useMemo(() => {
    if (allEntries.length === 0) return null;
    const covered = focusNutrients.filter((n) => (totals[n] ?? 0) / (NUTRIENT_DAILY[n] ?? 1) >= 0.5);
    const missing = focusNutrients.filter((n) => (totals[n] ?? 0) / (NUTRIENT_DAILY[n] ?? 1) < 0.3 && deficientSet.has(n));
    const lines: string[] = [];
    if (covered.length > 0) lines.push(`✅ ${covered.map((n) => DEFICIENCY_LABELS[n] || n).join(", ")} — 50%+ cover ho gaya!`);
    if (missing.length > 0) lines.push(`⚠️ ${missing.map((n) => DEFICIENCY_LABELS[n] || n).join(", ")} — aur chahiye aaj`);
    if (coveragePct >= 70) lines.push("🎉 Bahut acha! Aaj ka nutrition great hai.");
    else if (coveragePct >= 40) lines.push("💪 Theek hai, thoda aur achha ho sakta hai.");
    else lines.push("🌿 Abhi gap hai — kuch aur add karo.");
    return lines;
  }, [allEntries, totals, focusNutrients, deficientSet, coveragePct]);

  // Today's remaining plan
  const todayPlan = useMemo(() => {
    const missing = focusNutrients
      .filter((n) => (totals[n] ?? 0) / (NUTRIENT_DAILY[n] ?? 1) < 0.6 && deficientSet.has(n))
      .slice(0, 3);
    if (missing.length === 0) return null;
    const planMap: Record<string, string> = {
      iron:        "Raat ko: Palak dal + Bajra roti + Nimbu paani",
      vitamin_b12: "Raat ko: Dahi (lunch) + Egg/Paneer dish",
      vitamin_d:   "Kal subah: 20 min dhoop + Fortified milk",
      calcium:     "Lunch: 1 katori Dahi ya Doodh",
      zinc:        "Snacks: Kaju/Pumpkin seeds + Dahi",
      omega3:      "Raat ko: Flaxseed ki chutney ya Akhrot",
      magnesium:   "Raat ko: Akhrot + Palak sabzi",
      folate:      "Aaj: Hara dhaniya + Rajma dal",
      vitamin_c:   "Abhi: Amla/Guava/Orange ya Nimbu paani",
      vitamin_a:   "Raat ko: Gajar sabzi ya Papaya",
    };
    return missing.map((n) => planMap[n] ?? `${DEFICIENCY_LABELS[n] || n} ke liye rich foods lo`);
  }, [totals, focusNutrients, deficientSet]);

  const sendChat = () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatMsgs((p) => [...p, { role: "user", text: userMsg }]);
    setChatInput("");
    setAiTyping(true);
    setTimeout(() => {
      const reply = getAIReply(userMsg, logs, deficientSet, totals);
      setChatMsgs((p) => [...p, { role: "ai", text: reply }]);
      setAiTyping(false);
    }, 900);
  };

  const seasonalRecipes = useMemo(() => getSeasonalRecipes(userState), [userState]);

  // Find recipe in DB by name (partial match)
  const findRecipeInDB = (name: string): FoodItem | null => {
    const nl = name.toLowerCase();
    return RECIPE_DB.find((r) => r.name.toLowerCase().includes(nl.split(" ")[0])) ?? null;
  };

  return (
    <AppShell>
      <div className="px-4 sm:px-8 py-8 max-w-3xl mx-auto space-y-6">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <p className="text-xs font-semibold uppercase tracking-widest mb-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>
            Aaj ka — {new Date().toLocaleDateString("hi-IN", { weekday: "long", day: "numeric", month: "long" })}
          </p>
          <h1 className="font-display font-bold text-2xl" style={{ color: "rgba(255,255,255,0.9)" }}>Food Diary</h1>
        </motion.div>

        {/* Coverage ring */}
        <motion.div
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
          className="rounded-2xl p-5 flex items-center gap-5"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div className="relative w-20 h-20 shrink-0">
            <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
              <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              <circle cx="40" cy="40" r="32" fill="none"
                stroke={coveragePct > 60 ? "#00d97e" : coveragePct > 30 ? "#f59e0b" : "#ef4444"}
                strokeWidth="8" strokeLinecap="round" strokeDasharray={`${coveragePct * 2.01} 201`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-lg font-black font-display" style={{ color: coveragePct > 60 ? "#00d97e" : "#f59e0b" }}>
                {coveragePct}%
              </span>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold mb-1" style={{ color: "rgba(255,255,255,0.85)" }}>Daily Nutrient Coverage</p>
            {experience ? (
              <div className="space-y-0.5">
                {experience.map((line, i) => (
                  <p key={i} className="text-xs" style={{ color: "rgba(255,255,255,0.55)" }}>{line}</p>
                ))}
              </div>
            ) : (
              <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>Khaana log karo — gap track hoga</p>
            )}
          </div>
        </motion.div>

        {/* Nutrient bars */}
        {focusNutrients.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}
            className="rounded-2xl p-5"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
          >
            <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "rgba(255,255,255,0.3)" }}>
              Aaj ka Nutrient Status
            </p>
            <div className="space-y-3">
              {focusNutrients.map((n) => (
                <NutrientBar key={n} nutrient={n} covered={totals[n] ?? 0} daily={NUTRIENT_DAILY[n]} isDeficient={deficientSet.has(n)} />
              ))}
            </div>
          </motion.div>
        )}

        {/* Today's Plan (if gaps remain) */}
        {todayPlan && todayPlan.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="rounded-2xl p-4"
            style={{ background: "rgba(0,217,126,0.04)", border: "1px solid rgba(0,217,126,0.12)" }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-3.5 h-3.5" style={{ color: "#00d97e" }} />
              <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: "#00d97e" }}>Aaj ka Baaki Plan</p>
            </div>
            <div className="space-y-1.5">
              {todayPlan.map((line, i) => (
                <p key={i} className="text-xs" style={{ color: "rgba(255,255,255,0.65)" }}>• {line}</p>
              ))}
            </div>
          </motion.div>
        )}

        {/* Seasonal Recipes */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
          <div className="flex items-center gap-2 mb-3">
            <Leaf className="w-4 h-4" style={{ color: "#00d97e" }} />
            <p className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.8)" }}>
              September Seasonal Recipes {userState ? `— ${userState}` : ""}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {seasonalRecipes.map((name, i) => {
              const recipe = findRecipeInDB(name);
              return (
                <button
                  key={i}
                  onClick={() => {
                    if (recipe) { setActiveMeal("Lunch"); addFood(recipe); }
                    else setQuery(name.split(" ")[0]);
                  }}
                  className="flex items-center justify-between p-3 rounded-xl text-left gap-2"
                  style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate" style={{ color: "rgba(255,255,255,0.8)" }}>{name}</p>
                    {recipe && (
                      <p className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                        {recipe.category}
                      </p>
                    )}
                  </div>
                  <Plus className="w-3.5 h-3.5 shrink-0" style={{ color: "#00d97e" }} />
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Meal slots */}
        <div className="space-y-3">
          {MEAL_SLOTS.map((meal) => (
            <motion.div
              key={meal}
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
              className="rounded-2xl p-4"
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm">{MEAL_EMOJI[meal]}</span>
                  <p className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.75)" }}>{meal}</p>
                  {logs[meal].length > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold" style={{ background: "rgba(0,217,126,0.1)", color: "#00d97e" }}>
                      {logs[meal].length} items
                    </span>
                  )}
                </div>
                <button
                  onClick={() => { setActiveMeal(meal); setShowSearch(true); setTimeout(() => document.getElementById("diary-search")?.focus(), 100); }}
                  className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg font-medium"
                  style={{ background: "rgba(0,217,126,0.08)", border: "1px solid rgba(0,217,126,0.15)", color: "#00d97e" }}
                >
                  <Plus className="w-3 h-3" /> Add
                </button>
              </div>

              {logs[meal].length === 0 ? (
                <p className="text-xs" style={{ color: "rgba(255,255,255,0.2)" }}>
                  {meal === "Breakfast" ? "Poha, Paratha, Dalia, Idli..." :
                   meal === "Lunch"     ? "Dal + Roti + Sabzi + Salad..." :
                   meal === "Snacks"    ? "Fruits, Nuts, Roasted Chana..." :
                                         "Khichdi, Dal + Roti, Light Sabzi..."}
                </p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {logs[meal].map((e, i) => (
                    <div key={i} className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg"
                      style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.7)" }}>
                      {e.food.name}
                      <button onClick={() => removeFood(meal, i)} style={{ color: "rgba(255,255,255,0.25)" }}>
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* AI Chat */}
        <motion.div
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18 }}
          className="rounded-2xl overflow-hidden"
          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
            <Sparkles className="w-3.5 h-3.5" style={{ color: "#00d97e" }} />
            <p className="text-xs font-semibold" style={{ color: "rgba(255,255,255,0.6)" }}>BalanceAI — Nutrition Chat</p>
          </div>

          <div className="p-4 space-y-3 max-h-64 overflow-y-auto">
            {chatMsgs.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className="max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed whitespace-pre-line"
                  style={{
                    background: msg.role === "user" ? "rgba(0,217,126,0.12)" : "rgba(255,255,255,0.05)",
                    color: msg.role === "user" ? "#00d97e" : "rgba(255,255,255,0.75)",
                    borderBottomRightRadius: msg.role === "user" ? 4 : undefined,
                    borderBottomLeftRadius: msg.role === "ai" ? 4 : undefined,
                  }}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {aiTyping && (
              <div className="flex justify-start">
                <div className="rounded-2xl rounded-bl-sm px-3.5 py-2.5" style={{ background: "rgba(255,255,255,0.05)" }}>
                  <div className="flex gap-1">
                    {[0, 1, 2].map((d) => (
                      <motion.div key={d} className="w-1.5 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.3)" }}
                        animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, delay: d * 0.2, repeat: Infinity }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="px-4 pb-4">
            <div className="flex gap-2 items-center">
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendChat()}
                placeholder="Kuch poochho... 'iron kaise badhau', 'aaj ka plan'"
                className="flex-1 bg-transparent text-xs outline-none py-2.5 px-3.5 rounded-xl"
                style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.8)", border: "1px solid rgba(255,255,255,0.08)" }}
              />
              <button
                onClick={sendChat}
                className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: "rgba(0,217,126,0.15)", color: "#00d97e" }}
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
            {/* Quick prompts */}
            <div className="flex gap-1.5 mt-2 flex-wrap">
              {["Aaj ka plan", "Iron kaise badhau", "Dinner mein kya khau"].map((q) => (
                <button key={q} onClick={() => { setChatInput(q); }}
                  className="text-[10px] px-2 py-1 rounded-full"
                  style={{ background: "rgba(255,255,255,0.04)", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.07)" }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Search overlay */}
        <AnimatePresence>
          {showSearch && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex flex-col"
              style={{ background: "rgba(6,6,10,0.97)" }}
            >
              <div className="max-w-lg mx-auto w-full px-4 pt-8 pb-4 flex-1 flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <p className="text-sm font-bold flex-1" style={{ color: "rgba(255,255,255,0.85)" }}>
                    {MEAL_EMOJI[activeMeal]} {activeMeal} mein add karo
                  </p>
                  <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                    {activeMeal === "Dinner" ? "Raat: Dal, Roti, Sabzi" :
                     activeMeal === "Snacks" ? "Fruits, Nuts, Light snacks" :
                     activeMeal === "Breakfast" ? "Poha, Paratha, Dalia, Idli" : "Dal, Roti, Sabzi, Salad"}
                  </p>
                  <button onClick={() => { setShowSearch(false); setQuery(""); }} style={{ color: "rgba(255,255,255,0.4)" }}>
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl mb-4"
                  style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)" }}>
                  <Search className="w-4 h-4 shrink-0" style={{ color: "rgba(255,255,255,0.3)" }} />
                  <input
                    id="diary-search"
                    autoFocus
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Dal, roti, palak, alu, egg, chicken... galat spelling bhi chalegi"
                    className="flex-1 bg-transparent text-sm outline-none"
                    style={{ color: "rgba(255,255,255,0.85)" }}
                  />
                  {query && <button onClick={() => setQuery("")} style={{ color: "rgba(255,255,255,0.3)" }}><X className="w-4 h-4" /></button>}
                </div>

                {/* Quick chips by meal */}
                {!query && (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {(activeMeal === "Breakfast"
                      ? ["Poha","Upma","Paratha","Idli","Dalia","Oats","Egg"]
                      : activeMeal === "Lunch"
                      ? ["Dal","Roti","Sabzi","Rice","Rajma","Chole","Paneer"]
                      : activeMeal === "Snacks"
                      ? ["Banana","Apple","Guava","Peanut","Kaju","Sprouts","Chana"]
                      : ["Khichdi","Dal","Roti","Palak","Lauki","Moong"]
                    ).map((chip) => (
                      <button key={chip} onClick={() => setQuery(chip)}
                        className="text-xs px-2.5 py-1 rounded-full"
                        style={{ background: "rgba(0,217,126,0.06)", color: "#00d97e", border: "1px solid rgba(0,217,126,0.15)" }}>
                        {chip}
                      </button>
                    ))}
                  </div>
                )}

                <div className="flex-1 overflow-y-auto space-y-2">
                  {(searchRes.length > 0 ? searchRes
                    : query.length === 0
                    ? [...RECIPE_DB].slice(0, 12)
                    : []
                  ).map((food) => (
                    <button key={food.id} onClick={() => addFood(food)}
                      className="w-full flex items-center justify-between p-3 rounded-xl text-left"
                      style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <div>
                        <p className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.85)" }}>
                          {food.name}
                          {food.hindi && <span className="ml-2 text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>{food.hindi}</span>}
                        </p>
                        <p className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                          {food.serving} · {food.category} {food.state ? `· ${food.state.replace(/_/g," ")}` : ""}
                        </p>
                      </div>
                      <div className="flex gap-1 shrink-0 ml-2">
                        {Object.entries(food.nutrients)
                          .filter(([k, v]) => (v ?? 0) > 0 && deficientSet.has(k))
                          .slice(0, 2)
                          .map(([k]) => (
                            <span key={k} className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                              style={{ background: "rgba(0,217,126,0.1)", color: "#00d97e" }}>
                              {(DEFICIENCY_LABELS[k] || k).split(" ")[0]}
                            </span>
                          ))}
                      </div>
                    </button>
                  ))}
                  {query.length > 0 && searchRes.length === 0 && (
                    <div className="text-center py-8">
                      <p className="text-sm mb-1" style={{ color: "rgba(255,255,255,0.4)" }}>"{query}" nahi mila</p>
                      <p className="text-xs" style={{ color: "rgba(255,255,255,0.2)" }}>Try: dal, roti, sabzi, fruit, paneer</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </AppShell>
  );
}
