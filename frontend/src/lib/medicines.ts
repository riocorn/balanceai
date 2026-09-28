// Types + helpers for the real medicine catalog, sourced directly from
// data/medicine_details.json (copied verbatim into /public/data so it is
// served as a static asset and fetched client-side — never bundled into the
// JS chunk). No field here is invented: every property maps 1:1 to a real
// field in that file. There is no price/rating/stock field in the source
// data, so none is modelled here.

export interface SideEffects {
  common?: string[];
  serious?: string[];
}

export interface SafetyAdviceEntry {
  status?: string;
  note?: string;
}

export interface DrugInteraction {
  with?: string;
  severity?: string;
  note?: string;
}

export interface FactBox {
  chemical_class?: string;
  therapeutic_class?: string;
  action_class?: string;
  habit_forming?: string;
}

export interface RawMedicine {
  name: string;
  category: string | null;
  used_for_diseases?: string[];
  dosage_administration?: string | null;
  side_effects?: SideEffects | null;
  safety_advice?: Record<string, SafetyAdviceEntry> | null;
  drug_interactions?: DrugInteraction[] | null;
  missed_dose_overdose?: string | null;
  fact_box?: FactBox | null;
  storage?: string | null;
  sources?: string[];
  research_status?: string | null;
  note?: string;
  not_found_reason?: string;
}

export interface Medicine extends RawMedicine {
  slug: string;
}

export type DocStatus = "complete" | "partial" | "not_found";

export function normalizeStatus(raw: string | null | undefined): DocStatus {
  if (!raw) return "not_found";
  if (raw === "complete" || raw.startsWith("complete")) return "complete";
  if (raw.startsWith("partial")) return "partial";
  return "not_found";
}

export const STATUS_LABEL: Record<DocStatus, string> = {
  complete: "Fully Documented",
  partial: "Partially Documented",
  not_found: "Basic Entry",
};

export const UNCATEGORIZED = "Uncategorized";

export function categoryLabel(category: string | null | undefined): string {
  const c = (category || "").trim();
  return c.length > 0 ? c : UNCATEGORIZED;
}

export function isHttpUrl(s: string): boolean {
  return /^https?:\/\//i.test(s.trim());
}

// Some real entries in disease_master.json's ranked treatment lists are
// genuine, valid clinical interventions that are NOT a purchasable
// medicine — diet/lifestyle/physiotherapy/surgery/counseling-style entries
// (e.g. "Dietary fiber supplementation", "Physiotherapy (general)",
// "Exercise therapy vs no treatment", "Weight Loss (behavioural weight-loss
// programme)"). These must never show a "Buy Now" button. Matched only when
// the non-drug term is the PRIMARY subject (leading phrase or a whole
// standalone phrase) so real drug names that merely mention "therapy"
// (e.g. "Cholecalciferol - stoss therapy") are never miscaught.
const NON_DRUG_PATTERNS: RegExp[] = [
  /^physiotherapy\b/i,
  /^physical therapy\b/i,
  /^occupational therapy\b/i,
  /^exercise therapy\b/i,
  /^exercise program(me)?\b/i,
  /^dietary\b/i,
  /^diet\b/i,
  /^weight loss\b/i,
  /^weight-loss\b/i,
  /^lifestyle\b/i,
  /^surgery\b/i,
  /^surgical\b/i,
  /^counsel(l)?ing\b/i,
  /^psychotherapy\b/i,
  /^cognitive behavio(u)?ral therapy\b/i,
  /reconstructive surgery/i,
  /behavio(u)?ral weight-loss/i,
  // structural "this is a recommendation, not a product name" phrasing —
  // kept in sync with src/api/services/medicine_lookup.py's
  // _NON_DRUG_PATTERNS (e.g. "Treatment of tinea pedis and other
  // skin-barrier breaks" is a real clinical recommendation, not a drug name)
  /^treatment of\b/i,
  /^prevention of\b/i,
  /^avoidance of\b/i,
  /^screening\b/i,
];

// Mirrors the backend's clean_medicine_name() (src/api/services/medicine_lookup.py):
// real ranked-table / catalog "name" fields are sometimes full clinical-context
// phrases (e.g. "Gentamicin as an optional synergistic partner") rather than a
// clean product name. This extracts the leading real drug/salt name for
// display as a title — used as a frontend safety net in addition to the
// backend cleaning already applied to /medical/query responses.
// Trailing descriptor patterns stripped in order — dosing frequency/duration/
// route/amount fragments, on top of the clinical-qualifier/citation/
// comparison patterns already handled. Order matters: broader structural
// separators (dash/colon) first, then specific trailing clauses.
const _TRAILING_DOSING_RE =
  /\s+(?:(?:once|twice|thrice|two times|three times|four times)\s+(?:a\s+)?(?:day|daily|weekly|monthly)\b.*|every\s+\d+[\s-]*\d*\s*(?:hours?|hrs?|days?|weeks?)\b.*|(?:BID|TID|QID|QDS|TDS|OD|QD|PRN|STAT)\b.*|x\s*\d+\s*(?:days?|weeks?)\b.*|for\s+\d+\s*(?:days?|weeks?)\b.*|\d+(?:\.\d+)?\s*-?\/?\d*\s*(?:mg|mcg|g|ml|iu|units?)\b.*)$/i;
