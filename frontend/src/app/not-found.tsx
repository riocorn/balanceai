"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Stethoscope } from "lucide-react";
import { TEAL, BG, SURFACE, TEXT, MUTED, HERO_GRADIENT } from "@/components/diag/theme";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center" style={{ background: BG }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6 max-w-sm"
      >
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto" style={{ background: HERO_GRADIENT }}>
          <Stethoscope className="w-8 h-8 text-white" strokeWidth={2} />
        </div>
        <div>
          <p className="text-8xl font-black font-display mb-3" style={{ color: "rgba(11,32,39,0.08)" }}>404</p>
          <h1 className="text-2xl font-bold font-display mb-2" style={{ color: TEXT }}>
            Page nahi mili
          </h1>
          <p className="text-sm" style={{ color: MUTED }}>
            Yeh page exist nahi karta. Shayad link purana ho gaya.
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <Link href="/symptom-checker">
            <div
              className="px-6 py-3 rounded-xl text-sm font-semibold text-white text-center"
              style={{ background: HERO_GRADIENT }}
            >
              Find Treatment
            </div>
          </Link>
          <Link href="/pharmacy">
            <div
              className="px-6 py-3 rounded-xl text-sm font-medium text-center"
              style={{ background: SURFACE, border: "1px solid #E4EBEE", color: TEAL }}
            >
              Order Medicine
            </div>
          </Link>
          <Link href="/">
            <div
              className="px-6 py-3 rounded-xl text-sm font-medium text-center"
              style={{ background: "transparent", color: MUTED }}
            >
              Home Jao
            </div>
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
