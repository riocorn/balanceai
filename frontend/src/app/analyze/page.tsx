"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Loader2, User, Users, Leaf, ChevronDown } from "lucide-react";
import Link from "next/link";
import dynamic from "next/dynamic";
const VoiceRecorder = dynamic(() => import("@/components/VoiceRecorder"), { ssr: false });
import { SYMPTOM_OPTIONS, SYMPTOM_LABELS, analyzeText, analyzeImage, type ImageAnalysisResult } from "@/lib/api";
import {
  saveAnalysis, computeScoreLabel, getAllAnalyses, getOrCreateProfile, unlockAchievements,
} from "@/lib/db";
import { checkNewAchievements } from "@/lib/achievements";
import { toast } from "@/lib/toast";
import { generateDietPlan } from "@/lib/diet-engine";
import { RECIPE_DB } from "@/lib/recipe-db";
import { calculateNutritionTargets, type TodayActivity, type FeelingToday } from "@/lib/nutrition-engine";
import CameraCapture from "@/components/CameraCapture";
import { STATE_LIST, getCities, INDIA_LOCATIONS } from "@/lib/india-locations";
import { COMPREHENSIVE_FOOD_DB_RAW, COMPREHENSIVE_FOOD_DB, ALL_FOOD_ALIASES } from "@/lib/comprehensive-food-db";
import { NUTRIENT_UNITS } from "@/lib/food-db";
import {
  BIOMARKER_MAP, BALANCEAI_PANEL_TESTS, parseBiomarkerDeficiencies,
  getBiomarkerAlerts, type BloodValues,
} from "@/lib/blood-biomarker-map";
import {
  SYMPTOM_CATEGORIES, FREQ_OPTIONS, SEVERITY_OPTIONS, computeSymptomClusters,
  RED_FLAG_SYMPTOMS, checkStaticRedFlags, checkInfectionPatterns, getSymptomDeficiencies,
  type SymptomLog, type SymptomFreq, type SymptomSeverity,
} from "@/lib/symptom-disease-map";
import { runNutrientFusion, fusionToDeficiencyList } from "@/lib/nutrient-fusion-engine";
import { getMealPhotoHistory } from "@/lib/db";

const GREEN  = "#1d5c3d";
const AMBER  = "#d4a043";
const WHITE  = "#ffffff";
const TEXT   = "#1a1a1a";
const SUB    = "#3d5249";
const MUTED  = "#8a9a8e";
const BORDER = "#e4e7e2";
const BG     = "#f7f8f6";

const STEPS = [
  { id: "details",     label: "Step 1: Your Details"             },
  { id: "ingredients", label: "Step 2: Ingredients (optional)"   },
];

const MEDICAL_OPTIONS = [
  "Diabetes / Sugar", "High BP", "Thyroid", "Pregnancy / Breastfeeding",
  "Kidney Disease", "High Cholesterol", "Anaemia", "PCOD / PCOS",
];

// Layer 1: Last 3 months health history — illnesses & symptoms
const HISTORY_OPTIONS = [
  "Viral Fever", "Cold / Cough (Recurrent)", "Food Poisoning / Diarrhea",
  "Typhoid", "Dengue", "UTI (Urine Infection)", "Jaundice", "Malaria",
  "Weakness / Fatigue", "Hair Fall", "Joint / Bone Pain", "Muscle Cramps",
  "Bleeding Gums", "Mouth Ulcers", "Breathlessness", "Skin Rashes / Dryness",
  "Eye Problems", "Sleep Problems", "Mood Swings / Anxiety", "Brain Fog / Poor Focus",
];

// Maps each history item to the nutrients it depletes / signals deficiency of
const HISTORY_TO_NUTRIENTS: Record<string, string[]> = {
  "Viral Fever":                  ["zinc", "vitamin_c", "vitamin_a", "selenium", "vitamin_d"],
  "Cold / Cough (Recurrent)":     ["vitamin_c", "zinc", "vitamin_d", "vitamin_a", "selenium"],
  "Food Poisoning / Diarrhea":    ["zinc", "potassium", "folate", "vitamin_b12", "magnesium"],
  "Typhoid":                      ["zinc", "vitamin_c", "iron", "vitamin_a", "protein"],
  "Dengue":                       ["vitamin_c", "folate", "zinc", "iron", "vitamin_k"],
  "UTI (Urine Infection)":        ["vitamin_c", "vitamin_a", "zinc"],
  "Jaundice":                     ["vitamin_k", "vitamin_e", "selenium", "zinc", "vitamin_b12"],
  "Malaria":                      ["iron", "folate", "zinc", "vitamin_b12", "vitamin_c"],
  "Weakness / Fatigue":           ["iron", "vitamin_b12", "vitamin_d", "magnesium", "folate"],
  "Hair Fall":                    ["iron", "zinc", "vitamin_b7", "folate", "vitamin_d"],
  "Joint / Bone Pain":            ["vitamin_d", "calcium", "omega3", "magnesium", "vitamin_k"],
  "Muscle Cramps":                ["magnesium", "potassium", "calcium", "vitamin_d"],
  "Bleeding Gums":                ["vitamin_c", "vitamin_k", "calcium", "zinc"],
  "Mouth Ulcers":                 ["vitamin_b12", "folate", "iron", "zinc", "vitamin_c"],
  "Breathlessness":               ["iron", "vitamin_b12", "vitamin_d", "omega3"],
  "Skin Rashes / Dryness":        ["zinc", "vitamin_a", "omega3", "vitamin_e", "vitamin_c"],
  "Eye Problems":                 ["vitamin_a", "vitamin_c", "vitamin_e", "zinc", "omega3"],
  "Sleep Problems":               ["magnesium", "vitamin_b6", "vitamin_d", "vitamin_b3"],
  "Mood Swings / Anxiety":        ["omega3", "magnesium", "vitamin_b12", "folate", "vitamin_d", "zinc"],
  "Brain Fog / Poor Focus":       ["omega3", "vitamin_b12", "folate", "vitamin_d", "zinc"],
};

function getHistoryDeficiencies(history: string[]): string[] {
  const defs = new Set<string>();
  for (const h of history) {
    (HISTORY_TO_NUTRIENTS[h] ?? []).forEach((n) => defs.add(n));
  }
  return Array.from(defs);
}

// Real ingredient names from the ICMR-NIN/USDA-sourced database, grouped into our
// 6 UI buckets — used only to power search (so anything in the real database is
// findable even though each category shows just a handful of common chips by default).
const DB_CATEGORY_TO_UI: Record<string, string> = {
  Dal: "Proteins", Grain: "Carbs", Nuts: "Fats", Seeds: "Fats",
  Sabzi: "Veggies", Fruit: "Fruit", "Dry Fruits": "Treats & Enticers",
  Protein: "Proteins", Oil: "Fats", Dairy: "Treats & Enticers", Sweetener: "Treats & Enticers",
};
const DB_NAMES_BY_UI_CATEGORY: Record<string, string[]> = {};
COMPREHENSIVE_FOOD_DB_RAW.forEach((f) => {
  const uiCat = DB_CATEGORY_TO_UI[f.category];
  if (!uiCat) return;
  const clean = f.name.replace(/\s*\([^)]*\)\s*$/, "").trim();
  (DB_NAMES_BY_UI_CATEGORY[uiCat] ??= []).push(clean);
});

const KITCHEN_CATEGORIES: { name: string; required?: boolean; items: string[]; searchItems: string[] }[] = [
  { name: "Proteins", required: true, items: ["Moong Dal", "Paneer", "Egg", "Chicken", "Fish"],
    searchItems: ["Masoor Dal", "Chana Dal", "Rajma", "Mutton", "Paneer", "Egg", "Chicken", "Fish"] },
  { name: "Carbs", items: ["Gehu Atta", "Chawal", "Oats"],
    searchItems: ["Gehu Atta", "Chawal", "Oats", "Bajra", "Ragi", "Brown Rice"] },
  { name: "Fats", items: ["Ghee", "Tel", "Badam"],
    searchItems: ["Ghee", "Tel", "Akhrot", "Badam", "Til", "Flaxseed"] },
  { name: "Veggies", items: ["Palak", "Aloo", "Tamatar", "Pyaz"],
    searchItems: ["Palak", "Methi", "Aloo", "Tamatar", "Pyaz", "Lehsun", "Adrak"] },
  { name: "Fruit", items: ["Mango", "Banana", "Orange"],
    searchItems: ["Mango", "Banana", "Papaya", "Amla", "Orange"] },
  { name: "Treats & Enticers", items: ["Dahi", "Doodh"],
    searchItems: ["Dahi", "Doodh", "Pumpkin Seeds"] },
].map((cat) => ({
  ...cat,
  searchItems: [...new Set([...cat.searchItems, ...(DB_NAMES_BY_UI_CATEGORY[cat.name] ?? [])])],
}));

