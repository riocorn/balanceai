"use client";

import Link from "next/link";
import { Leaf, ExternalLink, Share2 } from "lucide-react";

const LINKS = {
  Product: [
    { label: "Analyze",    href: "/analyze"    },
    { label: "Demo",       href: "/demo"       },
    { label: "Dashboard",  href: "/dashboard"  },
    { label: "AI Chat",    href: "/chat"       },
    { label: "Food Diary", href: "/diary"      },
  ],
  Business: [
    { label: "Enterprise",    href: "/enterprise"   },
    { label: "For Hospitals", href: "/enterprise"   },
    { label: "API Access",    href: "/enterprise"   },
    { label: "Investor Info", href: "/#investor"    },
  ],
  Science: [
    { label: "How It Works",  href: "#how-it-works" },
    { label: "Research Basis",href: "#science"      },
    { label: "IIT Mandi",     href: "#science"      },
  ],
};

export default function Footer() {
  return (
    <footer
      className="relative py-20 px-5 sm:px-8"
      style={{
        background: "#04040808",
        borderTop: "1px solid rgba(255,255,255,0.05)",
        backgroundColor: "#040408",
      }}
    >
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10 mb-16">
          {/* Brand column */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-5">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: "#00d97e" }}
              >
                <Leaf className="w-4 h-4 text-black" />
              </div>
              <span className="font-bold text-base text-white font-display">BalanceAI</span>
            </div>
            <p className="text-sm leading-relaxed mb-6" style={{ color: "rgba(255,255,255,0.38)", fontFamily: "var(--font-inter)", maxWidth: "240px" }}>
              India ka pehla AI-powered nutrition deficiency detector. Free, offline, Hinglish.
            </p>
            <div
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs"
              style={{
                background: "rgba(0,217,126,0.07)",
                border: "1px solid rgba(0,217,126,0.15)",
                color: "rgba(0,217,126,0.8)",
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              IIT Mandi · AI Research Lab
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(LINKS).map(([group, links]) => (
            <div key={group}>
              <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "rgba(255,255,255,0.3)" }}>
                {group}
              </p>
              <ul className="flex flex-col gap-3">
                {links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-sm transition-colors"
                      style={{ color: "rgba(255,255,255,0.45)" }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.85)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.45)")}
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div
          className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-8"
          style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
        >
          <p className="text-xs text-center sm:text-left" style={{ color: "rgba(255,255,255,0.25)", fontFamily: "var(--font-inter)" }}>
            © 2024 BalanceAI · Ye medical diagnosis nahi hai · Serious symptoms mein doctor se milein
          </p>
          <div className="flex items-center gap-4">
            <Link href="#" className="transition-colors" style={{ color: "rgba(255,255,255,0.3)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.7)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.3)")}
            >
              <ExternalLink className="w-4 h-4" />
            </Link>
            <Link href="#" className="transition-colors" style={{ color: "rgba(255,255,255,0.3)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.7)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.3)")}
            >
              <Share2 className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
