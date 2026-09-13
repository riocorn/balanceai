import type { Metadata } from "next";
import { Syne, Inter } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import "./globals.css";

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BalanceAI — 25 Nutrient Deficiencies Detected, No Blood Test",
  description:
    "AI-powered micronutrient deficiency detection from symptoms, camera, and voice. Personalised Indian diet plan. Free, offline, in Hinglish.",
  keywords: ["nutrition AI", "deficiency detection", "Indian diet", "health", "IIT Mandi"],
  manifest: "/manifest.json",
  openGraph: {
    title: "BalanceAI — Know Your Nutrients. Free.",
    description: "25 deficiencies detected in 2 minutes. No blood test. Works offline. For India.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${syne.variable} ${inter.variable} ${geistMono.variable} h-full`}
    >
      <head>
        <meta name="theme-color" content="#06060a" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
        <script
          dangerouslySetInnerHTML={{
            __html: `if ('serviceWorker' in navigator) { window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js').catch(() => {}); }); }`,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col antialiased">{children}</body>
    </html>
  );
}
