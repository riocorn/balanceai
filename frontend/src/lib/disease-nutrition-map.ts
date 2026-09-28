/**
 * Disease→Nutrition Deep Map — derived from BalanceAI Disease PDF groups 1-20
 * covering 200 diseases. ICMR-NIN 2020 / WHO / NEJM / Lancet sources.
 *
 * Keys match normalized condition identifiers used in diet-engine.ts.
 * boost    = nutrients to prioritize (boost score) in recipe selection
 * avoid    = food name substrings to exclude from recipe pool
 * malabs   = nutrients with absorption impairment (flag only, diet can partially compensate)
 */

export interface DiseaseProfile {
  boost: string[];
  avoid: string[];
  malabs: string[];
}

export const DISEASE_NUTRITION_MAP: Record<string, DiseaseProfile> = {

  // ── Metabolic / Endocrine ──────────────────────────────────────────────────
  diabetes: {
    boost: ["magnesium", "chromium", "zinc", "vitamin_d", "vitamin_c", "vitamin_e",
            "omega3", "vitamin_b1", "fiber", "potassium"],
    avoid: ["sugar", "jaggery", "mahua", "maida", "banana", "mango", "potato", "aloo",
            "fried", "sweetened", "biscuit", "candy", "mithai", "halwa", "gulab jamun",
            "rasgulla", "ice cream", "soft drink", "cola"],
    malabs: [],
  },
  insulin_resistance: {
    boost: ["magnesium", "chromium", "zinc", "vitamin_d", "omega3", "fiber", "vitamin_e"],
    avoid: ["sugar", "maida", "fried", "refined", "sweetened", "jaggery"],
    malabs: [],
  },
  obesity: {
    boost: ["fiber", "vitamin_d", "magnesium", "zinc", "vitamin_c", "protein"],
    avoid: ["sugar", "fried", "maida", "butter", "cream", "mithai", "ultra-processed"],
    malabs: [],
  },

  // ── Cardiovascular ────────────────────────────────────────────────────────
  bp_high: {
    boost: ["potassium", "magnesium", "calcium", "vitamin_d", "omega3", "fiber", "vitamin_c"],
    avoid: ["pickle", "achaar", "papad", "namkeen", "bujia", "mathri", "sev", "chatpata",
            "ghee", "butter", "cream", "dalda"],
    malabs: [],
  },
  heart_disease: {
    boost: ["omega3", "vitamin_e", "magnesium", "vitamin_d", "folate", "vitamin_c",
            "vitamin_k", "potassium", "fiber"],
    avoid: ["ghee", "butter", "cream", "mutton", "pork", "fried", "dalda", "trans fat",
            "maida", "sugar", "alcohol"],
    malabs: [],
  },
  cholesterol: {
    boost: ["omega3", "fiber", "vitamin_e", "vitamin_c", "folate", "vitamin_b3",
            "vitamin_d", "potassium"],
    avoid: ["ghee", "butter", "cream", "mutton", "pork", "fried", "dalda",
            "coconut oil", "refined sugar", "maida"],
    malabs: [],
  },
  stroke_prevention: {
    boost: ["omega3", "folate", "vitamin_b12", "vitamin_k", "potassium", "magnesium",
            "vitamin_c", "vitamin_e", "fiber"],
    avoid: ["saturated fat", "ghee", "butter", "pickle", "papad", "sodium", "fried"],
    malabs: [],
  },

  // ── Kidney / Urinary ──────────────────────────────────────────────────────
  kidney: {
    boost: ["vitamin_d", "vitamin_c", "iron", "vitamin_b12", "folate", "calcium",
            "omega3", "vitamin_e"],
    avoid: ["rajma", "chana", "lobiya", "soybean", "tofu", "banana", "potato", "aloo",
            "tamatar", "tomato", "pickle", "papad", "phosphorus", "salt", "excess protein",
            "mutton", "red meat"],
    malabs: ["vitamin_d"],
  },
  kidney_stones: {
    boost: ["magnesium", "vitamin_k", "vitamin_b6", "calcium", "vitamin_c"],
    avoid: ["palak", "spinach", "beet", "chocolate", "peanut", "excess salt",
            "excess protein", "soda"],
    malabs: [],
  },

  // ── Thyroid ───────────────────────────────────────────────────────────────
  thyroid: {
    boost: ["iodine", "selenium", "zinc", "iron", "vitamin_d", "vitamin_b12"],
    avoid: ["soy", "tofu", "soybean", "soya", "broccoli", "cabbage", "band gobi",
            "phool gobi", "cauliflower", "kale", "turnip"],
    malabs: [],
  },
  hashimoto: {
    boost: ["selenium", "vitamin_d", "zinc", "omega3", "vitamin_c"],
    avoid: ["soy", "tofu", "excess iodine", "broccoli", "cabbage", "cauliflower", "gluten"],
    malabs: [],
  },

  // ── Reproductive / Hormonal ───────────────────────────────────────────────
  pregnancy: {
    boost: ["iron", "folate", "calcium", "vitamin_d", "vitamin_b12", "iodine", "zinc",
            "omega3", "vitamin_c", "protein", "vitamin_a", "phosphorus"],
    avoid: [],
    malabs: [],
  },
  pcod: {
    boost: ["magnesium", "vitamin_d", "zinc", "chromium", "omega3", "vitamin_b6",
            "fiber", "selenium", "iron", "vitamin_c"],
    avoid: ["sugar", "maida", "fried", "refined", "jaggery", "mithai", "biscuit",
            "sweetened", "saturated fat"],
    malabs: [],
  },
  menopause: {
    boost: ["calcium", "vitamin_d", "magnesium", "omega3", "vitamin_e", "vitamin_k",
            "vitamin_b6", "folate"],
    avoid: ["caffeine", "alcohol", "refined sugar"],
    malabs: [],
  },
  male_hypogonadism: {
    boost: ["zinc", "vitamin_d", "selenium", "vitamin_e", "omega3", "vitamin_c"],
    avoid: ["excess alcohol", "refined sugar", "soy"],
    malabs: [],
  },

  // ── Nutritional Deficiencies ──────────────────────────────────────────────
  anaemia: {
    boost: ["iron", "vitamin_c", "vitamin_b12", "folate", "copper", "zinc",
            "vitamin_b6", "protein"],
    avoid: ["tea with meals", "coffee with meals"],
    malabs: [],
  },
  iron_deficiency: {
    boost: ["iron", "vitamin_c", "folate", "copper", "vitamin_b6"],
    avoid: ["tea with meals", "coffee with meals"],
    malabs: [],
  },
  b12_deficiency: {
    boost: ["vitamin_b12", "folate", "iron", "protein"],
    avoid: [],
    malabs: ["vitamin_b12"],
  },
  vitamin_d_deficiency: {
    boost: ["vitamin_d", "calcium", "phosphorus", "magnesium"],
    avoid: [],
    malabs: [],
  },
  calcium_deficiency: {
    boost: ["calcium", "vitamin_d", "vitamin_k", "magnesium", "phosphorus"],
    avoid: ["excess sodium", "excess caffeine"],
    malabs: [],
  },
  zinc_deficiency: {
    boost: ["zinc", "vitamin_a", "protein", "vitamin_b6"],
    avoid: ["excess phytates"],
    malabs: [],
  },
  iodine_deficiency: {
    boost: ["iodine", "selenium", "vitamin_a"],
    avoid: ["excess goitrogens"],
    malabs: [],
  },
  folate_deficiency: {
    boost: ["folate", "vitamin_b12", "iron", "vitamin_c"],
    avoid: ["excess alcohol"],
    malabs: [],
  },

  // ── Neurological / Mental ─────────────────────────────────────────────────
  depression: {
    boost: ["omega3", "folate", "vitamin_b12", "vitamin_d", "zinc", "magnesium",
            "vitamin_b6", "tryptophan", "selenium"],
    avoid: ["excess sugar", "alcohol", "refined carbs"],
    malabs: [],
  },
  anxiety: {
    boost: ["magnesium", "vitamin_b6", "vitamin_d", "omega3", "zinc", "vitamin_c",
            "folate", "vitamin_b12"],
    avoid: ["caffeine", "alcohol", "refined sugar"],
    malabs: [],
  },
  alzheimers_prevention: {
    boost: ["omega3", "vitamin_e", "folate", "vitamin_b12", "vitamin_d", "vitamin_c",
            "selenium", "zinc", "vitamin_b6"],
    avoid: ["saturated fat", "refined sugar", "alcohol", "ultra-processed"],
    malabs: [],
  },
  dementia_prevention: {
    boost: ["omega3", "vitamin_b12", "folate", "vitamin_d", "selenium", "vitamin_c",
            "vitamin_e", "zinc"],
    avoid: ["refined sugar", "saturated fat", "alcohol"],
    malabs: [],
  },
  parkinsons: {
    boost: ["omega3", "vitamin_d", "vitamin_c", "vitamin_e", "folate", "vitamin_b6",
            "magnesium"],
    avoid: ["saturated fat", "excess iron", "high protein with levodopa"],
    malabs: [],
  },
  migraine: {
    boost: ["magnesium", "vitamin_b2", "omega3", "vitamin_d", "coenzyme_q10"],
    avoid: ["tyramine", "caffeine", "alcohol", "nitrates", "msg"],
    malabs: [],
  },
  insomnia: {
    boost: ["magnesium", "vitamin_b6", "vitamin_d", "vitamin_b3", "vitamin_b12",
            "tryptophan", "calcium"],
    avoid: ["caffeine", "refined sugar", "alcohol", "heavy meal at night"],
    malabs: [],
  },
  chronic_fatigue: {
    boost: ["vitamin_d", "vitamin_b12", "folate", "vitamin_c", "magnesium", "zinc",
            "iron", "omega3"],
    avoid: ["excess caffeine", "alcohol", "refined sugar"],
    malabs: [],
  },

  // ── Gastrointestinal ──────────────────────────────────────────────────────
  ibd: {
    boost: ["iron", "vitamin_d", "folate", "zinc", "vitamin_b12", "calcium",
            "vitamin_c", "omega3", "selenium"],
    avoid: ["fried", "spicy", "alcohol", "raw vegetables in flare", "high fiber during flare"],
    malabs: ["iron", "vitamin_b12", "calcium", "zinc", "vitamin_d"],
  },
  ibs: {
    boost: ["fiber", "magnesium", "vitamin_d", "omega3", "probiotic"],
    avoid: ["fried", "spicy", "excess fructose", "lactose", "gluten"],
    malabs: [],
  },
  celiac: {
    boost: ["iron", "calcium", "vitamin_d", "folate", "zinc", "vitamin_b12",
            "vitamin_e", "magnesium"],
    avoid: ["wheat", "atta", "gehu", "maida", "semolina", "suji", "barley",
            "jau", "rye", "oats"],
    malabs: ["iron", "calcium", "folate", "zinc", "vitamin_b12", "vitamin_d"],
  },
  gerd: {
    boost: ["magnesium", "fiber", "vitamin_c"],
    avoid: ["fried", "spicy", "masala", "tomato", "tamatar", "citrus", "orange",
            "lemon", "nimbu", "coffee", "chocolate", "alcohol", "mint"],
    malabs: [],
  },
  liver_disease: {
    boost: ["zinc", "vitamin_d", "folate", "vitamin_b12", "vitamin_k", "vitamin_e",
            "vitamin_c", "selenium", "protein"],
    avoid: ["alcohol", "fried", "saturated fat", "excess iron", "raw shellfish",
            "moldy foods"],
    malabs: ["vitamin_a", "vitamin_d", "vitamin_e", "vitamin_k"],
  },
  nafld: {
    boost: ["vitamin_e", "omega3", "vitamin_d", "choline", "vitamin_c", "fiber",
            "selenium", "zinc"],
    avoid: ["fructose", "maida", "fried", "saturated fat", "alcohol", "sugar",
            "soft drink", "cola", "juice"],
    malabs: [],
  },

  // ── Bone / Joint / Muscle ─────────────────────────────────────────────────
  osteoporosis: {
    boost: ["calcium", "vitamin_d", "vitamin_k", "magnesium", "phosphorus", "protein",
            "zinc", "copper", "manganese"],
    avoid: ["excess sodium", "excess caffeine", "excess alcohol", "excess phytates"],
    malabs: [],
  },
  osteoarthritis: {
    boost: ["vitamin_d", "omega3", "vitamin_c", "zinc", "selenium", "vitamin_e",
            "magnesium", "calcium"],
    avoid: ["refined sugar", "saturated fat", "fried", "alcohol"],
    malabs: [],
  },
  rheumatoid_arthritis: {
    boost: ["omega3", "vitamin_d", "folate", "selenium", "vitamin_e", "vitamin_c",
            "zinc", "magnesium"],
    avoid: ["refined sugar", "saturated fat", "fried", "alcohol", "excess omega6"],
    malabs: [],
  },
  gout: {
    boost: ["vitamin_c", "fiber", "potassium", "folate", "magnesium"],
    avoid: ["mutton", "gosht", "lamb", "beef", "pork", "organ meat", "kidney", "liver",
            "sardine", "mackerel", "anchovy", "prawn", "shellfish", "alcohol", "fructose",
            "sugar", "maida", "soft drink", "juice"],
    malabs: [],
  },
  sarcopenia: {
    boost: ["protein", "vitamin_d", "calcium", "omega3", "zinc", "magnesium",
            "vitamin_c", "selenium"],
    avoid: ["excess alcohol"],
    malabs: [],
  },

  // ── Immune / Autoimmune ────────────────────────────────────────────────────
  lupus: {
    boost: ["vitamin_d", "omega3", "calcium", "vitamin_e", "selenium", "zinc",
            "vitamin_c", "folate"],
    avoid: ["excess protein", "alfalfa", "high saturated fat", "alcohol"],
    malabs: [],
  },
  multiple_sclerosis: {
    boost: ["vitamin_d", "omega3", "vitamin_b12", "vitamin_e", "selenium", "zinc",
            "vitamin_c", "magnesium"],
    avoid: ["saturated fat", "excess salt", "alcohol"],
    malabs: ["vitamin_b12"],
  },

  // ── Skin / Hair ───────────────────────────────────────────────────────────
  acne: {
    boost: ["zinc", "vitamin_a", "omega3", "vitamin_e", "selenium", "vitamin_c"],
    avoid: ["maida", "sugar", "fried", "high gi foods", "excess dairy", "chocolate"],
    malabs: [],
  },
  psoriasis: {
    boost: ["omega3", "vitamin_d", "selenium", "zinc", "vitamin_e", "vitamin_c",
            "folate"],
    avoid: ["alcohol", "red meat", "fried", "refined sugar", "excess nightshades"],
    malabs: [],
  },
  hair_loss: {
    boost: ["iron", "zinc", "vitamin_b7", "folate", "vitamin_d", "protein",
            "vitamin_c", "selenium"],
    avoid: ["crash dieting", "very low calorie"],
    malabs: [],
  },

  // ── Respiratory ───────────────────────────────────────────────────────────
  asthma: {
    boost: ["vitamin_d", "omega3", "magnesium", "vitamin_c", "vitamin_e", "selenium"],
    avoid: ["sulfites", "preservative", "processed", "fried", "excess dairy", "salt"],
    malabs: [],
  },
  copd: {
    boost: ["vitamin_d", "omega3", "vitamin_c", "vitamin_e", "selenium", "magnesium",
            "protein", "zinc"],
    avoid: ["saturated fat", "fried", "excess carbs"],
    malabs: [],
  },

  // ── Cancer Prevention ─────────────────────────────────────────────────────
  cancer_prevention: {
    boost: ["vitamin_d", "omega3", "folate", "selenium", "vitamin_c", "vitamin_e",
            "zinc", "fiber", "calcium", "vitamin_a"],
    avoid: ["processed meat", "sausage", "salami", "red meat excess", "alcohol",
            "excess salt", "smoked", "charred", "fried"],
    malabs: [],
  },

  // ── Ageing / Systemic ────────────────────────────────────────────────────
  chronic_inflammation: {
    boost: ["omega3", "selenium", "vitamin_c", "vitamin_d", "vitamin_e", "fiber",
            "zinc", "magnesium", "folate"],
    avoid: ["saturated fat", "trans fat", "refined sugar", "ultra-processed", "alcohol",
            "fried"],
    malabs: [],
  },
  long_covid: {
    boost: ["vitamin_d", "omega3", "vitamin_c", "magnesium", "zinc", "vitamin_b12",
            "selenium", "vitamin_e"],
    avoid: ["alcohol", "excess sugar", "ultra-processed"],
    malabs: [],
  },
  immunodeficiency: {
    boost: ["vitamin_c", "zinc", "selenium", "vitamin_d", "protein", "folate", "iron",
            "vitamin_a", "omega3"],
    avoid: ["alcohol", "excess sugar", "ultra-processed"],
    malabs: [],
  },

  // ── Eye ──────────────────────────────────────────────────────────────────
  eye_disease: {
    boost: ["vitamin_a", "vitamin_c", "vitamin_e", "zinc", "omega3", "selenium",
            "lutein", "folate"],
    avoid: ["excess sugar", "saturated fat", "refined carbs"],
    malabs: [],
  },

  // ── Hormonal / Sleep ─────────────────────────────────────────────────────
  adrenal_fatigue: {
    boost: ["vitamin_c", "vitamin_b5", "magnesium", "selenium", "vitamin_e",
            "zinc", "vitamin_b12"],
    avoid: ["refined sugar", "caffeine excess", "alcohol"],
    malabs: [],
  },
  gallstones: {
    boost: ["vitamin_c", "fiber", "calcium", "magnesium", "omega3"],
    avoid: ["saturated fat", "fried", "maida", "refined sugar", "alcohol"],
    malabs: [],
  },
  hyperlipidemia: {
    boost: ["omega3", "fiber", "vitamin_e", "vitamin_c", "folate", "vitamin_b3",
            "vitamin_d", "potassium"],
    avoid: ["ghee", "butter", "cream", "mutton", "pork", "fried", "dalda",
            "refined sugar", "maida"],
    malabs: [],
  },

  // ── Paediatric ───────────────────────────────────────────────────────────
  stunting: {
    boost: ["protein", "zinc", "iron", "vitamin_a", "vitamin_d", "calcium", "iodine",
            "folate", "energy"],
    avoid: [],
    malabs: [],
  },
  wasting: {
    boost: ["protein", "energy", "zinc", "vitamin_a", "iron", "vitamin_d", "folate",
            "vitamin_c"],
    avoid: [],
    malabs: [],
  },

  // ── Oral / Dental ────────────────────────────────────────────────────────
  dental_issues: {
    boost: ["calcium", "vitamin_d", "vitamin_k", "phosphorus", "vitamin_c", "zinc"],
    avoid: ["sugar", "refined carbs", "acidic drinks", "soda", "cola"],
    malabs: [],
  },

  // ── Psychiatric ──────────────────────────────────────────────────────────
  schizophrenia: {
    boost: ["omega3", "folate", "vitamin_b12", "vitamin_d", "zinc", "vitamin_c"],
    avoid: ["excess caffeine", "alcohol"],
    malabs: [],
  },
  bipolar: {
    boost: ["omega3", "magnesium", "vitamin_d", "folate", "vitamin_b12", "zinc"],
    avoid: ["caffeine", "alcohol", "refined sugar"],
    malabs: [],
  },
  adhd: {
    boost: ["omega3", "zinc", "iron", "magnesium", "vitamin_d", "folate",
            "vitamin_b12"],
    avoid: ["artificial dyes", "excess sugar", "preservatives"],
    malabs: [],
  },
  autism: {
    boost: ["omega3", "vitamin_d", "folate", "zinc", "vitamin_b12", "magnesium",
            "selenium"],
    avoid: ["gluten", "excess casein (dairy)"],
    malabs: [],
  },
};

