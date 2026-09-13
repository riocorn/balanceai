import type { FoodItem } from "./food-db";
import { NUTRIENT_DAILY } from "./food-db";
import type { UserProfile } from "./db";
import { portionItem, type PortionedItem, type NutritionTargets } from "./nutrition-engine";

export type { PortionedItem };

export interface MealPlan {
  breakfast: PortionedItem[];
  lunch: PortionedItem[];
  snacks: PortionedItem[];
  dinner: PortionedItem[];
  targets?: NutritionTargets;
}

const MEDICAL_AVOID: Record<string, string[]> = {
  diabetes:     ["sugar", "mahua", "banana", "mango", "potato", "jaggery", "aloo"],
  bp_high:      ["pickle", "papad", "ghee", "namkeen", "bujia"],
  kidney:       ["rajma", "chana", "phosphorus"],
  thyroid:      ["soy", "broccoli", "cabbage"],
  pregnancy:    [],
  cholesterol:  ["ghee", "butter", "cream", "mutton", "pork"],
  pcod:         ["sugar", "maida", "fried"],
};

// Keywords for matching kitchen chip names → recipe names in RECIPE_DB
const KITCHEN_KEYWORDS: Record<string, string[]> = {
  "atta":          ["roti", "paratha", "chapati", "wheat", "makki"],
  "chawal":        ["rice", "chawal", "khichdi", "biryani", "pulao"],
  "dal (moong)":   ["moong", "green gram"],
  "dal (masoor)":  ["masoor", "red lentil", "lentil"],
  "dal (chana)":   ["chana", "chickpea", "gram"],
  "rajma":         ["rajma", "kidney bean"],
  "palak":         ["palak", "spinach", "saag"],
  "methi":         ["methi", "fenugreek"],
  "aloo":          ["aloo", "potato"],
  "tamatar":       ["tomato", "tamatar"],
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

function medicalFilter(recipe: FoodItem, medConditions: string[]): boolean {
  const name = recipe.name.toLowerCase();
  for (const cond of medConditions) {
    const avoidList = MEDICAL_AVOID[cond] ?? [];
    if (avoidList.some((a) => name.includes(a))) return false;
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
): FoodItem[] {
  const nonVegTerms = ["fish", "chicken", "mutton", "pork", "beef", "egg", "meat", "prawn", "duck", "mithun", "crab", "squid"];

  const candidates = pool.filter((r) => {
    if (exclude.has(r.id)) return false;
    if (!medicalFilter(r, medConditions)) return false;
    if (isVeg && nonVegTerms.some((t) => r.name.toLowerCase().includes(t))) return false;
    return true;
  });

  const withKitchen = candidates.filter((r) => kitchenMatch(r, kitchenItems));
  const source = withKitchen.length >= count ? withKitchen : candidates;

  const scored = source.map((r) => ({ r, score: nutrientScore(r, deficiencies, profile) }));
  scored.sort((a, b) => b.score - a.score);

  const picked: FoodItem[] = [];
  for (const { r } of scored) {
    if (picked.length >= count) break;
    if (!exclude.has(r.id)) {
      picked.push(r);
      exclude.add(r.id);
    }
  }
  return picked;
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
): MealPlan {
  const statePriority = userState ? recipeDB.filter((r) => r.state === userState) : [];
  const rest = recipeDB.filter((r) => r.state !== userState);
  const pool = [...statePriority, ...rest];
  const used = new Set<string>();

  const bfRaw  = pickForMeal(pool, deficiencies, kitchenItems, medConditions, isVeg, used, profile, 2);
  const lunchRaw  = pickForMeal(pool, deficiencies, kitchenItems, medConditions, isVeg, used, profile, 3);
  const snackRaw  = pickForMeal(pool, deficiencies, kitchenItems, medConditions, isVeg, used, profile, 2);
  const dinnerRaw = pickForMeal(pool, deficiencies, kitchenItems, medConditions, isVeg, used, profile, 3);

  const portion = (raw: FoodItem[], kcalBudget: number): PortionedItem[] =>
    raw.map((r) => portionItem(r, kcalBudget, raw.length));

  const bfKcal  = targets?.meal_kcal.breakfast ?? 500;
  const luKcal  = targets?.meal_kcal.lunch     ?? 700;
  const snKcal  = targets?.meal_kcal.snacks    ?? 300;
  const diKcal  = targets?.meal_kcal.dinner    ?? 500;

  return {
    breakfast: portion(bfRaw,  bfKcal),
    lunch:     portion(lunchRaw,  luKcal),
    snacks:    portion(snackRaw,  snKcal),
    dinner:    portion(dinnerRaw, diKcal),
    targets:   targets ?? undefined,
  };
}
