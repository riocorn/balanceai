"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { DeficiencyResult } from "@/lib/api";
import { DEFICIENCY_LABELS } from "@/lib/api";

type RegionId = "head" | "chest" | "abdomen" | "arms" | "legs";

const REGIONS: Record<RegionId, { label: string; emoji: string; deficiencies: string[] }> = {
  head: {
    label: "Head & Brain",
    emoji: "🧠",
    deficiencies: ["vitamin_b12", "iron", "vitamin_d", "vitamin_b7", "iodine", "folate", "vitamin_b3", "vitamin_a"],
  },
  chest: {
    label: "Chest & Heart",
    emoji: "❤️",
    deficiencies: ["vitamin_d", "calcium", "omega3", "magnesium", "potassium", "vitamin_k", "selenium", "vitamin_e"],
  },
  abdomen: {
    label: "Gut & Metabolism",
    emoji: "⚙️",
    deficiencies: ["zinc", "folate", "vitamin_b12", "vitamin_b6", "vitamin_c", "vitamin_b5", "chromium", "phosphorus", "vitamin_b1", "vitamin_b2"],
  },
  arms: {
    label: "Arms & Circulation",
    emoji: "💪",
    deficiencies: ["vitamin_b12", "iron", "calcium", "vitamin_d", "copper", "vitamin_e", "vitamin_b6"],
  },
  legs: {
    label: "Legs & Bones",
    emoji: "🦴",
    deficiencies: ["vitamin_d", "calcium", "magnesium", "potassium", "iron", "vitamin_b12", "manganese", "phosphorus", "vitamin_k"],
  },
};

type RiskLevel = "high" | "medium" | "low" | "none";

function regionRisk(id: RegionId, preds: DeficiencyResult[]): RiskLevel {
  const defs = REGIONS[id].deficiencies;
  const relevant = preds.filter((p) => defs.includes(p.deficiency));
  if (relevant.some((p) => p.risk_level === "high")) return "high";
  if (relevant.some((p) => p.risk_level === "medium")) return "medium";
  if (relevant.some((p) => p.risk_level === "low")) return "low";
  return "none";
}

const FILL: Record<RiskLevel, string> = {
  high: "rgba(239,68,68,0.22)",
  medium: "rgba(245,158,11,0.18)",
  low: "rgba(34,197,94,0.14)",
  none: "rgba(255,255,255,0.05)",
};
const STROKE: Record<RiskLevel, string> = {
  high: "rgba(239,68,68,0.65)",
  medium: "rgba(245,158,11,0.55)",
  low: "rgba(34,197,94,0.5)",
  none: "rgba(255,255,255,0.1)",
};
const GLOW_COLOR: Record<RiskLevel, string> = {
  high: "#ef4444", medium: "#f59e0b", low: "#22c55e", none: "transparent",
};

interface Props { predictions: DeficiencyResult[] }

