import type { Metadata } from "next";
import { FileText } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
import { TEXT, MUTED, BG, SURFACE, BLUE, ACCENT_PURPLE } from "@/components/diag/theme";
import { FOCUS_RING } from "@/components/diag/tokens";

export const metadata: Metadata = { title: "Terms of Service — BalanceAI" };

export default function TermsOfServicePage() {
  return (
    <main style={{ background: BG, minHeight: "100vh" }} className="font-sans">
      <SiteHeader active="other" />
      <div className="max-w-2xl mx-auto px-4 py-14">
        <Card className="!ring-0 !py-0 sc-card p-6 sm:p-8 overflow-hidden relative" style={{ background: SURFACE, border: "1px solid #E4E7E2" }}>
          <div className="absolute top-0 left-0 right-0 h-1.5" style={{ background: ACCENT_PURPLE }} />
          <div className="w-10 h-10 rounded-full flex items-center justify-center mb-4" style={{ background: "rgba(124,92,191,0.1)" }}>
            <FileText className="w-4.5 h-4.5" style={{ color: ACCENT_PURPLE }} strokeWidth={2.25} />
          </div>
          <h1 className="font-display font-extrabold text-3xl mb-6" style={{ color: TEXT }}>
            Terms of Service
          </h1>
          <p className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}>
            BalanceAI is an AI-assisted information tool, not a licensed medical provider, and is not
            intended for use in medical emergencies. By using BalanceAI, you agree that any treatment
            suggestion is reviewed and confirmed by a doctor before you act on it.
          </p>
          <p className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}>
            We aim to keep every piece of medical information on this site accurate and clearly
            sourced. If you ever spot something that looks wrong, please tell us — we take it
            seriously and will correct it promptly.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
            These terms will continue to be expanded as BalanceAI grows. Questions in the meantime are
            always welcome at{" "}
            <a href="mailto:contact@balanceai.example" className={`underline hover:opacity-75 rounded transition-opacity duration-200 ${FOCUS_RING}`} style={{ color: BLUE }}>contact@balanceai.example</a>.
          </p>
        </Card>
      </div>
      <SiteFooter />
    </main>
  );
}
