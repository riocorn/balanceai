/**
 * Dynamic Indian meal generator.
 * Combines seasonal produce + cooking methods to generate contextual meal ideas.
 * No hard-coded dish names — builds combinations from ingredients.
 */

// Seasonal produce by month (1-indexed) + Indian state categories
const SEASONAL_PRODUCE: Record<string, string[]> = {
  // Post-monsoon (Sep-Oct): gourds, leafy greens, pomegranate, guava
  "9-default":  ["lauki","tinda","turai","karela","kaddu","palak","methi","moong","bajra","guava","pomegranate","banana","papaya"],
  "9-north":    ["sarson","lauki","tinda","palak","methi","aloo","gobhi","moong","bajra","guava","amla","gajar","matar"],
  "9-west":     ["lauki","turai","kaddu","moong","bajra","jowar","guava","papaya","banana","til","coconut","groundnut"],
  "9-south":    ["drumstick","raw banana","coconut","taro","spinach","tomato","ragi","tamarind","curry leaves","green mango"],
  "9-east":     ["parwal","pointed gourd","leafy greens","mustard greens","banana flower","raw papaya","lichi","coconut","rice","mustard oil"],
  // Winter (Nov-Feb)
  "11-default": ["gobhi","gajar","matar","palak","methi","sarson","mooli","bathua","aloo","apple","orange","amla"],
  "12-default": ["gobhi","gajar","matar","palak","methi","bathua","sarson","aloo","apple","orange","amla","bajra","makki"],
  // Summer (Mar-Jun)
  "4-default":  ["lauki","turai","torai","aam","mango","kela","papaya","sattu","chhachh","bel","litchi","kokum"],
  // Monsoon (Jul-Aug)
  "7-default":  ["karela","arbi","bhindi","lauki","corn","jamun","peach","plum","jackfruit","ragi","jowar"],
  "8-default":  ["karela","arbi","bhindi","lauki","corn","moong","guava early","banana","papaya","ragi","jowar","til"],
};

// Protein sources (vegetarian + optional non-veg)
const VEG_PROTEINS   = ["moong dal","masoor dal","chana dal","toor dal","urad dal","rajma","chana","paneer","dahi","soya","til","mungfali","akhrot","badam","besan"];
const NONVEG_PROTEINS= ["egg","chicken","fish","mutton"];

// Whole grains base
const GRAINS: Record<string,string[]> = {
  north: ["bajra roti","makki roti","gehun roti","dalia","khichdi"],
  south: ["ragi mudde","rice","appam batter","dosa batter","idli batter"],
  west:  ["jowar roti","bajra rotla","rice","besan dhokla"],
  east:  ["rice","dalia","sattu","panta bhat"],
  default:["gehun roti","bajra roti","brown rice","dalia","oats"],
};

// Cooking methods for sabzi
const SABZI_METHODS = ["dry sabzi","light tadka","sautéed","steamed","light curry","stir-fried"];
const DAL_STYLES    = ["simple dal","dal tadka","moong soup","thick dal","khichdi style"];

// Map state → region
function getRegion(state: string): string {
  const s = state.toLowerCase();
  if (["punjab","haryana","uttar pradesh","delhi","himachal","uttarakhand","rajasthan","jammu"].some(x=>s.includes(x))) return "north";
  if (["maharashtra","gujarat","goa","mp","madhya pradesh"].some(x=>s.includes(x))) return "west";
  if (["kerala","tamil","karnataka","andhra","telangana"].some(x=>s.includes(x))) return "south";
  if (["west bengal","odisha","assam","bihar","jharkhand","chhattisgarh"].some(x=>s.includes(x))) return "east";
  return "default";
}

// Get current month seasonal produce
function getProduce(state: string): string[] {
  const month = new Date().getMonth() + 1;
  const region = getRegion(state);
  return (
    SEASONAL_PRODUCE[`${month}-${region}`] ??
    SEASONAL_PRODUCE[`${month}-default`] ??
    SEASONAL_PRODUCE["9-default"]
  );
}

function pick<T>(arr: T[], n = 1): T[] {
  const out: T[] = [];
  const copy = [...arr];
  while (out.length < n && copy.length > 0) {
    const i = Math.floor(Math.random() * copy.length);
    out.push(copy.splice(i, 1)[0]);
  }
  return out;
}

function cap(s: string) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ── Meal generators ───────────────────────────────────────────

