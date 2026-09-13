/**
 * Complete Indian Thali Generator
 * Real Indian meal structure: breakfast / lunch / snacks / dinner
 * Each meal = full thali with all components + quantities + expandable cooking guide
 */

export interface CookStep {
  text: string;
  tip?: string; // nutrition science tip (green callout)
}

export interface ThaliItem {
  name: string;       // "Toor Dal"
  qty: string;        // "1 katori (150g)"
  category: string;   // Dal / Grain / Sabzi / Dairy / Salad / Snack
  emoji: string;
  keyNutrient?: string; // "Iron 3.2mg", "Calcium 99mg"
  steps: CookStep[];
}

export interface ThaliOption {
  id: string;
  slot: "breakfast" | "lunch" | "snacks" | "dinner";
  title: string;
  items: ThaliItem[];
  tags: string[];     // ["iron-rich","vegetarian","light"]
  timing: string;     // "7–9 AM"
}

export interface DailyRoutine {
  dryFruits: { name: string; qty: string; when: string; tip: string }[];
  fruits: { name: string; qty: string; when: string; tip: string }[];
}

// ── Dal Cooking Steps ──────────────────────────────────────────
const DAL_COMMON_STEPS = (dalName: string): CookStep[] => [
  { text: `${dalName} ko raat bhar ya 1 ghante bhigo do phir dhoo lo` ,
    tip: "Bhigone se phytic acid 30–50% kam hota hai → iron/zinc better absorb hota hai" },
  { text: "Pressure cooker mein 2.5 cup paani + haldi + namak daal ke 3 seeti", },
  { text: "Lohe ki kadai (cast iron) garam karo — 1 tsp desi ghee ya tel",
    tip: "Lohe ki kadai se dal ka iron content 2–8x tak badh sakta hai (ICMR study)" },
  { text: "Jeera (1/2 tsp) chatakaao, phir hing (pinch) + sookhi lal mirch (1) + lehsun (2 kali) daalo",
    tip: "Ghee fat-soluble vitamins (A,D,E,K) absorb karata hai" },
  { text: "Tamatar (1 chota, katta hua) + haldi (1/4 tsp) + dhaniya powder (1/2 tsp) — 2 min bhunao" },
  { text: "Paki dal is tarka mein daalo, 5 min halke haath se pkaao",
    tip: "Haldi + kali mirch = curcumin absorption 20x (piperine effect)" },
  { text: "Serve karte time nimbu (1/2) nichod do",
    tip: "Vitamin C dal ka non-heme iron absorption 2–3x badhata hai — MUST hai" },
  { text: "Upar 1/2 tsp desi ghee daalo (optional but recommended)" },
];

const ROTI_STEPS = (grain = "gehun atta"): CookStep[] => [
  { text: `${grain} mein gunguna paani + thoda namak milao, 5 min goondo — tight dough` },
  { text: "20 min dhaka hua rakho — gluten develop hoga, roti soft banegi" },
  { text: "Tawa khub garam karo (medium-high), bina tel ke seko" },
  { text: "Dono taraf halke kaale dabbe aa jayein tab roti pakki samjo",
    tip: "Gehun mein B vitamins + iron + fiber; atta refined nahi — whole grain rakho" },
  { text: "Utarte hi 1/4 tsp ghee lagao — ghee fat-soluble vitamins ko absorb karata hai",
    tip: "Roti + ghee + dal = complete protein (complementary amino acids)" },
];

const SABZI_STEPS = (vegName: string, extraTips?: string[]): CookStep[] => [
  { text: `${vegName} ko acchi tarah dhoo ke medium size mein kaat lo` },
  { text: "Kadai mein 1 tsp tel/ghee garam karo — jeera + hing phodni",
    tip: "Lohe ki kadai use karo sabzi ke liye bhi — iron bonus milega" },
  { text: "Pyaz (1/2, barik katta) + lehsun (2-3 kali) + adrak (1/2 inch) bhunao 2 min",
    tip: extraTips?.[0] },
  { text: "Haldi (1/4 tsp) + dhaniya powder (1 tsp) + lal mirch (to taste) + namak — bhunao 30 sec" },
  { text: `${vegName} daalo, acchi tarah milaao — dhakkan laga ke medium flame pe 8–12 min` },
  { text: "Hara dhaniya + nimbu nichood ke serve karo",
    tip: extraTips?.[1] ?? "Sabzi cover karke pakao — nutrients steam mein bane rehte hain, paani mein nahi jaate" },
];

