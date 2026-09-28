"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Camera, RefreshCw, Loader2, Bell, BellRing } from "lucide-react";
import AppShell from "@/components/app/AppShell";
import {
  saveMealPhoto, getMealPhotoHistory, getAllAnalyses, todayDateStr,
  getOrCreateProfile, type MealPhotoEntry, type UserProfile, type AnalysisEntry,
} from "@/lib/db";
import { analyzeFoodPhoto, type FoodPhotoProfile } from "@/lib/api";
import {
  requestNotificationPermission, scheduleFoodPhotoReminder, isNotificationsSupported,
} from "@/lib/notifications";
import { toast } from "@/lib/toast";
import { BIOMARKER_MAP } from "@/lib/blood-biomarker-map";

const GREEN  = "#1d5c3d";
const BG     = "#f7f8f6";
const BORDER = "#e4e7e2";
const TEXT   = "#1a1a1a";
const MUTED  = "#6b7280";

const MEALS = ["Breakfast", "Lunch", "Snacks", "Dinner"] as const;
type Meal = typeof MEALS[number];
const MEAL_EMOJI: Record<Meal, string> = { Breakfast: "🌅", Lunch: "☀️", Snacks: "🍎", Dinner: "🌙" };

// UserProfile.occupation doesn't share vocabulary with the backend's job_type
// list (activity_calorie_engine.JOB_TO_PAL_BASE) — map the closest match rather
// than pass through and silently fall back to "sedentary" every time.
const OCCUPATION_TO_JOB_TYPE: Record<string, string> = {
  sedentary: "sedentary", moderate: "nurse", heavy: "manual",
};

function profileToFoodPhotoProfile(p: UserProfile | null): FoodPhotoProfile | undefined {
  if (!p?.weight_kg || !p?.height_cm || !p?.age || !p?.gender) return undefined;
  return {
    weight_kg: p.weight_kg, height_cm: p.height_cm, age_years: p.age, sex: p.gender,
    job_type: OCCUPATION_TO_JOB_TYPE[p.occupation ?? "sedentary"] ?? "sedentary",
  };
}

function MealSlotCard({
  meal, entry, onCapture, busy,
}: { meal: Meal; entry: MealPhotoEntry | undefined; onCapture: (meal: Meal, file: File) => void; busy: boolean }) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!entry?.image) { setPreviewUrl(null); return; }
    const url = URL.createObjectURL(entry.image);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [entry?.image]);

  const inputId = `meal-photo-${meal}`;

  return (
    <div className="rounded-xl overflow-hidden" style={{ border: `1px solid ${BORDER}`, background: "#fff" }}>
      <div className="px-3 py-2 flex items-center justify-between" style={{ borderBottom: `1px solid ${BORDER}` }}>
        <span className="text-xs font-semibold" style={{ color: TEXT }}>{MEAL_EMOJI[meal]} {meal}</span>
        {busy && <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: MUTED }} />}
      </div>
      <label htmlFor={inputId} className="block cursor-pointer">
        <input
          id={inputId} type="file" accept="image/*" capture="environment" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) onCapture(meal, f); e.target.value = ""; }}
        />
        <div className="aspect-square flex flex-col items-center justify-center gap-1.5 relative" style={{ background: BG }}>
          {previewUrl ? (
            <>
              <img src={previewUrl} alt={meal} className="w-full h-full object-cover" />
              <div className="absolute bottom-1 right-1 rounded-full p-1.5" style={{ background: "rgba(0,0,0,0.55)" }}>
                <RefreshCw className="w-3 h-3 text-white" />
              </div>
            </>
          ) : (
            <>
              <Camera className="w-5 h-5" style={{ color: MUTED }} />
              <span className="text-[10px]" style={{ color: MUTED }}>Photo lo</span>
            </>
          )}
        </div>
      </label>
      {entry?.food_name && (
        <div className="px-3 py-2 space-y-0.5">
          <p className="text-xs font-semibold truncate" style={{ color: GREEN }}>{entry.food_name}</p>
          <p className="text-[10px]" style={{ color: MUTED }}>
            {entry.assumed_portion_g}g · {entry.kcal ?? 0} kcal
          </p>
        </div>
      )}
    </div>
  );
}

