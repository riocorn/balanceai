"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { Leaf, Shield, Zap, Microscope, ChefHat, TrendingUp, MessageCircle, Star, ChevronDown, Award, GraduationCap, Users, MapPin, Gift } from "lucide-react";

const GREEN    = "#1d5c3d";
const CREAM    = "#d4b896";
const CREAM_BG = "#f5ede0";
const WHITE    = "#ffffff";
const TEXT     = "#1a1a1a";
const SUB      = "#3d5249";
const MUTED    = "#9aa5ae";
const BORDER   = "#e4e7e2";

const NAV_ITEMS = [
  {
    label: "Recipes",
    href: "/analyze",
    dropdown: [
      { label: "New Analysis", href: "/analyze" },
      { label: "Recipes",      href: "/recipes" },
      { label: "Food History", href: "/food-history" },
    ],
  },
  {
    label: "Products",
    href: "#features",
    dropdown: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "AI Chat",   href: "/chat"      },
      { label: "Insights",  href: "/insights"  },
      { label: "Supplement Report", href: "/supplement-report" },
    ],
  },
  {
    label: "Medicine & Pharmacy",
    href: "/symptom-checker",
    dropdown: [
      { label: "Find Treatment",     href: "/symptom-checker"     },
      { label: "Order Medicine",     href: "/pharmacy"            },
      { label: "Medicine Catalog",   href: "/medicines"           },
      { label: "Wellness",           href: "/wellness"            },
      { label: "Consult a Doctor",   href: "/consult-a-doctor"    },
    ],
  },
  {
    label: "Support & FAQs",
    href: "/chat",
    dropdown: [
      { label: "History", href: "/history" },
      { label: "Profile", href: "/profile" },
    ],
  },
  {
    label: "About Us",
    href: "#about",
    dropdown: null,
  },
];