const SALAD_STEPS: CookStep[] = [
  { text: "Kheera (1/2) + tamatar (1 chota) + pyaz (1/4) = thin slices ya cubes" },
  { text: "Kali mirch + kala namak + jeera powder (pinch each)" },
  { text: "Nimbu (1/2) nichood ke milaao — bilkul serve karte time",
    tip: "Fresh salad ke Vitamin C + fiber se dal-sabzi ka iron 2x better absorb hota hai" },
  { text: "Hara dhaniya garnish — folate + Vitamin C" },
];

const DAHI_STEPS: CookStep[] = [
  { text: "Fridge se 15–20 min pehle nikaalo — room temperature pe khana better" },
  { text: "Khana khane ke beech ya baad mein khaao — digestive enzyme help karta hai",
    tip: "Dahi ke probiotics B12 absorb karate hain + gut flora improve karte hain" },
  { text: "Namak, jeera, kala namak + hara dhaniya milaao (plain ya raita style)",
    tip: "Dahi SIRF lunch mein khaao — dinner mein Ayurved ke hisaab se avoid (kapha increases)" },
];

// ── BREAKFAST OPTIONS ──────────────────────────────────────────
export const BREAKFAST_OPTIONS: ThaliOption[] = [
  {
    id: "bf_poha_thali",
    slot: "breakfast",
    title: "Poha + Dahi + Fruit Thali",
    timing: "7–9 AM",
    tags: ["light","vegetarian","iron"],
    items: [
      {
        name: "Kanda Poha", qty: "1.5 katori (120g paka hua)", category: "Grain", emoji: "🌾",
        keyNutrient: "Iron 1.8mg, Fiber 2g",
        steps: [
          { text: "Poha dhoo ke 5 min drain rakho — zyada geela nahi" },
          { text: "Kadai mein 1 tsp tel — rai + curry leaves + hing phodni",
            tip: "Lohe ki kadai mein banao — iron 1.5x badh sakta hai" },
          { text: "Pyaz (1/2) + hara mirch (1) — sुनहरा होने तक bhunao" },
          { text: "Haldi (pinch) + namak + cheeni (1/4 tsp) + nimbu (1/2)" },
          { text: "Poha milaao, dhakkan 2 min — phir hara dhaniya + nimbu" },
          { text: "Saath mein bhuna mungfali (1 tbsp) — protein badhega",
            tip: "Nimbu ka Vitamin C poha ka iron 2x better absorb karata hai" },
        ],
      },
      {
        name: "Dahi (plain)", qty: "1 katori (150g)", category: "Dairy", emoji: "🥛",
        keyNutrient: "Calcium 180mg, B12 0.8mcg, Protein 8g",
        steps: DAHI_STEPS,
      },
      {
        name: "Seasonal Fruit", qty: "1 medium / 1 cup", category: "Fruit", emoji: "🍎",
        keyNutrient: "Vitamin C 30–200mg, Fiber 2–4g",
        steps: [
          { text: "Subah khaana khane ke 30 min pehle ya baad mein fruit khao",
            tip: "Empty stomach ya alag fruit → better absorption, no fermentation" },
          { text: "Guava > Amla > Pomegranate > Banana — seasonal choice karo",
            tip: "Vitamin C fruits ke saath dal/iron wala khaana khaao — iron absorption 3x" },
        ],
      },
      {
        name: "Chai / Doodh", qty: "1 cup (200ml)", category: "Dairy", emoji: "🍵",
        keyNutrient: "Calcium 240mg (agar doodh ho)",
        steps: [
          { text: "Chai mein doodh kam, adrak + elaichi + tulsi — herbal better" },
          { text: "Dal/sabzi khane ke 1 ghante baad chai piyo",
            tip: "Chai/coffee iron absorption 60–70% ROK deti hai — khaane ke saath bilkul nahi" },
        ],
      },
    ],
  },
  {
    id: "bf_dalia_thali",
    slot: "breakfast",
    title: "Dalia / Oats Porridge Thali",
    timing: "7–9 AM",
    tags: ["fiber","light","calcium"],
    items: [
      {
        name: "Dalia Porridge (Doodh mein)", qty: "1 bowl (150g paka hua)", category: "Grain", emoji: "🥣",
        keyNutrient: "Iron 2.1mg, Fiber 4g, B vitamins",
        steps: [
          { text: "1/4 cup dalia + 3/4 cup doodh + 3/4 cup paani — ek saath garam karo" },
          { text: "Medium flame pe 10–12 min hilaate raho — dalia fully pake" },
          { text: "Honey / gud (1 tsp) + elaichi powder — natural sweetener" },
          { text: "Upar: 5 soaked badam (chopped) + 2 akhrot + kishmish (8–10)",
            tip: "Dalia ka iron + akhrot ka omega-3 + badam ka calcium = complete nutrition" },
          { text: "Seasonal fruit pieces mix karo — banana / guava / papaya",
            tip: "Vitamin C fruit + dalia ka iron = absorption 2x. Chai se 1 ghante ka gap rakho" },
        ],
      },
      {
        name: "Soaked Badam + Akhrot", qty: "5–6 badam + 2 akhrot (raat bhar bhigoe)", category: "Nuts", emoji: "🌰",
        keyNutrient: "Omega-3 2g, Calcium 50mg, Magnesium 45mg",
        steps: [
          { text: "Raat ko sone se pehle 5–6 badam + 2 akhrot + 8–10 kishmish paani mein bhigo do" },
          { text: "Subah khali pet ya nashte ke saath khaao — chilka utaar ke badam khaao",
            tip: "Soaked badam ka tannin-bound iron 40% more available — enzyme inhibitors soften ho jaate hain" },
          { text: "Kishmish ka paani bhi pi lo — iron + potassium ghul jaata hai paani mein",
            tip: "Soaked kishmish (8–10) = natural iron tonic, hemoglobin ke liye best" },
        ],
      },
    ],
  },
  {
    id: "bf_paratha_thali",
    slot: "breakfast",
    title: "Paratha + Dahi Thali",
    timing: "7–9 AM (heavy breakfast ho tab)",
    tags: ["filling","iron","calcium"],
    items: [
      {
        name: "Methi / Aloo Paratha", qty: "2 paratha (140g)", category: "Grain", emoji: "🫓",
        keyNutrient: "Iron 2.5mg (methi), Fiber 3g, B vitamins",
        steps: [
          { text: "Filling: methi (1 cup, barik katti + namak) ya aloo (ubla + mashed + spices)" },
          { text: "Gehun atte ka dough — methi seedha atte mein mix karo",
            tip: "Methi iron ka powerhouse hai — breakfast mein best timing" },
          { text: "Tawa garam karo — medium flame, dono taraf 3 min" },
          { text: "Sirf 1/4 tsp ghee per paratha (zyada nahi)" ,
            tip: "Ghee fat-soluble vitamins absorb karaata hai" },
          { text: "Achar + hara dhaniya + nimbu chutney ke saath serve karo" },
        ],
      },
      {
        name: "Dahi (thick)", qty: "1 katori (150g)", category: "Dairy", emoji: "🥛",
        keyNutrient: "Calcium 180mg, B12 0.8mcg",
        steps: DAHI_STEPS,
      },
      {
        name: "Seasonal Fruit ya Nimbu Paani", qty: "1 glass", category: "Drink", emoji: "🍋",
        keyNutrient: "Vitamin C 30–600mg",
        steps: [
          { text: "Khane ke saath ya baad mein 1 glass nimbu paani (bina cheeni) piyo",
            tip: "Nimbu ka Vitamin C paratha + dal ka iron 2–3x better absorb karata hai" },
        ],
      },
    ],
  },
];

