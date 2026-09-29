import Link from "next/link";
import { CATEGORY_TILES } from "./categories";
import { TEXT, SURFACE, BORDER } from "./theme";

// Single restrained category-rail treatment, shared by every page that shows
// the 7 health-area tiles (symptom-checker, pharmacy). Replaces the earlier
// per-page pattern of a stock Unsplash photo tinted behind each icon — the
// circle is now one uniform surface/border block, and the tile's accent
// color differentiates it only through the icon itself. This is the
// "unified background block, icons do the differentiation" treatment named
// in the founder's redesign brief, not the "monochrome + accent-on-hover"
// alternative, since these tiles are colour-coded consistently elsewhere on
// the site (header dots, medicine-card accents) and keeping that mapping
// visible here (in the icon) preserves that meaning.
export default function CategoryRail({
  onSelect,
  linkToMedicines = false,
  disabled = false,
}: {
  onSelect?: (starter: string) => void;
  linkToMedicines?: boolean;
  disabled?: boolean;
}) {
  return (
    <div
      className="flex sm:grid sm:grid-cols-7 gap-4 sm:gap-3 overflow-x-auto sm:overflow-visible pb-2 sm:pb-0 -mx-1 px-1 [&::-webkit-scrollbar]:hidden"
      style={{ scrollbarWidth: "none" }}
    >
      {CATEGORY_TILES.map(({ icon: Icon, label, accent, starter, medicinesQuery }) => {
        const content = (
          <>
            <div
              className="w-14 h-14 sm:w-16 sm:h-16 rounded-full flex items-center justify-center shrink-0 transition-all duration-200 group-hover:-translate-y-1"
              style={{ background: SURFACE, border: `1.5px solid ${BORDER}` }}
            >
              <Icon className="w-6 h-6 sm:w-7 sm:h-7" style={{ color: accent }} strokeWidth={1.75} />
            </div>
            <span className="text-[11px] sm:text-xs font-semibold text-center leading-tight" style={{ color: TEXT }}>
              {label}
            </span>
          </>
        );
        const className = "group flex flex-col items-center gap-2.5 shrink-0 w-20 sm:w-auto transition-transform disabled:opacity-40";
        return linkToMedicines ? (
          <Link key={label} href={`/medicines?q=${encodeURIComponent(medicinesQuery)}`} className={className}>
            {content}
          </Link>
        ) : (
          <button key={label} type="button" disabled={disabled} onClick={() => onSelect?.(starter)} className={className}>
            {content}
          </button>
        );
      })}
    </div>
  );
}
