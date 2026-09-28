"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, ShoppingCart, Pill, Sparkles, ArrowRight } from "lucide-react";
import { useCartStore } from "@/lib/cart-store";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu";
import { TEAL, BLUE, BG, SURFACE, TEXT, MUTED, HERO_GRADIENT } from "./theme";
import { CATEGORY_TILES } from "./categories";
import {
  ensureSearchIndex,
  searchMedicines,
  isNonLatinScript,
  type MedicineMatch,
} from "@/lib/search-index";

// ---------------------------------------------------------------------------
// Shared 3-row header — real-measured structural match to Tata 1mg's header
// (getComputedStyle extracted 2026-09-28: 3 stacked rows, ~53/52/44px, border
// rgb(221,226,235), sharp product-card radius) combined with Netmeds' teal
// branded strip + full-pill search bar (measured radius 250px / height 40-44px).
// The hover mega-menus use shadcn/ui's NavigationMenu (Radix/base-ui
// primitive, opens on hover by default) styled with our own locked palette
// rather than the shared neutral theme tokens, so unrelated dashboard pages
// that also use shadcn/ui are unaffected.
// Reused across symptom-checker, pharmacy, medicines and legal pages so the
// nav/search/cart/mega-menu behavior is identical everywhere.
//
// Founder directive (2026-09-28, revised): the site keeps TWO real input
// boxes, each with a distinct job. Box 1 "Search Medicines" (Row A, next to
// Help/cart) is a plain, fast, real fuzzy product-name search (Fuse.js
// against the real medicine catalog only — no diseases, no AI). Box 2, the
// real AI-understanding natural-language box, sits directly beside the
// "BalanceAI" logo/wordmark in Row B and is the one entry point into the
// real /medical/query pipeline from every page. The symptom-checker page's
// own separate large hero textarea stays removed — Box 2 in the navbar is
// its replacement — but Box 1 was restored after being briefly removed
// earlier in this same work session, per an explicit founder correction.
// ---------------------------------------------------------------------------

function NavDropdown({
  label,
  items,
}: {
  label: string;
  items: { href: string; label: string; sub?: string }[];
}) {
  return (
    <NavigationMenu className="max-w-none">
      <NavigationMenuList>
        <NavigationMenuItem>
          <NavigationMenuTrigger
            className="!h-auto !bg-transparent !rounded-full px-3.5 py-1.5 text-xs sm:text-sm font-bold whitespace-nowrap data-[popup-open]:!bg-[rgba(14,124,134,0.08)] hover:!bg-[rgba(14,124,134,0.08)]"
            style={{ color: TEXT }}
          >
            {label}
          </NavigationMenuTrigger>
          <NavigationMenuContent className="!bg-transparent !shadow-none !ring-0 !p-0">
            <div
              className="w-72 rounded-xl p-1.5"
              style={{ background: SURFACE, border: "1px solid #E4EBEE", boxShadow: "0 16px 32px rgba(11,32,39,0.16)" }}
            >
              {items.map((item) => (
                <NavigationMenuLink
                  key={item.href}
                  render={<Link href={item.href} />}
                  className="!p-0 !rounded-lg hover:!bg-[rgba(14,124,134,0.06)]"
                >
                  <span className="block px-3 py-2.5">
                    <span className="block text-sm font-semibold" style={{ color: TEXT }}>{item.label}</span>
                    {item.sub && (
                      <span className="block text-xs mt-0.5" style={{ color: MUTED }}>{item.sub}</span>
                    )}
                  </span>
                </NavigationMenuLink>
              ))}
            </div>
          </NavigationMenuContent>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenu>
  );
}

