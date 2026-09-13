export interface FoodItem {
  id: string;
  name: string;
  hindi?: string;
  category: string;
  state?: string;
  serving: string;
  nutrients: Partial<Record<string, number>>;
}

const N = (iron = 0, b12 = 0, vd = 0, ca = 0, zn = 0, o3 = 0, fo = 0, va = 0, mg = 0) =>
  ({ iron, vitamin_b12: b12, vitamin_d: vd, calcium: ca, zinc: zn, omega3: o3, folate: fo, vitamin_a: va, magnesium: mg });

export const FOOD_DB: FoodItem[] = [
  // Dal / Legumes
  { id: "masoor_dal",  name: "Masoor Dal",    hindi: "मसूर दाल",   category: "Dal",      serving: "1 katori (100g)", nutrients: N(3.3, 0, 0, 56, 1.1, 0.1, 181, 0, 36) },
  { id: "moong_dal",   name: "Moong Dal",     hindi: "मूंग दाल",   category: "Dal",      serving: "1 katori (100g)", nutrients: N(1.4, 0, 0, 54, 0.8, 0.1, 159, 1, 34) },
  { id: "rajma",       name: "Rajma",         hindi: "राजमा",      category: "Dal",      serving: "1 katori (100g)", nutrients: N(2.9, 0, 0, 83, 1.8, 0.2, 130, 0, 45) },
  { id: "chana_dal",   name: "Chana Dal",     hindi: "चना दाल",   category: "Dal",      serving: "1 katori (100g)", nutrients: N(4.1, 0, 0, 105, 2.1, 0.1, 172, 0, 48) },
  { id: "urad_dal",    name: "Urad Dal",      hindi: "उड़द दाल",   category: "Dal",      serving: "1 katori (100g)", nutrients: N(7.6, 0, 0, 138, 3.4, 0, 216, 0, 138) },
  // Grains / Rotis
  { id: "wheat_roti",  name: "Wheat Roti",    hindi: "गेहूं रोटी",  category: "Grain",    serving: "2 roti (70g)",    nutrients: N(3.9, 0, 0, 34, 1.6, 0, 43, 0, 75) },
  { id: "bajra_roti",  name: "Bajra Roti",    hindi: "बाजरा रोटी", category: "Grain",    serving: "2 roti (70g)",    nutrients: N(8, 0, 0, 54, 2.8, 0, 85, 0, 114) },
  { id: "ragi_roti",   name: "Ragi Roti",     hindi: "रागी रोटी",  category: "Grain",    serving: "2 roti (70g)",    nutrients: N(3.9, 0, 0, 344, 2.5, 0, 34, 0, 137) },
  { id: "brown_rice",  name: "Brown Rice",    hindi: "ब्राउन चावल", category: "Grain",   serving: "1 cup (180g)",    nutrients: N(0.5, 0, 0, 10, 1.2, 0, 14, 0, 84) },
  { id: "oats",        name: "Oats",          hindi: "जई",         category: "Grain",    serving: "1 cup (80g)",     nutrients: N(2.1, 0, 0, 21, 1.9, 0.1, 56, 0, 57) },
  // Vegetables
  { id: "palak",       name: "Palak",         hindi: "पालक",       category: "Sabzi",    serving: "1 bowl (100g)",   nutrients: N(2.7, 0, 0, 99, 0.5, 0.1, 194, 469, 79) },
  { id: "methi",       name: "Methi Saag",    hindi: "मेथी",       category: "Sabzi",    serving: "1 bowl (100g)",   nutrients: N(1.9, 0, 0, 176, 0.9, 0, 57, 395, 62) },
  { id: "broccoli",    name: "Broccoli",      hindi: "ब्रोकोली",   category: "Sabzi",    serving: "1 cup (90g)",     nutrients: N(0.7, 0, 0, 47, 0.4, 0.3, 63, 623, 19) },
  { id: "carrot",      name: "Carrot",        hindi: "गाजर",       category: "Sabzi",    serving: "1 medium (80g)",  nutrients: N(0.3, 0, 0, 33, 0.2, 0, 19, 835, 11) },
  { id: "sweet_potato",name: "Sweet Potato",  hindi: "शकरकंद",     category: "Sabzi",    serving: "1 medium (100g)", nutrients: N(0.6, 0, 0, 30, 0.3, 0, 11, 961, 25) },
  { id: "chukandar",   name: "Chukandar",     hindi: "चुकंदर",     category: "Sabzi",    serving: "1 cup (136g)",    nutrients: N(1.1, 0, 0, 16, 0.5, 0, 148, 0, 31) },
  // Dairy
  { id: "dahi",        name: "Dahi",          hindi: "दही",        category: "Dairy",    serving: "1 cup (245g)",    nutrients: N(0.1, 1.4, 2.9, 296, 1.1, 0, 17, 14, 27) },
  { id: "paneer",      name: "Paneer",        hindi: "पनीर",       category: "Dairy",    serving: "100g",            nutrients: N(0.2, 0.8, 0, 476, 1.5, 0, 7, 130, 13) },
  { id: "milk",        name: "Doodh",         hindi: "दूध",        category: "Dairy",    serving: "1 glass (240ml)", nutrients: N(0.1, 1.2, 2.5, 298, 0.9, 0, 12, 56, 24) },
  // Eggs & Non-veg
  { id: "egg",         name: "Egg",           hindi: "अंडा",       category: "Protein",  serving: "2 eggs (100g)",   nutrients: N(1.9, 2.4, 2.2, 56, 1.3, 0.1, 47, 160, 12) },
  { id: "chicken",     name: "Chicken",       hindi: "चिकन",       category: "Protein",  serving: "100g cooked",     nutrients: N(1.3, 0.9, 0, 15, 2.1, 0.1, 9, 0, 28) },
  { id: "fish_mackerel",name:"Mackerel",      hindi: "बांगडा",     category: "Protein",  serving: "100g cooked",     nutrients: N(1.5, 19, 16, 66, 0.8, 2.7, 1, 50, 76) },
  // Fruits
  { id: "banana",      name: "Banana",        hindi: "केला",       category: "Fruit",    serving: "1 medium (100g)", nutrients: N(0.3, 0, 0, 5, 0.2, 0, 20, 3, 27) },
  { id: "papaya",      name: "Papaya",        hindi: "पपीता",      category: "Fruit",    serving: "1 cup (145g)",    nutrients: N(0.1, 0, 0, 25, 0.1, 0, 53, 1009, 14) },
  { id: "orange",      name: "Orange",        hindi: "संतरा",      category: "Fruit",    serving: "1 medium (130g)", nutrients: N(0.1, 0, 0, 52, 0.1, 0, 40, 225, 11) },
  { id: "amla",        name: "Amla",          hindi: "आंवला",      category: "Fruit",    serving: "1 amla (40g)",    nutrients: N(0.3, 0, 0, 25, 0.1, 0, 6, 58, 10) },
  // Nuts & Seeds
  { id: "akhrot",      name: "Akhrot",        hindi: "अखरोट",      category: "Nuts",     serving: "5-6 (30g)",       nutrients: N(0.8, 0, 0, 28, 0.9, 2.5, 28, 1, 45) },
  { id: "almond",      name: "Badaam",        hindi: "बादाम",      category: "Nuts",     serving: "10-12 (28g)",     nutrients: N(1.1, 0, 0, 77, 0.9, 0, 15, 0, 77) },
  { id: "til",         name: "Til",           hindi: "तिल",        category: "Seeds",    serving: "1 tbsp (9g)",     nutrients: N(1.3, 0, 0, 88, 0.7, 0, 13, 0, 32) },
  { id: "flaxseed",    name: "Flaxseeds",     hindi: "अलसी",       category: "Seeds",    serving: "1 tbsp (10g)",    nutrients: N(0.5, 0, 0, 26, 0.4, 1.6, 9, 0, 40) },
  { id: "pumpkin_seeds",name:"Pumpkin Seeds", hindi: "कद्दू बीज",  category: "Seeds",    serving: "1 tbsp (10g)",    nutrients: N(0.9, 0, 0, 5, 0.7, 0.1, 6, 0, 37) },
  { id: "bhuna_chana", name: "Bhuna Chana",   hindi: "भुना चना",   category: "Snack",    serving: "1 handful (30g)", nutrients: N(1.3, 0, 0, 31, 0.6, 0, 52, 0, 22) },
];

