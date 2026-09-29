import type { Metadata } from "next";
import { Lock } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
import { TEXT, MUTED, BG, SURFACE, BLUE } from "@/components/diag/theme";
import { FOCUS_RING } from "@/components/diag/tokens";

export const metadata: Metadata = { title: "Privacy Policy — BalanceAI" };

export default function PrivacyPolicyPage() {
  return (
    <main style={{ background: BG, minHeight: "100vh" }} className="font-sans">
      <SiteHeader active="other" />
      <div className="max-w-2xl mx-auto px-4 py-14">
        <Card className="!ring-0 !py-0 sc-card p-6 sm:p-8 overflow-hidden relative" style={{ background: SURFACE, border: "1px solid #E4E7E2" }}>
          <div className="absolute top-0 left-0 right-0 h-1.5" style={{ background: BLUE }} />
          <div className="w-10 h-10 rounded-full flex items-center justify-center mb-4" style={{ background: "rgba(30,111,217,0.1)" }}>
            <Lock className="w-4.5 h-4.5" style={{ color: BLUE }} strokeWidth={2.25} />
          </div>
          <h1 className="font-display font-extrabold text-3xl mb-6" style={{ color: TEXT }}>
            Privacy Policy
          </h1>
          <p className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}>
            When you describe your symptoms to BalanceAI, that information is used only to help
            understand your condition and match you with the right treatment. We do not sell your
            information to anyone.
          </p>
          <p className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}>
            If you choose to have your case reviewed by a doctor, the details you shared are passed
            to that doctor so they can confirm the suggestion — and to no one else.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
            We're continuing to expand this policy as BalanceAI grows. If you have any questions
            about your data in the meantime, reach out any time at{" "}
            <a href="mailto:contact@balanceai.example" className={`underline hover:opacity-75 rounded transition-opacity duration-200 ${FOCUS_RING}`} style={{ color: BLUE }}>contact@balanceai.example</a>.
          </p>
        </Card>
      </div>
      <SiteFooter />
    </main>
  );
}
