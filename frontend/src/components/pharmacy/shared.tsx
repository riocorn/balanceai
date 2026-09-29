"use client";

import { useState } from "react";
import { Check, Plus, PhoneCall } from "lucide-react";
import type { MedicineCard as MedicineCardType } from "@/lib/pharmacy-api";

// Locked to the same BalanceAI marketplace palette used on /pharmacy and
// /symptom-checker (--diag-primary-teal / --diag-primary-blue) so cart,
// checkout and results stay visually consistent with the rest of the
// pharmacy purchase flow instead of the older nutrition-app green.
export const GREEN = "#0E7C86";
export const BORDER = "#E4EBEE";
export const TEXT = "#0B2027";
export const MUTED = "#5B7480";
export const WHATSAPP_GREEN = "#25D366";
// Same secondary accent palette as the rest of the marketplace
// (components/diag/theme.ts) -- reused here so the pharmacy flow (cart,
// checkout, product cards) reads as one colorful system instead of a
// separate flat teal-only zone.
export const ACCENT_AMBER = "#C98A2C";
export const ACCENT_PURPLE = "#7C5CBF";

export function ExpandableText({
  text,
  collapsedChars = 260,
  className = "",
  style,
}: {
  text: string;
  collapsedChars?: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const [open, setOpen] = useState(false);
  if (!text) return null;
  const needsTruncate = text.length > collapsedChars;
  const shown = open || !needsTruncate ? text : text.slice(0, collapsedChars) + "…";

  return (
    <p className={className} style={style}>
      {shown}{" "}
      {needsTruncate && (
        <button
          onClick={() => setOpen((o) => !o)}
          className="font-semibold underline underline-offset-2"
          style={{ color: GREEN }}
        >
          {open ? "kam dikhayein" : "poora padhein"}
        </button>
      )}
    </p>
  );
}

/**
 * Hardcoded, always-on safety banner — independent of which specific disease
 * the AI model matched. Triggered by a deterministic red-flag keyword scan on
 * the server (never by the LLM's own judgment), because testing showed the
 * local model can correctly sense "this is an emergency" while still picking
 * an unlikely specific disease that may carry no emergency text of its own.
 */
export function HardEmergencyBanner() {
  return (
    <div
      className="rounded-xl p-4 mb-4 flex items-start gap-3"
      style={{ background: "#7f1d1d", color: "#fff" }}
    >
      <PhoneCall className="w-5 h-5 shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-bold mb-1">Ye emergency jaisa lag raha hai</p>
        <p className="text-xs leading-relaxed opacity-90">
          Apni describe ki hui problem ke hisaab se, kripya AI suggestion ka intezaar na karein —
          turant nearest hospital/emergency ke paas jaayein ya <strong>112</strong> par call karein.
        </p>
      </div>
    </div>
  );
}

export function EffectivenessBadge({ pct }: { pct: number | null }) {
  if (pct === null || pct === undefined) return null;
  const color = pct >= 85 ? "#0f7a3d" : pct >= 60 ? "#b7791f" : "#b91c1c";
  const bg = pct >= 85 ? "#eaf7ef" : pct >= 60 ? "#fdf3e0" : "#fdecec";
  return (
    <span
      className="text-[11px] font-bold px-2 py-1 rounded-full shrink-0"
      style={{ color, background: bg }}
    >
      {pct.toFixed(1)}% real-world effective
    </span>
  );
}

export function MedicineProductCard({
  medicine,
  diseaseId,
  diseaseName,
  inCart,
  onAdd,
  isCurative,
}: {
  medicine: MedicineCardType;
  diseaseId: string;
  diseaseName: string;
  inCart: boolean;
  onAdd: () => void;
  isCurative?: boolean;
}) {
  return (
    <div
      className="rounded-xl p-4 flex flex-col gap-2 relative"
      style={{ background: "#fff", border: `1px solid ${BORDER}` }}
    >
      {isCurative && (
        <span
          className="text-xs font-bold w-fit px-2 py-0.5 rounded"
          style={{ background: "#eef7f2", color: GREEN }}
        >
          Real curative option
        </span>
      )}
      <p className="text-sm font-semibold leading-snug pr-2" style={{ color: TEXT }}>
        {medicine.name}
      </p>
      {medicine.type && (
        <p className="text-[11px] font-medium" style={{ color: MUTED }}>
          {medicine.type}
        </p>
      )}
      {medicine.mechanism && (
        <ExpandableText
          text={medicine.mechanism}
          collapsedChars={180}
          className="text-xs leading-relaxed"
          style={{ color: "#374151" }}
        />
      )}
      {/* price-row slot, e-pharmacy pattern: metric badge left, small ADD pill right */}
      <div className="flex items-center justify-between mt-1 pt-2 border-t" style={{ borderColor: BORDER }}>
        <EffectivenessBadge pct={medicine.effectiveness_pct} />
        <button
          onClick={onAdd}
          disabled={inCart}
          className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg text-xs font-bold border transition-all disabled:opacity-100"
          style={{
            background: inCart ? "#eef7f2" : "#fff",
            color: GREEN,
            borderColor: GREEN,
          }}
        >
          {inCart ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
          {inCart ? "Added" : "Add"}
        </button>
      </div>
    </div>
  );
}
