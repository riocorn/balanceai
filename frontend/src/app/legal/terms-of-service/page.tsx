import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { Card } from "@/components/ui/card";
import { TEXT, MUTED, BG, SURFACE, BLUE } from "@/components/diag/theme";

export default function TermsOfServicePage() {
  return (
    <main style={{ background: BG, minHeight: "100vh" }} className="font-sans">
      <SiteHeader active="other" />
      <div className="max-w-2xl mx-auto px-4 py-14">
        <Card className="!ring-0 !py-0 sc-card p-6 sm:p-8" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
          <span className="inline-block text-xs font-bold uppercase tracking-widest mb-3" style={{ color: BLUE }}>
            Legal
          </span>
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
            <a href="mailto:contact@balanceai.example" className="underline" style={{ color: BLUE }}>contact@balanceai.example</a>.
          </p>
        </Card>
      </div>
      <SiteFooter />
    </main>
  );
}
