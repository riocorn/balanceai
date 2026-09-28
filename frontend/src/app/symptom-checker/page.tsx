"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import {
  ShieldCheck,
  Info,
  AlertTriangle,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Languages,
  Sparkles,
  Mic,
  Bot,
  Pill,
  ArrowRight,
  Stethoscope,
} from "lucide-react";
import { api } from "@/lib/api";
import { useCartStore } from "@/lib/cart-store";
import { isNonDrugIntervention, cleanMedicineName } from "@/lib/medicines";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import MedicinePackPlaceholder from "@/components/diag/MedicinePackPlaceholder";
import ScrollReveal from "@/components/diag/ScrollReveal";
import { Card } from "@/components/ui/card";
import { CATEGORY_TILES } from "@/components/diag/categories";
import { TEAL, BLUE, BG, SURFACE, TEXT, MUTED, EFFECTIVENESS, EFFECTIVENESS_TEXT, EMERGENCY, HERO_GRADIENT, ACCENT_PURPLE } from "@/components/diag/theme";

// ---------------------------------------------------------------------------
// Real API response shape (verified against routers/medical.py live source)
// ---------------------------------------------------------------------------
interface DiseaseOut {
  id: string;
  name: string;
}

interface MedicineOut {
  name: string;
  effectiveness_pct: number | null;
  is_curative: boolean;
  simple_explanation: string;
  sources: string[];
}

interface MedicalQueryResponse {
  matched: boolean;
  disease: DiseaseOut | null;
  understood_as: string | null;
  confidence: number;
  medicines: MedicineOut[];
  doctor_verification_required: boolean;
  disclaimer: string;
  hard_emergency_flag: boolean;
  possible_emergency: boolean;
  emergency_override_rule: string | null;
  message: string | null;
  redirect_to_whatsapp: boolean;
  whatsapp_link: string | null;
  // Two-turn clarifying-question flow (founder directive, 2026-09-28): a
  // symptom-style query never gets an LLM-guessed diagnosis — instead the
  // backend returns need_more_info=true with 2-4 real, KB-grounded
  // clarifying_questions the first time, and candidate_ids/translated_text
  // must be echoed back verbatim alongside the patient's answers on the
  // follow-up call for it to resolve to a real disease (or, failing that, the
  // real WhatsApp doctor fallback above).
  need_more_info: boolean;
  clarifying_questions: string[];
  candidate_ids: string[];
  translated_text: string | null;
}

interface QAPair {
  question: string;
  answer: string;
}

const TICKER_ITEMS = [
  "100% Doctor-Verified Before Any Suggestion",
  "Every Medicine Backed by Real Clinical Evidence",
  "Speak in Hindi, Hinglish or English",
  "Emergency Symptoms Flagged Instantly",
];

// Trust ladder / "How It Works" — doctor-first, patient-facing copy (no
// internal methodology language).
const TRUST_STEPS = [
  {
    icon: Languages,
    title: "Describe it, your way",
    detail:
      "Type your symptoms in whatever language feels natural. No forms, no medical terms to learn — just tell us what you're feeling.",
    accent: BLUE,
  },
  {
    icon: Stethoscope,
    title: "A doctor reviews it",
    detail:
      "Before anything is treated as final, a real doctor personally looks at your case and confirms it. Nothing reaches you without that check.",
    accent: TEAL,
  },
  {
    icon: ShieldCheck,
    title: "Get treatment you can trust",
    detail:
      "Once confirmed, you'll see your options with a clear picture of how each one helps — so you decide with confidence.",
    accent: EFFECTIVENESS,
  },
];

// Trust badges — shown as a compact chip row in the header and as a fuller
// icon+title+description band lower on the page. Each badge carries its own
// accent from the approved secondary palette for visual variety.
const TRUST_BADGES = [
  { icon: Stethoscope, title: "Doctor-Reviewed", detail: "Every suggestion is checked by a real doctor before it's treated as final.", accent: TEAL },
  { icon: Languages, title: "Speak Freely", detail: "English, Hindi, or Hinglish — describe things exactly as you'd tell a doctor.", accent: BLUE },
  { icon: Info, title: "Clear, Honest Information", detail: "You'll see what a treatment does and how it helps, explained simply.", accent: ACCENT_PURPLE },
  { icon: ShieldCheck, title: "No Pressure", detail: "We're here to help you find the right care, not to rush you into buying anything.", accent: EFFECTIVENESS },
];

const HERO_SLIDES: { badge: string; headline: string; sub: string }[] = [
  {
    badge: "Doctor-Verified Guidance",
    headline: "Tell us what's wrong. We'll find the right treatment.",
    sub: "Describe your symptoms in your own words — English, Hindi, or Hinglish. We'll match you with the latest, doctor-reviewed treatment for your condition.",
  },
  {
    badge: "Doctor Confirmation",
    headline: "A doctor always has the final word.",
    sub: "A licensed doctor personally reviews every suggestion, so you never act on the wrong medicine.",
  },
  {
    badge: "Real Medical Research",
    headline: "Grounded in the latest international medical research.",
    sub: "No generic advice, no guesswork — every treatment we suggest reflects the latest medical evidence available today.",
  },
];

const FAQ_ITEMS: { q: string; a: string }[] = [
  {
    q: "Will an AI decide my treatment?",
    a: "No. BalanceAI only suggests possibilities based on real medical information. A doctor always reviews and confirms before anything is considered final.",
  },
  {
    q: "What happens after I get my results?",
    a: "You can ask a doctor to confirm the suggestion. Right now a doctor reviews each case personally and replies over WhatsApp — we're working on making this faster.",
  },
  {
    q: "What if my symptoms could be serious?",
    a: "BalanceAI flags anything that looks like an emergency right away and tells you to go to the nearest hospital or call 108 immediately. Never wait for an online response in an emergency.",
  },
  {
    q: "Is my information kept private?",
    a: "We take this seriously and our privacy policy is still being finalized — it will be published here before it's needed.",
  },
  {
    q: "Will I have to pay to use this?",
    a: "Pricing is still being finalized. Any cost will always be shown clearly before you buy anything — nothing hidden.",
  },
];