const NUTRIENT_LABELS: Record<string, string> = {
  protein: "Protein", fiber: "Fiber", energy: "Energy",
  iron: "Iron", vitamin_b12: "Vitamin B12", vitamin_d: "Vitamin D", calcium: "Calcium",
  magnesium: "Magnesium", zinc: "Zinc", vitamin_c: "Vitamin C", vitamin_a: "Vitamin A",
  folate: "Folate", omega3: "Omega-3", selenium: "Selenium", vitamin_b6: "Vitamin B6",
  potassium: "Potassium", phosphorus: "Phosphorus", vitamin_b1: "Vitamin B1 (Thiamin)",
  vitamin_b2: "Vitamin B2 (Riboflavin)", vitamin_b3: "Vitamin B3 (Niacin)",
  vitamin_e: "Vitamin E", iodine: "Iodine", copper: "Copper", manganese: "Manganese",
  chromium: "Chromium", vitamin_k: "Vitamin K", vitamin_b5: "Vitamin B5 (Pantothenic Acid)",
  vitamin_b7: "Vitamin B7 (Biotin)",
};

// "soaked 4hr" -> "Soaked 4hr", "cooked (curry)" -> "Cooked (Curry)" — a clean,
// consistently capitalised label rather than the raw internal state key.
function formatStateLabel(state: string): string {
  return state.replace(/\b\w/g, (c) => c.toUpperCase());
}

// Look up every prep-state variant of a kitchen-chip ingredient in the real
// ICMR-NIN/USDA-sourced database, for the "ⓘ" full-nutrition-panel popup.
// Names in the database are now full USDA-style descriptors (e.g. "Beans, mung,
// mature seeds, split, raw") that no longer contain the short chip label as a
// substring, so matching goes through the alias table (short common names like
// "moong", "atta", "pyaz") instead of the display name.
function findIngredientStates(displayName: string) {
  const clean = displayName.replace(/\s*\([^)]*\)\s*$/, "").trim().toLowerCase();
  let baseId: string | undefined = ALL_FOOD_ALIASES[clean];
  if (!baseId) {
    const aliasEntries = Object.entries(ALL_FOOD_ALIASES).sort((a, b) => b[0].length - a[0].length);
    const hit = aliasEntries.find(([alias]) => clean.includes(alias) || alias.includes(clean));
    baseId = hit?.[1];
  }
  // Fallback: match against the ingredient's own id (e.g. "pyaz", "chawal") in
  // case its exact spelling isn't in the alias list.
  if (!baseId) {
    const cleanId = clean.replace(/\s+/g, "_");
    const idHit = COMPREHENSIVE_FOOD_DB_RAW.find((f) => {
      const bId = (f as { baseId?: string }).baseId ?? "";
      return bId === cleanId || bId.replace(/_/g, "") === cleanId.replace(/_/g, "");
    });
    baseId = (idHit as { baseId?: string } | undefined)?.baseId;
  }
  if (!baseId) return null;
  const base = COMPREHENSIVE_FOOD_DB_RAW.find((f) => (f as { baseId?: string }).baseId === baseId);
  if (!base) return null;
  const variants = COMPREHENSIVE_FOOD_DB.filter((f) => (f as { baseId?: string }).baseId === baseId);
  variants.sort((a, b) => (a.state ? 1 : 0) - (b.state ? 1 : 0));
  return { hindi: base.hindi, professionalName: base.name, variants };
}


type PersonProfile = {
  name: string;
  gender: "male" | "female" | "other" | "";
  ageYr: string;
  weightKg: string;
  heightCm: string;
  medConditions: string[];
  healthHistory: string[];
  isVeg: boolean;
  state: string;
  city: string;
};

const EMPTY_PERSON = (): PersonProfile => ({
  name: "", gender: "", ageYr: "", weightKg: "", heightCm: "",
  medConditions: [], healthHistory: [], isVeg: false, state: "", city: "",
});

const MEMBER_LABELS = ["Adult", "Child", "Elderly", "Member 4"];

const DOC_KEYS = ["medicines", "blood_test", "prescription"] as const;
type DocKey = typeof DOC_KEYS[number];

const fileToBase64 = (file: File): Promise<string> =>
  new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result as string);
    r.onerror = rej;
    r.readAsDataURL(file);
  });

const base64ToFile = (data: string, name: string, type: string): File => {
  const [, b64] = data.split(",");
  const bytes = atob(b64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  return new File([arr], name, { type });
};

const lsDocKey = (personIdx: number, key: string) => `bai_doc_${personIdx}_${key}`;

const saveDocToLS = async (personIdx: number, key: string, file: File) => {
  try {
    const data = await fileToBase64(file);
    localStorage.setItem(lsDocKey(personIdx, key), JSON.stringify({ name: file.name, type: file.type, data }));
  } catch { /* quota exceeded — session only */ }
};

const loadDocsFromLS = (personIdx: number): Record<string, File> => {
  const out: Record<string, File> = {};
  for (const k of DOC_KEYS) {
    try {
      const raw = localStorage.getItem(lsDocKey(personIdx, k));
      if (!raw) continue;
      const { name, type, data } = JSON.parse(raw);
      if (data) out[k] = base64ToFile(data, name, type);
    } catch {}
  }
  return out;
};

const inputCls = "w-full px-4 py-3 rounded-lg text-sm outline-none";
const inputStyle = { background: WHITE, border: `1px solid ${BORDER}`, color: TEXT };

function Chip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
      style={active
        ? { background: "#eef7f2", border: `1px solid #b6ddc9`, color: GREEN }
        : { background: WHITE, border: `1px solid ${BORDER}`, color: SUB }}>
      {label}
    </button>
  );
}

