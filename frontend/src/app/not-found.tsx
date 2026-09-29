"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { TEAL, BG, SURFACE, TEXT, MUTED, HERO_GRADIENT } from "@/components/diag/theme";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center" style={{ background: BG }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6 max-w-sm"
      >
        {/* Custom illustration (see public/illustrations/README.md): a map
            pin marking the dead end, with a broken amber path ring, forking
            into the same two ways back offered by the buttons below (a
            medicine capsule for Order Medicine, a pulse line for Find
            Treatment) — small accent size, not a full hero. */}
        <img
          src="/illustrations/not-found-pin.svg"
          alt=""
          aria-hidden="true"
          className="w-28 h-28 mx-auto"
        />
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
        </div>
      </motion.div>
    </div>
  );
}
