"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/app/AppShell";
import { getAllAnalyses, getOrCreateProfile } from "@/lib/db";
import { getSupplementReport, DEFICIENCY_LABELS, type SupplementReport, type SupplementRow } from "@/lib/api";
import { Loader2, ShieldCheck, Printer, Download, HelpCircle, Stethoscope, Flag } from "lucide-react";

// balance.it exact tokens, verified live on both the results-card page (/recipes/:id)
// and the deep nutrient-profile page (/profile/:id)
const GREEN = "#1d5c3d";
const GREEN_BTN = "#256358"; // verified rgb(37,99,88) — VIEW RECIPE / BUY SUPPLEMENT buttons on the results card
const GREEN_LT = "#eef7f2";
const GREEN_BORDER = "#b6ddc9";
const CORAL = "#ec5252"; // verified rgb(236,82,82) — "deficiencies without supplement(s)" number
const BG = "#ffffff";
const PAGE_BG = "#f7f8f6";
const BORDER = "#e4e7e2";
const TEXT = "#1a1a1a";
const SUB = "#5a6571";
const AMBER = "#ffa41c"; // balance.it's exact "Buy Now" button color, verified rgb(255,164,28)
const TABLE_TEXT = "#212529"; // balance.it's exact nutrient-table cell/header color, verified — plain, uncolored

