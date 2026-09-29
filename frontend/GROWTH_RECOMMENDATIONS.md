# Growth & conversion recommendations

Prioritized by real, honest impact for this specific product (AI symptom
checker → doctor review on WhatsApp → medicine purchase, India-focused).
Every item here is compatible with the site's existing honesty commitments
("Doctor Review Required (Beta)", self-confirmed not independently verified,
"No Pressure", no fake doctor depicted). Items marked **[declined]** are
classic growth tactics that would require breaking those commitments —
documented so the founder can see what was consciously left out, not quietly
softened.

## Implemented this pass

1. **Per-route SEO metadata.** Every route previously shared one identical
   `<title>`/description from the root layout — pharmacy, wellness, medicines
   and consult-a-doctor all showed the exact same search-result and
   social-share preview. Added a small server-side `layout.tsx` per major
   route (`symptom-checker`, `pharmacy`, `consult-a-doctor`, `wellness`,
   `medicines`) exporting real, accurate `Metadata` — doesn't touch the
   "use client" page components at all. This directly affects organic
   click-through rate, which is a real, honest, high-leverage growth lever
   for a product living on search intent ("migraine treatment India" etc.).
2. **`sitemap.xml`** (`src/app/sitemap.ts`) — the public routes (home,
   symptom-checker, pharmacy, consult-a-doctor, wellness, medicines,
   by-category, legal pages) now have a real sitemap for crawlers. Was
   completely missing before.
3. **`robots.txt` fixed**, not replaced — a real one already existed
   (referencing `https://balanceai.app/sitemap.xml`, so that's the intended
   production domain) but only disallowed `/api/`. Added explicit disallows
   for account-only routes (`/dashboard`, `/profile`, `/history`,
   `/food-history`, `/pharmacy/cart`, `/pharmacy/checkout`) that have zero
   unique public content and shouldn't compete for crawl budget or show up
   in search results with a stranger's session state.
4. **PWA manifest fixed** (`public/manifest.json`) — it still described the
   site as "BalanceAI — Nutrition Deficiency Detector... 25 nutrient
   deficiencies detected... No blood test", a real, live description of a
   *different, earlier* product line, with dark near-black theme colors left
   over from that build too. Anyone who "installs" the app today from
   `/symptom-checker` or `/pharmacy` would see the wrong name and wrong
   description on their home screen. Updated the name/description to
   honestly cover both real product lines this domain now serves, and the
   theme/background colors to match the live GREEN/CREAM brand. Also added
   real shortcuts for "Find Treatment" and "Order Medicine" (the manifest
   only had nutrition-analysis shortcuts before) — install-to-home-screen
   is a real, free retention lever this was actively working against.

## Recommended, not yet implemented (founder should review before shipping)

5. **Real custom domain.** The site is currently only reachable at
   `*.vercel.app` preview/alias URLs. A `.vercel.app` domain reads as
   noticeably less trustworthy for a medical product than `balanceai.app`
   (which `robots.txt` already references as if it's intended) — this is
   likely the single highest-leverage trust/conversion fix available, but
   registering and wiring a domain is a real infra/business decision, not
   something to do unilaterally in this pass.
6. **A real "why trust us with your data" page**, linked from the footer
   near the existing privacy/medical-disclaimer links — the site already
   makes strong honesty claims about the doctor-review step; a short, plain
   explanation of what happens to a user's symptom description and cart
   data (stored where, shared with whom, for how long) is the kind of real
   trust signal that measurably lifts checkout completion on health
   products, and it's just documentation — no new claims to fabricate.
7. **Reduce symptom-checker → cart friction.** Worth a real UX/funnel
   analysis (not implemented here, since it touches the interaction layer
   another process owns this session): how many steps/screens between
   "matched to a medicine" and "in cart"? Every real screen removed there is
   a real conversion lift on health-intent traffic that's often impatient.
8. **Real return-visit mechanism for the medicine side.** `src/app/history`
   already exists and is fully real — but it's wired to the *nutrition*
   product's `getAllAnalyses()`/`db.ts`, not to symptom-checker searches or
   past orders. A genuine "your past symptom checks" or "reorder your last
   medicine" surface (using data that's already being captured, not new
   tracking) is a real, honest retention lever — but it's a real feature
   build, not a copy/CSS change, so left as a recommendation.
9. **Structured data (JSON-LD).** A `MedicalWebPage`/`Product` schema on
   `/medicines/[slug]` pages would make individual medicine pages eligible
   for richer Google results (price, availability). Real, honest, standard
   SEO — not implemented this pass since it needs to be threaded through the
   dynamic route's real data fetch, which is riskier to touch blind.
10. **Cross-sell after a symptom match.** Checked `symptom-checker/page.tsx`
    and `results` — there's no real "you might also need" surfacing of
    relevant wellness products after a match today. A genuine, clearly-
    labeled "commonly paired with your treatment" surfacing from the real
    wellness catalog (not an upsell dark pattern — opt-in, no pre-added
    items, no pressure copy) could be a real revenue lever, but needs real
    product-pairing logic behind it, not just a UI change.

## Declined — would require breaking this site's honesty commitments

- **[declined]** Countdown timers / "offer ends in X hours" — there is no
  real time-limited offer on this product; a fake one is a classic dark
  pattern.
- **[declined]** "X people are viewing this / bought this today" — no real
  live-viewer or purchase-count data is being tracked to back this claim
  honestly.
- **[declined]** Inflating "Trusted by N users" or review counts beyond what
  `_meta` in the real data actually verifies — this session has already
  enforced elsewhere that every stat on this site traces to a real, checked
  source (`DISEASE_COUNT`, `MEDICINE_COUNT` etc. in `theme.ts` are explicit
  about this). Any new stat should follow the same rule.
- **[declined]** Pre-ticked add-ons/insurance/"recommended" upsells at
  checkout, or making the doctor-review step *feel* skippable/optional in
  copy to reduce friction — the whole product's credibility rests on that
  step being real and mandatory; softening it for a conversion bump would
  directly contradict the founder's own repeated instructions this session.
- **[declined]** Exaggerating what "beta" doctor review actually verifies
  (e.g. copy implying a licensed doctor has personally reviewed every case
  today) — stays exactly as accurately hedged as it already is.
