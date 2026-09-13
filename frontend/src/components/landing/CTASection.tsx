"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Leaf } from "lucide-react";

export default function CTASection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-32 px-5 sm:px-8 overflow-hidden"
      style={{ background: "var(--land-bg)" }}
    >
      {/* Glow background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 700px 500px at 50% 50%, rgba(0,217,126,0.07) 0%, transparent 70%)",
        }}
      />

      {/* Radial ring decorations */}
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full pointer-events-none"
          style={{
            width: `${i * 200 + 300}px`,
            height: `${i * 200 + 300}px`,
            border: `1px solid rgba(0,217,126,${0.06 - i * 0.015})`,
          }}
        />
      ))}

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 max-w-3xl mx-auto text-center"
      >
        {/* Icon */}
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-8 glow-md"
          style={{ background: "#00d97e" }}
        >
          <Leaf className="w-7 h-7 text-black" />
        </div>

        <h2 className="land-h2 mb-5">
          Apni Body Ko Samjho.
          <br />
          <span style={{ color: "#00d97e" }}>Aaj. Free. 2 Minute.</span>
        </h2>

        <p
          className="text-lg mb-10 max-w-xl mx-auto"
          style={{ color: "rgba(255,255,255,0.48)", fontFamily: "var(--font-inter)" }}
        >
          Koi blood test nahi, koi doctor nahi, koi subscription nahi.
          Bas apni awaaz — aur AI bata dega kya kami hai.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/analyze">
            <button
              className="flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-black text-base transition-all glow-btn"
              style={{ background: "#00d97e" }}
            >
              Analysis Shuru Karo
              <ArrowRight className="w-5 h-5" />
            </button>
          </Link>
          <Link href="/demo">
            <button
              className="flex items-center gap-2 px-8 py-4 rounded-xl font-semibold text-base glass-dark"
              style={{ color: "rgba(255,255,255,0.75)" }}
            >
              Pehle Demo Dekho
            </button>
          </Link>
        </div>

        {/* Trust line */}
        <div className="flex items-center justify-center gap-6 mt-10">
          {["No signup", "No credit card", "Works offline", "100% free"].map((t, i) => (
            <div key={t} className="flex items-center gap-1.5 text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>
              <span className="w-1 h-1 rounded-full" style={{ background: "#00d97e", opacity: 0.6 }} />
              {t}
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
