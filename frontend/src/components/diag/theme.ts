// ---------------------------------------------------------------------------
// Shared design tokens for the diagnostic/e-pharmacy surface of BalanceAI
// (symptom-checker, pharmacy, medicines catalog, legal pages). Locked palette
// — do not introduce new hex values here without founder sign-off, and never
// use EMERGENCY outside the emergency banner (grep-checked before every ship).
// ---------------------------------------------------------------------------
export const TEAL = "#0E7C86";
export const BLUE = "#1E6FD9";
export const BG = "#F7FAFB";
export const SURFACE = "#FFFFFF";
export const TEXT = "#0B2027";
export const MUTED = "#5B7480";
export const EFFECTIVENESS = "#1FAE7A";
// Darker shade of the same effectiveness green, for use as TEXT on light
// backgrounds only (the base EFFECTIVENESS hex is reserved for fills/badges/
// progress-bars; used as small text on white it fails WCAG AA contrast —
// verified via Lighthouse 2026-09-28). Never used as a background.
export const EFFECTIVENESS_TEXT = "#157A52";
export const EMERGENCY = "#D92D20"; // reserved exclusively for the emergency banner
export const BORDER = "#E4EBEE";
export const HERO_GRADIENT = `linear-gradient(135deg, ${TEAL} 0%, ${BLUE} 100%)`;

// ---------------------------------------------------------------------------
// Secondary accent palette — founder-approved 2026-09-28 to break the
// teal/blue monotony (real 1mg/Netmeds category pages use varied colors for
// category icons/badges, not one single brand color everywhere). These are
// used ONLY as decorative category/badge accents (icon circles, tags) — never
// as the primary brand color, never as a background swap for TEAL/BLUE, and
// never anywhere near the reserved EMERGENCY red. Every hex here is distinct
// from EMERGENCY (#D92D20); re-verify with a grep before ever touching this
// block.
export const ACCENT_PURPLE = "#7C5CBF";
export const ACCENT_CORAL = "#E0475A";
export const ACCENT_AMBER = "#C98A2C";
export const ACCENT_PINK = "#C15B8C";
export const ACCENT_INDIGO = "#5B6EE1";

// Rotation used when a category/list needs a deterministic-but-varied accent
// (e.g. medicine cards colored by category). Order chosen for maximum visual
// separation between neighbours.
export const ACCENT_ROTATION = [
  TEAL,
  ACCENT_CORAL,
  BLUE,
  ACCENT_AMBER,
  EFFECTIVENESS,
  ACCENT_PURPLE,
  ACCENT_PINK,
  ACCENT_INDIGO,
];

export function accentForKey(key: string): string {
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
  }
  return ACCENT_ROTATION[hash % ACCENT_ROTATION.length];
}

// Real, verified counts — counted directly from data/disease_master.json
// (_meta.diseases_researched) and data/medicine_details.json
// (_meta.total_unique_drugs) on 2026-09-28. Never hardcode a different number.
export const DISEASE_COUNT = 323;
export const MEDICINE_COUNT = 3126;
