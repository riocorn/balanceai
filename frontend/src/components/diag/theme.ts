// ---------------------------------------------------------------------------
// Shared design tokens for the diagnostic/e-pharmacy surface of BalanceAI
// (symptom-checker, pharmacy, medicines catalog, legal pages). Locked palette
// — do not introduce new hex values here without founder sign-off, and never
// use EMERGENCY outside the emergency banner (grep-checked before every ship).
//
// Founder directive, 2026-09-29 (live instruction): unify the diag surface's
// palette with the root landing page's (src/app/page.tsx) established
// GREEN/CREAM system instead of the earlier standalone teal/blue system, so
// the whole site — landing page, symptom-checker, pharmacy, consult-a-doctor,
// wellness, medicines, cart/checkout, 404 — reads as one frontend. Token
// NAMES are unchanged (every page/component already imports TEAL/BLUE/BG/etc
// by name), only the hex VALUES change, so this one file re-skins the entire
// diag surface without touching each page individually. TEAL now equals the
// landing page's GREEN (#1d5c3d); BLUE is repurposed as a secondary, lighter
// green (matching the landing page's #2d7a58 icon-box border tone) rather
// than an unrelated blue; BG matches the landing page's CREAM_BG (#f5ede0);
// TEXT/MUTED match the landing page's TEXT/SUB. Contrast re-checked against
// every new value below.
// ---------------------------------------------------------------------------
export const TEAL = "#1D5C3D";
export const BLUE = "#2D7A58";
export const BG = "#F5EDE0";
export const SURFACE = "#FFFFFF";
export const TEXT = "#1A1A1A";
export const MUTED = "#3D5249";
export const EFFECTIVENESS = "#2F9E5B";
// Darker shade of the same effectiveness green, for use as TEXT on light
// backgrounds only (the base EFFECTIVENESS hex is reserved for fills/badges/
// progress-bars; used as small text on white it fails WCAG AA contrast —
// verified via Lighthouse 2026-09-28). Never used as a background.
export const EFFECTIVENESS_TEXT = "#1F6B3E";
export const EMERGENCY = "#D92D20"; // reserved exclusively for the emergency banner
export const BORDER = "#E4E7E2";
export const HERO_GRADIENT = `linear-gradient(135deg, ${TEAL} 0%, ${TEAL} 58%, ${BLUE} 100%)`;

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
