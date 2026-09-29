"use client";

import { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { Stethoscope, MessageCircle, ShieldCheck, ClipboardList } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { TEAL, BG, SURFACE, TEXT, MUTED, HERO_GRADIENT, accentForKey } from "@/components/diag/theme";

const CONSULT_STEPS = [
  {
    icon: ClipboardList,
    title: "You describe your case",
    detail: "Start by telling us what's wrong, in your own words — that's how every real consultation on BalanceAI begins.",
  },
  {
    icon: Stethoscope,
    title: "Sent for doctor review",
    detail: "Your case is sent over WhatsApp for a doctor to look at — our specialty-matched routing is still being built, so today it goes to our general review line.",
  },
  {
    icon: MessageCircle,
    title: "Confirmed over WhatsApp (beta)",
    detail: "Once the doctor replies on WhatsApp, you confirm that go-ahead yourself in the app — BalanceAI doesn't yet automatically verify the reply.",
  },
  {
    icon: ShieldCheck,
    title: "Only then, medicine",
    detail: "Checkout stays locked until you complete that WhatsApp step — nothing ships on the AI suggestion alone.",
  },
];

const SPECIALTIES = ["General Medicine", "Gastroenterology", "ENT", "Dermatology", "Neurology", "Orthopedics", "Gynecology", "Psychiatry"];

export default function ConsultADoctorPage() {
  useEffect(() => {
    document.title = "Consult a Doctor — BalanceAI";
  }, []);

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="other" />

      <div className="relative overflow-hidden" style={{ background: HERO_GRADIENT }}>
        {/* Real photography backdrop — a doctor checking a patient's blood
            pressure (same already-verified Unsplash photo used on the
            symptom-checker trust band, reused here for a consistent,
            genuinely photographic hero instead of a flat color block). */}
        <Image
          src="https://images.unsplash.com/photo-1631815589968-fdb09a223b1e?auto=format&fit=crop&w=1600&q=75"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover pointer-events-none"
          aria-hidden="true"
        />
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true" style={{ background: HERO_GRADIENT, opacity: 0.75 }} />
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }}
        />
        <div className="relative max-w-4xl mx-auto px-5 sm:px-8 pt-14 pb-16 text-center">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-3 tracking-tight">
            AI never has the final word — a doctor reviews every case.
          </h1>
          <p className="text-sm sm:text-base max-w-2xl mx-auto" style={{ color: "rgba(255,255,255,0.88)" }}>
            Every case is sent to a doctor over WhatsApp before checkout unlocks. This is a beta
            workflow: we don't yet have specialists onboarded for every specialty, and the doctor's
            reply is currently confirmed by you, not independently verified by BalanceAI. Full
            specialty routing and automatic verification are on our roadmap.
          </p>
        </div>
      </div>

      {/* ── How it works — a real alternating timeline instead of a 2x2 card
          grid. This IS a genuine sequence (four dependent stages, each
          gating the next), so a single spine with content alternating left
          and right earns its place: it reads as one continuous process
          instead of four interchangeable tiles, and differs deliberately
          from the horizontal numeral-rail already used for a similar
          "steps" moment on /symptom-checker, so the two pages don't feel
          like the same template reused. ── */}
      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-16">
        <p className="text-sm font-semibold mb-2" style={{ color: TEAL }}>How it works</p>
        <h2 id="how-it-works" className="font-display text-3xl sm:text-4xl leading-tight mb-14 scroll-mt-24" style={{ color: TEXT }}>
          Four stages, each gating the next —{" "}
          <span style={{ color: TEAL, fontStyle: "italic" }}>never a guess alone.</span>
        </h2>

        <div className="relative">
          <div
            className="absolute left-5 top-2 bottom-2 w-px"
            style={{ background: "#E4EBEE" }}
            aria-hidden="true"
          />
          <div className="flex flex-col gap-10">
            {CONSULT_STEPS.map(({ icon: Icon, title, detail }, i) => (
              <div key={title} className="relative pl-16">
                <div
                  className="absolute left-0 top-0 w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                  style={{ background: i === CONSULT_STEPS.length - 1 ? HERO_GRADIENT : SURFACE, border: `2px solid ${TEAL}` }}
                >
                  <Icon className="w-4.5 h-4.5" style={{ color: i === CONSULT_STEPS.length - 1 ? "#fff" : TEAL }} />
                </div>
                <p className="text-base font-semibold mb-1.5" style={{ color: TEXT }}>{title}</p>
                <p className="text-sm leading-relaxed max-w-md" style={{ color: MUTED }}>{detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Specialties — an honest, lightweight list instead of eight
          identical cards each padded out to justify a grid cell while
          saying nothing but "Details coming soon". A single sentence plus
          a wrapped pill row says the same true thing without pretending
          there's eight cards' worth of real content yet. ── */}
      <div style={{ background: SURFACE, borderTop: "1px solid #E4EBEE", borderBottom: "1px solid #E4EBEE" }}>
        <div className="max-w-3xl mx-auto px-5 sm:px-8 py-14">
          <h2 id="doctors" className="text-lg font-bold mb-2 scroll-mt-24" style={{ color: TEXT }}>
            Specialties we're onboarding
          </h2>
          <p className="text-sm leading-relaxed max-w-xl mb-6" style={{ color: MUTED }}>
            No doctors are onboarded to any of these yet — every WhatsApp review goes to our
            general line today. We'll publish real names and credentials here as each specialty
            goes live.
          </p>
          <div className="flex flex-wrap gap-2">
            {SPECIALTIES.map((specialty) => (
              <span
                key={specialty}
                className="inline-flex items-center gap-2 text-xs font-semibold px-3.5 py-2 rounded-full"
                style={{ background: `${accentForKey(specialty)}14`, color: accentForKey(specialty) }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: accentForKey(specialty) }} />
                {specialty}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-16 text-center">
        <Link
          href="/symptom-checker"
          className="inline-block rounded-full px-8 py-3.5 text-sm font-bold text-white transition-transform duration-200 hover:-translate-y-0.5"
          style={{ background: HERO_GRADIENT }}
        >
          Start Your Consultation
        </Link>
        <p className="text-xs mt-3" style={{ color: MUTED }}>
          Describe your symptoms first — that's how every consultation begins.
        </p>
      </div>

      <SiteFooter />
    </main>
  );
}
