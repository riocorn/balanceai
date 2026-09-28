"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import MedicinePackPlaceholder from "@/components/diag/MedicinePackPlaceholder";
import ScrollReveal from "@/components/diag/ScrollReveal";
import { Card } from "@/components/ui/card";
import { CATEGORY_TILES } from "@/components/diag/categories";
import { TEAL, BG, SURFACE, TEXT, MUTED, HERO_GRADIENT, accentForKey } from "@/components/diag/theme";
import {
  type Medicine,
  fetchAllMedicines,
  categoryLabel,
  cleanMedicineName,
} from "@/lib/medicines";

const PER_CATEGORY = 6;

// A real, grouped browsing experience — distinct from both the flat,
// searchable full catalog (/medicines) and the free-text symptom-checker
// flow (/symptom-checker): here the same real medicine catalog is organized
// under the same 8 real health areas used across the site, each backed by a
// real substring match against name/category/used_for_diseases (counts
// verified against data/medicine_details.json on 2026-09-28).
export default function MedicinesByCategoryPage() {
  const [all, setAll] = useState<Medicine[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    document.title = "Browse by Health Area — BalanceAI";
  }, []);

  useEffect(() => {
    fetchAllMedicines()
      .then(setAll)
      .catch(() => setError("The medicine catalog couldn't be loaded. Please reload the page and try again."));
  }, []);

  const grouped = useMemo(() => {
    if (!all) return [];
    return CATEGORY_TILES.map((tile) => {
      const term = tile.medicinesQuery.toLowerCase();
      const matches = all.filter((m) => {
        const blob = `${m.name} ${categoryLabel(m.category)} ${(m.used_for_diseases || []).join(" ")}`.toLowerCase();
        return blob.includes(term);
      });
      return { tile, matches, total: matches.length };
    });
  }, [all]);

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="medicines" />

      <div className="relative overflow-hidden" style={{ background: HERO_GRADIENT }}>
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }}
        />
        <div className="relative max-w-7xl mx-auto px-5 sm:px-8 pt-10 pb-8">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white mb-2 tracking-tight">
            Browse by Health Area
          </h1>
          <p className="text-sm max-w-xl" style={{ color: "rgba(255,255,255,0.85)" }}>
            Real medicines from our catalog, grouped by the health area they're commonly used for —
            a quick way to see what's relevant to you before diving into the full list.
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

        {all && grouped.map(({ tile, matches, total }) => {
          const accent = tile.accent;
          const Icon = tile.icon;
          if (total === 0) return null;
          return (
            <section key={tile.label} className="mb-12">
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-11 h-11 rounded-full flex items-center justify-center shrink-0"
                    style={{ background: `linear-gradient(135deg, ${accent} 0%, ${TEAL} 100%)` }}
                  >
                    <Icon className="w-5 h-5 text-white" strokeWidth={2} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold" style={{ color: TEXT }}>{tile.label}</h2>
                    <p className="text-xs" style={{ color: MUTED }}>{total.toLocaleString("en-IN")} real medicines</p>
                  </div>
                </div>
                <Link
                  href={`/medicines?q=${encodeURIComponent(tile.medicinesQuery)}`}
                  className="text-sm font-semibold shrink-0 whitespace-nowrap"
                  style={{ color: TEAL }}
                >
                  View all {total.toLocaleString("en-IN")} →
                </Link>
              </div>

              <ScrollReveal className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4" stagger={0.03} y={16} start="top 95%">
                {matches.slice(0, PER_CATEGORY).map((m) => {
                  const displayName = cleanMedicineName(m.name);
                  const medAccent = accentForKey(categoryLabel(m.category));
                  return (
                    <Link key={m.slug} href={`/medicines/${encodeURIComponent(m.slug)}`} className="block">
                      <Card className="!ring-0 !py-0 sc-card sc-card-interactive h-full p-2.5" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                        <div className="mb-2"><MedicinePackPlaceholder accentColor={medAccent} /></div>
                        <p className="text-xs font-bold leading-snug line-clamp-2" style={{ color: TEXT }}>{displayName}</p>
                      </Card>
                    </Link>
                  );
                })}
              </ScrollReveal>
            </section>
          );
        })}
      </div>

      <SiteFooter />
    </main>
  );
}
