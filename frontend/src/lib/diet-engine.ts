import type { FoodItem } from "./food-db";
import { NUTRIENT_DAILY } from "./food-db";
import type { UserProfile } from "./db";
import { portionItem, type PortionedItem, type NutritionTargets } from "./nutrition-engine";
import { getMedicalAvoids, getMedicalBoosts, getMalabsorptionFlags } from "./disease-nutrition-map";

export type { PortionedItem };

export interface MealPlan {
  breakfast: PortionedItem[];
  lunch: PortionedItem[];
  snacks: PortionedItem[];
  dinner: PortionedItem[];
  targets?: NutritionTargets;
}

// Keywords for matching kitchen chip names → recipe names in RECIPE_DB
const KITCHEN_KEYWORDS: Record<string, string[]> = {
  "gehu atta":     ["roti", "paratha", "chapati", "wheat", "makki", "atta"],
  "chawal":        ["rice", "chawal", "khichdi", "biryani", "pulao"],
  "moong dal":     ["moong", "green gram"],
  "masoor dal":    ["masoor", "red lentil", "lentil"],
  "chana dal":     ["chana", "chickpea", "gram"],
  "rajma":         ["rajma", "kidney bean"],
  "palak":         ["palak", "spinach", "saag"],
  "methi":         ["methi", "fenugreek"],
  "aloo":          ["aloo", "potato"],
  "tamatar":       ["tomato", "tamatar"],
  "pyaz":          ["pyaz", "pyaaz", "onion"],
  "lehsun":        ["lehsun", "lahsun", "garlic"],
  "adrak":         ["adrak", "ginger"],
  "dahi":          ["dahi", "curd", "yogurt", "lassi"],
  "doodh":         ["milk", "doodh", "lassi"],
  "paneer":        ["paneer", "cheese"],
  "ghee":          ["ghee"],
  "tel":           ["tel", "oil"],
  "egg":           ["egg", "anda"],
  "chicken":       ["chicken", "murgi", "poultry"],
  "fish":          ["fish", "machli", "mackerel", "sardine", "tuna", "prawn", "seafood"],
  "mutton":        ["mutton", "lamb", "gosht", "goat"],
  "mango":         ["mango", "aam"],
  "banana":        ["banana", "kela"],
  "papaya":        ["papaya", "papita"],
  "amla":          ["amla", "gooseberry"],
  "orange":        ["orange", "citrus", "mosambi"],
  "akhrot":        ["akhrot", "walnut"],
  "badam":         ["badam", "almond"],
  "til":           ["til", "sesame"],
  "flaxseed":      ["flax", "alsi"],
  "pumpkin seeds": ["pumpkin", "kaddu"],
  "oats":          ["oats", "oatmeal"],
  "bajra":         ["bajra", "millet", "pearl millet"],
  "ragi":          ["ragi", "nachni", "finger millet"],
  "brown rice":    ["brown rice", "rice"],
};

function getKeywords(kitchenItem: string): string[] {
  const kl = kitchenItem.toLowerCase().trim();
  return KITCHEN_KEYWORDS[kl] ?? [kl.replace(/[()]/g, "").split(" ")[0]];
}

// Age/gender based RDA multipliers for key nutrients
function getRdaMultiplier(nutrient: string, profile?: UserProfile | null): number {
  if (!profile) return 1;
  const { age = 30, gender = "other" } = profile;
  const female = gender === "female";
  const senior = age >= 60;
  const child  = age < 18;

  if (nutrient === "iron")      return female ? (age < 50 ? 1.0 : 0.5) : 0.44; // women 18mg, men 8mg
  if (nutrient === "calcium")   return senior ? 1.2 : 1.0;
  if (nutrient === "vitamin_d") return senior ? 1.33 : 1.0;
  if (nutrient === "folate")    return female && age < 50 ? 1.0 : 0.75;
  if (nutrient === "iron" && child) return 0.61;
  return 1;
}

function nutrientScore(recipe: FoodItem, deficiencies: string[], profile?: UserProfile | null): number {
  return deficiencies.reduce((sum, d) => {
    const val = (recipe.nutrients[d] ?? 0) as number;
    const rda = (NUTRIENT_DAILY[d] ?? 1) * getRdaMultiplier(d, profile);
    return sum + Math.min((val / rda) * 100, 50);
  }, 0);
}