// ── LUNCH OPTIONS ──────────────────────────────────────────────
export const LUNCH_OPTIONS: ThaliOption[] = [
  {
    id: "lu_dal_roti_thali",
    slot: "lunch",
    title: "Dal + Roti + Sabzi Thali",
    timing: "12:30–2 PM (best time — digestive fire highest)",
    tags: ["complete","iron","calcium","protein"],
    items: [
      {
        name: "Gehun Roti", qty: "2–3 roti (ya 1 cup brown rice)", category: "Grain", emoji: "🫓",
        keyNutrient: "Iron 2.3mg, Fiber 3.5g, B1 0.3mg",
        steps: ROTI_STEPS("gehun atta"),
      },
      {
        name: "Toor/Masoor Dal", qty: "1 katori (150g paki hui)", category: "Dal", emoji: "🍲",
        keyNutrient: "Iron 3–5mg, Protein 9g, Folate 180mcg",
        steps: DAL_COMMON_STEPS("Toor ya masoor dal"),
      },
      {
        name: "Sezon ki Sabzi (dry)", qty: "1 bowl (100g)", category: "Sabzi", emoji: "🥦",
        keyNutrient: "Vitamins C, A, K + Fiber",
        steps: SABZI_STEPS("palak / aloo / gobhi / bhindi",
          ["Aloo ya sabzi ko zyada oil mein mat talo — 1 tsp kafi hai",
           "Palak bilkul kam pakao — 2–3 min bas, warna Vitamin C aadha ho jaata hai"]),
      },
      {
        name: "Dahi / Raita", qty: "1 katori (150g)", category: "Dairy", emoji: "🥛",
        keyNutrient: "Calcium 200mg, B12 0.8mcg, Probiotics",
        steps: DAHI_STEPS,
      },
      {
        name: "Salad", qty: "1 small bowl", category: "Salad", emoji: "🥗",
        keyNutrient: "Vitamin C, Fiber, Folate",
        steps: SALAD_STEPS,
      },
      {
        name: "Ghee (roti par)", qty: "1/2 tsp", category: "Fat", emoji: "🧈",
        keyNutrient: "Fat-soluble vitamin absorption",
        steps: [
          { text: "Garam roti par 1/4–1/2 tsp desi ghee — bilkul serve karte time",
            tip: "Ghee ke bina fat-soluble vitamins (A, D, E, K) theek se absorb nahi hote. 1/2 tsp = sahi amount" },
        ],
      },
    ],
  },
  {
    id: "lu_rajma_chawal",
    slot: "lunch",
    title: "Rajma Chawal + Salad Thali",
    timing: "12:30–2 PM",
    tags: ["iron","protein","fiber","filling"],
    items: [
      {
        name: "Brown/White Rice", qty: "1 cup paka hua (180g)", category: "Grain", emoji: "🍚",
        keyNutrient: "Carbs 39g, Manganese, Selenium",
        steps: [
          { text: "Brown rice: raat bhar bhi bhigo sakte ho (optional, faster cooking)" },
          { text: "1 cup rice : 2 cup paani — medium flame, 20 min dhakkan ke saath",
            tip: "Brown rice glycemic index lower + more fiber/minerals than white rice" },
          { text: "Khaana banana ke paani ko use karo — nutrients usi mein hote hain" },
        ],
      },
      {
        name: "Rajma (pressure cooked)", qty: "1 katori (120g dry → 300g paka hua)", category: "Dal", emoji: "🫘",
        keyNutrient: "Iron 8mg, Protein 15g, Folate 230mcg",
        steps: [
          { text: "Raat bhar bhigo do — ZARURI hai, warna gas hogi aur nutrients kam absorb honge",
            tip: "Soaking rajma: phytic acid 50% kam, iron/zinc bioavailability 2x badh jaata hai" },
          { text: "Bhigone ke paani ko fenko — fresh paani se pressure cooker mein 5–6 seeti" },
          { text: "Lohe ki kadai mein: 1 tsp ghee + jeera + 2 pyaz (brown) + adrak-lehsun paste",
            tip: "Lohe ki kadai: rajma ka iron content significantly badhata hai" },
          { text: "Tamatar (2) + haldi + lal mirch + garam masala — 10 min bhunao" },
          { text: "Pake rajma daalo, 15–20 min dum pe pakao — thick gravy banao" },
          { text: "Serve karte time nimbu squeeze + hara dhaniya",
            tip: "Vitamin C (nimbu) + rajma ka iron = absorption 3x. Dahi ke saath nahi — calcium iron absorption ROKTA hai" },
        ],
      },
      {
        name: "Salad + Achaar", qty: "1 bowl salad + 1 tsp achaar", category: "Salad", emoji: "🥗",
        keyNutrient: "Fiber, Vitamin C, Probiotics",
        steps: SALAD_STEPS,
      },
      {
        name: "Papad (optional)", qty: "1 papad", category: "Side", emoji: "🫓",
        keyNutrient: "Protein 2g",
        steps: [{ text: "Roasted papad better than fried — 80% less fat", tip: "Fried papad = unnecessary oil" }],
      },
    ],
  },
  {
    id: "lu_chole_roti",
    slot: "lunch",
    title: "Chole + Bajra Roti Thali",
    timing: "12:30–2 PM",
    tags: ["iron","calcium","protein","filling"],
    items: [
      {
        name: "Bajra Roti", qty: "2 roti (80g)", category: "Grain", emoji: "🫓",
        keyNutrient: "Iron 4.8mg, Calcium 36mg, Magnesium 68mg",
        steps: ROTI_STEPS("bajra atta (millet flour)"),
      },
      {
        name: "Chole (Kabuli Chana)", qty: "1 katori pake hue (150g)", category: "Dal", emoji: "🫘",
        keyNutrient: "Iron 4.7mg, Protein 14g, Folate 280mcg",
        steps: [
          { text: "Raat bhar bhi bhigao — jab tak andar se white colour na aaye",
            tip: "Soaking 12 hr + sprout 6 hr = iron absorption 40% better" },
          { text: "Bhigone ka paani fenko, fresh paani se 6–7 seeti pressure cooker mein" },
          { text: "Lohe ki kadai + 1 tsp ghee + 2 pyaz brown tak bhunao" },
          { text: "Adrak-lehsun paste (1 tsp) + 2 tamatar + chole masala (2 tsp) + haldi" },
          { text: "Pake chole + 1 cup stock (cooked water) — 20 min sim karo" },
          { text: "Serve: amchoor + nimbu + hara dhaniya + pyaz rings + adrak julienne",
            tip: "Amchoor + nimbu = double Vitamin C hit — iron absorption maximize hota hai" },
        ],
      },
      {
        name: "Palak Sabzi (ya Kachumber)", qty: "1 bowl (100g)", category: "Sabzi", emoji: "🥬",
        keyNutrient: "Iron 2.7mg, Calcium 99mg, Vitamin C 28mg",
        steps: SABZI_STEPS("palak (spinach)",
          ["Palak mein oxalic acid hota hai — nimbu ya tamatar milaane se bioavailability badh jaati hai",
           "2-3 min bas pakao palak — zyada pakane se iron AND Vitamin C dono kam ho jaate hain"]),
      },
      {
        name: "Kachumber Salad", qty: "1 small bowl", category: "Salad", emoji: "🥗",
        keyNutrient: "Vitamin C, Fiber",
        steps: SALAD_STEPS,
      },
    ],
  },
];

