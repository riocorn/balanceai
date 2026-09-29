import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Sans } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";

// Display face: Fraunces — an editorial serif with real personality at large
// sizes (soft ink-trap detailing), chosen to read as a considered clinical
// brand rather than the geometric-sans-display + Inter pairing every
// AI-generated SaaS page defaults to. Optical sizing set to its largest axis
// so headline weight stays warm, not spindly, at small sizes too.
const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  weight: "variable",
  style: ["normal", "italic"],
  axes: ["opsz", "SOFT", "WONK"],
  display: "swap",
});

// Body/UI face: IBM Plex Sans — precise and slightly technical, matching a
// "grounded in real medical evidence" brand story better than a default
// geometric grotesk.
const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
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
      className={`${fraunces.variable} ${plexSans.variable} ${geistMono.variable} h-full`}
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
