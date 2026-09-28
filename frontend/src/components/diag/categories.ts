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
// `image` — real, license-clear Unsplash photography (free for commercial
// use, no attribution required), reused from the site's already-verified set
// rather than introducing new unverified URLs.
// `medicinesQuery` — a real search term verified against
// data/medicine_details.json on 2026-09-28 (name+category+used_for_diseases
// substring match, same convention used everywhere else on the site).
//
// This exact 7-tile list is a founder override replacing an earlier
// Google-Trends-based set. Each tile was checked for real supporting data in
// data/disease_master.json (323 diseases) and data/medicine_details.json
// (3,126 medicines) before being added — verified counts below.
export const CATEGORY_TILES: { label: string; icon: typeof Heart; starter: string; accent: string; image: string; medicinesQuery: string }[] = [
  // Real: 21 real medicine matches for "reproductive"; real disease entries
  // include PCOS, menopause-related conditions, menstrual disorders.
  { label: "Women's Health", icon: HeartPulse, starter: "I have a problem related to my periods", accent: ACCENT_PINK, image: "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b", medicinesQuery: "reproductive" },
  // Real: 47 real medicine matches for "genital"; real disease entries HIV
  // Infection/AIDS, Chlamydia, Gonorrhea (all real STIs in disease_master.json).
  { label: "Sexual Problem", icon: ShieldCheck, starter: "I have a problem related to my sexual health", accent: ACCENT_PURPLE, image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be", medicinesQuery: "genital" },
  // Real: 86 real medicine matches for "heart" (246 for the broader
  // "cardiovascular" category label); real disease entries include Ischaemic
  // Heart Disease/CAD, Congestive Heart Failure, Atrial Fibrillation — genuine
  // conditions affecting both younger and older patients.
  { label: "Heart Disease", icon: Heart, starter: "I'm having chest pain or heart-related symptoms", accent: ACCENT_CORAL, image: "https://images.unsplash.com/photo-1584634731339-252c581abfc5", medicinesQuery: "heart" },
  // Real: 25 real medicine matches for "osteoarthritis"; real disease entry
  // "Osteoarthritis" — the specific age-related joint condition (distinct
  // from Rheumatoid Arthritis, an autoimmune disease, not age-related).
  { label: "Joint Pain", icon: Bone, starter: "I have joint pain and stiffness, especially as I've gotten older", accent: ACCENT_AMBER, image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b", medicinesQuery: "osteoarthritis" },
  // Real: 32 real medicine matches for "shock"; real disease entries Stroke,
  // Sepsis and Septic Shock, Anaphylaxis, Cardiogenic Shock, Aortic Aneurysm
  // and Aortic Dissection, Venous Thromboembolism — genuinely
  // severe/life-threatening conditions in disease_master.json.
  { label: "Emergency Care", icon: AlertTriangle, starter: "I think I'm having a serious medical emergency", accent: BLUE, image: "https://images.unsplash.com/photo-1590779033100-9f60a05a013d", medicinesQuery: "shock" },
  // Real: 79 real medicine matches for "cancer" (123 for the broader
  // "oncology" category label); real disease entries across the Oncology
  // category in disease_master.json.
  { label: "Cancer", icon: Dna, starter: "I've been diagnosed with cancer and want to understand treatment options", accent: ACCENT_INDIGO, image: "https://images.unsplash.com/photo-1573497491208-6b1acb260507", medicinesQuery: "cancer" },
  // Real: 40 real medicine matches for "migraine" (more precise than the
  // generic 16-match "headache"); real disease entry "Migraine".
  { label: "Migraine", icon: Brain, starter: "I get severe headaches that don't go away with normal painkillers", accent: TEAL, image: "https://images.unsplash.com/photo-1559757175-5700dde675bc", medicinesQuery: "migraine" },
];