// ── SNACK OPTIONS ──────────────────────────────────────────────
export const SNACK_OPTIONS: ThaliOption[] = [
  {
    id: "sn_fruit_nuts",
    slot: "snacks",
    title: "Fruit + Nuts Plate",
    timing: "4–5 PM",
    tags: ["vitamins","omega3","energy","light"],
    items: [
      {
        name: "Seasonal Fruit", qty: "1 medium ya 1 cup pieces", category: "Fruit", emoji: "🍎",
        keyNutrient: "Vitamin C 30–600mg, Fiber 2–5g",
        steps: [
          { text: "Best snack time: 4–5 PM (3+ ghante baad lunch, 2+ ghante pehle dinner)" },
          { text: "Guava (amrud): Vitamin C 228mg — best fruit for iron absorption",
            tip: "Ek guava = 3 oranges ka Vitamin C, double the fiber" },
          { text: "Pomegranate (anar): Iron 0.3mg + Vitamin C 10mg — daily khaao",
            tip: "Anar ke seeds mein punicic acid = best anti-inflammatory fatty acid" },
          { text: "Banana: potassium 358mg + B6 — gym ke baad best",
            tip: "Banana ka sugar slow-release (fiber ke saath) = sustained energy, crash nahi" },
        ],
      },
      {
        name: "Mixed Nuts (soaked/raw)", qty: "4-5 badam + 2 akhrot + 8 kishmish", category: "Nuts", emoji: "🌰",
        keyNutrient: "Omega-3 2g, Iron 1.5mg, Magnesium 50mg",
        steps: [
          { text: "Badam: raat bhar bhigo ke subah se bachaye hue use karo (ya 4 ghante bhi chalega)",
            tip: "Soaked badam: tannins 50% kam, Vitamin E + magnesium better absorbed" },
          { text: "Akhrot: KABHI heat nahi karna — omega-3 degrade ho jaate hain room temp par raho" },
          { text: "Kishmish: natural iron + quick energy — zyada nahi (sugar high)",
            tip: "Kaju/pista zyada mat khaao evening mein — calorie dense hain" },
        ],
      },
    ],
  },
  {
    id: "sn_roasted_chana",
    slot: "snacks",
    title: "Roasted Chana + Nimbu Paani",
    timing: "4–5 PM",
    tags: ["protein","iron","fiber"],
    items: [
      {
        name: "Bhuna Kala Chana", qty: "1 mutthi (30–40g)", category: "Snack", emoji: "🫘",
        keyNutrient: "Iron 2.7mg, Protein 6g, Fiber 4g",
        steps: [
          { text: "Dry roast kala chana in heavy pan — medium flame, 5–7 min hilaate raho" },
          { text: "Kala namak + jeera powder + nimbu — mix karo",
            tip: "Kala chana iron ka ek acha source hai. Nimbu ka Vitamin C absorption 2x karta hai" },
          { text: "Pyaz + hara dhaniya milaao — chaat style" },
        ],
      },
      {
        name: "Nimbu Paani (fresh)", qty: "1 glass (250ml)", category: "Drink", emoji: "🍋",
        keyNutrient: "Vitamin C 30mg, Potassium",
        steps: [
          { text: "1/2 nimbu + kala namak + jeera powder + paani — natural electrolyte drink",
            tip: "Bina cheeni nimbu paani = Vitamin C + minerals without calories. Chai se kahi better" },
        ],
      },
    ],
  },
];

