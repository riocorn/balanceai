"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { X } from "lucide-react";
import type { Achievement } from "@/lib/achievements";

interface Props {
  achievement: Achievement;
  onDismiss: () => void;
}

export default function AchievementToast({ achievement, onDismiss }: Props) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 4500);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 80, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 40, scale: 0.92 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className="fixed bottom-6 right-5 z-[60] flex items-center gap-3 px-4 py-3.5 rounded-2xl shadow-2xl"
      style={{
        background: "#0e0e16",
        border: `1px solid ${achievement.color}40`,
        boxShadow: `0 0 30px ${achievement.color}25`,
        maxWidth: 320,
      }}
    >
      {/* Pulsing icon */}
      <div
        className="relative w-11 h-11 rounded-xl flex items-center justify-center shrink-0 text-xl"
        style={{ background: `${achievement.color}18`, border: `1px solid ${achievement.color}35` }}
      >
        {achievement.icon}
        <span
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-ping"
          style={{ background: achievement.color }}
        />
        <span
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full"
          style={{ background: achievement.color }}
        />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-bold uppercase tracking-widest mb-0.5" style={{ color: achievement.color }}>
          Achievement Unlocked!
        </p>
        <p className="text-sm font-bold" style={{ color: "rgba(255,255,255,0.9)" }}>
          {achievement.title}
        </p>
        <p className="text-xs" style={{ color: "rgba(255,255,255,0.45)" }}>
          {achievement.desc}
        </p>
      </div>

      <button
        onClick={onDismiss}
        className="shrink-0 p-1 rounded-lg"
        style={{ color: "rgba(255,255,255,0.3)" }}
      >
        <X className="w-3.5 h-3.5" />
      </button>

      {/* Progress bar */}
      <motion.div
        className="absolute bottom-0 left-0 h-0.5 rounded-full"
        style={{ background: achievement.color }}
        initial={{ width: "100%" }}
        animate={{ width: "0%" }}
        transition={{ duration: 4.5, ease: "linear" }}
      />
    </motion.div>
  );
}