function makeBreakfast(produce: string[], grain: string[], isVeg: boolean, deficiencies: string[]): string[] {
  const meals: string[] = [];
  const greens = produce.filter(p => ["palak","methi","sarson","bathua","spinach"].includes(p));
  const fruits  = produce.filter(p => ["guava","banana","papaya","pomegranate","apple","orange","amla"].includes(p));
  const gourd   = produce.filter(p => ["lauki","tinda","turai","kaddu"].includes(p));

  // Option 1: Grain + dal protein (light)
  const g1 = pick(grain)[0] ?? "gehun roti";
  const dal1 = pick(VEG_PROTEINS.filter(x=>x.includes("dal")))[0] ?? "moong dal";
  meals.push(`${cap(dal1)} chilla with ${greens[0] ? greens[0] + " filling" : "dhaniya chutney"} + ${fruits[0] ?? "guava"}`);

  // Option 2: Oats/dalia porridge with fruit
  const fruit2 = pick(fruits, 2).join(" + ") || "banana";
  meals.push(`Dalia porridge with ${fruit2} + roasted til garnish`);

  // Option 3: Sabzi paratha (with current produce)
  const v3 = greens[0] ?? gourd[0] ?? produce[0] ?? "aloo";
  meals.push(`${cap(v3)} ka ${g1.includes("roti") ? "paratha" : "roti"} + dahi (lunch mein)`);

  // Option 4: Protein-forward if deficient in protein/iron
  if (deficiencies.includes("iron") || deficiencies.includes("protein")) {
    const p4 = isVeg ? (pick(VEG_PROTEINS)[0] ?? "moong dal") : (pick(NONVEG_PROTEINS)[0] ?? "egg");
    meals.push(`${cap(p4)} + ${g1} + nimbu paani (iron absorption ke liye)`);
  } else {
    meals.push(`${cap(fruits[0] ?? "papaya")} + roasted mungfali + ek glass doodh`);
  }

  return meals.slice(0, 4);
}

function makeLunch(produce: string[], grain: string[], isVeg: boolean, deficiencies: string[]): string[] {
  const meals: string[] = [];
  const greens = produce.filter(p => ["palak","methi","sarson","bathua","turai","bhindi","gobhi","gajar"].includes(p));
  const gourd  = produce.filter(p => ["lauki","tinda","karela","kaddu","arbi","drumstick"].includes(p));
  const protein = isVeg ? pick(VEG_PROTEINS.filter(x=>x.includes("dal")))[0] ?? "toor dal" : pick(NONVEG_PROTEINS)[0] ?? "masoor dal";
  const method  = pick(SABZI_METHODS)[0];
  const dalStyle= pick(DAL_STYLES)[0];
  const g       = pick(grain)[0] ?? "gehun roti";
  const sabzi1  = greens[0] ?? gourd[0] ?? produce[0] ?? "aloo";
  const sabzi2  = (greens[1] ?? gourd[1] ?? produce[2]) || "tamatar";

  meals.push(`${cap(protein)} (${dalStyle}) + ${cap(sabzi1)} ${method} + ${g} (2) + salad`);
  meals.push(`${cap(sabzi1)} + ${cap(sabzi2)} mixed sabzi + ${g} + dahi`);

  // Iron/calcium special
  if (deficiencies.includes("iron")) {
    const ironRich = ["palak","methi","rajma","kala chana","bathua"].find(x=>produce.includes(x) || true) ?? "palak";
    meals.push(`${cap(ironRich)} dal + ${g} + nimbu paani — iron max karo`);
  } else {
    const p3 = pick(VEG_PROTEINS)[0] ?? "rajma";
    meals.push(`${cap(p3)} + brown rice + ${Cap(greens[0] ?? "gobhi")} sabzi`);
  }

  if (deficiencies.includes("calcium")) {
    meals.push(`${cap(protein)} + ragi roti (2) + dahi + ${cap(greens[0] ?? "palak")} stir-fried`);
  } else {
    meals.push(`Mixed dal (moong+masoor) + ${g} + seasonal sabzi + salad`);
  }

  return meals.slice(0, 4);
}

function makeSnacks(produce: string[], _isVeg: boolean, deficiencies: string[]): string[] {
  const fruits = produce.filter(p => ["guava","banana","papaya","pomegranate","apple","orange","amla"].includes(p));
  const snacks: string[] = [];

  snacks.push(`${cap(fruits[0] ?? "guava")} + roasted mungfali (iron + Vitamin C combo)`);
  snacks.push("Roasted chana + ek glass nimbu paani");

  if (deficiencies.includes("omega3") || deficiencies.includes("magnesium")) {
    snacks.push("4-5 soaked akhrot + 2 khajoor");
  } else {
    snacks.push(`${cap(fruits[1] ?? "papaya")} chaat with jeera + kala namak`);
  }

  if (deficiencies.includes("vitamin_c")) {
    snacks.push("2-3 amla (fresh/pickle) + ek santara ya guava");
  } else {
    snacks.push("Makhane (fox nuts) roasted + ek cup green chai");
  }

  return snacks.slice(0, 4);
}

