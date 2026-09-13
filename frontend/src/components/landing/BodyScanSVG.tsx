"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const SCAN_POINTS = [
  { id: "b12",   x: 114, y: 46,  label: "B12",        risk: "high",   side: "right" },
  { id: "fold",  x: 86,  y: 58,  label: "Folate",     risk: "medium", side: "left"  },
  { id: "iod",   x: 114, y: 90,  label: "Iodine",     risk: "medium", side: "right" },
  { id: "iron",  x: 98,  y: 142, label: "Iron",        risk: "high",   side: "left"  },
  { id: "vitd",  x: 120, y: 155, label: "Vitamin D",   risk: "high",   side: "right" },
  { id: "zinc",  x: 42,  y: 162, label: "Zinc",        risk: "medium", side: "left"  },
  { id: "omega", x: 178, y: 158, label: "Omega-3",     risk: "medium", side: "right" },
  { id: "mag",   x: 114, y: 195, label: "Magnesium",   risk: "medium", side: "right" },
  { id: "vitb6", x: 80,  y: 188, label: "Vitamin B6",  risk: "low",    side: "left"  },
  { id: "cal",   x: 82,  y: 308, label: "Calcium",     risk: "low",    side: "left"  },
  { id: "vitk",  x: 146, y: 314, label: "Vitamin K",   risk: "low",    side: "right" },
];

const RISK_COLOR: Record<string, { dot: string; ring: string; glow: string }> = {
  high:   { dot: "#ef4444", ring: "rgba(239,68,68,0.25)",  glow: "rgba(239,68,68,0.6)"  },
  medium: { dot: "#f59e0b", ring: "rgba(245,158,11,0.2)",  glow: "rgba(245,158,11,0.5)" },
  low:    { dot: "#22c55e", ring: "rgba(34,197,94,0.2)",   glow: "rgba(34,197,94,0.5)"  },
};

const SVG_H = 420;

