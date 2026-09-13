"use client";

import { useRef } from "react";
import { motion } from "framer-motion";
import { Share2, Download, X } from "lucide-react";
import type { AnalysisEntry } from "@/lib/db";
import { DEFICIENCY_LABELS } from "@/lib/api";
import { scoreColor } from "@/lib/db";

interface Props {
  analysis: AnalysisEntry;
  onClose: () => void;
}

export default function ShareCard({ analysis, onClose }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const drawCard = (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const canvas = canvasRef.current;
      if (!canvas) return resolve(null);
      canvas.width = 720;
      canvas.height = 720;
      const ctx = canvas.getContext("2d")!;

      // Background
      ctx.fillStyle = "#06060a";
      ctx.fillRect(0, 0, 720, 720);

      // Top green gradient strip
      const grad = ctx.createLinearGradient(0, 0, 720, 0);
      grad.addColorStop(0, "rgba(0,217,126,0.25)");
      grad.addColorStop(1, "rgba(6,182,212,0.1)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 720, 6);

      // Logo area
      ctx.fillStyle = "#00d97e";
      roundRect(ctx, 48, 52, 48, 48, 12);
      ctx.fill();
      ctx.fillStyle = "#000";
      ctx.font = "bold 24px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("B", 72, 83);

      ctx.fillStyle = "rgba(255,255,255,0.9)";
      ctx.font = "bold 20px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText("BalanceAI", 112, 78);

      // Score circle
      const cx = 360, cy = 300, r = 120;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255,255,255,0.06)";
      ctx.lineWidth = 16;
      ctx.stroke();

      const pct = analysis.score / 100;
      const color = scoreColor(analysis.score);
      ctx.beginPath();
      ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + pct * Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 16;
      ctx.lineCap = "round";
      ctx.stroke();

      ctx.fillStyle = color;
      ctx.font = "bold 72px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(String(analysis.score), cx, cy + 24);
      ctx.fillStyle = "rgba(255,255,255,0.4)";
      ctx.font = "16px sans-serif";
      ctx.fillText(analysis.score_label, cx, cy + 52);

      // Deficiency chips
      const risks = [
        ...analysis.high_risk.map((d) => ({ key: d, level: "high" })),
        ...analysis.medium_risk.slice(0, 4).map((d) => ({ key: d, level: "medium" })),
      ].slice(0, 6);

      let chipX = 72, chipY = 480;
      risks.forEach(({ key, level }) => {
        const label = DEFICIENCY_LABELS[key] || key;
        const chipColor = level === "high" ? "#ef4444" : "#f59e0b";
        ctx.font = "13px sans-serif";
        const w = ctx.measureText(label).width + 24;
        roundRect(ctx, chipX, chipY, w, 28, 8);
        ctx.fillStyle = `${chipColor}18`;
        ctx.fill();
        ctx.strokeStyle = `${chipColor}45`;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = chipColor;
        ctx.textAlign = "center";
        ctx.fillText(label, chipX + w / 2, chipY + 18);
        chipX += w + 10;
        if (chipX > 600) { chipX = 72; chipY += 40; }
      });

      // Footer
      ctx.fillStyle = "rgba(255,255,255,0.2)";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("balanceai.app  ·  Free nutrition check, no blood test", 360, 680);

      canvas.toBlob((b) => resolve(b), "image/png");
    });
  };

  const handleDownload = async () => {
    const blob = await drawCard();
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `balanceai_score_${analysis.score}.png`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    const blob = await drawCard();
    if (!blob) return;
    const file = new File([blob], "balanceai_result.png", { type: "image/png" });
    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({ files: [file], title: "My BalanceAI Result", text: `Mera nutrition score: ${analysis.score}/100. Free check karo!` });
    } else {
      handleDownload();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[80] flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.8)" }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 24 }}
        className="rounded-2xl p-5 space-y-4 max-w-sm w-full"
        style={{ background: "#0e0e16", border: "1px solid rgba(255,255,255,0.08)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <p className="text-sm font-bold" style={{ color: "rgba(255,255,255,0.85)" }}>Share Card</p>
          <button onClick={onClose} style={{ color: "rgba(255,255,255,0.3)" }}><X className="w-4 h-4" /></button>
        </div>

        <canvas
          ref={canvasRef}
          className="w-full rounded-xl"
          style={{ aspectRatio: "1/1" }}
          onMouseEnter={() => drawCard()}
        />

        <div className="flex gap-3">
          <button
            onClick={handleShare}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold text-black"
            style={{ background: "#00d97e" }}
          >
            <Share2 className="w-4 h-4" /> Share
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium"
            style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.6)" }}
          >
            <Download className="w-4 h-4" /> Save
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}
