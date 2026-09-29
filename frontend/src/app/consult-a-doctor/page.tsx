"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Stethoscope, MessageCircle, ShieldCheck, ClipboardList, ArrowRight } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
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
        {/* Redesign, 2026-09-29: dropped the centered-text-on-gradient-banner
            treatment (a recognizable generic-AI-page tell) for the same
            left-aligned, asymmetric text+visual split used on
            /symptom-checker and /pharmacy, so all three primary entry
            points read as one considered layout system rather than
            interchangeable banner templates. */}
        <div
          className="absolute inset-0 opacity-[0.10] pointer-events-none"
          aria-hidden="true"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }}
        />
        <div className="absolute -right-24 -top-24 w-80 h-80 rounded-full pointer-events-none" aria-hidden="true" style={{ border: "1px solid rgba(255,255,255,0.12)" }} />
        <div className="relative max-w-5xl mx-auto px-5 sm:px-8 pt-16 pb-16 grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-10 items-center">
          <div className="text-center lg:text-left">
            <h1 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4 tracking-tight leading-[1.05]">
              AI never has the final word — a doctor reviews every case.
            </h1>
            <p className="text-sm sm:text-base max-w-xl mx-auto lg:mx-0" style={{ color: "rgba(255,255,255,0.88)" }}>
              Every case is sent to a doctor over WhatsApp before checkout unlocks. This is a beta
              workflow: we don't yet have specialists onboarded for every specialty, and the doctor's
              reply is currently confirmed by you, not independently verified by BalanceAI. Full
              specialty routing and automatic verification are on our roadmap.
            </p>
          </div>
          {/* Real product flow, not a stock photo of a generic doctor: the
              same three-icon relationship used on /symptom-checker, applied
              to this page's own real sequence — you describe your case,
              WhatsApp carries it to a doctor, you get a confirmed go-ahead. */}
          <div className="flex items-center justify-center gap-2 sm:gap-4" aria-hidden="true">
            {[
              { Icon: ClipboardList, label: "Your case" },
              { Icon: MessageCircle, label: "WhatsApp" },
              { Icon: ShieldCheck, label: "Confirmed" },
            ].map(({ Icon, label }, idx, arr) => (
              <div key={label} className="flex items-center gap-2 sm:gap-4">
                <div className="flex flex-col items-center gap-2">
                  <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl flex items-center justify-center shadow-lg" style={{ background: "#FFFFFF" }}>
                    <Icon className="w-7 h-7 sm:w-9 sm:h-9" style={{ color: idx === 1 ? "#25D366" : TEAL }} />
                  </div>
                  <span className="text-[11px] sm:text-xs font-semibold text-white whitespace-nowrap">{label}</span>
                </div>
                {idx < arr.length - 1 && (
                  <ArrowRight className="w-5 h-5 sm:w-6 sm:h-6 shrink-0" style={{ color: "rgba(255,255,255,0.75)" }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-5 sm:px-8 py-14">
        <h2 id="how-it-works" className="text-xl font-bold mb-6 text-center scroll-mt-24" style={{ color: TEXT }}>
          How a consultation works
        </h2>
        <div className="grid sm:grid-cols-2 gap-4 mb-16">
          {CONSULT_STEPS.map(({ icon: Icon, title, detail }, i) => (
            <Card key={title} className="!ring-0 !py-0 sc-card sc-card-interactive p-5 flex items-start gap-4" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
              <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 text-xs font-extrabold text-white" style={{ background: HERO_GRADIENT }}>
                {i + 1}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Icon className="w-4 h-4" style={{ color: TEAL }} />
                  <p className="text-sm font-bold" style={{ color: TEXT }}>{title}</p>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: MUTED }}>{detail}</p>
              </div>
            </Card>
          ))}
        </div>

        <h2 id="doctors" className="text-xl font-bold mb-2 text-center scroll-mt-24" style={{ color: TEXT }}>
          Specialties We're Onboarding
        </h2>
        <p className="text-sm text-center max-w-xl mx-auto mb-8" style={{ color: MUTED }}>
          We're building out specialty-matched doctor review. No doctors are onboarded to these
          specialties yet — today, every WhatsApp review goes to our general line. We'll publish
          real names and credentials here as each specialty goes live.
        </p>
        <div className="grid sm:grid-cols-3 gap-4 mb-16">
          {SPECIALTIES.map((specialty) => (
            <div
              key={specialty}
              className="sc-card p-5 flex items-center gap-3"
              style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
            >
              <div className="w-11 h-11 rounded-full flex items-center justify-center shrink-0" style={{ background: accentForKey(specialty) }}>
                <Stethoscope className="w-5 h-5 text-white" strokeWidth={2} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold" style={{ color: TEXT }}>{specialty}</p>
                <p className="text-xs" style={{ color: MUTED }}>Details coming soon</p>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center">
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
      </div>

      <SiteFooter />
    </main>
  );
}