// ── UI label → normalized key ─────────────────────────────────────────────────
// Maps the chip labels from analyze/page.tsx MEDICAL_OPTIONS to map keys above.
const LABEL_TO_KEY: Record<string, string> = {
  "diabetes / sugar":           "diabetes",
  "high bp":                    "bp_high",
  "thyroid":                    "thyroid",
  "pregnancy / breastfeeding":  "pregnancy",
  "kidney disease":             "kidney",
  "high cholesterol":           "cholesterol",
  "anaemia":                    "anaemia",
  "pcod / pcos":                "pcod",
  // extras (free-text or future chips)
  "high cholesterol/tg":        "cholesterol",
  "hyperlipidemia":             "hyperlipidemia",
  "diabetes":                   "diabetes",
  "anaemia / anemia":           "anaemia",
  "rheumatoid arthritis":       "rheumatoid_arthritis",
  "osteoporosis":               "osteoporosis",
  "depression":                 "depression",
  "anxiety":                    "anxiety",
  "gout":                       "gout",
  "ibs":                        "ibs",
  "ibd":                        "ibd",
  "celiac":                     "celiac",
  "gerd / acid reflux":         "gerd",
  "insomnia":                   "insomnia",
  "asthma":                     "asthma",
  "hair loss":                  "hair_loss",
  "acne":                       "acne",
};

export function normalizeCondition(label: string): string {
  return LABEL_TO_KEY[label.toLowerCase().trim()] ?? label.toLowerCase().trim();
}

export function getMedicalBoosts(medConditions: string[]): string[] {
  const boosts = new Set<string>();
  for (const cond of medConditions) {
    const key = normalizeCondition(cond);
    const profile = DISEASE_NUTRITION_MAP[key];
    if (profile) profile.boost.forEach((n) => boosts.add(n));
  }
  return Array.from(boosts);
}

export function getMedicalAvoids(medConditions: string[]): string[] {
  const avoids = new Set<string>();
  for (const cond of medConditions) {
    const key = normalizeCondition(cond);
    const profile = DISEASE_NUTRITION_MAP[key];
    if (profile) profile.avoid.forEach((a) => avoids.add(a));
  }
  return Array.from(avoids);
}

export function getMalabsorptionFlags(medConditions: string[]): string[] {
  const flags = new Set<string>();
  for (const cond of medConditions) {
    const key = normalizeCondition(cond);
    const profile = DISEASE_NUTRITION_MAP[key];
    if (profile) profile.malabs.forEach((n) => flags.add(n));
  }
  return Array.from(flags);
}
