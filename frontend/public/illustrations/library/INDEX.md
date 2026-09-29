# Illustration library — 20 premium colorful medical pieces

Reusable asset library, hand-coded SVG (no stock photos, no AI-image
generation), cleaned via Inkscape CLI, each PNG-rendered and visually
checked against its intended background before being marked done. Not
wired into any page yet — selection/placement is a separate step.

Style: colored clinical/textbook line art (not flat cartoon-mascot fills),
following the same instrument-precision conventions as the rest of
`../` (dashed leader-line callouts with lowercase micro-labels, faint
dashed construction circle behind each composition), but with a real,
deliberate color per subject instead of white + one accent.

## Anatomy (viewBox 280×260, light background e.g. #F5EDE0)
- `heart-anatomy.svg` — crimson #C23B3B, four-chamber silhouette + aorta arc, labelled "aorta" / "left ventricle".
- `lungs-anatomy.svg` — dusty rose #C97A8A, two lobes + trachea/bronchi branching, labelled "bronchi".
- `stomach-digestive.svg` — warm amber #C9822C, stomach pouch + esophagus + intestine coil, labelled "stomach" / "intestine".
- `brain-anatomy.svg` — lavender #7C5CBF, lobed outline with sulci lines + brainstem, labelled "cortex" / "brainstem".
- `kidney-anatomy.svg` — maroon #8C3550, bean shape + renal pelvis + ureter, labelled "renal pelvis" / "ureter".
- `joint-knee.svg` — slate blue #4A6FA5, femur/tibia + patella + cartilage gap, labelled "patella" / "cartilage".

## Nutrients (viewBox 160×160, light background)
- `iron.svg` — rust brown #A54A2E, horseshoe-magnet form + molecule dots.
- `vitamin-d.svg` — golden amber #C98A2C, sun-ray badge with a "D" mark.
- `vitamin-b12.svg` — magenta #B0407A, hexagonal cobalt-ring molecule shape.
- `calcium.svg` — mineral grey #6E7A82, bone cross-section silhouette.
- `zinc.svg` — slate blue-grey #5B7A93, hexagon shield with a "Zn" bolt mark.
- `protein.svg` — olive #8A7A2E, linked amino-acid chain of ellipses.

## Equipment / process (viewBox 160×160)
- `stethoscope-color.svg` — brand green #1D5C3D, colorized refinement of consult-hero.svg's stethoscope language.
- `whatsapp-review.svg` — WhatsApp green #25D366, chat bubble + confirmed checkmark badge.
- `capsule-dissolution.svg` — coral #E0475A, half-filled capsule with dissolving dot trail.
- `vitals-pulse.svg` — coral #E0475A, pulse waveform + thermometer.

## Category icons (viewBox 160×160) — real categories from `CATEGORY_TILES` in `src/components/diag/categories.ts`, using each tile's own existing accent
- `category-heart-disease.svg` — ACCENT_CORAL #E0475A, heart outline + pulse trace.
- `category-joint-pain.svg` — ACCENT_AMBER #C98A2C, two bones meeting at an inflamed joint.
- `category-womens-health.svg` — ACCENT_PINK #C15B8C, real female-symbol form.
- `category-migraine.svg` — ACCENT_INDIGO #5B6EE1, head silhouette with pain rays + a confirmed check.

Total: 20 files, ~80KB combined.
