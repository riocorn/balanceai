"use client";

import { useRef, useEffect, useState } from "react";
import { motion, useInView } from "framer-motion";

const BIG_STATS = [
  { end: 240000, suffix: "+", label: "Analyses Run",       format: (n: number) => n >= 1000 ? `${(n/1000).toFixed(0)}K` : String(n) },
  { end: 91,     suffix: "%", label: "Detection Accuracy", format: (n: number) => String(n) },
  { end: 28,     suffix: "",  label: "Indian States",      format: (n: number) => String(n) },
  { end: 0,      suffix: "₹", label: "Cost, Always Free",  format: (_: number) => "0" },
];

const TICKER_ITEMS = [
  "Priya from Mumbai detected Iron deficiency · 2 min ago",
  "Ramesh from Lucknow completed his weekly analysis · 5 min ago",
  "Sunita from Jaipur improved her score by 12 points · 8 min ago",
  "Arjun from Bengaluru detected Vitamin D deficiency · 11 min ago",
  "Meera from Delhi completed her first analysis · 14 min ago",
  "Vikram from Hyderabad detected B12 deficiency · 17 min ago",
  "Anjali from Pune improved her nutrition streak to 7 days · 20 min ago",
  "Kiran from Chennai shared her results · 22 min ago",
];

function CountUp({ end, format }: { end: number; format: (n: number) => string }) {
  const [val, setVal] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  useEffect(() => {
    if (!inView) return;
    const duration = 1800;
    const steps = 60;
    const inc = end / steps;
    let cur = 0;
    const timer = setInterval(() => {
      cur = Math.min(cur + inc, end);
      setVal(Math.round(cur));
      if (cur >= end) clearInterval(timer);
    }, duration / steps);
    return () => clearInterval(timer);
  }, [inView, end]);

  return <span ref={ref}>{format(val)}</span>;
}

export default function StatsSection() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const [tickerOffset, setTickerOffset] = useState(0);
  const tickerRef = useRef<number>(0);

  useEffect(() => {
    let raf: number;
    const speed = 0.4;
    const step = () => {
      tickerRef.current -= speed;
      setTickerOffset(tickerRef.current);
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, []);

  const repeated = [...TICKER_ITEMS, ...TICKER_ITEMS, ...TICKER_ITEMS];
  const singleWidth = TICKER_ITEMS.length * 320;
  const offset = ((tickerRef.current % singleWidth) + singleWidth) % singleWidth;

  return (
    <section
      ref={ref}
      className="relative py-20 overflow-hidden"
      style={{ background: "rgba(0,217,126,0.025)", borderTop: "1px solid rgba(0,217,126,0.07)", borderBottom: "1px solid rgba(0,217,126,0.07)" }}
    >
      {/* Big stats row */}
      <div className="max-w-6xl mx-auto px-5 sm:px-8 mb-12">
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-xs font-bold uppercase tracking-widest text-center mb-10"
          style={{ color: "rgba(0,217,126,0.6)" }}
        >
          Live Platform Stats
        </motion.p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {BIG_STATS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.08, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="text-center py-8 px-4 rounded-2xl"
              style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <div className="text-4xl sm:text-5xl font-black font-display mb-1" style={{ color: "#00d97e" }}>
                <CountUp end={s.end} format={s.format} />{s.suffix}
              </div>
              <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>{s.label}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Live activity ticker */}
      <div className="relative overflow-hidden" style={{ borderTop: "1px solid rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="py-3 flex items-center gap-3 px-5">
          <div className="flex items-center gap-1.5 shrink-0 mr-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00d97e] animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "rgba(0,217,126,0.7)" }}>Live</span>
          </div>
        </div>
        <div
          className="flex gap-0 whitespace-nowrap"
          style={{ transform: `translateX(-${offset % (singleWidth)}px)`, willChange: "transform" }}
        >
          {repeated.map((item, i) => (
            <div
              key={i}
              className="inline-flex items-center gap-2 shrink-0 px-6 py-2"
              style={{ minWidth: 320 }}
            >
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: "rgba(0,217,126,0.5)" }} />
              <span className="text-xs" style={{ color: "rgba(255,255,255,0.38)" }}>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