export default function SupplementReportPage() {
  const [report, setReport] = useState<SupplementReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const profile = await getOrCreateProfile();
      const analyses = await getAllAnalyses();
      const latest = analyses[0];

      if (!profile.age || !profile.weight_kg || !profile.height_cm) {
        setError("profile_incomplete");
        setLoading(false);
        return;
      }
      if (!latest || !latest.predictions?.length) {
        setError("no_analysis");
        setLoading(false);
        return;
      }

      const deficiencies: Record<string, { probability: number; deficient: boolean; threshold: number }> = {};
      for (const p of latest.predictions) {
        deficiencies[p.deficiency] = { probability: p.probability, deficient: p.risk_level !== "low", threshold: 0.5 };
      }

      try {
        const data = await getSupplementReport({
          age: profile.age,
          gender: profile.gender === "female" ? "female" : "male",
          weight_kg: profile.weight_kg,
          height_cm: profile.height_cm,
          deficiencies,
        });
        setReport(data);
      } catch {
        setError("backend_down");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <AppShell>
      <div style={{ background: PAGE_BG, minHeight: "100vh" }}>
        <div className="mx-auto max-w-4xl px-4 py-12 text-center">
          <div className="mx-auto rounded-full flex items-center justify-center"
            style={{ width: 96, height: 96, background: GREEN_LT }}>
            <ShieldCheck color={GREEN} size={44} />
          </div>
          <h1 className="mt-6" style={{ color: GREEN, fontSize: 34, fontWeight: 800, letterSpacing: "-0.02em" }}>
            {report
              ? `Your custom plan for ${report.deficiency_count || 0} flagged deficienc${report.deficiency_count === 1 ? "y" : "ies"}`
              : "Your personalised plan"}
          </h1>
          <p style={{ color: SUB, marginTop: 8 }}>
            Here is a plan we think will work well for you. Feel free to adjust your details and try again.
          </p>

          {loading && (
            <div className="flex items-center justify-center gap-2 mt-10" style={{ color: SUB }}>
              <Loader2 className="animate-spin" size={18} /> Calculating your report...
            </div>
          )}

          {error === "profile_incomplete" && (
            <ErrorCard text="We need your age, weight and height first." href="/profile" cta="Complete Profile" />
          )}
          {error === "no_analysis" && (
            <ErrorCard text="Run an analysis first so we know what to check for." href="/analyze" cta="Start Analysis" />
          )}
          {error === "backend_down" && (
            <div className="mt-8 rounded-lg p-6 text-left" style={{ background: BG, border: `1px solid ${BORDER}` }}>
              <p style={{ color: TEXT }}>Couldn&apos;t reach the server. Try again in a moment.</p>
            </div>
          )}

          {report && (
            <div className="flex justify-center mt-6">
              <Link href="/analyze"
                className="px-6 py-3 rounded-lg font-bold text-sm tracking-wide"
                style={{ background: "#fff", color: GREEN_BTN, border: `1px solid ${GREEN_BTN}` }}>
                CHANGE DETAILS
              </Link>
            </div>
          )}
        </div>

        {report && (
          <div className="mx-auto max-w-5xl px-4 pb-16">
            {/* Results-summary card — matches balance.it's page shown immediately after
                Step 2's "GET RECIPE" click, verified live at balance.it/recipes/:id */}
            <div className="rounded-lg p-8 mb-12" style={{ background: BG, border: `1px solid ${BORDER}` }}>
              <div className="rounded-full flex items-center justify-center"
                style={{ width: 30, height: 28, border: "1px solid #9a9a9a", color: "#9a9a9a", fontSize: 14, marginBottom: 12 }}>
                1
              </div>
              <h3 className="text-center" style={{ color: "#434343", fontSize: 32, fontWeight: 700 }}>
                Whole-Food + Supplement Plan
              </h3>
              <p className="text-center mt-2" style={{ color: SUB }}>
                <b>Includes:</b> real whole-food sources plus clinically-dosed supplements (ICMR-NIN/WHO/AIIMS protocols) for every flagged deficiency.
              </p>
              <hr style={{ border: "none", borderTop: `1px solid ${BORDER}`, margin: "20px 0" }} />
              <div className="grid sm:grid-cols-3 gap-6 text-center">
                <div>
                  <div style={{ color: SUB, fontSize: 14 }}>requires</div>
                  <div style={{ color: GREEN, fontWeight: 800, fontSize: 26 }}>
                    {report.rows.filter((r) => r.supplement).length} supplement{report.rows.filter((r) => r.supplement).length === 1 ? "" : "s"}
                  </div>
                  <a href="#ingredients" className="text-xs underline" style={{ color: SUB }}>LEARN MORE</a>
                </div>
                <div>
                  <div style={{ color: SUB, fontSize: 14 }}>daily requirement</div>
                  <div style={{ color: GREEN, fontWeight: 800, fontSize: 26 }}>
                    {Math.round(report.calories_kcal)} kcal
                  </div>
                  <Link href="/profile" className="text-xs underline" style={{ color: SUB }}>ADJUST DETAILS</Link>
                </div>
                <div>
                  <div style={{ color: SUB, fontSize: 14 }}>plan would have</div>
                  <div style={{ color: CORAL, fontWeight: 800, fontSize: 26 }}>
                    {report.deficiency_count}
                  </div>
                  <div style={{ color: SUB, fontSize: 12 }}>deficiencies without the supplement(s)</div>
                  <a href="#nutrient-profile" className="text-xs underline" style={{ color: SUB }}>SEE NUTRIENT PROFILE</a>
                </div>
              </div>
              <div className="flex justify-center gap-4 mt-6">
                <a href="#ingredients"
                  className="px-8 py-3 rounded-lg font-bold text-sm tracking-wide"
                  style={{ background: GREEN_BTN, color: "#fff" }}>
                  VIEW INGREDIENTS
                </a>
                <button className="px-8 py-3 rounded-lg font-bold text-sm tracking-wide"
                  style={{ background: "#fff", color: GREEN_BTN, border: `1px solid ${GREEN_BTN}` }}>
                  BUY SUPPLEMENT
                </button>
              </div>
            </div>

            {/* "Have questions?" resources — matches balance.it's own section, verified
                live on the results-card page: Visit FAQs / Contact Vet Nutritionist / Report Issue */}
            <div className="mb-16">
              <h2 className="text-center" style={{ color: "#434343", fontSize: 32, fontWeight: 800 }}>
                Have questions? Here are some helpful resources:
              </h2>
              <div className="grid sm:grid-cols-3 gap-8 mt-8">
                <HelpCard
                  icon={<HelpCircle color={GREEN} size={28} />}
                  title="Visit FAQs"
                  desc="Learn more about BalanceAI and how it works."
                  href="/chat"
                />
                <HelpCard
                  icon={<Stethoscope color={GREEN} size={28} />}
                  title="Contact Doctor"
                  desc="This is a screening tool, not a diagnosis. For serious or persistent symptoms, please consult a registered doctor or dietitian in person."
                  href="/chat"
                />
                <HelpCard
                  icon={<Flag color={GREEN} size={28} />}
                  title="Report Issue"
                  desc="Something off? Let us know and we'll get it right."
                  href="mailto:support@balanceai.app"
                />
              </div>
            </div>

            <div id="nutrient-profile" className="text-center mb-6">
              <div className="mx-auto rounded-full flex items-center justify-center"
                style={{ width: 72, height: 72, background: GREEN_LT }}>
                <ShieldCheck color={GREEN} size={32} />
              </div>
              <h2 className="mt-4" style={{ color: GREEN, fontSize: 26, fontWeight: 800 }}>Your nutrient profile</h2>
              <p style={{ color: SUB, marginTop: 6 }}>A detailed look at the complete nutritional information behind your assessment.</p>
              <div className="flex justify-center gap-4 mt-5">
                <IconCircle icon={<Printer size={18} color={GREEN} />} />
                <IconCircle icon={<Download size={18} color={GREEN} />} />
              </div>
            </div>

            <div className="flex justify-center gap-4 mb-10">
              <Link href="/dashboard"
                className="px-8 py-3 rounded-lg font-bold text-sm tracking-wide"
                style={{ background: "#fff", color: GREEN, border: `2px solid ${GREEN}` }}>
                BACK
              </Link>
              <button className="px-8 py-3 rounded-lg font-bold text-sm tracking-wide"
                style={{ background: GREEN, color: "#fff" }}>
                BUY SUPPLEMENT
              </button>
            </div>

            {report.rows.length === 0 ? (
              <div className="rounded-lg p-6 flex items-center gap-3 justify-center"
                style={{ background: GREEN_LT, border: `1px solid ${GREEN_BORDER}` }}>
                <ShieldCheck color={GREEN} size={22} />
                <p style={{ color: GREEN, fontWeight: 600 }}>No real deficiencies detected right now.</p>
              </div>
            ) : (
              <>
                <h3 id="ingredients" style={{ color: "#434343", fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Ingredients</h3>
                <div>
                  {(() => {
                    const foodLines = report.rows
                      .filter((r) => r.food_source)
                      .map((r) => ({
                        amount: `${r.food_source!.amount_g} g`,
                        name: r.food_source!.name,
                        buy: false,
                      }));
                    const suppLines = report.rows
                      .filter((r) => r.supplement)
                      .map((r) => ({ amount: r.supplement!.dose, name: r.supplement!.name, buy: true }));
                    const lines = [...foodLines, ...suppLines];
                    return lines.map((line, i) => (
                      <div key={i} className="flex items-center gap-4 py-3" style={{ borderBottom: `1px solid ${BORDER}` }}>
                        <div style={{ color: TEXT, fontWeight: 700, minWidth: 160 }}>{line.amount}</div>
                        <div className="flex-1" style={{ color: TEXT }}>{line.name}</div>
                        {line.buy && (
                          <button className="font-bold whitespace-nowrap flex-shrink-0"
                            style={{ background: AMBER, color: "#000", borderRadius: 8, padding: "13px 15px", fontSize: 14 }}>
                            Buy Now
                          </button>
                        )}
                      </div>
                    ));
                  })()}
                </div>
                <p style={{ color: SUB, fontSize: 13, fontStyle: "italic", marginTop: 10 }}>
                  Some values are estimates based on standard food-composition data (ICMR-NIN/USDA) and may vary by brand or source.
                </p>

                <div className="rounded-lg p-5 text-center my-8" style={{ background: GREEN_LT }}>
                  <span style={{ color: TEXT }}>Daily requirement: </span>
                  <b style={{ color: TEXT }}>{Math.round(report.calories_kcal)} kcal/day</b>
                  <span style={{ color: TEXT }}> &nbsp;OR&nbsp; </span>
                  <b style={{ color: CORAL }}>{report.deficiency_count} nutrient{report.deficiency_count > 1 ? "s" : ""}</b>
                  <span style={{ color: TEXT }}> flagged without a supplement</span>
                </div>

                <div>
                  <div style={{ color: TEXT, fontSize: 22, fontWeight: 700 }}>Nutrients</div>
                  <p style={{ color: SUB, fontSize: 14, marginTop: 2 }}>
                    A quick look at how fortifying your diet with a supplement can provide all the goodness you need to thrive.
                  </p>
                </div>

                <div className="mt-4 overflow-x-auto">
                  <table className="w-full" style={{ borderCollapse: "collapse", minWidth: 720 }}>
                    <thead>
                      <tr style={{ borderBottom: `1px solid #c4c4c4` }}>
                        <Th>Nutrient Name</Th>
                        <Th>Requirement Range</Th>
                        <Th align="right">Amount</Th>
                        <Th align="right">% of Requirement (with supplement)</Th>
                        <Th align="right">% of Requirement (without supplement)</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.rows.map((row) => (
                        <RowGroup key={row.nutrient} row={row}
                          isOpen={expanded === row.nutrient}
                          onToggle={() => setExpanded(expanded === row.nutrient ? null : row.nutrient)} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th className="py-3 px-3" style={{ color: TABLE_TEXT, fontWeight: 700, fontSize: 16, textAlign: align, verticalAlign: "bottom" }}>
      {children}
    </th>
  );
}

function HelpCard({ icon, title, desc, href }: { icon: React.ReactNode; title: string; desc: string; href: string }) {
  return (
    <Link href={href} className="flex flex-col items-center text-center">
      <div className="rounded-full flex items-center justify-center mb-4"
        style={{ width: 80, height: 80, background: GREEN_LT }}>
        {icon}
      </div>
      <h3 style={{ color: "#434343", fontSize: 16, fontWeight: 700 }}>{title}</h3>
      <p style={{ color: "#434343", fontSize: 14, marginTop: 6, maxWidth: 280 }}>{desc}</p>
    </Link>
  );
}

function IconCircle({ icon }: { icon: React.ReactNode }) {
  return (
    <div className="rounded-full flex items-center justify-center" style={{ width: 44, height: 44, background: GREEN_LT }}>
      {icon}
    </div>
  );
}

function ErrorCard({ text, href, cta }: { text: string; href: string; cta: string }) {
  return (
    <div className="mt-8 rounded-lg p-6 inline-block text-left" style={{ background: BG, border: `1px solid ${BORDER}` }}>
      <p style={{ color: TEXT }}>{text}</p>
      <Link href={href} className="inline-block mt-3 px-6 py-2 rounded-lg font-bold text-sm"
        style={{ background: GREEN, color: "#fff" }}>
        {cta}
      </Link>
    </div>
  );
}

function RowGroup({ row, isOpen, onToggle }: { row: SupplementRow; isOpen: boolean; onToggle: () => void }) {
  const label = DEFICIENCY_LABELS[row.nutrient] || row.display_name;
  return (
    <>
      <tr onClick={onToggle} className="cursor-pointer" style={{ borderBottom: `1px solid #c4c4c4` }}>
        <td className="py-4 px-3" style={{ color: TABLE_TEXT }}>{label}</td>
        <td className="py-4 px-3" style={{ color: TABLE_TEXT }}>{row.requirement_range} {row.unit}</td>
        <td className="py-4 px-3 text-right" style={{ color: TABLE_TEXT, fontVariantNumeric: "tabular-nums" }}>
          {row.target} {row.unit}
        </td>
        <td className="py-4 px-3 text-right" style={{ color: TABLE_TEXT, fontVariantNumeric: "tabular-nums" }}>
          {row.with_supplement_pct}%+
        </td>
        <td className="py-4 px-3 text-right" style={{ color: TABLE_TEXT, fontVariantNumeric: "tabular-nums" }}>
          {row.without_supplement_pct}%
        </td>
      </tr>
      {isOpen && (
        <tr style={{ background: GREEN_LT, borderBottom: `1px solid #c4c4c4` }}>
          <td colSpan={5} className="px-3 py-5">
            {row.supplement ? (
              <div>
                <div className="grid sm:grid-cols-4 gap-4">
                  <Info label="Supplement" value={row.supplement.name} />
                  <Info label="Dose" value={row.supplement.dose} />
                  <Info label="Form" value={row.supplement.form} />
                  <Info label="Duration" value={row.supplement.duration} />
                </div>
                <div className="mt-3 text-sm" style={{ color: TEXT }}>{row.supplement.note}</div>
                <div className="mt-2 text-sm italic" style={{ color: SUB }}>Why food alone fails: {row.supplement.why_food_fails}</div>
                <button className="mt-4 font-bold"
                  style={{ background: AMBER, color: "#000", borderRadius: 8, padding: "13px 15px", fontSize: 14 }}>
                  Buy Now
                </button>
              </div>
            ) : (
              <div style={{ color: SUB, fontSize: 14 }}>Mild level — correctable through diet, no supplement needed yet.</div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ color: SUB, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ color: TEXT, fontWeight: 600, fontSize: 14 }}>{value}</div>
    </div>
  );
}