function kitchenMatch(recipe: FoodItem, kitchenItems: string[]): boolean {
  if (kitchenItems.length === 0) return true;
  const name = recipe.name.toLowerCase();
  const id   = recipe.id.toLowerCase();
  return kitchenItems.some((k) => {
    const keywords = getKeywords(k);
    return keywords.some((kw) => name.includes(kw) || id.includes(kw));
  });
}

function medicalFilter(recipe: FoodItem, medConditions: string[], avoidTerms: string[]): boolean {
  const name = recipe.name.toLowerCase();
  return !avoidTerms.some((a) => name.includes(a));
}

// Indian meal-time rules
// breakfast: light grains, fruits, dairy ok, no heavy non-veg curry
// lunch: all ok including dahi/raita
// snacks: fruits, nuts, light items only
// dinner: NO dahi/curd, NO heavy fried, prefer light grains + dal + sabzi
const MEAL_AVOID_KEYWORDS: Record<string, string[]> = {
  breakfast: ["fish curry", "mutton", "biryani", "pulao", "haleem", "nihari", "keema"],
  lunch:     [],
  snacks:    ["roti", "paratha", "biryani", "pulao", "mutton", "chicken curry", "dal makhani"],
  dinner:    ["dahi", "curd", "yogurt", "lassi", "chaas", "raita", "ice cream", "mishti doi",
               "puri", "bhature", "fried", "pakora", "samosa", "jalebi", "mango lassi"],
};
const SNACK_PREFERRED = ["fruit", "nuts", "seed", "roasted", "bhuna", "chana", "makhana",
                          "sprout", "salad", "chaas", "lassi", "amla", "guava", "pomegranate", "banana"];

function mealFilter(recipe: FoodItem, meal: string): boolean {
  const name = recipe.name.toLowerCase();
  const cat  = recipe.category.toLowerCase();
  const avoidKw = MEAL_AVOID_KEYWORDS[meal] ?? [];
  if (avoidKw.some((kw) => name.includes(kw) || cat.includes(kw))) return false;

  // Snacks: prefer fruits/nuts/light
  if (meal === "snacks") {
    const isLight = SNACK_PREFERRED.some((kw) => name.includes(kw) || cat.includes(kw));
    const isFruitOrNut = cat.includes("fruit") || cat.includes("snack") || cat.includes("nut");
    return isLight || isFruitOrNut;
  }
  // Dinner: no dairy main items, prefer grain+dal+sabzi
  if (meal === "dinner") {
    if (cat === "dairy" || cat === "beverage") return false;
    if (name.includes("doodh") || name.includes("milk")) return false;
  }
  // Breakfast: no heavy meat curries
  if (meal === "breakfast") {
    if (name.includes("nihari") || name.includes("haleem")) return false;
  }
  return true;
}

function pickForMeal(
  pool: FoodItem[],
  deficiencies: string[],
  kitchenItems: string[],
  medConditions: string[],
  isVeg: boolean,
  exclude: Set<string>,
  profile: UserProfile | null,
  count = 2,
  meal = "lunch",
  avoidTerms: string[] = [],
): FoodItem[] {
  const nonVegTerms = ["fish", "chicken", "mutton", "pork", "beef", "egg", "meat", "prawn", "duck", "mithun", "crab", "squid"];

  const candidates = pool.filter((r) => {
    if (exclude.has(r.id)) return false;
    if (!medicalFilter(r, medConditions, avoidTerms)) return false;
    if (isVeg && nonVegTerms.some((t) => r.name.toLowerCase().includes(t))) return false;
    if (!mealFilter(r, meal)) return false;
    return true;
  });

  const withKitchen = candidates.filter((r) => kitchenMatch(r, kitchenItems));
  const source = withKitchen.length >= count ? withKitchen : candidates;

  const scored = source.map((r) => ({ r, score: nutrientScore(r, deficiencies, profile) }));
  scored.sort((a, b) => b.score - a.score);

  // Group key for the underlying food regardless of prep state, tracked via the shared
  // `exclude` set (prefixed so it can't collide with a real id) — avoids picking e.g.
  // both "Moong Dal" and "Moong Dal (sprouted)" across meals in the same day's plan.
  // COMPREHENSIVE_FOOD_DB items carry a reliable `baseId`; other sources fall back to
  // stripping a trailing "(...)" state suffix from the name.
  const baseName = (r: FoodItem & { baseId?: string }) =>
    "base::" + (r.baseId ?? r.name.replace(/(\s*\([^)]*\))+\s*$/, "").trim().toLowerCase());

  const picked: FoodItem[] = [];
  for (const { r } of scored) {
    if (picked.length >= count) break;
    const bn = baseName(r);
    if (!exclude.has(r.id) && !exclude.has(bn)) {
      picked.push(r);
      exclude.add(r.id);
      exclude.add(bn);
    }
  }
  return picked;
}