// ── DINNER OPTIONS ─────────────────────────────────────────────
export const DINNER_OPTIONS: ThaliOption[] = [
  {
    id: "di_moong_khichdi",
    slot: "dinner",
    title: "Moong Dal Khichdi + Sabzi Thali",
    timing: "7–8 PM (8 baje ke baad mat khao)",
    tags: ["light","easy-digest","iron","no-dahi"],
    items: [
      {
        name: "Moong Dal Khichdi", qty: "1.5 katori paki hui (200g)", category: "Grain+Dal", emoji: "🍲",
        keyNutrient: "Iron 2.1mg, Protein 8g, Easy digest",
        steps: [
          { text: "1/4 cup moong dal (dhuli) + 1/4 cup rice — dono dhoo ke 30 min bhigo do" },
          { text: "Pressure cooker: 2 cup paani + haldi + namak — 2–3 seeti" },
          { text: "Ghee (1 tsp) + jeera + hing + haldi + garam masala light tadka",
            tip: "Moong dal sabse easy to digest hai — raat ke liye perfect, gut pe stress nahi" },
          { text: "Thoda paani add karo — porridge jaise consistency" },
          { text: "Nimbu + hara dhaniya garnish",
            tip: "Moong dal ka iron + nimbu = night mein bhi iron absorb hota rehta hai" },
        ],
      },
      {
        name: "Light Sabzi (Lauki/Tinda/Turai)", qty: "1 bowl (100–120g)", category: "Sabzi", emoji: "🥒",
        keyNutrient: "Fiber, Vitamin C, low calorie",
        steps: SABZI_STEPS("lauki ya tinda ya turai",
          ["Raat ke liye gourds best — 90% water, easy digest, cool nature",
           "Lauki badle mein tinda ya turai bhi sahi hai — low calorie, high water"]),
      },
      {
        name: "Roti (optional)", qty: "1–2 roti (agar extra hunger)", category: "Grain", emoji: "🫓",
        keyNutrient: "Iron 1.3mg, Fiber 2g",
        steps: ROTI_STEPS("gehun ya bajra atta"),
      },
      {
        name: "AVOID: Dahi raat mein", qty: "—", category: "Reminder", emoji: "❌",
        keyNutrient: "",
        steps: [
          { text: "Raat mein dahi bilkul nahi khaana — Ayurveda + modern gut science dono agree karte hain",
            tip: "Raat mein dahi: kapha dosha badhaata hai, mucus, sinusitis, slow digestion. Lunch mein khaao dahi" },
          { text: "Agar doodh chahiye raat ko — 1 glass garam doodh + haldi = calcium + tryptophan for sleep",
            tip: "Garam haldi doodh raat ko: Vitamin D + calcium absorption sleep ke dauraan hoti hai" },
        ],
      },
    ],
  },
  {
    id: "di_dal_roti_sabzi",
    slot: "dinner",
    title: "Dal + Roti + Sabzi Thali (Light)",
    timing: "7–8 PM",
    tags: ["light","iron","protein","no-dahi"],
    items: [
      {
        name: "Masoor / Moong Dal", qty: "1 katori (120g paki hui)", category: "Dal", emoji: "🍲",
        keyNutrient: "Iron 3mg, Protein 9g",
        steps: DAL_COMMON_STEPS("Masoor ya moong dal"),
      },
      {
        name: "Gehun / Bajra Roti", qty: "2 roti (lunch se 1 kam)", category: "Grain", emoji: "🫓",
        keyNutrient: "Iron 2.5mg (bajra), Fiber 3g",
        steps: ROTI_STEPS("bajra ya gehun atta"),
      },
      {
        name: "Palak / Gobhi Sabzi", qty: "1 bowl (100g)", category: "Sabzi", emoji: "🥬",
        keyNutrient: "Iron 2.7mg (palak), Calcium 47mg (gobhi)",
        steps: SABZI_STEPS("palak ya gobhi",
          ["Raat ko palak best hai — iron high, easy digest",
           "Palak sirf 2 min pakao raat mein — vitamins preserve honge"]),
      },
      {
        name: "Salad (kheera + tamatar)", qty: "1 small bowl", category: "Salad", emoji: "🥗",
        keyNutrient: "Fiber, Vitamin C, Water",
        steps: SALAD_STEPS,
      },
      {
        name: "Raat ko sone se pehle (optional)", qty: "1 glass", category: "Drink", emoji: "🌙",
        keyNutrient: "Calcium 300mg, Tryptophan",
        steps: [
          { text: "Garam doodh (1 glass) + haldi (1/4 tsp) + kali mirch (pinch) + honey (1/2 tsp)",
            tip: "Haldi doodh raat ko: calcium absorption best hoti hai sleep mein + melatonin badhata hai (tryptophan)" },
        ],
      },
    ],
  },
];