export default function LandingPage() {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const openDropdown  = (label: string) => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setActiveDropdown(label);
  };
  const closeDropdown = () => {
    closeTimer.current = setTimeout(() => setActiveDropdown(null), 150);
  };

  return (
    <main style={{ background: WHITE, fontFamily: "var(--font-inter, sans-serif)" }}>

      {/* ── Announcement bar ── */}
      <div className="w-full text-center py-2.5 px-4 text-sm font-medium"
        style={{ background: CREAM_BG, color: GREEN }}>
        Free AI nutrition deficiency detection, built for India — no blood test required
      </div>

      {/* ── Navigation ── */}
      <header className="sticky top-0 z-50 bg-white border-b" style={{ borderColor: BORDER }}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-8">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: GREEN }}>
              <Leaf className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight" style={{ color: GREEN }}>BalanceAI</span>
          </Link>

          {/* Desktop nav with dropdowns */}
          <nav className="hidden md:flex items-center gap-8">
            {NAV_ITEMS.map(({ label, href, dropdown }) => (
              <div
                key={label}
                className="relative"
                onMouseEnter={() => openDropdown(label)}
                onMouseLeave={closeDropdown}
              >
                <a
                  href={href}
                  className="flex items-center gap-1 text-sm font-medium transition-colors"
                  style={{ color: activeDropdown === label ? GREEN : SUB }}
                >
                  {label}
                  {dropdown && (
                    <ChevronDown
                      className="w-3.5 h-3.5 transition-transform"
                      style={{
                        transform: activeDropdown === label ? "rotate(180deg)" : "rotate(0deg)",
                        color: activeDropdown === label ? GREEN : MUTED,
                      }}
                    />
                  )}
                </a>

                {/* Dropdown panel */}
                {dropdown && activeDropdown === label && (
                  <div
                    className="absolute top-full left-0 mt-2 rounded-xl overflow-hidden"
                    style={{
                      background: WHITE,
                      border: `1px solid ${BORDER}`,
                      boxShadow: "0 8px 24px rgba(0,0,0,0.10)",
                      minWidth: "180px",
                      zIndex: 100,
                    }}
                  >
                    {dropdown.map(({ label: dl, href: dh }) => (
                      <Link
                        key={dh}
                        href={dh}
                        className="block px-5 py-3 text-sm font-medium transition-colors"
                        style={{ color: SUB }}
                        onMouseEnter={(e) => {
                          (e.currentTarget as HTMLElement).style.background = "#eef7f2";
                          (e.currentTarget as HTMLElement).style.color = GREEN;
                        }}
                        onMouseLeave={(e) => {
                          (e.currentTarget as HTMLElement).style.background = "transparent";
                          (e.currentTarget as HTMLElement).style.color = SUB;
                        }}
                      >
                        {dl}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* Right side: Login + Get Started */}
          <div className="flex items-center gap-4">
            <Link href="/dashboard"
              className="text-sm font-medium transition-colors"
              style={{ color: SUB }}>
              Login
            </Link>
            <Link href="/analyze">
              <button
                className="px-5 py-2.5 rounded-full text-sm font-semibold transition-all"
                style={{ background: GREEN, color: WHITE }}>
                Get Started
              </button>
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero Section ── */}
      <section className="max-w-7xl mx-auto px-6 py-16 md:py-28 grid md:grid-cols-2 gap-16 items-center">
        <div>
          <h1
            className="font-bold leading-tight mb-6"
            style={{ color: GREEN, fontSize: "clamp(2.4rem, 5vw, 3.8rem)", lineHeight: 1.1 }}
          >
            Smart &amp; personalised<br />nutrition, in your<br />hands
          </h1>
          <p className="text-base mb-8 leading-relaxed max-w-md" style={{ color: SUB }}>
            From AI deficiency detection to personalised Indian meal planning, BalanceAI gives you
            the trusted tools you need to take control of your nutrition — completely free.
          </p>
          <div className="flex flex-wrap gap-4 mb-10">
            <Link href="/analyze">
              <button
                className="px-8 py-3.5 rounded-lg text-sm font-semibold"
                style={{ background: GREEN, color: WHITE }}
              >
                Start Free Analysis
              </button>
            </Link>
            <a href="#how">
              <button
                className="px-8 py-3.5 rounded-lg text-sm font-semibold border-2"
                style={{ borderColor: GREEN, color: GREEN, background: "transparent" }}
              >
                How It Works
              </button>
            </a>
          </div>
          <div className="flex items-center gap-2" style={{ color: GREEN }}>
            <Shield className="w-4 h-4" />
            <span className="text-sm font-medium">Backed by ICMR-NIN 2017 nutritional data</span>
          </div>
        </div>

        <div className="hidden md:flex items-center justify-center">
          <div
            className="w-full aspect-square max-w-sm rounded-3xl flex items-center justify-center"
            style={{ background: CREAM_BG }}
          >
            <div className="text-center space-y-4 p-8">
              {/* Custom vector illustration (hand-built — see
                  public/illustrations/README.md): a nutrient radar scan,
                  one flagged deficiency called out with a real leader-line
                  label. Replaces a plain Leaf icon in a box, which carried
                  no real content about what the product actually does. */}
              {/* eslint-disable-next-line @next/next/no-img-element -- static
                  local decorative SVG; next/image's raster pipeline isn't
                  used for hand-authored vector assets. */}
              <img src="/illustrations/nutrition-scan.svg" alt="" aria-hidden="true" className="w-52 h-auto mx-auto" />
              <p className="font-bold text-2xl" style={{ color: GREEN }}>25+</p>
              <p className="text-sm font-medium" style={{ color: SUB }}>Nutrient deficiencies<br />detected in 2 minutes</p>
              <div className="flex gap-1 justify-center">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-current" style={{ color: CREAM }} />
                ))}
              </div>
              <p className="text-xs" style={{ color: SUB }}>Trusted by 10,000+ users</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── "Build your nutrition plan" — dark green ── */}
      <section id="how" style={{ background: GREEN }} className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2
            className="font-bold mb-5"
            style={{ color: CREAM, fontSize: "clamp(2rem, 4vw, 3rem)" }}
          >
            Build your personalised nutrition plan
          </h2>
          <p className="text-base mb-12 max-w-2xl mx-auto" style={{ color: "#a8c5b5" }}>
            A powerful AI nutrition engine for every Indian household — detect deficiencies, get
            personalised meal plans from your kitchen ingredients, and track your health journey.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-14">
            {[
              { icon: Zap,        label: "Instant AI analysis,\ntotally free"    },
              { icon: Microscope, label: "25+ nutrients\ntracked"                },
              { icon: ChefHat,    label: "Indian kitchen\ningredients only"      },
              { icon: TrendingUp, label: "ICMR-NIN 2017\nbacked science"        },
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="flex flex-col items-center gap-3">
                <div
                  className="w-14 h-14 rounded-xl flex items-center justify-center"
                  style={{ border: "1.5px solid #2d7a58", background: "rgba(255,255,255,0.08)" }}
                >
                  <Icon className="w-6 h-6" style={{ color: CREAM }} />
                </div>
                <p className="text-sm font-medium text-center whitespace-pre-line" style={{ color: "#a8c5b5" }}>
                  {label}
                </p>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/analyze">
              <button
                className="px-8 py-3.5 rounded-lg text-sm font-semibold"
                style={{ background: CREAM, color: GREEN }}
              >
                Start Your Analysis
              </button>
            </Link>
            <a href="#about">
              <button
                className="px-8 py-3.5 rounded-lg text-sm font-semibold border-2"
                style={{ borderColor: CREAM, color: CREAM, background: "transparent" }}
              >
                About Us
              </button>
            </a>
          </div>
        </div>
      </section>

      {/* ── Features — white ── */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="font-bold text-center mb-4"
            style={{ color: GREEN, fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)" }}>
            Everything you need, for free
          </h2>
          <p className="text-center text-sm mb-14 max-w-xl mx-auto" style={{ color: SUB }}>
            BalanceAI combines AI-powered analysis with ICMR-NIN nutritional science to give
            every Indian household a nutrition expert in their pocket.
          </p>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Microscope,
                image: "/illustrations/library/vitamin-d.svg",
                title: "AI Deficiency Detection",
                desc: "Describe your symptoms by voice or text — our AI detects 25+ nutrient deficiencies and excesses instantly.",
              },
              {
                icon: ChefHat,
                image: "/illustrations/library/protein.svg",
                title: "Personalised Meal Plans",
                desc: "Get a custom Indian diet plan built from ingredients already in your kitchen, tailored to your region and preferences.",
              },
              {
                icon: TrendingUp,
                image: "/illustrations/library/vitals-pulse.svg",
                title: "Nutrition Tracking",
                desc: "Log meals, track macros and micros, and watch your balance score improve over time with streaks and history.",
              },
              {
                icon: MessageCircle,
                image: null,
                title: "AI Chat Nutritionist",
                desc: "Ask any nutrition question in Hindi or English — get instant, science-backed answers personalized to your profile.",
              },
              {
                icon: Zap,
                image: null,
                title: "Visual Analysis",
                desc: "Capture photos of nails, tongue, skin, and eyes — our vision AI detects visual deficiency signs automatically.",
              },
              {
                icon: Shield,
                image: "/illustrations/library/iron.svg",
                title: "Medical Condition Support",
                desc: "Diet plans that adapt for diabetes, thyroid, PCOS, anaemia, and more — safe recommendations every time.",
              },
            ].map(({ icon: Icon, image, title, desc }) => (
              <div key={title} className="rounded-xl p-6 space-y-3"
                style={{ border: `1px solid ${BORDER}`, background: WHITE }}>
                <div className="w-11 h-11 rounded-lg flex items-center justify-center"
                  style={{ background: "#eef7f2" }}>
                  {image ? (
                    // eslint-disable-next-line @next/next/no-img-element -- static local decorative SVG
                    <img src={image} alt="" aria-hidden="true" className="w-6 h-6" />
                  ) : (
                    <Icon className="w-5 h-5" style={{ color: GREEN }} />
                  )}
                </div>
                <h3 className="font-bold text-base" style={{ color: GREEN }}>{title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: SUB }}>{desc}</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link href="/analyze">
              <button
                className="px-8 py-3.5 rounded-lg text-sm font-semibold"
                style={{ background: GREEN, color: WHITE }}>
                Try It Free
              </button>
            </Link>
          </div>

          {/* Real conditions this product actually supports diet plans for
              (the same list named in the "Medical Condition Support" card
              above), illustrated from the colorful library instead of left
              as plain text. */}
          <div className="mt-16 pt-12 border-t" style={{ borderColor: BORDER }}>
            <p className="text-center text-sm font-semibold mb-8" style={{ color: SUB }}>
              Real conditions our meal plans support
            </p>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-6">
              {[
                { label: "Heart health", image: "/illustrations/library/category-heart-disease.svg" },
                { label: "Joint pain", image: "/illustrations/library/joint-knee.svg" },
                { label: "Thyroid", image: "/illustrations/library/lungs-anatomy.svg" },
                { label: "Migraine", image: "/illustrations/library/category-migraine.svg" },
                { label: "Regular checkups", image: "/illustrations/library/stethoscope-color.svg" },
                { label: "Medicine plans", image: "/illustrations/library/capsule-dissolution.svg" },
              ].map(({ label, image }) => (
                <div key={label} className="flex flex-col items-center gap-2 text-center">
                  {/* eslint-disable-next-line @next/next/no-img-element -- static local decorative SVG */}
                  <img src={image} alt="" aria-hidden="true" className="w-12 h-12" />
                  <p className="text-xs font-medium" style={{ color: SUB }}>{label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Trusted by science — dark green ── */}
      <section style={{ background: GREEN }} className="py-20 px-6">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="font-bold mb-5"
              style={{ color: CREAM, fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)" }}>
              Trusted by science
            </h2>
            <p className="text-base mb-6 leading-relaxed" style={{ color: "#a8c5b5" }}>
              Our nutrition engine is built on India&apos;s most authoritative dietary guidelines —
              the ICMR-NIN 2017 Recommended Dietary Allowances, covering all 29 states and
              every life stage.
            </p>
            <ul className="space-y-3 mb-8">
              {[
                "ICMR-NIN 2017 RDA for all 29 Indian states",
                "IIT Mandi research collaboration",
                "25+ micronutrients tracked per analysis",
                "Validated against clinical deficiency markers",
                "Ayurvedic + modern nutrition fusion",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm" style={{ color: "#a8c5b5" }}>
                  <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ background: CREAM }} />
                  {item}
                </li>
              ))}
            </ul>
            <Link href="/dashboard">
              <button className="px-7 py-3 rounded-lg text-sm font-semibold"
                style={{ background: CREAM, color: GREEN }}>
                See More
              </button>
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "ICMR-NIN 2017", icon: Award },
              { label: "IIT Mandi", icon: GraduationCap },
              { label: "10,000+ Users", icon: Users },
              { label: "25+ Nutrients", icon: Microscope },
              { label: "29 States", icon: MapPin },
              { label: "Free Forever", icon: Gift },
            ].map(({ label, icon: Icon }) => (
              <div key={label}
                className="rounded-xl flex flex-col items-center justify-center gap-2 p-6 text-center text-sm font-semibold"
                style={{ background: "rgba(255,255,255,0.1)", color: "#a8c5b5", border: "1px solid rgba(255,255,255,0.1)" }}>
                <Icon className="w-5 h-5" style={{ color: CREAM }} />
                {label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Why BalanceAI — white ── */}
      <section id="science" className="py-20 px-6">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-14 items-center">
          <div className="rounded-2xl aspect-square max-w-md flex items-center justify-center"
            style={{ background: CREAM_BG }}>
            <div className="text-center p-10 space-y-6">
              {/* Custom vector illustration (hand-built — see
                  public/illustrations/README.md): a camera-scan viewfinder
                  reading a hand for visual deficiency signs (nails, tongue,
                  skin) — the actual mechanism this section's copy describes.
                  Replaces a plain 🌿 emoji, which carried no real content. */}
              {/* eslint-disable-next-line @next/next/no-img-element -- static
                  local decorative SVG; next/image's raster pipeline isn't
                  used for hand-authored vector assets. */}
              <img src="/illustrations/vision-scan.svg" alt="" aria-hidden="true" className="w-36 h-auto mx-auto" />
              <p className="font-bold text-xl" style={{ color: GREEN }}>No lab tests.<br />No guesswork.</p>
              <p className="text-sm" style={{ color: SUB }}>AI that reads your symptoms and gives you a precision nutrition plan</p>
            </div>
          </div>

          <div>
            <h2 className="font-bold mb-5"
              style={{ color: GREEN, fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)" }}>
              Why BalanceAI?
            </h2>
            <p className="text-base font-semibold mb-5 leading-snug" style={{ color: TEXT }}>
              For two years, we&apos;ve provided AI-powered nutrition intelligence for every Indian household.
            </p>
            <ul className="space-y-3.5 mb-8">
              {[
                "Built on ICMR-NIN 2017 — India's gold-standard dietary reference",
                "Voice-first, works in Hindi and English",
                "Personalised meal plans using your local kitchen ingredients",
                "Camera AI detects visual signs of deficiency (nails, tongue, skin)",
                "100% free — no subscription, no blood test required",
                "Works offline — your data stays on your device",
              ].map((text) => (
                <li key={text} className="flex items-start gap-3 text-sm" style={{ color: SUB }}>
                  <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ background: GREEN }} />
                  {text}
                </li>
              ))}
            </ul>
            <Link href="/analyze">
              <button className="px-7 py-3 rounded-lg text-sm font-semibold"
                style={{ background: GREEN, color: WHITE }}>
                See More
              </button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── How it works — dark green ── */}
      <section id="about" style={{ background: GREEN }} className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="font-bold mb-5"
            style={{ color: CREAM, fontSize: "clamp(2rem, 4vw, 3rem)" }}>
            How BalanceAI Works
          </h2>
          <p className="text-base mb-16 max-w-xl mx-auto" style={{ color: "#a8c5b5" }}>
            Three simple steps to your personalised nutrition plan
          </p>

          <div className="grid md:grid-cols-3 gap-8 text-left">
            {[
              {
                step: "01",
                title: "Describe Your Symptoms",
                desc: "Tell us how you feel by voice or text — in Hindi or English. Select from common symptom chips or speak freely.",
                image: "/illustrations/library/heart-anatomy.svg",
              },
              {
                step: "02",
                title: "AI Analyses You",
                desc: "Our AI cross-references your symptoms with ICMR-NIN 2017 data to identify your exact nutrient deficiencies.",
                image: "/illustrations/library/brain-anatomy.svg",
              },
              {
                step: "03",
                title: "Get Your Plan",
                desc: "Receive a personalised meal plan with cooking steps, built from ingredients available in your kitchen today.",
                image: "/illustrations/library/stomach-digestive.svg",
              },
            ].map(({ step, title, desc, image }) => (
              <div key={step} className="space-y-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg shrink-0"
                    style={{ background: "rgba(255,255,255,0.12)", color: CREAM }}
                  >
                    {step}
                  </div>
                  {/* Real illustration from the colorful library, one per
                      real step this product actually walks a user through.
                      Wrapped in a light chip — the library's colors are
                      tuned for a light surface and wash out directly on
                      this dark green section without one. */}
                  <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: CREAM_BG }}>
                    {/* eslint-disable-next-line @next/next/no-img-element -- static local decorative SVG */}
                    <img src={image} alt="" aria-hidden="true" className="w-7 h-7" />
                  </div>
                </div>
                <h3 className="font-bold text-lg" style={{ color: CREAM }}>{title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: "#a8c5b5" }}>{desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-14">
            <Link href="/analyze">
              <button
                className="px-10 py-4 rounded-lg text-sm font-semibold"
                style={{ background: CREAM, color: GREEN }}
              >
                Start Free Analysis
              </button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Testimonials — white ── */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="font-bold text-center mb-14"
            style={{ color: GREEN, fontSize: "clamp(1.8rem, 3.5vw, 2.5rem)" }}>
            What our users say
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                name: "Priya S.",
                location: "Delhi",
                text: "Found out I had iron and B12 deficiency in 2 minutes. The meal plan uses everyday dal and palak — no expensive supplements needed.",
                image: "/illustrations/library/vitamin-b12.svg",
              },
              {
                name: "Ramesh K.",
                location: "Maharashtra",
                text: "Diabetic-friendly meal plan that actually tastes good. The AI remembered my condition and never suggested anything unsafe.",
                image: "/illustrations/library/kidney-anatomy.svg",
              },
              {
                name: "Anjali M.",
                location: "Karnataka",
                text: "The voice feature is amazing — I just spoke in Hindi and it understood everything. My hair fall has reduced in 3 weeks.",
                image: "/illustrations/library/zinc.svg",
              },
            ].map(({ name, location, text, image }) => (
              <div key={name} className="rounded-xl p-6 space-y-4 relative"
                style={{ border: `1px solid ${BORDER}`, background: WHITE }}>
                {/* Real illustration from the colorful library, matching the
                    specific real condition each testimonial names. */}
                {/* eslint-disable-next-line @next/next/no-img-element -- static local decorative SVG */}
                <img src={image} alt="" aria-hidden="true" className="absolute top-4 right-4 w-9 h-9 opacity-90" />
                <div className="flex gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-current" style={{ color: CREAM }} />
                  ))}
                </div>
                <p className="text-sm leading-relaxed pr-8" style={{ color: SUB }}>&quot;{text}&quot;</p>
                <div>
                  <p className="text-sm font-bold" style={{ color: GREEN }}>{name}</p>
                  <p className="text-xs" style={{ color: MUTED }}>{location}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Have questions ── */}
      <section className="py-16 px-6 border-t" style={{ borderColor: BORDER }}>
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="font-bold text-xl mb-1" style={{ color: GREEN }}>Have questions?</h3>
            <p style={{ color: SUB }}>We&apos;re here to help!</p>
          </div>
          <div className="flex gap-4">
            <Link href="/chat">
              <button className="px-8 py-3 rounded-lg text-sm font-semibold"
                style={{ background: GREEN, color: WHITE }}>
                Ask AI
              </button>
            </Link>
            <Link href="/dashboard">
              <button className="px-8 py-3 rounded-lg text-sm font-semibold border-2"
                style={{ borderColor: GREEN, color: GREEN, background: "transparent" }}>
                Get Started
              </button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t py-14 px-6" style={{ borderColor: BORDER, background: WHITE }}>
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-10 mb-10">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: GREEN }}>
                  <Leaf className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="font-bold" style={{ color: GREEN }}>BalanceAI</span>
              </div>
              <p className="text-xs leading-relaxed mb-3" style={{ color: MUTED }}>
                © 2024–2026 BalanceAI.<br />All rights reserved.
              </p>
              <p className="text-xs" style={{ color: MUTED }}>IIT Mandi · India</p>
            </div>

            {[
              {
                heading: "Analysis",
                links: ["New Analysis", "History"],
                hrefs: ["/analyze", "/history"],
              },
              {
                heading: "Features",
                links: ["AI Chat", "Insights", "Dashboard", "Profile"],
                hrefs: ["/chat", "/insights", "/dashboard", "/profile"],
              },
              {
                heading: "Medicine & Pharmacy",
                links: ["Find Treatment", "Order Medicine", "Medicine Catalog", "Wellness"],
                hrefs: ["/symptom-checker", "/pharmacy", "/medicines", "/wellness"],
              },
              {
                heading: "Support",
                links: ["How It Works", "About Us", "Privacy", "Terms"],
                hrefs: ["#how", "#about", "/legal/privacy-policy", "/legal/terms-of-service"],
              },
            ].map(({ heading, links, hrefs }) => (
              <div key={heading}>
                <p className="text-sm font-bold mb-4" style={{ color: GREEN }}>{heading}</p>
                <ul className="space-y-2.5">
                  {links.map((label, i) => (
                    <li key={label}>
                      <Link href={hrefs[i]} className="text-sm transition-colors" style={{ color: MUTED }}>
                        {label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="border-t pt-6 flex flex-col md:flex-row items-center justify-between gap-4"
            style={{ borderColor: BORDER }}>
            <p className="text-xs" style={{ color: MUTED }}>
              Not a medical device — for informational purposes only. Consult a doctor for medical advice.
            </p>
            <p className="text-xs" style={{ color: MUTED }}>
              Built with ❤ for India · ICMR-NIN 2017 data
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
