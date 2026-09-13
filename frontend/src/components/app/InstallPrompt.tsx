"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, X } from "lucide-react";

export default function InstallPrompt() {
  const [prompt, setPrompt] = useState<any>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem("pwa_install_dismissed")) return;
    const handler = (e: any) => { e.preventDefault(); setPrompt(e); };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstall = async () => {
    if (!prompt) return;
    prompt.prompt();
    await prompt.userChoice;
    setPrompt(null);
  };

  const handleDismiss = () => {
    localStorage.setItem("pwa_install_dismissed", "1");
    setDismissed(true);
  };

  const visible = !!prompt && !dismissed;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 80 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 80 }}
          transition={{ type: "spring", stiffness: 320, damping: 28 }}
          className="fixed bottom-6 left-4 right-4 sm:left-auto sm:right-5 sm:w-80 z-[65] flex items-center gap-3 px-4 py-3.5 rounded-2xl shadow-2xl"
          style={{
            background: "#0e0e16",
            border: "1px solid rgba(0,217,126,0.2)",
            boxShadow: "0 0 30px rgba(0,217,126,0.1)",
          }}
        >
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: "rgba(0,217,126,0.12)", border: "1px solid rgba(0,217,126,0.25)" }}
          >
            <Download className="w-4.5 h-4.5" style={{ color: "#00d97e" }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold" style={{ color: "rgba(255,255,255,0.85)" }}>
              App Install Karo
            </p>
            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.4)" }}>
              Offline bhi kaam karega, faster experience
            </p>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={handleInstall}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg text-black"
              style={{ background: "#00d97e" }}
            >
              Install
            </button>
            <button onClick={handleDismiss} className="p-1 rounded-lg" style={{ color: "rgba(255,255,255,0.3)" }}>
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
