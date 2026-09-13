"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Leaf } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center" style={{ background: "#06060a" }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6 max-w-sm"
      >
        <div className="w-16 h-16 rounded-2xl bg-[#00d97e] flex items-center justify-center mx-auto">
          <Leaf className="w-8 h-8 text-black" />
        </div>
        <div>
          <p className="text-8xl font-black font-display mb-3" style={{ color: "rgba(255,255,255,0.07)" }}>404</p>
          <h1 className="text-2xl font-bold font-display mb-2" style={{ color: "rgba(255,255,255,0.9)" }}>
            Page nahi mili
          </h1>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
            Yeh page exist nahi karta. Shayad link purana ho gaya.
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <Link href="/dashboard">
            <div
              className="px-6 py-3 rounded-xl text-sm font-semibold text-black text-center"
              style={{ background: "#00d97e" }}
            >
              Dashboard Jao
            </div>
          </Link>
          <Link href="/">
            <div
              className="px-6 py-3 rounded-xl text-sm font-medium text-center"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.5)" }}
            >
              Home Jao
            </div>
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
