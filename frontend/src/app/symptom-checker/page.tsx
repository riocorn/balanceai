"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
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
  MessageSquareQuote,
  HelpCircle,
  SearchX,
} from "lucide-react";
import { api } from "@/lib/api";
import { useCartStore } from "@/lib/cart-store";
import { isNonDrugIntervention, cleanMedicineName } from "@/lib/medicines";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import MedicinePackPlaceholder from "@/components/diag/MedicinePackPlaceholder";
import ScrollReveal from "@/components/diag/ScrollReveal";
import { Card } from "@/components/ui/card";
import CategoryRail from "@/components/diag/CategoryRail";
import { TEAL, BLUE, BG, SURFACE, TEXT, MUTED, EFFECTIVENESS, EFFECTIVENESS_TEXT, EMERGENCY, HERO_GRADIENT, ACCENT_PURPLE, ACCENT_CORAL, ACCENT_AMBER } from "@/components/diag/theme";
import { CTA_BASE, CTA_HERO_BASE, CTA_RADIUS, TRANSITION } from "@/components/diag/tokens";

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
  "Doctor Review Required Before Checkout (Beta)",
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
    title: "Send it for doctor review",
    detail:
      "Before checkout, send your case to a doctor on WhatsApp. This step is beta — the reply is currently self-confirmed by you, not yet independently verified by BalanceAI.",
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
  { icon: Stethoscope, title: "Doctor Review (Beta)", detail: "Send every suggestion to a doctor on WhatsApp before checkout — confirmation is currently self-reported.", accent: TEAL },
  { icon: Languages, title: "Speak Freely", detail: "English, Hindi, or Hinglish — describe things exactly as you'd tell a doctor.", accent: BLUE },
  { icon: Info, title: "Clear, Honest Information", detail: "You'll see what a treatment does and how it helps, explained simply.", accent: ACCENT_PURPLE },
  { icon: ShieldCheck, title: "No Pressure", detail: "We're here to help you find the right care, not to rush you into buying anything.", accent: EFFECTIVENESS },
];

