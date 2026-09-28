"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Stethoscope, MessageCircle, ShieldCheck, ClipboardList } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
import { TEAL, BG, SURFACE, TEXT, MUTED, HERO_GRADIENT } from "@/components/diag/theme";

const CONSULT_STEPS = [
  {
    icon: ClipboardList,
    title: "You describe your case",
    detail: "Start by telling us what's wrong, in your own words — that's how every real consultation on BalanceAI begins.",
  },
  {
    icon: Stethoscope,
    title: "Matched to a specialist",
    detail: "Your case is routed to a doctor from the relevant specialty, not a generic reviewer — the same way a real referral works.",
  },
  {
    icon: MessageCircle,
    title: "Confirmed over WhatsApp",
    detail: "The doctor reviews your case personally and confirms (or adjusts) the suggestion directly with you over WhatsApp.",
  },
  {
    icon: ShieldCheck,
    title: "Only then, medicine",
    detail: "Nothing is dispatched until that confirmation happens — the doctor's judgment is always the final step, not the AI's.",
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
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }}
        />
        <div className="relative max-w-4xl mx-auto px-5 sm:px-8 pt-14 pb-16 text-center">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-3 tracking-tight">
            A real doctor confirms every case.
          </h1>
          <p className="text-sm sm:text-base max-w-2xl mx-auto" style={{ color: "rgba(255,255,255,0.88)" }}>
            BalanceAI never lets AI have the final word. Every case is matched to a doctor from the
            relevant specialty, who personally reviews and confirms it over WhatsApp before any
            medicine is suggested for purchase.
          </p>
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
          Meet the Doctors Reviewing Your Case
        </h2>
        <p className="text-sm text-center max-w-xl mx-auto mb-8" style={{ color: MUTED }}>
          Every case is matched to a doctor from the relevant specialty before any suggestion is
          confirmed. We're publishing our doctors' names and credentials here as they're finalised.
        </p>
        <div className="grid sm:grid-cols-3 gap-4 mb-16">
          {SPECIALTIES.map((specialty) => (
            <div
              key={specialty}
              className="sc-card p-5 flex items-center gap-3"
              style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
            >
              <div className="w-11 h-11 rounded-full flex items-center justify-center shrink-0" style={{ background: HERO_GRADIENT }}>
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