export default function FoodHistoryPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [today, setToday] = useState<Record<string, MealPhotoEntry>>({});
  const [history, setHistory] = useState<Record<string, MealPhotoEntry[]>>({});
  const [medicalHistory, setMedicalHistory] = useState<AnalysisEntry[]>([]);
  const [busyMeal, setBusyMeal] = useState<Meal | null>(null);
  const [notifEnabled, setNotifEnabled] = useState(false);
  const [todayLabel, setTodayLabel] = useState("");
  // "Notification" in window is a browser-only check — reading it during SSR
  // vs. the client's first render gives different answers and throws a
  // hydration mismatch (Next's own "typeof window !== 'undefined'" case).
  // Gate on this only after mount so server and first client render agree.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const todayStr = todayDateStr();

  // Locale-formatted date must not be rendered during SSR — the server and
  // client can disagree on locale/timezone at that instant, which throws a
  // hydration mismatch. Compute it client-side only, after mount.
  useEffect(() => {
    setTodayLabel(new Date().toLocaleDateString("hi-IN", { weekday: "long", day: "numeric", month: "long" }));
  }, []);

  const refresh = useCallback(async () => {
    const [hist, p, analyses] = await Promise.all([getMealPhotoHistory(), getOrCreateProfile(), getAllAnalyses()]);
    setProfile(p);
    setHistory(hist);
    // getAllAnalyses() already prunes anything past the 3-month retention window —
    // only keep entries that actually carry medical history / blood data to show here.
    setMedicalHistory(analyses.filter((a) => a.health_history?.length || a.medical_conditions?.length || (a.blood_values && Object.values(a.blood_values).some((v) => v !== undefined))));
    const todaysEntries = hist[todayStr] ?? [];
    const map: Record<string, MealPhotoEntry> = {};
    for (const e of todaysEntries) map[e.meal] = e;
    setToday(map);
  }, [todayStr]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    if (isNotificationsSupported() && Notification.permission === "granted") {
      setNotifEnabled(true);
      scheduleFoodPhotoReminder();
    }
  }, []);

  const enableReminder = async () => {
    const granted = await requestNotificationPermission();
    if (granted) {
      scheduleFoodPhotoReminder();
      setNotifEnabled(true);
      toast.success("Daily reminder set ho gaya! Roz raat 8 baje.");
    } else {
      toast.warning("Notification permission denied hai.");
    }
  };

  const handleCapture = async (meal: Meal, file: File) => {
    setBusyMeal(meal);
    try {
      // Save the photo immediately — recognition is best-effort and must never
      // block or lose the photo if the backend is unreachable.
      let saved: Omit<MealPhotoEntry, "id"> = {
        date: todayStr, meal, timestamp: Date.now(), image: file,
      };
      try {
        const result = await analyzeFoodPhoto(file, profileToFoodPhotoProfile(profile));
        const top = result.items?.[0];
        if (result.available && top) {
          saved = {
            ...saved,
            food_name: top.food_name,
            confidence: top.confidence,
            assumed_portion_g: top.assumed_portion_g,
            standard_portion_g: top.standard_portion_g,
            portion_personalized: top.portion_personalized,
            kcal: top.kcal,
            nutrients: top.nutrients,
            note: result.note,
          };
        }
      } catch {
        // Recognition best-effort only — the photo itself is always saved regardless.
      }
      await saveMealPhoto(saved);
      await refresh();
    } finally {
      setBusyMeal(null);
    }
  };

  return (
    <AppShell>
      <div className="px-4 sm:px-8 py-8 max-w-5xl mx-auto space-y-6">
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <p className="text-xs font-semibold uppercase tracking-widest mb-0.5" style={{ color: "#9aa5ae" }}>
            Har din ka khana, photo se
          </p>
          <h1 className="font-display font-bold text-2xl" style={{ color: TEXT }}>Your Medical and Food</h1>
        </motion.div>

        {/* Daily reminder */}
        {mounted && isNotificationsSupported() && (
          <div className="rounded-xl p-4 flex items-center justify-between"
            style={{ background: "#ffffff", border: `1px solid ${BORDER}` }}>
            <div className="flex items-center gap-2.5">
              {notifEnabled ? <BellRing className="w-4 h-4" style={{ color: GREEN }} /> : <Bell className="w-4 h-4" style={{ color: MUTED }} />}
              <div>
                <p className="text-sm font-medium" style={{ color: TEXT }}>Daily Reminder</p>
                <p className="text-xs" style={{ color: MUTED }}>
                  {notifEnabled ? "Roz raat 8 baje — jo meal photo missing hai uska reminder" : "Har din khana photo update karne ka reminder"}
                </p>
              </div>
            </div>
            <button onClick={enableReminder} disabled={notifEnabled}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{
                background: notifEnabled ? "#eef7f2" : "#f5f5f3",
                color: notifEnabled ? GREEN : TEXT,
              }}>
              {notifEnabled ? "✓ On" : "Enable"}
            </button>
          </div>
        )}

        {/* Today */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#9aa5ae" }}>
            Aaj{todayLabel ? ` — ${todayLabel}` : ""}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {MEALS.map((meal) => (
              <MealSlotCard key={meal} meal={meal} entry={today[meal]} onCapture={handleCapture} busy={busyMeal === meal} />
            ))}
          </div>
        </div>

        {/* Last 7 days — meal photos */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#9aa5ae" }}>
            Pichhle 7 Din — Meal Photos
          </p>
          <div className="space-y-3">
            {Object.keys(history).filter((d) => d !== todayStr).sort((a, b) => (a < b ? 1 : -1)).map((date) => (
              <div key={date} className="rounded-xl p-3" style={{ background: "#fff", border: `1px solid ${BORDER}` }}>
                <p className="text-xs font-semibold mb-2" style={{ color: TEXT }}>
                  {new Date(date).toLocaleDateString("hi-IN", { weekday: "short", day: "numeric", month: "short" })}
                </p>
                <div className="flex gap-2 flex-wrap">
                  {history[date].map((entry) => <MealPhotoThumb key={entry.id} entry={entry} />)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Last 3 months — medical history & blood reports */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#9aa5ae" }}>
            Pichhle 3 Mahine — Medical History
          </p>
          <div className="space-y-3">
            {medicalHistory.map((entry) => (
              <div key={entry.id} className="rounded-xl p-4" style={{ background: "#fff", border: `1px solid ${BORDER}` }}>
                <p className="text-xs font-semibold mb-2" style={{ color: TEXT }}>
                  {new Date(entry.timestamp).toLocaleDateString("hi-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" })}
                </p>
                {!!entry.medical_conditions?.length && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {entry.medical_conditions.map((c) => (
                      <span key={c} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: "#eef7f2", color: GREEN }}>{c}</span>
                    ))}
                  </div>
                )}
                {!!entry.health_history?.length && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {entry.health_history.map((h) => (
                      <span key={h} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: BG, color: MUTED }}>{h}</span>
                    ))}
                  </div>
                )}
                {entry.blood_values && Object.entries(entry.blood_values).filter(([, v]) => v !== undefined).length > 0 && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1 mt-1">
                    {Object.entries(entry.blood_values).filter(([, v]) => v !== undefined).map(([biomarker, v]) => (
                      <p key={biomarker} className="text-[11px]" style={{ color: MUTED }}>
                        {BIOMARKER_MAP[biomarker]?.label ?? biomarker}: <span style={{ color: TEXT, fontWeight: 600 }}>{v}</span> {BIOMARKER_MAP[biomarker]?.unit}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

      </div>
    </AppShell>
  );
}

function MealPhotoThumb({ entry }: { entry: MealPhotoEntry }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    const u = URL.createObjectURL(entry.image);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [entry.image]);
  return (
    <div className="w-16 shrink-0 text-center">
      <div className="w-16 h-16 rounded-lg overflow-hidden" style={{ background: BG, border: `1px solid ${BORDER}` }}>
        {url && <img src={url} alt={entry.meal} className="w-full h-full object-cover" />}
      </div>
      <p className="text-[9px] mt-1 truncate" style={{ color: MUTED }}>{MEAL_EMOJI[entry.meal]} {entry.food_name ?? entry.meal}</p>
    </div>
  );
}
