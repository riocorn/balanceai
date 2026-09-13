"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Play, Sparkles } from "lucide-react";
import BodyScanSVG from "./BodyScanSVG";

const STATS = [
  { value: "25",    suffix: "",    label: "Nutrients mapped"     },
  { value: "97.3",  suffix: "%",   label: "Detection accuracy"   },
  { value: "2",     suffix: " min",label: "Complete analysis"    },
  { value: "0",     suffix: "₹",   label: "Cost, always free"    },
];

export default function HeroSection() {
  const orbRef1 = useRef<HTMLDivElement>(null);
  const orbRef2 = useRef<HTMLDivElement>(null);

  return (
    <section
      className="relative min-h-screen flex flex-col justify-center overflow-hidden"
      style={{ background: "var(--land-bg)", paddingTop: "5rem", paddingBottom: "4rem" }}
    >
      {/* Mesh gradient background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse 900px 700px at 10% 25%, rgba(0,217,126,0.07) 0%, transparent 65%),
            radial-gradient(ellipse 700px 900px at 88% 75%, rgba(99,102,241,0.055) 0%, transparent 65%),
            radial-gradient(ellipse 500px 500px at 55% 50%, rgba(0,217,126,0.028) 0%, transparent 65%)
          `,
          animation: "meshDrift 16s ease-in-out infinite",
        }}
      />

      {/* Floating orbs */}
      <div
        ref={orbRef1}
        className="absolute top-1/4 left-1/4 w-[400px] h-[400px] rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(0,217,126,0.06) 0%, transparent 70%)",
          filter: "blur(60px)",
          animation: "orbDrift 12s ease-in-out infinite",
        }}
      />
      <div
        ref={orbRef2}
        className="absolute bottom-1/4 right-1/3 w-[320px] h-[320px] rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 70%)",
          filter: "blur(60px)",
          animation: "orbDrift 18s ease-in-out infinite reverse",
        }}
      />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)
          `,
          backgroundSize: "72px 72px",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-8 items-center">
          {/* Left: Content */}
          <motion.div
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* Badge */}
            <div className="flex items-center gap-2 mb-7">
              <div
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-full"
                style={{
                  background: "rgba(0,217,126,0.1)",
                  border: "1px solid rgba(0,217,126,0.25)",
                }}
              >
                <Sparkles className="w-3 h-3" style={{ color: "#00d97e" }} />
                <span className="text-xs font-semibold" style={{ color: "#00d97e" }}>
                  IIT Mandi · AI Research Lab
                </span>
              </div>
              <div
                className="px-3 py-1.5 rounded-full text-xs font-medium"
                style={{
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "rgba(255,255,255,0.55)",
                }}
              >
                v1.0 · India&apos;s First
              </div>
            </div>

            {/* Headline */}
            <h1 className="land-h1 mb-5">
              <span className="text-shimmer">25 Nutrient</span>
              <br />
              <span style={{ color: "rgba(255,255,255,0.92)" }}>Deficiencies.</span>
              <br />
              <span style={{ color: "rgba(255,255,255,0.92)" }}>Detected in</span>{" "}
              <span style={{ color: "#00d97e" }}>2 Minutes.</span>
            </h1>

            {/* Subtext */}
            <p
              className="text-base sm:text-lg leading-relaxed mb-8 max-w-lg"
              style={{ color: "rgba(255,255,255,0.55)", fontFamily: "var(--font-inter)" }}
            >
              Bina blood test. Bina doctor visit. Sirf apni awaaz, ek photo — aur AI bata dega
              kya kami hai tumhare body mein. Hindi mein. Bilkul free.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap gap-3 mb-12">
              <Link href="/analyze">
                <button
                  className="flex items-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-sm text-black transition-all glow-btn"
                  style={{ background: "#00d97e" }}
                >
                  Analysis Shuru Karo
                  <ArrowRight className="w-4 h-4" />
                </button>
              </Link>
              <Link href="/demo">
                <button
                  className="flex items-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-sm transition-all glass-dark"
                  style={{ color: "rgba(255,255,255,0.8)" }}
                >
                  <Play className="w-4 h-4" style={{ color: "#00d97e" }} />
                  Live Demo Dekho
                </button>
              </Link>
            </div>

            {/* Trust stats */}
            <div
              className="grid grid-cols-4 gap-0 pt-8"
              style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}
            >
              {STATS.map((s, i) => (
                <motion.div
                  key={s.label}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + i * 0.1, duration: 0.5 }}
                  className="flex flex-col gap-0.5 pr-4 border-r last:border-r-0"
                  style={{ borderColor: "rgba(255,255,255,0.06)" }}
                >
                  <div className="flex items-baseline gap-0.5">
                    <span
                      className="text-xl sm:text-2xl font-bold font-display"
                      style={{ color: "#00d97e" }}
                    >
                      {s.value}
                    </span>
                    <span className="text-sm font-semibold" style={{ color: "#00d97e" }}>
                      {s.suffix}
                    </span>
                  </div>
                  <span className="text-[11px] leading-tight" style={{ color: "rgba(255,255,255,0.38)" }}>
                    {s.label}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right: Body scan visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="flex justify-center lg:justify-end"
          >
            <div
              className="relative p-6 rounded-3xl"
              style={{
                background: "rgba(0,217,126,0.025)",
                border: "1px solid rgba(0,217,126,0.1)",
                boxShadow: "0 0 80px rgba(0,217,126,0.05), inset 0 0 60px rgba(0,0,0,0.3)",
              }}
            >
              <BodyScanSVG />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom fade */}
      <div
        className="absolute bottom-0 left-0 right-0 h-28 pointer-events-none"
        style={{
          background: "linear-gradient(to bottom, transparent, rgba(6,6,10,0.8))",
        }}
      />
    </section>
  );
}
