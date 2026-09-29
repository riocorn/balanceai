# Illustration system (v2 — clinical instrument line art)

**v1 superseded, 2026-09-29.** The first pass on this session (flat filled
"scene" icons — rounded blob people, solid gradient badge circles, thick
rounded-cap limbs) was flagged by the founder as looking like a generic
unDraw/Storyset AI-illustration-kit — the single most common "this is an
AI-generated page" tell in current illustration work. Every illustration
was rebuilt from scratch in the style below. Do not go back to flat filled
mascot/blob-person shapes, ever, on this project.

**What v2 is:** precise, mostly stroke-only technical/clinical-instrument
diagrams — closer to a patent drawing or a medical measurement dial than a
marketing mascot. No cute flat "person" blobs, no big solid gradient badge
circles, no thick rounded-cap cartoon limbs.

**The grammar every file follows:**
- `viewBox="0 0 480 480"` for a full hero illustration; a smaller square
  (`200 200` / `240 240`) for a corner accent or empty-state icon.
- **Stroke, not fill, is the primary language.** Structure is built from
  thin/medium strokes (`stroke-width` 2–2.5 for primary lines, 1.25–1.6 for
  secondary/construction lines at `opacity 0.3–0.55`), `fill="none"`
  everywhere except: small solid node dots at joints (r 2.5–4.5), and the
  one accent-color highlight below.
- **One recurring "instrument dial" device**: a primary ring (`r=100` at
  480-scale) with 12 short rim tick marks every 30°, echoing a real
  measurement gauge — used as the composition's anchor on every full hero
  (symptom-checker, consult-a-doctor, pharmacy). Faint construction circles
  (`opacity 0.14–0.28`, dashed) sit behind it for depth.
- Base stroke color is white on the dark TEAL→BLUE gradient heroes, or
  `TEAL #0A5259` on light `BG #FAF7F1` surfaces (empty states, 404) — match
  whatever the illustration actually sits on, always check before writing
  the file.
- Exactly **one** accent color per illustration, used only as a thin arc
  segment, a small filled node, or a thin outline — never a big shape —
  from the existing secondary palette: `ACCENT_CORAL #E0475A`,
  `EFFECTIVENESS #1FAE7A`, `ACCENT_AMBER #C98A2C`, `ACCENT_PURPLE #7C5CBF`.
- Story beats (a satellite icon off the dial) connect back to the dial with
  a **thin dashed leader line** (`stroke-dasharray="1 5"`, `stroke-width
  1.25–1.4`, `opacity 0.5–0.55`) ending in a small open circle (`r 2.5–2.75`,
  stroke only) — a patent-diagram callout, not a thick dashed arrow.
- Micro-labels: small (`font-size 11`), lowercase, plain sans-serif,
  `opacity 0.6–0.72` — real short words ("flagged", "delivered", "your
  case"), never tracked-out ALL-CAPS, never a boxed pill badge.
- 2–4 small decorative dots (`opacity 0.25–0.3`) in otherwise-empty corners
  only — sparse, not scattered everywhere.
- Hand-code the SVG XML directly, then clean with:
  `inkscape <file> --actions="vacuum-defs;export-plain-svg;export-filename:<file>;export-do"`
  Always render to PNG against the real background color it will sit on and
  actually look at it before wiring it in:
  `inkscape <file> --export-type=png --export-background="<bg-hex>" --export-background-opacity=1 --export-width=480 -o /tmp/check.png`

**Files (all v2 unless noted):**
- `symptom-hero.svg` — a diagnostic dial: a pulse waveform crossing the
  ring, a flagged anomaly node, satellites for "your words" (speech
  outline) and "medicine" (capsule outline).
- `consult-hero.svg` — the dial holds a stethoscope glyph, a green
  "confirmed" arc segment, satellites for "your case" (document outline)
  and "whatsapp review" (chat outline) — honest "beta, self-confirmed"
  micro-label, no face drawn anywhere.
- `pharmacy-hero.svg` — the dial holds a pharmacy cross, an amber
  "verified" arc, satellites for "order" (bag outline) and "delivered"
  (package outline + check).
- `wellness-hero.svg` — a balance scale rendered as a precision instrument
  (thin stand/beam, tick-mark sun) — leaf vs. heart, tied to the product
  name rather than a generic leaf cliché.
- `trust-mark.svg` — a verification-seal dial with a completed green arc +
  checkmark, used to fill the empty gradient field under the "Why people
  trust BalanceAI…" headlines on /symptom-checker and /pharmacy.
- `empty-cart.svg` — line-art open tote + a dashed "ghost" capsule outline,
  TEAL strokes (light BG surface). Cart empty state.
- `medicines-accent.svg` — small corner accent (capsule/tablet outlines),
  white strokes (dark gradient hero). Search stays the real focal point.
- `not-found-pin.svg` — a broken-ring map pin forking (dashed leaders) into
  the page's two real recovery actions. TEAL strokes (light BG surface).
- `symptom-flow.svg` — used in the symptom-checker final CTA band.
  **Still v1/flat style as of this writing — needs the same v2 rebuild.**
  Do not treat it as a reference for new work.