export default function BodyHeatmap({ predictions }: Props) {
  const [selected, setSelected] = useState<RegionId | null>(null);
  const [hovered, setHovered] = useState<RegionId | null>(null);

  const risks = useMemo<Record<RegionId, RiskLevel>>(() => ({
    head: regionRisk("head", predictions),
    chest: regionRisk("chest", predictions),
    abdomen: regionRisk("abdomen", predictions),
    arms: regionRisk("arms", predictions),
    legs: regionRisk("legs", predictions),
  }), [predictions]);

  const selectedPreds = useMemo(() => {
    if (!selected) return [];
    return predictions
      .filter((p) => REGIONS[selected].deficiencies.includes(p.deficiency))
      .sort((a, b) => ({ high: 0, medium: 1, low: 2 }[a.risk_level] - { high: 0, medium: 1, low: 2 }[b.risk_level]));
  }, [selected, predictions]);

  const regionStyle = (id: RegionId) => {
    const r = risks[id];
    const isHov = hovered === id;
    const isDim = selected !== null && selected !== id;
    return {
      fill: FILL[r],
      stroke: STROKE[r],
      strokeWidth: isHov || selected === id ? 1.8 : 1,
      cursor: "pointer" as const,
      opacity: isDim ? 0.38 : 1,
      filter: r !== "none" && (isHov || selected === id)
        ? `drop-shadow(0 0 8px ${GLOW_COLOR[r]}60)`
        : undefined,
      transition: "all 0.18s",
    };
  };

  const click = (id: RegionId) => setSelected((p) => (p === id ? null : id));

  return (
    <div
      className="rounded-2xl p-5"
      style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
    >
      <p className="text-sm font-semibold mb-0.5" style={{ color: "rgba(255,255,255,0.7)" }}>
        Body Risk Map
      </p>
      <p className="text-xs mb-4" style={{ color: "rgba(255,255,255,0.3)" }}>
        Kisi bhi area par click karo
      </p>

      <div className="flex gap-5 items-start">
        {/* SVG silhouette */}
        <svg
          viewBox="0 0 120 300"
          width={108}
          height={270}
          style={{ overflow: "visible", flexShrink: 0 }}
        >
          {/* Head */}
          <ellipse
            cx={60} cy={26} rx={22} ry={24}
            style={regionStyle("head")}
            onClick={() => click("head")}
            onMouseEnter={() => setHovered("head")}
            onMouseLeave={() => setHovered(null)}
          />
          {/* Neck (non-interactive) */}
          <rect
            x={52} y={49} width={16} height={14} rx={4}
            style={{ fill: "rgba(255,255,255,0.04)", stroke: "rgba(255,255,255,0.07)", strokeWidth: 1 }}
          />
          {/* Left arm */}
          <rect
            x={2} y={64} width={26} height={88} rx={13}
            style={regionStyle("arms")}
            onClick={() => click("arms")}
            onMouseEnter={() => setHovered("arms")}
            onMouseLeave={() => setHovered(null)}
          />
          {/* Right arm */}
          <rect
            x={92} y={64} width={26} height={88} rx={13}
            style={regionStyle("arms")}
            onClick={() => click("arms")}
            onMouseEnter={() => setHovered("arms")}
            onMouseLeave={() => setHovered(null)}
          />
          {/* Chest */}
          <rect
            x={28} y={62} width={64} height={60} rx={10}
            style={regionStyle("chest")}
            onClick={() => click("chest")}
            onMouseEnter={() => setHovered("chest")}
            onMouseLeave={() => setHovered(null)}
          />
          {/* Abdomen */}
          <rect
            x={32} y={120} width={56} height={50} rx={8}
            style={regionStyle("abdomen")}
            onClick={() => click("abdomen")}
            onMouseEnter={() => setHovered("abdomen")}
            onMouseLeave={() => setHovered(null)}
          />
          {/* Left leg */}
          <rect
            x={34} y={168} width={24} height={124} rx={12}
            style={regionStyle("legs")}
            onClick={() => click("legs")}
            onMouseEnter={() => setHovered("legs")}
            onMouseLeave={() => setHovered(null)}
          />
          {/* Right leg */}
          <rect
            x={62} y={168} width={24} height={124} rx={12}
            style={regionStyle("legs")}
            onClick={() => click("legs")}
            onMouseEnter={() => setHovered("legs")}
            onMouseLeave={() => setHovered(null)}
          />
        </svg>

        {/* Right panel */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Legend */}
          <div className="space-y-1.5">
            {(["high", "medium", "low", "none"] as RiskLevel[]).map((r) => (
              <div key={r} className="flex items-center gap-2">
                <div
                  className="w-2.5 h-2.5 rounded-sm shrink-0"
                  style={{ background: r === "none" ? "rgba(255,255,255,0.1)" : GLOW_COLOR[r] }}
                />
                <span className="text-[11px]" style={{ color: "rgba(255,255,255,0.35)" }}>
                  {r === "high" ? "High Risk" : r === "medium" ? "Medium Risk" : r === "low" ? "Low Risk" : "No Issue"}
                </span>
              </div>
            ))}
          </div>

          {/* Selected region detail */}
          <AnimatePresence mode="wait">
            {selected ? (
              <motion.div
                key={selected}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.18 }}
                className="rounded-xl p-3"
                style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)" }}
              >
                <p className="text-xs font-bold mb-2" style={{ color: "rgba(255,255,255,0.8)" }}>
                  {REGIONS[selected].emoji} {REGIONS[selected].label}
                </p>
                {selectedPreds.length === 0 ? (
                  <p className="text-xs" style={{ color: "rgba(34,197,94,0.8)" }}>✓ Sab theek lag raha hai</p>
                ) : (
                  <div className="space-y-1.5">
                    {selectedPreds.slice(0, 5).map((p) => {
                      const c = p.risk_level === "high" ? "#ef4444" : p.risk_level === "medium" ? "#f59e0b" : "#22c55e";
                      return (
                        <div key={p.deficiency} className="flex items-center justify-between gap-2">
                          <span className="text-[11px] truncate" style={{ color: "rgba(255,255,255,0.65)" }}>
                            {DEFICIENCY_LABELS[p.deficiency] || p.deficiency}
                          </span>
                          <span className="text-[10px] font-bold shrink-0" style={{ color: c }}>
                            {Math.round(p.probability * 100)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.p
                key="hint"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-[11px]"
                style={{ color: "rgba(255,255,255,0.2)" }}
              >
                ← Area select karo
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