export default function AnalyzePage() {
  const router = useRouter();
  const [step, setStep]           = useState(0);
  const [loading, setLoading]     = useState(false);
  const [voiceTab, setVoiceTab]   = useState<"voice" | "text">("voice");
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const openDropdown  = (label: string) => { if (closeTimer.current) clearTimeout(closeTimer.current); setActiveDropdown(label); };
  const closeDropdown = () => { closeTimer.current = setTimeout(() => setActiveDropdown(null), 150); };

  /* ── 4 person profiles ── */
  const [persons,        setPersons]       = useState<PersonProfile[]>(() => {
    try {
      const saved = localStorage.getItem("balanceai_persons");
      if (saved) return JSON.parse(saved) as PersonProfile[];
    } catch {}
    return [EMPTY_PERSON(), EMPTY_PERSON(), EMPTY_PERSON(), EMPTY_PERSON()];
  });
  const [selectedPerson, setSelectedPerson] = useState(0);

  /* ── form fields (synced with persons[selectedPerson]) ── */
  const [gender,        setGender]        = useState<"male"|"female"|"other"|"">(persons[0].gender);
  const [petName,       setPetName]       = useState(persons[0].name);
  const [weightKg,      setWeightKg]      = useState(persons[0].weightKg);
  const [heightCm,      setHeightCm]      = useState(persons[0].heightCm);
  const [ageYr,         setAgeYr]         = useState(persons[0].ageYr);
  const [medSearch,     setMedSearch]     = useState("");
  const [medConditions, setMedConditions] = useState<string[]>(persons[0].medConditions);
  const [healthHistory, setHealthHistory] = useState<string[]>(persons[0].healthHistory ?? []);
  const [isVeg,         setIsVeg]         = useState(persons[0].isVeg);
  const [state,         setState_]        = useState(persons[0].state);
  const [city,          setCity]          = useState(persons[0].city);

  /* ── symptoms + session state ── */
  const [voiceText,        setVoiceText]        = useState("");
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [kitchenItems,     setKitchenItems]     = useState<string[]>([]);
  const [expandedCat,      setExpandedCat]      = useState<string | null>(null);
  const [onePotOnly,       setOnePotOnly]       = useState(false);
  const [excludeItems,     setExcludeItems]     = useState<string[]>([]);
  const [excludeInput,     setExcludeInput]     = useState("");
  const [ingredientSearch, setIngredientSearch] = useState("");
  const [infoItem, setInfoItem] = useState<string | null>(null);
  const [loadingStage, setLoadingStage] = useState(0);
  const [todayActivity,    setTodayActivity]    = useState<TodayActivity>("light_walk");
  const [feelingToday,     setFeelingToday]     = useState<FeelingToday>("normal");
  const [capturedImages,   setCapturedImages]   = useState<Record<string, File>>({});
  const [medDocs,          setMedDocs]          = useState<Record<string, File>>(() => {
    try { return loadDocsFromLS(0); } catch { return {}; }
  });
  const [bloodValues,      setBloodValues]      = useState<BloodValues>({});
  const [bloodTab,         setBloodTab]         = useState<"upload" | "manual" | "book">("upload");
  /* ── User History (Layers 1-4) — collapsed by default, kept out of the main flow ── */
  const [showHealthHistory, setShowHealthHistory] = useState(false);
  /* ── Layer 3 — Last 7 Days Symptoms ── */
  const [symptomLog, setSymptomLog] = useState<SymptomLog>({});
  const [expandedSymptomCat, setExpandedSymptomCat] = useState<string | null>(null);
  const [redFlagChecks, setRedFlagChecks] = useState<Record<string, boolean>>({});
  const setSymptomFreq = (id: string, freq: SymptomFreq) =>
    setSymptomLog((p) => ({ ...p, [id]: { freq, severity: p[id]?.severity ?? "mild" } }));
  const setSymptomSeverity = (id: string, severity: SymptomSeverity) =>
    setSymptomLog((p) => ({ ...p, [id]: { freq: p[id]?.freq ?? "sometimes", severity } }));
  const toggleRedFlag = (id: string) =>
    setRedFlagChecks((p) => ({ ...p, [id]: !p[id] }));
  const symptomClusters = computeSymptomClusters(symptomLog);
  const staticRedFlagMsgs = checkStaticRedFlags(redFlagChecks);
  const infectionPatternMsgs = checkInfectionPatterns(symptomLog);
  const symptomRedFlags = [...staticRedFlagMsgs, ...infectionPatternMsgs];
  const loggedSymptomCount = Object.values(symptomLog).filter((e) => e.freq !== "never").length;
  const [showPanelDetails, setShowPanelDetails] = useState(false);
  const [bookingDone,      setBookingDone]      = useState(false);

  /* ── save current form → persons array & localStorage ── */
  const saveCurrentPerson = useCallback((idx: number, overrides?: Partial<PersonProfile>) => {
    setPersons((prev) => {
      const next = [...prev];
      next[idx] = {
        name: petName, gender, ageYr, weightKg, heightCm,
        medConditions, healthHistory, isVeg, state, city,
        ...overrides,
      };
      try { localStorage.setItem("balanceai_persons", JSON.stringify(next)); } catch {}
      return next;
    });
  }, [petName, gender, ageYr, weightKg, heightCm, medConditions, healthHistory, isVeg, state]);

  /* ── switch to a different person ── */
  const switchPerson = (idx: number) => {
    saveCurrentPerson(selectedPerson);
    const p = persons[idx];
    setGender(p.gender);
    setPetName(p.name);
    setWeightKg(p.weightKg);
    setHeightCm(p.heightCm);
    setAgeYr(p.ageYr);
    setMedConditions(p.medConditions);
    setHealthHistory(p.healthHistory ?? []);
    setIsVeg(p.isVeg);
    setState_(p.state);
    setCity(p.city);
    setSelectedPerson(idx);
    setMedDocs(loadDocsFromLS(idx));
  };

  /* ── auto-save on field change ── */
  useEffect(() => {
    saveCurrentPerson(selectedPerson);
  }, [petName, gender, ageYr, weightKg, heightCm, isVeg, state, city]); // eslint-disable-line

  const toggleMed = (s: string) => {
    const next = medConditions.includes(s) ? medConditions.filter((x) => x !== s) : [...medConditions, s];
    setMedConditions(next);
    saveCurrentPerson(selectedPerson, { medConditions: next });
  };
  const toggleSymptom = (s: string) =>
    setSelectedSymptoms((p) => p.includes(s) ? p.filter((x) => x !== s) : [...p, s]);
  const toggleKitchen = (s: string) =>
    setKitchenItems((p) => p.includes(s) ? p.filter((x) => x !== s) : [...p, s]);
  const toggleCategory = (name: string) => setExpandedCat((p) => (p === name ? null : name));
  const addExclude = () => {
    const items = excludeInput.split(/[,،]/g).map((s) => s.trim()).filter(Boolean);
    setExcludeItems((p) => [...new Set([...p, ...items])]);
    setExcludeInput("");
  };
  const removeExclude = (s: string) => setExcludeItems((p) => p.filter((x) => x !== s));
  const handleCapture = (mod: string, file: File) =>
    setCapturedImages((p) => ({ ...p, [mod]: file }));

  const filteredMedical = MEDICAL_OPTIONS.filter((m) =>
    m.toLowerCase().includes(medSearch.toLowerCase())
  );

  const LOADING_STAGES = [
    "Analysing your symptoms...",
    "Reading your photos...",
    "Building your custom nutrition plan...",
    "Finalising your report...",
  ];

  const handleAnalyze = async () => {
    setLoading(true);
    setLoadingStage(0);
    try {
      const [allAnalysesPre, profile] = await Promise.all([getAllAnalyses(), getOrCreateProfile()]);
      const historyContext = allAnalysesPre.slice(0, 3)
        .flatMap((a) => a.high_risk)
        .filter((v, i, arr) => arr.indexOf(v) === i)
        .slice(0, 5).join(", ");

      const symptomStr = [
        voiceText,
        selectedSymptoms.map((s) => SYMPTOM_LABELS[s] || s).join(", "),
        healthHistory.length > 0 ? `Last 3 months illnesses: ${healthHistory.join(", ")}.` : "",
        medConditions.length > 0 ? `Medical conditions: ${medConditions.join(", ")}.` : "",
        ageYr    ? `Age: ${ageYr} years.`        : profile.age    ? `Age: ${profile.age}.`       : "",
        gender   ? `Gender: ${gender}.`           : profile.gender ? `Gender: ${profile.gender}.` : "",
        historyContext ? `Previously deficient in: ${historyContext}.` : "",
      ].filter(Boolean).join(" ");

      const result = await analyzeText({
        voice_text: symptomStr || "general health checkup",
        state: state || undefined,
        is_vegetarian: isVeg,
        _symptoms: selectedSymptoms,
      });

      setLoadingStage(1);
      const imageResults: Record<string, ImageAnalysisResult> = {};
      await Promise.allSettled(
        Object.entries(capturedImages).map(async ([mod, file]) => {
          const r = await analyzeImage(file, mod as any);
          imageResults[mod] = r;
        })
      );
      // Layer 4 (visual signs) is a modest-accuracy supporting signal only — never
      // treated as a primary deficiency driver, see generateDietPlan's weakDeficiencies.
      const imageDefs = Object.values(imageResults).flatMap((r) => (r?.available ? r.nutrients : []));

      setLoadingStage(2);
      const score    = result.balance_score?.overall_score ?? 0;
      const highRisk = result.balance_score?.high_risk_deficiencies ?? [];
      const medRisk  = result.balance_score?.medium_risk_deficiencies ?? [];
      const effectiveProfile = {
        ...profile,
        weight_kg: weightKg ? parseFloat(weightKg) : profile.weight_kg,
        height_cm: heightCm ? parseFloat(heightCm) : profile.height_cm,
      };
      const nutritionTargets = calculateNutritionTargets(
        effectiveProfile, profile.occupation ?? "sedentary", todayActivity, feelingToday, medConditions,
      );

      // 5-layer fusion engine + XGBoost ML layer
      const mealPhotosByDate = await getMealPhotoHistory(7);
      const mealPhotos = Object.values(mealPhotosByDate).flat();

      // Call XGBoost backend for ML predictions (optional — gracefully skipped if backend down)
      let mlPredictions: Record<string, { probability: number; deficient: boolean; threshold: number }> | undefined;
      try {
        const { API_BASE } = await import("@/lib/api");
        const mlResp = await fetch(`${API_BASE}/nutrition/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            age: profile?.age ?? 30,
            female: (gender === "female") ? 1 : 0,
            bmi: (profile?.weight_kg && profile?.height_cm)
              ? parseFloat((profile.weight_kg / ((profile.height_cm / 100) ** 2)).toFixed(1))
              : undefined,
          }),
          signal: AbortSignal.timeout(5000),
        });
        if (mlResp.ok) {
          const mlData = await mlResp.json();
          mlPredictions = mlData.predictions;
        }
      } catch { /* backend not running — proceed with rule-based layers only */ }

      const fusion = runNutrientFusion({
        healthHistory,
        bloodValues,
        gender: gender as "male" | "female" | "other" | "",
        symptomLog,
        imageResults,
        mealPhotos,
        profile,
        mlPredictions,
      });
      const fusionDefs = fusionToDeficiencyList(fusion);

      const historyDefs  = getHistoryDeficiencies(healthHistory);
      const bloodDefs    = parseBiomarkerDeficiencies(bloodValues, gender);
      const symptomDefs  = getSymptomDeficiencies(symptomLog);
      // Use fusion deficiencies as primary; legacy layer defs as fallback if fusion has no data
      const primaryDefs  = fusionDefs.length > 0
        ? fusionDefs
        : [...new Set([...highRisk, ...medRisk, ...historyDefs, ...bloodDefs, ...symptomDefs])];
      const generatedMealPlan = generateDietPlan(
        RECIPE_DB, primaryDefs,
        kitchenItems, state, isVeg, medConditions, profile, nutritionTargets, imageDefs,
      );

      setLoadingStage(3);
      await saveAnalysis({
        timestamp: Date.now(), date: new Date(), score,
        score_label: computeScoreLabel(score),
        predictions: result.deficiency_predictions ?? [],
        high_risk: highRisk, medium_risk: medRisk,
        diet_plan: result.diet_plan ?? {},
        recommendations: result.recommendations ?? [],
        alerts: result.alerts ?? [],
        symptoms_text: symptomStr,
        selected_symptoms: selectedSymptoms,
        state: state || "", is_vegetarian: isVeg,
        image_results: imageResults,
        kitchen_items: kitchenItems,
        medical_conditions: medConditions,
        health_history: healthHistory,
        blood_values: bloodValues,
      });

      sessionStorage.setItem("balanceai_meal_plan", JSON.stringify(generatedMealPlan));
      sessionStorage.setItem("balanceai_fusion", JSON.stringify(fusion));
      const allAnalyses = await getAllAnalyses();
      const newBadges = checkNewAchievements(allAnalyses, profile);
      if (newBadges.length > 0) {
        await unlockAchievements(newBadges.map((b) => b.id));
        sessionStorage.setItem("pending_achievement", JSON.stringify(newBadges[0]));
      }
      sessionStorage.setItem("balanceai_result", JSON.stringify({ ...result, imageResults }));
      router.push("/supplement-report");
    } catch {
      toast.error("Analysis mein error aaya. API server check karo.");
      setLoading(false);
    }
  };

  const NAV_ITEMS = [
    { label: "Recipes",        href: "/analyze",  dropdown: [{ label: "New Analysis", href: "/analyze" }] },
    { label: "Products",       href: "#",         dropdown: [{ label: "Dashboard", href: "/dashboard" }, { label: "AI Chat", href: "/chat" }, { label: "Insights", href: "/insights" }] },
    { label: "Support & FAQs", href: "/chat",     dropdown: [{ label: "History", href: "/history" }, { label: "Profile", href: "/profile" }] },
    { label: "About Us",       href: "/",         dropdown: null },
  ];

  return (
    <div style={{ background: WHITE, minHeight: "100vh" }}>

      {/* ── Announcement bar ── */}
      <div className="w-full text-center py-2.5 px-4 text-sm font-medium"
        style={{ background: "#f5ede0", color: GREEN }}>
        AI-powered nutrition deficiency detection in minutes · No blood test · Free · Made for India
      </div>

      {/* ── Nav — same as landing page ── */}
      <header className="sticky top-0 z-50 bg-white border-b" style={{ borderColor: BORDER }}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-8">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: GREEN }}>
              <Leaf className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight" style={{ color: GREEN }}>BalanceAI</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {NAV_ITEMS.map(({ label, href, dropdown }) => (
              <div key={label} className="relative"
                onMouseEnter={() => openDropdown(label)}
                onMouseLeave={closeDropdown}>
                <a href={href}
                  className="flex items-center gap-1 text-sm font-medium transition-colors"
                  style={{ color: label === "Recipes" ? GREEN : SUB }}>
                  {label}
                  {dropdown && <ChevronDown className="w-3.5 h-3.5"
                    style={{ transform: activeDropdown === label ? "rotate(180deg)" : "rotate(0deg)", color: MUTED }} />}
                </a>
                {dropdown && activeDropdown === label && (
                  <div className="absolute top-full left-0 mt-2 rounded-xl overflow-hidden"
                    style={{ background: WHITE, border: `1px solid ${BORDER}`, boxShadow: "0 8px 24px rgba(0,0,0,0.10)", minWidth: "180px", zIndex: 100 }}>
                    {dropdown.map(({ label: dl, href: dh }) => (
                      <Link key={dh} href={dh}
                        className="block px-5 py-3 text-sm font-medium"
                        style={{ color: SUB }}
                        onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#eef7f2"; (e.currentTarget as HTMLElement).style.color = GREEN; }}
                        onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; (e.currentTarget as HTMLElement).style.color = SUB; }}>
                        {dl}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm font-medium" style={{ color: SUB }}>Login</Link>
            <Link href="/analyze">
              <button className="px-5 py-2.5 rounded-full text-sm font-semibold"
                style={{ background: GREEN, color: WHITE }}>Get Started</button>
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 pt-12 pb-20">

          {/* ── Centered heading ── */}
          <div className="text-center mb-10">
            <h1
              className="font-bold mb-6"
              style={{ color: GREEN, fontSize: "clamp(1.8rem, 4vw, 2.6rem)", lineHeight: 1.2 }}
            >
              Get your free personalised AI nutrition analysis in seconds
            </h1>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => document.getElementById("step-form")?.scrollIntoView({ behavior: "smooth" })}
                className="px-7 py-2.5 rounded-full text-sm font-bold"
                style={{ background: AMBER, color: WHITE }}
              >
                Try Now
              </button>
              <button
                className="px-7 py-2.5 rounded-full text-sm font-bold border-2"
                style={{ borderColor: GREEN, color: GREEN, background: "transparent" }}
              >
                How To
              </button>
            </div>
          </div>

          {/* ── 2-step horizontal underline tabs ── */}
          <div className="flex border-b mb-10" style={{ borderColor: BORDER }}>
            {STEPS.map((s, i) => {
              const active = i === step;
              const done   = i < step;
              return (
                <button
                  key={s.id}
                  onClick={() => done && setStep(i)}
                  className="flex-1 py-4 text-sm font-semibold text-center transition-all"
                  style={{
                    color: active ? GREEN : done ? SUB : MUTED,
                    borderBottom: active ? `3px solid ${GREEN}` : "3px solid transparent",
                    marginBottom: "-1px",
                    cursor: done ? "pointer" : "default",
                    background: "transparent",
                  }}
                >
                  {done ? `✓ ${s.label.split(": ")[0]}` : s.label}
                </button>
              );
            })}
          </div>

          {/* ── Step content ── */}
          <div id="step-form">

            {/* ── STEP 0: Your Details + Symptoms (merged) ── */}
            {step === 0 && (
              <div className="space-y-8">

                {/* Who is this for */}
                <div>
                  <h2 className="font-bold text-lg mb-5" style={{ color: TEXT }}>
                    Enter who this analysis is for below:
                  </h2>

                  {/* 4 person profile tiles — balance.it style */}
                  <div className="flex gap-3 mb-6">
                    {persons.map((p, idx) => {
                      const sel = idx === selectedPerson;
                      const initials = p.name ? p.name[0].toUpperCase() : (idx + 1).toString();
                      return (
                        <button key={idx} onClick={() => switchPerson(idx)}
                          className="flex-1 flex flex-col items-center gap-2 py-4 rounded-xl transition-all"
                          style={sel
                            ? { border: `2px solid ${GREEN}`, background: "#eef7f2" }
                            : { border: `2px solid ${BORDER}`, background: WHITE }}>
                          <div className="w-14 h-14 rounded-full flex items-center justify-center relative"
                            style={sel ? { background: GREEN } : { background: "#f0f0f0" }}>
                            {p.name ? (
                              <span className="text-lg font-bold" style={{ color: sel ? WHITE : MUTED }}>{initials}</span>
                            ) : (
                              <User className="w-6 h-6" style={{ color: sel ? WHITE : MUTED }} />
                            )}
                            {/* Small upload icon like balance.it */}
                            {sel && (
                              <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-xs"
                                style={{ background: GREEN, color: WHITE, border: `2px solid white` }}>↑</span>
                            )}
                          </div>
                          <span className="text-xs font-semibold text-center leading-tight"
                            style={{ color: sel ? GREEN : MUTED }}>
                            {p.name || MEMBER_LABELS[idx]}
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Name */}
                  <input value={petName} onChange={(e) => setPetName(e.target.value)}
                    placeholder="Enter first and last name (optional)"
                    className={inputCls + " mb-4"} style={inputStyle} />

                  {/* Gender row */}
                  <div className="flex gap-3 mb-4">
                    {(["male","female","other"] as const).map((g) => (
                      <button key={g} onClick={() => setGender(g)}
                        className="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                        style={gender === g
                          ? { background: "#eef7f2", border: `1px solid #b6ddc9`, color: GREEN }
                          : { background: WHITE, border: `1px solid ${BORDER}`, color: SUB }}>
                        {g.charAt(0).toUpperCase() + g.slice(1)}
                      </button>
                    ))}
                  </div>

                  {/* Weight + Age + Height */}
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    {[
                      { val: weightKg, set: setWeightKg, ph: "60",  unit: "kg" },
                      { val: ageYr,    set: setAgeYr,    ph: "25",  unit: "yr" },
                      { val: heightCm, set: setHeightCm, ph: "165", unit: "cm" },
                    ].map(({ val, set, ph, unit }) => (
                      <div key={unit} className="relative">
                        <input type="number" value={val} onChange={(e) => set(e.target.value)}
                          placeholder={ph} className={inputCls + " pr-10"} style={inputStyle} />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold px-2 py-0.5 rounded"
                          style={{ background: GREEN, color: WHITE }}>{unit}</span>
                      </div>
                    ))}
                  </div>

                  {/* Calorie bar */}
                  {weightKg && ageYr && (
                    <div className="rounded-lg px-4 py-3 mb-6"
                      style={{ background: BG, border: `1px solid ${BORDER}` }}>
                      <p className="text-sm" style={{ color: SUB }}>
                        A <strong style={{ color: TEXT }}>{weightKg} kg</strong>, <strong style={{ color: TEXT }}>{ageYr} yr</strong> old {gender || "person"} requires approx{" "}
                        <strong style={{ color: GREEN }}>{Math.round(parseFloat(weightKg) * 30 + (gender === "male" ? 200 : 0))} kcal/day</strong>.
                      </p>
                    </div>
                  )}
                </div>

                {/* Symptoms */}
                <div>
                  <h2 className="font-bold text-base mb-4" style={{ color: TEXT }}>
                    Describe your symptoms below:
                  </h2>
                  <div className="flex border-b mb-4" style={{ borderColor: BORDER }}>
                    {(["voice", "text"] as const).map((t) => (
                      <button key={t} onClick={() => setVoiceTab(t)}
                        className="px-5 py-2.5 text-sm font-semibold transition-all"
                        style={{
                          color: voiceTab === t ? GREEN : MUTED,
                          borderBottom: voiceTab === t ? `2px solid ${GREEN}` : "2px solid transparent",
                          marginBottom: "-1px", background: "transparent",
                        }}>
                        {t === "voice" ? "Voice" : "Type it"}
                      </button>
                    ))}
                  </div>
                  {voiceTab === "voice" ? (
                    <div>
                      <VoiceRecorder onTranscript={(t) => setVoiceText((p) => p ? `${p} ${t}` : t)}
                        placeholder="Mic dabao — Hindi ya English mein bolein" />
                      {voiceText && (
                        <div className="mt-3 p-4 rounded-lg text-sm"
                          style={{ background: "#eef7f2", border: `1px solid #b6ddc9` }}>
                          <p className="text-xs font-semibold mb-1" style={{ color: MUTED }}>Transcribed:</p>
                          <p style={{ color: TEXT }}>{voiceText}</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <textarea value={voiceText} onChange={(e) => setVoiceText(e.target.value)}
                      placeholder="Describe your symptoms — e.g. feeling very tired, hair fall, poor sleep, weak nails..."
                      rows={4} className={inputCls + " resize-none"} style={inputStyle} />
                  )}
                  <div className="mt-4">
                    <p className="text-sm font-semibold mb-3" style={{ color: SUB }}>Or select from common symptoms:</p>
                    <div className="flex flex-wrap gap-2">
                      {SYMPTOM_OPTIONS.map((s) => (
                        <Chip key={s}
                          label={SYMPTOM_LABELS[s]?.split(" / ")[1] || SYMPTOM_LABELS[s] || s}
                          active={selectedSymptoms.includes(s)} onClick={() => toggleSymptom(s)} />
                      ))}
                    </div>
                  </div>
                </div>

                {/* User History — Layers 1-4 (photos, 3-month history, medical conditions,
                    blood test, 7-day symptoms) live ONLY here, collapsed by default so the
                    main flow stays short; nothing layer-related appears anywhere else. */}
                <div className="rounded-2xl overflow-hidden" style={{ border: `1px solid ${BORDER}` }}>
                  <button type="button" onClick={() => setShowHealthHistory((p) => !p)}
                    className="flex items-center justify-between w-full px-5 py-4 text-left"
                    style={{ background: BG }}>
                    <div>
                      <p className="text-base font-bold" style={{ color: TEXT }}>
                        📋 Your Health History <span className="text-sm font-normal" style={{ color: MUTED }}>(optional, improves accuracy)</span>
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: MUTED }}>
                        Photos · Last 3 months · Medical conditions · Blood test · Last 7 days symptoms
                      </p>
                    </div>
                    <span style={{ color: MUTED }}>{showHealthHistory ? "▲" : "▼"}</span>
                  </button>
                  {showHealthHistory && (
                    <div className="p-5 space-y-8" style={{ background: WHITE }}>

                {/* Photos */}
                <div>
                  <p className="text-sm font-semibold mb-3" style={{ color: SUB }}>
                    Take photos for visual analysis: <span style={{ color: MUTED }}>(optional)</span>
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    {(["nail", "tongue", "skin", "eye"] as const).map((mod) => (
                      <div key={mod} className="rounded-lg overflow-hidden"
                        style={{ border: capturedImages[mod] ? `1px solid #b6ddc9` : `1px solid ${BORDER}` }}>
                        <CameraCapture modality={mod} onCapture={(f) => handleCapture(mod, f)}
                          captured={!!capturedImages[mod]} />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Layer 1 — Last 3 months health history */}
                <div>
                  <p className="text-base font-bold mb-1" style={{ color: TEXT }}>
                    Last 3 months mein kya kya hua? <span className="text-sm font-normal" style={{ color: MUTED }}>(optional)</span>
                  </p>
                  <p className="text-sm mb-3" style={{ color: MUTED }}>
                    Koi bhi bimari ya symptoms jo pichhle 3 mahine mein aaye ho — select karo
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {HISTORY_OPTIONS.map((h) => (
                      <Chip
                        key={h}
                        label={h}
                        active={healthHistory.includes(h)}
                        onClick={() => {
                          const next = healthHistory.includes(h)
                            ? healthHistory.filter((x) => x !== h)
                            : [...healthHistory, h];
                          setHealthHistory(next);
                          saveCurrentPerson(selectedPerson, { healthHistory: next });
                        }}
                      />
                    ))}
                  </div>
                  {healthHistory.length > 0 && (
                    <p className="text-xs mt-3 italic" style={{ color: "#1d5c3d" }}>
                      ✓ {healthHistory.length} item{healthHistory.length > 1 ? "s" : ""} selected — recipe mein inn nutrients ko boost kiya jayega
                    </p>
                  )}
                </div>

                {/* Medical conditions */}
                <div>
                  <p className="text-base font-bold mb-3" style={{ color: TEXT }}>
                    Any special health conditions or diet we should be aware of? (optional)
                  </p>
                  <div className="relative mb-3">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm" style={{ color: MUTED }}>🔍</span>
                    <input value={medSearch} onChange={(e) => setMedSearch(e.target.value)}
                      placeholder="Search for & select health conditions, and/or requirements"
                      className={inputCls + " pl-9"} style={inputStyle} />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {filteredMedical.map((m) => (
                      <Chip key={m} label={m} active={medConditions.includes(m)} onClick={() => toggleMed(m)} />
                    ))}
                  </div>
                  {medConditions.length > 0 && (
                    <p className="text-xs mt-3 italic" style={{ color: "#dc2626" }}>
                      Medical conditions selected — plan will be adjusted accordingly.
                    </p>
                  )}
                </div>

                {/* Layer 2 — Blood Test Analysis */}
                <div className="rounded-2xl overflow-hidden" style={{ border: `2px solid ${GREEN}` }}>
                  {/* Header */}
                  <div className="px-5 py-4" style={{ background: GREEN }}>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-white text-base font-bold">🩸 Blood Test Analysis</span>
                        </div>
                        <p className="text-xs mt-0.5" style={{ color: "#b6ddc9" }}>
                          Most accurate way to know your exact nutrition status
                        </p>
                      </div>
                    </div>
                    {/* Tabs */}
                    <div className="flex gap-2 mt-3">
                      {(["upload", "manual", "book"] as const).map((t) => (
                        <button key={t} onClick={() => setBloodTab(t)}
                          className="text-xs px-3 py-1.5 rounded-full font-semibold transition-all"
                          style={bloodTab === t
                            ? { background: WHITE, color: GREEN }
                            : { background: "rgba(255,255,255,0.15)", color: WHITE }}>
                          {t === "upload" ? "📄 Upload Report" : t === "manual" ? "✏️ Enter Values" : "🏠 Book Panel"}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Tab: Upload Report */}
                  {bloodTab === "upload" && (
                    <div className="p-5" style={{ background: WHITE }}>
                      <p className="text-sm mb-4" style={{ color: MUTED }}>
                        Upload photo or PDF of your blood test report — AI will read it and adjust your nutrition plan
                      </p>
                      <div className="grid grid-cols-3 gap-3">
                        {([
                          { key: "blood_test",   label: "Blood Test Report", icon: "🩸" },
                          { key: "medicines",    label: "Current Medicines",  icon: "💊" },
                          { key: "prescription", label: "Prescription",       icon: "📋" },
                        ] as const).map(({ key, label, icon }) => {
                          const uploaded = !!medDocs[key];
                          return (
                            <label key={key} className="cursor-pointer">
                              <input type="file" accept="image/*,.pdf" className="hidden"
                                onChange={(e) => {
                                  const f = e.target.files?.[0];
                                  if (!f) return;
                                  setMedDocs((p) => ({ ...p, [key]: f }));
                                  saveDocToLS(selectedPerson, key, f);
                                }} />
                              <div className="flex flex-col items-center gap-2 py-4 rounded-xl transition-all text-center"
                                style={uploaded
                                  ? { border: `2px solid ${GREEN}`, background: "#eef7f2" }
                                  : { border: `2px dashed ${BORDER}`, background: BG }}>
                                <span className="text-2xl">{uploaded ? "✅" : icon}</span>
                                <span className="text-xs font-semibold leading-tight px-1"
                                  style={{ color: uploaded ? GREEN : MUTED }}>
                                  {uploaded ? medDocs[key].name.slice(0, 14) + "…" : label}
                                </span>
                                <span className="text-xs" style={{ color: MUTED }}>
                                  {uploaded ? "tap to change" : "tap to upload"}
                                </span>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                      {Object.keys(medDocs).length > 0 && (
                        <p className="text-xs mt-3 font-medium" style={{ color: GREEN }}>
                          ✓ {Object.keys(medDocs).length} document{Object.keys(medDocs).length > 1 ? "s" : ""} uploaded — AI will read them during analysis
                        </p>
                      )}
                    </div>
                  )}

                  {/* Tab: Manual Entry */}
                  {bloodTab === "manual" && (
                    <div className="p-5" style={{ background: WHITE }}>
                      <p className="text-sm mb-4" style={{ color: MUTED }}>
                        Enter your blood test values — plan will be adjusted based on your exact numbers
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        {BALANCEAI_PANEL_TESTS.map(({ test, biomarker, why }) => {
                          const def = BIOMARKER_MAP[biomarker];
                          if (!def) return null;
                          const val = bloodValues[biomarker];
                          const hasVal = val !== undefined && val !== null;
                          const alerts = hasVal ? getBiomarkerAlerts({ [biomarker]: val }, gender) : [];
                          const alert = alerts[0];
                          return (
                            <div key={biomarker} className="rounded-xl p-3"
                              style={{ border: `1px solid ${hasVal ? (alert?.status === "ok" ? "#b6ddc9" : "#fbbf24") : BORDER}`, background: hasVal ? (alert?.status === "ok" ? "#f0faf4" : "#fffbeb") : BG }}>
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-xs font-semibold" style={{ color: TEXT }}>{def.label}</span>
                                {hasVal && (
                                  <span className="text-xs font-bold" style={{ color: alert?.status === "ok" ? GREEN : alert?.status === "low" ? "#dc2626" : "#d97706" }}>
                                    {alert?.status === "ok" ? "✓" : alert?.status === "low" ? "↓" : "↑"}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <input
                                  type="number"
                                  placeholder={def.low ? `Normal ≥${def.low}` : def.high ? `Normal <${def.high}` : "Value"}
                                  value={val ?? ""}
                                  onChange={(e) => {
                                    const n = e.target.value === "" ? undefined : parseFloat(e.target.value);
                                    setBloodValues((p) => ({ ...p, [biomarker]: n }));
                                  }}
                                  className="w-full text-sm rounded-lg px-2 py-1.5 outline-none"
                                  style={{ border: `1px solid ${BORDER}`, background: WHITE, color: TEXT }}
                                />
                                <span className="text-xs whitespace-nowrap" style={{ color: MUTED }}>{def.unit}</span>
                              </div>
                              {hasVal && alert?.note && (
                                <p className="text-xs mt-1" style={{ color: alert.status === "ok" ? GREEN : "#d97706" }}>{alert.note}</p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                      {Object.keys(bloodValues).filter((k) => bloodValues[k] !== undefined).length > 0 && (
                        <p className="text-xs mt-3 font-medium" style={{ color: GREEN }}>
                          ✓ {Object.keys(bloodValues).filter((k) => bloodValues[k] !== undefined).length} values entered — nutrition plan will be calibrated to your blood data
                        </p>
                      )}
                    </div>
                  )}

                  {/* Tab: Book BalanceAI Panel */}
                  {bloodTab === "book" && (
                    <div style={{ background: WHITE }}>
                      {/* Hero */}
                      <div className="px-5 pt-5 pb-4" style={{ background: "#f0faf4" }}>
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h3 className="text-base font-bold" style={{ color: GREEN }}>BalanceAI Nutrition Panel</h3>
                            <p className="text-xs mt-0.5" style={{ color: MUTED }}>14 tests · Home Collection · Results in 24 hours</p>
                          </div>
                          <div className="text-right shrink-0">
                            <div className="text-xl font-bold" style={{ color: GREEN }}>₹799</div>
                            <div className="text-xs line-through" style={{ color: MUTED }}>₹2,500</div>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2 mt-3">
                          {["🏠 Home Collection", "⏱ 24h Results", "📊 Free Nutrition Report", "🔬 NABL Certified Lab"].map((b) => (
                            <span key={b} className="text-xs px-2 py-1 rounded-full font-medium"
                              style={{ background: "#d1f5e3", color: GREEN }}>{b}</span>
                          ))}
                        </div>
                      </div>

                      {/* What's included */}
                      <div className="px-5 py-4">
                        <button
                          onClick={() => setShowPanelDetails((p) => !p)}
                          className="flex items-center justify-between w-full text-sm font-semibold mb-3"
                          style={{ color: TEXT }}>
                          <span>What&apos;s included in the panel?</span>
                          <span style={{ color: MUTED }}>{showPanelDetails ? "▲" : "▼"}</span>
                        </button>
                        {showPanelDetails && (
                          <div className="grid grid-cols-1 gap-1.5 mb-4">
                            {BALANCEAI_PANEL_TESTS.map(({ test, why }) => (
                              <div key={test} className="flex items-start gap-2 text-xs">
                                <span style={{ color: GREEN }}>✓</span>
                                <span style={{ color: TEXT }}><b>{test}</b> — <span style={{ color: MUTED }}>{why}</span></span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Booking form / CTA */}
                        {!bookingDone ? (
                          <div>
                            <p className="text-xs mb-3" style={{ color: MUTED }}>
                              Enter your details — our team will call to confirm slot within 2 hours
                            </p>
                            <div className="flex flex-col gap-2">
                              <input id="book_name" type="text" placeholder="Your name"
                                className="text-sm rounded-xl px-4 py-2.5 w-full outline-none"
                                style={{ border: `1px solid ${BORDER}`, color: TEXT }} />
                              <input id="book_phone" type="tel" placeholder="Mobile number"
                                className="text-sm rounded-xl px-4 py-2.5 w-full outline-none"
                                style={{ border: `1px solid ${BORDER}`, color: TEXT }} />
                              <input id="book_area" type="text" placeholder="Area / Pincode"
                                className="text-sm rounded-xl px-4 py-2.5 w-full outline-none"
                                style={{ border: `1px solid ${BORDER}`, color: TEXT }} />
                            </div>
                            <button
                              onClick={() => {
                                const name  = (document.getElementById("book_name")  as HTMLInputElement)?.value.trim();
                                const phone = (document.getElementById("book_phone") as HTMLInputElement)?.value.trim();
                                if (!name || !phone) { toast.error("Name aur mobile number zaroori hai"); return; }
                                setBookingDone(true);
                                toast.success("Request bhej di! 2 ghante mein call aayega.");
                              }}
                              className="mt-3 w-full py-3 rounded-xl font-bold text-white text-sm transition-all"
                              style={{ background: GREEN }}>
                              Book Home Collection →
                            </button>
                          </div>
                        ) : (
                          <div className="text-center py-4 rounded-xl" style={{ background: "#f0faf4" }}>
                            <div className="text-2xl mb-2">✅</div>
                            <p className="font-bold text-sm" style={{ color: GREEN }}>Booking request sent!</p>
                            <p className="text-xs mt-1" style={{ color: MUTED }}>Hamare team member 2 ghante mein call karenge slot confirm karne ke liye</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Layer 3 — Last 7 Days Symptoms */}
                <div className="rounded-2xl overflow-hidden" style={{ border: `2px solid ${GREEN}` }}>
                  <div className="px-5 py-4" style={{ background: GREEN }}>
                    <div className="flex items-center gap-2">
                      <span className="text-white text-base font-bold">📅 Last 7 Days Symptoms</span>
                    </div>
                    <p className="text-xs mt-0.5" style={{ color: "#b6ddc9" }}>
                      Pichhle 7 dino mein kaunse symptoms kitni baar aaye — early warning ke liye (optional)
                    </p>
                  </div>
                  <div className="p-5" style={{ background: WHITE }}>
                    {/* Static red-flag checklist — always visible, checked directly (not frequency-scored) */}
                    <div className="mb-4 p-3 rounded-xl" style={{ background: "#fef2f2", border: `1px solid #fca5a5` }}>
                      <p className="text-xs font-bold mb-2" style={{ color: "#dc2626" }}>
                        ⚠ Any of these right now? (tick if yes — needs a doctor, not diet)
                      </p>
                      <div className="flex flex-col gap-1.5">
                        {RED_FLAG_SYMPTOMS.map((f) => (
                          <label key={f.id} className="flex items-center gap-2 text-xs cursor-pointer" style={{ color: "#991b1b" }}>
                            <input type="checkbox" checked={!!redFlagChecks[f.id]} onChange={() => toggleRedFlag(f.id)} />
                            {f.label}
                          </label>
                        ))}
                      </div>
                    </div>

                    {SYMPTOM_CATEGORIES.map((cat) => (
                      <div key={cat.id} className="mb-2 rounded-xl overflow-hidden" style={{ border: `1px solid ${BORDER}` }}>
                        <button
                          onClick={() => setExpandedSymptomCat((p) => (p === cat.id ? null : cat.id))}
                          className="flex items-center justify-between w-full px-4 py-3 text-sm font-semibold"
                          style={{ background: BG, color: TEXT }}>
                          <span>{cat.label}</span>
                          <span style={{ color: MUTED }}>{expandedSymptomCat === cat.id ? "▲" : "▼"}</span>
                        </button>
                        {expandedSymptomCat === cat.id && (
                          <div className="p-4 flex flex-col gap-4">
                            {cat.symptoms.map((s) => {
                              const entry = symptomLog[s.id];
                              return (
                                <div key={s.id}>
                                  <p className="text-xs font-medium mb-1.5" style={{ color: TEXT }}>{s.label}</p>
                                  <div className="flex flex-wrap gap-1.5">
                                    {FREQ_OPTIONS.map((f) => (
                                      <button key={f.value} onClick={() => setSymptomFreq(s.id, f.value)}
                                        className="px-2.5 py-1 rounded-full text-xs font-medium transition-all"
                                        style={entry?.freq === f.value
                                          ? { background: "#eef7f2", border: `1px solid #b6ddc9`, color: GREEN }
                                          : { background: WHITE, border: `1px solid ${BORDER}`, color: SUB }}>
                                        {f.label}
                                      </button>
                                    ))}
                                  </div>
                                  {entry && entry.freq !== "never" && (
                                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                                      {SEVERITY_OPTIONS.map((sv) => (
                                        <button key={sv.value} onClick={() => setSymptomSeverity(s.id, sv.value)}
                                          className="px-2.5 py-1 rounded-full text-xs font-medium transition-all"
                                          style={entry.severity === sv.value
                                            ? { background: "#fff7ed", border: `1px solid #fbbf24`, color: "#d97706" }
                                            : { background: WHITE, border: `1px solid ${BORDER}`, color: SUB }}>
                                          {sv.label}
                                        </button>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    ))}

                    {loggedSymptomCount > 0 && symptomRedFlags.length > 0 && (
                      <div className="mt-3 p-3 rounded-xl" style={{ background: "#fef2f2", border: `1px solid #fca5a5` }}>
                        <p className="text-xs font-bold mb-1" style={{ color: "#dc2626" }}>⚠ Please see a doctor</p>
                        {symptomRedFlags.map((m, i) => (
                          <p key={i} className="text-xs mt-1" style={{ color: "#991b1b" }}>{m}</p>
                        ))}
                      </div>
                    )}
                    {loggedSymptomCount > 0 && symptomClusters.length > 0 && (
                      <div className="mt-3 p-3 rounded-xl" style={{ background: "#f0faf4" }}>
                        <p className="text-xs font-bold mb-1.5" style={{ color: GREEN }}>Possible patterns detected:</p>
                        {symptomClusters.slice(0, 3).map((r) => (
                          <p key={r.cluster.id} className="text-xs mt-0.5" style={{ color: SUB }}>
                            • {r.cluster.name} <span style={{ color: MUTED }}>({r.confidence} confidence)</span>
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                    </div>
                  )}
                </div>

                {/* State + City + Diet */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2" style={{ color: SUB }}>State / UT</label>
                    <select
                      value={state}
                      onChange={(e) => { setState_(e.target.value); setCity(""); }}
                      className={inputCls}
                      style={{ ...inputStyle, appearance: "auto", cursor: "pointer" }}
                    >
                      <option value="">— Select State —</option>
                      <optgroup label="States">
                        {INDIA_LOCATIONS.filter((l) => l.type === "state").map((l) => (
                          <option key={l.state} value={l.state}>{l.state}</option>
                        ))}
                      </optgroup>
                      <optgroup label="Union Territories">
                        {INDIA_LOCATIONS.filter((l) => l.type === "ut").map((l) => (
                          <option key={l.state} value={l.state}>{l.state}</option>
                        ))}
                      </optgroup>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold mb-2" style={{ color: SUB }}>City / District</label>
                    <select
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      disabled={!state}
                      className={inputCls}
                      style={{ ...inputStyle, appearance: "auto", cursor: state ? "pointer" : "not-allowed", opacity: state ? 1 : 0.5 }}
                    >
                      <option value="">{state ? "— Select City —" : "Select state first"}</option>
                      {getCities(state).map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-sm font-semibold mb-2" style={{ color: SUB }}>Diet preference</p>
                    <div className="flex gap-2">
                      {[{ label: "Vegetarian", val: true }, { label: "Non-Veg", val: false }].map((opt) => (
                        <button key={String(opt.val)} onClick={() => setIsVeg(opt.val)}
                          className="flex-1 py-2.5 rounded-lg text-sm font-semibold"
                          style={isVeg === opt.val
                            ? { background: "#eef7f2", border: `1px solid #b6ddc9`, color: GREEN }
                            : { background: WHITE, border: `1px solid ${BORDER}`, color: SUB }}>
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold mb-2" style={{ color: SUB }}>Activity today</p>
                  <div className="flex flex-wrap gap-2">
                    {([
                      { v: "rest", l: "Rest" }, { v: "light_walk", l: "Walk <30min" },
                      { v: "walk_30_60", l: "Walk 30–60min" }, { v: "walk_60plus", l: "Walk >60min" },
                      { v: "yoga", l: "Yoga" }, { v: "gym_light", l: "Gym (light)" },
                      { v: "gym_heavy", l: "Gym (heavy)" }, { v: "run_30", l: "Run ~30min" },
                    ] as const).map(({ v, l }) => (
                      <Chip key={v} label={l} active={todayActivity === v} onClick={() => setTodayActivity(v)} />
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold mb-2" style={{ color: SUB }}>How are you feeling today?</p>
                  <div className="flex flex-wrap gap-2">
                    {([
                      { v: "normal", l: "Normal" }, { v: "tired", l: "Tired" },
                      { v: "very_tired", l: "Very tired" }, { v: "sick", l: "Unwell" },
                      { v: "stressed", l: "Stressed" },
                    ] as const).map(({ v, l }) => (
                      <Chip key={v} label={l} active={feelingToday === v} onClick={() => setFeelingToday(v)} />
                    ))}
                  </div>
                </div>

                {/* Bottom CTAs — exactly balance.it */}
                <div className="border-t pt-8" style={{ borderColor: BORDER }}>
                  <p className="text-xs text-center mb-6" style={{ color: MUTED }}>
                    Not a medical diagnosis — do not use in place of a doctor&apos;s advice
                  </p>
                  <div className="flex gap-4">
                    <button onClick={handleAnalyze} disabled={loading}
                      className="flex-1 flex items-center justify-center py-4 rounded-lg text-sm font-bold transition-all"
                      style={{ background: loading ? "#c8963a" : AMBER, color: WHITE }}>
                      {loading ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />Analysing...</> : "Build My Nutrition Plan Now"}
                    </button>
                    <button onClick={() => setStep(1)}
                      className="flex-1 flex items-center justify-center py-4 rounded-lg text-sm font-bold transition-all"
                      style={{ background: GREEN, color: WHITE }}>
                      Let Me Pick Ingredients
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ── STEP 1: Ingredients (optional) — exactly balance.it Step 2 ── */}
            {step === 1 && (
              <div className="space-y-6">

                {/* Help banner */}
                <div className="rounded-lg py-3 px-4 text-center text-sm" style={{ background: "#eef7f2", color: SUB }}>
                  Need a little help?{" "}
                  <button onClick={handleAnalyze} disabled={loading} className="underline font-semibold" style={{ color: GREEN }}>
                    We&apos;ll pick the ingredients for you.
                  </button>
                </div>

                {/* Heading row + leave-out link + one-pot checkbox */}
                <div>
                  <div className="flex items-start justify-between gap-4 flex-wrap mb-3">
                    <div>
                      <h2 className="font-bold text-lg mb-1" style={{ color: TEXT }}>
                        What ingredients would you like to use?
                      </h2>
                      <button onClick={() => document.getElementById("leave-out-box")?.scrollIntoView({ behavior: "smooth" })}
                        className="text-xs font-bold underline" style={{ color: SUB }}>
                        ANY INGREDIENTS YOU&apos;D LIKE TO LEAVE OUT?
                      </button>
                    </div>
                    <label className="flex items-center gap-2 text-sm font-medium cursor-pointer" style={{ color: SUB }}>
                      <input type="checkbox" checked={onePotOnly} onChange={(e) => setOnePotOnly(e.target.checked)} />
                      🍲 Show <strong>one pot cooking</strong> ingredients &amp; recipes ONLY
                    </label>
                  </div>

                  {/* Search ingredients */}
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm" style={{ color: MUTED }}>🔍</span>
                    <input value={ingredientSearch} onChange={(e) => setIngredientSearch(e.target.value)}
                      placeholder="Search ingredients | For one pot cooking options & recipes, click checkbox above first"
                      className={inputCls + " pl-9"} style={inputStyle} />
                  </div>
                </div>

                {/* 6-category accordion — exactly balance.it Proteins/Carbs/Fats/Veggies/Fruit/Treats */}
                <div className="rounded-lg overflow-hidden" style={{ border: `1px solid ${BORDER}` }}>
                  {KITCHEN_CATEGORIES.map((cat) => {
                    const pool = ingredientSearch ? cat.searchItems : cat.items;
                    const matches = pool.filter((item) =>
                      item.toLowerCase().includes(ingredientSearch.toLowerCase())
                    );
                    if (ingredientSearch && matches.length === 0) return null;
                    const open = ingredientSearch ? true : expandedCat === cat.name;
                    return (
                      <div key={cat.name} style={{ borderBottom: `1px solid ${BORDER}` }}>
                        <button onClick={() => toggleCategory(cat.name)}
                          className="w-full flex items-center justify-between px-5 py-5 text-left">
                          <span className="flex items-center gap-2">
                            <span className="font-bold text-base" style={{ color: TEXT }}>{cat.name}</span>
                            {cat.required && <span className="text-xs" style={{ color: MUTED }}>add at least 1</span>}
                          </span>
                          <span className="flex items-center gap-1.5 text-sm font-medium shrink-0" style={{ color: SUB }}>
                            Most Popular
                            <ChevronDown className="w-4 h-4 transition-transform"
                              style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }} />
                          </span>
                        </button>
                        {open && (
                          <div className="px-5 pb-5 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3" style={{ background: BG }}>
                            {matches.map((item) => {
                              const active = kitchenItems.includes(item);
                              return (
                                <button key={item} onClick={() => toggleKitchen(item)}
                                  className="relative px-3 py-3 rounded-lg text-sm font-semibold text-center transition-all"
                                  style={active
                                    ? { background: GREEN, color: WHITE, border: `1px solid ${GREEN}` }
                                    : { background: "#f3e3ea", color: TEXT, border: "1px solid #e9cdd8" }}>
                                  {item}
                                  <span
                                    role="button"
                                    aria-label={`${item} nutrition info`}
                                    onClick={(e) => { e.stopPropagation(); setInfoItem(item); }}
                                    className="absolute top-1 right-1.5 text-[11px] opacity-70 hover:opacity-100 cursor-pointer">
                                    ⓘ
                                  </span>
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Selected summary */}
                {kitchenItems.length > 0 && (
                  <div className="rounded-xl p-4" style={{ background: "#eef7f2", border: `1px solid #b6ddc9` }}>
                    <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: GREEN }}>
                      Selected ({kitchenItems.length})
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {kitchenItems.map((k) => (
                        <span key={k} onClick={() => toggleKitchen(k)}
                          className="text-xs px-3 py-1 rounded-full cursor-pointer"
                          style={{ background: WHITE, border: `1px solid #b6ddc9`, color: GREEN }}>
                          {k} ×
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Leave out these ingredients */}
                <div id="leave-out-box">
                  <p className="font-bold text-base mb-3" style={{ color: TEXT }}>Leave out these ingredients:</p>
                  <input value={excludeInput} onChange={(e) => setExcludeInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addExclude()}
                    placeholder="Search or add ingredients to exclude (press Enter to add)"
                    className={inputCls + " mb-3"} style={inputStyle} />
                  {excludeItems.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {excludeItems.map((k) => (
                        <span key={k} onClick={() => removeExclude(k)}
                          className="text-xs px-3 py-1 rounded-full cursor-pointer"
                          style={{ background: WHITE, border: `1px solid ${BORDER}`, color: SUB }}>
                          {k} ×
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Bottom CTAs — exactly balance.it Step 2 bottom: BACK + GET RECIPE */}
                <div className="border-t pt-8" style={{ borderColor: BORDER }}>
                  <p className="text-xs text-center mb-6" style={{ color: MUTED }}>
                    Not a medical diagnosis — do not use in place of a doctor&apos;s advice
                  </p>
                  <div className="flex gap-4">
                    <button onClick={() => setStep(0)}
                      className="px-8 py-4 rounded-lg text-sm font-bold border-2 transition-all"
                      style={{ borderColor: GREEN, color: GREEN, background: "transparent" }}>
                      BACK
                    </button>
                    <button onClick={handleAnalyze} disabled={loading}
                      className="flex-1 flex items-center justify-center py-4 rounded-lg text-sm font-bold transition-all"
                      style={{ background: loading ? "#5a8a72" : GREEN, color: WHITE }}>
                      {loading ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />Analysing...</> : "GET RECIPE"}
                    </button>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* Full-screen "Building your custom plan" loading overlay — matches balance.it's
            "Building N custom recipes..." progress screen, staged to real async work. */}
        {loading && (
          <div className="fixed inset-0 z-[300] flex items-center justify-center p-4" style={{ background: WHITE }}>
            <div className="text-center max-w-md w-full">
              <div className="w-24 h-24 rounded-full mx-auto mb-6 flex items-center justify-center"
                style={{ background: "#eef7f2", border: `2px solid ${GREEN}` }}>
                <Leaf className="w-10 h-10" style={{ color: GREEN }} />
              </div>
              <h2 className="font-bold text-2xl mb-6" style={{ color: GREEN }}>
                Building your custom nutrition plan{petName ? ` for ${petName}` : ""}
              </h2>
              <div className="flex items-center justify-between text-sm font-semibold mb-2">
                <span style={{ color: GREEN }}>{loadingStage + 1} of {LOADING_STAGES.length} complete</span>
                <span style={{ color: MUTED }}>{Math.round(((loadingStage + 1) / LOADING_STAGES.length) * 100)}%</span>
              </div>
              <div className="w-full h-2 rounded-full overflow-hidden mb-6" style={{ background: BORDER }}>
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${((loadingStage + 1) / LOADING_STAGES.length) * 100}%`, background: GREEN }} />
              </div>
              <p className="text-sm" style={{ color: SUB }}>{LOADING_STAGES[loadingStage]}</p>
            </div>
          </div>
        )}

        {/* Ingredient nutrition-info modal — opened by the "ⓘ" icon on a chip */}
        {infoItem && (() => {
          const info = findIngredientStates(infoItem);
          return (
            <div className="fixed inset-0 z-[200] flex items-center justify-center p-4"
              style={{ background: "rgba(0,0,0,0.45)" }}
              onClick={() => setInfoItem(null)}>
              <div className="rounded-xl w-full max-w-lg max-h-[80vh] overflow-y-auto"
                style={{ background: WHITE }}
                onClick={(e) => e.stopPropagation()}>
                <div className="sticky top-0 flex items-center justify-between px-5 py-4 border-b"
                  style={{ background: WHITE, borderColor: BORDER }}>
                  <div>
                    <p className="font-bold text-base" style={{ color: TEXT }}>
                      {info?.professionalName ?? infoItem}{info?.hindi ? ` · ${info.hindi}` : ""}
                    </p>
                    <p className="text-xs" style={{ color: MUTED }}>Per 100g</p>
                  </div>
                  <button onClick={() => setInfoItem(null)}
                    className="text-lg leading-none px-2" style={{ color: MUTED }}>×</button>
                </div>
                <div className="p-5">
                  {!info ? (
                    <p className="text-sm" style={{ color: MUTED }}>
                      Detailed nutrient data isn&apos;t in our database for this ingredient yet.
                    </p>
                  ) : (
                    <div className="space-y-6">
                      {info.variants.map((v) => (
                        <div key={v.id}>
                          <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: GREEN }}>
                            {v.state ? formatStateLabel(v.state) : "Raw"}
                          </p>
                          <div className="rounded-lg overflow-hidden" style={{ border: `1px solid ${BORDER}` }}>
                            {Object.entries(v.nutrients).length === 0 ? (
                              <p className="text-xs p-3" style={{ color: MUTED }}>No data for this state.</p>
                            ) : (
                              Object.entries(v.nutrients).map(([k, val], i) => (
                                <div key={k}
                                  className="flex items-center justify-between px-3 py-2 text-sm"
                                  style={{ background: i % 2 === 0 ? WHITE : BG }}>
                                  <span style={{ color: SUB }}>{NUTRIENT_LABELS[k] ?? k}</span>
                                  <span className="font-semibold" style={{ color: TEXT }}>
                                    {val as number} {k === "energy" ? "kcal" : NUTRIENT_UNITS[k] ?? "g"}
                                  </span>
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })()}
    </div>
  );
}
