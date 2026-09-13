"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Trash2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { type AnalysisEntry, scoreColor, deleteAnalysis } from "@/lib/db";
import { DEFICIENCY_LABELS } from "@/lib/api";
import DeficiencyChart from "@/components/DeficiencyChart";

interface Props {
  entry: AnalysisEntry;
  onDelete: (id: number) => void;
}

export default function HistoryCard({ entry, onDelete }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const color = scoreColor(entry.score);

  const date = new Date(entry.date);
  const dateStr = date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  const timeStr = date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  const handleDelete = async () => {
    if (!entry.id) return;
    setDeleting(true);
    await deleteAnalysis(entry.id);
    onDelete(entry.id);
  };

  return (
    <motion.div
      layout
      className="rounded-2xl overflow-hidden"
      style={{ background: "rgba(255,255,255,0.035)", border: "1px solid rgba(255,255,255,0.07)" }}
    >
      {/* Header row */}
      <div
        className="flex items-center gap-4 px-5 py-4 cursor-pointer transition-colors"
        onClick={() => setExpanded((e) => !e)}
        style={{ borderBottom: expanded ? "1px solid rgba(255,255,255,0.06)" : "none" }}
      >
        {/* Score pill */}
        <div
          className="w-14 h-14 rounded-2xl flex flex-col items-center justify-center shrink-0"
          style={{ background: `${color}12`, border: `1px solid ${color}25` }}
        >
          <span className="text-xl font-black font-display leading-none" style={{ color }}>
            {entry.score}
          </span>
          <span className="text-[9px]" style={{ color: "rgba(255,255,255,0.3)" }}>/100</span>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className="px-2 py-0.5 rounded-full text-xs font-semibold"
              style={{ background: `${color}15`, color, border: `1px solid ${color}25` }}
            >
              {entry.score_label}
            </span>
            {entry.high_risk.length > 0 && (
              <div className="flex items-center gap-1 text-xs" style={{ color: "#ef4444" }}>
                <AlertTriangle className="w-3 h-3" />
                {entry.high_risk.length} high
              </div>
            )}
          </div>
          <p className="text-xs truncate" style={{ color: "rgba(255,255,255,0.4)" }}>
            {dateStr} · {timeStr}
            {entry.state && <> · {entry.state}</>}
            {entry.symptoms_text && (
              <> · "{entry.symptoms_text.slice(0, 40)}{entry.symptoms_text.length > 40 ? "..." : ""}"</>
            )}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-1.5 rounded-lg transition-colors"
            style={{ color: "rgba(255,255,255,0.2)" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#ef4444")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.2)")}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <ChevronDown
            className="w-4 h-4 transition-transform duration-200"
            style={{
              color: "rgba(255,255,255,0.3)",
              transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
            }}
          />
        </div>
      </div>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="px-5 py-5 space-y-5">
              {/* Deficiency chart */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>
                  Deficiency Analysis
                </p>
                <DeficiencyChart predictions={entry.predictions} showAll={false} />
              </div>

              {/* Diet plan preview */}
              {entry.diet_plan && Object.keys(entry.diet_plan).length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>
                    Diet Plan
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(entry.diet_plan).slice(0, 4).map(([meal, foods]) => (
                      <div
                        key={meal}
                        className="p-3 rounded-xl"
                        style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}
                      >
                        <p className="text-xs font-semibold capitalize mb-1.5" style={{ color: "rgba(255,255,255,0.5)" }}>
                          {meal === "breakfast" ? "🌅" : meal === "lunch" ? "☀️" : meal === "snacks" ? "🍎" : "🌙"} {meal}
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {(Array.isArray(foods) ? foods : [foods]).slice(0, 3).map((f: string, i: number) => (
                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "rgba(0,217,126,0.08)", color: "rgba(0,217,126,0.8)" }}>
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
