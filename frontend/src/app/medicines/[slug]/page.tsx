import MedicineDetailPage from "@/components/medicines/MedicineDetailPage";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  // This Next.js version hands the raw, still-percent-encoded path segment to
  // params (verified 2026-09-28: %20/%3A arrive un-decoded) — decode before
  // matching it against the real medicine_details.json slug keys.
  let decoded = slug;
  try {
    decoded = decodeURIComponent(slug);
  } catch {
    // malformed encoding — fall back to the raw segment
  }
  return <MedicineDetailPage slug={decoded} />;
}
