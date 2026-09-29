import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Online Pharmacy — Order Medicine with Doctor Review | BalanceAI",
  description:
    "Order real medicines matched to your symptoms. Every order is routed to a doctor on WhatsApp for review before checkout unlocks — describe your problem in any language.",
  openGraph: {
    title: "Online Pharmacy — Order Medicine with Doctor Review | BalanceAI",
    description: "Describe your problem and order the right medicine, with doctor review before checkout.",
    type: "website",
  },
};

export default function PharmacyLayout({ children }: { children: React.ReactNode }) {
  return children;
}
