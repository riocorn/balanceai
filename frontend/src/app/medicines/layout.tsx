import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Medicine Catalog — Search Thousands of Medicines | BalanceAI",
  description:
    "Search clear, source-cited information on thousands of medicines, so you always know exactly what you're taking, what it does, and how effective it really is.",
  openGraph: {
    title: "Medicine Catalog — Search Thousands of Medicines | BalanceAI",
    description: "Search clear, source-cited information on thousands of medicines.",
    type: "website",
  },
};

export default function MedicinesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
