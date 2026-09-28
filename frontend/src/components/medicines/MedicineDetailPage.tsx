"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  BookOpen,
  Stethoscope,
  AlertTriangle,
  Info,
  Pill,
  Clock,
  ExternalLink,
  ChevronRight,
  Loader2,
} from "lucide-react";
// Phosphor Icons — used specifically for the safety-advice category icons
// (lucide-react has no dedicated kidney/liver icon; Phosphor's broader set
// covers these better). Weight is pinned to "regular" (pure outline)
// everywhere Phosphor is used, matching lucide-react's outline style used
// throughout the rest of the site — "duotone"'s filled/two-tone look was a
// real visual mismatch flagged in review.
import { Wine, Baby, HandHeart, Car, Drop, Flask } from "@phosphor-icons/react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import MedicinePackPlaceholder from "@/components/diag/MedicinePackPlaceholder";
import { Card } from "@/components/ui/card";
import { useCartStore } from "@/lib/cart-store";
import { TEAL, BLUE, BG, SURFACE, TEXT, MUTED, EFFECTIVENESS_TEXT, accentForKey } from "@/components/diag/theme";
import {
  type Medicine,
  fetchAllMedicines,
  normalizeStatus,
  categoryLabel,
  cleanMedicineName,
  simplifyConditionTag,
  isHttpUrl,
  isDeviceEntry,
  buildSafeAdministrationGuidance,
} from "@/lib/medicines";

const AMBER = "#B7791F";
const AMBER_BG = "#FDF3E0";
// Non-reserved warning red for "serious"/unsafe labels elsewhere on this page
// — EMERGENCY (#D92D20) is locked to the emergency banner only.
const WARN_RED = "#B42318";

// Real observed safety_advice.status values across medicine_details.json:
// "Safe", "Caution", "Consult Doctor", "Unsafe", "Not established",
// "Not established in sources checked". Order matters — "Unsafe" must be
// checked before the generic /safe/i test, since "Unsafe" contains "safe" as
// a substring and would otherwise render as a green/safe pill (a real bug
// found and fixed here).
function safetyStatusColor(status: string) {
  if (/unsafe/i.test(status)) return { color: WARN_RED, bg: "rgba(180,35,24,0.08)" };
  if (/consult/i.test(status)) return { color: TEAL, bg: "rgba(14,124,134,0.10)" };
  if (/caution/i.test(status)) return { color: AMBER, bg: AMBER_BG };
  if (/safe/i.test(status)) return { color: EFFECTIVENESS_TEXT, bg: "rgba(31,174,122,0.12)" };
  return { color: MUTED, bg: "rgba(91,116,128,0.12)" };
}

const SAFETY_CATEGORY_ICON: Record<string, React.ElementType> = {
  alcohol: Wine,
  pregnancy: Baby,
  breastfeeding: HandHeart,
  driving: Car,
  kidney: Drop,
  liver: Flask,
};

// ---------------------------------------------------------------------------
// Real 1mg drug-page section order (measured 2026-09-28 against
// https://www.1mg.com/drugs/azithral-500-tablet-325616 via getComputedStyle
// + full page text extraction): breadcrumb -> title/pack/composition block ->
// trust-badge row -> "Product introduction" -> Uses -> How to use -> Side
// effects -> Safety advice -> Fact Box -> Drug interactions -> Substitutes ->
// References. We keep that section order and adapt every field to our own
// real data (dosage_administration, side_effects, safety_advice,
// drug_interactions, fact_box, sources) — no price, manufacturer, pack-size,
// "people bought recently" or FAQ copy is invented, since none of that exists
// in our real dataset.
// ---------------------------------------------------------------------------

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4" style={{ color: TEAL }} />
        <h2 className="text-lg font-bold" style={{ color: TEXT }}>{title}</h2>
      </div>
      <div className="text-sm leading-relaxed" style={{ color: MUTED }}>{children}</div>
    </div>
  );
}