export default function BodyScanSVG() {
  const [visibleDots, setVisibleDots] = useState<Set<string>>(new Set());
  const [scanPhase, setScanPhase] = useState<"scan" | "hold" | "fade">("scan");
  const timerRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    let loopTimeout: ReturnType<typeof setTimeout>;

    const runCycle = () => {
      setScanPhase("scan");
      setVisibleDots(new Set());

      const sorted = [...SCAN_POINTS].sort((a, b) => a.y - b.y);
      const timers: ReturnType<typeof setTimeout>[] = [];

      sorted.forEach((pt) => {
        const delay = (pt.y / SVG_H) * 3500 + 400;
        const t = setTimeout(() => {
          setVisibleDots((prev) => new Set([...prev, pt.id]));
        }, delay);
        timers.push(t);
      });

      const holdT = setTimeout(() => setScanPhase("hold"), 3500 + 400);
      const fadeT = setTimeout(() => setScanPhase("fade"), 7000);
      loopTimeout = setTimeout(() => runCycle(), 8200);

      timerRef.current = [...timers, holdT, fadeT];
    };

    runCycle();
    return () => {
      timerRef.current.forEach(clearTimeout);
      clearTimeout(loopTimeout);
    };
  }, []);

  return (
    <div
      className="relative w-full max-w-[260px] mx-auto select-none"
      style={{ height: `${SVG_H + 40}px` }}
    >
      {/* Outer glow ring */}
      <div
        className="absolute inset-0 rounded-3xl pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at center, rgba(0,217,126,0.04) 0%, transparent 70%)",
          border: "1px solid rgba(0,217,126,0.1)",
        }}
      />

      {/* Status badge */}
      <div
        className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-3 py-1 rounded-full z-20"
        style={{
          background: "rgba(0,0,0,0.6)",
          border: "1px solid rgba(0,217,126,0.2)",
          backdropFilter: "blur(8px)",
        }}
      >
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background: scanPhase === "scan" ? "#00d97e" : "#f59e0b",
            boxShadow: `0 0 6px ${scanPhase === "scan" ? "#00d97e" : "#f59e0b"}`,
            animation: "dotPulse 1.2s ease-in-out infinite",
          }}
        />
        <span className="text-[9px] font-semibold tracking-widest" style={{ color: "rgba(255,255,255,0.7)" }}>
          {scanPhase === "scan" ? "SCANNING" : "ANALYSIS DONE"}
        </span>
      </div>

      {/* Scan line */}
      {scanPhase === "scan" && (
        <div
          className="scan-line"
          style={{ animationDuration: "3.5s", animationDelay: "0.4s" }}
        />
      )}

      {/* Body SVG */}
      <svg
        viewBox="0 0 220 420"
        width="100%"
        height={SVG_H}
        className="relative z-10"
        style={{ filter: "drop-shadow(0 0 12px rgba(0,217,126,0.08))" }}
      >
        {/* ── Body outline ─── */}
        <g style={{ color: "#00d97e" }}>
          {/* Head */}
          <circle cx="110" cy="46" r="28" fill="none" stroke="#00d97e" strokeWidth="1.2" opacity="0.45" />
          {/* Ear left */}
          <ellipse cx="82" cy="46" rx="5" ry="8" fill="none" stroke="#00d97e" strokeWidth="0.9" opacity="0.3" />
          {/* Ear right */}
          <ellipse cx="138" cy="46" rx="5" ry="8" fill="none" stroke="#00d97e" strokeWidth="0.9" opacity="0.3" />

          {/* Neck */}
          <line x1="100" y1="73" x2="100" y2="88" stroke="#00d97e" strokeWidth="1" opacity="0.3" />
          <line x1="120" y1="73" x2="120" y2="88" stroke="#00d97e" strokeWidth="1" opacity="0.3" />

          {/* Shoulders */}
          <path d="M60,94 C75,86 100,88 110,89 C120,88 145,86 160,94" fill="none" stroke="#00d97e" strokeWidth="1.2" opacity="0.4" />

          {/* Torso */}
          <path d="M60,94 L52,205 Q52,213 62,213 L158,213 Q168,213 168,205 L160,94" fill="none" stroke="#00d97e" strokeWidth="1.2" opacity="0.38" />

          {/* Spine (dashed) */}
          <line x1="110" y1="88" x2="110" y2="213" stroke="#00d97e" strokeWidth="0.7" opacity="0.18" strokeDasharray="4 5" />

          {/* Rib lines */}
          {[108, 118, 128, 138, 148, 158].map((y, i) => (
            <path key={i} d={`M68,${y} Q110,${y + 7} 152,${y}`} fill="none" stroke="#00d97e" strokeWidth="0.7" opacity={0.1 - i * 0.008} />
          ))}

          {/* Left arm */}
          <path d="M60,94 C47,118 36,162 30,196" fill="none" stroke="#00d97e" strokeWidth="1.2" opacity="0.38" />
          <path d="M30,196 C27,208 19,214 17,223" fill="none" stroke="#00d97e" strokeWidth="1" opacity="0.28" />
          <ellipse cx="16" cy="232" rx="9" ry="11" fill="none" stroke="#00d97e" strokeWidth="0.9" opacity="0.22" />

          {/* Right arm */}
          <path d="M160,94 C173,118 184,162 190,196" fill="none" stroke="#00d97e" strokeWidth="1.2" opacity="0.38" />
          <path d="M190,196 C193,208 201,214 203,223" fill="none" stroke="#00d97e" strokeWidth="1" opacity="0.28" />
          <ellipse cx="204" cy="232" rx="9" ry="11" fill="none" stroke="#00d97e" strokeWidth="0.9" opacity="0.22" />

          {/* Pelvis */}
          <path d="M75,213 Q110,225 145,213" fill="none" stroke="#00d97e" strokeWidth="0.8" opacity="0.22" strokeDasharray="5 4" />

          {/* Left leg */}
          <path d="M78,213 C74,255 70,300 66,358" fill="none" stroke="#00d97e" strokeWidth="1.2" opacity="0.35" />
          <path d="M102,213 C99,255 96,300 93,358" fill="none" stroke="#00d97e" strokeWidth="1.1" opacity="0.3" />
          {/* Left knee detail */}
          <ellipse cx="84" cy="298" rx="12" ry="8" fill="none" stroke="#00d97e" strokeWidth="0.7" opacity="0.18" />
          {/* Left foot */}
          <path d="M66,358 C64,370 76,374 86,370 C94,367 93,358 93,358" fill="none" stroke="#00d97e" strokeWidth="0.9" opacity="0.22" />

          {/* Right leg */}
          <path d="M142,213 C146,255 150,300 154,358" fill="none" stroke="#00d97e" strokeWidth="1.2" opacity="0.35" />
          <path d="M118,213 C121,255 124,300 127,358" fill="none" stroke="#00d97e" strokeWidth="1.1" opacity="0.3" />
          {/* Right knee detail */}
          <ellipse cx="136" cy="298" rx="12" ry="8" fill="none" stroke="#00d97e" strokeWidth="0.7" opacity="0.18" />
          {/* Right foot */}
          <path d="M154,358 C156,370 144,374 134,370 C126,367 127,358 127,358" fill="none" stroke="#00d97e" strokeWidth="0.9" opacity="0.22" />
        </g>

        {/* ── Nutrient dots ─── */}
        {SCAN_POINTS.map((pt) => {
          const c = RISK_COLOR[pt.risk];
          const visible = visibleDots.has(pt.id);
          const labelX = pt.side === "right" ? pt.x + 28 : pt.x - 28;
          const lineX1 = pt.side === "right" ? pt.x + 8  : pt.x - 8;
          const lineX2 = pt.side === "right" ? pt.x + 20 : pt.x - 20;
          const textAnchor = pt.side === "right" ? "start" : "end";

          return (
            <AnimatePresence key={pt.id}>
              {visible && (
                <motion.g
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0 }}
                  transition={{ type: "spring", stiffness: 340, damping: 22 }}
                  style={{ transformOrigin: `${pt.x}px ${pt.y}px` }}
                >
                  {/* Outer pulse ring */}
                  <circle
                    cx={pt.x} cy={pt.y} r={16}
                    fill="none" stroke={c.dot} strokeWidth="0.6" opacity="0.3"
                    style={{ animation: "dotPulse 2.4s ease-in-out infinite" }}
                  />
                  {/* Inner filled circle */}
                  <circle cx={pt.x} cy={pt.y} r={9} fill={c.ring} stroke={c.dot} strokeWidth="0.8" strokeOpacity="0.6" />
                  {/* Center dot */}
                  <circle
                    cx={pt.x} cy={pt.y} r={4}
                    fill={c.dot}
                    style={{ filter: `drop-shadow(0 0 5px ${c.glow})` }}
                  />
                  {/* Connector line */}
                  <line
                    x1={lineX1} y1={pt.y}
                    x2={lineX2} y2={pt.y}
                    stroke={c.dot} strokeWidth="0.6" opacity="0.6"
                  />
                  {/* Label */}
                  <text
                    x={labelX} y={pt.y + 4}
                    fill={c.dot} fontSize="7.5"
                    fontFamily="var(--font-inter), Inter, sans-serif"
                    fontWeight="500"
                    textAnchor={textAnchor}
                    opacity="0.9"
                  >
                    {pt.label}
                  </text>
                </motion.g>
              )}
            </AnimatePresence>
          );
        })}
      </svg>

      {/* Bottom label */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-center">
        <span
          className="text-[9px] tracking-widest uppercase font-semibold"
          style={{ color: "rgba(0,217,126,0.5)" }}
        >
          25 Nutrients Mapped
        </span>
      </div>
    </div>
  );
}
