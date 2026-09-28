import type { Metadata } from "next";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
import { TEXT, MUTED, BG, SURFACE, BLUE } from "@/components/diag/theme";

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
        <Card className="!ring-0 !py-0 sc-card p-6 sm:p-8" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
          <span className="inline-block text-xs font-bold uppercase tracking-widest mb-3" style={{ color: BLUE }}>
            Legal
          </span>
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