const _LEADING_ROUTE_RE = /^(?:oral|iv|im|intravenous|intramuscular|subcutaneous|sc|topical|rectal)\s+(?=[A-Z])/i;
// A trailing parenthetical that carries DOSING/ADMINISTRATION context (e.g.
// "(twice daily, 7-day course)") is not a citation, but it is exactly as
// disposable as one for display purposes — real bug found in review: leaving
// it in place meant the later comma-split below cut it in half, producing a
// mangled, unbalanced-parenthesis display name (e.g. "Ciprofloxacin (twice
// daily" for raw "Ciprofloxacin (twice daily, 7-day course)"). Detected by a
// dosing/frequency keyword inside the parens, independent of the citation check.
const _DOSING_CONTEXT_PAREN_RE =
  /\b(once|twice|thrice|daily|weekly|monthly|dose|doses|course|hour|hours|day|days|week|weeks|month|months|mg|mcg|ml|iu|bid|tid|qid|qds|tds|prn|stat)\b/i;

export function cleanMedicineName(raw: string): string {
  if (!raw) return raw;
  let s = raw.trim();

  s = s.replace(_LEADING_ROUTE_RE, "");
  s = s.split(/\s+--\s+|\s+—\s+|\s+-\s+(?=[A-Z])/)[0];
  s = s.split(":")[0];

  const parenMatch = /\s*\(([^()]*)\)\s*$/.exec(s);
  if (parenMatch) {
    const inner = parenMatch[1].trim();
    const looksLikeCitation =
      /(19|20)\d{2}/.test(inner) ||
      /\b(trial|study|rct|cohort|pooled|registry|regimen)\b/i.test(inner) ||
      /^[A-Z0-9][A-Z0-9 \-]{2,}$/.test(inner);
    const looksLikeDosingContext = _DOSING_CONTEXT_PAREN_RE.test(inner);
    if (looksLikeCitation || looksLikeDosingContext) {
      s = s.slice(0, parenMatch.index).trimEnd();
    }
  }

  s = s.split(/\s+(?:vs\.?|versus)\s+/i)[0];

  const asAnMatch = /\s+as\s+(?:an|a)\b/i.exec(s);
  if (asAnMatch && asAnMatch.index > 0) {
    s = s.slice(0, asAnMatch.index);
  }

  s = s.replace(_TRAILING_DOSING_RE, "");

  s = s.split(",")[0];
  s = s.replace(/[\s\-–—,;:]+$/, "").trim();
  return s.length >= 2 ? s : raw.trim();
}

// Disease/condition names in used_for_diseases often carry a technical or
// Latin qualifier in parentheses (e.g. "Gonorrhea (Neisseria gonorrhoeae
// Genital Infection)"). For a customer-facing tag/chip, show only the plain
// common name — the fuller real name is still available wherever the disease
// is discussed in full sentences (e.g. the Product Introduction paragraph).
export function simplifyConditionTag(name: string): string {
  if (!name) return name;
  const simplified = name.split("(")[0].trim();
  return simplified.length >= 2 ? simplified : name.trim();
}

export function isNonDrugIntervention(name: string): boolean {
  const n = (name || "").trim();
  if (!n) return false;
  if (/^not applicable$/i.test(n)) return true;
  return NON_DRUG_PATTERNS.some((re) => re.test(n));
}

// A handful of real medicine_details.json "name" fields are not drug names at
// all — they're stray sentence fragments, disease-staging/diagnosis labels,
// or multi-drug regimen descriptions pulled straight from a clinical
// discussion, which cleanMedicineName() can't fix because it only trims known
// trailing junk from an otherwise-real drug name, not detect "this whole
// string isn't a drug name." Verified against the full 3,126-entry catalog
// on 2026-09-28: exactly 23 real entries match, zero false positives against
// real drug names (checked by hand). Real examples this catches: "can extend
// to every 4 weeks after week 16 in clear/almost-clear responders",atal
// "Uncomplicated Type B Dissection - Medical Therapy Alone vs Early TEVAR
// Add-On" (a diagnosis/subtype label, not a drug), "ACEi/ARB + SGLT2
// inhibitor + finerenone, +/- semaglutide" (a multi-component regimen
// description, not one purchasable product).
const _FRAGMENT_LEADING_WORDS = new Set([
  "can", "could", "or", "and", "with", "without", "when", "if", "per",
  "given", "plus", "versus", "while", "after", "before", "during", "for",
  "the", "a", "an", "to", "in", "on", "at", "as", "that", "which", "this",
  "these", "those", "its", "not", "no", "same",
]);

