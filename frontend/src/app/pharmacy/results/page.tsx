"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, Loader2, ShoppingCart } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { BG } from "@/components/diag/theme";
import { getMedicineDetail, type MedicinePayload, type MatchResult } from "@/lib/pharmacy-api";
import { useCartStore } from "@/lib/cart-store";
import {
  GREEN, BORDER, TEXT, MUTED,
  ExpandableText, MedicineProductCard, HardEmergencyBanner,
} from "@/components/pharmacy/shared";

export default function PharmacyResultsPage() {
  const router = useRouter();
  const [stored, setStored] = useState<{ text: string; match: MatchResult } | null>(null);
  const [detail, setDetail] = useState<MedicinePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const cart = useCartStore();

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
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-6 h-6 animate-spin" style={{ color: GREEN }} />
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
          <Link href="/pharmacy" className="text-sm font-semibold underline" style={{ color: GREEN }}>
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
        <Link href="/pharmacy" className="inline-flex items-center gap-1 text-xs font-medium mb-4" style={{ color: MUTED }}>
          <ArrowLeft className="w-3.5 h-3.5" /> Naya search
        </Link>

        {match.hard_emergency_flag && <HardEmergencyBanner />}

        <div className="rounded-xl p-4 mb-4" style={{ background: "#eef7f2", border: `1px solid #b6ddc9` }}>
          <p className="text-xs font-semibold mb-1" style={{ color: GREEN }}>
            AI ne samjha ({
              match.ai_mode === "local_llm" ? "AI-based match" :
              match.ai_mode === "embedding_fallback" ? "semantic-search match" :
              "keyword-based match"
            })
          </p>
          <p className="text-sm" style={{ color: "#1a1a1a" }}>{match.explanation}</p>
        </div>

        {(match.possible_emergency || detail?.emergency_override_rule) && detail?.emergency_override_rule && (
          <div className="rounded-xl p-4 mb-4" style={{ background: "#fdecec", border: "1px solid #f5b5b5" }}>
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
              <div className="rounded-xl p-4 mb-4" style={{ background: "#fff", border: `2px solid ${GREEN}` }}>
                <p className="text-[10px] font-bold uppercase tracking-wide mb-1" style={{ color: GREEN }}>
                  Real curative option
                </p>
                <p className="text-sm font-semibold mb-1" style={{ color: TEXT }}>{detail.curative_option.name}</p>
                <ExpandableText
                  text={detail.curative_option.note}
                  collapsedChars={220}
                  className="text-xs leading-relaxed"
                  style={{ color: "#374151" }}
                />
              </div>
            )}

            <p className="text-sm font-semibold mb-3" style={{ color: TEXT }}>
              AI-suggested medicines ({detail.medicines.length})
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {detail.medicines.map((m) => (
                <MedicineProductCard
                  key={m.name}
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
                className="fixed bottom-5 left-1/2 -translate-x-1/2 flex items-center gap-2 px-6 py-3 rounded-full text-sm font-semibold text-white shadow-lg"
                style={{ background: GREEN }}
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