// Compute nutrient totals across all portioned items
function sumNutrients(items: PortionedItem[]): Record<string, number> {
  const totals: Record<string, number> = {};
  for (const item of items) {
    for (const [k, v] of Object.entries(item.nutrients_total)) {
      totals[k] = (totals[k] ?? 0) + v;
    }
  }
  return totals;
}

// Pick one booster food for a specific nutrient gap
function pickBooster(
  pool: FoodItem[],
  targetNutrient: string,
  meal: string,
  kitchenItems: string[],
  medConditions: string[],
  isVeg: boolean,
  used: Set<string>,
  profile: UserProfile | null,
  avoidTerms: string[] = [],
): FoodItem | null {
  const nonVegTerms = ["fish", "chicken", "mutton", "pork", "beef", "egg", "meat", "prawn", "duck", "mithun", "crab", "squid"];
  const candidates = pool.filter((r) => {
    if (used.has(r.id)) return false;
    if (!medicalFilter(r, medConditions, avoidTerms)) return false;
    if (isVeg && nonVegTerms.some((t) => r.name.toLowerCase().includes(t))) return false;
    if (!mealFilter(r, meal)) return false;
    const val = (r.nutrients[targetNutrient] ?? 0) as number;
    return val > 0;
  });
  if (candidates.length === 0) return null;
  candidates.sort((a, b) => {
    const bv = (b.nutrients[targetNutrient] ?? 0) as number;
    const av = (a.nutrients[targetNutrient] ?? 0) as number;
    return bv - av;
  });
  // Prefer kitchen-available foods
  const withKitchen = candidates.filter((r) => kitchenMatch(r, kitchenItems));
  return (withKitchen[0] ?? candidates[0]);
}

