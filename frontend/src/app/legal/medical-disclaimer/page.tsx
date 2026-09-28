import type { Metadata } from "next";
import { ShieldAlert } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
import { TEXT, MUTED, BG, SURFACE, ACCENT_AMBER } from "@/components/diag/theme";

export const metadata: Metadata = { title: "Medical Disclaimer — BalanceAI" };

// Verbatim, from src/api/routers/medical.py DISCLAIMER constant (the exact
// string the live /medical/query API returns in every response's "disclaimer"
// field) — never rewritten or shortened here.
const DISCLAIMER =
  "Yeh AI-assisted information hai, jo ek real medical knowledge base se li gayi hai -- " +
  "yeh koi diagnosis nahi hai. Koi bhi dawai lene se pehle ek doctor se zaroor confirm karein. " +
  "(This is AI-assisted information from a real medical knowledge base, not a diagnosis -- " +
  "a doctor must confirm before taking any medicine.)";

export default function MedicalDisclaimerPage() {
  return (
    <main style={{ background: BG, minHeight: "100vh" }} className="font-sans">
      <SiteHeader active="other" />
      <div className="max-w-2xl mx-auto px-4 py-14">
        <Card className="!ring-0 !py-0 sc-card p-6 sm:p-8 overflow-hidden relative" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
          <div className="absolute top-0 left-0 right-0 h-1.5" style={{ background: ACCENT_AMBER }} />
          <div className="w-10 h-10 rounded-full flex items-center justify-center mb-4" style={{ background: "rgba(201,138,44,0.1)" }}>
            <ShieldAlert className="w-4.5 h-4.5" style={{ color: ACCENT_AMBER }} strokeWidth={2.25} />
          </div>
          <h1 className="font-display font-extrabold text-3xl mb-6" style={{ color: TEXT }}>
            Medical Disclaimer
          </h1>
          <p className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}>
            {DISCLAIMER}
          </p>
          <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
            BalanceAI is an AI-assisted information tool, not a licensed medical provider. Not for use
            in medical emergencies.
          </p>
        </Card>
      </div>
      <SiteFooter />
    </main>
  );
}