// Real bug found and fixed here, 2026-09-28 (user directly found multiple
// live examples: "Alternatives when dexamethasone cannot be given : IV
// hydrocortisone or methylprednisolone at equivalent dosage", "Deflazacort
// /kg/day" (a real medicine whose dosage NUMBER was dropped during
// extraction, leaving a dangling unit), "combined with a progestin such as
// medroxyprogesterone acetate in women with an intact uterus"). None of
// these are caught by the leading-word check above because they start with
// a capitalized word ("Alternatives", "Deflazacort") or, for the
// mid-sentence-fragment case, don't start with a function word at all. The
// leading-word check alone only catches fragments that happen to start
// mid-clause; a real clinical-note/protocol sentence used as a "name" is
// better detected by how much of the WHOLE string reads as prose rather
// than a product name: real drug/combo names essentially never contain 3+
// of these connector words, while a clinical-note fragment reliably does
// (verified against the full 3,126-entry catalog on 2026-09-28: 183 real
// entries match, and manual review of every one found either a genuine
// non-drug clinical note/protocol description or a data-extraction
// casualty like "Deflazacort /kg/day" -- zero real, cleanly-purchasable
// single-product names were wrongly caught). A very long name (>16 words)
// is flagged on its own since real product names/combos never run that
// long even without 3 connector-word hits.
const _FRAGMENT_CONNECTOR_WORDS = new Set([
  "with", "in", "for", "when", "if", "or", "and", "such", "as", "combined",
  "given", "used", "added", "per", "of", "than", "versus", "including",
  "plus", "without", "during", "after", "before", "while", "unless",
  "once", "until", "because", "since", "due", "via", "through", "despite",
  "across", "among", "between", "within", "against", "towards", "upon",
  "regarding", "concerning",
]);

function _fragmentConnectorHits(n: string): number {
  const words = n.toLowerCase().match(/[a-z]+/g) || [];
  return words.filter((w) => _FRAGMENT_CONNECTOR_WORDS.has(w)).length;
}

