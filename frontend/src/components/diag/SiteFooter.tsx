import Link from "next/link";
import { TEAL, MUTED, TEXT, SURFACE, BORDER, BLUE } from "./theme";
import { FOCUS_RING, TRANSITION_ALL } from "./tokens";

// Shared link treatment for every footer nav item — real hover.focus states
// (color shift + underline together, plus a real keyboard-focus ring)
// instead of the previous bare `hover:underline` with no color change and
// no visible focus state at all.
const FOOTER_LINK_CLASS = `rounded hover:text-[#1D5C3D] ${FOCUS_RING}`;
const FOOTER_LINK_STYLE = { color: MUTED, transition: TRANSITION_ALL };

// Real 4-column footer structure. Redesign, 2026-09-29: column headers were
// tracked-out ALL-CAPS labels (Netmeds' own convention, but flagged by the
// design skill as one of the commonest generated-page tells) — replaced
// with the same font-display treatment used for every other heading on the
// site, so the footer reads as part of one considered type system instead
// of a bolted-on template footer.
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
          <p className="font-display font-semibold text-sm mb-4" style={{ color: TEAL }}>
            Company
          </p>
          <p className="text-sm leading-relaxed mb-4" style={{ color: MUTED }}>
            Helping you understand your symptoms and find the right care — in your own words, in
            your own language.
          </p>
          <a
            href="mailto:contact@balanceai.example"
            className={`text-sm font-semibold underline hover:opacity-75 rounded ${FOCUS_RING}`}
            style={{ color: BLUE, transition: TRANSITION_ALL }}
          >
            Contact Us
          </a>
        </div>

        <div>
          <p className="font-display font-semibold text-sm mb-4" style={{ color: TEAL }}>
            Product
          </p>
          <ul className="space-y-2.5 text-sm">
            <li>
              <Link href="/symptom-checker" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                Find Treatment
              </Link>
            </li>
            <li>
              <Link href="/pharmacy" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                Pharmacy
              </Link>
            </li>
            <li>
              <Link href="/medicines" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                Medicine Catalog
              </Link>
            </li>
            <li>
              <Link href="/wellness" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                Wellness
              </Link>
            </li>
            <li>
              <Link href="/consult-a-doctor" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                Consult a Doctor
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="font-display font-semibold text-sm mb-4" style={{ color: TEAL }}>
            Support
          </p>
          <ul className="space-y-2.5 text-sm">
            <li>
              <a href="/symptom-checker#how-it-works" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                How It Works
              </a>
            </li>
            <li>
              <a href="/symptom-checker#faq" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                FAQ
              </a>
            </li>
            <li>
              <Link href="/pharmacy/cart" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                My Cart
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="font-display font-semibold text-sm mb-4" style={{ color: TEAL }}>
            Legal
          </p>
          <ul className="space-y-2.5 text-sm">
            <li>
              <Link href="/legal/privacy-policy" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                Privacy Policy
              </Link>
            </li>
            <li>
              <Link href="/legal/terms-of-service" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
                Terms of Service
              </Link>
            </li>
            <li>
              <Link href="/legal/medical-disclaimer" style={FOOTER_LINK_STYLE} className={`hover:underline ${FOOTER_LINK_CLASS}`}>
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
