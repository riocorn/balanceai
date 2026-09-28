import Link from "next/link";
import { TEAL, MUTED, TEXT, SURFACE, BORDER } from "./theme";

// Real 4-column footer structure — measured/observed on Netmeds
// (COMPANY / OUR POLICIES / SHOPPING / SOCIAL, bold uppercase column headers,
// plain link lists) — filled with our own real routes and copy only.
export default function SiteFooter() {
  return (
    <footer style={{ background: SURFACE, borderTop: `3px solid ${TEAL}` }} className="px-4 py-14">
      <div className="max-w-5xl mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-10">
        <div>
          <p className="flex items-center gap-2 font-display font-extrabold text-lg mb-4" style={{ color: TEXT }}>
            {/* eslint-disable-next-line @next/next/no-img-element -- static local vector brand mark */}
            <img src="/illustrations/brand-mark.svg" alt="" aria-hidden="true" className="w-7 h-7 shrink-0" />
            Balance<span style={{ color: TEAL }}>AI</span>
          </p>
          <p className="text-xs font-bold uppercase tracking-wide mb-4" style={{ color: TEAL }}>
            Company
          </p>
          <p className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}>
            Helping you understand your symptoms and find the right care — in your own words, in
            your own language.
          </p>
          <a href="mailto:contact@balanceai.example" className="text-sm font-semibold underline" style={{ color: "#1E6FD9" }}>
            Contact Us
          </a>
        </div>

        <div>
          <p className="text-xs font-bold uppercase tracking-wide mb-4" style={{ color: TEAL }}>
            Product
          </p>
          <ul className="space-y-2.5 text-sm">
            <li>
              <Link href="/symptom-checker" style={{ color: MUTED }} className="hover:underline">
                Find Treatment
              </Link>
            </li>
            <li>
              <Link href="/pharmacy" style={{ color: MUTED }} className="hover:underline">
                Pharmacy
              </Link>
            </li>
            <li>
              <Link href="/medicines" style={{ color: MUTED }} className="hover:underline">
                Medicine Catalog
              </Link>
            </li>
            <li>
              <Link href="/wellness" style={{ color: MUTED }} className="hover:underline">
                Wellness
              </Link>
            </li>
            <li>
              <Link href="/consult-a-doctor" style={{ color: MUTED }} className="hover:underline">
                Consult a Doctor
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-xs font-bold uppercase tracking-wide mb-4" style={{ color: TEAL }}>
            Support
          </p>
          <ul className="space-y-2.5 text-sm">
            <li>
              <a href="/symptom-checker#how-it-works" style={{ color: MUTED }} className="hover:underline">
                How It Works
              </a>
            </li>
            <li>
              <a href="/symptom-checker#faq" style={{ color: MUTED }} className="hover:underline">
                FAQ
              </a>
            </li>
            <li>
              <Link href="/pharmacy/cart" style={{ color: MUTED }} className="hover:underline">
                My Cart
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-xs font-bold uppercase tracking-wide mb-4" style={{ color: TEAL }}>
            Legal
          </p>
          <ul className="space-y-2.5 text-sm">
            <li>
              <Link href="/legal/privacy-policy" style={{ color: MUTED }} className="hover:underline">
                Privacy Policy
              </Link>
            </li>
            <li>
              <Link href="/legal/terms-of-service" style={{ color: MUTED }} className="hover:underline">
                Terms of Service
              </Link>
            </li>
            <li>
              <Link href="/legal/medical-disclaimer" style={{ color: MUTED }} className="hover:underline">
                Medical Disclaimer
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className="max-w-5xl mx-auto border-t pt-6 space-y-2" style={{ borderColor: BORDER }}>
        <p className="text-xs" style={{ color: MUTED }}>
          🔒 Your privacy matters to us · Medical emergency? Call 108 immediately
        </p>
        <p className="text-xs" style={{ color: MUTED }}>
          BalanceAI is an AI-assisted information tool, not a licensed medical provider, and is not
          intended for use in medical emergencies. Every order must be sent to a doctor on WhatsApp
          before checkout — this review step is currently self-confirmed by you and not yet
          independently verified by BalanceAI.
        </p>
        <p className="text-xs" style={{ color: MUTED }}>
          © 2026 BalanceAI. Made in India.
        </p>
      </div>
    </footer>
  );
}
