"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Loader2, Pill, Sparkles, HeartPulse, Baby, Heart } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import MedicinePackPlaceholder from "@/components/diag/MedicinePackPlaceholder";
import ScrollReveal from "@/components/diag/ScrollReveal";
import { Card } from "@/components/ui/card";
import {
  TEAL,
  BG,
  SURFACE,
  TEXT,
  MUTED,
  HERO_GRADIENT,
  ACCENT_CORAL,
  ACCENT_INDIGO,
  ACCENT_PURPLE,
  ACCENT_AMBER,
} from "@/components/diag/theme";
import {
  type Medicine,
  fetchAllMedicines,
  categoryLabel,
  cleanMedicineName,
} from "@/lib/medicines";

const PER_GROUP = 6;

// Real wellness sections, built only from what genuinely exists in
// data/medicine_details.json — verified by direct inspection on 2026-09-28,
// re-verified again after the founder's confirmed 5-section structure
// (Sexual Wellness / Vitamins & Supplements / Personal Care / Women's
// Health / Mom & Baby Care). Matching uses word-boundary-safe regexes
// throughout, learned from a real bug caught in the previous pass: plain
// substring matching on "omega" false-positive matched "acromegaly" (an
// unrelated pituitary condition), surfacing acromegaly drugs mislabeled as
// omega-3 supplements. EXCLUDE_PATTERN strips out a handful of other
// confirmed-wrong substring matches found this pass — e.g. "Soap and
// running water" (a rabies wound-care instruction, matched via "soap", not
// a personal-care product), "SOAP II protocol" (a dopamine-dosing acronym),
// "a lubricating eye ointment ... moisture chamber" (a Bell's Palsy
// treatment description, matched via "moisture") — plus the iron-chelator /
// calcium-channel-blocker / zinc-shampoo false positives already found
// before. This is a structural first pass, not exhaustive curation: real,
// verified counts as of this pass — Vitamins & Supplements 57 (vitamins,
// calcium, iron, omega-3 and zinc items merged into one umbrella), Women's
// Health 27, Mom & Baby Care 24, Personal Care 13, Sexual Wellness 5 (the
// real data for this section is genuinely thin — mostly combined oral
// contraceptives — and is reported as such rather than padded).
const EXCLUDE_PATTERN = /defer|chelat|non-iron-deficient|polystyrene sulfonate|dobesilate|pyrithione|channel blocker|soap and running water|soap ii protocol|lubricating eye ointment|moisture chamber|pcos-specific metabolic screening frequency/i;

const WELLNESS_GROUPS: { anchorId: string; label: string; blurb: string; query: RegExp; searchLinkQuery: string; icon: typeof Pill; accent: string }[] = [
  {
    anchorId: "sexual-wellness",
    label: "Sexual Wellness",
    blurb: "Real contraception and sexual-health items from our catalog.",
    query: /\berectile\b|\bcontracept|\bcondom\b|\bsexual\b|\blibido\b|\bejaculat/i,
    searchLinkQuery: "contraceptive",
    icon: Heart,
    accent: ACCENT_CORAL,
  },
  {
    anchorId: "vitamins-supplements",
    label: "Vitamins & Supplements",
    blurb: "Real vitamins, minerals and supplements from our catalog — vitamins, calcium, iron, omega-3 and zinc items — for genuine, doctor-recognised deficiencies.",
    query: /\bvitamin|\bcalcium|\biron\b|\bomega-?3\b|\bfish oil\b|\bzinc\b/i,
    searchLinkQuery: "vitamin",
    icon: Pill,
    accent: TEAL,
  },
  {
    anchorId: "personal-care",
    label: "Personal Care",
    blurb: "Real topical and hygiene-related treatments from our catalog — medicated shampoos, lotions and sun protection.",
    query: /\bshampoo\b|\bsoap\b|\blotion\b|\bsunscreen\b|\btoothpaste\b|\bmouthwash\b|\bdeodorant\b|\bmoistur/i,
    searchLinkQuery: "lotion",
    icon: Sparkles,
    accent: ACCENT_AMBER,
  },
  {
    anchorId: "womens-health",
    label: "Women's Health",
    blurb: "Real treatments for PCOS, menopause and other women-specific conditions from our catalog.",
    query: /\bpcos\b|\bmenstrual|\bmenopaus|\bgynaec|\bgynec|\bendometrio|\bvaginal\b/i,
    searchLinkQuery: "pcos",
    icon: HeartPulse,
    accent: ACCENT_PURPLE,
  },
  {
    anchorId: "mom-baby-care",
    label: "Mom & Baby Care",
    blurb: "Real pregnancy-related, neonatal and paediatric treatments from our catalog.",
    query: /\bpregnan|\binfant\b|\bpediatric|\bpaediatric|\bneonat|\bbreastfeed|\blactation\b/i,
    searchLinkQuery: "pediatric",
    icon: Baby,
    accent: ACCENT_INDIGO,
  },
];

// Real, genuinely preventive/lifestyle-relevant disease entries from
// data/disease_master.json (checked directly on 2026-09-28 — most of the
// 323 entries are acute or genetic/immune conditions with no honest
// "wellness" framing; these three are the ones that do fit):
const RELATED_HEALTH_AREAS = [
  {
    name: "Iron Deficiency Anaemia",
    detail: "The most common nutritional deficiency — fatigue, breathlessness and pallor are the usual first signs.",
    starter: "I feel very tired and breathless, and I think I might be anaemic",
  },
  {
    name: "Obesity and Metabolic Syndrome",
    detail: "A real, common condition covered in our medical data — weight, blood sugar and cholesterol are assessed together.",
    starter: "I'm overweight and want to understand my metabolic health",
  },
  {
    name: "Osteoporosis",
    detail: "Bone-density loss that's preventable and treatable when caught early, especially after menopause or with age.",
    starter: "I'm worried about my bone health and osteoporosis risk",
  },
];

