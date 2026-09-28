"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, ArrowLeft } from "lucide-react";
import AppShell from "@/components/app/AppShell";
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
    if (!cart.doctorVerified || cart.items.length === 0) {
      router.replace("/pharmacy/cart");
    }
  }, [cart.doctorVerified, cart.items.length, router]);

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
      <AppShell>
        <div className="max-w-md mx-auto px-5 py-20 text-center">
          <CheckCircle2 className="w-12 h-12 mx-auto mb-4" style={{ color: GREEN }} />
          <h1 className="text-lg font-bold mb-1" style={{ color: TEXT }}>Order Placed!</h1>
          <p className="text-sm mb-1" style={{ color: MUTED }}>Order ID: <span className="font-mono font-semibold">{orderRef}</span></p>
          <p className="text-xs mb-6" style={{ color: MUTED }}>
            Doctor-verified prescription ke basis par aapka order confirm ho gaya hai.
          </p>
          <Link href="/pharmacy" className="text-sm font-semibold underline" style={{ color: GREEN }}>
            Wapas Pharmacy jaayein
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-lg mx-auto px-5 py-8 pb-10">
        <Link href="/pharmacy/cart" className="inline-flex items-center gap-1 text-xs font-medium mb-4" style={{ color: MUTED }}>
          <ArrowLeft className="w-3.5 h-3.5" /> Cart par wapas jaayein
        </Link>

        <h1 className="text-xl font-bold mb-5" style={{ color: TEXT }}>Checkout</h1>

        <p className="text-sm font-semibold mb-2" style={{ color: TEXT }}>Delivery Address</p>
        <div className="flex flex-col gap-2 mb-6">
          <input placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)}
            className="px-4 py-2.5 rounded-xl text-sm outline-none" style={{ background: "#fff", border: `1px solid ${BORDER}`, color: TEXT }} />
          <input placeholder="Phone number" value={phone} onChange={(e) => setPhone(e.target.value)}
            className="px-4 py-2.5 rounded-xl text-sm outline-none" style={{ background: "#fff", border: `1px solid ${BORDER}`, color: TEXT }} />
          <input placeholder="Pincode" value={pincode} onChange={(e) => setPincode(e.target.value)}
            className="px-4 py-2.5 rounded-xl text-sm outline-none" style={{ background: "#fff", border: `1px solid ${BORDER}`, color: TEXT }} />
          <input placeholder="Address line" value={line} onChange={(e) => setLine(e.target.value)}
            className="px-4 py-2.5 rounded-xl text-sm outline-none" style={{ background: "#fff", border: `1px solid ${BORDER}`, color: TEXT }} />
        </div>

        <p className="text-sm font-semibold mb-2" style={{ color: TEXT }}>Payment Method</p>
        <div className="flex flex-col gap-2 mb-6">
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
          className="w-full py-3.5 rounded-xl text-sm font-bold text-white disabled:opacity-40"
          style={{ background: GREEN }}
        >
          {placing ? "Placing Order..." : "Place Order"}
        </button>
      </div>
    </AppShell>
  );
}
