"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, Menu, X, ArrowUpRight } from "lucide-react";

const NAV_LINKS = [
  { label: "Features",    href: "#features" },
  { label: "How It Works",href: "#how-it-works" },
  { label: "Science",     href: "#science" },
  { label: "Demo",        href: "/demo" },
];

export default function Navigation() {
  const [scrolled,  setScrolled]  = useState(false);
  const [menuOpen,  setMenuOpen]  = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <header
      className="fixed top-0 inset-x-0 z-50 transition-all duration-500"
      style={{
        background: scrolled ? "rgba(6,6,10,0.75)" : "transparent",
        backdropFilter: scrolled ? "blur(24px)" : "none",
        borderBottom: scrolled ? "1px solid rgba(255,255,255,0.06)" : "none",
      }}
    >
      <nav className="max-w-7xl mx-auto px-5 sm:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 group-hover:scale-105"
            style={{ background: "#00d97e" }}
          >
            <Leaf className="w-4 h-4 text-black" />
          </div>
          <span
            className="font-bold text-base tracking-tight text-white hidden sm:block font-display"
          >
            BalanceAI
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-7">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.label}
              href={l.href}
              className="text-sm transition-colors duration-150"
              style={{ color: "rgba(255,255,255,0.55)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.95)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.55)")}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link href="/demo" className="text-sm" style={{ color: "rgba(255,255,255,0.55)" }}>
            Live Demo
          </Link>
          <Link href="/analyze">
            <button
              className="flex items-center gap-1.5 px-5 py-2 rounded-full text-sm font-semibold text-black transition-all duration-200 glow-btn"
              style={{ background: "#00d97e" }}
            >
              Shuru Karo
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 rounded-lg transition-colors"
          style={{ color: "rgba(255,255,255,0.7)" }}
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </nav>

      {/* Mobile drawer */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
            className="md:hidden px-5 pb-5"
            style={{
              background: "rgba(6,6,10,0.96)",
              backdropFilter: "blur(30px)",
              borderBottom: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            {NAV_LINKS.map((l) => (
              <Link
                key={l.label}
                href={l.href}
                className="flex items-center justify-between py-3.5 text-sm border-b"
                style={{ color: "rgba(255,255,255,0.65)", borderColor: "rgba(255,255,255,0.05)" }}
                onClick={() => setMenuOpen(false)}
              >
                {l.label}
                <ArrowUpRight className="w-3.5 h-3.5 opacity-40" />
              </Link>
            ))}
            <Link href="/analyze" onClick={() => setMenuOpen(false)}>
              <button
                className="mt-4 w-full py-3.5 rounded-xl font-semibold text-sm text-black"
                style={{ background: "#00d97e" }}
              >
                Shuru Karo — Bilkul Free
              </button>
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