export const CATEGORIES = [...new Set(FOOD_DB.map((f) => f.category))];

export const NUTRIENT_DAILY: Record<string, number> = {
  iron: 18, vitamin_b12: 2.4, vitamin_d: 15, calcium: 1000,
  zinc: 8, omega3: 1.6, folate: 400, vitamin_a: 900, magnesium: 320,
  vitamin_c: 75, iodine: 150, selenium: 55, vitamin_b6: 1.3, potassium: 3500,
  copper: 0.9, vitamin_e: 15, vitamin_b1: 1.2, vitamin_b2: 1.3, vitamin_b3: 16,
  vitamin_b5: 5, vitamin_b7: 30, vitamin_k: 120, phosphorus: 700, manganese: 2.3, chromium: 35,
};

export const NUTRIENT_UNITS: Record<string, string> = {
  iron: "mg", vitamin_b12: "mcg", vitamin_d: "mcg", calcium: "mg",
  zinc: "mg", omega3: "g", folate: "mcg", vitamin_a: "mcg", magnesium: "mg",
  vitamin_c: "mg", iodine: "mcg", selenium: "mcg", vitamin_b6: "mg", potassium: "mg",
  copper: "mg", vitamin_e: "mg", vitamin_b1: "mg", vitamin_b2: "mg", vitamin_b3: "mg",
  vitamin_b5: "mg", vitamin_b7: "mcg", vitamin_k: "mcg", phosphorus: "mg", manganese: "mg", chromium: "mcg",
};

