import { DEFICIENCY_LABELS } from "@/lib/api";
import type { DeficiencyResult, Recommendation } from "@/lib/api";

interface PDFData {
  score: number;
  score_label: string;
  predictions: DeficiencyResult[];
  diet_plan: Record<string, string[]>;
  recommendations: Recommendation[];
  alerts: string[];
  date: string;
  state?: string;
}

type RGB = [number, number, number];

const RISK_RGB: Record<string, RGB> = {
  high: [239, 68, 68],
  medium: [245, 158, 11],
  low: [34, 197, 94],
};

function scoreRGB(score: number): RGB {
  return score >= 70 ? [34, 197, 94] : score >= 40 ? [245, 158, 11] : [239, 68, 68];
}

const MEAL_LABEL: Record<string, string> = {
  breakfast: "Breakfast", lunch: "Lunch", snacks: "Snacks", dinner: "Dinner",
};

export async function generatePDF(data: PDFData): Promise<void> {
  const { default: jsPDF } = await import("jspdf");

  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const W = 210;
  const M = 18;
  const COL = W - M * 2;
  let y = 0;

  const setRGB = (rgb: RGB) => doc.setTextColor(rgb[0], rgb[1], rgb[2]);
  const gray = (v: number) => doc.setTextColor(v, v, v);
  const fillRGB = (rgb: RGB, a = 1) => {
    const blend = rgb.map((c) => Math.round(c * a + 255 * (1 - a))) as RGB;
    doc.setFillColor(blend[0], blend[1], blend[2]);
  };
  const hRule = () => {
    doc.setDrawColor(220, 220, 220);
    doc.setLineWidth(0.2);
    doc.line(M, y, W - M, y);
    y += 2;
  };

  // ── Header bar ───────────────────────────────────────────
  doc.setFillColor(6, 6, 10);
  doc.rect(0, 0, W, 30, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(17);
  doc.setTextColor(0, 217, 126);
  doc.text("BalanceAI", M, 13);

  doc.setFontSize(8);
  doc.setTextColor(190, 190, 190);
  doc.text("Nutrition Deficiency Report", M, 20);
  doc.setFont("helvetica", "normal");
  doc.text(`Generated: ${data.date}${data.state ? "  ·  " + data.state : ""}`, M, 26);

  y = 40;

  // ── Score box ────────────────────────────────────────────
  const sc = data.score;
  const sRGB = scoreRGB(sc);
  fillRGB(sRGB, 0.07);
  doc.roundedRect(M, y, COL, 38, 4, 4, "F");
  doc.setDrawColor(sRGB[0], sRGB[1], sRGB[2]);
  doc.setLineWidth(0.4);
  doc.roundedRect(M, y, COL, 38, 4, 4, "S");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(38);
  setRGB(sRGB);
  doc.text(`${sc}`, M + 10, y + 26);
  doc.setFontSize(11);
  gray(140);
  doc.text("/100", M + 28, y + 26);

  doc.setFontSize(13);
  setRGB(sRGB);
  doc.text(data.score_label, M + 50, y + 18);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8.5);
  gray(130);
  doc.text("Nutrition Balance Score", M + 50, y + 26);

  const hi = data.predictions.filter((p) => p.risk_level === "high").length;
  const med = data.predictions.filter((p) => p.risk_level === "medium").length;
  doc.setFontSize(7.5);
  doc.setTextColor(239, 68, 68);
  doc.text(`${hi} High Risk`, M + 50, y + 34);
  doc.setTextColor(245, 158, 11);
  doc.text(`${med} Medium Risk`, M + 80, y + 34);

  y += 48;

  // ── Alerts ───────────────────────────────────────────────
  data.alerts.forEach((alert) => {
    const str = typeof alert === "string" ? alert : (alert as any)?.message || "";
    if (!str) return;
    doc.setFillColor(255, 243, 205);
    doc.roundedRect(M, y, COL, 11, 2, 2, "F");
    doc.setFontSize(7.5);
    gray(80);
    doc.text(`⚠  ${str}`, M + 3, y + 7, { maxWidth: COL - 6 });
    y += 14;
  });

  // ── Deficiency Analysis ──────────────────────────────────
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  gray(35);
  doc.text("Deficiency Analysis", M, y);
  y += 4;
  hRule();

  const drawGroup = (preds: DeficiencyResult[], title: string, color: RGB) => {
    if (!preds.length) return;
    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.5);
    setRGB(color);
    doc.text(title, M, y);
    y += 5;

    preds.forEach((p) => {
      if (y > 272) { doc.addPage(); y = 22; }
      const label = DEFICIENCY_LABELS[p.deficiency] || p.deficiency;
      const pct = Math.round(p.probability * 100);
      const BAR_X = M + 78;
      const BAR_W = 84;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      gray(70);
      doc.text(label, M + 3, y);

      doc.setFillColor(225, 225, 225);
      doc.rect(BAR_X, y - 3.2, BAR_W, 2.8, "F");
      doc.setFillColor(color[0], color[1], color[2]);
      doc.rect(BAR_X, y - 3.2, BAR_W * (pct / 100), 2.8, "F");

      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.5);
      setRGB(color);
      doc.text(`${pct}%`, BAR_X + BAR_W + 3, y);
      y += 5.5;
    });
    y += 2;
  };

  drawGroup(data.predictions.filter((p) => p.risk_level === "high"), "HIGH RISK", RISK_RGB.high);
  drawGroup(data.predictions.filter((p) => p.risk_level === "medium"), "MEDIUM RISK", RISK_RGB.medium);
  drawGroup(data.predictions.filter((p) => p.risk_level === "low"), "LOW RISK", RISK_RGB.low);

  // ── Page 2: Diet + Recommendations ──────────────────────
  doc.addPage();
  y = 18;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.setTextColor(0, 217, 126);
  doc.text("BalanceAI", M, 12);
  gray(180);
  doc.setFontSize(7.5);
  doc.setFont("helvetica", "normal");
  doc.text(`Page 2  ·  ${data.date}`, W - M - 35, 12);

  if (Object.keys(data.diet_plan).length > 0) {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    gray(35);
    doc.text("Personalized Diet Plan", M, y);
    y += 4; hRule();

    Object.entries(data.diet_plan).forEach(([meal, foods]) => {
      if (y > 262) { doc.addPage(); y = 22; }
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      gray(55);
      doc.text(MEAL_LABEL[meal] || meal.charAt(0).toUpperCase() + meal.slice(1), M, y);
      y += 4.5;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      gray(110);
      const foodStr = (Array.isArray(foods) ? foods : [foods]).join("  •  ");
      const lines = doc.splitTextToSize(foodStr, COL - 6);
      doc.text(lines, M + 4, y);
      y += lines.length * 4 + 4;
    });
    y += 4;
  }

  if (data.recommendations.length > 0) {
    if (y > 220) { doc.addPage(); y = 22; }
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    gray(35);
    doc.text("Food Recommendations", M, y);
    y += 4; hRule();

    data.recommendations.slice(0, 12).forEach((rec) => {
      if (y > 265) { doc.addPage(); y = 22; }
      const label = DEFICIENCY_LABELS[rec.deficiency] || rec.deficiency;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8);
      gray(50);
      doc.text(label, M, y);
      y += 4.5;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      gray(110);
      const foodStr = rec.foods?.slice(0, 7).join(", ") || "";
      doc.text(foodStr, M + 4, y, { maxWidth: COL - 4 });
      y += 5;
      if (rec.traditional_remedy) {
        doc.setTextColor(0, 140, 80);
        doc.text(`🌿  ${rec.traditional_remedy}`, M + 4, y, { maxWidth: COL - 4 });
        y += 5;
      }
      y += 1.5;
    });
  }

  // ── Footer on every page ─────────────────────────────────
  const total = doc.getNumberOfPages();
  for (let i = 1; i <= total; i++) {
    doc.setPage(i);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(6.5);
    gray(175);
    doc.text(
      "This is NOT a medical diagnosis. Consult a qualified doctor for serious symptoms.",
      M,
      291
    );
    doc.text(`${i} / ${total}`, W - M - 10, 291);
  }

  doc.save(`BalanceAI_Report_${data.date.replace(/[/]/g, "-")}.pdf`);
}
