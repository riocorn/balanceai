"use client";

import { AnimatePresence, motion } from "framer-motion";
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { useToastStore, type ToastType } from "@/lib/toast";

const CONFIG: Record<ToastType, { icon: React.ComponentType<any>; color: string; bg: string }> = {
  success: { icon: CheckCircle2,  color: "#00d97e", bg: "rgba(0,217,126,0.08)"  },
  error:   { icon: AlertCircle,   color: "#ef4444", bg: "rgba(239,68,68,0.08)"  },
  info:    { icon: Info,          color: "#818cf8", bg: "rgba(129,140,248,0.08)" },
  warning: { icon: AlertTriangle, color: "#f59e0b", bg: "rgba(245,158,11,0.08)" },
};

export default function Toaster() {
  const { toasts, remove } = useToastStore();

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[70] flex flex-col gap-2 items-center pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => {
          const { icon: Icon, color, bg } = CONFIG[t.type];
          return (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 32, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 16, scale: 0.92 }}
              transition={{ type: "spring", stiffness: 380, damping: 28 }}
              className="pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-2xl shadow-2xl"
              style={{
                background: "#0e0e16",
                border: `1px solid ${color}35`,
                boxShadow: `0 0 24px ${color}18`,
                minWidth: 240,
                maxWidth: 360,
              }}
            >
              <Icon className="w-4 h-4 shrink-0" style={{ color }} />
              <p className="flex-1 text-sm font-medium" style={{ color: "rgba(255,255,255,0.85)" }}>
                {t.message}
              </p>
              <button
                onClick={() => remove(t.id)}
                className="shrink-0 p-0.5 rounded-md"
                style={{ color: "rgba(255,255,255,0.3)" }}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