const HERO_SLIDES: { badge: string; headline: string; sub: string }[] = [
  {
    badge: "Doctor Review Required (Beta)",
    headline: "Tell us what's wrong. We'll find the right treatment.",
    sub: "Describe your symptoms in your own words — English, Hindi, or Hinglish. Every suggestion must be sent to a doctor on WhatsApp before checkout unlocks.",
  },
  {
    badge: "Doctor Confirmation (Beta)",
    headline: "AI never has the final word alone.",
    sub: "Send your case to a doctor over WhatsApp before you buy. Today that confirmation is self-declared by you — automatic verification is coming.",
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
    a: "No. BalanceAI only suggests possibilities based on real medical information. Checkout stays locked until you send your case to a doctor on WhatsApp — this review step is currently self-confirmed by you, not yet automatically verified by BalanceAI.",
  },
  {
    q: "What happens after I get my results?",
    a: "You can send the suggestion to a doctor over our WhatsApp review line (beta — not specialty-matched yet). Once they reply, you confirm that go-ahead yourself in the app before checkout unlocks.",
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

function SectionHeading({ eyebrow, title, accent }: { eyebrow: string; title: string; accent?: string }) {
  return (
    <div className="flex items-start gap-4 mb-10">
      <span
        className="w-1 self-stretch rounded-full shrink-0"
        style={{ background: accent || TEAL, minHeight: 44 }}
        aria-hidden="true"
      />
      <div>
        <p className="text-sm font-semibold mb-1" style={{ color: accent || TEAL }}>
          {eyebrow}
        </p>
        <h2 className="font-display font-bold text-3xl sm:text-4xl leading-tight" style={{ color: TEXT }}>
          {title}
        </h2>
      </div>
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
          {/* Redesign (2026-09-29): the previous hero used a tinted stock
              photo as a backdrop — diagnosed as the single biggest driver of
              the site's templated/cheap feel. Replaced with a deliberate
              typography-led hero: a solid brand gradient field, a dense
              dot-grid texture (a considered graphic device, not a blurred
              "SaaS gradient blob"), and two large soft rings that echo the
              logo's pulse mark rather than any photographic content. */}
          <div
            className="absolute inset-0 opacity-[0.12] pointer-events-none"
            aria-hidden="true"
            style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }}
          />
          <div
            className="absolute -right-32 -top-40 w-[30rem] h-[30rem] rounded-full pointer-events-none"
            aria-hidden="true"
            style={{ border: "1px solid rgba(255,255,255,0.14)" }}
          />
          <div
            className="absolute -right-16 -top-16 w-72 h-72 rounded-full pointer-events-none"
            aria-hidden="true"
            style={{ border: "1px solid rgba(255,255,255,0.10)" }}
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
                    className="font-display font-bold leading-[1.05] mb-4 text-white tracking-tight"
                    style={{ fontSize: "clamp(2.25rem, 6vw, 4rem)" }}
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
                      Trusted Treatments, Sent for Doctor Review
                    </p>
                    <p className="text-[11px] font-semibold mt-0.5" style={{ color: MUTED }}>
                      Checkout stays locked until you complete WhatsApp review
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

          {/* Redesign, 2026-09-29: dropped the 3-card icon-in-circle "trust
              ladder" that used to sit here — it duplicated the numbered
              How It Works rail further down the page (same three steps,
              same icons) and was exactly the generic SaaS-card-grid pattern
              this redesign is removing everywhere else. The hero now ends
              on the trust seal above instead of a second, redundant grid. */}
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
            className="sc-card p-5 mb-5 flex items-start gap-3.5"
            style={{ background: "rgba(30,111,217,0.06)", border: "1px solid rgba(30,111,217,0.22)" }}
          >
            <div
              className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
              style={{ background: BLUE }}
            >
              <MessageSquareQuote className="w-4 h-4 text-white" strokeWidth={2.25} />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold mb-1.5" style={{ color: BLUE }}>
                Here's how we understood you
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
          </div>

          {result.need_more_info ? (
            <div
              className="sc-card p-5 mb-5"
              style={{ background: "rgba(124,92,191,0.06)", border: "1px solid rgba(124,92,191,0.22)" }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                  style={{ background: ACCENT_PURPLE }}
                >
                  <HelpCircle className="w-4 h-4 text-white" strokeWidth={2.25} />
                </div>
                <p className="text-sm font-semibold" style={{ color: ACCENT_PURPLE }}>
                  A couple more questions to narrow this down
                </p>
              </div>
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
                      className="w-full rounded-lg px-3.5 py-2.5 text-sm outline-none transition-colors duration-150"
                      style={{ background: SURFACE, border: "1px solid #D5DEE1", color: TEXT }}
                      onFocus={(e) => { e.currentTarget.style.borderColor = ACCENT_PURPLE; }}
                      onBlur={(e) => { e.currentTarget.style.borderColor = "#D5DEE1"; }}
                    />
                  </div>
                ))}
              </div>
              <button
                onClick={submitClarifyingAnswers}
                disabled={submittingAnswers || result.clarifying_questions.some((_, i) => !(clarifyAnswers[i] || "").trim())}
                className={`${CTA_BASE} mt-5 w-full sm:w-auto ${CTA_RADIUS} text-white hover:brightness-110 disabled:opacity-50 disabled:hover:brightness-100`}
                style={{ background: `linear-gradient(135deg, ${ACCENT_PURPLE} 0%, ${BLUE} 100%)`, transition: TRANSITION }}
              >
                {submittingAnswers ? "Checking..." : "Continue"}
              </button>
            </div>
          ) : result.matched && result.disease ? (
            <div
              className="sc-card p-5 mb-5 flex items-start gap-4"
              style={{ background: "rgba(14,124,134,0.06)", border: "1px solid rgba(14,124,134,0.22)" }}
            >
              <div
                className="w-14 h-14 rounded-full flex items-center justify-center shrink-0"
                style={{ background: HERO_GRADIENT, boxShadow: "0 8px 18px rgba(14,124,134,0.28)" }}
              >
                <Stethoscope className="w-6 h-6 text-white" strokeWidth={2} />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold mb-1" style={{ color: MUTED }}>
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
              className="sc-card p-5 mb-5 flex items-start gap-3.5"
              style={{ background: "rgba(201,138,44,0.06)", border: "1px solid rgba(201,138,44,0.22)" }}
            >
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                style={{ background: ACCENT_AMBER }}
              >
                <SearchX className="w-4 h-4 text-white" strokeWidth={2.25} />
              </div>
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
                  {purchasableMedicines.map((m, idx) => {
                    const inCart = cartItems.some((i) => i.name === cleanMedicineName(m.name));
                    const firstSource = m.sources[0];
                    const pct = m.effectiveness_pct != null ? Math.round(m.effectiveness_pct) : null;
                    return (
                      <Card
                        // Real bug found live, 2026-09-29: the backend's
                        // ranked-medicines list can legitimately contain the
                        // same medicine name twice (e.g. "Ertapenem +
                        // Metronidazole" at two different rows/doses), which
                        // made React log a duplicate-key warning on every
                        // re-render and risks silently dropping/duplicating
                        // cards per React's own documented behavior for
                        // non-unique keys. Name alone was never a safe key;
                        // combining with its position in the (already
                        // effectiveness-sorted, stable) list is.
                        key={`${m.name}-${idx}`}
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
                                  <p className="text-[10px] font-semibold mt-0.5" style={{ color: MUTED }}>
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
                            className={`mt-4 h-10 px-5 text-sm font-medium ${CTA_RADIUS} border hover:bg-[rgba(30,111,217,0.08)] disabled:opacity-60 disabled:hover:bg-transparent`}
                            style={{ borderColor: BLUE, color: BLUE, background: "transparent", transition: TRANSITION }}
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
        <SectionHeading eyebrow="Browse by category" title="Browse real medicines by health area" accent={ACCENT_PURPLE} />
        {/* Horizontally scrollable circular category strip — mirrors the real
            "shop by category" structural pattern used across pharmacy/health apps.
            Each tile takes you to a real, filtered view of the medicine catalog
            for that health area — a distinct action from the header's quick-link
            strip, which instead pre-fills the symptom-checker input. */}
        <CategoryRail linkToMedicines />
      </section>

      {/* Trust claims band — redesigned, 2026-09-29, from a 2x2 icon-circle
          card grid (the generic "SaaS card kit" tell) into an asymmetric
          headline + list split, closer to how a considered product page
          actually earns trust: one confident claim, then the specifics. */}
      <section
        className="relative w-full py-16 px-4 overflow-hidden"
        style={{ background: `linear-gradient(120deg, ${TEAL} 0%, ${TEAL} 35%, ${BLUE} 100%)` }}
      >
        <div
          className="absolute inset-0 opacity-[0.10] pointer-events-none"
          aria-hidden="true"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "26px 26px" }}
        />
        <div className="relative max-w-5xl mx-auto grid sm:grid-cols-[1fr_1.2fr] gap-10 items-start">
          <h2 className="font-display font-bold text-white leading-[1.05]" style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)" }}>
            Why people trust BalanceAI with what they tell it.
          </h2>
          <div className="divide-y divide-[rgba(255,255,255,0.18)]">
            {TRUST_BADGES.map(({ title, detail }) => (
              <div key={title} className="py-4 first:pt-0">
                <p className="text-sm font-bold text-white mb-1">{title}</p>
                <p className="text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.78)" }}>{detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works — a real connected sequence (describe -> doctor review
          -> treatment), so it earns a numbered rail rather than three
          identical floating-badge cards. Numerals are set in the display
          serif as a genuine type-driven device (ghost-weight, large scale)
          instead of a small colored pill repeated on each card, and a single
          running rule ties the three stages together left-to-right on
          desktop / top-to-bottom on mobile, reading as one continuous
          journey instead of three interchangeable tiles. */}
      <section id="how-it-works" className="w-full py-24 px-4 scroll-mt-24" style={{ background: SURFACE }}>
        <div className="max-w-5xl mx-auto">
          <div className="mb-14 max-w-lg">
            <p className="text-sm font-semibold mb-2" style={{ color: BLUE }}>How it works</p>
            <h2 className="font-display leading-[1.08] text-3xl sm:text-4xl" style={{ color: TEXT }}>
              From what you feel to what you take —{" "}
              <span style={{ color: BLUE, fontStyle: "italic" }}>three real steps.</span>
            </h2>
          </div>
          <div className="relative grid sm:grid-cols-3 gap-10 sm:gap-8">
            <div
              className="hidden sm:block absolute top-7 left-0 right-0 h-px"
              style={{ background: "linear-gradient(90deg, #E4EBEE 0%, #E4EBEE 100%)" }}
              aria-hidden="true"
            />
            {TRUST_STEPS.map(({ icon: Icon, title, detail, accent }, i) => (
              <div key={title} className="relative">
                <div className="flex items-center gap-4 sm:block">
                  <span
                    className="font-display shrink-0 leading-none select-none"
                    style={{ fontSize: "3.25rem", color: accent, opacity: 0.28 }}
                  >
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div
                    className="relative z-10 w-11 h-11 rounded-full flex items-center justify-center shrink-0 sm:-mt-9 sm:ml-11"
                    style={{ background: accent, boxShadow: `0 8px 18px ${accent}40` }}
                  >
                    <Icon className="w-5 h-5 text-white" strokeWidth={2} />
                  </div>
                </div>
                <h3 className="text-lg font-semibold mt-4 mb-2" style={{ color: TEXT }}>
                  {title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  {detail}
                </p>
              </div>
            ))}
          </div>
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
          <h3 className="text-lg font-bold text-white mb-2">Curious how doctor review works?</h3>
          <p className="text-sm text-white/85 mb-5 max-w-md mx-auto">
            See exactly how the real WhatsApp review step works today — and what&apos;s still beta.
          </p>
          <Link
            href="/consult-a-doctor"
            className={`inline-flex items-center justify-center h-11 px-6 text-sm font-medium ${CTA_RADIUS} hover:brightness-95`}
            style={{ background: "#FFFFFF", color: TEAL, transition: TRANSITION }}
          >
            Meet Our Doctors
          </Link>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="max-w-2xl mx-auto px-4 pb-20 scroll-mt-24">
        <SectionHeading eyebrow="Questions" title="FAQ" accent={ACCENT_CORAL} />
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
          Real clinical evidence, in your own language — doctor review before checkout.
        </p>
        <button
          onClick={() => scrollToHero()}
          className={`relative ${CTA_HERO_BASE} ${CTA_RADIUS} hover:brightness-95`}
          style={{ background: "#FFFFFF", color: TEAL, transition: TRANSITION }}
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
            className={`${CTA_HERO_BASE} w-full sm:w-auto ${CTA_RADIUS} hover:brightness-95`}
            style={{ background: "#FFFFFF", color: TEAL, transition: TRANSITION }}
          >
            Talk to a Doctor on WhatsApp
          </a>
          <p className="text-xs text-white/90 mt-3 max-w-md mx-auto leading-relaxed">
            Don&apos;t know the exact name of your condition? Send it over WhatsApp (beta review
            line) and describe what you&apos;re feeling.
          </p>
        </>
      ) : (
        <>
          <button
            onClick={onClick}
            className={`${CTA_HERO_BASE} w-full sm:w-auto ${CTA_RADIUS} hover:brightness-95`}
            style={{ background: "#FFFFFF", color: TEAL, transition: TRANSITION }}
          >
            Send to a Doctor on WhatsApp
          </button>
          <p className="text-xs text-white/90 mt-3 max-w-md mx-auto leading-relaxed">
            This sends your case to our WhatsApp review line (beta — specialty matching isn't live
            yet). Once a doctor replies, you confirm that go-ahead yourself in the app; BalanceAI
            doesn't yet automatically verify the reply.
          </p>
        </>
      )}
    </div>
  );
}