export function generateDietPlan(
  recipeDB: FoodItem[],
  deficiencies: string[],
  kitchenItems: string[],
  userState: string,
  isVeg: boolean,
  medConditions: string[],
  profile: UserProfile | null = null,
  targets: NutritionTargets | null = null,
  // Low-weight signals only (e.g. Layer 4 visual-sign inference from photos —
  // a modest-accuracy image classifier). These NEVER drive primary meal selection;
  // they only get a chance in the lowest-priority gap-filling tier below, and only
  // for nutrients no stronger signal already flagged.
  weakDeficiencies: string[] = [],
): MealPlan {
  const statePriority = userState ? recipeDB.filter((r) => r.state === userState) : [];
  const rest = recipeDB.filter((r) => r.state !== userState);
  const pool = [...statePriority, ...rest];
  const used = new Set<string>();

  // Merge disease-specific nutrient boosts with incoming deficiencies (deduplicated)
  const diseaseBoosts = getMedicalBoosts(medConditions);
  const mergedDefs = [...new Set([...deficiencies, ...diseaseBoosts])];

  // Build avoid terms from all selected conditions (used in medicalFilter)
  const avoidTerms = getMedicalAvoids(medConditions);

  // Malabsorption flags (informational — the engine can't fix these via diet alone,
  // but we still try to boost the nutrient so the plan covers partial compensation)
  const _malabs = getMalabsorptionFlags(medConditions);

  // Pass 1: standard selection — 3 items each for B/L/D, 2 for snacks
  const bfRaw     = pickForMeal(pool, mergedDefs, kitchenItems, medConditions, isVeg, used, profile, 3, "breakfast", avoidTerms);
  const lunchRaw  = pickForMeal(pool, mergedDefs, kitchenItems, medConditions, isVeg, used, profile, 4, "lunch", avoidTerms);
  const snackRaw  = pickForMeal(pool, mergedDefs, kitchenItems, medConditions, isVeg, used, profile, 2, "snacks", avoidTerms);
  const dinnerRaw = pickForMeal(pool, mergedDefs, kitchenItems, medConditions, isVeg, used, profile, 4, "dinner", avoidTerms);

  const bfKcal  = targets?.meal_kcal.breakfast ?? 500;
  const luKcal  = targets?.meal_kcal.lunch     ?? 700;
  const snKcal  = targets?.meal_kcal.snacks    ?? 300;
  const diKcal  = targets?.meal_kcal.dinner    ?? 500;

  const portion = (raw: FoodItem[], kcalBudget: number): PortionedItem[] =>
    raw.map((r) => portionItem(r, kcalBudget, raw.length));

  const bf     = portion(bfRaw,    bfKcal);
  const lu     = portion(lunchRaw, luKcal);
  const sn     = portion(snackRaw, snKcal);
  const di     = portion(dinnerRaw, diKcal);

  // Pass 2: gap-filling — identify nutrients still <80% RDA and add boosters
  const rda = targets?.rda ?? NUTRIENT_DAILY;
  const allItems = [...bf, ...lu, ...sn, ...di];
  const totals = sumNutrients(allItems);

  // Find nutrients with gaps (< 80% of RDA), sorted by worst gap first
  const gaps = Object.keys(rda)
    .filter((k) => {
      const req = rda[k] ?? 0;
      if (req <= 0) return false;
      const pct = (totals[k] ?? 0) / req;
      return pct < 0.80;
    })
    .sort((a, b) => {
      const pctA = (totals[a] ?? 0) / (rda[a] ?? 1);
      const pctB = (totals[b] ?? 0) / (rda[b] ?? 1);
      return pctA - pctB; // worst gap first
    });

  // Weak signals are appended AFTER the real RDA-gap ranking — they only ever get
  // a booster slot if the top 8 primary gaps don't already fill the list, and never
  // for a nutrient a stronger signal (deficiencies/medConditions) already covers.
  const weakGaps = weakDeficiencies.filter((d) => !gaps.includes(d) && !mergedDefs.includes(d));
  const rankedGaps = [...gaps, ...weakGaps];

  // Meals for booster distribution (lunch and dinner can absorb extras best)
  const boosterMeals = ["lunch", "dinner", "breakfast", "snacks"] as const;
  const boosterBuckets: Record<string, FoodItem[]> = { lunch: [], dinner: [], breakfast: [], snacks: [] };

  for (const gap of rankedGaps.slice(0, 8)) { // address top 8 remaining gaps
    let added = false;
    for (const meal of boosterMeals) {
      // Cap: no meal gets more than 2 extra booster items
      if (boosterBuckets[meal].length >= 2) continue;
      const booster = pickBooster(pool, gap, meal, kitchenItems, medConditions, isVeg, used, profile, avoidTerms);
      if (booster) {
        boosterBuckets[meal].push(booster);
        used.add(booster.id);
        // Mark base name used too
        const bn = "base::" + booster.name.replace(/(\s*\([^)]*\))+\s*$/, "").trim().toLowerCase();
        used.add(bn);
        added = true;
        break;
      }
    }
    if (!added) continue;
  }

  // Portion and merge boosters into meals
  const portionBooster = (raw: FoodItem[], kcalBudget: number, existingCount: number): PortionedItem[] =>
    raw.map((r) => portionItem(r, kcalBudget * 0.4, existingCount + raw.length));

  return {
    breakfast: [...bf, ...portionBooster(boosterBuckets.breakfast, bfKcal, bfRaw.length)],
    lunch:     [...lu, ...portionBooster(boosterBuckets.lunch,     luKcal, lunchRaw.length)],
    snacks:    [...sn, ...portionBooster(boosterBuckets.snacks,    snKcal, snackRaw.length)],
    dinner:    [...di, ...portionBooster(boosterBuckets.dinner,    diKcal, dinnerRaw.length)],
    targets:   targets ?? undefined,
  };
}
