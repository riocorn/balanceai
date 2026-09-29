"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, ArrowLeft } from "lucide-react";
import SiteHeader from "@/components/diag/SiteHeader";
import SiteFooter from "@/components/diag/SiteFooter";
import { BG, EFFECTIVENESS, HERO_GRADIENT } from "@/components/diag/theme";
import { useCartStore } from "@/lib/cart-store";
import { placePharmacyOrder } from "@/lib/db";
import { GREEN, BORDER, TEXT, MUTED } from "@/components/pharmacy/shared";

type PaymentMethod = "cod" | "upi" | "card";

export default function PharmacyCheckoutPage() {
  const router = useRouter();
  const cart = useCartStore();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [pincode, setPincode] = useState("");
  const [line, setLine] = useState("");
  const [payment, setPayment] = useState<PaymentMethod>("cod");
  const [placing, setPlacing] = useState(false);
  const [orderRef, setOrderRef] = useState<string | null>(null);

  useEffect(() => {
    document.title = "Checkout — BalanceAI";
  }, []);

  // Real bug found and fixed here, 2026-09-28 (reproduced live): placeOrder()
  // below calls cart.clear() on success, which resets doctorVerified to
  // false and items to []. This guard effect re-runs on every state change
  // and, without the orderRef check, immediately fired right after a
  // successful order and force-navigated the user back to (now-empty)
  // /pharmacy/cart -- so the "Order Placed!" confirmation screen with the
  // real order ID was never actually seen, even though the order itself was
  // saved correctly. Skipping the redirect once an order has been placed
  // (orderRef is set) lets the success screen actually render.
  useEffect(() => {
    if (orderRef) return;
    if (!cart.doctorVerified || cart.items.length === 0) {
      router.replace("/pharmacy/cart");
    }
  }, [cart.doctorVerified, cart.items.length, router, orderRef]);

  async function placeOrder() {
    if (!name.trim() || !phone.trim() || !pincode.trim() || !line.trim()) return;
    setPlacing(true);
    const ref = "BAI" + Math.random().toString(36).slice(2, 9).toUpperCase();
    await placePharmacyOrder({
      order_ref: ref,
      timestamp: Date.now(),
      items: cart.items.map((i) => ({
        disease_id: i.disease_id,
        disease_name: i.disease_name,
        name: i.name,
        effectiveness_pct: i.effectiveness_pct,
      })),
      address: { name, phone, pincode, line },
      payment_method: payment,
      doctor_verified: true,
      status: "placed",
    });
    setOrderRef(ref);
    cart.clear();
    setPlacing(false);
  }

  if (orderRef) {
    return (
      <main style={{ background: BG }} className="min-h-screen font-sans">
        <SiteHeader active="pharmacy" />
        <div className="max-w-md mx-auto px-5 py-20 text-center">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
            style={{ background: `linear-gradient(135deg, ${EFFECTIVENESS} 0%, ${GREEN} 100%)`, boxShadow: "0 10px 26px rgba(31,174,122,0.3)" }}
          >
            <CheckCircle2 className="w-8 h-8 text-white" strokeWidth={2} />
          </div>
          <h1 className="text-lg font-bold mb-1" style={{ color: TEXT }}>Order Placed!</h1>
          <p className="text-sm mb-1" style={{ color: MUTED }}>Order ID: <span className="font-mono font-semibold">{orderRef}</span></p>
          <p className="text-xs mb-6" style={{ color: MUTED }}>
            This order was placed on the basis of your self-confirmed WhatsApp doctor go-ahead.
            BalanceAI doesn't yet automatically verify that step.
          </p>
          <Link href="/pharmacy" className="text-sm font-semibold underline" style={{ color: GREEN }}>
            Back to Pharmacy
          </Link>
        </div>
        <SiteFooter />
      </main>
    );
  }

  const itemCount = cart.items.length;

  return (
    <main style={{ background: BG }} className="min-h-screen font-sans">
      <SiteHeader active="pharmacy" />
      <div className="max-w-4xl mx-auto px-5 py-8 pb-16">
        <Link href="/pharmacy/cart" className="inline-flex items-center gap-1 text-xs font-medium mb-4" style={{ color: MUTED }}>
          <ArrowLeft className="w-3.5 h-3.5" /> Back to cart
        </Link>

        <h1 className="font-display text-2xl sm:text-3xl mb-8" style={{ color: TEXT }}>Checkout</h1>

        <div className="grid lg:grid-cols-[1fr_320px] gap-10 items-start">
          {/* ── Left: the actual form, split into two clearly separated
              stages instead of one undifferentiated stack of inputs ── */}
          <div>
            <div className="flex items-baseline gap-2 mb-3">
              <span className="font-display text-2xl leading-none select-none" style={{ color: GREEN, opacity: 0.35 }}>01</span>
              <p className="text-sm font-semibold" style={{ color: TEXT }}>Where should this go?</p>
            </div>
            <div className="flex flex-col gap-2 mb-8 pl-8">
              {[
                { placeholder: "Full name", value: name, set: setName },
                { placeholder: "Phone number", value: phone, set: setPhone },
                { placeholder: "Pincode", value: pincode, set: setPincode },
                { placeholder: "Address line", value: line, set: setLine },
              ].map((f) => (
                <input
                  key={f.placeholder}
                  placeholder={f.placeholder}
                  value={f.value}
                  onChange={(e) => f.set(e.target.value)}
                  className="px-4 py-2.5 rounded-xl text-sm outline-none transition-colors duration-150"
                  style={{ background: "#fff", border: `1px solid ${BORDER}`, color: TEXT }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = GREEN; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = BORDER; }}
                />
              ))}
            </div>

            <div className="flex items-baseline gap-2 mb-3">
              <span className="font-display text-2xl leading-none select-none" style={{ color: GREEN, opacity: 0.35 }}>02</span>
              <p className="text-sm font-semibold" style={{ color: TEXT }}>How will you pay?</p>
            </div>
            <div className="flex flex-col gap-2 mb-8 pl-8">
              {([
                { id: "cod", label: "Cash on Delivery" },
                { id: "upi", label: "UPI (real gateway pending merchant setup)" },
                { id: "card", label: "Card (real gateway pending merchant setup)" },
              ] as { id: PaymentMethod; label: string }[]).map((opt) => (
                <label key={opt.id} className="flex items-center gap-2 px-4 py-2.5 rounded-xl cursor-pointer"
                  style={{ background: "#fff", border: `1px solid ${payment === opt.id ? GREEN : BORDER}` }}>
                  <input type="radio" name="payment" checked={payment === opt.id} onChange={() => setPayment(opt.id)} />
                  <span className="text-sm" style={{ color: TEXT }}>{opt.label}</span>
                </label>
              ))}
            </div>

            <button
              onClick={placeOrder}
              disabled={placing || !name.trim() || !phone.trim() || !pincode.trim() || !line.trim()}
              className="w-full py-3.5 rounded-xl text-sm font-bold text-white disabled:opacity-40 shadow-md hover:shadow-lg transition-shadow duration-200"
              style={{ background: HERO_GRADIENT }}
            >
              {placing ? "Placing Order..." : "Place Order"}
            </button>
          </div>

          {/* ── Right: order summary — the thing every real checkout has
              that this one was missing entirely, letting someone place an
              order with zero visibility into what's actually in it ── */}
          <div className="rounded-2xl p-5 lg:sticky lg:top-20" style={{ background: "#fff", border: `1px solid ${BORDER}` }}>
            <p className="text-sm font-semibold mb-4" style={{ color: TEXT }}>
              Order summary — {itemCount} medicine{itemCount === 1 ? "" : "s"}
            </p>
            <div className="flex flex-col gap-3 mb-4 max-h-72 overflow-y-auto pr-1">
              {cart.items.map((item) => (
                <div key={item.name} className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-xs font-semibold leading-snug" style={{ color: TEXT }}>{item.name}</p>
                    <p className="text-[11px]" style={{ color: MUTED }}>{item.disease_name}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="pt-3 flex items-center gap-2 text-[11px]" style={{ borderTop: `1px solid ${BORDER}`, color: MUTED }}>
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" style={{ color: GREEN }} />
              Doctor go-ahead self-confirmed for this order
            </div>
          </div>
        </div>
      </div>
      <SiteFooter />
    </main>
  );
}
