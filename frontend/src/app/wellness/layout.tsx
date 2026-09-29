import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Wellness — Sexual Health, Vitamins, Personal Care | BalanceAI",
  description:
    "Real, commonly used products across sexual wellness, vitamins & supplements, personal care, women's health, and mom & baby care — for genuine preventive health, not general \"boosting\".",
  openGraph: {
    title: "Wellness — Sexual Health, Vitamins, Personal Care | BalanceAI",
    description: "Real wellness products for genuine preventive health.",
    type: "website",
  },
};

export default function WellnessLayout({ children }: { children: React.ReactNode }) {
  return children;
}
