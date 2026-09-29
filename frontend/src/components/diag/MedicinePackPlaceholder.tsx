import { Pill } from "lucide-react";
import { TEAL } from "./theme";

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// Generic pack-shot placeholder — occupies exactly the position/aspect-ratio
// real 1mg product photography sits in (square image slot: full-width top of
// a catalog card, or a fixed square block beside the title on a drug detail
// page) so it is a drop-in slot for real photography later. Deliberately NOT
// a fake photo — a flat tinted illustration, so nobody mistakes it for a real
// product image. No caption text — a clean visual only, nothing that reads
// as internal/dev-status commentary to the customer.
//
// `accentColor` (from the approved secondary palette, usually chosen via
// accentForKey(category)) tints the placeholder per medicine category, so a
// catalog grid reads with real color variety instead of one repeated brand
// tint everywhere — mirrors how real 1mg/Netmeds category tiles vary color.
export default function MedicinePackPlaceholder({
  variant = "card",
  className = "",
  accentColor = TEAL,
}: {
  variant?: "card" | "detail";
  className?: string;
  accentColor?: string;
}) {
  const iconSize = variant === "detail" ? "w-16 h-16" : "w-9 h-9";
  return (
    <div
      className={`relative w-full aspect-square rounded-xl flex items-center justify-center overflow-hidden ${className}`}
      style={{
        background: `linear-gradient(155deg, ${hexToRgba(accentColor, 0.14)} 0%, ${hexToRgba(accentColor, 0.05)} 100%)`,
        border: "1px solid #E4E7E2",
      }}
      aria-hidden="true"
    >
      <div
        className="absolute inset-0 opacity-[0.5] pointer-events-none"
        style={{ backgroundImage: `radial-gradient(circle, ${hexToRgba(accentColor, 0.14)} 1px, transparent 1px)`, backgroundSize: "14px 14px" }}
      />
      <Pill className={`relative ${iconSize}`} style={{ color: accentColor }} strokeWidth={1.5} />
    </div>
  );
}
