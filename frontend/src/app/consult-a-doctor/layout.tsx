import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Consult a Doctor — Real Review Before Checkout | BalanceAI",
  description:
    "AI never has the final word — every case is sent to a doctor over WhatsApp before checkout unlocks. This is a beta workflow: today the doctor's reply is confirmed by you, not yet independently verified by BalanceAI.",
  openGraph: {
    title: "Consult a Doctor — Real Review Before Checkout | BalanceAI",
    description: "Every case is sent to a doctor over WhatsApp before checkout unlocks.",
    type: "website",
  },
};

export default function ConsultLayout({ children }: { children: React.ReactNode }) {
  return children;
}
