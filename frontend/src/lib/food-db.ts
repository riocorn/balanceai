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

// ── Comprehensive multi-language food alias map ───────────────
// Hindi / English / Punjabi / Bengali / Gujarati / Tamil / Telugu / Marathi / Kannada / Odia
// + common misspellings for every entry
export const FOOD_ALIASES: Record<string, string[]> = {

  // ── GRAINS / ROTI ──────────────────────────────────────────
  roti: ["chapati","chapatti","chappati","chapathi","phulka","fulka","wheat roti","gehu roti",
         "rotto","atta roti","gehun roti","gehu","chapdi","chappathi","chappathi","tawa roti",
         // Punjabi
         "atta di roti","gehun di roti",
         // Gujarati
         "rotli","bhakri","chapdi","fulka",
         // Tamil
         "chapathi","chappati","wheat chapathi",
         // Telugu
         "chapati","phulka roti",
         // Marathi
         "poli","bhakar",
         // Bengali
         "ruti","luchi",
         // common typos
         "rotti","rotii","chappathi","caapati"],
  "bajra roti": ["bajre ki roti","bajre roti","millet roti","bajra","pearl millet",
                 "bajri rotla","bajri roti","bajre","bajra rotla","baarjra",
                 // Punjabi
                 "makki nal bajra","bajre di roti",
                 // Gujarati
                 "bajri rotla","bajri",
                 // Marathi
                 "bajrichi bhakri","bajrichya roti",
                 // Rajasthani
                 "bajre ki roti","baajra",
                 "bajre","bajara","bajraa"],
  "ragi roti":  ["nachni","mandua","finger millet","ragi","nachni roti","raagi",
                 "ragi mudde","ragi ball","kelvaragu",
                 // Kannada
                 "ragi rotti","raagi rotti","ragi mudde",
                 // Tamil
                 "kelvaragu","kezhvaragu","keppai",
                 // Telugu
                 "ragi rotte","ragulu",
                 // Marathi
                 "nachni bhakri","naachni",
                 "raagi","raagi roti","rragi"],
  "makki roti": ["makki di roti","cornmeal roti","corn roti","maize roti","maki roti",
                 "makai roti","makii","makki"],
  rice:         ["chawal","chaawal","chaval","bhat","bhaat","white rice","plain rice","bhaat",
                 // Bengali
                 "bhat","anna",
                 // Tamil
                 "sadam","soru","rice sadam",
                 // Telugu
                 "annam","biyyam",
                 // Kannada
                 "anna","akki",
                 // Gujarati
                 "chaval","bhaat",
                 // Odia
                 "bhata","anna",
                 // typos
                 "chaawl","chawl","chaawl","rce"],
  "brown rice": ["brown chawal","unpolished rice","whole grain rice","bura chawal","sabut chawal"],
  poha:         ["pohe","aval","chiwda","beaten rice","flattened rice","avalakki",
                 // Tamil
                 "aval","poha",
                 // Telugu
                 "atukulu","borugulu",
                 // Kannada
                 "avalakki","beaten rice",
                 // Gujarati
                 "poha","pauwa","thick poha",
                 // Bengali
                 "chira","chiura",
                 // Marathi
                 "pohe","kanda pohe",
                 "pohaa","powa","pawaa"],
  upma:         ["uppama","uppuma","semolina upma","suji upma","sooji upma","rava upma","uppittu",
                 // Kannada
                 "uppittu","upma",
                 // Tamil
                 "upma","sooji upma",
                 // Telugu
                 "uppudi pindi","uppuma",
                 "oopmaa","upuma","upamma"],
  khichdi:      ["khichri","khichadi","khichari","dal rice","dal chawal","khichdee",
                 // Bengali
                 "khichuri","bhog khichuri",
                 // Gujarati
                 "khichdi","dal bhat",
                 // Tamil
                 "pongal","ven pongal",
                 // Telugu
                 "huggi","pongali",
                 // Odia
                 "khechudi",
                 "khicdi","khichdii","kkhichdi"],
  dalia:        ["daliya","broken wheat","wheat porridge","lapsi","porridge","gehu dalia",
                 "daliya porridge","cracked wheat",
                 // Gujarati
                 "lapsi","wheat lapsi",
                 "dalia","daliyaa"],
  idli:         ["idly","idlies","steam cake","idly rice","idli batter",
                 // Tamil
                 "idli","kanchipuram idli",
                 // Telugu
                 "idli","ravva idli",
                 // Kannada
                 "idli","thatte idli",
                 "idlii","iddli","iddly"],
  dosa:         ["dosai","dose","plain dosa","masala dosa","rava dosa","set dosa",
                 // Tamil
                 "dosai","adai dosa",
                 // Telugu
                 "dosa","pesarattu dosa",
                 // Kannada
                 "dose","neer dose","akki rotti",
                 // typos
                 "dosaa","doosa","dhosa"],
  oats:         ["oatmeal","rolled oats","quick oats","jai","javi","oat porridge","granola",
                 "oate","oats porridge","oatts","oat"],
  dalia_oats:   ["dalia porridge","oat dalia","mixed porridge"],

  // ── DAL / LEGUMES ──────────────────────────────────────────
  dal:          ["daal","dhal","lentil","lentils","daal",
                 // Tamil
                 "paruppu","dal",
                 // Telugu
                 "pappu","dal",
                 // Kannada
                 "bele","dal",
                 // Bengali
                 "daal","dal",
                 // Marathi
                 "dal","varan",
                 // Gujarati
                 "dal","daal",
                 "dhal","daal","dhaal"],
  "masoor dal": ["masoor","red lentil","pink dal","lal dal","masur","red masoor",
                 // Bengali
                 "moshur dal","masur dal",
                 // Tamil
                 "mysore paruppu","masoor paruppu",
                 // Gujarati
                 "masoor ni dal",
                 // Marathi
                 "masoor dal","masoorachi dal",
                 "masur","massoor","masoorr","masoor daal"],
  "moong dal":  ["moong","mung","green gram","mung dal","mung bean","sabut moong","hari moong",
                 "dhuli moong","yellow moong","moong soup",
                 // Bengali
                 "mug dal","mug daal","moog dal",
                 // Tamil
                 "payatham paruppu","moong paruppu",
                 // Telugu
                 "pesara pappu","moong pappu",
                 // Kannada
                 "hesaru bele","moong",
                 // Gujarati
                 "mag ni dal","mag dal",
                 // Marathi
                 "mugachi dal","mug dal",
                 "moong daal","muung","mong","moongdal"],
  rajma:        ["kidney bean","red beans","rajmah","rajme","red kidney beans",
                 // Bengali
                 "rajma","shim",
                 // Punjabi
                 "rajma chawal","rajme",
                 // Kashmiri
                 "rajmah","rajma roganjosh",
                 "raajma","rajmaa","rajmma","rajuma"],
  "chana dal":  ["chana","bengal gram","desi chana","gram dal","chane ki dal",
                 // Tamil
                 "kadalai paruppu","chana paruppu",
                 // Telugu
                 "senagapappu","chana pappu",
                 // Kannada
                 "kadle bele","chana bele",
                 // Gujarati
                 "chana ni dal","chana dal",
                 "channa dal","chanaa dal","chaana","channadal"],
  "urad dal":   ["urad","black gram","kaali dal","maa di dal","black lentil","maa ki dal",
                 "dhuli urad","sabut urad",
                 // Bengali
                 "biulir dal","mashkalai dal",
                 // Tamil
                 "ulunthu paruppu","urad paruppu",
                 // Telugu
                 "minumula pappu","urad pappu",
                 // Kannada
                 "uddina bele","urad bele",
                 // Gujarati
                 "adad ni dal","urad dal",
                 // Marathi
                 "udid dal","uddachi dal",
                 "uradd","urad daal","uradd","maaki dal"],
  "toor dal":   ["arhar dal","tur dal","pigeon pea","tuvar dal","arhar","toovar","arhar daal",
                 // Tamil
                 "tuvaram paruppu","thuvaram paruppu",
                 // Telugu
                 "kandi pappu","toor pappu",
                 // Kannada
                 "togari bele","toor bele",
                 // Gujarati
                 "tuver ni dal","toor ni dal",
                 // Marathi
                 "tur dal","toorichi dal",
                 "toordal","toovar dal","tuvar","arahr","arhardal"],
  "kala chana": ["black chana","desi chana whole","horse gram","kale chane","bengal gram whole",
                 "kala chhola","kaale chane",
                 // Bengali
                 "kala chana",
                 // Punjabi
                 "kale channe","kaale chane",
                 "kala channa","kale chane","kaalachana"],
  chole:        ["chhole","chickpea","kabuli chana","safed chana","garbanzo","white chana",
                 // Bengali
                 "chhola","kabuli chhola",
                 // Gujarati
                 "chana","chhole",
                 // Punjabi
                 "chole","channe",
                 // Tamil
                 "kondakadalai","kabuli kadalai",
                 // Telugu
                 "senagalu","chole",
                 "cholle","chhole","chhola","choley","chholey","channey"],
  lobia:        ["cowpea","black eyed peas","chauli","lobiya","black eye beans",
                 // Bengali
                 "barbati","borboti",
                 // Gujarati
                 "chola","val",
                 // Tamil
                 "karamani","thatta payiru",
                 // Telugu
                 "bobbarlu","lobia",
                 "lobiyaa","lobi"],
  "sabut moong":["whole moong","whole green gram","sabut mung","green moong whole","hari moong"],

  // ── VEGETABLES ─────────────────────────────────────────────
  palak:        ["paalak","spinach","saag","palaka","hara saag","spinch","palok",
                 // Bengali
                 "palak shak","paalang","palang saag",
                 // Tamil
                 "keerai","pasalai keerai",
                 // Telugu
                 "palakura","paala kura",
                 // Kannada
                 "palaka soppu","soppu",
                 // Gujarati
                 "palak","paalak",
                 // Marathi
                 "palak","palakachi bhaji",
                 // Punjabi
                 "paalak","saag",
                 "palakk","paalk","paalak","spinaach","spinich"],
  methi:        ["methi saag","fenugreek","fenugreek leaves","kasuri methi","methi leaves",
                 "methi ka saag",
                 // Bengali
                 "methi shak","methi pata",
                 // Tamil
                 "vendhaya keerai","methi keerai",
                 // Telugu
                 "menthiku","menthi koora",
                 // Kannada
                 "menthya soppu","menthe",
                 // Gujarati
                 "methi","methi ni bhaji",
                 // Marathi
                 "methi","methichi bhaji",
                 // Punjabi
                 "methi","methi da saag",
                 "meethee","meethi","methee","meti"],
  sarson:       ["mustard greens","sarson saag","sarson leaves","mustard leaves","sarsoo",
                 "sarson da saag",
                 // Punjabi
                 "sarson da saag","sarso",
                 // Bengali
                 "shorshe shak","sarisha",
                 // Marathi
                 "mohri bhaji","sarson",
                 "sarso","sarsoon","saason","sarsav"],
  bathua:       ["chenopodium","goosefoot","pigweed","bathuwa","bathwa",
                 // Punjabi
                 "bathua saag","bathua",
                 // Bengali
                 "bethu shak",
                 "bathoa","bathwa"],
  aloo:         ["alu","aaloo","potato","batata","urulaikizhangu","aloo",
                 // Bengali
                 "aloo","alu","alur dom",
                 // Tamil
                 "urulaikizhangu","aloo",
                 // Telugu
                 "bangaladumpa","aloo kura",
                 // Kannada
                 "aloo","genasinakki",
                 // Gujarati
                 "bateta","aloo","bataaka",
                 // Marathi
                 "bataata","aloo",
                 // Punjabi
                 "aloo","alu",
                 "aallu","allu","potatoes","poteto","patato"],
  "aloo gobhi": ["aloo gobi","potato cauliflower","alu gobhi","aloo phoolgobi"],
  gobhi:        ["gobi","cauliflower","cauliflower sabzi","phoolgobhi","phool gobhi",
                 "phool gobi","foolgobhi",
                 // Bengali
                 "phulkopi","phool kopi",
                 // Tamil
                 "cauliflower","kovippu",
                 // Telugu
                 "cauliflower","gobi",
                 // Gujarati
                 "cauliflower","flaavara",
                 // Marathi
                 "phulkohala","phool gobhi",
                 "gobhee","gobbhi","cauliflower"],
  "palak paneer":["palak pneer","spinach paneer","saag paneer","saagpaneer","palak cheese"],
  baingan:      ["brinjal","eggplant","aubergine","baigan","begun","ringna","vangi","bangan",
                 // Bengali
                 "begun","begoon",
                 // Tamil
                 "katharikai","kathirikai",
                 // Telugu
                 "vankaya","baingan",
                 // Kannada
                 "badnekai","baingan",
                 // Gujarati
                 "ringna","baingan",
                 // Marathi
                 "vaangi","baingan",
                 // Punjabi
                 "baingan","begun",
                 "baigan","baingun","bainkan","egg plant"],
  bhindi:       ["okra","ladies finger","lady finger","vendakka","bendekai","lady's finger",
                 // Bengali
                 "dheros","dherosh",
                 // Tamil
                 "vendakkai","vendaikkai",
                 // Telugu
                 "bendakaya","bhindi",
                 // Kannada
                 "bendekai","bhindi",
                 // Gujarati
                 "bhinda","bhindi",
                 // Marathi
                 "bhendi","bhindi",
                 // Punjabi
                 "bhindi","bhindi da saag",
                 "bhindee","bindi","bindee","okraa"],
  lauki:        ["bottle gourd","ghiya","doodhi","dudhi","sorakkai","kaddu wali","lau","gheeya",
                 // Bengali
                 "lau","lao",
                 // Tamil
                 "sorakkai","bottle gourd",
                 // Telugu
                 "anapa kaya","lauki",
                 // Kannada
                 "sorekai","lauki",
                 // Gujarati
                 "dudhi","lauki",
                 // Marathi
                 "dudhi","doodhi",
                 // Punjabi
                 "lauki","ghiya","gheeya",
                 "laukee","laukii","ghiya","gheeya"],
  karela:       ["bitter gourd","bitter melon","pavakka","hagalakai","pavakkai",
                 "bittergourd","bitter guard",
                 // Bengali
                 "uchhe","karala",
                 // Tamil
                 "pavakkai","paavakkai",
                 // Telugu
                 "kakarakaya","karela",
                 // Kannada
                 "hagalakai","karela",
                 // Gujarati
                 "karela","karelu",
                 // Marathi
                 "karle","karela",
                 "karella","kaarela","bitter gourd"],
  tinda:        ["round gourd","apple gourd","tindora","kundru","tindli",
                 // Bengali
                 "tinda","kundri",
                 // Gujarati
                 "tindola","tindora",
                 // Telugu
                 "dondakaya","tindora",
                 // Kannada
                 "tendli","tindora",
                 // Marathi
                 "tendli","tondekai",
                 "tindaa","kundru","kunduri"],
  turai:        ["ridge gourd","torai","beerakaya","dodka","silk gourd",
                 // Bengali
                 "jhinge","jhingey",
                 // Tamil
                 "peerkangai","ridge gourd",
                 // Telugu
                 "beerakaya","turai",
                 // Kannada
                 "heerekai","turai",
                 // Gujarati
                 "turiya","turai",
                 // Marathi
                 "dodka","turai",
                 "torai","turaii","turahi"],
  pumpkin:      ["kaddu","sitaphal","petha","kumbalangi","parangikkai","kaddoo",
                 // Bengali
                 "kumro","kumra",
                 // Tamil
                 "poosanikai","parangikkai",
                 // Telugu
                 "gummadikaya","pumpkin",
                 // Kannada
                 "kumbalakai","pumpkin",
                 // Gujarati
                 "kaddu","kolu","kadoo",
                 // Marathi
                 "lal bhopla","kaddu",
                 "kadduu","kadduuu","pumpkin"],
  gajar:        ["carrot","gaajar","carrot sabzi","gajjar","carrots",
                 // Bengali
                 "gajar","gaajor",
                 // Tamil
                 "carrot","carrot kizhangu",
                 // Telugu
                 "carrot","gajjara",
                 // Kannada
                 "carrot","gaajari",
                 // Gujarati
                 "gajar","gajar nu shaak",
                 "caroot","carrot","gaajjar","gaajaar"],
  matar:        ["peas","green peas","mattar","vatana","pattani","hare matar","fresh peas",
                 // Bengali
                 "matar","motorshuti",
                 // Tamil
                 "pattani","green peas",
                 // Telugu
                 "pachi batani","matar",
                 // Kannada
                 "batani","matar",
                 // Gujarati
                 "vatana","matar",
                 // Marathi
                 "vatana","matar",
                 "mattar","mattarr","peas","pea"],
  tamatar:      ["tomato","tamaatar","tamaater","timaatar","tomatoes",
                 // Bengali
                 "tamato","tomatoo",
                 // Tamil
                 "thakkali","tomato",
                 // Telugu
                 "tomato","ramamulakaya",
                 // Kannada
                 "tomato","tomatoo",
                 // Gujarati
                 "tameta","tomato",
                 // Marathi
                 "tomato","tamatar",
                 "tameto","tamito","tomatoo"],
  pyaz:         ["onion","pyaaz","piaz","dungri","kanda",
                 // Bengali
                 "piyaj","piaj",
                 // Tamil
                 "vengayam","venkayam",
                 // Telugu
                 "ulli","neerulli",
                 // Kannada
                 "eerulli","ulli",
                 // Gujarati
                 "dungri","kanda",
                 // Marathi
                 "kanda","pyaz",
                 // Punjabi
                 "pyaz","piaz",
                 "pyaz","pyaaz","oinin","onnion"],
  lehsun:       ["garlic","lasan","lasun","garlic clove","lahasun","lahsun",
                 // Bengali
                 "rasun","laasun",
                 // Tamil
                 "poondu","puntu",
                 // Telugu
                 "vellulli","vellaipoondu",
                 // Kannada
                 "bellulli","lasun",
                 // Gujarati
                 "lasun","garlic",
                 // Marathi
                 "lasun","lehsun",
                 "garlik","garlick","lahasun","lahsun"],
  adrak:        ["ginger","ginger root","saunth","sonth","inguru","sooth","fresh ginger",
                 // Bengali
                 "ada","aada",
                 // Tamil
                 "inji","ginger",
                 // Telugu
                 "allam","ginger",
                 // Kannada
                 "shunti","ginger",
                 // Gujarati
                 "aadu","ginger",
                 // Marathi
                 "aale","ginger",
                 "gingger","adrak","adarak","aadrakh"],
  "shimla mirch":["capsicum","bell pepper","red pepper","green pepper","yellow pepper",
                  "sweet pepper","paprika",
                  // Bengali
                  "capsicum","shimla mirch",
                  // Tamil
                  "kodaimilagai","capsicum",
                  // Telugu
                  "capsicum","donga mirchi",
                  // Kannada
                  "capsicum","donne menasinakai",
                  // Gujarati
                  "shimla mirchi","capsicum",
                  "shimlamirch","capsikum","capscium"],
  "hara dhaniya":["coriander leaves","cilantro","dhania","dhaniya","kothimira",
                  "coriander","kothmeer","dhaniwa",
                  // Bengali
                  "dhone pata","dhanepata",
                  // Tamil
                  "kothamalli","kothambari",
                  // Telugu
                  "kothimira","kothamara",
                  // Kannada
                  "kottambari soppu","kothambari",
                  // Gujarati
                  "kothmir","kothmiri",
                  // Marathi
                  "kothimbir","kothmir",
                  "corriander","corainder","dhanyia"],
  broccoli:     ["brokali","brocoli","broccolli","green gobhi","broko","brokli"],
  "sweet potato":["shakarkand","shakarkandi","sarkande","ratalu","meetha aloo",
                  // Bengali
                  "misti alu","misti aloo",
                  // Tamil
                  "sakkaravalli kizhangu",
                  // Telugu
                  "chettu dumpa","sweet potato",
                  // Kannada
                  "genasina gedde","sweet potato",
                  "shakar kand","sakarkand","shakarkend","sweet aloo"],
  chukandar:    ["beetroot","beet","red beet","chukander","chukundar",
                 // Bengali
                 "beet","chukundar",
                 // Tamil
                 "beetroot","beet kizhangu",
                 "beetrut","beet root","chukndar","chukandaar"],
  "drumstick":  ["sahjan","moringa pods","saijan","munaga","muringakkai","saginakaya",
                 // Tamil
                 "murungakkai","drumstick",
                 // Telugu
                 "munagakaya","drumstick",
                 // Kannada
                 "nuggekai","drumstick",
                 // Marathi
                 "shevga","drumstick",
                 "sajan","sahjann","muringa","sahjanaa"],
  arbi:         ["taro root","taro","kachalu","ghuiyan","eddoe","arvi",
                 // Bengali
                 "kochu","kochur","mukhi kochu",
                 // Tamil
                 "seppankizhangu","colocasia",
                 // Telugu
                 "chama dumpa","arbi",
                 // Kannada
                 "kesavinakki","arbi",
                 // Gujarati
                 "arvi","arbi",
                 // Marathi
                 "alu","arvi",
                 "arvii","arbiiii","taroroot"],

  // ── DAIRY ──────────────────────────────────────────────────
  dahi:         ["curd","yogurt","yoghurt","daahi","plain curd","plain yogurt",
                 // Bengali
                 "doi","dahi",
                 // Tamil
                 "thayir","mosaru",
                 // Telugu
                 "perugu","dahi",
                 // Kannada
                 "mosaru","majjige",
                 // Gujarati
                 "dahi","dahi nu shaak",
                 // Marathi
                 "dahi","curd",
                 // Punjabi
                 "dahi","daahi",
                 "dahii","cerd","yougurt","yogert","yoghurt","yoghert"],
  paneer:       ["cottage cheese","panner","pneer","fresh cheese","soft cheese",
                 // Bengali
                 "chena","chhana","paneer",
                 // Tamil
                 "paneer","panner",
                 // Telugu
                 "paneer","paniru",
                 // Kannada
                 "paneer","chenna",
                 // Gujarati
                 "paneer","chhena",
                 // Marathi
                 "paneer","chena",
                 "paneer","panier","panir","panear","paneeer"],
  doodh:        ["milk","dudh","dudha","gaay ka doodh","cow milk","whole milk","full fat milk",
                 // Bengali
                 "dudh","doodh",
                 // Tamil
                 "paal","pal",
                 // Telugu
                 "palu","doodh",
                 // Kannada
                 "halu","doodh",
                 // Gujarati
                 "dudh","doodh",
                 // Marathi
                 "dudh","doodh",
                 // Punjabi
                 "doodh","dudh",
                 "milkk","miilk","dudh","dooodh"],
  lassi:        ["sweet lassi","salted lassi","butter milk","thick lassi","fruit lassi",
                 // Punjabi
                 "makhan lassi","meethi lassi",
                 "laassi","lasi","laasi"],
  chaas:        ["buttermilk","chaach","mattha","majjiga","tak",
                 // Tamil
                 "mor","neer mor",
                 // Telugu
                 "majjiga","chaas",
                 // Kannada
                 "majjige","chaas",
                 // Gujarati
                 "chaas","matho",
                 // Marathi
                 "taak","chaas",
                 "chaach","chhaas","taak","takk"],
  ghee:         ["clarified butter","desi ghee","pure ghee","cow ghee",
                 // Tamil
                 "nei","ghee",
                 // Telugu
                 "neyyi","ghee",
                 // Kannada
                 "thuppa","ghee",
                 // Gujarati
                 "ghee","ghee nu desi",
                 "ghee","ghii","ghi"],

  // ── PROTEIN / NON-VEG ──────────────────────────────────────
  anda:         ["egg","boiled egg","omelette","egg white","egg yolk","scrambled egg","fried egg",
                 "anDa","anda bhurji","half fry",
                 // Bengali
                 "dim","deem",
                 // Tamil
                 "muttai","muttay",
                 // Telugu
                 "guddu","muttai",
                 // Kannada
                 "motte","mutte",
                 // Gujarati
                 "anda","egg",
                 // Marathi
                 "anda","andya",
                 "andaa","eggg","eeg","anDa"],
  chicken:      ["murgi","murga","murg","poultry","grilled chicken","chicken curry","murgi",
                 "tandoori chicken","chicken tikka",
                 // Bengali
                 "murgir mangsho","chicken",
                 // Tamil
                 "kozhi","chicken",
                 // Telugu
                 "kodi","chicken",
                 // Kannada
                 "koli","chicken",
                 "chiken","chickin","chickenn"],
  fish:         ["machli","machali","maach","meen","seafood","salmon","rohu","katla","pomfret",
                 "hilsa","bangda",
                 // Bengali
                 "maachh","mach","ilish",
                 // Tamil
                 "meen","fish",
                 // Telugu
                 "chepala","fish",
                 // Kannada
                 "meenu","fish",
                 // Odia
                 "machha","fish",
                 "mackali","machhli","maachhi","fishh"],
  mutton:       ["lamb","gosht","maas","meat","keema","kheema","minced meat","goat meat",
                 // Bengali
                 "mangsho","khasi",
                 // Tamil
                 "aadu kari","mutton",
                 // Telugu
                 "mamsam","mutton",
                 // Kannada
                 "mamsada saaru","mutton",
                 // Punjabi
                 "maas","gosht",
                 "muttonn","muttn","goshat"],

  // ── FRUITS ─────────────────────────────────────────────────
  kela:         ["banana","kella","plantain","raw banana","green banana","kacha kela",
                 // Bengali
                 "kola","kela",
                 // Tamil
                 "vaazhai pazham","vaalai",
                 // Telugu
                 "aratipandu","kela",
                 // Kannada
                 "bale hannu","kela",
                 // Gujarati
                 "kela","kelo",
                 // Marathi
                 "kela","kel",
                 "banaana","bananna","bannaana","kella"],
  seb:          ["apple","saab","apple fruit","appl","shimla apple","kashmiri apple",
                 // Bengali
                 "seb","aapel",
                 // Tamil
                 "apple","aapil",
                 "appl","aplee","appel"],
  aam:          ["mango","amra","keri","raw mango","kacha aam","paka aam","alphonso",
                 // Bengali
                 "aam","aamer",
                 // Tamil
                 "maambazham","mangai","manga",
                 // Telugu
                 "mamidipandu","mango",
                 // Kannada
                 "maavinahannu","mango",
                 // Gujarati
                 "keri","aam",
                 // Marathi
                 "amba","aamba",
                 "mangg","maango","mnago"],
  papaya:       ["papita","papetas","papaya fruit","raw papaya","paka papita","kachha papita",
                 // Bengali
                 "papey","papeya",
                 // Tamil
                 "pappali pazham","pappayi",
                 // Telugu
                 "boppaya pazham","papaya",
                 // Kannada
                 "parangi hannu","papaya",
                 "papayaa","papaaya","papita"],
  anar:         ["pomegranate","annar","dalim","anaar",
                 // Bengali
                 "dalim","daanaa",
                 // Tamil
                 "mathulampazham","anar",
                 // Telugu
                 "danimma pandu","anar",
                 // Kannada
                 "daalimbe","anar",
                 "anar","pomgranate","pomegranete"],
  amrud:        ["guava","peru","jaamfal","amrood","jamphal",
                 // Bengali
                 "peara","piara",
                 // Tamil
                 "koiyya pazham","kovva",
                 // Telugu
                 "jaamapandu","guava",
                 // Kannada
                 "seebe hannu","guava",
                 // Gujarati
                 "jamfal","amrood",
                 // Marathi
                 "peru","amrood",
                 "guavaa","guawa","jaamfal","jamfal"],
  santara:      ["orange","naranga","santra","narangi","mosambi","malta","citrus",
                 // Bengali
                 "komola","kamalalebu",
                 // Tamil
                 "aaranjai","orange",
                 // Telugu
                 "narinza pandu","orange",
                 // Kannada
                 "kittale","orange",
                 // Gujarati
                 "santra","narangi",
                 "santaraa","organge","orangge","narangi"],
  nimbu:        ["lemon","lime","neembu","limon","citrus","nimboo","lemon juice","nimbu ras",
                 // Bengali
                 "lebu","nimboo",
                 // Tamil
                 "elumichai","lemon",
                 // Telugu
                 "nimma pandu","lemon",
                 // Kannada
                 "nimbe hannu","lemon",
                 "limon","nimbuu","lemoon","lemmn"],
  amla:         ["gooseberry","indian gooseberry","awla","nellikai","aonla","awala","vitamin c fruit",
                 // Bengali
                 "amloki","awla",
                 // Tamil
                 "nellikai","amla",
                 // Telugu
                 "usirikaya","amla",
                 // Kannada
                 "nelli hannu","amla",
                 // Gujarati
                 "amla","aamla",
                 "amlaa","aamla","awla","awwla"],
  "khajoor":    ["dates","date fruit","medjool","arabic dates","chuara","sukhe khajoor",
                 // Tamil
                 "perichamkani","dates",
                 // Telugu
                 "kharjura pandu","dates",
                 // Arabic origin
                 "khurma","kurma","khurmaa"],
  "kismis":     ["raisins","kishmish","dry grapes","dried grapes","sultana","kismis",
                 "black raisins","kali kishmish","munakka",
                 "kishmis","kismish","resins","raisns"],
  "anjeer":     ["dried fig","fig","dry fig","sookhi anjeer","figs",
                 // Bengali
                 "dumur","anjeer",
                 // Tamil
                 "athi pazham","fig",
                 // Telugu
                 "athi pandu","anjeer",
                 "aanjeer","anjiir","figs"],

  // ── NUTS & SEEDS ────────────────────────────────────────────
  badam:        ["almond","badaam","almonds","soaked almond","peeled almond","badam milk",
                 // Tamil
                 "badam","vadumaai",
                 // Telugu
                 "badam","badaamu",
                 // Kannada
                 "badam","badaami",
                 "baadaam","badamm","almonnd","almand"],
  akhrot:       ["walnut","walnuts","omega-3 nuts","akhrot",
                 // Bengali
                 "akhrot",
                 // Tamil
                 "akhrot","vella kottai",
                 "akhrott","aakhrot","walnut"],
  kaju:         ["cashew","cashewnut","keshoo","kaaju","cashew nut",
                 // Bengali
                 "kaju","keshoo",
                 // Tamil
                 "mundhiri","kaju",
                 // Telugu
                 "jeedipappu","kaju",
                 // Kannada
                 "godambi","kaju",
                 "caashew","cashuew","cajoo","kaaju"],
  pista:        ["pistachio","pista nut","pistachios","pista",
                 // Bengali
                 "pesta","pista",
                 // Tamil
                 "pista","pistaa",
                 "pistacchio","pistachio","peesta"],
  mungfali:     ["peanut","groundnut","moongphali","singdana","mungphali","ground nut",
                 // Bengali
                 "badam","cheenababadam",
                 // Tamil
                 "verkadalai","kadalai",
                 // Telugu
                 "pallilu","verusenaga",
                 // Kannada
                 "kadale beeja","kadlekai",
                 // Gujarati
                 "singdana","mungfali",
                 // Marathi
                 "shengdana","mungfali",
                 "moongphali","moongphaali","peanuts","peanut"],
  til:          ["sesame","sesame seeds","gingelly","white sesame","black sesame","kala til","safed til",
                 // Bengali
                 "til","teel",
                 // Tamil
                 "ellu","til",
                 // Telugu
                 "nuvvulu","til",
                 // Kannada
                 "ellu","til",
                 // Gujarati
                 "tal","til",
                 // Marathi
                 "til","teel",
                 "teel","tilll","sesame seed","sesmi"],
  alsi:         ["flaxseed","linseed","flax seed","flax","alasi","omega3 seeds","flaxseeds",
                 // Bengali
                 "tisi","alshi",
                 // Gujarati
                 "alsi","alasi",
                 // Marathi
                 "alashi","alsi",
                 "alsii","alsee","flaxseed","flax seeds"],
  "kaddu beej": ["pumpkin seeds","pepitas","kaddu ke beej","kaddu beej",
                 // Tamil
                 "parangi virai","pumpkin seed",
                 "kaddu ka beej","pumpkin seeds"],
  chia:         ["chia seeds","soaked chia","chia seed","chea seeds","sabja like",
                 "cheea","chiaa","chiya","chia seed"],

  // ── DRY FRUITS ──────────────────────────────────────────────
  "khumani":    ["apricot","dried apricot","khubani","sukhi khubani","sookhi khubani",
                 "khubaani","khubani","apricots","aabkhurmani"],
  "prune":      ["alubukhara","dried plum","prunes","plum dry","sookha alubukhara",
                 "prune fruit","aloobukhara"],
  "coconut":    ["nariyal","naarial","coconut","thengai","kobri","kopra",
                 // Bengali
                 "narikol","nariyal",
                 // Tamil
                 "thengai","coconut",
                 // Telugu
                 "kobbari","coconut",
                 // Kannada
                 "thengi","coconut",
                 // Gujarati
                 "nariyal","naariyal",
                 "narial","narikol","cocnut","coconutt"],

  // ── COMMON DISHES ───────────────────────────────────────────
  "dal makhani":["daal makhani","dal makhni","makhani dal","butter dal","kaali dal makhani",
                 "dal makhni","daal makhni"],
  "dal tadka":  ["tadke wali dal","tarka dal","tadka wali dal","yellow dal tadka"],
  "shahi paneer":["paneer makhani","butter paneer","paneer in gravy","paneer curry"],
  "matar paneer":["mattar paneer","peas paneer","mutter paneer"],
  biryani:      ["biriyani","biriani","veg biryani","chicken biryani","rice dish","pulao rice",
                 "biriyaani","biriyan","birryani"],
  sambar:       ["sambaar","south indian dal","sambhar","saambar",
                 // Tamil
                 "sambar","sambhar",
                 // Telugu
                 "sambhar","saambar",
                 // Kannada
                 "huli","saar",
                 "sambarr","sambaarr"],
  rasam:        ["pepper water","tomato rasam","tamarind soup","clear soup south indian",
                 // Tamil
                 "rasam","charu",
                 // Telugu
                 "charu","rasam",
                 // Kannada
                 "saaru","rasam",
                 "rasam","rasam"],
  "pav bhaji":  ["pao bhaji","paw bhaji","mumbai pav bhaji","pavbhaji"],
  halwa:        ["sheera","halva","sooji halwa","gajar halwa","atta halwa","moong dal halwa",
                 // Tamil
                 "kesari","halwa",
                 // Telugu
                 "halwa","ravva halwa",
                 "halwaa","halvaa","halva"],
  kheer:        ["payasam","rice pudding","milk pudding","chawal ki kheer","ksheeram",
                 // Tamil
                 "payasam","pal payasam",
                 // Telugu
                 "paramannam","payasam",
                 // Bengali
                 "payesh","kheer",
                 "khirr","kheerr","payasam"],
  "chole bhature":["chhole bhature","cholay bhature","bhatura chole"],
  "rajma chawal":["rajma rice","kidney beans rice","rajma dal chawal"],
  "aloo paratha":["alu paratha","stuffed paratha","potato paratha","aluu paratha"],
  "kadhi":      ["kadhi pakora","besan kadhi","dahi kadhi","buttermilk curry",
                 // Gujarati
                 "kadhi","gujarati kadhi",
                 // Punjabi
                 "kadhi pakora","kadhi",
                 "kadi","kaadhi"],
  "dhokla":     ["dhokla","dhokala","besan dhokla","gujarati dhokla","khaman",
                 // Gujarati
                 "dhokla","khaman dhokla",
                 "dokla","dhokla"],
  "thepla":     ["gujarati thepla","methi thepla","wheat thepla",
                 "tepla","thepala","thepla"],
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
