# Illustration system

One consistent style, established by `symptom-flow.svg` (the first piece
built this session) and extended to every hero illustration added after it.
Read this before adding another illustration to the site.

**What it is:** flat geometric "scene" icons — no photography, no stock
imagery, no AI-generated art. Built from circles, rounded rectangles and
rounded-cap stroke paths only, hand-authored as SVG then cleaned with
`inkscape <file> --actions="vacuum-defs;export-plain-svg;export-filename:<file>;export-do"`.

**The grammar every file follows:**
- `viewBox="0 0 480 480"` — one square canvas size, so any illustration
  drops into a hero's right-hand column at the same scale.
- One `badgeGradient` (`#0E7C86` → `#1E6FD9`, i.e. `TEAL`→`BLUE` from
  `theme.ts`) marking the "verified/trusted" moment of each scene — the
  doctor-review badge on `symptom-flow.svg`, the pharmacy-verified badge on
  `pharmacy-hero.svg`, etc. It's the one recurring visual anchor that ties
  every illustration back to the same brand mark.
- Base shapes are white (`#ffffff`) or the two brand hues (TEAL/BLUE).
  Exactly **one** accent color from the approved secondary palette
  (`ACCENT_CORAL #E0475A`, `EFFECTIVENESS #1FAE7A`, `ACCENT_AMBER #C98A2C`,
  `ACCENT_PURPLE #7C5CBF`) is allowed per illustration, used for a single
  highlighted detail (a pill, a leaf, a heart) — never as a second base
  color competing with white/teal/blue.
- Story beats are linked with dashed connector paths
  (`stroke-dasharray="2 9"`, `stroke-width="3"`, white, `opacity="0.85"`),
  never solid arrows or lucide `ArrowRight` icons.
- 4–6 small white dots at `opacity 0.3–0.35` scattered for texture, same
  as the decorative dots already in `symptom-flow.svg`.
- No literal photographic detail (no faces, no real doctor depicted) — every
  "person" is the same reusable head-circle + rounded-rect-torso figure, and
  every "doctor" is represented abstractly through a medical glyph inside the
  badge (stethoscope, pulse line), consistent with the site's honest
  "beta, not a real onboarded doctor yet" positioning.

**Files:**
- `symptom-flow.svg` — speak → AI+doctor review (pulse badge) → medicine.
  Used in the symptom-checker final CTA band.
- `symptom-hero.svg` — same story, mic + soundwave instead of phone, sized
  for the top hero's right column (kept distinct from the CTA piece above it
  on the same page so the two don't read as a literal duplicate).
- `pharmacy-hero.svg` — order → pharmacy-verified badge (cross) → delivered
  package (checkmark). Pharmacy/fulfillment story, not the symptom-matching
  story, so it earns its own page.
- `consult-hero.svg` — patient (chat dots) → consult screen framing a
  stethoscope badge. No face is drawn anywhere — the "doctor" is the
  stethoscope glyph only, on purpose.
- `wellness-hero.svg` — a balance scale (leaf vs. heart), a deliberate nod to
  the product name rather than a generic leaf/plant wellness cliché.
- `medicines-accent.svg` — small corner accent (overlapping capsules), scaled
  down, for the medicines catalog hero, which keeps its search bar as the
  primary focal element.
