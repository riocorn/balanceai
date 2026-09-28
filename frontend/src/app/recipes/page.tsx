"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/app/AppShell";
import { getOrCreateProfile, getAllAnalyses, type UserProfile, type AnalysisEntry } from "@/lib/db";
import { api } from "@/lib/api";
import { ChefHat, MapPin, Thermometer, Droplets, Clock, Leaf, Fish, Egg, Flame } from "lucide-react";

const C = {
  bg:      "#f7f8f6",
  card:    "#ffffff",
  border:  "#e4e7e2",
  green:   "#1d5c3d",
  greenLt: "#eef7f2",
  text:    "#1a1a1a",
  sub:     "#5a6571",
  muted:   "#9aa5ae",
  amber:   "#d97706",
  red:     "#dc2626",
  teal:    "#0b4f6c",
};

const DIET_ICON: Record<string, React.ReactNode> = {
  veg:       <Leaf size={12} color="#1d5c3d" />,
  vegan:     <Leaf size={12} color="#16a34a" />,
  eggetarian:<Egg  size={12} color="#d97706" />,
  non_veg:   <Fish size={12} color="#0b4f6c" />,
};

const LEVEL_COLOR: Record<string, string> = {
  severe:   "#dc2626",
  moderate: "#d97706",
  mild:     "#ca8a04",
  normal:   "#1d5c3d",
};

const MEAL_BG: Record<string, string> = {
  breakfast: "#fff8ed",
  lunch:     "#f0fdf4",
  dinner:    "#eff6ff",
};
const MEAL_BORDER: Record<string, string> = {
  breakfast: "#fde68a",
  lunch:     "#bbf7d0",
  dinner:    "#bfdbfe",
};
const MEAL_LABEL: Record<string, string> = {
  breakfast: "🌅 Breakfast",
  lunch:     "☀️ Lunch",
  dinner:    "🌙 Dinner",
};

interface RecipeItem {
  id: string; name: string; meal_type: string; cuisine: string;
  diet: string; prep_time_min: number; ingredient_names: string[];
  tags: string[]; description: string; top_nutrients: string[];
  nutrition: Record<string, number>;
}
interface RecipeSet {
  set_number: number; score: number; highlight: string;
  breakfast: RecipeItem; lunch: RecipeItem; dinner: RecipeItem;
  nutrition_total: Record<string, number>;
  coverage_pct: Record<string, number>;
}
interface DayPlanResponse {
  city: string; state: string; season: string; season_hindi: string;
  region: string;
  weather: { temperature_c: number; humidity_pct: number; description: string; is_raining: boolean };
  deficient_nutrients: Array<{ key: string; display: string; level: string; target: number; unit: string }>;
  recipe_sets: RecipeSet[];
  targets: Record<string, { target: number; deficiency_level: string; display_name: string; unit: string }>;
}

const INDIA_STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
  "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
  "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
  "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh",
  "Uttarakhand","West Bengal","Delhi","Jammu and Kashmir","Ladakh","Chandigarh",
  "Puducherry","Goa",
];

const DIET_OPTIONS = [
  { value: "", label: "Any" },
  { value: "veg", label: "Vegetarian" },
  { value: "vegan", label: "Vegan" },
  { value: "eggetarian", label: "Eggetarian" },
  { value: "non_veg", label: "Non-Veg" },
];