function makeDinner(produce: string[], grain: string[], isVeg: boolean, deficiencies: string[]): string[] {
  const meals: string[] = [];
  const light  = produce.filter(p => ["lauki","tinda","turai","moong","palak","pumpkin","kaddu"].includes(p));
  const g      = pick(grain.filter(x=>!x.includes("rice")))[0] ?? "gehun roti";
  const lightDal = ["moong dal","masoor dal","toor dal"].find(d => true) ?? "moong dal";

  // Dinner rule: no dahi/curd, light grains, dal + sabzi
  meals.push(`${cap(lightDal)} khichdi (dal + chawal + ghee) + ${cap(light[0] ?? "lauki")} sabzi — easy to digest`);
  meals.push(`${cap(light[0] ?? "lauki")} + ${Cap(light[1] ?? "tinda")} mixed sabzi + ${g} (2) + dal soup`);

  if (deficiencies.includes("iron")) {
    meals.push(`Palak + moong dal + bajra roti + nimbu squeeze — iron ke liye`);
  } else {
    meals.push(`${cap(lightDal)} tadka + ${g} (2) + ${Cap(light[0] ?? "turai")} stir-fried`);
  }

  if (isVeg) {
    meals.push(`Paneer + ${cap(light[0] ?? "palak")} ${pick(SABZI_METHODS)[0]} + ragi roti (calcium + protein)`);
  } else {
    meals.push(`Light ${pick(["egg bhurji","grilled fish","chicken soup"])[0] ?? "egg bhurji"} + ${g} + sabzi`);
  }

  return meals.slice(0, 4);
}

function Cap(s: string) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ── Public API ────────────────────────────────────────────────

export interface GeneratedMeals {
  breakfast: string[];
  lunch:     string[];
  snacks:    string[];
  dinner:    string[];
  produce:   string[];   // for display
}

export function generateMeals(
  state: string,
  isVeg: boolean,
  deficiencies: string[],
): GeneratedMeals {
  const produce = getProduce(state);
  const region  = getRegion(state);
  const grain   = GRAINS[region] ?? GRAINS.default;

  return {
    breakfast: makeBreakfast(produce, grain, isVeg, deficiencies),
    lunch:     makeLunch(produce, grain, isVeg, deficiencies),
    snacks:    makeSnacks(produce, isVeg, deficiencies),
    dinner:    makeDinner(produce, grain, isVeg, deficiencies),
    produce:   produce.slice(0, 6),
  };
}

// For the "Today's Remaining Plan" in diary — generate 1 suggestion per missing nutrient
export function quickSuggestion(nutrient: string, meal: string, state: string): string {
  const produce = getProduce(state);
  const grain   = getRegion(state);
  const g = (GRAINS[grain]?.[0]) ?? "gehun roti";
  const lightVeg = produce.find(p => ["palak","methi","lauki","tinda","turai","kaddu"].includes(p)) ?? "palak";
  const fruit    = produce.find(p => ["guava","amla","pomegranate","papaya","banana","orange"].includes(p)) ?? "guava";

  const map: Record<string,string> = {
    iron:        `${meal}: ${cap(lightVeg)} + moong dal + ${g} + nimbu paani`,
    vitamin_b12: `${meal}: Paneer ya dahi + ${g} + dal`,
    vitamin_d:   `Subah: 20 min dhoop + fortified doodh`,
    calcium:     `${meal}: Ragi roti + til chutney + dahi (agar lunch ho)`,
    zinc:        `${meal}: Kaju + pumpkin seeds + ${g}`,
    omega3:      `${meal}: 4-5 soaked akhrot + alsi ka powder ${g} mein`,
    magnesium:   `${meal}: Akhrot + ${cap(lightVeg)} sabzi + dark dal`,
    folate:      `${meal}: Hara dhaniya + rajma dal + ${g}`,
    vitamin_c:   `Abhi: ${cap(fruit)} ya amla ya nimbu paani`,
    vitamin_a:   `${meal}: Gajar + ${cap(lightVeg)} sabzi + ${g}`,
  };

  return map[nutrient] ?? `${cap(nutrient)} ke liye: ${cap(lightVeg)} + ${g}`;
}
