"use client";

import { useState } from "react";
import { Check, Plus, PhoneCall } from "lucide-react";
import type { MedicineCard as MedicineCardType } from "@/lib/pharmacy-api";
import { TRANSITION_ALL, FOCUS_RING, CTA_RADIUS } from "@/components/diag/tokens";
import { TEAL, BORDER as THEME_BORDER, TEXT as THEME_TEXT, MUTED as THEME_MUTED, EFFECTIVENESS, EFFECTIVENESS_TEXT, EMERGENCY, SURFACE } from "@/components/diag/theme";
import MedicinePackPlaceholder from "@/components/diag/MedicinePackPlaceholder";

// Re-exported from the single shared palette in theme.ts (not a hardcoded
// copy) so cart, checkout and results always stay in sync with the rest of
// the pharmacy purchase flow -- this file's own hardcoded hex copy is what
// let it silently drift out of sync with the 2026-09-29 palette deepen
// until it was caught and fixed here.
export const GREEN = TEAL;
export const BORDER = THEME_BORDER;
export const TEXT = THEME_TEXT;
export const MUTED = THEME_MUTED;
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
          className={`font-semibold underline underline-offset-2 rounded hover:opacity-75 ${FOCUS_RING}`}
          style={{ color: GREEN, transition: TRANSITION_ALL }}
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
  // Real color-consistency fix, tier 2 (2026-09-29): this banner was
  // hardcoded to a different dark maroon (#7f1d1d) than the one true
  // EMERGENCY red reserved for every other emergency surface on the site
  // (symptom-checker's banner, theme.ts's own grep-checked rule) — the two
  // reds sitting side by side across pages was a real, visible brand
  // inconsistency. Now pulls the same EMERGENCY token.
  return (
    <div
      className="rounded-xl p-4 mb-4 flex items-start gap-3"
      style={{ background: EMERGENCY, color: "#fff" }}
    >
      <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0" style={{ background: "rgba(255,255,255,0.18)" }}>
        <PhoneCall className="w-4 h-4" strokeWidth={2.25} />
      </div>
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
  const color = pct >= 85 ? EFFECTIVENESS_TEXT : pct >= 60 ? ACCENT_AMBER : "#B42318";
  const bg = pct >= 85 ? "rgba(31,174,122,0.12)" : pct >= 60 ? "rgba(201,138,44,0.12)" : "rgba(180,35,24,0.08)";
  return (
    <span
      className="text-[11px] font-bold px-2 py-1 rounded-full shrink-0"
      style={{ color, background: bg }}
    >
      {pct.toFixed(1)}% real-world effective
    </span>
  );
}

// Rebuilt tier 2 (2026-09-29): this card was a flat, plain
// border-only rectangle with no icon, no effectiveness bar and no
// hover/focus states at all — visibly a generation behind the matching
// symptom-checker medicine card it sits one click away from in the same
// purchase journey. Now shares that exact card system (sc-card hover-lift,
// icon avatar + curative pill overlay, effectiveness progress bar, focus
// ring on Add) so the two feel like one product, not two different eras of
// the same site.
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
  const pct = medicine.effectiveness_pct != null ? Math.round(medicine.effectiveness_pct) : null;
  return (
    <div
      className="sc-card sc-card-interactive p-4 flex flex-col gap-3 relative"
      style={{ background: SURFACE, border: `1px solid ${BORDER}` }}
    >
      <div className="flex items-start gap-3">
        <div className="relative w-12 h-12 shrink-0">
          <MedicinePackPlaceholder />
          <div
            className="sc-icon-pop absolute -bottom-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center border-2"
            style={{
              background: isCurative ? `linear-gradient(135deg, ${EFFECTIVENESS} 0%, ${GREEN} 100%)` : GREEN,
              borderColor: SURFACE,
            }}
          >
            <Plus className="w-2.5 h-2.5 text-white" strokeWidth={2.5} />
          </div>
        </div>
        <div className="min-w-0 flex-1">
          {isCurative && (
            <span
              className="inline-block mb-1 text-[10px] font-bold px-2 py-0.5 rounded-full"
              style={{ background: "rgba(31,174,122,0.12)", color: EFFECTIVENESS_TEXT }}
            >
              Real curative option
            </span>
          )}
          <p className="text-sm font-semibold leading-snug" style={{ color: TEXT }}>
            {medicine.name}
          </p>
          {medicine.type && (
            <p className="text-[11px] font-medium mt-0.5" style={{ color: MUTED }}>
              {medicine.type}
            </p>
          )}
        </div>
      </div>

      {pct != null && (
        <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "#E4E7E2" }}>
          <div
            className="h-full rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, pct))}%`, background: EFFECTIVENESS }}
          />
        </div>
      )}

      {medicine.mechanism && (
        <ExpandableText
          text={medicine.mechanism}
          collapsedChars={180}
          className="text-xs leading-relaxed"
          style={{ color: MUTED }}
        />
      )}
      {/* price-row slot, e-pharmacy pattern: metric badge left, small ADD pill right */}
      <div className="flex items-center justify-between gap-3 pt-2 border-t" style={{ borderColor: "#EEF3F5" }}>
        <EffectivenessBadge pct={medicine.effectiveness_pct} />
        <button
          onClick={onAdd}
          disabled={inCart}
          className={`flex items-center gap-1 px-3.5 py-1.5 ${CTA_RADIUS} text-xs font-medium border hover:bg-[rgba(10,82,89,0.06)] disabled:opacity-100 disabled:hover:bg-[#EEF7F2] shrink-0 ${FOCUS_RING}`}
          style={{
            background: inCart ? "#EEF7F2" : "transparent",
            color: GREEN,
            borderColor: GREEN,
            transition: TRANSITION_ALL,
          }}
        >
          {inCart ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
          {inCart ? "Added" : "Add"}
        </button>
      </div>
    </div>
  );
}
