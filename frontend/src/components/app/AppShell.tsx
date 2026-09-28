"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, Menu, X, ShoppingCart } from "lucide-react";
import { getOrCreateProfile, type UserProfile } from "@/lib/db";
import { useCartStore } from "@/lib/cart-store";
import { type Achievement } from "@/lib/achievements";
import OnboardingModal from "@/components/app/OnboardingModal";
import AchievementToast from "@/components/app/AchievementToast";
import Toaster from "@/components/app/Toaster";
import InstallPrompt from "@/components/app/InstallPrompt";

const NAV = [
  { href: "/dashboard",  label: "Dashboard"    },
  { href: "/analyze",    label: "New Analysis" },
  { href: "/symptom-checker", label: "Find Treatment" },
  { href: "/pharmacy",   label: "Pharmacy"     },
  { href: "/medicines",  label: "Medicines"    },
  { href: "/wellness",   label: "Wellness"     },
  { href: "/food-history", label: "Your Medical and Food" },
  { href: "/supplement-report", label: "Supplement Report" },
  { href: "/insights",   label: "Insights"     },
  { href: "/profile",    label: "Profile"      },
];

const GREEN  = "#1d5c3d";
const BG     = "#f7f8f6";
const BORDER = "#e4e7e2";
const TEXT   = "#1a1a1a";
const MUTED  = "#6b7280";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [toast, setToast] = useState<Achievement | null>(null);
  const cartCount = useCartStore((s) => s.items.length);

  useEffect(() => {
    getOrCreateProfile().then((p) => {
      setProfile(p);
    });
    const raw = sessionStorage.getItem("pending_achievement");
    if (raw) {
      try { setToast(JSON.parse(raw)); } catch {}
      sessionStorage.removeItem("pending_achievement");
    }
  }, []);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: BG }}>
      <AnimatePresence>
        {toast && <AchievementToast achievement={toast} onDismiss={() => setToast(null)} />}
      </AnimatePresence>
      <Toaster />
      <InstallPrompt />

      {/* ── Top navigation bar — balance.it style ── */}
      <header className="sticky top-0 z-40 bg-white border-b" style={{ borderColor: BORDER }}>
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between gap-6">

          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded-md flex items-center justify-center" style={{ background: GREEN }}>
              <Leaf className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold text-sm tracking-tight" style={{ color: TEXT }}>BalanceAI</span>
          </Link>

          {/* Desktop nav links */}
          <nav className="hidden lg:flex items-center gap-1 flex-1">
            {NAV.map(({ href, label }) => {
              const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
              return (
                <Link key={href} href={href}>
                  <span
                    className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                    style={{
                      background: active ? "#eef7f2" : "transparent",
                      color: active ? GREEN : MUTED,
                      borderBottom: active ? `2px solid ${GREEN}` : "2px solid transparent",
                    }}
                  >
                    {label}
                  </span>
                </Link>
              );
            })}
          </nav>

          {/* Profile chip */}
          <div className="hidden lg:flex items-center gap-2 shrink-0">
            {profile?.name && (
              <Link href="/profile">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition-all hover:bg-gray-50"
                  style={{ border: `1px solid ${BORDER}` }}>
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
                    style={{ background: GREEN }}>
                    {profile.name[0].toUpperCase()}
                  </div>
                  <span className="text-sm font-medium" style={{ color: TEXT }}>{profile.name}</span>
                </div>
              </Link>
            )}
            {!profile?.name && (
              <Link href="/profile">
                <div className="px-3 py-1.5 rounded-lg text-sm font-medium cursor-pointer"
                  style={{ border: `1px solid ${BORDER}`, color: MUTED }}>
                  Profile
                </div>
              </Link>
            )}
          </div>

          {/* Pharmacy cart icon — always visible, e-pharmacy pattern */}
          <Link href="/pharmacy/cart" className="relative p-1.5 rounded-lg shrink-0" style={{ color: MUTED }}>
            <ShoppingCart className="w-5 h-5" />
            {cartCount > 0 && (
              <span
                className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full text-[9px] font-bold text-white flex items-center justify-center"
                style={{ background: GREEN }}
              >
                {cartCount}
              </span>
            )}
          </Link>

          {/* Mobile hamburger */}
          <button className="lg:hidden p-1.5 rounded-lg" style={{ color: MUTED }}
            onClick={() => setMobileOpen(true)}>
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/20 z-50 lg:hidden"
              onClick={() => setMobileOpen(false)} />
            <motion.div
              initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
              transition={{ type: "spring", stiffness: 350, damping: 32 }}
              className="fixed right-0 top-0 bottom-0 w-64 z-50 flex flex-col bg-white lg:hidden"
              style={{ borderLeft: `1px solid ${BORDER}` }}>
              <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: BORDER }}>
                <span className="font-bold text-sm" style={{ color: TEXT }}>Menu</span>
                <button onClick={() => setMobileOpen(false)} style={{ color: MUTED }}>
                  <X className="w-4 h-4" />
                </button>
              </div>
              <nav className="flex-1 px-3 py-4 space-y-0.5">
                {NAV.map(({ href, label }) => {
                  const active = pathname === href;
                  return (
                    <Link key={href} href={href} onClick={() => setMobileOpen(false)}>
                      <div className="px-4 py-2.5 rounded-lg text-sm font-medium"
                        style={{
                          background: active ? "#eef7f2" : "transparent",
                          color: active ? GREEN : MUTED,
                        }}>
                        {label}
                      </div>
                    </Link>
                  );
                })}
              </nav>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ── Page content — full width ── */}
      <main className="flex-1">
        <motion.div
          key={pathname}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}