// ── DRY FRUIT + FRUIT ROUTINE ──────────────────────────────────
export const DAILY_ROUTINE: DailyRoutine = {
  dryFruits: [
    { name: "Soaked Badam", qty: "5–6 (chilke utaar ke)", when: "Subah khali pet ya nashte ke saath",
      tip: "Soaking: enzyme inhibitors hat jaate hain → Vitamin E + magnesium 30% better absorb" },
    { name: "Soaked Akhrot", qty: "2–3 pieces (raat bhar bhigoe)", when: "Subah nashte ke saath",
      tip: "Akhrot = best plant omega-3. Kabhi heat nahi karna. Soaking tannins remove karta hai" },
    { name: "Soaked Kishmish / Munakka", qty: "8–10 dane", when: "Subah khali pet",
      tip: "Soaked kishmish ka paani bhi pio — iron dissolved hota hai. Hemoglobin ke liye best" },
    { name: "Anjeer (Dried Fig)", qty: "2–3 (raat bhar bhigoe)", when: "Subah nashte ke saath",
      tip: "Anjeer: Calcium 162mg + Iron 2mg per 100g. Constipation bhi door karta hai" },
    { name: "Khajoor (Dates)", qty: "2–3 dana", when: "Lunch ya snack ke saath (NOT raat mein)",
      tip: "Khajoor: natural iron + instant energy. Raat ko avoid — sugar spike ho sakta hai" },
    { name: "Kaju / Pista", qty: "4–5 piece (limited)", when: "Snack time (4–5 PM)",
      tip: "Kaju-pista calorie dense hai — zyada nahi. Zinc + magnesium ke liye rooz thoda" },
  ],
  fruits: [
    { name: "Amla", qty: "2–3 fresh ya 1 tsp powder", when: "Subah khali pet best, ya nashte ke saath",
      tip: "Amla: Vitamin C 600mg — highest among all fruits. Dal ke saath khao → iron 3x absorb" },
    { name: "Guava (Amrud)", qty: "1 medium (100g)", when: "Snack (4–5 PM) ya breakfast ke baad",
      tip: "Guava: Vitamin C 228mg + Fiber 5g — best iron-absorption fruit. Daily khaao" },
    { name: "Pomegranate (Anar)", qty: "1/2 medium ya 1/2 cup dana", when: "Snack (4 PM) ya lunch ke baad",
      tip: "Anar: iron + Vitamin C combo already in one fruit. Hemoglobin ke liye best" },
    { name: "Banana (Kela)", qty: "1 medium", when: "Breakfast ke saath ya gym ke baad",
      tip: "Kela: B6 + potassium + quick energy. Empty stomach avoid karo (acidic response)" },
    { name: "Papaya (Papita)", qty: "1 cup pieces (150g)", when: "Breakfast baad ya snack",
      tip: "Papaya: Vitamin A 1009mcg + Vitamin C 60mg + papain (digestive enzyme). Weekly 3–4 baar" },
    { name: "Seasonal Citrus", qty: "1 orange / mosambi", when: "Snack ya lunch ke baad",
      tip: "Citrus ka Vitamin C: best if eaten 30 min after iron-rich meal for max absorption" },
  ],
};

