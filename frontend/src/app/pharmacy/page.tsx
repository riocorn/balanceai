"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldCheck, MessageCircle, Sparkles, CheckCircle2,
  ChevronLeft, ChevronRight,
} from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import CategoryRail from "@/components/diag/CategoryRail";
import { matchSymptoms } from "@/lib/pharmacy-api";
import {
  TEAL as GREEN,
  BLUE as GREEN_DARK,
  EFFECTIVENESS as AMBER,
  ACCENT_CORAL,
  ACCENT_PURPLE,
  BORDER,
  TEXT,
  MUTED,
  BG,
  SURFACE,
} from "@/components/diag/theme";
import { TRANSITION_ALL, FOCUS_RING } from "@/components/diag/tokens";

const SLIDES = [
  {
    badge: "AI Pharmacy",
    headline: "Describe your problem, in any language",
    desc: "Tell us how you feel, and we'll help you find the right medicine — every order is routed to WhatsApp for doctor review before checkout unlocks.",
  },
  {
    badge: "Doctor Review (Beta)",
    headline: "Every order is sent to a doctor on WhatsApp",
    desc: "We route your case to WhatsApp before purchase. This step is currently self-confirmed by you — BalanceAI doesn't yet independently verify the doctor's reply.",
  },
  {
    badge: "Real Effectiveness Data",
    headline: "Every medicine's effectiveness is backed by research",
    desc: "Every treatment we recommend is backed by real clinical research, so you know it actually works.",
  },
];

const TRUST_ITEMS = [
  { icon: ShieldCheck, title: "Doctor Review (Beta)", desc: "Every order is sent to a doctor on WhatsApp — confirmation is currently self-reported, not independently verified yet" },
  { icon: Sparkles, title: "Multilingual AI", desc: "Understands Hindi, Hinglish and English alike" },
  { icon: CheckCircle2, title: "Proven Effectiveness", desc: "Backed by real clinical research" },
  { icon: MessageCircle, title: "WhatsApp Support", desc: "Send your case to a doctor before you purchase" },
];

