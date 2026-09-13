"use client";

import { useMemo, useState } from "react";
import { buildHeatmapData, scoreColor, type AnalysisEntry } from "@/lib/db";

interface Props {
  analyses: AnalysisEntry[];
  weeks?: number;
}

function cellColor(score: number | undefined): string {
  if (score === undefined) return "rgba(255,255,255,0.04)";
  const c = scoreColor(score);
  const intensity = score / 100;
  if (score >= 70) return `rgba(34,197,94,${0.15 + intensity * 0.75})`;
  if (score >= 40) return `rgba(245,158,11,${0.15 + intensity * 0.65})`;
  return `rgba(239,68,68,${0.15 + intensity * 0.6})`;
}

export default function StreakCalendar({ analyses, weeks = 26 }: Props) {
  const [tooltip, setTooltip] = useState<{ date: string; score?: number; x: number; y: number } | null>(null);
  const heatmap = useMemo(() => buildHeatmapData(analyses), [analyses]);

  const cells = useMemo(() => {
    const result: Array<{ dateStr: string; score?: number; dayOfWeek: number }> = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let w = weeks - 1; w >= 0; w--) {
      for (let d = 0; d < 7; d++) {
        const date = new Date(today);
        const daysBack = w * 7 + (6 - d);
        date.setDate(today.getDate() - daysBack);
        const dateStr = date.toISOString().split("T")[0];
        result.push({ dateStr, score: heatmap.get(dateStr), dayOfWeek: d });
      }
    }
    return result;
  }, [heatmap, weeks]);

  const CELL = 11;
  const GAP  = 2;
  const total = CELL + GAP;

  return (
    <div className="relative">
      {/* Day labels */}
      <div className="flex mb-1" style={{ marginLeft: 0 }}>
        <div style={{ display: "grid", gridTemplateRows: `repeat(7, ${total}px)` }}>
          {["S","M","T","W","T","F","S"].map((d, i) => (
            <div key={i} className="flex items-center" style={{ height: total }}>
              <span style={{ fontSize: 8, color: "rgba(255,255,255,0.2)", width: 12 }}>
                {i % 2 === 1 ? d : ""}
              </span>
            </div>
          ))}
        </div>

        {/* Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateRows: `repeat(7, ${CELL}px)`,
            gridTemplateColumns: `repeat(${weeks}, ${CELL}px)`,
            gap: GAP,
            gridAutoFlow: "column",
          }}
        >
          {cells.map(({ dateStr, score }, idx) => (
            <div
              key={idx}
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const parent = e.currentTarget.closest(".relative")?.getBoundingClientRect();
                setTooltip({
                  date: dateStr,
                  score,
                  x: rect.left - (parent?.left ?? 0) + CELL / 2,
                  y: rect.top - (parent?.top ?? 0) - 36,
                });
              }}
              onMouseLeave={() => setTooltip(null)}
              style={{
                width: CELL,
                height: CELL,
                borderRadius: 2,
                background: cellColor(score),
                cursor: score !== undefined ? "pointer" : "default",
                transition: "opacity 0.15s",
              }}
            />
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-20 px-2.5 py-1.5 rounded-lg text-xs pointer-events-none"
          style={{
            left: tooltip.x,
            top: tooltip.y,
            transform: "translateX(-50%)",
            background: "rgba(10,10,15,0.95)",
            border: "1px solid rgba(255,255,255,0.1)",
            color: "rgba(255,255,255,0.85)",
            whiteSpace: "nowrap",
          }}
        >
          <div className="font-semibold">{tooltip.date}</div>
          {tooltip.score !== undefined ? (
            <div style={{ color: scoreColor(tooltip.score) }}>Score: {tooltip.score}/100</div>
          ) : (
            <div style={{ color: "rgba(255,255,255,0.3)" }}>No analysis</div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-2 mt-2">
        <span style={{ fontSize: 9, color: "rgba(255,255,255,0.25)" }}>Less</span>
        {[0.1, 0.3, 0.5, 0.7, 0.9].map((v) => (
          <div
            key={v}
            style={{
              width: CELL, height: CELL, borderRadius: 2,
              background: `rgba(34,197,94,${v})`,
            }}
          />
        ))}
        <span style={{ fontSize: 9, color: "rgba(255,255,255,0.25)" }}>More</span>
      </div>
    </div>
  );
}