export default function WellnessPage() {
  const [all, setAll] = useState<Medicine[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    document.title = "Wellness — BalanceAI";
  }, []);

  useEffect(() => {
    fetchAllMedicines()
      .then((meds) => {
        setAll(meds);
        // The 5 subsections only exist in the DOM once real data has loaded,
        // so a direct #anchor link from the Wellness nav dropdown (e.g.
        // /wellness#personal-care) would land before the browser's own
        // scroll-to-hash runs — do it ourselves once the real content exists.
        const hash = window.location.hash.replace("#", "");
        if (hash) {
          window.setTimeout(() => {
            document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 50);
        }
      })
      .catch(() => setError("The medicine catalog couldn't be loaded. Please reload the page and try again."));
  }, []);

  const grouped = useMemo(() => {
    if (!all) return [];
    return WELLNESS_GROUPS.map((group) => {
      const matches = all.filter((m) => {
        if (EXCLUDE_PATTERN.test(m.name)) return false;
        const blob = `${m.name} ${categoryLabel(m.category)} ${(m.used_for_diseases || []).join(" ")}`;
        return group.query.test(blob);
      });
      return { group, matches, total: matches.length };
    }).filter((g) => g.total > 0);
  }, [all]);

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="wellness" />

      <div className="relative overflow-hidden" style={{ background: HERO_GRADIENT }}>
        {/* Typography-led hero — solid gradient field + dot-grid texture,
            no stock photography (redesign, 2026-09-29). */}
        <div
          className="absolute inset-0 opacity-[0.10] pointer-events-none"
          aria-hidden="true"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }}
        />
        <div className="absolute -right-20 -top-24 w-80 h-80 rounded-full pointer-events-none" aria-hidden="true" style={{ border: "1px solid rgba(255,255,255,0.12)" }} />
        <div className="relative max-w-7xl mx-auto px-5 sm:px-8 pt-12 pb-10">
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-white mb-3 tracking-tight leading-[1.05]">Wellness</h1>
          <p className="text-sm sm:text-base max-w-xl" style={{ color: "rgba(255,255,255,0.88)" }}>
            Real, commonly used products from our catalog across sexual wellness, vitamins &amp;
            supplements, personal care, women&apos;s health, and mom &amp; baby care — for genuine
            preventive health, not general &quot;boosting&quot;.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-10">
        {error && (
          <div className="rounded-xl p-4 mb-6 flex items-start gap-2" style={{ background: "#fdecec", border: "1px solid #f5b5b5" }}>
            <p className="text-sm" style={{ color: "#7f1d1d" }}>{error}</p>
          </div>
        )}

        {!all && !error && (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-6 h-6 animate-spin" style={{ color: TEAL }} />
          </div>
        )}

        {all && grouped.map(({ group, matches, total }) => {
          const Icon = group.icon;
          return (
            <section key={group.label} id={group.anchorId} className="mb-12 scroll-mt-28">
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="flex items-center gap-3">
                  <div
                    className="w-11 h-11 rounded-full flex items-center justify-center shrink-0"
                    style={{ background: `linear-gradient(135deg, ${group.accent} 0%, ${TEAL} 100%)` }}
                  >
                    <Icon className="w-5 h-5 text-white" strokeWidth={2} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold" style={{ color: TEXT }}>{group.label}</h2>
                    <p className="text-xs" style={{ color: MUTED }}>{total.toLocaleString("en-IN")} real items in our catalog</p>
                  </div>
                </div>
                <Link
                  href={`/medicines?q=${encodeURIComponent(group.searchLinkQuery)}`}
                  className="text-sm font-semibold shrink-0 whitespace-nowrap"
                  style={{ color: TEAL }}
                >
                  View all {total.toLocaleString("en-IN")} →
                </Link>
              </div>
              <p className="text-xs max-w-2xl mb-4" style={{ color: MUTED }}>{group.blurb}</p>

              <ScrollReveal className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4" stagger={0.03} y={16} start="top 95%">
                {matches.slice(0, PER_GROUP).map((m) => {
                  const displayName = cleanMedicineName(m.name);
                  return (
                    <Link key={m.slug} href={`/medicines/${encodeURIComponent(m.slug)}`} className="block">
                      <Card className="!ring-0 !py-0 sc-card sc-card-interactive h-full p-2.5" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                        <div className="mb-2"><MedicinePackPlaceholder accentColor={group.accent} /></div>
                        <p className="text-xs font-bold leading-snug line-clamp-2" style={{ color: TEXT }}>{displayName}</p>
                      </Card>
                    </Link>
                  );
                })}
              </ScrollReveal>
            </section>
          );
        })}

        <section className="mt-16">
          <h2 className="text-xl font-bold mb-2 text-center" style={{ color: TEXT }}>
            Related Preventive Health Areas
          </h2>
          <p className="text-sm text-center max-w-xl mx-auto mb-8" style={{ color: MUTED }}>
            Some conditions in our medical data are as much about prevention and long-term
            management as they are about treatment.
          </p>
          <div className="grid sm:grid-cols-3 gap-4">
            {RELATED_HEALTH_AREAS.map((area) => (
              <Link
                key={area.name}
                href={`/symptom-checker?q=${encodeURIComponent(area.starter)}`}
                className="block"
              >
                <Card className="!ring-0 !py-0 sc-card sc-card-interactive h-full p-5" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                  <p className="text-sm font-bold mb-1.5" style={{ color: TEXT }}>{area.name}</p>
                  <p className="text-xs leading-relaxed" style={{ color: MUTED }}>{area.detail}</p>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      </div>

      <SiteFooter />
    </main>
  );
}