export default function PharmacyIntakePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [slide, setSlide] = useState(0);

  useEffect(() => {
    document.title = "Order Medicine — BalanceAI";
  }, []);

  useEffect(() => {
    const id = setInterval(() => setSlide((s) => (s + 1) % SLIDES.length), 4500);
    return () => clearInterval(id);
  }, [slide]);

  async function submit(query: string) {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError("");
    try {
      const match = await matchSymptoms(query.trim());
      sessionStorage.setItem(
        "pharmacy_last_match",
        JSON.stringify({ text: query.trim(), match })
      );
      router.push("/pharmacy/results");
    } catch {
      setError("Something went wrong. Please try again, or come back in a little while.");
      setLoading(false);
    }
  }

  const active = SLIDES[slide];

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="pharmacy" />
      {/* ── Hero banner — typography-led, no stock photography (redesign,
          2026-09-29): a solid brand gradient field with a dense dot-grid
          texture and two soft outline rings, matching the same device used
          on /symptom-checker so the two entry points feel like one site. ── */}
      <div className="relative overflow-hidden" style={{ background: GREEN }}>

        <div className="relative max-w-7xl mx-auto px-5 sm:px-8 pt-8 pb-6 sm:pt-10 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          {/* ── Left: rotating bold text block + search ── */}
          <div className="order-2 md:order-1 text-center md:text-left">
            <AnimatePresence mode="wait">
              <motion.div
                key={slide}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.35, ease: "easeOut" }}
              >
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mb-4" style={{ background: "rgba(255,255,255,0.16)", color: "#fff" }}>
                  <Sparkles className="w-3.5 h-3.5" />
                  {active.badge}
                </div>
                <h1 className="font-display text-4xl sm:text-5xl lg:text-[3.25rem] font-bold mb-3 text-white leading-[1.05] tracking-tight">
                  {active.headline}
                </h1>
                <p className="text-sm sm:text-base max-w-md mx-auto md:mx-0" style={{ color: "rgba(255,255,255,0.85)" }}>
                  {active.desc}
                </p>
              </motion.div>
            </AnimatePresence>

            {/* carousel controls — arrows + dots, dense composition matching real banner nav */}
            <div className="flex items-center gap-3 mt-5 justify-center md:justify-start">
              <button
                aria-label="Previous"
                onClick={() => setSlide((s) => (s - 1 + SLIDES.length) % SLIDES.length)}
                className={`w-7 h-7 rounded-full flex items-center justify-center hover:bg-[rgba(255,255,255,0.22)] ${FOCUS_RING} focus-ring-on-dark`}
                style={{ background: "rgba(255,255,255,0.14)", color: "#fff", transition: TRANSITION_ALL }}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="flex items-center gap-1.5">
                {SLIDES.map((_, i) => (
                  <button
                    key={i}
                    aria-label={`Slide ${i + 1}`}
                    onClick={() => setSlide(i)}
                    className={`flex items-center justify-center rounded-full ${FOCUS_RING} focus-ring-on-dark`}
                    style={{ width: 24, height: 24, transition: TRANSITION_ALL }}
                  >
                    <span
                      className="rounded-full"
                      style={{
                        width: i === slide ? 20 : 6,
                        height: 6,
                        background: i === slide ? AMBER : "rgba(255,255,255,0.35)",
                        transition: TRANSITION_ALL,
                      }}
                    />
                  </button>
                ))}
              </div>
              <button
                aria-label="Next"
                onClick={() => setSlide((s) => (s + 1) % SLIDES.length)}
                className={`w-7 h-7 rounded-full flex items-center justify-center hover:bg-[rgba(255,255,255,0.22)] ${FOCUS_RING} focus-ring-on-dark`}
                style={{ background: "rgba(255,255,255,0.14)", color: "#fff", transition: TRANSITION_ALL }}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* The real intake input now lives once, site-wide, in the shared
                navbar next to the "BalanceAI" logo — this page no longer has
                its own separate duplicate box. Category tiles below submit
                straight through that same real matching flow. */}

            {/* dense trust strip, real-banner pattern */}
            <div className="hidden sm:flex items-center gap-2 mt-4 text-[11px] font-medium justify-center md:justify-start" style={{ color: "rgba(255,255,255,0.75)" }}>
              <span>50+ symptom areas</span>
              <span className="w-1 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.4)" }} />
              <span>Hindi/Hinglish supported</span>
              <span className="w-1 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.4)" }} />
              <span>WhatsApp doctor review (beta)</span>
            </div>
          </div>

          {/* Custom vector illustration (hand-built — see
              public/illustrations/README.md): order -> pharmacy-verified
              badge (cross) -> delivered package (checkmark). A pharmacy
              fulfillment story, distinct from the AI-matching chat mockup
              this replaces (which duplicated the same "chat card" idea
              already used on /symptom-checker). */}
          <div className="order-1 md:order-2 flex justify-center md:justify-end" aria-hidden="true">
            {/* eslint-disable-next-line @next/next/no-img-element -- static
                local decorative SVG; next/image's raster pipeline isn't used
                for hand-authored vector assets. */}
            <img
              src="/illustrations/pharmacy-hero.svg"
              alt=""
              className="w-full max-w-[380px] sm:max-w-[480px] h-auto"
              style={{ filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.18))" }}
            />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {/* ── Category rail — circular icon badges, dense horizontal-scroll, 1mg/Netmeds "shop by category" pattern ── */}
        <div className="-mt-1 sm:mt-0 pt-6">
          <p className="text-sm font-semibold mb-3" style={{ color: MUTED }}>Browse by health area</p>
          <CategoryRail onSelect={(starter) => submit(starter)} disabled={loading} />
          {error && <p className="text-xs mt-3" style={{ color: "#B42318" }}>{error}</p>}
        </div>

        {/* Real loading state for the matchSymptoms() call this page waits
            on before it navigates away (15-100s, per founder research) —
            previously the ONLY feedback here was the category tiles going
            disabled, with nothing else on screen communicating that
            anything was happening. Same progress-bar + content-shaped
            skeleton language as /symptom-checker, so a person who's used
            one recognizes the other instantly. */}
        {loading && (
          <div aria-live="polite" className="mt-6 max-w-2xl">
            <div className="sc-card p-4 sm:p-5" style={{ background: SURFACE, border: `1px solid ${BORDER}` }}>
              <p className="text-sm font-semibold" style={{ color: TEXT }}>Finding your medicine...</p>
              <div className="sc-progress-track mt-3">
                <div className="sc-progress-bar" />
              </div>
              <p className="text-xs mt-2.5" style={{ color: MUTED }}>
                This can take anywhere from 15 seconds to a couple of minutes while we match your
                case against real clinical data.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4" aria-hidden="true">
              {[0, 1].map((i) => (
                <div key={i} className="sc-card p-4" style={{ background: SURFACE, border: `1px solid ${BORDER}` }}>
                  <div className="flex items-start gap-3">
                    <div className="sk w-12 h-12 rounded-xl shrink-0" />
                    <div className="flex-1 space-y-2 pt-1">
                      <div className="sk h-3.5 w-3/4 rounded-full" />
                      <div className="sk h-2.5 w-1/2 rounded-full" />
                    </div>
                  </div>
                  <div className="sk h-1.5 w-full rounded-full mt-3" />
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* Trust band — redesigned, 2026-09-29: the page used to run two
          separate icon-in-circle card grids back to back here, with real
          content overlap between them (both covered "AI understands any
          language" and "WhatsApp doctor review" separately). Consolidated
          into one asymmetric headline + list band, matching the same
          treatment used on /symptom-checker so the two entry points read as
          one system instead of two differently-templated pages. */}
      <section
        className="relative w-full py-16 px-4 overflow-hidden mt-10"
        style={{ background: GREEN }}
      >
        <div className="relative max-w-5xl mx-auto grid sm:grid-cols-[1fr_1.2fr] gap-10 items-start">
          <div>
            <h2 className="font-display font-bold text-white leading-[1.05] mb-8" style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)" }}>
              Why people trust BalanceAI to find their medicine.
            </h2>
            {/* Custom vector illustration (hand-built — see
                public/illustrations/README.md): a verification-seal dial
                with a completed arc + checkmark, filling what was previously
                a large empty gradient field under this headline. */}
            {/* eslint-disable-next-line @next/next/no-img-element -- static
                local decorative SVG; next/image's raster pipeline isn't used
                for hand-authored vector assets. */}
            <img
              src="/illustrations/trust-mark.svg"
              alt=""
              aria-hidden="true"
              className="hidden sm:block w-32 h-32 opacity-90"
            />
          </div>
          <div className="divide-y divide-[rgba(255,255,255,0.18)]">
            {TRUST_ITEMS.map(({ icon: Icon, title, desc }, i) => (
              <div key={title} className="py-4 first:pt-0 flex items-start gap-3.5">
                <span
                  className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                  style={{ background: [ACCENT_CORAL, "rgba(255,255,255,0.18)", AMBER, ACCENT_PURPLE][i % 4] }}
                >
                  <Icon className="w-4 h-4 text-white" />
                </span>
                <div>
                  <p className="text-sm font-bold text-white mb-1">{title}</p>
                  <p className="text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.78)" }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}
