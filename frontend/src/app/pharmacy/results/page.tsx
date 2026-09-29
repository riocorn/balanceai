"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, ShoppingCart } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { BG, SURFACE } from "@/components/diag/theme";
import { getMedicineDetail, type MedicinePayload, type MatchResult } from "@/lib/pharmacy-api";
import { useCartStore } from "@/lib/cart-store";
import {
  GREEN, BORDER, TEXT, MUTED,
  ExpandableText, MedicineProductCard, HardEmergencyBanner,
} from "@/components/pharmacy/shared";
import { CTA_RADIUS, TRANSITION_ALL, FOCUS_RING, ELEVATED_SHADOW } from "@/components/diag/tokens";

export default function PharmacyResultsPage() {
  const router = useRouter();
  const [stored, setStored] = useState<{ text: string; match: MatchResult } | null>(null);
  const [detail, setDetail] = useState<MedicinePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const cart = useCartStore();

  useEffect(() => {
    document.title = "Results — BalanceAI";
  }, []);

  useEffect(() => {
    const raw = sessionStorage.getItem("pharmacy_last_match");
    if (!raw) {
      router.replace("/pharmacy");
      return;
    }
    const parsed = JSON.parse(raw);
    setStored(parsed);

    if (!parsed.match?.disease_id) {
      setLoading(false);
      setNotFound(true);
      return;
    }

    getMedicineDetail(parsed.match.disease_id)
      .then(setDetail)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <main style={{ background: BG }} className="min-h-screen font-sans">
        <SiteHeader active="pharmacy" />
        <div className="max-w-3xl mx-auto px-5 py-8" aria-live="polite" aria-label="Loading your results">
          <div className="sk h-3.5 w-24 rounded-full mb-4" />
          <div className="sc-card p-4 mb-4" style={{ background: SURFACE, border: `1px solid ${BORDER}` }}>
            <div className="sk h-3 w-40 rounded-full mb-2" />
            <div className="sk h-4 w-full rounded-full" />
          </div>
          <div className="sk h-6 w-1/2 rounded-full mb-1.5" />
          <div className="sk h-3 w-1/4 rounded-full mb-5" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" aria-hidden="true">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="sc-card p-4" style={{ background: SURFACE, border: `1px solid ${BORDER}` }}>
                <div className="flex items-start gap-3">
                  <div className="sk w-12 h-12 rounded-xl shrink-0" />
                  <div className="flex-1 space-y-2 pt-1">
                    <div className="sk h-3.5 w-3/4 rounded-full" />
                    <div className="sk h-2.5 w-1/2 rounded-full" />
                  </div>
                </div>
                <div className="sk h-1.5 w-full rounded-full mt-3" />
              </div>
            ))}
          </div>
        </div>
        <SiteFooter />
      </main>
    );
  }

  if (notFound || !stored) {
    return (
      <main style={{ background: BG }} className="min-h-screen font-sans">
        <SiteHeader active="pharmacy" />
        <div className="max-w-lg mx-auto px-5 py-16 text-center">
          {stored?.match?.hard_emergency_flag && <HardEmergencyBanner />}
          <p className="text-sm mb-4" style={{ color: MUTED }}>
            {stored?.match?.explanation ||
              "No matching condition was found. Please describe your problem in a bit more detail."}
          </p>
          <Link href="/pharmacy" className={`text-sm font-semibold underline hover:opacity-75 rounded ${FOCUS_RING}`} style={{ color: GREEN, transition: TRANSITION_ALL }}>
            Dobara try karein
          </Link>
        </div>
        <SiteFooter />
      </main>
    );
  }

  const { match } = stored;
  const cartNames = new Set(cart.items.map((i) => i.name));

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="pharmacy" />
      <div className="max-w-3xl mx-auto px-5 py-8">
        <Link href="/pharmacy" className={`inline-flex items-center gap-1 text-xs font-medium mb-4 rounded hover:opacity-75 ${FOCUS_RING}`} style={{ color: MUTED, transition: TRANSITION_ALL }}>
          <ArrowLeft className="w-3.5 h-3.5" /> Naya search
        </Link>

        {match.hard_emergency_flag && <HardEmergencyBanner />}

        <div className="sc-card p-4 mb-4" style={{ background: "rgba(10,82,89,0.06)", border: "1px solid rgba(10,82,89,0.22)" }}>
          <p className="text-xs font-semibold mb-1" style={{ color: GREEN }}>
            AI ne samjha ({
              match.ai_mode === "local_llm" ? "AI-based match" :
              match.ai_mode === "embedding_fallback" ? "semantic-search match" :
              "keyword-based match"
            })
          </p>
          <p className="text-sm" style={{ color: TEXT }}>{match.explanation}</p>
        </div>

        {(match.possible_emergency || detail?.emergency_override_rule) && detail?.emergency_override_rule && (
          <div className="sc-card p-4 mb-4" style={{ background: "#fdecec", border: "1px solid #f5b5b5" }}>
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4" style={{ color: "#b91c1c" }} />
              <p className="text-xs font-bold" style={{ color: "#b91c1c" }}>
                Safety Alert — pehle ye padhein
              </p>
            </div>
            <ExpandableText
              text={detail.emergency_override_rule}
              collapsedChars={300}
              className="text-xs leading-relaxed"
              style={{ color: "#7f1d1d" }}
            />
          </div>
        )}

        {detail && (
          <>
            <h1 className="text-xl font-bold mb-0.5" style={{ color: TEXT }}>{detail.name}</h1>
            <p className="text-xs mb-5" style={{ color: MUTED }}>{detail.category}</p>

            {detail.curative_option && (
              <div className="sc-card p-4 mb-4" style={{ background: SURFACE, border: `1.5px solid ${GREEN}` }}>
                <p className="text-xs font-bold mb-1" style={{ color: GREEN }}>
                  Real curative option
                </p>
                <p className="text-sm font-semibold mb-1" style={{ color: TEXT }}>{detail.curative_option.name}</p>
                <ExpandableText
                  text={detail.curative_option.note}
                  collapsedChars={220}
                  className="text-xs leading-relaxed"
                  style={{ color: MUTED }}
                />
              </div>
            )}

            <p className="text-sm font-semibold mb-3" style={{ color: TEXT }}>
              AI-suggested medicines ({detail.medicines.length})
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {detail.medicines.map((m, idx) => (
                <MedicineProductCard
                  // Same duplicate-name-key bug fixed on symptom-checker's
                  // results list (real example found live: "Ertapenem +
                  // Metronidazole" appearing twice) -- name alone isn't a
                  // safe React key here either.
                  key={`${m.name}-${idx}`}
                  medicine={m}
                  diseaseId={detail.id}
                  diseaseName={detail.name}
                  inCart={cartNames.has(m.name)}
                  isCurative={detail.curative_option?.name === m.name}
                  onAdd={() =>
                    cart.addItem({
                      disease_id: detail.id,
                      disease_name: detail.name,
                      name: m.name,
                      type: m.type,
                      mechanism: m.mechanism,
                      effectiveness_pct: m.effectiveness_pct,
                    })
                  }
                />
              ))}
            </div>

            {cart.items.length > 0 && (
              <Link
                href="/pharmacy/cart"
                className={`fixed bottom-5 left-1/2 -translate-x-1/2 h-11 flex items-center gap-2 px-6 ${CTA_RADIUS} text-sm font-medium text-white hover:brightness-110 hover:-translate-y-0.5 ${FOCUS_RING}`}
                style={{ background: GREEN, boxShadow: ELEVATED_SHADOW, transition: TRANSITION_ALL }}
              >
                <ShoppingCart className="w-4 h-4" />
                Cart dekhein ({cart.items.length})
              </Link>
            )}
          </>
        )}
      </div>
      <SiteFooter />
    </main>
  );
}
