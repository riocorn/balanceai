import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface CartItem {
  disease_id: string;
  disease_name: string;
  name: string;
  type: string;
  mechanism: string;
  effectiveness_pct: number | null;
}

interface CartState {
  items: CartItem[];
  doctorVerified: boolean;
  addItem: (item: CartItem) => void;
  removeItem: (name: string) => void;
  clear: () => void;
  setDoctorVerified: (v: boolean) => void;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      doctorVerified: false,
      addItem: (item) => {
        // Any change to cart contents invalidates a prior doctor verification —
        // the doctor only confirmed the item set they were shown on WhatsApp.
        // Every order must be re-confirmed against what's actually in the cart.
        if (get().items.some((i) => i.name === item.name)) return;
        set({ items: [...get().items, item], doctorVerified: false });
      },
      removeItem: (name) =>
        set({ items: get().items.filter((i) => i.name !== name), doctorVerified: false }),
      clear: () => set({ items: [], doctorVerified: false }),
      setDoctorVerified: (v) => set({ doctorVerified: v }),
    }),
    { name: "balanceai_pharmacy_cart" }
  )
);
