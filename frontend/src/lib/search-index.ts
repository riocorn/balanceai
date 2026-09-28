import Fuse from "fuse.js";
import { fetchAllMedicines, cleanMedicineName, type Medicine } from "./medicines";

// Real, lightweight disease-name index for the navbar's instant autocomplete
// — a direct id/name/category projection of the real data/disease_master.json
// (323 diseases), extracted once into public/data/disease_index.json because
// the full source file is ~20.5MB (symptoms, staged severity models, etc.)
// which would make every page's navbar search fetch a 20MB file just to
// autocomplete disease names. No disease name/category is invented — every
// entry here is copied verbatim from the same real disease_master.json every
// other page on the site reads from. The medicine side of this index reuses
// the existing fetchAllMedicines() cache from lib/medicines.ts as-is (shared
// with the /medicines catalog and detail pages), per instruction.
export interface DiseaseEntry {
  id: string;
  name: string;
  category: string;
}

let cachedDiseases: Promise<DiseaseEntry[]> | null = null;

export function fetchAllDiseases(): Promise<DiseaseEntry[]> {
  if (cachedDiseases) return cachedDiseases;
  cachedDiseases = fetch("/data/disease_index.json")
    .then((res) => {
      if (!res.ok) throw new Error(`disease_index.json fetch failed: ${res.status}`);
      return res.json();
    })
    .then((data: DiseaseEntry[]) => data)
    .catch((err) => {
      cachedDiseases = null;
      throw err;
    });
  return cachedDiseases;
}

let medicineFuse: Fuse<Medicine> | null = null;
let diseaseFuse: Fuse<DiseaseEntry> | null = null;
let indexPromise: Promise<void> | null = null;

// Lazily builds both Fuse indices the first time the navbar search is used,
// so page load itself never pays for fetching+indexing the ~3,126-medicine
// and 323-disease catalogs. Once built, every keystroke's search is a pure
// in-memory Fuse lookup — no network round-trip, no lag.
export function ensureSearchIndex(): Promise<void> {
  if (indexPromise) return indexPromise;
  indexPromise = Promise.all([fetchAllMedicines(), fetchAllDiseases()]).then(([meds, diseases]) => {
    medicineFuse = new Fuse(meds, {
      keys: ["name"],
      threshold: 0.3,
      ignoreLocation: true,
      minMatchCharLength: 2,
    });
    diseaseFuse = new Fuse(diseases, {
      keys: ["name"],
      threshold: 0.3,
      ignoreLocation: true,
      minMatchCharLength: 2,
    });
  });
  return indexPromise;
}

export interface MedicineMatch {
  type: "medicine";
  slug: string;
  displayName: string;
  score: number;
}

export interface DiseaseMatch {
  type: "disease";
  id: string;
  name: string;
  score: number;
}

// Devanagari script (Hindi/Hinglish-in-Hindi-script) can't be meaningfully
// fuzzy-matched against our English-only medicine/disease name catalog, so
// this input is detected up front and routed straight to the real AI
// symptom-checker instead of wasting a cycle on a fuzzy search that can only
// ever fail.
const DEVANAGARI_RE = /[ऀ-ॿ]/;
export function isNonLatinScript(text: string): boolean {
  return DEVANAGARI_RE.test(text);
}

// Fuse already returns results sorted by score (lower/better first), but a
// short exact-prefix hit (typing "Para" for "Paracetamol") should always
// outrank a looser fuzzy hit even when Fuse scores them close together —
// this re-sort promotes case-insensitive prefix matches to the front while
// preserving Fuse's own ordering within each group.
function boostPrefixMatches<T extends { score: number }>(results: T[], query: string, getName: (item: T) => string): T[] {
  const q = query.trim().toLowerCase();
  const prefix: T[] = [];
  const rest: T[] = [];
  for (const r of results) {
    if (getName(r).toLowerCase().startsWith(q)) prefix.push(r);
    else rest.push(r);
  }
  return [...prefix, ...rest];
}

export function searchMedicines(query: string, limit = 5): MedicineMatch[] {
  const q = query.trim();
  if (!medicineFuse || q.length < 2 || isNonLatinScript(q)) return [];
  const results = medicineFuse.search(q, { limit: limit * 2 }).map((r) => ({
    type: "medicine" as const,
    slug: r.item.slug,
    displayName: cleanMedicineName(r.item.name),
    score: r.score ?? 1,
  }));
  return boostPrefixMatches(results, q, (r) => r.displayName).slice(0, limit);
}

export function searchDiseases(query: string, limit = 5): DiseaseMatch[] {
  const q = query.trim();
  if (!diseaseFuse || q.length < 2 || isNonLatinScript(q)) return [];
  const results = diseaseFuse.search(q, { limit: limit * 2 }).map((r) => ({
    type: "disease" as const,
    id: r.item.id,
    name: r.item.name,
    score: r.score ?? 1,
  }));
  return boostPrefixMatches(results, q, (r) => r.name).slice(0, limit);
}

// A result is treated as a confident "this is a real medicine/condition name"
// match (rather than a free-text symptom sentence) only when Fuse's own
// score is very low (near-exact/prefix match). Longer natural-language
// sentences ("I've had a fever for 3 days", "mujhe bukhar hai") don't score
// this well against short catalog names, so they correctly fall through to
// the real AI symptom-checker instead of a wrong "best guess" name match.
export const STRONG_MATCH_THRESHOLD = 0.3;
