"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import Link from "next/link";
import {
  Leaf, ArrowRight, Building2, Stethoscope, Users, BarChart3,
  CheckCircle2, Mail, Phone, Globe, Zap, Shield, Database,
} from "lucide-react";

const USE_CASES = [
  {
    icon: Stethoscope,
    title: "Primary Health Centres",
    desc: "Screen 100+ patients/day for nutrition deficiencies without lab infrastructure. Get instant risk flags for anaemia, B12, D3 deficiency.",
    stat: "847 patients screened · 23% cost reduction",
    color: "#00d97e",
  },
  {
    icon: Building2,
    title: "Hospital Nutrition Depts",
    desc: "Pre-admission nutrition screening. Reduce unnecessary blood panels by flagging only high-risk patients for lab tests.",
    stat: "₹1,200 avg savings per patient",
    color: "#818cf8",
  },
  {
    icon: Users,
    title: "Corporate Wellness",
    desc: "Annual nutrition health drives for employees. Anonymous aggregate reporting. Identify deficiency patterns in your workforce.",
    stat: "32% employee engagement increase",
    color: "#06b6d4",
  },
];

const API_TIERS = [
  {
    name: "Clinic",
    price: "₹999",
    period: "/month",
    desc: "For small clinics & PHCs",
    features: [
      "500 analyses/month",
      "Basic API access",
      "PDF reports",
      "Email support",
    ],
    cta: "Start Free Trial",
    highlight: false,
  },
  {
    name: "Hospital",
    price: "₹4,999",
    period: "/month",
    desc: "For hospitals & chains",
    features: [
      "Unlimited analyses",
      "Full API + webhooks",
      "Branded PDF reports",
      "ABDM integration",
      "Dedicated support",
      "Analytics dashboard",
    ],
    cta: "Schedule Demo",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "For large health systems",
    features: [
      "White-label app",
      "On-premise deployment",
      "Custom AI training",
      "EHR/HIS integration",
      "SLA guarantee",
      "24/7 support",
    ],
    cta: "Contact Sales",
    highlight: false,
  },
];

const CASE_STUDY = {
  org: "District Hospital, Himachal Pradesh",
  period: "3 months pilot, 2024",
  stats: [
    { value: "847", label: "Patients screened" },
    { value: "34%", label: "Had iron deficiency (prev. unknown)" },
    { value: "23%", label: "Reduction in unnecessary lab tests" },
    { value: "₹8.2L", label: "Cost saved for hospital" },
  ],
  quote: "BalanceAI ne hamare PHC ke kaam ko completely badal diya. Ab nurse khud initial screening kar sakti hai bina lab ke.",
  person: "Dr. Anita Sharma, Chief Medical Officer",
};

const TECH_FEATURES = [
  { icon: Zap,      title: "Real-time API",  desc: "< 300ms response, 99.9% uptime SLA" },
  { icon: Shield,   title: "HIPAA-compliant",desc: "On-device processing, zero data retention" },
  { icon: Database, title: "ABDM Ready",     desc: "Integrates with Ayushman Bharat ABDM" },
  { icon: Globe,    title: "12 Languages",   desc: "Hindi, Tamil, Telugu, Bengali + more" },
];

