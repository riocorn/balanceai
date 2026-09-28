import type { Metadata } from "next";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
import { TEXT, MUTED, BG, SURFACE, BLUE } from "@/components/diag/theme";

export const metadata: Metadata = { title: "Privacy Policy — BalanceAI" };

export default function PrivacyPolicyPage() {
  return (
    <main style={{ background: BG, minHeight: "100vh" }} className="font-sans">
      <SiteHeader active="other" />
      <div className="max-w-2xl mx-auto px-4 py-14">
        <Card className="!ring-0 !py-0 sc-card p-6 sm:p-8" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
          <span className="inline-block text-xs font-bold uppercase tracking-widest mb-3" style={{ color: BLUE }}>
            Legal
          </span>
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
            <a href="mailto:contact@balanceai.example" className="underline" style={{ color: BLUE }}>contact@balanceai.example</a>.
          </p>
        </Card>
      </div>
      <SiteFooter />
    </main>
  );
}
