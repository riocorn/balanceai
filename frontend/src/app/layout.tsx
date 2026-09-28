import type { Metadata } from "next";
import { Syne, Inter } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import Script from "next/script";
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
  title: "BalanceAI — Find the Right Treatment",
  description:
    "Describe your symptoms in your own words and get matched to real, source-cited medicines and treatments — with every order sent to a doctor on WhatsApp before checkout.",
  keywords: ["symptom checker", "online pharmacy", "medicine", "health", "India"],
  manifest: "/manifest.json",
  openGraph: {
    title: "BalanceAI — Find the Right Treatment",
    description: "Describe your symptoms, get matched to real medicines, doctor review before checkout.",
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
        <meta name="theme-color" content="#f7f8f6" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
      </head>
      <body className="min-h-full flex flex-col antialiased">
        {children}
        <Script id="register-sw" strategy="afterInteractive">
          {`if ('serviceWorker' in navigator) { window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js').catch(() => {}); }); }`}
        </Script>
      </body>
    </html>
  );
}