export default function RecipesPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisEntry | null>(null);
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [diet, setDiet] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DayPlanResponse | null>(null);
  const [error, setError] = useState("");
  const [activeSet, setActiveSet] = useState(0);

  useEffect(() => {
    Promise.all([getOrCreateProfile(), getAllAnalyses()]).then(([p, analyses]) => {
      setProfile(p);
      if (analyses[0]) setLatestAnalysis(analyses[0]);
    });
  }, []);

  async function fetchPlan() {
    if (!city.trim() || !state) { setError("City aur State dono bharo"); return; }
    if (!profile?.age || !profile?.gender || !profile?.weight_kg || !profile?.height_cm) {
      setError("Profile me age, gender, weight, height bharo pehle"); return;
    }
    setLoading(true); setError(""); setData(null); setActiveSet(0);

    const deficiencies: Record<string, { probability: number; deficient: boolean; threshold: number }> = {};
    if (latestAnalysis?.predictions) {
      for (const p of latestAnalysis.predictions) {
        deficiencies[p.deficiency] = {
          probability: p.probability,
          deficient: p.risk_level === "high" || p.risk_level === "medium",
          threshold: 0.5,
        };
      }
    }

    const activityMap: Record<string, string> = {
      sedentary: "sedentary", moderate: "moderate", heavy: "active",
    };

    try {
      const res = await api.post("/api/recipe/day-plan", {
        city: city.trim(),
        state,
        age: profile.age,
        gender: profile.gender === "other" ? "female" : profile.gender,
        weight_kg: profile.weight_kg,
        height_cm: profile.height_cm,
        activity_level: activityMap[profile.occupation || "moderate"] || "moderate",
        life_stage: "normal",
        diet_filter: diet || null,
        deficiencies,
        n_sets: 8,
      });
      setData(res.data);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Backend se connect nahi ho pa raha");
    } finally {
      setLoading(false);
    }
  }

  const active = data?.recipe_sets[activeSet];

  return (
    <AppShell>
      <div style={{ maxWidth: 760, margin: "0 auto", padding: "24px 16px 80px" }}>

        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <ChefHat size={24} color={C.green} />
            <h1 style={{ fontSize: 22, fontWeight: 700, color: C.text }}>Recipe Maker AI</h1>
          </div>
          <p style={{ fontSize: 14, color: C.sub }}>
            Season + weather + tumhari nutritional need ke hisaab se aaj ke best meals
          </p>
        </div>

        {/* Input card */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20, marginBottom: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: C.sub, display: "block", marginBottom: 4 }}>City *</label>
              <input
                value={city} onChange={e => setCity(e.target.value)}
                placeholder="e.g. Mumbai"
                style={{ width: "100%", padding: "9px 12px", border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 14, outline: "none", boxSizing: "border-box" }}
              />
            </div>
            <div>
              <label style={{ fontSize: 12, color: C.sub, display: "block", marginBottom: 4 }}>State *</label>
              <select
                value={state} onChange={e => setState(e.target.value)}
                style={{ width: "100%", padding: "9px 12px", border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 14, outline: "none", background: "#fff", boxSizing: "border-box" }}
              >
                <option value="">Select state</option>
                {INDIA_STATES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, color: C.sub, display: "block", marginBottom: 4 }}>Diet preference</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {DIET_OPTIONS.map(d => (
                <button key={d.value} onClick={() => setDiet(d.value)}
                  style={{ padding: "6px 14px", borderRadius: 20, border: `1px solid ${diet === d.value ? C.green : C.border}`,
                    background: diet === d.value ? C.greenLt : "#fff",
                    color: diet === d.value ? C.green : C.sub,
                    fontSize: 13, cursor: "pointer", fontWeight: diet === d.value ? 600 : 400 }}>
                  {d.label}
                </button>
              ))}
            </div>
          </div>
          {error && <p style={{ fontSize: 13, color: C.red, marginBottom: 12 }}>{error}</p>}
          <button onClick={fetchPlan} disabled={loading}
            style={{ width: "100%", padding: "12px", background: loading ? C.muted : C.green,
              color: "#fff", border: "none", borderRadius: 8, fontSize: 15, fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer" }}>
            {loading ? "Weather + Recipes load ho raha hai..." : "Aaj ka Meal Plan Dekho"}
          </button>
        </div>

        {/* Weather + season strip */}
        {data && (
          <div style={{ background: C.teal, borderRadius: 10, padding: "14px 18px", marginBottom: 20, color: "#fff" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
              <MapPin size={14} /><span style={{ fontWeight: 600 }}>{data.city}, {data.state}</span>
              <span style={{ opacity: 0.7, fontSize: 13 }}>—</span>
              <span style={{ fontSize: 13, opacity: 0.9 }}>{data.season} ({data.season_hindi})</span>
              {data.weather.is_raining && <span style={{ fontSize: 12, background: "rgba(255,255,255,0.2)", padding: "2px 8px", borderRadius: 10 }}>🌧 Raining</span>}
            </div>
            <div style={{ display: "flex", gap: 16, fontSize: 13, opacity: 0.85, flexWrap: "wrap" }}>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}><Thermometer size={13} />{data.weather.temperature_c}°C</span>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}><Droplets size={13} />{data.weather.humidity_pct}% humidity</span>
              <span>{data.weather.description}</span>
            </div>
          </div>
        )}

        {/* Deficient nutrients */}
        {data && data.deficient_nutrients.length > 0 && (
          <div style={{ background: "#fff8ed", border: "1px solid #fde68a", borderRadius: 10, padding: "14px 18px", marginBottom: 20 }}>
            <p style={{ fontSize: 12, fontWeight: 600, color: C.amber, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Deficient nutrients — recipes inhe cover karenge
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {data.deficient_nutrients.map(n => (
                <span key={n.key} style={{ fontSize: 12, padding: "4px 10px", borderRadius: 12,
                  background: "#fff", border: `1px solid ${LEVEL_COLOR[n.level]}`,
                  color: LEVEL_COLOR[n.level], fontWeight: 500 }}>
                  {n.display} · {n.level} · {n.target}{n.unit}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Set selector tabs */}
        {data && data.recipe_sets.length > 0 && (
          <>
            <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4, marginBottom: 16 }}>
              {data.recipe_sets.map((s, i) => (
                <button key={s.set_number} onClick={() => setActiveSet(i)}
                  style={{ flexShrink: 0, padding: "8px 16px", borderRadius: 20,
                    border: `1px solid ${activeSet === i ? C.green : C.border}`,
                    background: activeSet === i ? C.green : "#fff",
                    color: activeSet === i ? "#fff" : C.sub,
                    fontSize: 13, fontWeight: activeSet === i ? 600 : 400, cursor: "pointer" }}>
                  Set {s.set_number}
                </button>
              ))}
            </div>

            {/* Active set highlight */}
            {active && (
              <div style={{ marginBottom: 16, fontSize: 13, color: C.green, fontWeight: 500, padding: "8px 14px", background: C.greenLt, borderRadius: 8 }}>
                ★ {active.highlight}
              </div>
            )}

            {/* 3 meal cards */}
            {active && (
              <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 24 }}>
                {(["breakfast", "lunch", "dinner"] as const).map(slot => {
                  const r = active[slot];
                  return (
                    <div key={slot} style={{ background: MEAL_BG[slot], border: `1px solid ${MEAL_BORDER[slot]}`, borderRadius: 12, padding: 18 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                        <div>
                          <p style={{ fontSize: 11, fontWeight: 600, color: C.muted, textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 2 }}>
                            {MEAL_LABEL[slot]}
                          </p>
                          <h3 style={{ fontSize: 17, fontWeight: 700, color: C.text }}>{r.name}</h3>
                          <p style={{ fontSize: 13, color: C.sub, marginTop: 2 }}>{r.description}</p>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: C.muted, flexShrink: 0, marginLeft: 12 }}>
                          <Clock size={12} />{r.prep_time_min}min
                        </div>
                      </div>

                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                        <span style={{ display: "flex", alignItems: "center", gap: 4, padding: "3px 8px", background: "#fff", border: `1px solid ${C.border}`, borderRadius: 10, fontSize: 11, color: C.sub }}>
                          {DIET_ICON[r.diet]}{r.diet}
                        </span>
                        <span style={{ padding: "3px 8px", background: "#fff", border: `1px solid ${C.border}`, borderRadius: 10, fontSize: 11, color: C.sub }}>
                          {r.cuisine}
                        </span>
                        {r.top_nutrients.map(n => (
                          <span key={n} style={{ padding: "3px 8px", background: "#fff", border: "1px solid #b6ddc9", borderRadius: 10, fontSize: 11, color: C.green }}>
                            {n}
                          </span>
                        ))}
                      </div>

                      <div style={{ fontSize: 12, color: C.sub }}>
                        <span style={{ fontWeight: 500 }}>Ingredients: </span>
                        {r.ingredient_names.join(", ")}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Coverage table */}
            {active && data.deficient_nutrients.length > 0 && (
              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18 }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 14 }}>
                  Nutrition Coverage — Set {active.set_number}
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {data.deficient_nutrients.map(n => {
                    const pct = Math.min(active.coverage_pct[n.key] || 0, 150);
                    const actual = active.nutrition_total[n.key] || 0;
                    const color = pct >= 80 ? "#1d5c3d" : pct >= 40 ? "#d97706" : "#dc2626";
                    return (
                      <div key={n.key}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 13 }}>
                          <span style={{ color: C.text, fontWeight: 500 }}>{n.display}</span>
                          <span style={{ color, fontWeight: 600 }}>
                            {actual.toFixed(1)}{n.unit} / {n.target}{n.unit} ({(active.coverage_pct[n.key] || 0).toFixed(0)}%)
                          </span>
                        </div>
                        <div style={{ height: 8, background: "#e5e7eb", borderRadius: 4, overflow: "hidden" }}>
                          <div style={{ height: "100%", width: `${Math.min(pct, 100)}%`, background: color, borderRadius: 4, transition: "width 0.4s ease" }} />
                        </div>
                        <p style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                          {n.level} deficiency
                          {pct < 40 && " · Supplement recommended"}
                          {pct >= 80 && " ✓"}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}

        {/* Empty state */}
        {!data && !loading && (
          <div style={{ textAlign: "center", padding: "48px 24px", color: C.muted }}>
            <ChefHat size={40} style={{ margin: "0 auto 12px", opacity: 0.3 }} />
            <p style={{ fontSize: 14 }}>City aur state bharo, aaj ka meal plan milega</p>
          </div>
        )}

      </div>
    </AppShell>
  );
}
