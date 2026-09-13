"use client";

import { motion } from "framer-motion";
import { scoreColor } from "@/lib/db";

interface Props {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export default function ScoreRing({ score, size = 148, strokeWidth = 10, label }: Props) {
  const r = (size - strokeWidth * 2) / 2;
  const cx = size / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const color = scoreColor(score);
  const scoreLabel = label ?? (score >= 70 ? "Good" : score >= 40 ? "Needs Attention" : "Action Required");

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: size, height: size }}>
        {/* Outer glow */}
        <div
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            boxShadow: `0 0 40px ${color}22, 0 0 80px ${color}0a`,
          }}
        />

        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rotate-[-90deg]">
          {/* Track */}
          <circle
            cx={cx} cy={cx} r={r}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <motion.circle
            cx={cx} cy={cx} r={r}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
            style={{ filter: `drop-shadow(0 0 8px ${color}90)` }}
          />
          {/* Tick marks (subtle) */}
          {Array.from({ length: 20 }).map((_, i) => {
            const angle = (i / 20) * 360;
            const rad = (angle * Math.PI) / 180;
            const x1 = cx + (r - 2) * Math.cos(rad);
            const y1 = cx + (r - 2) * Math.sin(rad);
            const x2 = cx + (r + strokeWidth * 0.4) * Math.cos(rad);
            const y2 = cx + (r + strokeWidth * 0.4) * Math.sin(rad);
            return (
              <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
            );
          })}
        </svg>

        {/* Center label */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
        >
          <motion.span
            className="font-black font-display leading-none"
            style={{ fontSize: size * 0.28, color }}
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.8, duration: 0.4 }}
          >
            {score}
          </motion.span>
          <span className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>
            /100
          </span>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="px-3 py-1 rounded-full text-xs font-semibold"
        style={{
          background: `${color}18`,
          border: `1px solid ${color}35`,
          color,
        }}
      >
        {scoreLabel}
      </motion.div>
    </div>
  );
}
