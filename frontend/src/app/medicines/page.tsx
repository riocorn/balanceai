"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Search, Loader2, X, ChevronLeft, ChevronRight, AlertCircle } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import MedicinePackPlaceholder from "@/components/diag/MedicinePackPlaceholder";
import ScrollReveal from "@/components/diag/ScrollReveal";
import { Card } from "@/components/ui/card";
import { useCartStore } from "@/lib/cart-store";
import { TEAL, BLUE, BG, SURFACE, TEXT, MUTED, HERO_GRADIENT, accentForKey } from "@/components/diag/theme";
import { CTA_RADIUS, TRANSITION } from "@/components/diag/tokens";
import {
  type Medicine,
  fetchAllMedicines,
  categoryLabel,
  cleanMedicineName,
  simplifyConditionTag,
} from "@/lib/medicines";

const PAGE_SIZE = 30;
const TOP_CHIP_COUNT = 10;

export default function MedicinesPage() {
  const [all, setAll] = useState<Medicine[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [showAllCategories, setShowAllCategories] = useState(false);
  const cartItems = useCartStore((s) => s.items);
  const addCartItem = useCartStore((s) => s.addItem);

  useEffect(() => {
    document.title = "Medicine Catalog — BalanceAI";
  }, []);

  useEffect(() => {
    fetchAllMedicines()
      .then(setAll)
      .catch(() => setError("The medicine catalog couldn't be loaded. Please reload the page and try again."));
  }, []);

  // Real deep-link support: the shared header's search can pass ?q= into any
  // page — prefill the catalog search box from it.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) setQuery(q);
  }, []);

  // Precompute a lowercase search index once when data arrives — avoids
  // repeated toLowerCase() calls on every keystroke over ~3000 entries.
  const indexed = useMemo(() => {
    if (!all) return [];
    return all.map((m) => ({
      med: m,
      cat: categoryLabel(m.category),
      searchBlob: `${m.name} ${categoryLabel(m.category)} ${(m.used_for_diseases || []).join(" ")}`.toLowerCase(),
    }));
  }, [all]);

  const categories = useMemo(() => {
    const counts = new Map<string, number>();
    for (const row of indexed) counts.set(row.cat, (counts.get(row.cat) || 0) + 1);
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));
  }, [indexed]);

  const topChips = categories.slice(0, TOP_CHIP_COUNT);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return indexed.filter((row) => {
      if (category && row.cat !== category) return false;
      if (q && !row.searchBlob.includes(q)) return false;
      return true;
    });
  }, [indexed, query, category]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageItems = useMemo(
    () => filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE),
    [filtered, safePage]
  );

  useEffect(() => { setPage(1); }, [query, category]);

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="medicines" />

      {/* ── Hero banner — typography-led gradient field, no stock photography
          (redesign, 2026-09-29), same device used across the redesigned
          pages so the site reads as one system. ── */}
      <div className="relative overflow-hidden" style={{ background: HERO_GRADIENT }}>
        <div
          className="absolute inset-0 opacity-[0.10] pointer-events-none"
          aria-hidden="true"
          style={{ backgroundImage: "radial-gradient(circle, #fff 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }}
        />
        <div className="absolute -right-20 -top-24 w-80 h-80 rounded-full pointer-events-none" aria-hidden="true" style={{ border: "1px solid rgba(255,255,255,0.12)" }} />
        <div className="relative max-w-7xl mx-auto px-5 sm:px-8 pt-12 pb-10">
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-white mb-3 tracking-tight leading-[1.05]">
            Find the right medicine, fast.
          </h1>
          <p className="text-sm sm:text-base max-w-xl mb-6" style={{ color: "rgba(255,255,255,0.88)" }}>
            Search clear, source-cited information on thousands of medicines, so you always know
            exactly what you're taking.
          </p>
          <div className="flex items-center gap-2 rounded-full h-11 px-4 shadow-lg max-w-lg" style={{ background: "#fff" }}>
            <Search className="w-4.5 h-4.5 shrink-0" style={{ color: MUTED }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by medicine name, category or condition..."
              className="flex-1 min-w-0 outline-none text-sm bg-transparent"
              style={{ color: TEXT }}
            />
            {query && (
              <button onClick={() => setQuery("")} aria-label="Clear search">
                <X className="w-4 h-4" style={{ color: MUTED }} />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-6 grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-6">
        {/* ── Category sidebar (desktop) ── */}
        <aside className="hidden lg:block">
          <div className="sticky top-20 rounded-2xl p-4" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
            <p className="text-sm font-semibold mb-3" style={{ color: MUTED }}>Browse by category</p>
            <div className="max-h-[65vh] overflow-y-auto pr-1 space-y-1">
              <button
                onClick={() => setCategory(null)}
                className="w-full text-left text-sm px-2.5 py-1.5 rounded-lg flex items-center justify-between"
                style={{ background: category === null ? "rgba(14,124,134,0.10)" : "transparent", color: category === null ? TEAL : TEXT, fontWeight: category === null ? 700 : 500 }}
              >
                <span>All Medicines</span>
                <span className="text-xs" style={{ color: MUTED }}>{indexed.length}</span>
              </button>
              {categories.map(({ name, count }) => (
                <button
                  key={name}
                  onClick={() => setCategory(category === name ? null : name)}
                  className="w-full text-left text-sm px-2.5 py-1.5 rounded-lg flex items-center justify-between gap-2"
                  style={{ background: category === name ? "rgba(14,124,134,0.10)" : "transparent", color: category === name ? TEAL : TEXT, fontWeight: category === name ? 700 : 500 }}
                >
                  <span className="truncate">{name}</span>
                  <span className="text-xs shrink-0" style={{ color: MUTED }}>{count}</span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* ── Category chips (mobile/tablet) ── */}
        <div className="lg:hidden -mx-5 px-5">
          <div className="flex gap-2 overflow-x-auto pb-2 [scrollbar-width:thin]">
            <button
              onClick={() => setCategory(null)}
              className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full whitespace-nowrap"
              style={{ background: category === null ? TEAL : "#fff", color: category === null ? "#fff" : TEXT, border: `1px solid ${category === null ? TEAL : "#E4EBEE"}` }}
            >
              All
            </button>
            {topChips.map(({ name }) => (
              <button
                key={name}
                onClick={() => setCategory(category === name ? null : name)}
                className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full whitespace-nowrap"
                style={{ background: category === name ? TEAL : "#fff", color: category === name ? "#fff" : TEXT, border: `1px solid ${category === name ? TEAL : "#E4EBEE"}` }}
              >
                {name}
              </button>
            ))}
            <button
              onClick={() => setShowAllCategories((v) => !v)}
              className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full whitespace-nowrap"
              style={{ background: "#fff", color: BLUE, border: `1px solid #E4EBEE` }}
            >
              {showAllCategories ? "Hide" : `+${Math.max(0, categories.length - TOP_CHIP_COUNT)} more`}
            </button>
          </div>
          {showAllCategories && (
            <div className="rounded-xl p-3 mb-2 max-h-56 overflow-y-auto grid grid-cols-2 gap-1.5" style={{ background: "#fff", border: "1px solid #E4EBEE" }}>
              {categories.map(({ name, count }) => (
                <button
                  key={name}
                  onClick={() => { setCategory(category === name ? null : name); setShowAllCategories(false); }}
                  className="text-left text-xs px-2 py-1 rounded-lg truncate"
                  style={{ background: category === name ? "rgba(14,124,134,0.10)" : "transparent", color: category === name ? TEAL : TEXT }}
                >
                  {name} <span style={{ color: MUTED }}>({count})</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ── Grid + pagination ── */}
        <div>
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <p className="text-sm" style={{ color: MUTED }}>
              {all ? (
                <>
                  Showing <strong style={{ color: TEXT }}>{filtered.length.toLocaleString("en-IN")}</strong> of{" "}
                  {all.length.toLocaleString("en-IN")} medicines
                  {category ? <> in <strong style={{ color: TEAL }}>{category}</strong></> : null}
                </>
              ) : "Loading real medicine data…"}
            </p>
            {category && (
              <button onClick={() => setCategory(null)} className="text-xs font-semibold flex items-center gap-1" style={{ color: BLUE }}>
                <X className="w-3 h-3" /> Clear category
              </button>
            )}
          </div>

          {error && (
            <div className="rounded-xl p-4 flex items-start gap-2" style={{ background: "#fdecec", border: "1px solid #f5b5b5" }}>
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" style={{ color: "#b91c1c" }} />
              <p className="text-sm" style={{ color: "#7f1d1d" }}>{error}</p>
            </div>
          )}

          {!all && !error && (
            <div className="flex items-center justify-center py-24">
              <Loader2 className="w-6 h-6 animate-spin" style={{ color: TEAL }} />
            </div>
          )}

          {all && !error && filtered.length === 0 && (
            <div className="rounded-xl p-8 text-center" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
              <p className="text-sm" style={{ color: MUTED }}>No medicines matched your search. Try a different name or category.</p>
            </div>
          )}

          {all && pageItems.length > 0 && (
            <>
              {/* Real-measured grid gap: 24px, matching 1mg's live product-grid
                  (.CategoryPage-module__skuListContainer, gap: 24px) */}
              <ScrollReveal className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" stagger={0.04} y={20} start="top 95%">
                {pageItems.map(({ med }) => {
                  const diseases = med.used_for_diseases || [];
                  const displayName = cleanMedicineName(med.name);
                  const inCart = cartItems.some((i) => i.name === displayName);
                  const catLabel = categoryLabel(med.category);
                  const accent = accentForKey(catLabel);
                  return (
                    <Card key={med.slug} className="!ring-0 !py-0 sc-card sc-card-interactive h-full flex flex-col overflow-hidden" style={{ background: SURFACE, border: "1px solid #E4EBEE" }}>
                      <div className="h-1" style={{ background: accent }} aria-hidden="true" />
                      <Link href={`/medicines/${encodeURIComponent(med.slug)}`} className="block">
                        <div className="p-3 pb-0">
                          <MedicinePackPlaceholder accentColor={accent} />
                        </div>
                        <div className="px-3 pt-2.5">
                          <p className="text-[11px] font-semibold mb-0.5 truncate" style={{ color: TEAL }}>
                            {catLabel}
                          </p>
                          <h3 className="text-sm font-bold leading-snug line-clamp-2 mb-1.5" style={{ color: TEXT }}>
                            {displayName}
                          </h3>

                          {diseases.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-2">
                              {diseases.slice(0, 2).map((d) => (
                                <span key={d} className="text-[10px] font-medium px-1.5 py-0.5 rounded-full" style={{ background: "rgba(30,111,217,0.08)", color: BLUE }}>
                                  {simplifyConditionTag(d)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </Link>
                      <div className="px-3 pb-3 pt-1 mt-auto flex items-center justify-between gap-2">
                        <button
                          onClick={() =>
                            addCartItem({
                              name: displayName,
                              disease_id: med.slug,
                              disease_name: diseases[0] ? simplifyConditionTag(diseases[0]) : categoryLabel(med.category),
                              type: categoryLabel(med.category),
                              mechanism: "",
                              effectiveness_pct: null,
                            })
                          }
                          disabled={inCart}
                          className={`text-xs font-medium ${CTA_RADIUS} px-3.5 py-1.5 border hover:bg-[rgba(30,111,217,0.08)] disabled:opacity-60`}
                          style={{ borderColor: BLUE, color: BLUE, background: "transparent", transition: TRANSITION }}
                          title="Placeholder — no real payment/checkout is implemented yet"
                        >
                          {inCart ? "Added" : "Buy Now"}
                        </button>
                        <Link href={`/medicines/${encodeURIComponent(med.slug)}`} className="text-[11px] font-semibold shrink-0" style={{ color: TEAL }}>
                          View details →
                        </Link>
                      </div>
                    </Card>
                  );
                })}
              </ScrollReveal>

              {/* ── Pagination ── */}
              <div className="flex items-center justify-center gap-3 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={safePage <= 1}
                  className="w-9 h-9 rounded-full flex items-center justify-center disabled:opacity-30"
                  style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
                >
                  <ChevronLeft className="w-4 h-4" style={{ color: TEXT }} />
                </button>
                <span className="text-sm font-semibold" style={{ color: TEXT }}>
                  Page {safePage} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safePage >= totalPages}
                  className="w-9 h-9 rounded-full flex items-center justify-center disabled:opacity-30"
                  style={{ background: SURFACE, border: "1px solid #E4EBEE" }}
                >
                  <ChevronRight className="w-4 h-4" style={{ color: TEXT }} />
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <SiteFooter />
    </main>
  );
}
