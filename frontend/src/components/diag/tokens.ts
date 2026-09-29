import type { CSSProperties } from "react";

// Shared component tokens — buttons, inputs, cards, motion. Redesign,
// 2026-09-29: pulled from live computed-CSS research on Stripe, Linear,
// Vercel, Ramp and Maven Clinic. The finding driving this file: component
// INCONSISTENCY across pages (one page's button radius/shadow/height
// disagreeing with another's) reads as more "cheap/template" than any one
// component being merely plain — so every button/input/card on the diag
// surface (symptom-checker, pharmacy, cart/checkout/results,
// consult-a-doctor, medicines, wellness) should pull from here rather than
// re-declaring its own radius/shadow ad hoc.
//
// Rules encoded here:
// - Real CTA buttons are never full pills (rounded-full) — that shape is
//   reserved for status badges/chips/nav tags. CTA_RADIUS matches how
//   Stripe/Linear/Vercel actually round their buttons (6-8px).
// - Static content cards (a medicine result, a product card) lean on a
//   hairline border, not a drop shadow — "white rounded rectangle floating
//   on gray with shadow-lg" is the single most common cheap-SaaS-template
//   tell. The one shadow token here is reserved for things that actually
//   float: dropdown menus, modals, a hovered interactive card.
// - One easing curve, one duration band, everywhere motion is used.
export const CTA_RADIUS = "rounded-lg"; // ~8px — real button radius, not a pill
export const INPUT_RADIUS = "rounded-lg"; // ~8-10px
export const CARD_RADIUS = "rounded-xl"; // ~12px — one step up from buttons, same family
export const BADGE_RADIUS = "rounded-full"; // pills stay reserved for badges/chips/tags

export const CARD_BORDER = "1px solid rgba(11,32,39,0.08)";
// Reserved for genuinely elevated/floating elements only (dropdowns,
// modals, a hovered card) — never a static content card at rest.
export const ELEVATED_SHADOW = "0 1px 2px rgba(11,32,39,0.04), 0 4px 12px rgba(11,32,39,0.08)";

export const EASE = "cubic-bezier(0.45,0.05,0.55,0.95)";
export const TRANSITION = `background-color 220ms ${EASE}, border-color 220ms ${EASE}, color 220ms ${EASE}`;
export const TRANSITION_STYLE: CSSProperties = { transition: TRANSITION };

// CTA button base classes — fill (primary) or outline (secondary) at the
// same size, per the researched spec (primary vs secondary is fill vs
// outline, never a size difference; weight 400-500, never bold; a real
// rectangular radius, never a pill; near-zero or no shadow).
export const CTA_BASE =
  "inline-flex items-center justify-center gap-2 h-11 px-6 text-sm font-medium";
export const CTA_HERO_BASE =
  "inline-flex items-center justify-center gap-2 h-12 px-8 text-[15px] font-medium";
