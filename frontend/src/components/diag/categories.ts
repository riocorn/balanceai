import {
  HeartPulse,
  ShieldCheck,
  Heart,
  Bone,
  AlertTriangle,
  Dna,
  Brain,
} from "lucide-react";
import { TEAL, BLUE, ACCENT_CORAL, ACCENT_AMBER, ACCENT_PURPLE, ACCENT_INDIGO, ACCENT_PINK } from "./theme";

// Shared "browse by category" quick-start list used by the symptom-checker
// hero/category rail and, on other pages, by the shared header's Row C
// quick-link strip (which deep-links into the symptom checker with the
// starter phrase pre-filled). UI copy and example text are English-only per
// the locked site-language rule; the real /medical/query API underneath is
// unchanged and still understands Hindi/Hinglish/English input typed by hand.
// Each tile gets its own accent from the approved secondary palette (real
// 1mg/Netmeds category rails use varied colors per category, not one single
// brand color repeated everywhere) — never the reserved EMERGENCY red, even
// for the "Critical Life-Taking Disease Solution" tile below.
//
// Founder redesign directive (2026-09-29): tiles no longer carry a stock
// photo — the category rail (components/diag/CategoryRail.tsx) renders every
// tile as one uniform surface-color circle with the tile's own `icon` in its
// `accent` color, never a tinted Unsplash photo. The `image` field this data
// used to carry has been removed for the same reason.
// `medicinesQuery` — a real search term verified against
// data/medicine_details.json on 2026-09-28 (name+category+used_for_diseases
// substring match, same convention used everywhere else on the site).
//
// This exact 7-tile list is a founder override replacing an earlier
// Google-Trends-based set. Each tile was checked for real supporting data in
// data/disease_master.json (323 diseases) and data/medicine_details.json
// (3,126 medicines) before being added — verified counts below.
export const CATEGORY_TILES: { label: string; icon: typeof Heart; starter: string; accent: string; medicinesQuery: string }[] = [
  // Real: 21 real medicine matches for "reproductive"; real disease entries
  // include PCOS, menopause-related conditions, menstrual disorders.
  { label: "Women's Health", icon: HeartPulse, starter: "I have a problem related to my periods", accent: ACCENT_PINK, medicinesQuery: "reproductive" },
  // Real: 47 real medicine matches for "genital"; real disease entries HIV
  // Infection/AIDS, Chlamydia, Gonorrhea (all real STIs in disease_master.json).
  { label: "Sexual Problem", icon: ShieldCheck, starter: "I have a problem related to my sexual health", accent: ACCENT_PURPLE, medicinesQuery: "genital" },
  // Real: 86 real medicine matches for "heart" (246 for the broader
  // "cardiovascular" category label); real disease entries include Ischaemic
  // Heart Disease/CAD, Congestive Heart Failure, Atrial Fibrillation — genuine
  // conditions affecting both younger and older patients.
  { label: "Heart Disease", icon: Heart, starter: "I'm having chest pain or heart-related symptoms", accent: ACCENT_CORAL, medicinesQuery: "heart" },
  // Real: 25 real medicine matches for "osteoarthritis"; real disease entry
  // "Osteoarthritis" — the specific age-related joint condition (distinct
  // from Rheumatoid Arthritis, an autoimmune disease, not age-related).
  { label: "Joint Pain", icon: Bone, starter: "I have joint pain and stiffness, especially as I've gotten older", accent: ACCENT_AMBER, medicinesQuery: "osteoarthritis" },
  // Real: 32 real medicine matches for "shock"; real disease entries Stroke,
  // Sepsis and Septic Shock, Anaphylaxis, Cardiogenic Shock, Aortic Aneurysm
  // and Aortic Dissection, Venous Thromboembolism — genuinely
  // severe/life-threatening conditions in disease_master.json.
  { label: "Emergency Care", icon: AlertTriangle, starter: "I think I'm having a serious medical emergency", accent: BLUE, medicinesQuery: "shock" },
  // Real: 79 real medicine matches for "cancer" (123 for the broader
  // "oncology" category label); real disease entries across the Oncology
  // category in disease_master.json.
  { label: "Cancer", icon: Dna, starter: "I've been diagnosed with cancer and want to understand treatment options", accent: ACCENT_INDIGO, medicinesQuery: "cancer" },
  // Real: 40 real medicine matches for "migraine" (more precise than the
  // generic 16-match "headache"); real disease entry "Migraine".
  { label: "Migraine", icon: Brain, starter: "I get severe headaches that don't go away with normal painkillers", accent: TEAL, medicinesQuery: "migraine" },
];