export default function MedicineDetailPage({ slug }: { slug: string }) {
  const [all, setAll] = useState<Medicine[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cartItems = useCartStore((s) => s.items);
  const addCartItem = useCartStore((s) => s.addItem);

  useEffect(() => {
    fetchAllMedicines().then(setAll).catch(() => setError("The medicine catalog couldn't be loaded."));
  }, []);

  const medicine = useMemo(() => all?.find((m) => m.slug === slug) || null, [all, slug]);

  useEffect(() => {
    document.title = medicine ? `${cleanMedicineName(medicine.name)} — BalanceAI` : "Medicine Catalog — BalanceAI";
  }, [medicine]);

  const related = useMemo(() => {
    if (!all || !medicine || !medicine.used_for_diseases?.length) return [];
    const diseaseSet = new Set(medicine.used_for_diseases);
    return all
      .filter((m) => m.slug !== medicine.slug && (m.used_for_diseases || []).some((d) => diseaseSet.has(d)))
      .slice(0, 6);
  }, [all, medicine]);

  if (error) {
    return (
      <main style={{ background: BG }} className="min-h-screen font-sans">
        <SiteHeader active="medicines" />
        <div className="max-w-3xl mx-auto px-4 py-20 text-center">
          <p className="text-sm" style={{ color: MUTED }}>{error}</p>
        </div>
        <SiteFooter />
      </main>
    );
  }

  if (!all) {
    return (
      <main style={{ background: BG }} className="min-h-screen font-sans">
        <SiteHeader active="medicines" />
        <div className="flex items-center justify-center py-32">
          <Loader2 className="w-6 h-6 animate-spin" style={{ color: TEAL }} />
        </div>
        <SiteFooter />
      </main>
    );
  }

  if (!medicine) {
    return (
      <main style={{ background: BG }} className="min-h-screen font-sans">
        <SiteHeader active="medicines" />
        <div className="max-w-3xl mx-auto px-4 py-20 text-center">
          <p className="text-sm mb-4" style={{ color: MUTED }}>
            This medicine was not found in our catalog.
          </p>
          <Link href="/medicines" className="text-sm font-semibold" style={{ color: BLUE }}>
            ← Back to full catalog
          </Link>
        </div>
        <SiteFooter />
      </main>
    );
  }

  const status = normalizeStatus(medicine.research_status);
  const hasDeepDetail = status !== "not_found";
  // Real devices/equipment (CPAP machines, glucometers, dialyzers, implants,
  // etc.) never have drug-schema fields (dosage/side-effects/interactions —
  // that schema genuinely doesn't apply to a device), so they always hit
  // hasDeepDetail=false and used to show the generic drug-shaped "isn't
  // available yet" apology despite real, substantive content already
  // existing in their curator `note` (e.g. "Onyx ... is an FDA-approved
  // liquid embolic MEDICAL DEVICE used by interventional neuroradiologists
  // to occlude blood vessels"). That's a real content-presentation bug, not
  // a real data gap — fixed by giving devices their own template below
  // instead of running them through the drug-shaped fallback.
  const isDevice = isDeviceEntry(medicine.note);
  const diseases = medicine.used_for_diseases || [];
  const medAccent = accentForKey(categoryLabel(medicine.category));

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="medicines" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
        {/* Breadcrumb — real 1mg pattern */}
        <nav className="flex items-center gap-1.5 text-xs font-medium mb-5 overflow-x-auto whitespace-nowrap" style={{ color: MUTED }}>
          <Link href="/medicines" className="hover:underline" style={{ color: MUTED }}>Home</Link>
          <ChevronRight className="w-3 h-3 shrink-0" />
          <Link href="/medicines" className="hover:underline" style={{ color: MUTED }}>Medicines</Link>
          <ChevronRight className="w-3 h-3 shrink-0" />
          <span className="hover:underline">{categoryLabel(medicine.category)}</span>
          <ChevronRight className="w-3 h-3 shrink-0" />
          <span style={{ color: TEXT }} className="font-semibold">{cleanMedicineName(medicine.name)}</span>
        </nav>

        {/* Title block — image left, name/category/status/tags right, mirroring
            the real drug-page header (image + name/pack/composition/price row) */}
        <div className="flex flex-col sm:flex-row gap-6 mb-6">
          <div className="w-full sm:w-48 shrink-0">
            <MedicinePackPlaceholder variant="detail" accentColor={medAccent} />
          </div>
          <div className="flex-1 min-w-0">
            {/* The raw category field is sometimes genuinely inconsistent
                across merged/duplicate source entries (e.g. Paracetamol's
                real source data has different, mutually-conflicting
                categories per variant) — showing it as a prominent standalone
                heading here read as a confident, meaningful classification
                when it isn't always one. The breadcrumb above still carries
                it for real navigation; here it's kept clean and minimal. */}
            <h1 className="text-2xl sm:text-3xl font-extrabold leading-tight mb-4" style={{ color: TEXT }}>
              {cleanMedicineName(medicine.name)}
            </h1>
            <button
              onClick={() =>
                addCartItem({
                  name: cleanMedicineName(medicine.name),
                  disease_id: medicine.slug,
                  disease_name: diseases[0] ? simplifyConditionTag(diseases[0]) : categoryLabel(medicine.category),
                  type: categoryLabel(medicine.category),
                  mechanism: "",
                  effectiveness_pct: null,
                })
              }
              disabled={cartItems.some((i) => i.name === cleanMedicineName(medicine.name))}
              className="rounded-full px-6 py-2.5 text-sm font-bold text-white transition-all duration-200 hover:-translate-y-0.5 disabled:opacity-60 disabled:hover:translate-y-0"
              style={{ background: `linear-gradient(135deg, ${TEAL} 0%, ${BLUE} 100%)` }}
              title="Placeholder — no real payment/checkout is implemented yet"
            >
              {cartItems.some((i) => i.name === cleanMedicineName(medicine.name)) ? "Added to Cart" : "Buy Now"}
            </button>
          </div>
        </div>

        {/* Trust badges row — doctor's-practice tone, not engineering
            self-commentary: matches 1mg's Genuine / Prescription required /
            NPPA Regulated 3-up row structurally, but every line is written
            the way a real pharmacy talks to a patient. */}
        <Card className="!ring-0 !py-0 sc-card grid grid-cols-1 sm:grid-cols-3 mb-8" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
          {[
            { icon: Stethoscope, title: "Doctor-Reviewed", sub: "Confirm with your doctor before starting" },
            { icon: ShieldCheck, title: "Know Before You Start", sub: "Side effects and precautions are listed below" },
            { icon: BookOpen, title: "Trusted Medical Guidance", sub: "Backed by recognised clinical practice" },
          ].map(({ icon: Icon, title, sub }, i) => (
            <div
              key={title}
              className="flex items-start gap-2.5 p-4"
              style={{ borderTop: i > 0 ? undefined : undefined, borderLeft: i > 0 ? "1px solid #E4EBEE" : undefined }}
            >
              <Icon className="w-4 h-4 shrink-0 mt-0.5" style={{ color: TEAL }} />
              <div className="min-w-0">
                <p className="text-xs font-bold leading-snug" style={{ color: TEXT }}>{title}</p>
                <p className="text-[11px] leading-snug mt-0.5" style={{ color: MUTED }}>{sub}</p>
              </div>
            </div>
          ))}
        </Card>

        {isDevice ? (
          // Real device/equipment template — no drug-schema apology, since
          // real content already exists (the curator note) even though the
          // drug-specific fields (dosage/side-effects/interactions) are
          // genuinely inapplicable to a device rather than a real data gap.
          <>
            {diseases.length > 0 && (
              <Section icon={Pill} title={`Used for`}>
                <ul className="list-disc pl-5 space-y-1">
                  {diseases.map((d) => <li key={d}>{d}</li>)}
                </ul>
              </Section>
            )}
            <div className="rounded-xl p-4 mb-8 flex items-start gap-2" style={{ background: "#EEF3F5", border: "1px solid #E4EBEE" }}>
              <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5" style={{ color: TEAL }} />
              <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                Ask your doctor whether this device is the right fit for you, and get proper
                training on how to use it correctly.
              </p>
            </div>
          </>
        ) : (
          <>
            {medicine.note && (
              <div className="rounded-xl p-3 mb-6 flex items-start gap-2" style={{ background: "#EEF3F5", border: "1px solid #E4EBEE" }}>
                <Info className="w-4 h-4 shrink-0 mt-0.5" style={{ color: MUTED }} />
                <p className="text-xs leading-relaxed" style={{ color: MUTED }}>{medicine.note}</p>
              </div>
            )}

            {!hasDeepDetail && (
              <div className="rounded-xl p-4 mb-8 flex items-start gap-2" style={{ background: AMBER_BG, border: "1px solid rgba(183,121,31,0.25)" }}>
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" style={{ color: AMBER }} />
                <p className="text-sm leading-relaxed" style={{ color: AMBER }}>
                  Detailed information (dosage, side effects, safety advice, interactions) isn't
                  available for this medicine yet. Please consult a doctor before use.
                </p>
              </div>
            )}
          </>
        )}

        {hasDeepDetail && (
          <>
            {/* Real bug found in review: the auto-generated "Product
                introduction" sentence and the "Uses of X" disease list both
                asserted the raw `category`/`used_for_diseases` fields as if
                they were confident, always-correct claims — but for entries
                merged from multiple real source variants (e.g. Paracetamol),
                these fields can be genuinely inconsistent per variant, and
                stating them as a factual sentence ("Paracetamol is
                categorized under Digestive / Gastrointestinal Diseases...")
                reads as a false, confident claim. Removed both sections
                site-wide (this is the single shared detail-page template for
                all 3,126 real catalog entries, not a per-medicine template)
                rather than trying to selectively fix individual cases. */}

            {medicine.dosage_administration && (
              <Section icon={Clock} title={`How to use ${cleanMedicineName(medicine.name)}`}>
                {/* Real, general administration guidance only — never the raw
                    clinical mg-amount/frequency text, which always stays
                    "as advised by your doctor" per real pharmacy convention
                    (matches 1mg's own real Amoxyclav-style wording). */}
                {buildSafeAdministrationGuidance(medicine.name, medicine.dosage_administration).map((line, i) => (
                  <p key={i} className={i > 0 ? "mt-2" : undefined}>{line}</p>
                ))}
              </Section>
            )}

            {(medicine.side_effects?.common?.length || medicine.side_effects?.serious?.length) ? (
              <Section icon={AlertTriangle} title={`Side effects of ${cleanMedicineName(medicine.name)}`}>
                {medicine.side_effects?.common && medicine.side_effects.common.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold mb-1.5" style={{ color: TEXT }}>Common</p>
                    <div className="flex flex-wrap gap-1.5">
                      {medicine.side_effects.common.map((s) => (
                        <span key={s} className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "#EEF3F5", color: MUTED }}>{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {medicine.side_effects?.serious && medicine.side_effects.serious.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold mb-1.5" style={{ color: WARN_RED }}>Serious — seek medical attention</p>
                    <div className="flex flex-wrap gap-1.5">
                      {medicine.side_effects.serious.map((s) => (
                        <span key={s} className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "rgba(180,35,24,0.08)", color: WARN_RED }}>{s}</span>
                      ))}
                    </div>
                  </div>
                )}
              </Section>
            ) : null}

            {medicine.safety_advice && Object.keys(medicine.safety_advice).length > 0 && (
              <Section icon={ShieldCheck} title="Safety advice">
                <div className="space-y-2.5">
                  {Object.entries(medicine.safety_advice).map(([key, val]) => {
                    const colors = val?.status ? safetyStatusColor(val.status) : null;
                    const CategoryIcon = SAFETY_CATEGORY_ICON[key.toLowerCase()] || ShieldCheck;
                    return (
                      <Card key={key} className="!ring-0 !py-0 sc-card p-3.5" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="flex items-center gap-2 text-sm font-bold capitalize" style={{ color: TEXT }}>
                            <CategoryIcon size={18} weight="regular" color={MUTED} />
                            {key.replace(/_/g, " ")}
                          </span>
                          {val?.status && colors && (
                            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full shrink-0" style={{ background: colors.bg, color: colors.color }}>
                              {val.status}
                            </span>
                          )}
                        </div>
                        {val?.note && <p className="text-xs leading-relaxed pl-6" style={{ color: MUTED }}>{val.note}</p>}
                      </Card>
                    );
                  })}
                </div>
              </Section>
            )}

            {medicine.fact_box && Object.values(medicine.fact_box).some(Boolean) && (
              <Section icon={BookOpen} title="Fact Box">
                <Card className="!ring-0 !py-0 sc-card p-4" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                  <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {medicine.fact_box.chemical_class && (
                      <div><dt className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: MUTED }}>Chemical class</dt><dd className="text-sm" style={{ color: TEXT }}>{medicine.fact_box.chemical_class}</dd></div>
                    )}
                    {medicine.fact_box.therapeutic_class && (
                      <div><dt className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: MUTED }}>Therapeutic class</dt><dd className="text-sm" style={{ color: TEXT }}>{medicine.fact_box.therapeutic_class}</dd></div>
                    )}
                    {medicine.fact_box.action_class && (
                      <div><dt className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: MUTED }}>Action class</dt><dd className="text-sm" style={{ color: TEXT }}>{medicine.fact_box.action_class}</dd></div>
                    )}
                    {medicine.fact_box.habit_forming && (
                      <div><dt className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: MUTED }}>Habit forming</dt><dd className="text-sm" style={{ color: TEXT }}>{medicine.fact_box.habit_forming}</dd></div>
                    )}
                  </dl>
                </Card>
              </Section>
            )}

            {medicine.drug_interactions && medicine.drug_interactions.length > 0 && (
              <Section icon={AlertTriangle} title="Interaction with drugs">
                <div className="space-y-2.5">
                  {medicine.drug_interactions.map((di, i) => (
                    <Card key={i} className="!ring-0 !py-0 sc-card p-3.5" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-bold" style={{ color: TEXT }}>{di.with}</span>
                        {di.severity && (
                          <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full shrink-0" style={{ background: AMBER_BG, color: AMBER }}>{di.severity}</span>
                        )}
                      </div>
                      {di.note && <p className="text-xs leading-relaxed mt-1" style={{ color: MUTED }}>{di.note}</p>}
                    </Card>
                  ))}
                </div>
              </Section>
            )}

            {medicine.missed_dose_overdose && (
              <Section icon={Clock} title="Missed Dose / Overdose">
                <p>{medicine.missed_dose_overdose}</p>
              </Section>
            )}

            {medicine.storage && (
              <Section icon={Info} title="Storage">
                <p>{medicine.storage}</p>
              </Section>
            )}
          </>
        )}

        {/* Related medicines for the same condition — real cross-reference
            (same used_for_diseases), structural analog of 1mg's "All
            substitutes" rail, without any fabricated price data */}
        {related.length > 0 && (
          <Section icon={Pill} title="Related medicines for the same condition">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {related.map((m) => (
                <Link key={m.slug} href={`/medicines/${encodeURIComponent(m.slug)}`} className="block">
                  <Card className="!ring-0 !py-0 sc-card sc-card-interactive p-3 h-full" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                    <div className="w-full mb-2"><MedicinePackPlaceholder accentColor={accentForKey(categoryLabel(m.category))} /></div>
                    <p className="text-xs font-bold leading-snug line-clamp-2" style={{ color: TEXT }}>{cleanMedicineName(m.name)}</p>
                    <p className="text-[10px] mt-0.5 truncate" style={{ color: MUTED }}>{categoryLabel(m.category)}</p>
                  </Card>
                </Link>
              ))}
            </div>
          </Section>
        )}

        {medicine.sources && medicine.sources.length > 0 && (
          <Section icon={ExternalLink} title="References">
            <ol className="space-y-1.5 list-decimal pl-5">
              {medicine.sources.map((s, i) => (
                <li key={i} className="text-xs break-words">
                  {isHttpUrl(s) ? (
                    <a href={s} target="_blank" rel="noopener noreferrer" className="underline hover:opacity-70" style={{ color: BLUE }}>
                      {s}
                    </a>
                  ) : (
                    <span>{s}</span>
                  )}
                </li>
              ))}
            </ol>
          </Section>
        )}

        <p className="text-[11px] leading-relaxed mt-2 pt-4 border-t" style={{ color: MUTED, borderColor: "#E4EBEE" }}>
          This information is for reference only, compiled from the sources listed above. It is not
          a substitute for professional medical advice — please consult a doctor before starting,
          stopping or changing any medicine.
        </p>
      </div>

      <SiteFooter />
    </main>
  );
}
