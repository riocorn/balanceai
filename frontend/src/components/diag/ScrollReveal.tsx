"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

let pluginRegistered = false;

// GSAP + ScrollTrigger stagger-reveal wrapper — animates each direct child in
// once as the section scrolls into view (fade + rise). Used for category
// tiles, trust bands and card grids across the diagnostic pages so the site
// doesn't feel static, per the real e-pharmacy micro-interaction pass.
export default function ScrollReveal({
  children,
  className,
  stagger = 0.08,
  y = 24,
  start = "top 88%",
}: {
  children: React.ReactNode;
  className?: string;
  stagger?: number;
  y?: number;
  start?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!pluginRegistered) {
      gsap.registerPlugin(ScrollTrigger);
      pluginRegistered = true;
    }
    const el = ref.current;
    if (!el) return;
    const targets = Array.from(el.children);
    if (targets.length === 0) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        targets,
        { opacity: 0, y },
        {
          opacity: 1,
          y: 0,
          duration: 0.6,
          stagger,
          ease: "power2.out",
          scrollTrigger: { trigger: el, start, once: true },
        }
      );
    }, ref);

    return () => ctx.revert();
  }, [stagger, y, start]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
