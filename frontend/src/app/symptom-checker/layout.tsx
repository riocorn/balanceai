import type { Metadata } from "next";

// Real per-route metadata — previously every route on the site shared the
// exact same title/description from the root layout, so search results and
// social-share previews for /pharmacy, /wellness etc. all showed identical,
// slightly-wrong copy. This file adds this route's own accurate metadata
// without touching the "use client" page.tsx it wraps.
export const metadata: Metadata = {
  title: "Symptom Checker — Find the Right Treatment | BalanceAI",
  description:
    "Describe your symptoms in Hindi, Hinglish or English and get matched to real, source-cited medicines — every suggestion is sent to a doctor on WhatsApp for review before checkout.",
  openGraph: {
    title: "Symptom Checker — Find the Right Treatment | BalanceAI",
    description: "Describe your symptoms and get matched to real medicines, with doctor review before checkout.",
    type: "website",
  },
};

export default function SymptomCheckerLayout({ children }: { children: React.ReactNode }) {
  return children;
}
