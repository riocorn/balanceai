"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldCheck, MessageCircle, Sparkles, CheckCircle2,
  Pill, ChevronLeft, ChevronRight,
} from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { matchSymptoms } from "@/lib/pharmacy-api";
import { CATEGORY_TILES } from "@/components/diag/categories";

// Aligned to the locked BalanceAI palette (--diag-primary-teal / --diag-primary-blue /
// --diag-effectiveness) so /pharmacy shares the same design language as /symptom-checker.
const GREEN = "#0E7C86"; // locked teal
const GREEN_DARK = "#1E6FD9"; // locked blue
const AMBER = "#1FAE7A"; // locked effectiveness green (was a non-palette amber accent)
const BORDER = "#E4EBEE";
const TEXT = "#0B2027";
const MUTED = "#5B7480";
const WHATSAPP_GREEN = "#25D366";
const BG = "#F7FAFB";

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
      {/* ── Full-bleed hero banner — 1mg/Netmeds pattern: split text/graphic + carousel dots ── */}
      <div className="relative overflow-hidden" style={{ background: `linear-gradient(135deg, ${GREEN} 0%, ${GREEN_DARK} 100%)` }}>
        {/* Real photography backdrop — pills spilling from a bottle, tinted
            with the brand gradient (Unsplash, license-clear, verified
            2026-09-28). */}
        <Image
          src="https://images.unsplash.com/photo-1587854692152-cbe660dbde88?auto=format&fit=crop&w=1600&q=75"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover pointer-events-none"
          aria-hidden="true"
        />
        {/* Real bug found and fixed here: this tint sat at opacity 0.97 over
            the real photo, hiding ~97% of it — the "real photography
            backdrop" comment above was true in code but not in what a
            visitor actually saw (a flat gradient block). Brought down to
            match the same tuned treatment used on /symptom-checker, where
            the photo is genuinely visible outside the text column. */}
        <div
          className="absolute inset-0 pointer-events-none"
          aria-hidden="true"
          style={{ background: `linear-gradient(135deg, ${GREEN} 0%, ${GREEN_DARK} 100%)`, opacity: 0.4 }}
        />
        {/* Left-side scrim — the rotating headline/search copy sits on the
            left column, so it needs the strongest contrast there. */}
        <div
          className="absolute inset-0 pointer-events-none"
          aria-hidden="true"
          style={{ background: "linear-gradient(100deg, rgba(4,20,24,0.92) 0%, rgba(4,20,24,0.68) 45%, rgba(4,20,24,0.18) 70%, rgba(4,20,24,0) 88%)" }}
        />
        {/* decorative background texture, dense pattern like real e-pharmacy banners */}
        <div className="absolute inset-0 opacity-[0.08]" style={{
          backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)",
          backgroundSize: "22px 22px",
        }} />
        <div className="absolute -right-24 -top-24 w-96 h-96 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }} />
        <div className="absolute -left-16 bottom-0 w-64 h-64 rounded-full" style={{ background: "rgba(255,255,255,0.05)" }} />

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
                <h1 className="font-display text-3xl sm:text-4xl lg:text-[2.75rem] font-extrabold mb-3 text-white leading-[1.12] tracking-tight">
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
                className="w-7 h-7 rounded-full flex items-center justify-center transition-all"
                style={{ background: "rgba(255,255,255,0.14)", color: "#fff" }}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="flex items-center gap-1.5">
                {SLIDES.map((_, i) => (
                  <button
                    key={i}
                    aria-label={`Slide ${i + 1}`}
                    onClick={() => setSlide(i)}
                    className="flex items-center justify-center rounded-full transition-all"
                    style={{ width: 24, height: 24 }}
                  >
                    <span
                      className="rounded-full transition-all"
                      style={{
                        width: i === slide ? 20 : 6,
                        height: 6,
                        background: i === slide ? AMBER : "rgba(255,255,255,0.35)",
                      }}
                    />
                  </button>
                ))}
              </div>
              <button
                aria-label="Next"
                onClick={() => setSlide((s) => (s + 1) % SLIDES.length)}
                className="w-7 h-7 rounded-full flex items-center justify-center transition-all"
                style={{ background: "rgba(255,255,255,0.14)", color: "#fff" }}
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

          {/* ── Right: bold graphic — device mockup + floating badges ── */}
          <div className="order-1 md:order-2 flex justify-center md:justify-end">
            <div className="relative w-64 sm:w-72" style={{ aspectRatio: "0.82" }}>
              {/* blob backdrop */}
              <div className="absolute inset-0 rounded-[2.5rem]" style={{ background: "rgba(255,255,255,0.08)", transform: "rotate(6deg)" }} />

              {/* phone/chat card — real illustrative example copy instead of
                  grey skeleton-loading bars standing in as permanent
                  decoration (a real bug: skeleton bars read as "still
                  loading" or broken, not as a finished graphic). */}
              <motion.div
                initial={{ y: 0 }}
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-3 rounded-[2rem] p-4 flex flex-col shadow-2xl"
                style={{ background: "#fff" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: "rgba(14,124,134,0.10)" }}>
                    <Sparkles className="w-3.5 h-3.5" style={{ color: GREEN }} />
                  </div>
                  <p className="text-xs font-bold" style={{ color: TEXT }}>BalanceAI</p>
                </div>
                <div className="rounded-2xl rounded-tr-sm px-3 py-2 mb-2 self-end max-w-[85%]" style={{ background: "rgba(11,32,39,0.06)" }}>
                  <p className="text-[11px] leading-snug" style={{ color: TEXT }}>&quot;mujhe migraine hai, kai saalo se&quot;</p>
                </div>
                <div className="rounded-2xl rounded-tl-sm px-3 py-2 mb-3 max-w-[90%]" style={{ background: "rgba(14,124,134,0.10)" }}>
                  <p className="text-[11px] leading-snug font-semibold" style={{ color: GREEN_DARK }}>Matched: Migraine — 9 real treatments found</p>
                </div>
                <div className="mt-auto rounded-xl p-3 flex items-center gap-2.5" style={{ background: "rgba(14,124,134,0.10)" }}>
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: GREEN }}>
                    <Pill className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-bold truncate" style={{ color: TEXT }}>Prochlorperazine</p>
                    <p className="text-[10px] truncate" style={{ color: MUTED }}>Symptom relief</p>
                  </div>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0" style={{ background: AMBER, color: "#fff" }}>82%</span>
                </div>
              </motion.div>

              {/* floating WhatsApp-verify badge */}
              <motion.div
                initial={{ y: 0 }}
                animate={{ y: [0, 6, 0] }}
                transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
                className="absolute -left-8 -top-4 flex items-center gap-1.5 rounded-full pl-1.5 pr-3 py-1.5 shadow-xl"
                style={{ background: "#fff" }}
              >
                <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: WHATSAPP_GREEN }}>
                  <MessageCircle className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-[10px] font-bold" style={{ color: TEXT }}>Doctor Review (Beta)</span>
              </motion.div>

              {/* floating amber accent chip */}
              <motion.div
                initial={{ y: 0 }}
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 3.6, repeat: Infinity, ease: "easeInOut", delay: 0.6 }}
                className="absolute -right-2 -bottom-3 flex items-center gap-1.5 rounded-full pl-1.5 pr-3 py-1.5 shadow-xl"
                style={{ background: "#fff" }}
              >
                <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: AMBER }}>
                  <ShieldCheck className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-[10px] font-bold" style={{ color: TEXT }}>Clinically Proven</span>
              </motion.div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {/* ── Category rail — circular icon badges, dense horizontal-scroll, 1mg/Netmeds "shop by category" pattern ── */}
        <div className="-mt-1 sm:mt-0 pt-6">
          <p className="text-xs font-bold uppercase tracking-wide mb-3" style={{ color: MUTED }}>Browse by health area</p>
          <div className="flex sm:grid sm:grid-cols-6 gap-4 sm:gap-3 overflow-x-auto sm:overflow-visible pb-2 sm:pb-0 -mx-5 px-5 sm:mx-0 sm:px-0">
            {CATEGORY_TILES.map(({ icon: Icon, label, accent, starter, image }) => (
              <button
                key={label}
                onClick={() => submit(starter)}
                disabled={loading}
                className="flex flex-col items-center gap-2 shrink-0 w-20 sm:w-auto transition-transform disabled:opacity-40 hover:-translate-y-0.5"
              >
                <div className="relative w-14 h-14 rounded-full overflow-hidden shadow-sm">
                  <Image src={`${image}?auto=format&fit=crop&w=200&q=70`} alt="" fill sizes="56px" className="object-cover" />
                  <div className="absolute inset-0" style={{ background: `${accent}66` }} />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Icon className="w-6 h-6 text-white drop-shadow-sm" />
                  </div>
                </div>
                <span className="text-[11px] font-semibold text-center leading-tight" style={{ color: TEXT }}>{label}</span>
              </button>
            ))}
          </div>
          {error && <p className="text-xs mt-3" style={{ color: "#B42318" }}>{error}</p>}
        </div>

        {/* ── Trust badge strip — dense 4-up row with separators, real e-pharmacy "why us" pattern ── */}
        <div className="sc-card mt-8 grid grid-cols-2 sm:grid-cols-4" style={{ background: "#fff", border: `1px solid ${BORDER}` }}>
          {TRUST_ITEMS.map(({ icon: Icon, title, desc }, i) => (
            <div
              key={title}
              className="group flex flex-col items-start gap-2 p-4 transition-colors duration-200 hover:bg-[rgba(14,124,134,0.04)]"
              style={{
                borderRight: i % 2 === 0 ? `1px solid ${BORDER}` : undefined,
                borderTop: i >= 2 ? `1px solid ${BORDER}` : undefined,
              }}
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center transition-transform duration-200 group-hover:scale-110" style={{ background: "rgba(14,124,134,0.10)" }}>
                <Icon className="w-4 h-4" style={{ color: GREEN }} />
              </div>
              <p className="text-xs font-bold leading-tight" style={{ color: TEXT }}>{title}</p>
              <p className="text-[11px] leading-snug" style={{ color: MUTED }}>{desc}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-6 mb-10">
          {[
            { icon: Sparkles, title: "AI Understanding", desc: "Recognizes the condition from text written in any language or style" },
            { icon: ShieldCheck, title: "Proven Treatments", desc: "Backed by real clinical evidence, never a guess" },
            { icon: MessageCircle, title: "WhatsApp Doctor Review", desc: "Send your prescription to a doctor over WhatsApp before purchase — reply is currently self-confirmed, not independently verified yet" },
          ].map(({ icon: Icon, title, desc }) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="group sc-card sc-card-interactive p-4"
              style={{ background: "#fff", border: `1px solid ${BORDER}` }}
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-2 transition-transform duration-200 group-hover:scale-110" style={{ background: "rgba(14,124,134,0.10)" }}>
                <Icon className="w-4 h-4" style={{ color: GREEN }} />
              </div>
              <p className="text-sm font-semibold mb-1" style={{ color: TEXT }}>{title}</p>
              <p className="text-xs" style={{ color: MUTED }}>{desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
      <SiteFooter />
    </main>
  );
}
