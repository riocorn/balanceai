"use client";

import { motion } from "framer-motion";
import { WifiOff, Leaf } from "lucide-react";
import Link from "next/link";

export default function OfflinePage() {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6 text-center"
      style={{ background: "#06060a" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6 max-w-sm"
      >
        <div className="w-16 h-16 rounded-2xl bg-[#00d97e] flex items-center justify-center mx-auto">
          <Leaf className="w-8 h-8 text-black" />
        </div>
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto"
          style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
        >
          <WifiOff className="w-6 h-6" style={{ color: "rgba(255,255,255,0.3)" }} />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-display mb-2" style={{ color: "rgba(255,255,255,0.9)" }}>
            Offline ho gaye
          </h1>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
            Internet nahi hai abhi. Pehle se cache pages dekh sakte ho — dashboard aur history available hai.
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <Link href="/dashboard">
            <div
              className="px-6 py-3 rounded-xl text-sm font-semibold text-black text-center"
              style={{ background: "#00d97e" }}
            >
              Dashboard Dekho
            </div>
          </Link>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 rounded-xl text-sm font-medium"
            style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.5)" }}
          >
            Retry
          </button>
        </div>
      </motion.div>
    </div>
  );
}