function SectionHeading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div className="text-center mb-10">
      <span
        className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest mb-3"
        style={{ color: "#0A646D" }}
      >
        <span className="w-6 h-[3px] rounded-full" style={{ background: HERO_GRADIENT }} />
        {eyebrow}
        <span className="w-6 h-[3px] rounded-full" style={{ background: HERO_GRADIENT }} />
      </span>
      <h2 className="font-display font-bold text-3xl" style={{ color: TEXT }}>
        {title}
      </h2>
    </div>
  );
}

function confidencePhrase(confidence: number): string {
  if (confidence >= 0.85) return "We're confident about this";
  if (confidence >= 0.6) return "This looks likely — worth confirming";
  return "Our best guess — please have a doctor confirm this";
}

function isHttpUrl(s: string): boolean {
  try {
    const u = new URL(s);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export default function SymptomCheckerPage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MedicalQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [doctorRequestSent, setDoctorRequestSent] = useState(false);
  // Clarifying-question flow: the original patient text for this whole Q&A
  // thread (needed again on the follow-up call, since the box itself may
  // already hold a new draft by the time the patient answers) and the
  // in-progress answers, keyed by question index.
  const [originalQueryText, setOriginalQueryText] = useState("");
  const [clarifyAnswers, setClarifyAnswers] = useState<string[]>([]);
  const [submittingAnswers, setSubmittingAnswers] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [bannerCollapsed, setBannerCollapsed] = useState(false);
  const [slide, setSlide] = useState(0);
  const [heroVisible, setHeroVisible] = useState(false);

  const cartItems = useCartStore((s) => s.items);
  const addCartItem = useCartStore((s) => s.addItem);

  const heroSectionRef = useRef<HTMLDivElement>(null);
  const heroCardRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.title = "Find Treatment — BalanceAI";
  }, []);

  // Hero entrance animation — real load-in motion (fade + rise) for the
  // floating search card, distinct from the framer-motion slide transitions
  // used for the rotating headline above it.
  //
  // Real root cause of the recurring "hero input box disappeared" bug: the
  // previous implementation used an imperative GSAP `gsap.fromTo()` call in
  // a useEffect, guarded by checking the element's *current* computed
  // opacity before re-animating. That guard was itself broken — on a fresh,
  // never-animated DOM node, `getComputedStyle`/`gsap.getProperty` reports
  // opacity as "1" by CSS default (verified live: polling the card's
  // computed opacity at 50ms resolution across a cold Turbopack compile and
  // a brand-new browser profile, it never once left "1" — the tween was
  // dead code on every normal load). The only way the card's opacity could
  // ever leave 1 was if gsap had already pushed it below 1 on that same DOM
  // node and a second overlapping effect invocation (Fast Refresh or React
  // Strict Mode double-invoking effects while racing a same-node re-render)
  // interrupted the tween before it finished — an inherently fragile trap,
  // because GSAP mutates the element's inline style imperatively, outside
  // React's render cycle, so an interruption can leave it stuck with no way
  // for React to self-heal it. That's a structural flaw, not a one-off race
  // to patch around.
  //
  // Fix: drop GSAP for this element entirely and drive the fade with a
  // declarative CSS transition keyed off React state (`heroVisible`). This
  // can't get stuck: every render computes its opacity/transform classes
  // fresh from that boolean, so however many times the effect below reruns
  // (Strict Mode, Fast Refresh, real remounts), the worst case is a harmless
  // re-play of the same fade-in — never a permanently invisible card.
  useEffect(() => {
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => setHeroVisible(true));
    });
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    if (result && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  // Real deep-link support: the shared header's one real AI input navigates
  // here with ?q=<text>&autoSubmit=1 from every other page, since that's now
  // the only input box on the site and it always submits immediately — no
  // fake data, no separate prefill-only step.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    const autoSubmit = params.get("autoSubmit") === "1";
    if (q) {
      setText(q);
      if (autoSubmit) {
        submitQuery(q);
        window.setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 300);
      } else {
        scrollToHero();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Hero dot-indicator carousel — real, auto-advancing, matches the same
  // pattern already used on /pharmacy for full-site consistency.
  useEffect(() => {
    const id = setInterval(() => setSlide((s) => (s + 1) % HERO_SLIDES.length), 5000);
    return () => clearInterval(id);
  }, [slide]);

  function scrollToHero() {
    heroSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Used by the shared header's one real AI input (and its Row C quick-link
  // category buttons) when the user is already on this page — fills the
  // page's own query state, scrolls to the hero status area, and immediately
  // kicks off the real /medical/query call in place rather than navigating
  // away.
  function fillStarterAndSubmit(starter: string) {
    setText(starter);
    scrollToHero();
    submitQuery(starter);
  }

  async function submitQuery(overrideText?: string) {
    const trimmed = (overrideText ?? text).trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<MedicalQueryResponse>(
        "/medical/query",
        { text: trimmed },
        { timeout: 300000 }
      );
      setResult(data);
      setDoctorRequestSent(false);
      setBannerCollapsed(false);
      setOriginalQueryText(trimmed);
      setClarifyAnswers(data.need_more_info ? new Array(data.clarifying_questions.length).fill("") : []);
    } catch (err) {
      setError(
        "Something went wrong — the medical understanding service isn't available right now. Please try again shortly."
      );
      setResult(null);
      console.error("medical/query failed", err);
    } finally {
      setLoading(false);
    }
  }

  // Turn 2 of the clarifying-question flow: re-POST the SAME original text
  // plus the patient's real answers, echoing candidate_ids/translated_text
  // back verbatim exactly as the backend requires to resolve against the
  // same real candidate shortlist from turn one (never re-derived client
  // side, never a fresh guess).
  async function submitClarifyingAnswers() {
    if (!result || !result.need_more_info || submittingAnswers) return;
    const qaHistory: QAPair[] = result.clarifying_questions.map((q, i) => ({
      question: q,
      answer: (clarifyAnswers[i] || "").trim(),
    }));
    if (qaHistory.some((qa) => !qa.answer)) return;

    setSubmittingAnswers(true);
    setError(null);
    try {
      const { data } = await api.post<MedicalQueryResponse>(
        "/medical/query",
        {
          text: originalQueryText,
          qa_history: qaHistory,
          candidate_ids: result.candidate_ids,
          translated_text: result.translated_text,
        },
        { timeout: 300000 }
      );
      setResult(data);
      setDoctorRequestSent(false);
      setBannerCollapsed(false);
      setClarifyAnswers(data.need_more_info ? new Array(data.clarifying_questions.length).fill("") : []);
    } catch (err) {
      setError(
        "Something went wrong — the medical understanding service isn't available right now. Please try again shortly."
      );
      console.error("medical/query (clarifying answers) failed", err);
    } finally {
      setSubmittingAnswers(false);
    }
  }

  function addToCart(medicineName: string, diseaseName: string, diseaseId: string, effectivenessPct: number | null, isCurative: boolean) {
    addCartItem({
      name: medicineName,
      disease_id: diseaseId,
      disease_name: diseaseName,
      type: isCurative ? "Curative" : "Symptom relief",
      mechanism: "",
      effectiveness_pct: effectivenessPct,
    });
  }

  const showEmergencyBanner = !!(result && (result.hard_emergency_flag || result.possible_emergency));

  // Only real purchasable medicines are ever shown as result cards — non-drug
  // interventions (diet/lifestyle/physiotherapy/surgery/exercise-programme
  // entries real in the clinical data but not something we can sell) are
  // excluded entirely, not shown with a label, per the founder's explicit
  // "purchasable items only" rule.
  const purchasableMedicines = result ? result.medicines.filter((m) => !isNonDrugIntervention(m.name)) : [];

  return (
    <main style={{ background: BG, minHeight: "100vh" }} className="font-sans">
      <SiteHeader active="symptoms" onQuickFillAndSubmit={fillStarterAndSubmit} />

      {/* Emergency banner: only condition on which EMERGENCY red is ever used */}
      {showEmergencyBanner && (
        <div
          role="alert"
          className="sticky top-[166px] z-40 w-full"
          style={{ background: EMERGENCY, color: "#FFFFFF" }}
        >
          {bannerCollapsed ? (
            <button
              onClick={() => setBannerCollapsed(false)}
              className="w-full flex items-center justify-center gap-2 px-4 py-1.5 text-xs font-semibold"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Emergency warning — tap to expand
            </button>
          ) : (
            <div className="max-w-4xl mx-auto px-4 py-3 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="flex-1 text-sm leading-relaxed">
                <p className="font-semibold">
                  ⚠ These symptoms may indicate a medical emergency. Please go to your nearest hospital's
                  emergency room immediately, or call 108. Nothing on this page is a reason to wait in an
                  emergency.
                </p>
                {result?.emergency_override_rule && (
                  <p className="mt-1 font-medium">{result.emergency_override_rule}</p>
                )}
              </div>
              <button
                onClick={() => setBannerCollapsed(true)}
                aria-label="Collapse emergency banner"
                className="text-xs underline opacity-90 shrink-0 mt-0.5"
              >
                Collapse
              </button>
            </div>
          )}
        </div>
      )}

      {/* Hero */}
      <section ref={heroSectionRef} className="relative">
        {/* Full-bleed colored band */}
        <div
          className="relative overflow-hidden pt-14 pb-36 sm:pb-40 px-4 rounded-b-[32px] sm:rounded-b-[48px]"
          style={{ background: HERO_GRADIENT }}
        >
          {/* Real photography backdrop — doctors reviewing a case together,
              tinted with the brand gradient so the white headline text stays
              fully legible (Unsplash, license-clear, verified 2026-09-28). */}
          <Image
            src="https://images.unsplash.com/photo-1666214280391-8ff5bd3c0bf0?auto=format&fit=crop&w=1600&q=75"
            alt=""
            fill
            priority
            sizes="100vw"
            className="object-cover pointer-events-none"
            aria-hidden="true"
          />
          {/* A near-opaque overlay across the WHOLE hero previously hid the
              real photo almost entirely (read as a flat gradient again,
              defeating the point of using real photography). The brand tint
              is now light and even, and the actual contrast work is done by
              the localized scrim below — strong only behind the left-aligned
              text column, fading out so the photo is genuinely visible on
              the right/illustration side. */}
          <div className="absolute inset-0 pointer-events-none" aria-hidden="true" style={{ background: HERO_GRADIENT, opacity: 0.38 }} />
          {/* Left-side scrim — the headline/search copy is left-aligned, so it
              needs the strongest contrast on that side; the photo is left
              clearly visible toward the right/illustration column. */}
          <div
            className="absolute inset-0 pointer-events-none"
            aria-hidden="true"
            style={{ background: "linear-gradient(100deg, rgba(3,15,18,0.82) 0%, rgba(3,15,18,0.66) 42%, rgba(3,15,18,0.25) 68%, rgba(3,15,18,0) 88%)" }}
          />
          {/* Dense dot-grid texture — deliberately not a soft blurred "SaaS
              gradient blob"; matches the tighter, information-dense visual
              language of real e-pharmacy hero banners */}
          <div
            className="absolute inset-0 opacity-[0.10] pointer-events-none"
            aria-hidden="true"
            style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "20px 20px" }}
          />

          {/* Rotating offer/trust ticker — mirrors the promo-carousel strip real pharmacy hero
              banners run edge-to-edge across the top of the banner */}
          <div
            className="relative -mx-4 mb-8 overflow-hidden ticker-wrap"
            style={{ background: "rgba(255,255,255,0.12)", borderTop: "1px solid rgba(255,255,255,0.22)", borderBottom: "1px solid rgba(255,255,255,0.22)" }}
            aria-hidden="true"
          >
            <div className="ticker-inner py-2">
              {[...TICKER_ITEMS, ...TICKER_ITEMS].map((t, i) => (
                <span
                  key={i}
                  className="flex items-center gap-2 px-6 whitespace-nowrap text-xs sm:text-sm font-semibold text-white shrink-0"
                >
                  <Sparkles className="w-3.5 h-3.5 shrink-0" style={{ color: "rgba(255,255,255,0.85)" }} />
                  {t}
                </span>
              ))}
            </div>
          </div>

          <div className="relative max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-10 items-center text-center lg:text-left">
            <div>
              {/* Real root cause of a reported "washed out" hero headline:
                  mode="wait" made the outgoing slide fade all the way to
                  opacity 0 BEFORE the incoming one faded back in, creating a
                  real ~0.7s low-contrast window every 5s (easy to catch in a
                  glance or a screenshot). Opacity now only dips to 0.9 for a
                  brief 150ms, instead of a full 0 -> 1 crossfade — the
                  headline stays high-contrast at every instant. */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={slide}
                  initial={{ opacity: 0.9, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0.9, y: -10 }}
                  transition={{ duration: 0.15, ease: "easeOut" }}
                >
                  <span
                    className="inline-block text-xs font-semibold px-3 py-1.5 rounded-full mb-5 backdrop-blur-sm"
                    style={{ background: "rgba(255,255,255,0.18)", color: "#FFFFFF", border: "1px solid rgba(255,255,255,0.35)" }}
                  >
                    {HERO_SLIDES[slide].badge}
                  </span>
                  <h1
                    className="font-display font-bold leading-tight mb-4 text-white"
                    style={{ fontSize: "clamp(2rem, 5vw, 3rem)" }}
                  >
                    {HERO_SLIDES[slide].headline}
                  </h1>
                  <p className="text-base leading-relaxed mb-5 max-w-xl mx-auto lg:mx-0" style={{ color: "rgba(255,255,255,0.92)" }}>
                    {HERO_SLIDES[slide].sub}
                  </p>
                </motion.div>
              </AnimatePresence>

              {/* carousel controls — real-measured dot + arrow mechanic (Netmeds
                  hero: circular semi-transparent chevrons + pill-shaped active dot) */}
              <div className="flex items-center gap-3 mb-6 justify-center lg:justify-start">
                <button
                  aria-label="Previous"
                  onClick={() => setSlide((s) => (s - 1 + HERO_SLIDES.length) % HERO_SLIDES.length)}
                  className="w-7 h-7 rounded-full flex items-center justify-center transition-colors duration-200 hover:bg-[rgba(255,255,255,0.22)]"
                  style={{ background: "rgba(255,255,255,0.14)", color: "#fff" }}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <div className="flex items-center gap-1.5">
                  {HERO_SLIDES.map((_, i) => (
                    <button
                      key={i}
                      aria-label={`Slide ${i + 1}`}
                      onClick={() => setSlide(i)}
                      className="flex items-center justify-center rounded-full transition-all duration-200"
                      style={{ width: 24, height: 24 }}
                    >
                      <span
                        className="rounded-full transition-all duration-200"
                        style={{ width: i === slide ? 20 : 6, height: 6, background: i === slide ? EFFECTIVENESS : "rgba(255,255,255,0.35)" }}
                      />
                    </button>
                  ))}
                </div>
                <button
                  aria-label="Next"
                  onClick={() => setSlide((s) => (s + 1) % HERO_SLIDES.length)}
                  className="w-7 h-7 rounded-full flex items-center justify-center transition-colors duration-200 hover:bg-[rgba(255,255,255,0.22)]"
                  style={{ background: "rgba(255,255,255,0.14)", color: "#fff" }}
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              <div className="flex flex-wrap justify-center lg:justify-start gap-x-5 gap-y-2 mb-6">
                {TRUST_BADGES.map(({ title }) => (
                  <span key={title} className="flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-white">
                    <ShieldCheck className="w-3.5 h-3.5 shrink-0" style={{ color: "rgba(255,255,255,0.85)" }} />
                    {title}
                  </span>
                ))}
              </div>

              {/* Trust seal — commercial framing, not a dataset statistic */}
              <div className="flex justify-center lg:justify-start">
                <div
                  className="flex items-center gap-3 rounded-2xl px-5 py-3.5 transition-all duration-200 hover:-translate-y-1"
                  style={{ background: SURFACE, boxShadow: "0 14px 30px rgba(11,32,39,0.22)" }}
                >
                  <div
                    className="w-11 h-11 rounded-full flex items-center justify-center shrink-0"
                    style={{ background: HERO_GRADIENT }}
                  >
                    <ShieldCheck className="w-5 h-5 text-white" strokeWidth={2.25} />
                  </div>
                  <div className="text-left">
                    <p className="font-display font-extrabold text-base leading-tight" style={{ color: TEXT }}>
                      Trusted Treatments, Verified by Doctors
                    </p>
                    <p className="text-[11px] font-semibold mt-0.5" style={{ color: MUTED }}>
                      Every suggestion is checked before it reaches you
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Bold illustration: speak -> AI+doctor -> medicine */}
            <div className="flex items-center justify-center gap-2 sm:gap-4" aria-hidden="true">
              {[
                { Icon: Mic, label: "Bolo" },
                { Icon: Bot, label: "AI + Doctor" },
                { Icon: Pill, label: "Medicine" },
              ].map(({ Icon, label }, idx, arr) => (
                <div key={label} className="flex items-center gap-2 sm:gap-4">
                  <div className="flex flex-col items-center gap-2">
                    <div
                      className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl flex items-center justify-center shadow-lg"
                      style={{ background: "#FFFFFF" }}
                    >
                      <Icon className="w-7 h-7 sm:w-9 sm:h-9" style={{ color: idx === 1 ? BLUE : TEAL }} />
                    </div>
                    <span className="text-[11px] sm:text-xs font-semibold text-white whitespace-nowrap">
                      {label}
                    </span>
                  </div>
                  {idx < arr.length - 1 && (
                    <ArrowRight className="w-5 h-5 sm:w-6 sm:h-6 shrink-0" style={{ color: "rgba(255,255,255,0.75)" }} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Trust ladder — glass cards floating on the colored band */}
          <div className="relative max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-4 mt-10 text-left">
            {TRUST_STEPS.map(({ icon: Icon, title }) => (
              <div
                key={title}
                className="rounded-2xl p-4 flex items-start gap-3 backdrop-blur-sm transition-all duration-200 hover:bg-[rgba(255,255,255,0.20)] hover:-translate-y-0.5"
                style={{ background: "rgba(255,255,255,0.14)", border: "1px solid rgba(255,255,255,0.28)" }}
              >
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                  style={{ background: "rgba(255,255,255,0.22)" }}
                >
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <p className="text-sm font-semibold leading-snug text-white">{title}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Status card, floating over the bottom edge of the colored band —
            the actual input now lives in the shared navbar next to the logo
            (the site's one real AI input box); this card just surfaces
            real loading/error feedback for a query submitted from there
            while already on this page. */}
        <div className="relative max-w-3xl mx-auto px-4 -mt-24 sm:-mt-28 pb-16">
          <div
            ref={heroCardRef}
            className={`rounded-2xl p-4 sm:p-6 transition-all duration-700 ease-out ${heroVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10"}`}
            style={{ background: SURFACE, border: "1px solid #E4EBEE", boxShadow: "0 20px 45px rgba(11,32,39,0.18)" }}
          >
            <p className="flex items-center gap-2 text-sm font-semibold" style={{ color: TEXT }}>
              {loading && <Loader2 className="w-4 h-4 animate-spin" style={{ color: TEAL }} />}
              {loading ? "Checking your symptoms..." : "Grounded in real, up-to-date medical evidence — never a guess."}
            </p>
            {loading && (
              <p className="text-xs mt-2" style={{ color: MUTED }}>
                This can take anywhere from 10 seconds to 2–3 minutes while we carefully check a real
                medical knowledge base.
              </p>
            )}
            {error && (
              <p className="text-xs mt-3 font-medium" style={{ color: "#B42318" }}>
                {error}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Results section */}
      {result && (
        <section ref={resultsRef} className="max-w-3xl mx-auto px-4 pb-20 scroll-mt-24">
          <div
            className="sc-card p-5 mb-5"
            style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
          >
            <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: MUTED }}>
              Here's how we understood you:
            </p>
            <p className="text-base font-medium mb-3" style={{ color: TEXT }}>
              {result.understood_as || "—"}
            </p>
            <button
              onClick={() => scrollToHero()}
              className="text-sm font-semibold underline decoration-2 underline-offset-2 transition-opacity duration-200 hover:opacity-70"
              style={{ color: BLUE }}
            >
              Did we get it wrong? Rewrite it
            </button>
          </div>

          {result.need_more_info ? (
            <div
              className="sc-card p-5 mb-5"
              style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
            >
              <p className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: MUTED }}>
                A couple more questions to narrow this down
              </p>
              <div className="space-y-4">
                {result.clarifying_questions.map((q, i) => (
                  <div key={i}>
                    <label className="text-sm font-medium block mb-1.5" style={{ color: TEXT }}>
                      {q}
                    </label>
                    <input
                      type="text"
                      value={clarifyAnswers[i] || ""}
                      onChange={(e) =>
                        setClarifyAnswers((prev) => {
                          const next = [...prev];
                          next[i] = e.target.value;
                          return next;
                        })
                      }
                      placeholder="Your answer..."
                      className="w-full rounded-lg px-3.5 py-2.5 text-sm outline-none"
                      style={{ border: "1px solid #D5DEE1", color: TEXT }}
                    />
                  </div>
                ))}
              </div>
              <button
                onClick={submitClarifyingAnswers}
                disabled={submittingAnswers || result.clarifying_questions.some((_, i) => !(clarifyAnswers[i] || "").trim())}
                className="mt-5 w-full sm:w-auto rounded-full px-6 py-3 text-sm font-bold text-white shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 disabled:opacity-50 disabled:hover:translate-y-0 disabled:hover:shadow-md"
                style={{ background: HERO_GRADIENT }}
              >
                {submittingAnswers ? "Checking..." : "Continue"}
              </button>
            </div>
          ) : result.matched && result.disease ? (
            <div
              className="sc-card p-5 mb-5 flex items-start gap-4"
              style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
            >
              <div
                className="w-14 h-14 rounded-full flex items-center justify-center shrink-0"
                style={{ background: HERO_GRADIENT, boxShadow: "0 8px 18px rgba(14,124,134,0.28)" }}
              >
                <Stethoscope className="w-6 h-6 text-white" strokeWidth={2} />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: MUTED }}>
                  Possible match
                </p>
                <h2 className="font-display font-bold text-2xl mb-2 leading-tight" style={{ color: TEXT }}>
                  {result.disease.name}
                </h2>
                <span
                  className="inline-block text-xs font-semibold px-2.5 py-1 rounded-full"
                  style={{ background: "rgba(14,124,134,0.10)", color: TEAL }}
                >
                  {confidencePhrase(result.confidence)}
                </span>
              </div>
            </div>
          ) : (
            <div
              className="sc-card p-5 mb-5"
              style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
            >
              <p className="text-sm leading-relaxed" style={{ color: TEXT }}>
                {result.message || "No confident disease match was found for this complaint."}
              </p>
            </div>
          )}

          {!result.matched && !result.need_more_info && (
            <DoctorCTA
              sent={doctorRequestSent}
              onClick={() => setDoctorRequestSent(true)}
              whatsappLink={result.redirect_to_whatsapp ? result.whatsapp_link : null}
            />
          )}

          {result.matched && (
            <>
              {purchasableMedicines.length > 0 && (
                <div className="space-y-4 mb-5">
                  {purchasableMedicines.map((m) => {
                    const inCart = cartItems.some((i) => i.name === cleanMedicineName(m.name));
                    const firstSource = m.sources[0];
                    const pct = m.effectiveness_pct != null ? Math.round(m.effectiveness_pct) : null;
                    return (
                      <Card
                        key={m.name}
                        className="!ring-0 !py-0 sc-card sc-card-interactive p-5"
                        style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
                      >
                        <div className="flex items-start gap-4">
                          <div className="relative w-16 h-16 shrink-0">
                            <MedicinePackPlaceholder />
                            <div
                              className="sc-icon-pop absolute -bottom-1.5 -right-1.5 w-7 h-7 rounded-full flex items-center justify-center border-2"
                              style={{
                                background: m.is_curative
                                  ? `linear-gradient(135deg, ${EFFECTIVENESS} 0%, ${TEAL} 100%)`
                                  : HERO_GRADIENT,
                                borderColor: SURFACE,
                              }}
                            >
                              <Pill className="w-3.5 h-3.5 text-white" strokeWidth={2.25} />
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-3">
                              <h3 className="font-bold text-base leading-snug" style={{ color: TEXT }}>
                                {cleanMedicineName(m.name)}
                              </h3>
                              {pct != null && (
                                <div className="shrink-0 text-right">
                                  <p className="font-display font-extrabold text-2xl leading-none" style={{ color: EFFECTIVENESS_TEXT }}>
                                    {pct}%
                                  </p>
                                  <p className="text-[10px] font-semibold uppercase tracking-wide mt-0.5" style={{ color: MUTED }}>
                                    Effective
                                  </p>
                                </div>
                              )}
                            </div>
                            <span
                              className="inline-block mt-1.5 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
                              style={{
                                background: m.is_curative ? "rgba(31,174,122,0.12)" : "rgba(91,116,128,0.12)",
                                color: m.is_curative ? EFFECTIVENESS_TEXT : MUTED,
                              }}
                            >
                              {m.is_curative ? "Curative" : "Symptom relief"}
                            </span>
                          </div>
                        </div>

                        {pct != null && (
                          <div
                            className="w-full h-2 rounded-full overflow-hidden mt-4"
                            style={{ background: "#E4EBEE" }}
                          >
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${Math.min(100, Math.max(0, pct))}%`, background: EFFECTIVENESS }}
                            />
                          </div>
                        )}

                        <p className="text-sm leading-relaxed mt-4 mb-3" style={{ color: MUTED }}>
                          {m.simple_explanation}
                        </p>

                        {firstSource && (
                          <p className="text-xs mb-4 break-words" style={{ color: MUTED }}>
                            Source:{" "}
                            {isHttpUrl(firstSource) ? (
                              <a
                                href={firstSource}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline transition-opacity duration-200 hover:opacity-70"
                                style={{ color: BLUE }}
                              >
                                {firstSource}
                              </a>
                            ) : (
                              <span>{firstSource}</span>
                            )}
                          </p>
                        )}

                        <div className="flex items-center justify-between gap-3 pt-1 border-t" style={{ borderColor: "#EEF3F5" }}>
                          <button
                            onClick={() => addToCart(cleanMedicineName(m.name), result.disease!.name, result.disease!.id, m.effectiveness_pct, m.is_curative)}
                            disabled={inCart}
                            className="mt-4 text-sm font-semibold rounded-full px-5 py-2 border transition-all duration-200 hover:bg-[rgba(30,111,217,0.08)] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-60 disabled:hover:bg-transparent disabled:hover:translate-y-0"
                            style={{ borderColor: BLUE, color: BLUE, background: "transparent" }}
                            title="Placeholder — no real payment/checkout is implemented yet"
                          >
                            {inCart ? "Added to cart" : "Buy Now"}
                          </button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}

              <div
                className="rounded-2xl p-4 mb-5 flex items-start gap-3"
                style={{ background: "#EEF3F5", border: "1px solid #E4EBEE" }}
              >
                <Info className="w-4 h-4 shrink-0 mt-0.5" style={{ color: MUTED }} />
                <p className="text-xs leading-relaxed" style={{ color: MUTED }}>
                  <span className="font-semibold" style={{ color: TEXT }}>Before you take anything, please read this: </span>
                  {result.disclaimer}
                </p>
              </div>

              <DoctorCTA sent={doctorRequestSent} onClick={() => setDoctorRequestSent(true)} />
            </>
          )}
        </section>
      )}

      {/* Category tiles */}
      <section id="categories" className="max-w-5xl mx-auto px-4 pb-20 scroll-mt-24">
        <SectionHeading eyebrow="Browse by category" title="Browse real medicines by health area" />
        {/* Horizontally scrollable circular category strip — mirrors the real
            "shop by category" structural pattern used across pharmacy/health apps.
            Each tile takes you to a real, filtered view of the medicine catalog
            for that health area — a distinct action from the header's quick-link
            strip, which instead pre-fills the symptom-checker input. */}
        <ScrollReveal className="flex gap-5 sm:gap-7 overflow-x-auto pb-3 px-1 -mx-1 snap-x snap-proximity [scrollbar-width:thin]" stagger={0.05} y={16}>
          {CATEGORY_TILES.map(({ label, icon: Icon, accent, image, medicinesQuery }) => (
            <Link
              key={label}
              href={`/medicines?q=${encodeURIComponent(medicinesQuery)}`}
              className="group shrink-0 snap-start w-20 sm:w-24 flex flex-col items-center gap-3 text-center"
            >
              <div
                className="relative w-16 h-16 sm:w-20 sm:h-20 rounded-full overflow-hidden transition-all duration-200 group-hover:-translate-y-1 group-hover:scale-105 group-active:translate-y-0 group-active:scale-100"
                style={{ boxShadow: "0 8px 20px rgba(11,32,39,0.22), 0 3px 8px rgba(11,32,39,0.14)" }}
              >
                {/* Real, license-clear Unsplash photo per category, tinted with
                    the tile's accent so the icon stays legible on top — verified
                    by direct download before wiring in 2026-09-28. */}
                <Image src={`${image}?auto=format&fit=crop&w=200&q=70`} alt="" fill sizes="80px" className="object-cover" />
                <div
                  className="absolute inset-0"
                  style={{ background: `linear-gradient(150deg, ${accent}b3 0%, ${TEAL}99 100%)` }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-white drop-shadow-sm" strokeWidth={2} />
                </div>
              </div>
              <span className="text-xs sm:text-sm font-semibold leading-snug" style={{ color: TEXT }}>
                {label}
              </span>
            </Link>
          ))}
        </ScrollReveal>
      </section>

      {/* Trust claims band — layered gradient + texture, not a flat fill */}
      <section
        className="relative w-full py-14 px-4 overflow-hidden"
        style={{ background: `linear-gradient(120deg, ${TEAL} 0%, ${TEAL} 35%, ${BLUE} 100%)` }}
      >
        {/* Real photography backdrop — a doctor checking a patient's blood
            pressure — tinted with the same brand gradient (Unsplash,
            license-clear, verified 2026-09-28). */}
        <Image
          src="https://images.unsplash.com/photo-1631815589968-fdb09a223b1e?auto=format&fit=crop&w=1600&q=75"
          alt=""
          fill
          sizes="100vw"
          className="object-cover pointer-events-none"
          aria-hidden="true"
        />
        <div
          className="absolute inset-0 pointer-events-none"
          aria-hidden="true"
          style={{ background: `linear-gradient(120deg, ${TEAL} 0%, ${TEAL} 35%, ${BLUE} 100%)`, opacity: 0.85 }}
        />
        <div
          className="absolute inset-0 opacity-[0.10] pointer-events-none"
          aria-hidden="true"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "26px 26px" }}
        />
        <ScrollReveal className="relative max-w-5xl mx-auto grid sm:grid-cols-2 gap-4">
          {TRUST_BADGES.map(({ icon: Icon, title, detail, accent }) => (
            <div
              key={title}
              className="group sc-card sc-card-interactive p-5 flex items-start gap-4"
              style={{ background: SURFACE, boxShadow: "0 14px 30px rgba(11,32,39,0.20)" }}
            >
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center shrink-0 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-6"
                style={{ background: `linear-gradient(135deg, ${accent} 0%, ${TEAL} 100%)`, boxShadow: "0 6px 14px rgba(11,32,39,0.20)" }}
              >
                <Icon className="w-5 h-5 text-white" strokeWidth={2.25} />
              </div>
              <div>
                <p className="text-sm font-bold mb-1" style={{ color: TEXT }}>
                  {title}
                </p>
                <p className="text-xs leading-relaxed" style={{ color: MUTED }}>
                  {detail}
                </p>
              </div>
            </div>
          ))}
        </ScrollReveal>
      </section>

      {/* How It Works — tinted full-bleed band for color rhythm */}
      <section
        id="how-it-works"
        className="w-full py-20 px-4 scroll-mt-24"
        style={{ background: "rgba(30,111,217,0.05)" }}
      >
        <div className="max-w-4xl mx-auto">
          <SectionHeading eyebrow="The process" title="How It Works" />
          <ScrollReveal className="grid sm:grid-cols-3 gap-6">
            {TRUST_STEPS.map(({ icon: Icon, title, detail, accent }, i) => (
              <div
                key={title}
                className="relative sc-card sc-card-interactive p-6 pt-8 text-center"
                style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
              >
                <span
                  className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-extrabold px-3 py-1 rounded-full text-white"
                  style={{ background: `linear-gradient(135deg, ${accent} 0%, ${TEAL} 100%)`, boxShadow: "0 6px 14px rgba(11,32,39,0.25)" }}
                >
                  STEP {String(i + 1).padStart(2, "0")}
                </span>
                <div
                  className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4"
                  style={{ background: `linear-gradient(135deg, ${accent} 0%, ${TEAL} 100%)`, boxShadow: "0 8px 18px rgba(11,32,39,0.20)" }}
                >
                  <Icon className="w-6 h-6 text-white" strokeWidth={2} />
                </div>
                <h3 className="font-bold text-base mb-2" style={{ color: TEXT }}>
                  {title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  {detail}
                </p>
              </div>
            ))}
          </ScrollReveal>
        </div>
      </section>

      {/* Pointer to the dedicated Consult a Doctor page — full detail on the
          real doctor-verification process and specialty team lives there,
          not duplicated here. */}
      <section className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div
          className="sc-card p-8"
          style={{ background: `linear-gradient(135deg, ${TEAL} 0%, ${BLUE} 100%)` }}
        >
          <Stethoscope className="w-8 h-8 text-white mx-auto mb-3" strokeWidth={2} />
          <h3 className="text-lg font-bold text-white mb-2">Curious who reviews your case?</h3>
          <p className="text-sm text-white/85 mb-5 max-w-md mx-auto">
            See exactly how our specialty-matched doctor team confirms every suggestion before it
            reaches you.
          </p>
          <Link
            href="/consult-a-doctor"
            className="inline-block rounded-full px-6 py-2.5 text-sm font-bold transition-transform duration-200 hover:-translate-y-0.5"
            style={{ background: "#FFFFFF", color: TEAL }}
          >
            Meet Our Doctors
          </Link>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="max-w-2xl mx-auto px-4 pb-20 scroll-mt-24">
        <SectionHeading eyebrow="Questions" title="FAQ" />
        <ScrollReveal className="space-y-3" stagger={0.06} y={12}>
          {FAQ_ITEMS.map((item, i) => (
            <div key={item.q} className="sc-card overflow-hidden" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left cursor-pointer transition-colors duration-200 hover:bg-[rgba(14,124,134,0.04)] focus-visible:outline-none focus-visible:bg-[rgba(14,124,134,0.06)]"
              >
                <span className="text-sm font-semibold" style={{ color: TEXT }}>
                  {item.q}
                </span>
                <ChevronDown
                  className="w-4 h-4 shrink-0 transition-transform duration-200"
                  style={{ color: MUTED, transform: openFaq === i ? "rotate(180deg)" : "rotate(0deg)" }}
                />
              </button>
              {openFaq === i && (
                <div className="px-4 pb-4 text-sm leading-relaxed" style={{ color: MUTED }}>
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </ScrollReveal>
      </section>

      {/* Final CTA band — layered gradient + texture, not a flat fill */}
      <section
        className="relative py-20 px-4 text-center overflow-hidden"
        style={{ background: `linear-gradient(135deg, ${TEAL} 0%, ${BLUE} 65%, ${BLUE} 100%)` }}
      >
        <div
          className="absolute inset-0 opacity-[0.09] pointer-events-none"
          aria-hidden="true"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "26px 26px" }}
        />
        {/* Custom vector illustration (hand-built, cleaned/optimized via
            Inkscape CLI — public/illustrations/symptom-flow.svg) depicting
            the real product flow: describe your symptoms -> doctor + AI
            review -> real medicine. */}
        {/* eslint-disable-next-line @next/next/no-img-element -- static local
            decorative SVG; next/image's raster pipeline isn't used for
            hand-authored vector assets. */}
        <img
          src="/illustrations/symptom-flow.svg"
          alt=""
          aria-hidden="true"
          className="relative mx-auto mb-6 w-full max-w-[220px] sm:max-w-[260px] h-auto"
        />
        <h2 className="relative font-display font-extrabold text-3xl sm:text-5xl tracking-tight text-white mb-3 leading-tight">
          Describe what you're feeling. Get an answer you can trust.
        </h2>
        <p className="relative text-sm sm:text-base font-semibold text-white/85 mb-8">
          Doctor-reviewed guidance, in your own language.
        </p>
        <button
          onClick={() => scrollToHero()}
          className="relative rounded-full px-10 py-4 text-base font-extrabold shadow-xl hover:shadow-2xl hover:-translate-y-1 hover:brightness-105 active:translate-y-0 transition-all duration-200"
          style={{ background: "#FFFFFF", color: TEAL }}
        >
          Check My Symptoms
        </button>
      </section>

      <SiteFooter />
    </main>
  );
}

function DoctorCTA({
  sent,
  onClick,
  whatsappLink,
}: {
  sent: boolean;
  onClick: () => void;
  whatsappLink?: string | null;
}) {
  return (
    <div className="sc-card p-6 text-center mb-8" style={{ background: TEAL }}>
      {sent ? (
        <p className="text-white font-semibold text-base">
          Request sent — we&apos;ll reach out shortly.
        </p>
      ) : whatsappLink ? (
        <>
          <a
            href={whatsappLink}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClick}
            className="inline-block w-full sm:w-auto rounded-full px-8 py-3.5 text-base font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200"
            style={{ background: "#FFFFFF", color: TEAL }}
          >
            Talk to a Doctor on WhatsApp
          </a>
          <p className="text-xs text-white/90 mt-3 max-w-md mx-auto leading-relaxed">
            Don&apos;t know the exact name of your condition? A real doctor from our team will help
            you over WhatsApp.
          </p>
        </>
      ) : (
        <>
          <button
            onClick={onClick}
            className="w-full sm:w-auto rounded-full px-8 py-3.5 text-base font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200"
            style={{ background: "#FFFFFF", color: TEAL }}
          >
            Ask a Doctor to Confirm This
          </button>
          <p className="text-xs text-white/90 mt-3 max-w-md mx-auto leading-relaxed">
            Every case is personally reviewed by a qualified doctor from our team, matched to your
            specific condition, before any medicine is confirmed — expect a reply shortly on WhatsApp.
          </p>
        </>
      )}
    </div>
  );
}