export function getRecipesForDeficiency(
  nutrient: string,
  userState?: string,
  limit = 5,
  pool: FoodItem[] = []
): FoodItem[] {
  const scored = pool
    .map((f) => ({ f, val: (f.nutrients[nutrient] ?? 0) as number }))
    .filter((x) => x.val > 0);
  scored.sort((a, b) => {
    const stateBoost = (f: FoodItem) => (userState && f.state === userState ? 1000 : 0);
    return (b.val + stateBoost(b.f)) - (a.val + stateBoost(a.f));
  });
  return scored.slice(0, limit).map((x) => x.f);
}

// ── Comprehensive Hindi food alias map (fuzzy search) ────────
export const FOOD_ALIASES: Record<string, string[]> = {
  // Grains / Roti
  roti:        ["chapati","chapatti","chappati","chapathi","phulka","fulka","wheat roti","gehu roti","rotto","atta","gehu"],
  "bajra roti":["bajre ki roti","bajre roti","millet roti","bajra","pearl millet"],
  "ragi roti": ["nachni","mandua","finger millet","ragi"],
  rice:        ["chawal","chaawal","chaval","bhat","bhaat","white rice","plain rice"],
  poha:        ["pohe","aval","chiwda","beaten rice","flattened rice"],
  upma:        ["uppama","uppuma","semolina","suji","sooji upma"],
  khichdi:     ["khichri","khichadi","khichari","dal rice","dal chawal"],
  dalia:       ["daliya","broken wheat","oatmeal","porridge"],
  idli:        ["idly","idlies","steam cake"],
  dosa:        ["dosai","dose","plain dosa","masala dosa"],

  // Dal / Legumes
  dal:         ["daal","dhal","lentil","lentils"],
  "masoor dal":["masoor","red lentil","pink dal","lal dal","masur"],
  "moong dal": ["moong","mung","green gram","mung dal","mung bean","sabut moong"],
  rajma:       ["kidney bean","red beans","rajmah","rajme"],
  "chana dal": ["chana","bengal gram","desi chana"],
  "urad dal":  ["urad","black gram","kaali dal","maa di dal","black lentil"],
  "toor dal":  ["arhar dal","tur dal","pigeon pea","tuvar dal","arhar"],
  "kala chana":["black chana","desi chana","horse gram","kale chane"],
  "chole":     ["chhole","chickpea","kabuli chana","safed chana","garbanzo"],

  // Vegetables
  palak:       ["paalak","spinach","saag","palaka","hara saag","spinch"],
  methi:       ["methi saag","fenugreek","fenugreek leaves","kasuri methi"],
  aloo:        ["alu","aaloo","potato","batata","urulaikizhangu","aloo"],
  "aloo gobhi":["aloo gobi","potato cauliflower","alu gobhi"],
  gobhi:       ["gobi","cauliflower","cauliflower sabzi","phoolgobhi","phool gobhi"],
  "palak paneer":["palak pneer","spinach paneer","saag paneer","saagpaneer"],
  baingan:     ["brinjal","eggplant","aubergine","baigan","begun","ringna"],
  bhindi:      ["okra","ladies finger","lady finger","vendakka","bendekai"],
  lauki:       ["bottle gourd","ghiya","doodhi","dudhi","sorakkai"],
  karela:      ["bitter gourd","bitter melon","pavakka","hagalakai"],
  tinda:       ["round gourd","apple gourd","tindora","kundru"],
  turai:       ["ridge gourd","zucchini","torai","beerakaya"],
  pumpkin:     ["kaddu","sitaphal","petha","kumbalangi","parangikkai"],
  "gajar":     ["carrot","gaajar","carrot sabzi","gajjar"],
  "matar":     ["peas","green peas","mattar","vatana","pattani"],
  tamatar:     ["tomato","tamaatar","tamaater","timaatar"],
  pyaz:        ["onion","pyaaz","piaz","dungri"],
  lehsun:      ["garlic","lasan","lasun","garlic clove"],
  adrak:       ["ginger","ginger root","saunth","sonth","inguru"],
  "shimla mirch":["capsicum","bell pepper","red pepper","green pepper","yellow pepper"],
  "hara dhaniya":["coriander leaves","cilantro","dhania","dhaniya","kothimira"],
  "saag":      ["mixed greens","leafy vegetables","harisaag","saagwala"],
  broccoli:    ["brokali","brocoli"],
  "sweet potato":["shakarkand","shakarkandi","sarkande","ratalu"],
  chukandar:   ["beetroot","beet","red beet","chukander"],

  // Dairy
  dahi:        ["curd","yogurt","yoghurt","daahi","plain curd"],
  paneer:      ["cottage cheese","panner","pneer","fresh cheese"],
  doodh:       ["milk","dudh","dudha","gaay ka doodh","cow milk","whole milk"],
  "lassi":     ["sweet lassi","salted lassi","butter milk"],
  "chaas":     ["buttermilk","chaach","mattha","majjiga"],
  ghee:        ["clarified butter","desi ghee","pure ghee"],

  // Protein / Non-veg
  anda:        ["egg","anda","anDA","boiled egg","omelette","egg white","egg yolk","scrambled"],
  chicken:     ["murgi","murga","murg","poultry","grilled chicken","chicken curry"],
  fish:        ["machli","machali","maach","meen","sea food","seafood","salmon","rohu","katla"],
  mutton:      ["lamb","gosht","maas","meat","keema","kheema","minced meat"],

  // Fruits
  kela:        ["banana","kella","plantain"],
  seb:         ["apple","saab","apple fruit"],
  aam:         ["mango","amra","keri","raw mango"],
  papaya:      ["papita","papetas","papaya fruit"],
  anar:        ["pomegranate","annar","dalim"],
  "amrud":     ["guava","peru","jaamfal"],
  "santara":   ["orange","naranga","santra","narangi"],
  nimbu:       ["lemon","lime","neembu","limon","citrus"],
  amla:        ["gooseberry","indian gooseberry","awla","nellikai"],

  // Nuts & Seeds
  badam:       ["almond","badaam","almonds"],
  akhrot:      ["walnut","akhrot"],
  kaju:        ["cashew","cashewnut","keshoo","kaaju"],
  "mungfali":  ["peanut","groundnut","moongphali","singdana"],
  til:         ["sesame","sesame seeds","gingelly"],
  "alsi":      ["flaxseed","linseed","flax seed","flax"],
  "kaddu ke beej":["pumpkin seeds","pepitas"],

  // Common dishes
  "dal makhani":["daal makhani","dal makhni","makhani dal","butter dal"],
  "dal tadka":  ["tadke wali dal","tarka dal","tadka wali dal"],
  "shahi paneer":["paneer makhani","butter paneer","paneer in gravy"],
  "matar paneer":["mattar paneer","peas paneer"],
  biryani:     ["biriyani","biriani","veg biryani","chicken biryani","rice dish"],
  "sambar":    ["sambaar","south indian dal","sambhar"],
  rasam:       ["pepper water","tomato rasam","tamarind soup"],
  "pav bhaji": ["pao bhaji","paw bhaji","mumbai pav bhaji"],
  "halwa":     ["sheera","halva","sooji halwa","gajar halwa"],
  "kheer":     ["payasam","rice pudding","milk pudding"],
};

