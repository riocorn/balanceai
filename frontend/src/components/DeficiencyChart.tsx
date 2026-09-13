"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { DEFICIENCY_LABELS } from "@/lib/api";
import type { DeficiencyResult } from "@/lib/api";

interface Props {
  predictions: DeficiencyResult[];
  showAll?: boolean;
}

const RISK_CONFIG = {
  high:   { label: "High Risk",   color: "bg-red-500",    text: "text-red-600 dark:text-red-400",   badge: "destructive" as const },
  medium: { label: "Medium Risk", color: "bg-amber-400",  text: "text-amber-600 dark:text-amber-400", badge: "secondary" as const },
  low:    { label: "Low Risk",    color: "bg-emerald-400", text: "text-emerald-600 dark:text-emerald-400", badge: "outline" as const },
};

export default function DeficiencyChart({ predictions, showAll = false }: Props) {
  const items = showAll ? predictions : predictions.slice(0, 10);

  return (
    <div className="space-y-3">
      {items.map((item, i) => {
        const cfg = RISK_CONFIG[item.risk_level];
        const label = DEFICIENCY_LABELS[item.deficiency] || item.deficiency;
        const pct = Math.round(item.probability * 100);

        return (
          <motion.div
            key={item.deficiency}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="space-y-1.5"
          >
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="font-medium">{label}</span>
                <Badge variant={cfg.badge} className="text-xs py-0">{cfg.label}</Badge>
              </div>
              <span className={`text-xs font-semibold ${cfg.text}`}>{pct}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                className={`h-full ${cfg.color} rounded-full`}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ delay: i * 0.05 + 0.2, duration: 0.7, ease: "easeOut" }}
              />
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