// Real, honest example phrases for the navbar box's placeholder — rotated
// every 10s so the box demonstrates its actual real capability (English,
// Hindi and Hinglish natural-language understanding via the real
// /medical/query pipeline) rather than staying static on one example. This is
// an intentional, explicit exception to the general English-only UI copy
// rule, same as the logo tagline exception, since these placeholders exist
// specifically to show the real Hindi/Hinglish input capability.
//
// Founder directive, 2026-09-28: this is a disease-NAME lookup AI, not a
// symptom checker -- /medical/query no longer tries to interpret a symptom
// narrative into a guessed disease (see identify_disease()'s
// redirect_to_whatsapp behavior), so every placeholder example must actually
// name a specific real condition, never describe bare symptoms with no
// disease name in them (a real bug this fixes: the old 2nd example,
// "I have had a fever and headache for 3 days...", named no disease and
// would now just bounce the user straight to the WhatsApp-a-doctor redirect
// instead of a real result).
const SYMPTOM_PLACEHOLDER_EXAMPLES = [
  "e.g. 'mujhe migraine hai, kai saalo se pareshan hoon...'",
  "e.g. 'I have gout, my toe joint swells up and hurts...'",
  "e.g. 'mujhe kai saalo se babaseer hai...'",
];

export default function SiteHeader({
  active,
  onQuickFillAndSubmit,
}: {
  active: "symptoms" | "pharmacy" | "medicines" | "wellness" | "other";
  onQuickFillAndSubmit?: (text: string) => void;
}) {
  const router = useRouter();

  // Box 1 — "Search Medicines": a plain, fast, real fuzzy product-name search
  // (Fuse.js against the real medicine catalog only — no diseases, no AI).
  // Matches the real 1mg/Netmeds pattern of a simple name search box.
  const [medQuery, setMedQuery] = useState("");
  const [medMatches, setMedMatches] = useState<MedicineMatch[]>([]);
  const [medDropdownOpen, setMedDropdownOpen] = useState(false);
  const [medHighlightedIndex, setMedHighlightedIndex] = useState(-1);
  const [medDropdownRect, setMedDropdownRect] = useState<{ top: number; right: number } | null>(null);
  const medWrapRef = useRef<HTMLDivElement>(null);
  const medDropdownRef = useRef<HTMLDivElement>(null);

  // Box 2 — the one real AI natural-language box, in any language, that
  // always routes straight to the real /medical/query pipeline. No fuzzy
  // matching happens here at all — this box's entire job is free-text
  // symptom/disease-name understanding.
  const [symptomText, setSymptomText] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setPlaceholderIndex((i) => (i + 1) % SYMPTOM_PLACEHOLDER_EXAMPLES.length), 10000);
    return () => clearInterval(id);
  }, []);

  const cartCount = useCartStore((s) => s.items.length);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      const insideWrap = medWrapRef.current && medWrapRef.current.contains(target);
      const insideDropdown = medDropdownRef.current && medDropdownRef.current.contains(target);
      if (!insideWrap && !insideDropdown) {
        setMedDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleMedFocus() {
    ensureSearchIndex();
  }

  // Row A (the top nav-link strip Box 1 lives in) has overflow-x-auto for its
  // horizontal nav-link scrolling on narrow screens — CSS forces overflow-y
  // to also clip whenever overflow-x is non-visible, which silently clips
  // this dropdown into invisibility if rendered inline. Fixed by rendering
  // the dropdown through a React portal straight onto document.body with
  // position:fixed, positioned from the real input's getBoundingClientRect()
  // — so it fully escapes the clipping ancestor instead of being hidden
  // inside it.
  function updateMedDropdownRect() {
    const rect = medWrapRef.current?.getBoundingClientRect();
    if (rect) setMedDropdownRect({ top: rect.bottom + 8, right: window.innerWidth - rect.right });
  }

  function handleMedChange(value: string) {
    setMedQuery(value);
    setMedHighlightedIndex(-1);
    // Devanagari/Hindi-script input can't be meaningfully fuzzy-matched
    // against our English-only medicine names — this box is a plain product
    // search, so it correctly shows "no results" rather than guessing.
    if (value.trim().length < 2 || isNonLatinScript(value)) {
      setMedMatches([]);
      setMedDropdownOpen(false);
      return;
    }
    ensureSearchIndex().then(() => {
      setMedMatches(searchMedicines(value, 6));
      updateMedDropdownRect();
      setMedDropdownOpen(true);
    });
  }

  function pickMedicine(m: MedicineMatch) {
    setMedDropdownOpen(false);
    setMedQuery("");
    router.push(`/medicines/${encodeURIComponent(m.slug)}`);
  }

  // No AI fallback here at all — if there's a real top match, go straight to
  // it; if there isn't, the dropdown's own "No results found" state already
  // told the user that, and pressing Enter does nothing further.
  function handleMedSubmit() {
    const q = medQuery.trim();
    if (!q) return;
    if (medMatches.length > 0) {
      pickMedicine(medMatches[0]);
    }
  }

  function handleMedKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && medHighlightedIndex >= 0 && medMatches[medHighlightedIndex]) {
      e.preventDefault();
      pickMedicine(medMatches[medHighlightedIndex]);
      return;
    }
    if (!medDropdownOpen || medMatches.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setMedHighlightedIndex((i) => (i + 1) % medMatches.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setMedHighlightedIndex((i) => (i <= 0 ? medMatches.length - 1 : i - 1));
    } else if (e.key === "Escape") {
      setMedDropdownOpen(false);
      setMedHighlightedIndex(-1);
    }
  }

  // Real submit action for the one navbar input, and for the Row C
  // quick-link category buttons: if the calling page already provides
  // in-place handling (currently only the symptom-checker page, via
  // onQuickFillAndSubmit), use that so the query is answered without leaving
  // the page; otherwise navigate to /symptom-checker with the query
  // pre-filled and immediately auto-submitted.
  function goToSymptomCheckerAutoSubmit(text: string) {
    if (onQuickFillAndSubmit) {
      onQuickFillAndSubmit(text);
      return;
    }
    router.push(`/symptom-checker?q=${encodeURIComponent(text)}&autoSubmit=1`);
  }

  function handleSymptomSubmit() {
    const q = symptomText.trim();
    if (!q) return;
    goToSymptomCheckerAutoSubmit(q);
  }

  return (
    <header className="sticky top-0 z-50 w-full">
      {/* Utility strip — bold solid-color commercial strip (matches Netmeds/1mg
          announcement-bar convention) */}
      <div
        style={{ background: TEAL, color: "#FFFFFF", height: 34 }}
        className="w-full flex items-center justify-center text-center text-xs font-semibold px-4"
      >
        🔒 Your privacy matters to us · Medical emergency? Call 108 immediately
      </div>

      <div style={{ background: SURFACE }}>
        {/* Row A — primary nav strip */}
        <div className="w-full border-b" style={{ borderColor: "#E4EBEE" }}>
          <div
            className="max-w-6xl mx-auto px-4 h-11 flex items-center gap-3 text-xs sm:text-sm font-bold overflow-x-auto [&::-webkit-scrollbar]:hidden"
            style={{ scrollbarWidth: "none" }}
          >
            <Link
              href="/"
              className="pb-[13px] whitespace-nowrap"
              style={{ color: TEXT }}
            >
              Nutrient Scan
            </Link>
            <Link
              href="/symptom-checker"
              className="pb-[13px] whitespace-nowrap"
              style={
                active === "symptoms"
                  ? { color: TEAL, borderBottom: `2px solid ${TEAL}` }
                  : { color: TEXT }
              }
            >
              Find Treatment
            </Link>
            <NavDropdown
              label="Medicines"
              items={[
                { href: "/medicines", label: `Browse Full Catalog`, sub: `Thousands of real medicines, searchable and filterable` },
                { href: "/pharmacy", label: "Order Medicine", sub: "Describe your problem, get matched medicines and check out" },
                { href: "/medicines/by-category", label: "Browse by Health Area", sub: "Fever, skin, joints, women's health & more" },
              ]}
            />
            <NavDropdown
              label="Wellness"
              items={[
                { href: "/wellness#sexual-wellness", label: "Sexual Wellness", sub: "Real contraception and sexual-health items" },
                { href: "/wellness#vitamins-supplements", label: "Vitamins & Supplements", sub: "Vitamins, calcium, iron, omega-3 and zinc" },
                { href: "/wellness#personal-care", label: "Personal Care", sub: "Medicated shampoos, lotions and sun protection" },
                { href: "/wellness#womens-health", label: "Women's Health", sub: "PCOS, menopause and women-specific conditions" },
                { href: "/wellness#mom-baby-care", label: "Mom & Baby Care", sub: "Pregnancy, neonatal and paediatric treatments" },
              ]}
            />
            <a
              href="/symptom-checker#how-it-works"
              style={{ color: TEXT }}
              className="hidden md:inline whitespace-nowrap transition-colors duration-200 hover:text-[#0E7C86]"
            >
              How It Works
            </a>
            <NavDropdown
              label="Help"
              items={[
                { href: "/symptom-checker#faq", label: "FAQ" },
                { href: "/legal/privacy-policy", label: "Privacy Policy" },
                { href: "/legal/terms-of-service", label: "Terms of Service" },
                { href: "/legal/medical-disclaimer", label: "Medical Disclaimer" },
              ]}
            />

            {/* Box 1 — Search Medicines (plain fuzzy product-name search, no
                AI). Compact, placed right beside Help in the top nav row —
                deliberately small and separate from Box 2 (the real AI input)
                beside the logo in Row B below. */}
            <div ref={medWrapRef} className="hidden lg:block relative w-32 xl:w-36 shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleMedSubmit();
                }}
                className="flex items-center gap-1.5 rounded-full h-7 px-3 transition-shadow duration-200 focus-within:ring-2"
                style={{ background: BG, border: "1px solid #E4EBEE" }}
              >
                <Search className="w-3 h-3 shrink-0" style={{ color: MUTED }} />
                <input
                  value={medQuery}
                  onChange={(e) => handleMedChange(e.target.value)}
                  onFocus={handleMedFocus}
                  onKeyDown={handleMedKeyDown}
                  placeholder="Search medicines..."
                  className="flex-1 min-w-0 bg-transparent outline-none text-xs font-normal"
                  style={{ color: TEXT }}
                  role="combobox"
                  aria-expanded={medDropdownOpen}
                  aria-autocomplete="list"
                />
              </form>

              {medDropdownOpen && medDropdownRect && typeof document !== "undefined" && createPortal(
                <div
                  ref={medDropdownRef}
                  className="fixed w-72 rounded-xl overflow-hidden z-[100] max-h-96 overflow-y-auto"
                  style={{
                    top: medDropdownRect.top,
                    right: medDropdownRect.right,
                    background: SURFACE,
                    border: "1px solid #E4EBEE",
                    boxShadow: "0 16px 32px rgba(11,32,39,0.16)",
                  }}
                >
                  {medMatches.length > 0 ? (
                    <div className="py-1.5">
                      {medMatches.map((m, idx) => {
                        const active = idx === medHighlightedIndex;
                        return (
                          <button
                            key={m.slug}
                            type="button"
                            onClick={() => pickMedicine(m)}
                            onMouseEnter={() => setMedHighlightedIndex(idx)}
                            className="w-full flex items-center gap-2.5 text-left px-4 py-2 text-sm transition-colors duration-150"
                            style={{ color: TEXT, background: active ? "rgba(14,124,134,0.08)" : "transparent" }}
                          >
                            <Pill className="w-3.5 h-3.5 shrink-0" style={{ color: TEAL }} />
                            <span className="truncate">{m.displayName}</span>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="px-4 py-3 text-sm" style={{ color: MUTED }}>
                      No medicines found for &quot;{medQuery.trim()}&quot;.
                    </p>
                  )}
                </div>,
                document.body
              )}
            </div>

            <Link href="/pharmacy/cart" aria-label="View cart" className="relative shrink-0 transition-transform duration-200 hover:scale-110">
              <ShoppingCart className="w-4 h-4" style={{ color: TEXT }} />
              {cartCount > 0 && (
                <span
                  className="absolute -top-2 -right-2 text-[9px] font-bold rounded-full w-3.5 h-3.5 flex items-center justify-center"
                  style={{ background: BLUE, color: "#fff" }}
                >
                  {cartCount}
                </span>
              )}
            </Link>

            <span className="ml-auto flex items-center gap-5 shrink-0">
              <span
                className="cursor-pointer transition-colors duration-200 hover:text-[#0E7C86]"
                style={{ color: TEXT }}
                title="Login/Sign Up is not implemented yet — placeholder only"
              >
                Login | Signup
              </span>
            </span>
          </div>
        </div>

        {/* Row B — logo + Box 2, the real AI-understanding input, positioned
            directly beside the "BalanceAI" wordmark.
            Real bug found and fixed here, 2026-09-28: Box 2 was
            `hidden sm:block`, and the symptom-checker page's own separate
            hero textarea was deliberately removed in favour of this single
            navbar box being the one real entry point into /medical/query
            everywhere -- so below the sm breakpoint (640px, i.e. on
            virtually every real phone in portrait mode) there was no way at
            all to type a symptom and use the core feature of the site. Row B
            now stacks the logo above the input on narrow screens (flex-col,
            switching to flex-row at sm:) instead of hiding the input. */}
        <div className="w-full border-b" style={{ borderColor: "#E4EBEE" }}>
          <div className="max-w-6xl mx-auto px-4 py-3 sm:h-20 sm:py-0 flex flex-col sm:flex-row sm:items-center gap-3">
            <Link href="/" className="flex items-center gap-2 shrink-0" style={{ color: TEXT }}>
              {/* eslint-disable-next-line @next/next/no-img-element -- static local vector brand mark */}
              <img src="/illustrations/brand-mark.svg" alt="" aria-hidden="true" className="w-8 h-8 shrink-0" />
              <span className="flex items-baseline gap-1.5">
                <span className="font-display font-extrabold text-xl">
                  Balance<span style={{ color: TEAL }}>AI</span>
                </span>
                <span className="text-[8px] font-bold uppercase tracking-wide whitespace-nowrap" style={{ color: TEAL }}>
                  (Medical Research)
                </span>
              </span>
            </Link>

            {/* Box 2 — the real AI /medical/query input, everywhere, right
                next to the logo. Visible at every width (see fix note
                above) -- stacked below the logo on mobile, inline on sm+. */}
            <div className="flex-1 relative min-w-0">
              <p className="absolute -top-3.5 left-4 text-[9px] font-bold uppercase tracking-wide px-1 flex items-center gap-1" style={{ color: TEAL, background: SURFACE }}>
                <Sparkles className="w-2.5 h-2.5" /> Find the Right Treatment
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSymptomSubmit();
                }}
                className="flex items-center gap-2 rounded-full h-11 pl-4 pr-1.5 transition-shadow duration-200 focus-within:ring-2"
                style={{ background: "rgba(14,124,134,0.05)", border: `1px solid rgba(14,124,134,0.35)` }}
              >
                <Sparkles className="w-4 h-4 shrink-0" style={{ color: TEAL }} />
                <input
                  value={symptomText}
                  onChange={(e) => setSymptomText(e.target.value)}
                  placeholder={SYMPTOM_PLACEHOLDER_EXAMPLES[placeholderIndex]}
                  className="flex-1 min-w-0 bg-transparent outline-none text-sm"
                  style={{ color: TEXT }}
                />
                <button
                  type="submit"
                  aria-label="Check symptoms with AI"
                  className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white transition-transform duration-200 hover:-translate-y-0.5"
                  style={{ background: HERO_GRADIENT }}
                >
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Row C — secondary quick-link row, our real symptom categories.
            Since the one real input box always auto-submits immediately
            (there's no separate page-level box left to prefill for editing),
            these quick-links go straight through the same real
            /medical/query auto-submit path. */}
        <div className="w-full border-b" style={{ borderColor: "#E4EBEE" }}>
          <div
            className="max-w-6xl mx-auto px-4 h-10 flex items-center gap-6 text-xs font-semibold overflow-x-auto [&::-webkit-scrollbar]:hidden"
            style={{ scrollbarWidth: "none" }}
          >
            {CATEGORY_TILES.map(({ label, starter }) => (
              <button
                key={label}
                onClick={() => goToSymptomCheckerAutoSubmit(starter)}
                className="whitespace-nowrap transition-colors duration-200 hover:text-[#0E7C86]"
                style={{ color: MUTED }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}