// ── Public API ──────────────────────────────────────────────────

export function getMealOptions(
  slot: "breakfast" | "lunch" | "snacks" | "dinner",
  deficiencies: string[],
): ThaliOption[] {
  const allOptions: Record<string, ThaliOption[]> = {
    breakfast: BREAKFAST_OPTIONS,
    lunch: LUNCH_OPTIONS,
    snacks: SNACK_OPTIONS,
    dinner: DINNER_OPTIONS,
  };
  const opts = allOptions[slot] ?? LUNCH_OPTIONS;

  // Sort by relevance to deficiencies
  return [...opts].sort((a, b) => {
    const score = (o: ThaliOption) => deficiencies.filter(d => o.tags.includes(d) ||
      o.items.some(it => (it.keyNutrient ?? "").toLowerCase().includes(d.replace("_"," ")))).length;
    return score(b) - score(a);
  });
}

// For "Today's Remaining Plan" - nutrient-specific suggestion
export function quickSuggestion(nutrient: string, meal: string, _state: string): string {
  const map: Record<string,string> = {
    iron:        `${meal}: Dal (lohe ki kadai mein) + Roti + Nimbu paani — iron 3x absorb hoga`,
    vitamin_b12: `${meal}: Dahi (lunch mein) + Paneer + Doodh raat ko`,
    vitamin_d:   `Kal subah: 20 min dhoop (9–11 AM), phir fortified doodh`,
    calcium:     `${meal}: Ragi roti (344mg per 100g) + Dahi (lunch) + Til chutney`,
    zinc:        `${meal}: Kaju (4–5) + Pumpkin seeds (1 tbsp) + Dal`,
    omega3:      `${meal}: 2–3 akhrot (soaked) + Alsi powder roti mein milaao`,
    magnesium:   `${meal}: Akhrot + Palak sabzi + Dark moong dal`,
    folate:      `${meal}: Hara dhaniya + Rajma dal + Moong sprouts`,
    vitamin_c:   `Abhi: Amla ya guava khaao — phir iron wala khaana khaao 30 min mein`,
    vitamin_a:   `${meal}: Gajar sabzi + Palak + Papita snack mein`,
  };
  return map[nutrient] ?? `${nutrient} ke rich foods lo is meal mein`;
}
