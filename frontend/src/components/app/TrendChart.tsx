"use client";

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import { scoreColor } from "@/lib/db";

interface DataPoint { date: string; score: number }

interface Props {
  data: DataPoint[];
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const score = payload[0]?.value as number;
  return (
    <div
      className="px-3 py-2 rounded-xl text-sm"
      style={{
        background: "rgba(6,6,10,0.95)",
        border: "1px solid rgba(255,255,255,0.1)",
        backdropFilter: "blur(12px)",
      }}
    >
      <p style={{ color: "rgba(255,255,255,0.5)", marginBottom: 2, fontSize: 11 }}>{label}</p>
      <p style={{ color: scoreColor(score), fontWeight: 700 }}>{score}/100</p>
    </div>
  );
};

export default function TrendChart({ data, height = 180 }: Props) {
  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl"
        style={{ height, background: "rgba(255,255,255,0.02)", border: "1px dashed rgba(255,255,255,0.07)" }}
      >
        <p style={{ color: "rgba(255,255,255,0.25)", fontSize: 13 }}>Koi data nahi — pehle analyze karo</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 4, left: -24, bottom: 0 }}>
        <defs>
          <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#00d97e" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#00d97e" stopOpacity={0}    />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
          axisLine={false} tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }}
          axisLine={false} tickLine={false}
          ticks={[0, 25, 50, 75, 100]}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(0,217,126,0.2)", strokeWidth: 1 }} />
        <ReferenceLine y={70} stroke="rgba(34,197,94,0.2)"  strokeDasharray="4 3" />
        <ReferenceLine y={40} stroke="rgba(245,158,11,0.15)" strokeDasharray="4 3" />
        <Area
          type="monotone"
          dataKey="score"
          stroke="#00d97e"
          strokeWidth={2}
          fill="url(#scoreGrad)"
          dot={{ fill: "#00d97e", strokeWidth: 0, r: 3 }}
          activeDot={{ fill: "#00d97e", strokeWidth: 2, stroke: "rgba(0,217,126,0.3)", r: 5 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
