"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Check, X, Minus } from "lucide-react";

const ROWS = [
  { feature: "Cost",               balance: "₹0",      blood: "₹3,000–8,000",  apps: "₹500/month"  },
  { feature: "Time to Result",      balance: "2 min",   blood: "3–7 days",       apps: "Varies"       },
  { feature: "Works Offline",       balance: true,      blood: false,            apps: false          },
  { feature: "Hindi / Hinglish",    balance: true,      blood: false,            apps: false          },
  { feature: "25 Nutrients",        balance: true,      blood: true,             apps: "partial"      },
  { feature: "Personalised Diet",   balance: true,      blood: false,            apps: "partial"      },
  { feature: "Visual Analysis",     balance: true,      blood: false,            apps: false          },
  { feature: "No Signup Required",  balance: true,      blood: false,            apps: false          },
  { feature: "Doctor PDF Report",   balance: true,      blood: true,             apps: false          },
  { feature: "Indian Foods",        balance: true,      blood: false,            apps: "partial"      },
];

type CellValue = string | boolean | "partial";

function Cell({ val, highlight }: { val: CellValue; highlight?: boolean }) {
  if (typeof val === "boolean") {
    return val ? (
      <Check
        className="w-4 h-4 mx-auto"
        style={{ color: highlight ? "#00d97e" : "rgba(34,197,94,0.6)" }}
      />
    ) : (
      <X className="w-4 h-4 mx-auto" style={{ color: "rgba(239,68,68,0.5)" }} />
    );
  }
  if (val === "partial") {
    return <Minus className="w-4 h-4 mx-auto" style={{ color: "rgba(245,158,11,0.6)" }} />;
  }
  return (
    <span
      className="text-sm font-semibold"
      style={{ color: highlight ? "#00d97e" : "rgba(255,255,255,0.75)" }}
    >
      {val}
    </span>
  );
}

export default function ComparisonTable() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-28 px-5 sm:px-8"
      style={{ background: "var(--land-bg)" }}
    >
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-center mb-14"
        >
          <p className="land-label mb-4">Comparison</p>
          <h2 className="land-h2 mb-5">
            BalanceAI vs{" "}
            <span style={{ color: "rgba(255,255,255,0.35)" }}>The Alternatives</span>
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.65, delay: 0.15 }}
          className="rounded-2xl overflow-hidden"
          style={{ border: "1px solid rgba(255,255,255,0.08)" }}
        >
          {/* Header */}
          <div
            className="grid grid-cols-4 text-center"
            style={{ background: "rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.07)" }}
          >
            <div className="p-5 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: "rgba(255,255,255,0.35)" }}>
              Feature
            </div>
            <div
              className="p-5 flex flex-col items-center gap-1 relative"
              style={{
                background: "rgba(0,217,126,0.06)",
                borderLeft: "1px solid rgba(0,217,126,0.15)",
                borderRight: "1px solid rgba(0,217,126,0.15)",
              }}
            >
              <div
                className="absolute top-0 left-0 right-0 h-0.5"
                style={{ background: "#00d97e" }}
              />
              <span className="text-xs font-bold tracking-wide" style={{ color: "#00d97e" }}>
                BALANCE AI
              </span>
              <span className="text-[9px]" style={{ color: "rgba(0,217,126,0.55)" }}>Recommended</span>
            </div>
            <div className="p-5" style={{ borderLeft: "1px solid rgba(255,255,255,0.05)" }}>
              <span className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.45)" }}>Blood Test</span>
            </div>
            <div className="p-5" style={{ borderLeft: "1px solid rgba(255,255,255,0.05)" }}>
              <span className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.45)" }}>Other Apps</span>
            </div>
          </div>

          {/* Rows */}
          {ROWS.map((row, i) => (
            <div
              key={row.feature}
              className="grid grid-cols-4 text-center transition-colors"
              style={{
                borderBottom: i < ROWS.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none",
                background: i % 2 === 0 ? "rgba(255,255,255,0.012)" : "transparent",
              }}
            >
              <div className="p-4 text-left text-sm" style={{ color: "rgba(255,255,255,0.55)" }}>
                {row.feature}
              </div>
              <div
                className="p-4 flex items-center justify-center"
                style={{
                  background: "rgba(0,217,126,0.035)",
                  borderLeft: "1px solid rgba(0,217,126,0.1)",
                  borderRight: "1px solid rgba(0,217,126,0.1)",
                }}
              >
                <Cell val={row.balance} highlight />
              </div>
              <div className="p-4 flex items-center justify-center" style={{ borderLeft: "1px solid rgba(255,255,255,0.03)" }}>
                <Cell val={row.blood} />
              </div>
              <div className="p-4 flex items-center justify-center" style={{ borderLeft: "1px solid rgba(255,255,255,0.03)" }}>
                <Cell val={row.apps} />
              </div>
            </div>
          ))}
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ delay: 0.6 }}
          className="text-center text-xs mt-6"
          style={{ color: "rgba(255,255,255,0.25)", fontFamily: "var(--font-inter)" }}
        >
          * Comparison is indicative. BalanceAI is a screening tool, not a medical diagnostic device.
        </motion.p>
      </div>
    </section>
  );
}