// Normalize text for fuzzy matching
function normalize(s: string): string {
  return s
    .toLowerCase()
    .replace(/aa/g, "a")
    .replace(/ee/g, "i")
    .replace(/oo/g, "u")
    .replace(/ph/g, "f")
    .replace(/kh/g, "k")
    .replace(/gh/g, "g")
    .replace(/ch/g, "c")
    .replace(/sh/g, "s")
    .replace(/[^a-z0-9 ]/g, "")
    .trim();
}

// Levenshtein distance (for short words)
function levenshtein(a: string, b: string): number {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  );
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1] : 1 + Math.min(dp[i-1][j-1], dp[i-1][j], dp[i][j-1]);
  return dp[m][n];
}

export function searchFoods(query: string, extra: FoodItem[] = []): FoodItem[] {
  if (!query.trim()) return [];
  const raw = query.toLowerCase().trim();
  const norm = normalize(raw);
  const all = [...FOOD_DB, ...extra];

  // Score each food item
  const scored = all.map((f) => {
    const nameLow   = f.name.toLowerCase();
    const hindiLow  = (f.hindi ?? "").toLowerCase();
    const normName  = normalize(nameLow);
    let score = 0;

    // Exact match = highest priority
    if (nameLow === raw || hindiLow === raw) score = 100;
    // Starts with
    else if (nameLow.startsWith(raw) || normName.startsWith(norm)) score = 90;
    // Contains
    else if (nameLow.includes(raw) || hindiLow.includes(raw) || normName.includes(norm)) score = 70;
    else {
      // Check aliases
      for (const [canonical, aliases] of Object.entries(FOOD_ALIASES)) {
        const allTerms = [canonical, ...aliases];
        if (
          allTerms.some((t) => nameLow.includes(t) || t.includes(raw)) &&
          allTerms.some((t) => t.includes(raw) || raw.includes(t) || normalize(t).includes(norm))
        ) {
          score = 60;
          break;
        }
        // If query matches an alias and food matches the canonical
        if (allTerms.some((t) => t === raw || t.startsWith(raw) || raw.startsWith(t))) {
          if (nameLow.includes(canonical) || normName.includes(normalize(canonical))) {
            score = 65;
            break;
          }
        }
      }
      // Fuzzy (Levenshtein) for short words
      if (score === 0 && raw.length >= 3) {
        const words = normName.split(" ");
        const dist = Math.min(...words.map((w) => levenshtein(norm, w)));
        if (dist <= 2) score = Math.max(10, 50 - dist * 15);
      }
    }

    return { food: f, score };
  });

  return scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((s) => s.food)
    .slice(0, 20);
}