export default function EnterprisePage() {
  const heroRef = useRef<HTMLElement>(null);

  return (
    <div className="min-h-screen" style={{ background: "#06060a" }}>
      {/* Nav */}
      <nav
        className="flex items-center justify-between px-6 sm:px-10 h-16 border-b sticky top-0 z-40 backdrop-blur"
        style={{ borderColor: "rgba(255,255,255,0.06)", background: "rgba(6,6,10,0.92)" }}
      >
        <Link href="/">
          <div className="flex items-center gap-2.5 cursor-pointer">
            <div className="w-8 h-8 rounded-lg bg-[#00d97e] flex items-center justify-center">
              <Leaf className="w-4 h-4 text-black" />
            </div>
            <span className="font-bold text-sm text-white font-display">BalanceAI</span>
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-semibold ml-1"
              style={{ background: "rgba(129,140,248,0.12)", color: "#818cf8", border: "1px solid rgba(129,140,248,0.2)" }}
            >
              Enterprise
            </span>
          </div>
        </Link>
        <div className="flex items-center gap-3">
          <Link href="/">
            <span className="text-sm hidden sm:block" style={{ color: "rgba(255,255,255,0.4)" }}>← Back to Home</span>
          </Link>
          <a
            href="mailto:enterprise@balanceai.app"
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-black"
            style={{ background: "#00d97e" }}
          >
            <Mail className="w-3.5 h-3.5" /> Contact Sales
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section
        ref={heroRef}
        className="relative py-28 px-5 sm:px-10 text-center overflow-hidden"
      >
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: "radial-gradient(ellipse 800px 500px at 50% 0%, rgba(129,140,248,0.07) 0%, transparent 70%)",
          }}
        />
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="relative z-10 max-w-4xl mx-auto"
        >
          <div
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold mb-7"
            style={{ background: "rgba(129,140,248,0.1)", border: "1px solid rgba(129,140,248,0.2)", color: "#818cf8" }}
          >
            <Building2 className="w-3.5 h-3.5" /> For Healthcare Providers & Enterprises
          </div>
          <h1 className="land-h1 mb-6">
            AI Nutrition Screening
            <br />
            <span style={{ color: "#818cf8" }}>At Scale, Across India</span>
          </h1>
          <p className="text-lg mb-10 max-w-2xl mx-auto" style={{ color: "rgba(255,255,255,0.5)", fontFamily: "var(--font-inter)" }}>
            Deploy BalanceAI in your hospital, PHC, or wellness program.
            Screen thousands of patients daily — no lab, no blood test.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="mailto:enterprise@balanceai.app?subject=Enterprise Demo Request"
              className="flex items-center gap-2 px-7 py-3.5 rounded-xl font-bold text-sm text-black"
              style={{ background: "#00d97e", boxShadow: "0 0 32px rgba(0,217,126,0.2)" }}
            >
              Schedule a Demo <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="mailto:enterprise@balanceai.app?subject=API Access Request"
              className="flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-sm"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.65)" }}
            >
              API Documentation
            </a>
          </div>
        </motion.div>
      </section>

      {/* Use cases */}
      <section className="py-20 px-5 sm:px-10" style={{ background: "rgba(255,255,255,0.015)" }}>
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-bold uppercase tracking-widest text-center mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>
            Use Cases
          </p>
          <h2 className="text-2xl font-bold text-center mb-12 font-display" style={{ color: "rgba(255,255,255,0.9)" }}>
            Built for Healthcare at Every Level
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {USE_CASES.map((u, i) => (
              <motion.div
                key={u.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="rounded-2xl p-6"
                style={{ background: `${u.color}06`, border: `1px solid ${u.color}18` }}
              >
                <u.icon className="w-6 h-6 mb-4" style={{ color: u.color }} />
                <h3 className="text-sm font-bold mb-2" style={{ color: "rgba(255,255,255,0.85)" }}>{u.title}</h3>
                <p className="text-xs leading-relaxed mb-4" style={{ color: "rgba(255,255,255,0.5)" }}>{u.desc}</p>
                <div
                  className="text-[10px] font-semibold px-2.5 py-1 rounded-full inline-block"
                  style={{ background: `${u.color}12`, color: u.color, border: `1px solid ${u.color}25` }}
                >
                  {u.stat}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Case study */}
      <section className="py-20 px-5 sm:px-10">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-bold uppercase tracking-widest text-center mb-12" style={{ color: "rgba(255,255,255,0.3)" }}>
            Case Study
          </p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-2xl p-8"
            style={{ background: "rgba(0,217,126,0.03)", border: "1px solid rgba(0,217,126,0.12)" }}
          >
            <div className="flex flex-col sm:flex-row items-start justify-between gap-6 mb-8">
              <div>
                <h3 className="text-lg font-bold mb-1" style={{ color: "rgba(255,255,255,0.9)" }}>
                  {CASE_STUDY.org}
                </h3>
                <p className="text-xs" style={{ color: "rgba(255,255,255,0.35)" }}>{CASE_STUDY.period}</p>
              </div>
              <div
                className="text-xs px-3 py-1.5 rounded-full font-semibold"
                style={{ background: "rgba(0,217,126,0.1)", color: "#00d97e", border: "1px solid rgba(0,217,126,0.2)" }}
              >
                Pilot Complete ✓
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
              {CASE_STUDY.stats.map((s) => (
                <div key={s.label} className="text-center">
                  <div className="text-2xl font-black font-display mb-0.5" style={{ color: "#00d97e" }}>{s.value}</div>
                  <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.4)" }}>{s.label}</p>
                </div>
              ))}
            </div>

            <blockquote
              className="text-sm leading-relaxed italic border-l-2 pl-4"
              style={{ color: "rgba(255,255,255,0.65)", borderColor: "rgba(0,217,126,0.4)" }}
            >
              "{CASE_STUDY.quote}"
            </blockquote>
            <p className="text-xs mt-2 ml-4" style={{ color: "rgba(255,255,255,0.3)" }}>— {CASE_STUDY.person}</p>
          </motion.div>
        </div>
      </section>

      {/* Tech features */}
      <section className="py-20 px-5 sm:px-10" style={{ background: "rgba(255,255,255,0.015)" }}>
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-10 font-display" style={{ color: "rgba(255,255,255,0.9)" }}>
            Enterprise-Grade Technology
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {TECH_FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, x: i % 2 === 0 ? -12 : 12 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06 }}
                className="flex items-start gap-4 p-5 rounded-2xl"
                style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: "rgba(0,217,126,0.08)", border: "1px solid rgba(0,217,126,0.15)" }}
                >
                  <f.icon className="w-4.5 h-4.5" style={{ color: "#00d97e" }} />
                </div>
                <div>
                  <p className="text-sm font-semibold mb-0.5" style={{ color: "rgba(255,255,255,0.85)" }}>{f.title}</p>
                  <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-5 sm:px-10">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-bold uppercase tracking-widest text-center mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>
            Pricing
          </p>
          <h2 className="text-2xl font-bold text-center mb-12 font-display" style={{ color: "rgba(255,255,255,0.9)" }}>
            Transparent, Usage-Based
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {API_TIERS.map((tier, i) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="rounded-2xl p-6 flex flex-col"
                style={{
                  background: tier.highlight ? "rgba(0,217,126,0.05)" : "rgba(255,255,255,0.025)",
                  border: tier.highlight ? "1px solid rgba(0,217,126,0.25)" : "1px solid rgba(255,255,255,0.07)",
                }}
              >
                {tier.highlight && (
                  <div
                    className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full self-start mb-4"
                    style={{ background: "rgba(0,217,126,0.12)", color: "#00d97e", border: "1px solid rgba(0,217,126,0.2)" }}
                  >
                    Most Popular
                  </div>
                )}
                <p className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: "rgba(255,255,255,0.35)" }}>
                  {tier.name}
                </p>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-3xl font-black font-display" style={{ color: "rgba(255,255,255,0.9)" }}>
                    {tier.price}
                  </span>
                  {tier.period && <span className="text-sm" style={{ color: "rgba(255,255,255,0.4)" }}>{tier.period}</span>}
                </div>
                <p className="text-xs mb-5" style={{ color: "rgba(255,255,255,0.35)" }}>{tier.desc}</p>
                <ul className="space-y-2 flex-1 mb-6">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-xs" style={{ color: "rgba(255,255,255,0.6)" }}>
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" style={{ color: "#00d97e" }} /> {f}
                    </li>
                  ))}
                </ul>
                <a
                  href="mailto:enterprise@balanceai.app"
                  className="flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold text-center"
                  style={{
                    background: tier.highlight ? "#00d97e" : "rgba(255,255,255,0.06)",
                    color: tier.highlight ? "#000" : "rgba(255,255,255,0.65)",
                    border: tier.highlight ? "none" : "1px solid rgba(255,255,255,0.1)",
                  }}
                >
                  {tier.cta}
                </a>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section
        className="py-20 px-5 sm:px-10 text-center"
        style={{ background: "rgba(0,217,126,0.025)", borderTop: "1px solid rgba(0,217,126,0.07)" }}
      >
        <h2 className="text-2xl font-bold mb-4 font-display" style={{ color: "rgba(255,255,255,0.9)" }}>
          Ready to deploy BalanceAI in your facility?
        </h2>
        <p className="text-sm mb-8" style={{ color: "rgba(255,255,255,0.45)", fontFamily: "var(--font-inter)" }}>
          We'll set up a 30-minute live demo with your team — no commitment needed.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href="mailto:enterprise@balanceai.app?subject=Demo Request"
            className="flex items-center gap-2 px-7 py-3.5 rounded-xl font-bold text-sm text-black"
            style={{ background: "#00d97e" }}
          >
            <Mail className="w-4 h-4" /> Book a Free Demo
          </a>
          <a
            href="tel:+911800BALANCE"
            className="flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-sm"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.6)" }}
          >
            <Phone className="w-4 h-4" /> 1800-BALANCE
          </a>
        </div>
      </section>
    </div>
  );
}
