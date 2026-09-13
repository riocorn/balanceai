"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      className={cn("rounded-xl overflow-hidden", className)}
      style={{ background: "rgba(255,255,255,0.05)", position: "relative", ...style }}
    >
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.06) 50%, transparent 100%)",
          backgroundSize: "200% 100%",
          animation: "shimmer 1.6s infinite linear",
        }}
      />
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="px-5 sm:px-8 py-8 space-y-6 max-w-5xl mx-auto">
      <Skeleton className="h-8 w-40" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Skeleton className="h-52 rounded-2xl" />
        <Skeleton className="h-52 rounded-2xl" />
      </div>
      <Skeleton className="h-36 rounded-2xl" />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-24 rounded-2xl" />)}
      </div>
    </div>
  );
}

export function HistorySkeleton() {
  return (
    <div className="px-5 sm:px-8 py-8 space-y-4 max-w-3xl mx-auto">
      <Skeleton className="h-8 w-32" />
      <Skeleton className="h-10 w-48 rounded-xl" />
      {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24 rounded-2xl" />)}
    </div>
  );
}

export function ProfileSkeleton() {
  return (
    <div className="px-5 sm:px-8 py-8 space-y-6 max-w-2xl mx-auto">
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-32 rounded-2xl" />
      <div className="grid grid-cols-4 gap-3">
        {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
      </div>
      <Skeleton className="h-64 rounded-2xl" />
    </div>
  );
}