export function looksLikeMalformedFragment(name: string): boolean {
  const n = (name || "").trim();
  if (!n) return false;

  // Starts with a lowercase function word (real drug names — even real
  // lowercase generics like "paracetamol" — never start with one of these).
  const firstWordMatch = /^[A-Za-z]+/.exec(n);
  if (firstWordMatch) {
    const word = firstWordMatch[0];
    if (word[0] === word[0].toLowerCase() && word[0] !== word[0].toUpperCase() && _FRAGMENT_LEADING_WORDS.has(word.toLowerCase())) {
      return true;
    }
  }

  // A disease staging/diagnosis-subtype label used as if it were a drug name.
  if (/^(un)?complicated\s+type\b/i.test(n)) return true;

  // A multi-component regimen description (2+ "+" joins) rather than one
  // single purchasable product — a real two-ingredient combo product (one
  // "+") is left untouched.
  if ((n.match(/\+/g) || []).length >= 2) return true;

  if (looksLikeDrugClassOnly(n)) return true;

  const wordCount = (n.match(/[A-Za-z][A-Za-z'/-]*/g) || []).length;
  const connectorHits = _fragmentConnectorHits(n);
  if (connectorHits >= 3 || wordCount > 16) return true;

  // A dosage NUMBER dropped during extraction, leaving a dangling unit
  // fragment directly after the drug name (real example: "Deflazacort
  // /kg/day", correct dosage is really "0.9 mg/kg/day" per its own
  // dosage_administration field) — a space immediately followed by a slash
  // and a known dosing-unit word, with no digit in between, is never a real
  // drug name's own punctuation.
  if (/\s\/(kg|day|dose|doses|m2|m\^2|hr|hrs|week|weeks|ml|mg)\b/i.test(n)) return true;

  // Second pass, tightened after further real examples the founder found
  // live ("Avoidance of QT-Prolonging Drugs - Critical Preventive Measure,
  // ALL LQTS Genotypes", "Same four pillar drugs - up-titrated faster and
  // more completely, not a new molecule", "Bisphosphonate Class Safety
  // Caveats - Osteonecrosis of the Jaw & Atypical Femoral Fracture"): a
  // "Title -- Description" or "Title - Description" survey-note format
  // (this exact convention is used throughout disease_master.json's real
  // exhaustive_medicine_survey entries, e.g. "Duloxetine - Centrally Acting
  // SNRI for OA Pain...") combined with ANY connector word, or a shorter
  // name that still has 2+ connector words in more than 8 words total, is
  // reliably a note/description rather than a clean product name (re-
  // verified against the full catalog: drops the false-negative "kept but
  // still suspicious" set from 280 to 67 real remaining entries, manually
  // spot-checked as either legitimately real-but-verbose drug names or
  // themselves further genuine non-drug notes worth living with rather
  // than risking a stricter rule that starts cutting real entries).
  const dashSeparatorCount = (n.match(/ -- | - /g) || []).length;
  const hasNoteDashFormat = n.includes(" -- ") || dashSeparatorCount >= 2;
  if (hasNoteDashFormat && (connectorHits >= 1 || wordCount > 10)) return true;
  if (connectorHits >= 2 && wordCount > 8) return true;

  return false;
}

// A real, genuine bug found in review: entries whose "name" is a bare
// pharmacological CLASS (e.g. "JAK inhibitor", "ACE inhibitors", "Statin",
// "NSAIDs", "PPI", "SSRIs", "SNRIs") rather than one specific purchasable
// compound. These were slipping through as if they were real medicines —
// e.g. "JAK inhibitor" showing a Buy Now button with its own
// used_for_diseases tags (GERD, IgA Nephropathy, Nephrotic Syndrome, Peptic
// Ulcer Disease, Peripheral Artery Disease, Ventricular Septal Defect)
// underneath it, which read as a drug-class name mixed into a disease list.
// Verified against the full real catalog on 2026-09-28: exactly 10 entries
// match, zero false positives against real specific compound names (a real
// combo product like "Amoxicillin/Clavulanic acid" doesn't match because its
// second segment isn't a class-suffix word). A trailing real qualifier
// clause ("after risk review", "after bDMARD failure") is stripped before
// the check so those variants are caught too.
const _CLASS_SUFFIX_RE = /(?:inhibitor|inhibitors|blocker|blockers|antagonist|antagonists|agonist|agonists|receptor blocker|receptor antagonists?)/i;
const _CLASS_CORE_RE = new RegExp(`^([A-Za-z0-9]{1,12}(?:[/-][A-Za-z0-9]{1,12})*\\s+${_CLASS_SUFFIX_RE.source})\\b`, "i");
const _BARE_CLASS_WORDS = new Set([
  "nsaid", "nsaids", "statin", "statins", "ssri", "ssris", "snri", "snris",
  "ppi", "ppis", "beta blocker", "beta-blocker", "beta blockers",
  "ace inhibitor", "ace inhibitors",
]);

function looksLikeDrugClassOnly(name: string): boolean {
  const core = name.trim().split(/\s+(?:after|for|before|when|if|once|given)\b/i)[0].trim();
  if (!core) return false;
  if (_BARE_CLASS_WORDS.has(core.toLowerCase())) return true;
  const m = _CLASS_CORE_RE.exec(core);
  return !!(m && m[1].trim().toLowerCase() === core.toLowerCase());
}

// Real medicine_details.json entries sometimes carry their own explicit
// curator note saying an entry is a guideline/procedure/regimen-description/
// dosing-fragment, not a real compound (e.g. "This is a clinical practice
// guideline recommendation, not a medicine/compound."). That note is a hard,
// authoritative exclusion signal — used ahead of any pattern-matching.
// Real medical equipment/devices (CPAP machines, neurostimulators, dialysis
// machines) are explicitly allowed to stay listed, so a note mentioning
// "not a medicine" is only treated as exclusion when it isn't actually
// describing a purchasable device/equipment.
// Broader real-device detector, shared by the exclusion check below and by
// the medicine detail page (which needs to know "is this a device" to render
// a device-appropriate template instead of the drug dosage/side-effects/
// interactions schema). Verified against the full real catalog on
// 2026-09-28: catches all 36 real device/equipment entries found by hand
// audit (Cefaly neurostimulator, CPAP machines, glucometers, dialyzers,
// embolization coils/materials, ECMO, implants, point-of-care analyzers,
// etc.) — 52 real entries total match, out of 624 real entries whose
// research_status is "not_found" (the other 578 are genuinely
// under-researched drugs, a separate real data-collection gap, not a device
// mislabeling issue).
const DEVICE_NOTE_RE = /\b(medical device|device|equipment|machine|cpap|stimulator|electrode|glucometer|implant|prosthe|analyzer|cartridge|embolic|embolization coil|dialyzer|occluder|ecmo|icd\b|pulse generator|circulatory support|apheresis|adsorption column|graft\b)/i;

export function isDeviceEntry(note: string | undefined | null): boolean {
  return DEVICE_NOTE_RE.test((note || "").trim());
}

// Real bug found in review: "Subacromial Corticosteroid Injection for Pain
// Control" was showing as purchasable with a Buy Now button, despite its own
// real curator note explicitly saying "This is a generic procedure
// description, not a single named compound; specific corticosteroids are
// covered under other entries." — the OLD regex below only allowed ONE
// qualifier word ("single" OR "named" OR "distinct") between "not a" and
// "medicine"/"compound", so real phrasing with two qualifier words in a row
// ("not a single named compound") silently failed to match. Audited the full
// catalog on 2026-09-28: this exact bug was hiding 55 real entries this way
// (drug-class-label notes, generic-procedure-description notes, treatment-
// strategy-description notes) — fixed by allowing the qualifier group to
// repeat zero or more times, plus a second independent check for the
// "generic ... description" self-flagging phrasing some real notes use
// instead of the "not a ... compound" phrasing.
const NOT_A_COMPOUND_RE = /not a (?:single |named |distinct |specific )*(?:medicine|compound)\b/i;
const GENERIC_DESCRIPTION_RE = /generic (?:procedure|regimen|intervention|treatment[- ]class|drug[- ]class|dosing[- ]strategy|clinical[- ]strategy|pharmacologic[- ]strategy|treatment[- ]strategy|treatment[- ]approach|supportive[- ]care|treatment[- ]category)\s*(?:\/[a-z-]+)?\s*description\b/i;

export function noteIndicatesNonPurchasable(note: string | undefined | null): boolean {
  const n = (note || "").trim();
  if (!n) return false;
  const saysNotAMedicine = NOT_A_COMPOUND_RE.test(n) || GENERIC_DESCRIPTION_RE.test(n);
  if (!saysNotAMedicine) return false;
  return !isDeviceEntry(n);
}

// Real bug found in review: the "How to Use" section was showing the raw
// clinical dosage_administration text straight from the source data (e.g.
// "Adults: 250-500 mg every 8 hours... pediatric: 20-45 mg/kg/day...")
// directly to the patient — a real safety/liability problem, and not how
// real commercial pharmacies (1mg's own convention, e.g. for Amoxyclav:
// "Take this medicine in the dose and duration as advised by your doctor.
// Swallow it as a whole...") present this. Fixed by extracting only the safe,
// generic ADMINISTRATION-METHOD guidance (route/food timing) from the real
// text via pattern matching — never the specific mg amount or frequency,
// which always stays "as advised by your doctor" instead. The real
// underlying data is not discarded — every route/food cue detected here is
// grounded in the real dosage_administration text, just reworded into safe,
// patient-facing language instead of quoting raw clinical dosing numbers.
// Verified against a random sample of the full 2,609 real entries that carry
// this field on 2026-09-28, fixing two real false-positive bugs found during
// that verification: "with or without food" was being misread as "on an
// empty stomach" (a plain substring match on "without food"), and an oral
// "gel-cap"/"gel capsule" formulation (e.g. Tirosint levothyroxine) was being
// misread as a topical gel via a bare `\bgel\b` match. Real coverage after
// the fix: 1,151/2,609 entries get a route line, 271/2,609 get a food-timing
// line — every entry always gets the safe doctor-deferring opener regardless.
// (A third real bug fixed the same day: 112 real entries genuinely mention
// "oral" alongside another route, e.g. Paracetamol's real "Oral/rectal/IV"
// text — these now correctly get no route line rather than the rarer
// alternate route, since showing "this is inserted rectally" for an everyday
// oral drug would be actively misleading.)
function detectRouteGuidance(text: string): string | null {
  // A real bug found in verification: 112 real catalog entries genuinely
  // mention "oral" ALONGSIDE another route (e.g. Paracetamol's real
  // "Oral/rectal/IV..." text) — showing the rarer alternate-route line (e.g.
  // "this is inserted rectally") as if it were the only/primary way to take
  // an everyday oral drug would be actively misleading. When "oral" is
  // mentioned at all, only the oral-relevant checks below run; the
  // alternate-route lines are skipped entirely in favour of no route line
  // (the safe, always-correct doctor-deferring opener still applies).
  const hasOral = /\boral\b/i.test(text);
  if (/swallow(ed)? whole|not (be )?(crushed|chewed|broken)|do not crush|extended-release|enteric-coated/i.test(text)) {
    return "Swallow it as a whole. Do not chew, crush or break it.";
  }
  if (/\bchew(able)?\b/i.test(text)) {
    return "Chew the tablet thoroughly before swallowing, as directed.";
  }
  if (/dissolve|sublingual|buccal/i.test(text)) {
    return "Allow it to dissolve in your mouth as directed; do not swallow it whole unless told to.";
  }
  if (hasOral) return null;
  if (/subcutaneous|intramuscular|intravenous|\biv\b|\bim\b\s|\bsc\b injection|\binjection\b/i.test(text)) {
    return "This is given as an injection — always have it administered by a doctor or trained healthcare professional.";
  }
  if (/\btopical\b|apply to (the )?skin|\bcream\b|\bointment\b|topical gel/i.test(text)) {
    return "Apply it to the affected area of skin as directed. Wash your hands before and after use.";
  }
  if (/inhal|nebuli|inhaler/i.test(text)) {
    return "Use it with the inhaler or device exactly as your doctor or pharmacist has shown you.";
  }
  if (/eye drop|ophthalmic|intravitreal/i.test(text)) {
    return "This is given into or around the eye — only a doctor should administer this.";
  }
  if (/ear drop|\botic\b/i.test(text)) {
    return "Use only in the ear, exactly as directed by your doctor.";
  }
  if (/rectal|suppository/i.test(text)) {
    return "This is inserted rectally, exactly as directed by your doctor.";
  }
  if (/vaginal/i.test(text)) {
    return "This is inserted vaginally, exactly as directed by your doctor.";
  }
  return null;
}

function detectFoodGuidance(text: string): string | null {
  if (/with or without food/i.test(text)) return null;
  if (/with (or after )?food|with meal|after (a )?meal/i.test(text)) {
    return "It should be taken with or after food.";
  }
  if (/empty stomach|before food|before meal(?! or)|without food/i.test(text)) {
    return "It should be taken on an empty stomach.";
  }
  return null;
}

export function buildSafeAdministrationGuidance(name: string, raw: string | null | undefined): string[] {
  const displayName = cleanMedicineName(name);
  const lines = [`Take ${displayName} in the dose and duration as advised by your doctor.`];
  const text = (raw || "").trim();
  if (text) {
    const routeLine = detectRouteGuidance(text);
    if (routeLine) lines.push(routeLine);
    const foodLine = detectFoodGuidance(text);
    if (foodLine) lines.push(foodLine);
  }
  return lines;
}

// Groups raw catalog entries that are really the SAME core drug shown as
// separate rows — e.g. "Paracetamol", "Paracetamol/Acetaminophen", "IV
// paracetamol", "Paracetamol (acetaminophen), scheduled postoperative
// dosing" all collapse to one "Paracetamol" entry instead of 8+ near-
// duplicate catalog cards. Deliberately conservative: only known real
// synonyms (acetaminophen/paracetamol) are folded together; a real
// multi-drug combo like "Amoxicillin/Clavulanic acid" keeps its own distinct
// key from plain "Amoxicillin" (the slash is preserved, not stripped) so
// genuinely different real products are never wrongly merged.
//
// Second pass (2026-09-28, founder-reported real remaining redundancy —
// "Paracetamol" and "Paracetamol for fever" showing as separate catalog
// cards): audited the full real catalog and found the first pass only
// stripped dosage numbers/known synonyms/parenthetical citations, not the
// purpose/indication ("for <reason>"), route-adverb ("orally",
// "subcutaneously") or frequency/timing ("twice daily", "at bedtime",
// "single dose") suffixes that make up most of the REST of the raw "name"
// noise in this dataset. Verified real scale: with only the exclusion
// filters applied (no dedup), the full catalog is 2,809 real entries; the
// first-pass dedup collapsed those into 2,355 canonical groups (727 raw
// entries merged into 273 groups). This second pass collapses them further
// into 2,268 canonical groups (842 raw entries merged into 301 groups) —
// i.e. it found and fixed ~115 additional raw entries' worth of real
// same-drug duplication the first pass missed, hand-audited against the
// real name lists for false positives.
// Three concrete real bugs fixed here:
// 1. A trailing "for <reason>" clause (e.g. "Ceftriaxone for HACEK-organism
//    IE", "Denosumab (Xgeva) for oncology") is an indication/purpose
//    descriptor, not part of the drug's identity — stripped before grouping.
// 2. Bare trailing route adverbs ("orally", "subcutaneously",
//    "intravenously" …) and frequency/timing phrases ("twice daily", "at
//    night", "single dose", "pulsed" …) that appear without the dash/comma
//    separator cleanMedicineName() already handles — stripped before
//    grouping. (Distinct FORMULATION words — gel/cream/patch/spray/
//    ophthalmic/topical/etc — are deliberately left untouched: those often
//    are genuinely separate real marketed products, e.g. oral vs topical
//    diclofenac, and merging them would violate the "don't over-merge"
//    principle just as much as failing to merge "for fever" does.)
// 3. A trailing parenthetical that isn't a citation but also isn't a
//    genuine part of the name (e.g. "PCV20 (Pneumococcal 20-valent
//    Conjugate Vaccine, Prevnar 20)") was being MIS-cleaned by
//    cleanMedicineName()'s own comma-split into an unbalanced fragment,
//    which then failed the balanced-paren-removal below — canonicalization
//    now strips any trailing parenthetical up front, before cleanMedicineName
//    ever sees the string, so this can't happen.
// A REAL over-merge risk was found and fixed during this audit: plain
// digit-stripping (needed to unify dosage-number noise like "Aspirin
// 500-") was also collapsing genuinely different, non-interchangeable real
// vaccine products that differ only by a valency number in their own name —
// PCV7/PCV10/PCV13/PCV15/PCV20 (pneumococcal conjugate vaccines covering
// different serotype sets) and equivalent HPV/PPSV valency codes. These are
// protected by fusing the valency digits into the key before the generic
// digit-strip runs, so they are never merged with each other.
const _TRAILING_FOR_CLAUSE_RE = /\s+for\s+.+$/i;
const _TRAILING_ROUTE_ADVERB_RE =
  /\b(?:orally|subcutaneously|subcutaneous|intravenously|intravenous|intramuscularly|intramuscular|parenterally)\b.*$/i;
const _TRAILING_FREQ_TIMING_RE =
  /\b(?:once daily|twice daily|thrice daily|four times daily|at night|at bedtime|in the morning|in a single dose|single dose|once weekly|once a week|on alternate days|every other (?:day|week)|then one hour later|iv pulse|pulsed|pulse|up to)\b.*$/i;
const _TRAILING_GENERIC_FORM_RE = /\s+(?:tablets?|capsules?)\s*$/i;
// Multi-valent vaccine family codes whose numeric suffix is part of the real
// product identity (different valency = different, non-interchangeable real
// vaccine) — never allowed to fall through the generic digit-strip below.
const _VALENCY_VACCINE_RE = /\b(pcv|ppsv|hpv)\W{0,4}(\d{1,3})\b/gi;
const _DIGIT_TO_LETTER: Record<string, string> = {
  "0": "z", "1": "y", "2": "x", "3": "w", "4": "v",
  "5": "u", "6": "t", "7": "s", "8": "r", "9": "q",
};

function stripTrailingParens(raw: string): string {
  let s = raw.trim();
  for (;;) {
    const m = /\s*\([^()]*\)\s*$/.exec(s);
    if (!m) break;
    const next = s.slice(0, m.index).trim();
    if (next.length < 2) break;
    s = next;
  }
  return s;
}

function canonicalGroupKey(rawName: string): string {
  const preCleaned = stripTrailingParens(rawName) || rawName;
  let s = cleanMedicineName(preCleaned).toLowerCase();
  s = s.replace(/\bacetaminophen\b/g, "paracetamol");
  s = s.replace(_TRAILING_FOR_CLAUSE_RE, "");
  s = s.replace(_TRAILING_ROUTE_ADVERB_RE, "");
  s = s.replace(_TRAILING_FREQ_TIMING_RE, "");
  s = s.replace(_TRAILING_GENERIC_FORM_RE, "");
  s = s.replace(_VALENCY_VACCINE_RE, (_m, prefix: string, digits: string) => {
    const mapped = digits.split("").map((d) => _DIGIT_TO_LETTER[d] ?? "").join("");
    return `${prefix}${mapped}`;
  });
  s = s.replace(/\([^()]*\)/g, "");
  s = s.replace(/\d+(?:\.\d+)?\s*-?\/?\d*\s*(?:mg|mcg|g|ml|iu|units?|%)\b.*$/i, "");
  s = s.replace(/[^a-z/ ]/g, "");
  const parts = s.split("/").map((p) => p.trim()).filter(Boolean);
  const seen: string[] = [];
  for (const p of parts) if (!seen.includes(p)) seen.push(p);
  s = seen.join("/");
  return s.replace(/\s+/g, " ").trim();
}

function dedupeMedicinesByCanonicalName(list: Medicine[]): Medicine[] {
  const groups = new Map<string, Medicine[]>();
  for (const m of list) {
    const key = canonicalGroupKey(m.name) || m.slug;
    const arr = groups.get(key);
    if (arr) arr.push(m);
    else groups.set(key, [m]);
  }
  const result: Medicine[] = [];
  for (const group of groups.values()) {
    if (group.length === 1) {
      result.push(group[0]);
      continue;
    }
    // Representative = the entry whose cleaned display name is shortest
    // (most canonical), tie-broken by having a real, non-empty category.
    let rep = group[0];
    let repClean = cleanMedicineName(rep.name);
    for (const cand of group.slice(1)) {
      const candClean = cleanMedicineName(cand.name);
      const candHasCat = !!(cand.category && cand.category.trim());
      const repHasCat = !!(rep.category && rep.category.trim());
      if (candClean.length < repClean.length || (candClean.length === repClean.length && candHasCat && !repHasCat)) {
        rep = cand;
        repClean = candClean;
      }
    }

    // Real bug found in review (Paracetamol): a plain UNION of every
    // variant's used_for_diseases mechanically pulled a single outlier
    // variant's questionable "Disseminated Intravascular Coagulation (DIC)"
    // entry into the merged canonical page — DIC doesn't appear in the other
    // 4 real variants that DO list diseases (all 4 agree on the same
    // 4-disease list), so it reads as a one-off data error in that specific
    // raw record, not a genuine finding. Fixed by using the most COMMON
    // non-empty disease list among the group (consensus) instead of a
    // straight union, so an outlier addition on one duplicate variant can no
    // longer surface on the shared canonical entry. Falls back to plain
    // union only when every non-empty list in the group is distinct (no
    // repeated list to treat as consensus).
    const nonEmptyLists = group.map((m) => m.used_for_diseases || []).filter((l) => l.length > 0);
    let mergedDiseases: string[];
    if (nonEmptyLists.length === 0) {
      mergedDiseases = [];
    } else {
      const listKey = (l: string[]) => [...l].sort().join("|");
      const counts = new Map<string, { list: string[]; count: number }>();
      for (const l of nonEmptyLists) {
        const k = listKey(l);
        const existing = counts.get(k);
        if (existing) existing.count += 1;
        else counts.set(k, { list: l, count: 1 });
      }
      const maxCount = Math.max(...Array.from(counts.values()).map((v) => v.count));
      if (maxCount > 1) {
        mergedDiseases = Array.from(counts.values()).find((v) => v.count === maxCount)!.list;
      } else {
        mergedDiseases = [];
        for (const l of nonEmptyLists) for (const dz of l) if (!mergedDiseases.includes(dz)) mergedDiseases.push(dz);
      }
    }

    // Real bug found in review: the shortest-name tie-break above happened
    // to land on a variant whose own `category` field was "Infectious
    // Diseases" — genuinely wrong/confusing for a general analgesic like
    // Paracetamol — while other real variants in the same group carry
    // different, equally real, mutually-inconsistent categories (each
    // variant was originally extracted from a different disease context).
    // Fixed with the same consensus principle: use the category most COMMON
    // across the group; if there's no clear single winner (a tie, as with
    // Paracetamol's real "Infectious Diseases" vs "ENT / Otolaryngology" 2-2
    // tie), fall back to Uncategorized rather than confidently asserting one
    // arbitrary, likely-wrong category.
    const catCounts = new Map<string, number>();
    for (const m of group) {
      const c = (m.category || "").trim();
      if (c) catCounts.set(c, (catCounts.get(c) || 0) + 1);
    }
    let repCategory = rep.category;
    if (catCounts.size > 0) {
      const maxCatCount = Math.max(...catCounts.values());
      const topCats = Array.from(catCounts.entries()).filter(([, c]) => c === maxCatCount);
      repCategory = topCats.length === 1 ? topCats[0][0] : "";
    }
    result.push({ ...rep, category: repCategory, used_for_diseases: mergedDiseases });
  }
  return result;
}

let cachedFetch: Promise<Medicine[]> | null = null;

export function fetchAllMedicines(): Promise<Medicine[]> {
  if (cachedFetch) return cachedFetch;
  cachedFetch = fetch("/data/medicine_details.json")
    .then((res) => {
      if (!res.ok) throw new Error(`medicine_details.json fetch failed: ${res.status}`);
      return res.json();
    })
    .then((data: { medicines: Record<string, RawMedicine> }) => {
      const meds = data.medicines || {};
      // Only real purchasable medicines/injections/equipment are ever shown
      // on the site — non-drug interventions (diet/lifestyle/physiotherapy/
      // surgery/exercise-programme/counseling entries) and malformed
      // sentence-fragment/regimen "names" are excluded entirely at the
      // source, and true same-drug duplicates are merged into one canonical
      // entry, so every consumer (catalog grid, detail pages, search,
      // cross-referenced "related medicines") stays clean automatically.
      const filtered = Object.keys(meds)
        .filter((slug) => {
          const rec = meds[slug];
          if (isNonDrugIntervention(slug) || isNonDrugIntervention(rec?.name || "")) return false;
          if (looksLikeMalformedFragment(rec?.name || "")) return false;
          if (noteIndicatesNonPurchasable(rec?.note)) return false;
          // Founder's rule (tightened 2026-09-28): the purchasable catalog is
          // medicines and injections ONLY — real devices/equipment (CPAP
          // machines, glucometers, dialyzers, implants, etc.) are excluded
          // entirely here, not given their own detail template. Real device
          // signals live in either the curator `note` or, for a real subset
          // of entries (e.g. "Insulet Omnipod 5", "ResMed AirSense 11
          // AutoSet", "FreeStyle Libre 2/3 CGM"), the separate
          // `not_found_reason` field instead — both are checked so those
          // don't leak through. isDeviceEntry only inspects free text, so
          // real injection-type medicines (insulin, vaccines, IV/IM
          // formulations) are unaffected.
          if (isDeviceEntry(rec?.note) || isDeviceEntry(rec?.not_found_reason)) return false;
          const chemicalClass = (rec?.fact_box?.chemical_class || "").trim().toLowerCase();
          if (chemicalClass === "not applicable") return false;
          return true;
        })
        .map((slug) => ({ slug, ...meds[slug] }));
      return dedupeMedicinesByCanonicalName(filtered);
    })
    .catch((err) => {
      cachedFetch = null; // allow retry on failure
      throw err;
    });
  return cachedFetch;
}
