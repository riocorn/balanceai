"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Calendar, Leaf,
  Flame, ChevronRight, PlusCircle, X, Menu,
  User, Globe, MessageCircle, BookOpen,
} from "lucide-react";
import { getOrCreateProfile, type UserProfile } from "@/lib/db";
import { type Achievement } from "@/lib/achievements";
import OnboardingModal from "@/components/app/OnboardingModal";
import AchievementToast from "@/components/app/AchievementToast";
import Toaster from "@/components/app/Toaster";
import InstallPrompt from "@/components/app/InstallPrompt";

const NAV = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard"    },
  { href: "/analyze",   icon: PlusCircle,       label: "New Analysis" },
  { href: "/history",   icon: Calendar,          label: "History"      },
  { href: "/chat",      icon: MessageCircle,     label: "AI Chat"      },
  { href: "/diary",     icon: BookOpen,           label: "Food Diary"   },
  { href: "/insights",  icon: Globe,             label: "Insights"     },
  { href: "/profile",   icon: User,              label: "Profile"      },
];

const BG  = "#06060a";
const SBG = "#0c0c12"; // sidebar bg

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [sideOpen, setSideOpen] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [toast, setToast] = useState<Achievement | null>(null);

  useEffect(() => {
    getOrCreateProfile().then((p) => {
      setProfile(p);
      if (!p.name) setShowOnboarding(true);
    });

    const raw = sessionStorage.getItem("pending_achievement");
    if (raw) {
      try { setToast(JSON.parse(raw)); } catch {}
      sessionStorage.removeItem("pending_achievement");
    }
  }, []);

  return (
    <div className="flex min-h-screen" style={{ background: BG }}>
      {showOnboarding && (
        <OnboardingModal onComplete={() => {
          setShowOnboarding(false);
          getOrCreateProfile().then(setProfile);
        }} />
      )}
      <AnimatePresence>
        {toast && <AchievementToast achievement={toast} onDismiss={() => setToast(null)} />}
      </AnimatePresence>
      <Toaster />
      <InstallPrompt />
      {/* ── Desktop sidebar ─────────────────────────────── */}
      <aside
        className="hidden lg:flex flex-col w-56 shrink-0 sticky top-0 h-screen border-r"
        style={{ background: SBG, borderColor: "rgba(255,255,255,0.06)" }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
          <div className="w-8 h-8 rounded-lg bg-[#00d97e] flex items-center justify-center shrink-0">
            <Leaf className="w-4 h-4 text-black" />
          </div>
          <span className="font-bold text-sm text-white font-display tracking-tight">BalanceAI</span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-5 space-y-1">
          {NAV.map(({ href, icon: Icon, label }) => {
            const active = pathname === href || (href !== "/" && pathname.startsWith(href));
            return (
              <Link key={href} href={href}>
                <div
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer"
                  style={{
                    background: active ? "rgba(0,217,126,0.1)" : "transparent",
                    color: active ? "#00d97e" : "rgba(255,255,255,0.52)",
                    border: active ? "1px solid rgba(0,217,126,0.2)" : "1px solid transparent",
                  }}
                  onMouseEnter={(e) => { if (!active) e.currentTarget.style.color = "rgba(255,255,255,0.85)"; }}
                  onMouseLeave={(e) => { if (!active) e.currentTarget.style.color = "rgba(255,255,255,0.52)"; }}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                  {active && <ChevronRight className="w-3 h-3 ml-auto opacity-60" />}
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Streak + back to landing */}
        <div className="px-4 pb-5 space-y-3">
          {profile && (
            <div
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
              style={{ background: "rgba(245,158,11,0.07)", border: "1px solid rgba(245,158,11,0.15)" }}
            >
              <Flame className="w-4 h-4" style={{ color: "#f59e0b" }} />
              <div>
                <p className="text-xs font-bold" style={{ color: "#f59e0b" }}>
                  {profile.streak} day streak
                </p>
                <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.35)" }}>
                  {profile.total_analyses} analyses total
                </p>
              </div>
            </div>
          )}
          <Link href="/">
            <div
              className="text-xs px-3 py-2 rounded-xl text-center cursor-pointer transition-colors"
              style={{
                color: "rgba(255,255,255,0.3)",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.7)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.3)")}
            >
              ← Back to home
            </div>
          </Link>
        </div>
      </aside>

      {/* ── Main content ────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <div
          className="lg:hidden flex items-center justify-between px-4 h-14 border-b shrink-0"
          style={{ background: SBG, borderColor: "rgba(255,255,255,0.06)" }}
        >
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#00d97e] flex items-center justify-center">
              <Leaf className="w-3.5 h-3.5 text-black" />
            </div>
            <span className="font-bold text-sm text-white font-display">BalanceAI</span>
          </div>
          <button
            onClick={() => setSideOpen(true)}
            className="text-white/60 p-1"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        {/* Mobile drawer */}
        <AnimatePresence>
          {sideOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 z-40 lg:hidden"
                onClick={() => setSideOpen(false)}
              />
              <motion.div
                initial={{ x: -260 }} animate={{ x: 0 }} exit={{ x: -260 }}
                transition={{ type: "spring", stiffness: 350, damping: 32 }}
                className="fixed left-0 top-0 bottom-0 w-60 z-50 flex flex-col lg:hidden"
                style={{ background: SBG, borderRight: "1px solid rgba(255,255,255,0.06)" }}
              >
                <div className="flex items-center justify-between px-5 py-5">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-[#00d97e] flex items-center justify-center">
                      <Leaf className="w-3.5 h-3.5 text-black" />
                    </div>
                    <span className="font-bold text-sm text-white font-display">BalanceAI</span>
                  </div>
                  <button onClick={() => setSideOpen(false)} className="text-white/40">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <nav className="flex-1 px-3 space-y-1">
                  {NAV.map(({ href, icon: Icon, label }) => (
                    <Link key={href} href={href} onClick={() => setSideOpen(false)}>
                      <div
                        className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium"
                        style={{ color: pathname === href ? "#00d97e" : "rgba(255,255,255,0.6)" }}
                      >
                        <Icon className="w-4 h-4" />
                        {label}
                      </div>
                    </Link>
                  ))}
                </nav>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
