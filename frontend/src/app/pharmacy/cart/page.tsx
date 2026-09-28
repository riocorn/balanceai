"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trash2, MessageCircle, ArrowLeft, ShoppingBag, CheckCircle2 } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { BG } from "@/components/diag/theme";
import { useCartStore } from "@/lib/cart-store";
import { getWhatsappLink } from "@/lib/pharmacy-api";
import { GREEN, BORDER, TEXT, MUTED, WHATSAPP_GREEN, EffectivenessBadge } from "@/components/pharmacy/shared";

export default function PharmacyCartPage() {
  const router = useRouter();
  const cart = useCartStore();
  const [waSent, setWaSent] = useState(false);
  const [waLoading, setWaLoading] = useState(false);

  async function verifyOnWhatsapp() {
    setWaLoading(true);
    try {
      const grouped = new Map<string, string[]>();
      cart.items.forEach((i) => {
        const arr = grouped.get(i.disease_name) ?? [];
        arr.push(i.name);
        grouped.set(i.disease_name, arr);
      });
      const [firstDisease] = cart.items;
      const link = await getWhatsappLink({
        disease_id: firstDisease?.disease_id ?? "",
        disease_name: [...grouped.keys()].join(", "),
        medicine_names: cart.items.map((i) => i.name),
      });
      window.open(link, "_blank");
      setWaSent(true);
    } finally {
      setWaLoading(false);
    }
  }

  if (cart.items.length === 0) {
    return (
      <main style={{ background: BG }} className="min-h-screen font-sans">
        <SiteHeader active="pharmacy" />
        <div className="max-w-lg mx-auto px-5 py-20 text-center">
          <ShoppingBag className="w-10 h-10 mx-auto mb-3" style={{ color: MUTED }} />
          <p className="text-sm mb-4" style={{ color: MUTED }}>Your cart is empty.</p>
          <Link href="/pharmacy" className="text-sm font-semibold underline" style={{ color: GREEN }}>
            Describe your problem to find medicines
          </Link>
        </div>
        <SiteFooter />
      </main>
    );
  }

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="pharmacy" />
      <div className="max-w-2xl mx-auto px-5 py-8 pb-32">
        <Link href="/pharmacy" className="inline-flex items-center gap-1 text-xs font-medium mb-4" style={{ color: MUTED }}>
          <ArrowLeft className="w-3.5 h-3.5" /> Add more medicines
        </Link>

        <h1 className="text-xl font-bold mb-4" style={{ color: TEXT }}>
          My Cart ({cart.items.length})
        </h1>

        <div className="flex flex-col gap-2 mb-6">
          {cart.items.map((item) => (
            <div
              key={item.name}
              className="flex items-start justify-between gap-3 rounded-xl p-4"
              style={{ background: "#fff", border: `1px solid ${BORDER}` }}
            >
              <div className="min-w-0">
                <p className="text-[10px] font-semibold uppercase tracking-wide mb-0.5" style={{ color: MUTED }}>
                  {item.disease_name}
                </p>
                <p className="text-sm font-semibold" style={{ color: TEXT }}>{item.name}</p>
                <div className="mt-1.5">
                  <EffectivenessBadge pct={item.effectiveness_pct} />
                </div>
              </div>
              <button onClick={() => cart.removeItem(item.name)} className="p-1.5 rounded-lg shrink-0" style={{ color: "#b91c1c" }}>
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Doctor verification gate — mandatory for every order, every time.
            Step 1 (send to doctor) must happen before Step 2 (confirm) can even
            be touched, and changing the cart resets both steps. */}
        <div className="rounded-xl p-4 mb-4" style={{ background: "#fff", border: `1px solid ${BORDER}` }}>
          <p className="text-sm font-semibold mb-1" style={{ color: TEXT }}>
            Doctor Review Required — mandatory for every order
          </p>
          <p className="text-xs mb-3" style={{ color: MUTED }}>
            No medicine on BalanceAI can be checked out without sending your case to a doctor on
            WhatsApp first. This applies to every order, with no exceptions.
          </p>
          <p className="text-xs mb-3 font-semibold" style={{ color: "#b45309" }}>
            Honesty note: Step 2 below is currently self-declared by you — BalanceAI does not yet
            independently verify that the doctor actually replied. Full backend-verified
            confirmation is coming soon; for now, only check the box if a doctor genuinely
            confirmed this on WhatsApp.
          </p>

          <div className="mb-3">
            <p className="text-[11px] font-bold uppercase tracking-wide mb-1.5" style={{ color: cart.doctorVerified || waSent ? GREEN : TEXT }}>
              Step 1 of 2 — Send your case to the doctor
            </p>
            <button
              onClick={verifyOnWhatsapp}
              disabled={waLoading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-white"
              style={{ background: WHATSAPP_GREEN }}
            >
              <MessageCircle className="w-4 h-4" />
              {waSent ? "Resend on WhatsApp" : "Send for Doctor Verification on WhatsApp"}
            </button>
          </div>

          <div>
            <p className="text-[11px] font-bold uppercase tracking-wide mb-1.5" style={{ color: waSent ? TEXT : MUTED }}>
              Step 2 of 2 — Self-declare the doctor's go-ahead (not yet independently verified)
            </p>
            <label className={`flex items-start gap-2 ${waSent ? "cursor-pointer" : "cursor-not-allowed"}`}>
              <input
                type="checkbox"
                checked={cart.doctorVerified}
                disabled={!waSent}
                onChange={(e) => cart.setDoctorVerified(e.target.checked)}
                className="mt-0.5"
              />
              <span className="text-xs" style={{ color: waSent ? MUTED : "#b0b6b8" }}>
                I confirm a doctor replied on WhatsApp and approved this exact prescription for me.
                (This is a self-declaration — BalanceAI does not yet automatically verify the
                doctor's reply.)
              </span>
            </label>
            {!waSent && (
              <p className="text-[11px] mt-1.5" style={{ color: "#b91c1c" }}>
                Locked — send your case in Step 1 first. You can't confirm without doing that.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Sticky bottom checkout bar */}
      <div className="fixed bottom-0 inset-x-0 border-t px-5 py-3" style={{ background: "#fff", borderColor: BORDER }}>
        <div className="max-w-2xl mx-auto flex items-center justify-between gap-4">
          <div>
            <p className="text-xs" style={{ color: MUTED }}>{cart.items.length} medicine(s)</p>
            {cart.doctorVerified ? (
              <p className="text-xs font-semibold flex items-center gap-1" style={{ color: GREEN }}>
                <CheckCircle2 className="w-3.5 h-3.5" /> Doctor go-ahead self-confirmed
              </p>
            ) : (
              <p className="text-xs" style={{ color: "#b91c1c" }}>WhatsApp doctor review pending</p>
            )}
          </div>
          <button
            onClick={() => router.push("/pharmacy/checkout")}
            disabled={!cart.doctorVerified}
            className="px-6 py-3 rounded-xl text-sm font-bold text-white disabled:opacity-40 transition-all"
            style={{ background: GREEN }}
          >
            Proceed to Checkout
          </button>
        </div>
      </div>
      <SiteFooter />
    </main>
  );
}
