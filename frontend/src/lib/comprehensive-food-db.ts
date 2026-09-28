/**
 * Comprehensive Indian Food Nutritional Database
 * Sources: ICMR-NIN 2017, USDA FoodData Central, published literature
 * Per 100g edible portion (raw/dry unless state noted)
 * Nutrients: iron(mg), vitamin_b12(mcg), vitamin_d(mcg), calcium(mg), magnesium(mg),
 *            zinc(mg), vitamin_c(mg), vitamin_a(mcg RAE), folate(mcg), omega3(g),
 *            selenium(mcg), vitamin_b6(mg), potassium(mg), phosphorus(mg),
 *            vitamin_b1(mg), vitamin_b2(mg), vitamin_b3(mg), vitamin_e(mg),
 *            protein(g), fiber(g), energy(kcal)
 */
import type { FoodItem } from "./food-db";

type N = Partial<Record<string,number>>;

function n(iron=0,b12=0,vitD=0,ca=0,mg=0,zn=0,vitC=0,vitA=0,folate=0,om3=0,se=0,b6=0,k=0,phos=0,b1=0,b2=0,b3=0,vitE=0,iodine=0,copper=0,manganese=0,chromium=0,vitK=0,b5=0,b7=0,prot=0,fiber=0,kcal=0): N {
  const o: N = {};
  const keys = ["iron","vitamin_b12","vitamin_d","calcium","magnesium","zinc","vitamin_c","vitamin_a","folate","omega3","selenium","vitamin_b6","potassium","phosphorus","vitamin_b1","vitamin_b2","vitamin_b3","vitamin_e","iodine","copper","manganese","chromium","vitamin_k","vitamin_b5","vitamin_b7"];
  const vals = [iron,b12,vitD,ca,mg,zn,vitC,vitA,folate,om3,se,b6,k,phos,b1,b2,b3,vitE,iodine,copper,manganese,chromium,vitK,b5,b7];
  keys.forEach((k,i) => { if(vals[i]>0) o[k]=vals[i]; });
  if(prot>0) o["protein"]=prot;
  if(fiber>0) o["fiber"]=fiber;
  if(kcal>0) o["energy"]=kcal;
  return o;
}

// Preparation state multipliers (applied to raw values)
// [iron, b12, vitD, ca, mg, zn, vitC, vitA, folate, om3, se, b6, k, phos, b1, b2, b3, vitE,
//  iodine, copper, manganese, chromium, vitK, b5, b7, prot, fiber, kcal_factor, weight_change]
// New trace/vitamin columns (iodine..b7) follow the retention behaviour of the closest-studied
// nutrient in the same class: iodine~potassium (leaches in cooking water), copper/manganese/
// chromium~zinc (heat-stable trace minerals), vitamin_k~vitamin_e (fat-soluble, heat-stable),
// b5/b7~b2 (water-soluble B-vitamins, moderate boiling loss). Source: USDA Table of Nutrient
// Retention Factors, Release 6 (2007); ICMR-NIN (2017) cooking-loss studies for Indian staples.
const STATE_MULT: Record<string, number[]> = {
  //                  Fe   B12  D    Ca   Mg   Zn   C    A    Fol  Om3  Se   B6   K    P    B1   B2   B3   E    I    Cu   Mn   Cr   K2   B5   B7   Prot Fib  Kcal Wt
  "raw":            [ 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
  "soaked 4hr":     [ 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 0.95,1.05,1.0, 1.0, 1.0, 0.95,1.0, 1.0, 1.0, 0.95,1.3],
  "soaked overnight":[ 1.2, 1.0, 1.0, 0.9, 0.9, 1.3, 1.1, 1.0, 1.1, 1.0, 1.0, 1.0, 0.85,0.9, 1.0, 1.0, 1.0, 1.0, 0.9, 1.1, 1.0, 1.0, 1.0, 0.9, 0.95,1.0, 1.0, 0.9, 1.4],
  "sprouted":       [ 1.5, 1.0, 1.0, 0.85,0.9, 1.4, 4.0, 1.2, 2.0, 1.1, 1.0, 1.3, 0.8, 0.85,1.5, 1.3, 1.2, 1.0, 0.85,1.2, 1.1, 1.0, 1.0, 1.3, 1.2, 1.0, 1.0, 0.8, 1.6],
  "boiled":         [ 0.85,1.0, 1.0, 0.9, 0.85,0.85,0.5, 0.85,0.6, 0.9, 0.85,0.75,0.75,0.85,0.7, 0.75,0.75,0.85,0.75,0.85,0.85,0.85,0.85,0.75,0.85,0.9, 0.9, 0.85,2.5],
  "pressure cooked":[ 0.85,1.0, 1.0, 0.88,0.85,0.85,0.45,0.8, 0.55,0.9, 0.82,0.7, 0.72,0.82,0.65,0.7, 0.7, 0.8, 0.72,0.82,0.82,0.82,0.8, 0.7, 0.8, 0.88,0.88,0.85,2.4],
  "roasted":        [ 0.95,1.0, 1.0, 1.0, 0.95,0.95,0.4, 0.9, 0.85,0.88,0.9, 0.85,0.9, 0.95,0.8, 0.85,0.85,0.82,0.9, 0.95,0.95,0.95,0.85,0.85,0.88,1.0, 0.95,1.1, 0.85],
  "steamed":        [ 0.9, 1.0, 1.0, 0.95,0.9, 0.9, 0.7, 0.9, 0.75,0.95,0.9, 0.85,0.88,0.9, 0.8, 0.85,0.85,0.9, 0.85,0.9, 0.9, 0.9, 0.9, 0.85,0.88,0.95,0.95,0.9, 1.2],
  "cooked (curry)": [ 0.88,1.0, 1.0, 0.88,0.85,0.85,0.45,0.85,0.6, 0.9, 0.85,0.75,0.72,0.85,0.7, 0.75,0.75,0.85,0.72,0.85,0.85,0.85,0.83,0.7, 0.83,0.9, 0.9, 0.87,2.2],
  "dry roasted":    [ 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.95,0.9, 0.9, 0.95,0.9, 0.95,1.0, 0.85,0.9, 0.9, 0.88,0.95,1.0, 1.0, 1.0, 0.92,0.9, 0.92,1.0, 1.0, 1.05,0.9],
};

interface BaseFoodData {
  id: string;
  name: string;
  hindi: string;
  aliases: string[];      // search aliases
  category: string;
  baseNutrients: N;       // per 100g raw
  states: string[];       // which prep states apply
  serving100g: string;    // human-readable serving ~100g
  state?: string;         // Indian state (optional)
}

// ── DAL / LEGUMES ─────────────────────────────────────────────
const DALS: BaseFoodData[] = [
  {
    id:"moong_dal", name:"Beans, mung, mature seeds, split, raw (Moong Dal)", hindi:"मूंग दाल",
    aliases:["moong","mung","green gram","mung dal","mung bean","sabut moong","hari moong","dhuli moong"],
    category:"Dal",
    baseNutrients: n(8.5,0,0,124,189,2.7,4.8,6,625,0.6,6.2,0.38,789,367,0.62,0.23,2.6,0.5,0,0.94,1.04,0,9,1.19,0,24,8,347),
    states:["raw","soaked 4hr","soaked overnight","sprouted","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori pakne ke baad (~60g raw)"
  },
  {
    id:"masoor_dal", name:"Lentils, red, split, raw (Masoor Dal)", hindi:"मसूर दाल",
    aliases:["masoor","red lentil","pink dal","lal dal","masur","red dal"],
    category:"Dal",
    baseNutrients: n(7.6,0,0,56,122,3.3,4.4,0,479,0.09,8.3,0.54,678,451,0.87,0.21,2.6,0.4,0,0.75,1.4,0,5,1.5,0,25.8,10.7,343),
    states:["raw","soaked 4hr","soaked overnight","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g raw)"
  },
  {
    id:"chana_dal", name:"Chickpeas (Bengal gram), split, raw", hindi:"चना दाल",
    aliases:["chana","bengal gram","desi chana","chane ki dal","gram dal"],
    category:"Dal",
    baseNutrients: n(4.6,0,0,73,139,2.8,1.5,3,285,0.1,8.2,0.54,846,318,0.48,0.13,1.7,0.4,0,0.66,1.6,0,9,1.0,0,20.1,16.8,372),
    states:["raw","soaked 4hr","soaked overnight","sprouted","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g raw)"
  },
  {
    id:"urad_dal", name:"Beans, black gram (urad), split, raw", hindi:"उड़द दाल",
    aliases:["urad","black gram","kaali dal","maa di dal","black lentil","dhuli urad","sabut urad","maa ki dal"],
    category:"Dal",
    baseNutrients: n(7.3,0,0,154,267,3.7,0,0,622,0.06,1.5,0.28,1388,379,0.44,0.27,2.0,0.5,0,0.94,1.4,0,8,1.2,0,25.2,18.3,347),
    states:["raw","soaked 4hr","soaked overnight","sprouted","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g raw)"
  },
  {
    id:"toor_dal", name:"Peas, pigeon (toor), split, raw", hindi:"तूर दाल",
    aliases:["arhar","arhar dal","tur dal","pigeon pea","tuvar","tur","arhar ki dal"],
    category:"Dal",
    baseNutrients: n(7.0,0,0,73,134,2.9,0,0,456,0.14,7.9,0.29,1392,294,0.56,0.21,2.8,0.4,0,0.75,1.79,0,6,1.3,0,22.3,15.0,335),
    states:["raw","soaked 4hr","soaked overnight","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g raw)"
  },
  {
    id:"rajma", name:"Beans, kidney, red, mature seeds, raw (Rajma)", hindi:"राजमा",
    aliases:["kidney bean","red beans","rajmah","rajme","red kidney beans"],
    category:"Dal",
    baseNutrients: n(8.2,0,0,143,140,2.7,4.5,0,394,0.28,3.2,0.4,1406,407,0.5,0.22,2.1,0.3,0,0.86,1.06,0,19,0.8,0,22.5,24.9,336),
    states:["raw","soaked overnight","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g dry)"
  },
  {
    id:"kala_chana", name:"Chickpeas, whole, brown, raw (Kala Chana)", hindi:"काला चना",
    aliases:["black chana","desi chana whole","horse gram","kale chane","bengal gram whole","kala chhola"],
    category:"Dal",
    baseNutrients: n(7.2,0,0,202,166,2.76,1.5,9,557,0.2,7.0,0.54,875,324,0.48,0.13,2.0,0.4,0,0.66,1.6,0,9,1.0,0,17.4,17.4,360),
    states:["raw","soaked overnight","sprouted","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g dry)"
  },
  {
    id:"chole", name:"Chickpeas (garbanzo beans), whole, raw (Chole)", hindi:"छोले / काबुली चना",
    aliases:["chickpea","kabuli chana","safed chana","garbanzo","chhole","white chana","kabuli"],
    category:"Dal",
    baseNutrients: n(6.2,0,0,105,115,3.43,1.3,4,557,0.1,8.2,0.54,875,366,0.48,0.21,1.3,0.3,0,0.66,1.6,0,9,1.0,0,19.3,17.4,364),
    states:["raw","soaked overnight","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g dry)"
  },
  {
    id:"lobia", name:"Peas, cowpeas (blackeyed), mature seeds, raw (Lobia)", hindi:"लोबिया",
    aliases:["cowpea","black eyed peas","lobia","lobiya","chauli"],
    category:"Dal",
    baseNutrients: n(8.4,0,0,77,184,3.4,1.5,10,633,0.2,9.9,0.39,1112,423,0.85,0.45,2.3,0.5,0,0.68,1.66,0,5,1.0,0,23.5,25.5,323),
    states:["raw","soaked overnight","sprouted","boiled","pressure cooked","cooked (curry)"],
    serving100g:"1 katori (~60g dry)"
  },
  {
    id:"kulthi", name:"Beans, horse gram, mature seeds, raw (Kulthi)", hindi:"कुल्थी",
    aliases:["horse gram","kulthi","hurali","kollu","muthira","gahat"],
    category:"Dal",
    baseNutrients: n(6.8,0,0,287,163,2.4,0,0,0,0,0,0.1,1200,311,0.4,0.2,1.5,0.5,0,0.6,1.5,0,0,0,0,22,5.3,321),
    states:["raw","soaked overnight","sprouted","boiled","cooked (curry)"],
    serving100g:"1 katori (~60g dry)"
  },
  {
    id:"matki", name:"Beans, moth, mature seeds, raw (Matki)", hindi:"मटकी",
    aliases:["moth bean","matki","matkee","dew bean"],
    category:"Dal",
    baseNutrients: n(10.4,0,0,202,181,3.1,2.5,0,0,0,0,0.3,1055,374,0.56,0.25,2.0,0.4,0,0.7,1.5,0,0,0,0,22.9,8.0,343),
    states:["raw","soaked overnight","sprouted","boiled","cooked (curry)"],
    serving100g:"1 katori (~60g dry)"
  },
  {
    id:"sabut_moong", name:"Beans, mung, mature seeds, whole, raw (Sabut Moong)", hindi:"साबुत मूंग",
    aliases:["whole moong","whole green gram","sabut moong","hari moong whole","green moong"],
    category:"Dal",
    baseNutrients: n(7.0,0,0,132,173,2.6,4.8,6,625,0.6,6.0,0.38,789,367,0.54,0.23,2.3,0.5,0,0.94,1.04,0,9,1.19,0,24.0,7.6,347),
    states:["raw","soaked overnight","sprouted","boiled","cooked (curry)"],
    serving100g:"1 katori (~60g dry)"
  },
];

// ── VEGETABLES ────────────────────────────────────────────────
const VEGETABLES: BaseFoodData[] = [
  {
    id:"palak", name:"Spinach, raw", hindi:"पालक",
    aliases:["paalak","spinach","saag","palaka","hara saag","spinch","palok"],
    category:"Sabzi",
    baseNutrients: n(2.7,0,0,99,79,0.53,28,469,194,0.1,1,0.2,558,49,0.08,0.19,0.72,2.0,0,0,0,0,0,0,0,2.9,2.2,23),
    states:["raw","steamed","boiled","cooked (curry)"],
    serving100g:"1 katora"
  },
  {
    id:"methi_leaves", name:"Fenugreek leaves, raw", hindi:"मेथी",
    aliases:["methi","fenugreek","fenugreek leaves","methi leaves","kasuri methi","methi ka saag"],
    category:"Sabzi",
    baseNutrients: n(1.93,0,0,176,67,0.36,52,395,57,0.07,0.9,0.13,770,51,0.1,0.37,0.8,0.5,0,0,0,0,0,0,0,4.4,3.9,49),
    states:["raw","steamed","boiled","cooked (curry)"],
    serving100g:"1 katora"
  },
  {
    id:"bathua", name:"Chenopodium (bathua) leaves, raw", hindi:"बथुआ",
    aliases:["bathua","bathwa","chenopodium","goosefoot","pigweed","bathuwa"],
    category:"Sabzi",
    baseNutrients: n(4.2,0,0,150,62,0.4,35,0,0,0,0,0,0,0,0.1,0.21,0.3,0.5,0,0,0,0,0,0,0,3.7,2.0,34),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 katora"
  },
  {
    id:"sarson_saag", name:"Mustard greens, raw", hindi:"सरसों का साग",
    aliases:["sarson","mustard greens","sarson saag","sarson leaves","mustard leaves","sarsoo"],
    category:"Sabzi",
    baseNutrients: n(4.4,0,0,155,29,0.25,117,640,187,0.17,0.9,0.16,384,58,0.08,0.11,0.73,2.6,0,0,0,0,0,0,0,2.1,3.2,27),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 katora"
  },
  {
    id:"aloo", name:"Potatoes, flesh and skin, raw", hindi:"आलू",
    aliases:["alu","aaloo","potato","batata","urulaikizhangu","aloo","batate"],
    category:"Sabzi",
    baseNutrients: n(0.78,0,0,12,23,0.3,19.7,0,15,0.01,0.4,0.3,421,57,0.08,0.03,1.05,0.01,0,0,0,0,0,0,0,2.0,2.2,77),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 medium aloo"
  },
  {
    id:"matar", name:"Peas, green, raw", hindi:"मटर",
    aliases:["peas","green peas","mattar","vatana","pattani","hare matar","fresh peas"],
    category:"Sabzi",
    baseNutrients: n(1.47,0,0,25,33,1.24,40,38,65,0.04,1.8,0.17,244,108,0.27,0.13,2.09,0.13,0,0,0,0,0,0,0,5.4,5.1,81),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 katora"
  },
  {
    id:"gajar", name:"Carrots, raw", hindi:"गाजर",
    aliases:["carrot","gaajar","carrot sabzi","gajjar","gajar"],
    category:"Sabzi",
    baseNutrients: n(0.3,0,0,33,12,0.24,5.9,835,19,0.01,0.1,0.14,320,35,0.07,0.06,0.98,0.66,0,0,0,0,0,0,0,0.9,2.8,41),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 badi gajar"
  },
  {
    id:"gobhi", name:"Cauliflower, raw", hindi:"फूलगोभी",
    aliases:["gobi","cauliflower","cauliflower sabzi","phoolgobhi","phool gobhi","aloo gobhi"],
    category:"Sabzi",
    baseNutrients: n(0.44,0,0,22,15,0.27,48.2,0,57,0.04,0.6,0.18,299,44,0.06,0.06,0.51,0.08,0,0,0,0,0,0,0,1.9,2.5,25),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 cup phool"
  },
  {
    id:"baingan", name:"Eggplant (aubergine), raw", hindi:"बैंगन",
    aliases:["brinjal","eggplant","aubergine","baigan","begun","ringna","begun","vangi"],
    category:"Sabzi",
    baseNutrients: n(0.23,0,0,9,14,0.16,2.2,0,22,0.07,0.3,0.08,229,24,0.04,0.04,0.65,0.3,0,0,0,0,0,0,0,0.98,3.0,25),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 medium baingan"
  },
  {
    id:"bhindi", name:"Okra, raw", hindi:"भिंडी",
    aliases:["okra","ladies finger","lady finger","vendakka","bendekai","bhindi","dendo"],
    category:"Sabzi",
    baseNutrients: n(0.62,0,0,82,57,0.58,23,36,88,0.03,0.7,0.22,299,61,0.2,0.06,1.0,0.36,0,0,0,0,0,0,0,2.0,3.2,33),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"8-10 bhindi"
  },
  {
    id:"lauki", name:"Gourd, bottle (lauki), raw", hindi:"लौकी",
    aliases:["bottle gourd","ghiya","doodhi","dudhi","sorakkai","lau","lauki","kaddu"],
    category:"Sabzi",
    baseNutrients: n(0.2,0,0,26,11,0.07,10.1,0,0,0.01,0.2,0.04,150,13,0.03,0.02,0.4,0.02,0,0,0,0,0,0,0,0.6,0.5,14),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 cup pieces"
  },
  {
    id:"karela", name:"Bitter melon (karela), raw", hindi:"करेला",
    aliases:["bitter gourd","bitter melon","pavakka","hagalakai","karela","bitter"],
    category:"Sabzi",
    baseNutrients: n(0.43,0,0,19,17,0.8,88,24,72,0.02,0.2,0.04,296,31,0.04,0.04,0.4,0.14,0,0,0,0,0,0,0,1.0,2.8,17),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"2 medium karele"
  },
  {
    id:"tinda", name:"Gourd, round (tinda), raw", hindi:"टिंडा",
    aliases:["tinda","round gourd","apple gourd","tindora","kundru","tindli"],
    category:"Sabzi",
    baseNutrients: n(0.3,0,0,20,11,0.1,13,0,0,0,0.2,0.05,110,30,0.03,0.02,0.3,0.04,0,0,0,0,0,0,0,1.2,1.5,21),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"6-8 tinde"
  },
  {
    id:"turai", name:"Gourd, ridge (turai), raw", hindi:"तुरई",
    aliases:["ridge gourd","torai","beerakaya","turai","zucchini like"],
    category:"Sabzi",
    baseNutrients: n(0.36,0,0,18,14,0.06,12.0,35,0,0.05,0.2,0.04,139,32,0.05,0.06,0.4,0.14,0,0,0,0,0,0,0,1.1,0.5,17),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 cup pieces"
  },
  {
    id:"kaddu", name:"Pumpkin, raw", hindi:"कद्दू",
    aliases:["pumpkin","sitaphal","petha","kumbalangi","parangikkai","kaddu","lal kaddu"],
    category:"Sabzi",
    baseNutrients: n(0.8,0,0,21,12,0.32,9,426,16,0.05,0.3,0.06,340,44,0.05,0.11,0.6,1.06,0,0,0,0,0,0,0,1.0,0.5,26),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 cup pieces"
  },
  {
    id:"shimla_mirch", name:"Peppers, sweet, bell, raw", hindi:"शिमला मिर्च",
    aliases:["capsicum","bell pepper","red pepper","green pepper","yellow pepper","shimla","sweet pepper","lal mirch sabzi"],
    category:"Sabzi",
    baseNutrients: n(0.43,0,0,7,10,0.13,128,157,46,0.28,0.3,0.29,211,26,0.05,0.09,0.98,1.58,0,0,0,0,0,0,0,0.99,2.1,31),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 medium shimla mirch"
  },
  {
    id:"tamatar", name:"Tomatoes, red, ripe, raw", hindi:"टमाटर",
    aliases:["tomato","tamaatar","tamaater","timaatar","lal tamatar"],
    category:"Sabzi",
    baseNutrients: n(0.27,0,0,10,11,0.17,13.7,42,15,0.05,0.2,0.08,237,24,0.04,0.02,0.59,0.54,0,0,0,0,0,0,0,0.88,1.2,18),
    states:["raw","cooked (curry)"],
    serving100g:"1-2 tamatar"
  },
  {
    id:"broccoli", name:"Broccoli, raw", hindi:"ब्रोकोली",
    aliases:["brokali","brocoli","broccoli","hara gobhi"],
    category:"Sabzi",
    baseNutrients: n(0.73,0,0,47,21,0.41,89.2,623,63,0.11,2.5,0.18,316,66,0.07,0.12,0.64,0.78,0,0,0,0,0,0,0,2.82,2.6,34),
    states:["raw","steamed","boiled","cooked (curry)"],
    serving100g:"1 cup florets"
  },
  {
    id:"sweet_potato", name:"Sweet potato, raw, unprepared", hindi:"शकरकंद",
    aliases:["shakarkand","shakarkandi","sweet potato","ratalu","sarkande","meetha aloo"],
    category:"Sabzi",
    baseNutrients: n(0.61,0,0,30,25,0.3,2.4,961,11,0.01,0.6,0.3,337,47,0.08,0.06,0.56,0.26,0,0,0,0,0,0,0,1.57,3.0,86),
    states:["raw","boiled","steamed"],
    serving100g:"1 medium shakarkand"
  },
  {
    id:"chukandar", name:"Beets, raw", hindi:"चुकंदर",
    aliases:["beetroot","beet","red beet","chukander","chukandar"],
    category:"Sabzi",
    baseNutrients: n(0.8,0,0,16,23,0.35,4.9,0,109,0.02,0.7,0.07,325,40,0.03,0.04,0.33,0.04,0,0,0,0,0,0,0,1.61,2.8,43),
    states:["raw","boiled","steamed"],
    serving100g:"2 medium chukandars"
  },
  {
    id:"drumstick", name:"Drumstick (moringa) pods, raw", hindi:"सहजन",
    aliases:["drumstick","sahjan","moringa pods","saijan","munaga","muringakkai","drumstick sabzi"],
    category:"Sabzi",
    baseNutrients: n(0.36,0,0,30,45,0.45,141,74,44,0.1,0.8,0.12,461,50,0.05,0.07,0.62,0.15,0,0,0,0,0,0,0,2.1,3.2,37),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"5-6 drumstick pieces"
  },
  {
    id:"moringa_leaves", name:"Moringa leaves, raw", hindi:"सहजन पत्ते",
    aliases:["moringa leaves","sahjan patta","moringa","drumstick leaves","munaga leaves"],
    category:"Sabzi",
    baseNutrients: n(4.0,0,0,185,147,0.6,220,378,40,1.6,8.9,1.2,337,112,0.26,0.66,2.2,3.0,0,0,0,0,0,0,0,9.4,2.0,64),
    states:["raw","steamed","cooked (curry)"],
    serving100g:"1 cup packed"
  },
  {
    id:"arbi", name:"Taro root (arbi), raw", hindi:"अरबी",
    aliases:["arbi","taro root","taro","kachalu","ghuiyan","eddoe","arvi"],
    category:"Sabzi",
    baseNutrients: n(0.55,0,0,43,33,0.23,4.5,2,22,0.05,0.9,0.33,591,84,0.09,0.02,0.6,2.9,0,0,0,0,0,0,0,1.5,2.3,112),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"4-5 arbi"
  },
  {
    id:"kathal", name:"Jackfruit, raw", hindi:"कटहल",
    aliases:["jackfruit","kathal","katahal","raw jackfruit","kacha kathal","panasa"],
    category:"Sabzi",
    baseNutrients: n(0.23,0,0,24,29,0.13,13.7,110,24,0.06,0.6,0.33,303,21,0.1,0.13,0.92,0.34,0,0,0,0,0,0,0,1.72,1.5,95),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 cup pieces"
  },
  {
    id:"pyaz", name:"Onions, raw", hindi:"प्याज",
    aliases:["onion","pyaaz","piaz","dungri","kanda","onion sabzi"],
    category:"Sabzi",
    baseNutrients: n(0.21,0,0,23,10,0.17,7.4,0,19,0.02,0.5,0.12,146,29,0.04,0.03,0.12,0.02,0,0,0,0,0,0,0,1.1,1.7,40),
    states:["raw","cooked (curry)"],
    serving100g:"1 medium pyaz"
  },
  {
    id:"lehsun", name:"Garlic, raw", hindi:"लहसुन",
    aliases:["garlic","lasan","lasun","garlic cloves","lehsun","lahsun"],
    category:"Sabzi",
    baseNutrients: n(1.7,0,0,181,25,1.16,31.2,0,3,0.07,14.2,1.24,401,153,0.2,0.11,0.7,0.08,0,0,0,0,0,0,0,6.36,2.1,149),
    states:["raw","cooked (curry)"],
    serving100g:"10-12 cloves"
  },
  {
    id:"lotus_stem", name:"Lotus root (kamal kakdi), raw", hindi:"कमल ककड़ी",
    aliases:["lotus stem","kamal kakdi","bhe","lotus root","nadru","kamal kand"],
    category:"Sabzi",
    baseNutrients: n(1.16,0,0,45,23,0.4,44.0,0,13,0.07,0.7,0.44,556,100,0.16,0.22,0.41,0.18,0,0,0,0,0,0,0,1.58,4.9,74),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"8-10 slices"
  },
  {
    id:"adrak", name:"Ginger root, raw", hindi:"अदरक",
    aliases:["ginger","adrak","ginger root","adarak","alla"],
    category:"Sabzi",
    baseNutrients: n(0.6,0,0,16,43,0.34,5,0,11,0,0.7,0.16,415,34,0.025,0.034,0.75,0.26,0,0.226,0.229,0,0,0.2,0,1.8,2.0,80),
    states:["raw","cooked (curry)"],
    serving100g:"1 inch tukda"
  },
  {
    id:"hari_dhania", name:"Coriander (cilantro) leaves, raw", hindi:"हरा धनिया",
    aliases:["coriander leaves","cilantro","dhania","hara dhania","kothimbir","kothamalli"],
    category:"Sabzi",
    baseNutrients: n(1.77,0,0,67,26,0.5,27,337,62,0.03,0.4,0.15,521,48,0.067,0.162,1.11,2.5,0,0.225,0.426,0,310,0.57,0,2.13,2.8,23),
    states:["raw","cooked (curry)"],
    serving100g:"1 katori kata hua"
  },
  {
    id:"pudina", name:"Mint (spearmint), fresh, raw", hindi:"पुदीना",
    aliases:["mint","pudina","mint leaves","pudhina","mentha"],
    category:"Sabzi",
    baseNutrients: n(5.08,0,0,199,80,1.11,31.8,212,114,0.07,0.9,0.13,569,73,0.08,0.27,1.71,0.5,0,0.329,1.118,0,104.7,0.34,0,3.75,8.0,70),
    states:["raw"],
    serving100g:"1 katori kata hua"
  },
  {
    id:"hari_mirch", name:"Peppers, hot chili, green, raw", hindi:"हरी मिर्च",
    aliases:["green chilli","green chili","hari mirch","mirchi","pachi mirapakayalu"],
    category:"Sabzi",
    baseNutrients: n(1.2,0,0,18,25,0.3,143.7,36,23,0,0.5,0.26,340,46,0.09,0.09,0.95,0.69,0,0.13,0.24,0,0,0.2,0,1.9,1.5,40),
    states:["raw","cooked (curry)"],
    serving100g:"4-5 mirch"
  },
  {
    id:"mooli", name:"Radishes, raw", hindi:"मूली",
    aliases:["radish","mooli","muli","mullangi","daikon"],
    category:"Sabzi",
    baseNutrients: n(0.34,0,0,25,10,0.28,14.8,0,25,0,0.6,0.07,233,20,0.012,0.039,0.25,0,0,0.05,0.069,0,1.3,0.16,0,0.68,1.6,16),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 medium mooli"
  },
  {
    id:"shalgam", name:"Turnips, raw", hindi:"शलगम",
    aliases:["turnip","shalgam","shaljam","salgam"],
    category:"Sabzi",
    baseNutrients: n(0.3,0,0,30,11,0.27,21,0,15,0,0.7,0.09,191,27,0.04,0.03,0.4,0.03,0,0.08,0.12,0,0.1,0.2,0,0.9,1.8,28),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 medium shalgam"
  },
  {
    id:"parwal", name:"Pointed gourd (parwal), raw", hindi:"परवल",
    aliases:["pointed gourd","parwal","parval","potol","kovakkai variant"],
    category:"Sabzi",
    baseNutrients: n(1.25,0,0,25,17,0.35,4.0,50,8,0,0.4,0.05,83,32,0.05,0.05,0.5,0.4,0,0.1,0.14,0,0,0.2,0,1.5,2.9,20),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"4-5 parwal"
  },
  {
    id:"cabbage", name:"Cabbage, raw", hindi:"पत्ता गोभी",
    aliases:["cabbage","patta gobhi","band gobhi","muttaikose"],
    category:"Sabzi",
    baseNutrients: n(0.47,0,0,40,12,0.18,36.6,5,43,0.02,0.3,0.12,170,26,0.06,0.04,0.23,0.15,0,0.02,0.16,0,76,0.21,0,1.28,2.5,25),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 katori kata hua"
  },
  {
    id:"spring_onion", name:"Onions, spring, raw", hindi:"हरा प्याज",
    aliases:["spring onion","hara pyaz","green onion","scallion"],
    category:"Sabzi",
    baseNutrients: n(1.48,0,0,72,20,0.39,18.8,50,64,0.01,0.6,0.06,276,37,0.06,0.08,0.51,0.55,0,0.08,0.16,0,207,0.14,0,1.83,2.6,32),
    states:["raw","cooked (curry)"],
    serving100g:"1 katori kata hua"
  },
  {
    id:"green_beans", name:"Beans, snap, green, raw", hindi:"फली (फ्रेंच बीन्स)",
    aliases:["green beans","french beans","phalli","snap beans","farasbi"],
    category:"Sabzi",
    baseNutrients: n(1.03,0,0,37,25,0.24,12.2,35,33,0.03,0.6,0.14,211,38,0.08,0.10,0.75,0.41,0,0.07,0.22,0,43,0.23,0,1.83,2.7,31),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 katori"
  },
  {
    id:"red_bell_pepper", name:"Peppers, sweet, red, raw", hindi:"लाल शिमला मिर्च",
    aliases:["red bell pepper","red capsicum","lal shimla mirch"],
    category:"Sabzi",
    baseNutrients: n(0.43,0,0,7,12,0.25,127.7,157,46,0.28,0.1,0.29,211,26,0.05,0.09,0.98,1.58,0,0.09,0.11,0,4.9,0.34,0,0.99,2.1,31),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 medium shimla mirch"
  },
  {
    id:"yellow_bell_pepper", name:"Peppers, sweet, yellow, raw", hindi:"पीली शिमला मिर्च",
    aliases:["yellow bell pepper","yellow capsicum","peeli shimla mirch"],
    category:"Sabzi",
    baseNutrients: n(0.46,0,0,11,12,0.17,183.5,18,26,0.06,0.1,0.25,212,24,0.02,0.03,0.99,0.66,0,0.06,0.11,0,7.4,0.11,0,1.0,0.9,27),
    states:["raw","boiled","steamed","cooked (curry)"],
    serving100g:"1 medium shimla mirch"
  },
  {
    id:"amaranth_leaves", name:"Amaranth leaves, raw", hindi:"चौलाई साग",
    aliases:["amaranth leaves","chaulai","chaulai saag","chauli bhaji"],
    category:"Sabzi",
    baseNutrients: n(2.32,0,0,215,55,0.9,43.3,146,85,0.06,0.9,0.19,611,50,0.03,0.16,0.66,1.13,0,0.19,0.9,0,1.14,0.4,0,2.46,2.1,23),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 katora kata hua"
  },
  {
    id:"dill_leaves", name:"Dill weed, fresh, raw", hindi:"सुआ भाजी",
    aliases:["dill leaves","suva bhaji","sowa saag","dill weed"],
    category:"Sabzi",
    baseNutrients: n(6.59,0,0,208,55,0.91,85,386,150,0.6,0.6,0.185,738,66,0.42,0.31,1.42,1.7,0,0.146,1.264,0,0,0.4,0,3.46,2.1,43),
    states:["raw","cooked (curry)"],
    serving100g:"1 katori kata hua"
  },
  {
    id:"cucumber", name:"Cucumber, with peel, raw", hindi:"खीरा",
    aliases:["cucumber","kakdi","kheera","vellarikka"],
    category:"Sabzi",
    baseNutrients: n(0.28,0,0,16,13,0.2,2.8,5,7,0.01,0.3,0.04,147,24,0.03,0.03,0.1,0.03,0,0.04,0.08,0,16.4,0.26,0,0.65,0.5,15),
    states:["raw"],
    serving100g:"1 medium kakdi"
  },
];

// ── FRUITS ────────────────────────────────────────────────────
const FRUITS: BaseFoodData[] = [
  {
    id:"aam", name:"Mangos, raw", hindi:"आम",
    aliases:["mango","amra","keri","aam","raw mango","kacha aam","paka aam","alphonso"],
    category:"Fruit",
    baseNutrients: n(0.16,0,0,11,10,0.09,36.4,54,43,0.06,0.6,0.12,168,14,0.06,0.06,0.67,0.9,0,0,0,0,0,0,0,0.82,1.6,60),
    states:["raw"],
    serving100g:"1 small mango ya ½ bada"
  },
  {
    id:"kela", name:"Bananas, raw", hindi:"केला",
    aliases:["banana","kella","plantain","kela","banaana"],
    category:"Fruit",
    baseNutrients: n(0.26,0,0,5,27,0.15,8.7,3,20,0.03,1.0,0.37,358,22,0.03,0.07,0.67,0.1,0,0,0,0,0,0,0,1.09,2.6,89),
    states:["raw"],
    serving100g:"1 medium kela"
  },
  {
    id:"seb", name:"Apples, raw, with skin", hindi:"सेब",
    aliases:["apple","saab","seb","appl"],
    category:"Fruit",
    baseNutrients: n(0.12,0,0,6,5,0.04,4.6,3,3,0.02,0.2,0.04,107,11,0.02,0.03,0.09,0.18,0,0,0,0,0,0,0,0.26,2.4,52),
    states:["raw"],
    serving100g:"1 medium seb"
  },
  {
    id:"amla", name:"Indian gooseberry (amla), raw", hindi:"आँवला",
    aliases:["amla","gooseberry","indian gooseberry","awla","nellikai","awala","aonla","vitamin c fruit"],
    category:"Fruit",
    baseNutrients: n(1.2,0,0,50,10,0.12,600,15,6,0.01,0.6,0.08,198,27,0.03,0.01,0.3,0.37,0,0,0,0,0,0,0,0.88,3.4,44),
    states:["raw"],
    serving100g:"4-5 amle (khatte hain — thode hi kaafi)"
  },
  {
    id:"anar", name:"Pomegranates, raw", hindi:"अनार",
    aliases:["pomegranate","annar","dalim","anaar","anar"],
    category:"Fruit",
    baseNutrients: n(0.3,0,0,10,12,0.35,10.2,0,38,0.07,0.5,0.08,236,36,0.07,0.05,0.29,0.6,0,0,0,0,0,0,0,1.67,4.0,83),
    states:["raw"],
    serving100g:"½ anar ke daane"
  },
  {
    id:"amrud", name:"Guavas, common, raw", hindi:"अमरूद",
    aliases:["guava","peru","jaamfal","amrood","peru"],
    category:"Fruit",
    baseNutrients: n(0.26,0,0,18,22,0.23,228,31,49,0.11,0.6,0.11,417,40,0.07,0.04,1.08,0.73,0,0,0,0,0,0,0,2.55,5.4,68),
    states:["raw"],
    serving100g:"1 medium amrud"
  },
  {
    id:"papaya", name:"Papayas, raw", hindi:"पपीता",
    aliases:["papaya","papita","papetas","papaya fruit","papeeta"],
    category:"Fruit",
    baseNutrients: n(0.25,0,0,20,21,0.08,60.9,47,37,0.06,0.6,0.04,182,10,0.02,0.03,0.34,0.3,0,0,0,0,0,0,0,0.47,1.7,43),
    states:["raw"],
    serving100g:"1 cup pieces"
  },
  {
    id:"santara", name:"Oranges, raw", hindi:"संतरा",
    aliases:["orange","naranga","santra","narangi","mosambi","malta","citrus orange"],
    category:"Fruit",
    baseNutrients: n(0.1,0,0,40,10,0.07,53.2,11,30,0.01,0.5,0.06,181,14,0.09,0.04,0.28,0.18,0,0,0,0,0,0,0,0.94,2.4,47),
    states:["raw"],
    serving100g:"1 medium santara"
  },
  {
    id:"nimbu", name:"Lemons, raw, without peel", hindi:"नींबू",
    aliases:["lemon","lime","neembu","limon","citrus","lemon juice","nimbu paani"],
    category:"Fruit",
    baseNutrients: n(0.6,0,0,26,8,0.06,53,0,11,0.03,0.4,0.08,138,16,0.04,0.02,0.1,0.15,0,0,0,0,0,0,0,1.1,2.8,29),
    states:["raw"],
    serving100g:"3-4 nimbu"
  },
  {
    id:"chikoo", name:"Sapodilla (chikoo), raw", hindi:"चीकू",
    aliases:["chikoo","sapota","sapodilla","sapoota","chiku","naseberry"],
    category:"Fruit",
    baseNutrients: n(0.8,0,0,21,12,0.1,14.7,3,14,0,0.6,0.03,193,12,0.06,0.02,0.2,0.56,0,0,0,0,0,0,0,0.44,5.3,83),
    states:["raw"],
    serving100g:"2-3 chikoo"
  },
  {
    id:"jamun", name:"Java plum (jamun), raw", hindi:"जामुन",
    aliases:["jamun","black plum","java plum","syzygium","naval pazham"],
    category:"Fruit",
    baseNutrients: n(0.19,0,0,19,15,0.19,14.3,3,23,0,0.2,0.04,79,17,0.01,0.01,0.26,0.32,0,0,0,0,0,0,0,0.72,0.6,60),
    states:["raw"],
    serving100g:"1 cup jamun"
  },
  {
    id:"anjeer_fresh", name:"Figs, raw", hindi:"अंजीर (ताज़ा)",
    aliases:["fresh fig","anjeer","fig fresh","aaanjeer"],
    category:"Fruit",
    baseNutrients: n(0.37,0,0,35,17,0.15,2.0,7,6,0.09,0.2,0.11,232,14,0.06,0.05,0.4,0.11,0,0,0,0,0,0,0,0.75,2.9,74),
    states:["raw"],
    serving100g:"2-3 fresh figs"
  },
  {
    id:"ananas", name:"Pineapple, raw, all varieties", hindi:"अनानास",
    aliases:["pineapple","ananas","pineapple fruit","anaanas"],
    category:"Fruit",
    baseNutrients: n(0.29,0,0,13,12,0.12,47.8,3,18,0.02,0.1,0.11,109,8,0.08,0.03,0.5,0.02,0,0,0,0,0,0,0,0.54,1.4,50),
    states:["raw"],
    serving100g:"1 cup pieces"
  },
  {
    id:"imli", name:"Tamarinds, raw", hindi:"इमली",
    aliases:["tamarind","imli","imly","tamarindo"],
    category:"Fruit",
    baseNutrients: n(2.8,0,0,74,92,0.1,3.5,2,14,0.1,1.3,0.07,628,113,0.43,0.15,1.94,0.1,0,0,0,0,0,0,0,2.8,5.1,239),
    states:["raw"],
    serving100g:"2 tbsp pulp"
  },
  {
    id:"angoor", name:"Grapes, raw", hindi:"अंगूर",
    aliases:["grapes","angoor","grape","draksha"],
    category:"Fruit",
    baseNutrients: n(0.36,0,0,10,7,0.07,3.2,3,2,0.01,0.1,0.086,191,20,0.07,0.07,0.19,0.19,0,0.13,0.07,0,14.6,0.05,0,0.72,0.9,69),
    states:["raw"],
    serving100g:"1 katori"
  },
  {
    id:"tarbooz", name:"Watermelon, raw", hindi:"तरबूज़",
    aliases:["watermelon","tarbooz","tarbuj","tarbuz"],
    category:"Fruit",
    baseNutrients: n(0.24,0,0,7,10,0.1,8.1,28,3,0,0.4,0.045,112,11,0.033,0.021,0.178,0.05,0,0.042,0.038,0,0.1,0.221,0,0.61,0.4,30),
    states:["raw"],
    serving100g:"1 katora pieces"
  },
  {
    id:"kharbooja", name:"Melons, muskmelon (cantaloupe), raw", hindi:"खरबूजा",
    aliases:["muskmelon","kharbooja","kharbuja","cantaloupe"],
    category:"Fruit",
    baseNutrients: n(0.21,0,0,9,12,0.18,36.7,169,21,0,0.4,0.105,267,15,0.041,0.019,0.734,0.05,0,0.041,0.041,0,0,0.105,0,0.84,0.9,34),
    states:["raw"],
    serving100g:"1 katora pieces"
  },
  {
    id:"litchi", name:"Lychees, raw", hindi:"लीची",
    aliases:["lychee","litchi","leechi","lichi"],
    category:"Fruit",
    baseNutrients: n(0.31,0,0,5,10,0.07,71.5,0,14,0,0.6,0.1,171,31,0.011,0.065,0.603,0.07,0,0.148,0.055,0,0,0.14,0,0.83,1.3,66),
    states:["raw"],
    serving100g:"8-10 litchi"
  },
  {
    id:"sitaphal", name:"Custard apple (sitaphal), raw", hindi:"सीताफल",
    aliases:["custard apple","sitaphal","sharifa","atis","seetha phal"],
    category:"Fruit",
    baseNutrients: n(0.71,0,0,24,18,0.1,19.2,0,14,0,0.3,0.221,247,21,0.09,0.1,0.5,0,0,0.07,0.113,0,0,0.226,0,1.7,2.4,94),
    states:["raw"],
    serving100g:"1 medium sitaphal"
  },
  {
    id:"kinnow", name:"Mandarin oranges (kinnow), raw", hindi:"किन्नू",
    aliases:["kinnow","kinno","kinu","mandarin"],
    category:"Fruit",
    baseNutrients: n(0.15,0,0,37,12,0.07,26.7,34,16,0.01,0.5,0.078,166,20,0.087,0.036,0.269,0.18,0,0.042,0.031,0,0,0.216,0,0.81,1.8,53),
    states:["raw"],
    serving100g:"1 medium kinnow"
  },
  {
    id:"coconut_fresh", name:"Nuts, coconut meat, raw (fresh)", hindi:"नारियल (ताज़ा)",
    aliases:["fresh coconut","nariyal","coconut meat","fresh nariyal"],
    category:"Fruit",
    baseNutrients: n(2.43,0,0,14,32,1.1,3.3,0,26,0,10.1,0.05,356,113,0.07,0.02,0.54,0.24,0,0.435,1.5,0,0.2,0.3,0,3.33,9.0,354),
    states:["raw"],
    serving100g:"1 katori kaddukas"
  },
  {
    id:"coconut_dried", name:"Nuts, coconut meat, dried (desiccated, khopra)", hindi:"सूखा नारियल (खोपरा)",
    aliases:["dried coconut","khopra","desiccated coconut","copra","sookha nariyal"],
    category:"Fruit",
    baseNutrients: n(3.32,0,0,26,90,2.01,1.1,0,26,0,15.3,0.09,543,206,0.06,0.02,0.66,0.44,0,0.66,2.83,0,0.5,0.44,0,6.88,16.3,660),
    states:["raw"],
    serving100g:"2 tbsp grated (20g)"
  },
  {
    id:"jackfruit_ripe", name:"Jackfruit, ripe, raw", hindi:"पका कटहल",
    aliases:["ripe jackfruit","pakka kathal","sweet jackfruit"],
    category:"Fruit",
    baseNutrients: n(0.23,0,0,24,29,0.13,13.7,5,24,0.06,0.6,0.33,448,21,0.105,0.055,0.92,0.34,0,0.19,0.19,0,0,0.24,0,1.72,1.5,95),
    states:["raw"],
    serving100g:"1 katori pieces"
  },
  {
    id:"strawberry", name:"Strawberries, raw", hindi:"स्ट्रॉबेरी",
    aliases:["strawberry","strawberries"],
    category:"Fruit",
    baseNutrients: n(0.41,0,0,16,13,0.14,58.8,1,24,0.07,0.4,0.047,153,24,0.024,0.022,0.386,0.29,0,0.048,0.386,0,2.2,0.125,0,0.67,2.0,32),
    states:["raw"],
    serving100g:"1 katori"
  },
  {
    id:"kiwi", name:"Kiwifruit, green, raw", hindi:"कीवी",
    aliases:["kiwi","kiwifruit"],
    category:"Fruit",
    baseNutrients: n(0.31,0,0,34,17,0.14,92.7,4,25,0.05,0.2,0.063,312,34,0.027,0.025,0.341,1.46,0,0.13,0.098,0,40.3,0.183,0,1.14,3.0,61),
    states:["raw"],
    serving100g:"1-2 kiwi"
  },
];

// ── NUTS ─────────────────────────────────────────────────────
const NUTS: BaseFoodData[] = [
  {
    id:"chilgoza", name:"Nuts, pine nuts, dried", hindi:"चिलगोज़ा",
    aliases:["pine nuts","chilgoza","pignoli","neja"],
    category:"Nuts",
    baseNutrients: n(5.53,0,0,16,251,6.45,0.8,1,34,9.3,0.7,0.09,597,575,0.36,0.23,4.39,9.3,0,1.32,8.8,0,53.9,0.31,0,13.7,3.7,673),
    states:["raw","dry roasted"],
    serving100g:"2 tbsp (28g = 1 serving)"
  },
  {
    id:"badam", name:"Nuts, almonds, raw", hindi:"बादाम",
    aliases:["almond","badaam","almonds","almond nut","soaked almond","badam"],
    category:"Nuts",
    baseNutrients: n(3.71,0,0,264,270,3.12,0,0,44,0.004,4.1,0.14,705,481,0.21,1.14,3.62,25.6,0,1.0,2.3,0,0,0.47,0,21.2,12.5,579),
    states:["raw","soaked overnight","soaked 4hr","dry roasted"],
    serving100g:"~23 badam (28g = 1 serving)"
  },
  {
    id:"akhrot", name:"Nuts, walnuts, English, raw", hindi:"अखरोट",
    aliases:["walnut","akhrot","walnuts","omega-3 nuts"],
    category:"Nuts",
    baseNutrients: n(2.91,0,0,98,158,3.09,1.3,1,98,9.08,4.9,0.54,441,346,0.34,0.15,1.13,0.7,0,1.6,3.4,0,2.7,0.6,0,15.2,6.7,654),
    states:["raw","dry roasted"],
    serving100g:"~7 akhrot (28g = 1 serving)"
  },
  {
    id:"kaju", name:"Nuts, cashew nuts, raw", hindi:"काजू",
    aliases:["cashew","cashewnut","keshoo","kaaju","kaju nut"],
    category:"Nuts",
    baseNutrients: n(6.68,0,0,37,292,5.78,0.5,0,25,0.14,11.7,0.42,660,593,0.42,0.06,1.06,0.9,0,2.2,1.66,0,34.1,0.86,0,18.2,3.3,553),
    states:["raw","dry roasted"],
    serving100g:"~18 kaju (28g = 1 serving)"
  },
  {
    id:"pista", name:"Nuts, pistachio nuts, raw", hindi:"पिस्ता",
    aliases:["pistachio","pista","pistachios","pista nut"],
    category:"Nuts",
    baseNutrients: n(3.92,0,0,105,121,2.2,5.6,26,51,0.26,7.4,1.7,1025,490,0.87,0.16,1.3,2.86,0,1.3,1.2,0,13.2,0.52,0,20.6,10.6,562),
    states:["raw","dry roasted"],
    serving100g:"~49 pista (28g = 1 serving)"
  },
  {
    id:"mungfali", name:"Peanuts, raw, all types", hindi:"मूंगफली",
    aliases:["peanut","groundnut","moongphali","singdana","mungphali","ground nut"],
    category:"Nuts",
    baseNutrients: n(4.58,0,0,92,168,3.27,0,0,240,0.003,7.2,0.35,705,376,0.64,0.14,12.07,8.33,0,0.65,1.9,0,0,1.77,34,25.8,8.5,567),
    states:["raw","dry roasted","boiled"],
    serving100g:"~30-35 mungfali (28g = 1 serving)"
  },
  {
    id:"til", name:"Seeds, sesame seeds, whole, raw", hindi:"तिल",
    aliases:["sesame","sesame seeds","gingelly","til","kala til","white til","safed til"],
    category:"Seeds",
    baseNutrients: n(14.6,0,0,975,351,7.75,0,0,97,0.38,34.4,0.79,468,629,1.23,0.25,4.52,0.25,0,4.08,2.46,0,0,0.05,0,17.7,11.8,573),
    states:["raw","dry roasted","soaked overnight"],
    serving100g:"2 tbsp (15g = 1 serving)"
  },
  {
    id:"alsi", name:"Seeds, flaxseed, raw", hindi:"अलसी",
    aliases:["flaxseed","linseed","flax seed","flax","alsi","alasi","omega3 seeds"],
    category:"Seeds",
    baseNutrients: n(5.73,0,0,255,392,4.34,0.6,0,87,22.8,25.4,0.47,813,642,1.64,0.16,3.08,0.47,0,1.22,2.5,0,4.3,0.57,0,18.3,27.3,534),
    states:["raw","dry roasted","soaked overnight"],
    serving100g:"2 tbsp (15g = 1 serving)"
  },
  {
    id:"kaddu_beej", name:"Seeds, pumpkin seeds, whole, raw", hindi:"कद्दू के बीज",
    aliases:["pumpkin seeds","pepitas","kaddu ke beej","kaddu beej","pumpkin seed"],
    category:"Seeds",
    baseNutrients: n(8.82,0,0,46,592,10.3,1.9,16,58,0.12,9.4,0.14,919,1233,0.27,0.32,4.99,0.35,0,1.4,4.5,0,7.3,0.85,0,30.2,6.0,559),
    states:["raw","dry roasted"],
    serving100g:"2 tbsp (28g = 1 serving)"
  },
  {
    id:"chia_seeds", name:"Seeds, chia seeds, dried", hindi:"चिया सीड्स",
    aliases:["chia seeds","chia","soaked chia","chia seed","chea seeds"],
    category:"Seeds",
    baseNutrients: n(7.72,0,0,631,335,4.58,1.6,54,49,17.8,55.9,0.51,407,860,0.62,0.17,8.83,0.5,0,0.9,2.72,0,0,0.09,0,16.5,34.4,486),
    states:["raw","soaked 4hr","soaked overnight"],
    serving100g:"2 tbsp (28g = 1 serving)"
  },
];

// ── DRY FRUITS ───────────────────────────────────────────────
const DRY_FRUITS: BaseFoodData[] = [
  {
    id:"kishmish", name:"Raisins, seedless", hindi:"किशमिश",
    aliases:["raisins","kishmish","dry grapes","dried grapes","sultana","kismis"],
    category:"Dry Fruits",
    baseNutrients: n(1.88,0,0,50,32,0.22,3.2,0,5,0.06,0.6,0.17,749,101,0.12,0.12,0.77,0.12,0,0.32,0.3,0,3.5,0.05,0,3.07,3.7,299),
    states:["raw","soaked overnight"],
    serving100g:"~60 kishmish (30g = 1 serving)"
  },
  {
    id:"anjeer_dry", name:"Figs, dried, uncooked", hindi:"सूखी अंजीर",
    aliases:["dried fig","anjeer","dry fig","sookhi anjeer","anjeer dry","fig"],
    category:"Dry Fruits",
    baseNutrients: n(2.03,0,0,162,68,0.55,1.2,0,9,0.17,0.6,0.11,680,67,0.08,0.08,0.62,0.35,0,0.29,0.34,0,15.6,0.43,0,3.3,9.8,249),
    states:["raw","soaked overnight"],
    serving100g:"2-3 sookhi anjeer"
  },
  {
    id:"khajoor", name:"Dates, dried", hindi:"खजूर",
    aliases:["dates","khajoor","date fruit","medjool dates","deglet","arabic dates"],
    category:"Dry Fruits",
    baseNutrients: n(0.9,0,0,64,54,0.44,0.4,7,15,0.06,3.0,0.19,696,62,0.05,0.07,1.61,0.1,0,0.36,0.3,0,2.7,0.8,0,1.81,6.7,277),
    states:["raw","soaked overnight"],
    serving100g:"5-6 khajoor"
  },
  {
    id:"khumani", name:"Apricots, dried, sulfured", hindi:"खुरमानी / सूखी खुबानी",
    aliases:["dried apricot","khumani","apricots","khubani","sukhi khubani","apricot dry"],
    category:"Dry Fruits",
    baseNutrients: n(2.66,0,0,55,32,0.39,1.0,180,10,0.06,2.2,0.14,1162,71,0.02,0.07,2.59,4.33,0,0.34,0.24,0,3.1,0.52,0,3.39,7.3,241),
    states:["raw","soaked overnight"],
    serving100g:"7-8 khumani"
  },
  {
    id:"prune", name:"Plums, dried (prunes), uncooked", hindi:"आलूबुखारा",
    aliases:["prune","dried plum","alubukhara","plum dry","sukha alubukhara"],
    category:"Dry Fruits",
    baseNutrients: n(0.93,0,0,43,41,0.44,0.6,39,4,0.07,0.3,0.21,732,69,0.05,0.18,1.88,0.43,0,0.34,0.3,0,59.5,0.42,0,2.18,7.1,240),
    states:["raw","soaked overnight"],
    serving100g:"4-5 alubukhara"
  },
  {
    id:"munakka", name:"Raisins, dark, seeded (Munakka)", hindi:"मुनक्का",
    aliases:["munakka","large raisins","black raisins","kali kishmish","munaka"],
    category:"Dry Fruits",
    baseNutrients: n(2.0,0,0,45,32,0.25,3.5,0,5,0.07,0.6,0.17,750,100,0.12,0.12,0.8,0.15,0,0.3,0.3,0,3.5,0.05,0,2.5,4.0,302),
    states:["raw","soaked overnight"],
    serving100g:"~15 munakka"
  },
];

// ── GRAINS ───────────────────────────────────────────────────
const GRAINS: BaseFoodData[] = [
  {
    id:"bajra_grain", name:"Millet, pearl (bajra), raw", hindi:"बाजरा",
    aliases:["bajra","pearl millet","bajre","bajra grain","millet","bajra roti ingredient"],
    category:"Grain",
    baseNutrients: n(8.0,0,0,42,114,2.76,0,5,40,0.11,2.7,0.38,307,296,0.33,0.25,2.3,0.12,0,0,0,0,0,0,0,11.6,1.2,361),
    states:["raw","cooked (curry)"],
    serving100g:"1 katori pakka"
  },
  {
    id:"jowar_grain", name:"Sorghum grain (jowar), raw", hindi:"ज्वार",
    aliases:["jowar","sorghum","jowar grain","jwaar","sholam"],
    category:"Grain",
    baseNutrients: n(4.1,0,0,25,165,1.68,0,0,0,0.05,0,0.4,350,289,0.24,0.14,3.6,0.52,0,0,0,0,0,0,0,10.4,6.3,349),
    states:["raw","cooked (curry)"],
    serving100g:"1 katori pakka"
  },
  {
    id:"ragi_grain", name:"Millet, finger (ragi), raw", hindi:"रागी",
    aliases:["ragi","nachni","mandua","finger millet","ragi grain","nachni grain"],
    category:"Grain",
    baseNutrients: n(3.9,0,0,344,137,2.53,0,26,18,0.09,0,0.11,408,283,0.42,0.19,1.1,0.05,0,0,0,0,0,0,0,7.3,3.6,328),
    states:["raw","cooked (curry)"],
    serving100g:"1 katori pakka"
  },
  {
    id:"oats_raw", name:"Oats, raw", hindi:"जई / ओट्स",
    aliases:["oats","oatmeal","jai","oate","rolled oats","quick oats","old fashioned oats"],
    category:"Grain",
    baseNutrients: n(4.72,0,0,54,177,3.97,0,0,56,0.11,28.9,0.12,429,523,0.76,0.14,0.96,0.42,0,0,0,0,0,0,0,16.9,10.6,389),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"½ cup raw"
  },
  {
    id:"dalia", name:"Wheat, cracked (dalia), raw", hindi:"दलिया",
    aliases:["dalia","daliya","broken wheat","cracked wheat","lapsi","gehun dalia","wheat porridge"],
    category:"Grain",
    baseNutrients: n(3.9,0,0,34,137,2.6,0,0,36,0.08,35.6,0.3,405,288,0.4,0.16,4.3,0.11,0,0,0,0,0,0,0,12.0,10.7,342),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 katori pakka"
  },
  {
    id:"sabudana", name:"Tapioca pearls (sabudana), dry", hindi:"साबूदाना",
    aliases:["sabudana","sago","sabudaana","tapioca pearls","sabudhana","vrat food"],
    category:"Grain",
    baseNutrients: n(0.31,0,0,8,1,0.09,0,0,0,0,0,0,11,3,0,0,0,0,0,0,0,0,0,0,0,0.2,0.1,352),
    states:["raw","soaked 4hr","boiled"],
    serving100g:"¼ cup raw = 1 serving"
  },
  {
    id:"chawal", name:"Rice, white, raw", hindi:"चावल",
    aliases:["rice","chaawal","white rice","raw rice","chaval","bhaat ingredient"],
    category:"Grain",
    baseNutrients: n(0.8,0,0,10,25,1.2,0,0,8,0,15,0.16,115,140,0.07,0.05,1.6,0.11,0,0.2,1.1,0,0,0.6,0,6.8,0.6,365),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 katori pakka bhaat"
  },
  {
    id:"gehu_atta", name:"Wheat flour, whole-grain, raw", hindi:"गेहूं का आटा",
    aliases:["atta","wheat flour","gehu","gehun","whole wheat flour","roti flour","chapati atta"],
    category:"Grain",
    baseNutrients: n(4.9,0,0,48,138,2.7,0,0,30,0.03,70,0.3,340,355,0.45,0.17,5.0,1.0,0,0.4,3.0,0,0,0.9,0,12.0,11.5,341),
    states:["raw","roasted"],
    serving100g:"2 roti (~40g atta)"
  },
  {
    id:"suji", name:"Wheat, semolina (suji), raw", hindi:"सूजी",
    aliases:["suji","rava","semolina","sooji","ravva","upma ingredient"],
    category:"Grain",
    baseNutrients: n(1.2,0,0,17,47,0.9,0,0,13,0,20,0.1,186,136,0.1,0.08,1.5,0.1,0,0.2,0.6,0,0,0.5,0,10.4,2.2,360),
    states:["raw","boiled","roasted"],
    serving100g:"1 katori pakka upma"
  },
  {
    id:"poha", name:"Rice, flattened (poha), raw", hindi:"पोहा",
    aliases:["poha","flattened rice","beaten rice","chivda base","avalakki","pauwa"],
    category:"Grain",
    baseNutrients: n(20,0,0,9,35,1.0,0,0,10,0,15,0.1,115,140,0.06,0.03,1.2,0.05,0,0.15,1.0,0,0,0.3,0,6.6,0.9,356),
    states:["raw","steamed","cooked (curry)"],
    serving100g:"1 katori pakka poha"
  },
  {
    id:"jau", name:"Barley, hulled, raw", hindi:"जौ",
    aliases:["barley","jau","jav","jaun","hulled barley"],
    category:"Grain",
    baseNutrients: n(3.6,0,0,33,133,2.13,0,0,23,0.03,37,0.26,452,264,0.19,0.11,4.6,0.02,0,0.42,1.9,0,0,0.28,0,12.5,17.3,354),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 katori pakka"
  },
  {
    id:"makka", name:"Corn, yellow, raw", hindi:"मक्का",
    aliases:["maize","corn","makka","makki","corn grain","bhutta dried","corn kernel"],
    category:"Grain",
    baseNutrients: n(2.7,0,0,10,127,2.2,0,11,19,0.02,15.5,0.62,287,210,0.39,0.2,3.6,0.5,0,0.31,0.5,0,0,0.42,0,9.4,7.3,365),
    states:["raw","boiled","roasted","cooked (curry)"],
    serving100g:"1 katori pakka / 1 bhutta"
  },
  {
    id:"brown_rice", name:"Rice, brown, raw", hindi:"ब्राउन चावल",
    aliases:["brown rice","unpolished rice","brown chawal"],
    category:"Grain",
    baseNutrients: n(1.47,0,0,23,143,2.02,0,0,20,0,23.4,0.51,268,333,0.401,0.093,5.09,1.2,0,0.277,3.74,0,0,1.5,0,7.9,3.5,370),
    states:["raw","boiled","cooked (curry)"],
    serving100g:"1 katori pakka"
  },
  {
    id:"maida", name:"Wheat flour, white, all-purpose, raw", hindi:"मैदा",
    aliases:["maida","refined flour","all purpose flour","white flour","refined atta"],
    category:"Grain",
    baseNutrients: n(1.3,0,0,20,22,0.7,0,0,30,0,0,0,107,108,0.1,0.04,1.25,0,0,0.15,0.68,0,0,0,0,10,2.7,364),
    states:["raw","roasted"],
    serving100g:"2 poori/paratha (~40g maida)"
  },
];

// ── Generate FoodItem entries for all states ──────────────────
function generateItems(base: BaseFoodData): FoodItem[] {
  return base.states.map((state) => {
    const mult = STATE_MULT[state] ?? STATE_MULT["raw"];
    const bn = base.baseNutrients;
    const keys = ["iron","vitamin_b12","vitamin_d","calcium","magnesium","zinc","vitamin_c",
                  "vitamin_a","folate","omega3","selenium","vitamin_b6","potassium","phosphorus",
                  "vitamin_b1","vitamin_b2","vitamin_b3","vitamin_e",
                  "iodine","copper","manganese","chromium","vitamin_k","vitamin_b5","vitamin_b7"];
    const scaled: N = {};
    keys.forEach((k, i) => {
      const v = (bn[k] ?? 0) * (mult[i] ?? 1);
      if (v > 0) scaled[k] = parseFloat(v.toFixed(3));
    });
    // protein/fiber/energy — scaled by their own retention factors (indices 25-27)
    const macroKeys: [string, number][] = [["protein", 25], ["fiber", 26], ["energy", 27]];
    macroKeys.forEach(([k, i]) => {
      const v = (bn[k] ?? 0) * (mult[i] ?? 1);
      if (v > 0) scaled[k] = parseFloat(v.toFixed(3));
    });
    // weight change for cooked foods (e.g. dal absorbs water when boiled) — dilutes
    // every per-100g value (micronutrients + macros) since it's now per 100g of the
    // heavier, water-absorbed cooked food rather than 100g of the original dry/raw food.
    const wtFactor = mult[28] ?? 1;
    if (wtFactor > 1.1) {
      Object.keys(scaled).forEach((k) => { scaled[k] = parseFloat(((scaled[k] ?? 0) / wtFactor).toFixed(3)); });
    }

    const isRaw = state === "raw";
    const stateSuffix = isRaw ? "" : ` (${state})`;
    const stateLabel = isRaw ? "" : state;

    return {
      id: `${base.id}_${state.replace(/ /g,"_")}`,
      baseId: base.id,
      name: `${base.name}${stateSuffix}`,
      hindi: base.hindi,
      category: base.category,
      serving: base.serving100g,
      state: stateLabel || undefined,
      nutrients: scaled,
    } as FoodItem & { state?: string; baseId?: string };
  });
}

// Export the full comprehensive DB
// ── DAIRY ────────────────────────────────────────────────────
const DAIRY: BaseFoodData[] = [
  {
    id:"dahi", name:"Yogurt, plain, whole milk (dahi)", hindi:"दही",
    aliases:["dahi","curd","yogurt","yoghurt","plain curd","fresh curd"],
    category:"Dairy",
    baseNutrients: n(0.1,0.75,0.03,149,12,0.59,0.5,27,7,0,3.4,0.03,155,106,0.03,0.14,0.1,0.02,0,0.01,0.004,0,0.2,0.39,0,3.5,0,61),
    states:["raw"],
    serving100g:"1 katori"
  },
  {
    id:"doodh", name:"Milk, whole, cow, raw", hindi:"दूध",
    aliases:["milk","doodh","cow milk","whole milk","doodhh"],
    category:"Dairy",
    baseNutrients: n(0.03,0.45,0.05,113,10,0.38,0,28,5,0,2.1,0.04,132,84,0.04,0.15,0.08,0.07,0,0.01,0.004,0,0.3,0.31,0,3.2,0,61),
    states:["raw"],
    serving100g:"1 glass (240ml)"
  },
  {
    id:"paneer", name:"Cheese, paneer (Indian cottage cheese), raw", hindi:"पनीर",
    aliases:["paneer","cottage cheese","indian cheese","panir"],
    category:"Dairy",
    baseNutrients: n(0.2,0.5,0,208,9,1.5,0,180,15,0,4,0.02,95,300,0.02,0.28,0.1,0.2,0,0.02,0.01,0,0.5,0.34,0,18.3,0,265),
    states:["raw"],
    serving100g:"100g cube"
  },
  {
    id:"toned_milk", name:"Milk, toned, cow, raw", hindi:"टोन्ड दूध",
    aliases:["toned milk","standardised milk"],
    category:"Dairy",
    baseNutrients: n(0.02,0.35,0.03,120,10,0.35,0,20,5,0,1.8,0.03,140,90,0.03,0.14,0.07,0.03,0,0.01,0.003,0,0.2,0.28,0,3.1,0,58),
    states:["raw"],
    serving100g:"1 glass (240ml)"
  },
  {
    id:"skimmed_milk", name:"Milk, skim, cow, raw", hindi:"स्किम्ड दूध",
    aliases:["skimmed milk","skim milk","fat free milk"],
    category:"Dairy",
    baseNutrients: n(0.03,0.4,0,125,11,0.4,0,2,5,0,1.9,0.04,150,95,0.04,0.18,0.09,0.01,0,0.01,0.004,0,0.1,0.32,0,3.4,0,35),
    states:["raw"],
    serving100g:"1 glass (240ml)"
  },
  {
    id:"chaas", name:"Buttermilk, cultured, low-fat (chaas)", hindi:"छाछ",
    aliases:["buttermilk","chaas","chach","spiced buttermilk"],
    category:"Dairy",
    baseNutrients: n(0.05,0.2,0,80,6,0.3,0,4,3,0,0.9,0.02,80,55,0.02,0.08,0.05,0.01,0,0.005,0.002,0,0.1,0.15,0,1.5,0,25),
    states:["raw"],
    serving100g:"1 glass (240ml)"
  },
  {
    id:"khoya", name:"Milk, dried whole (khoya/mawa)", hindi:"खोया",
    aliases:["khoya","mawa","dried milk solids","milk khoya"],
    category:"Dairy",
    baseNutrients: n(0.5,1.0,0,650,30,1.6,0,120,20,0,5,0.05,350,350,0.06,0.4,0.2,0.4,0,0.05,0.02,0,0.8,0.6,0,14.6,0,421),
    states:["raw"],
    serving100g:"1 katori"
  },
  {
    id:"malai", name:"Cream, fresh (malai)", hindi:"मलाई",
    aliases:["cream","malai","fresh cream","milk cream"],
    category:"Dairy",
    baseNutrients: n(0.03,0.2,0,65,5,0.2,0,350,3,0,0.9,0.02,70,50,0.02,0.09,0.04,0.3,0,0.01,0.003,0,0.3,0.16,0,2.1,0,330),
    states:["raw"],
    serving100g:"2 tbsp (30g)"
  },
];

// ── OILS & FATS ──────────────────────────────────────────────
const OILS: BaseFoodData[] = [
  {
    id:"ghee", name:"Butter, clarified (ghee)", hindi:"घी",
    aliases:["ghee","clarified butter","desi ghee","cow ghee"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,805,0,0,0,0,0,0,0,0,0,2.8,0,0,0,0,7,0,0,0,0,900),
    states:["raw"],
    serving100g:"1 tbsp (15g = 1 serving)"
  },
  {
    id:"tel", name:"Oil, mustard", hindi:"तेल",
    aliases:["oil","tel","mustard oil","cooking oil","sarson tel","vegetable oil"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,9.1,0,0,0,0,0,0,0,13.6,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"groundnut_oil", name:"Oil, peanut (groundnut)", hindi:"मूंगफली का तेल",
    aliases:["groundnut oil","peanut oil","mungfali tel","mungfali ka tel"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,15.7,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"sunflower_oil", name:"Oil, sunflower", hindi:"सूरजमुखी तेल",
    aliases:["sunflower oil","surajmukhi tel"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,41.1,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"coconut_oil", name:"Oil, coconut", hindi:"नारियल तेल",
    aliases:["coconut oil","nariyal tel"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,0,0,0,0,0,0,0,0,862),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"soyabean_oil", name:"Oil, soybean", hindi:"सोयाबीन तेल",
    aliases:["soyabean oil","soybean oil","soya tel"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,6.8,0,0,0,0,0,0,0,8.18,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"sesame_oil", name:"Oil, sesame (til)", hindi:"तिल का तेल",
    aliases:["sesame oil","til oil","til ka tel","gingelly oil"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0.3,0,0,0,0,0,0,0,1.4,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"olive_oil", name:"Oil, olive", hindi:"जैतून का तेल",
    aliases:["olive oil","jaitun tel"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,14.4,0,0,0,0,60.2,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"rice_bran_oil", name:"Oil, rice bran", hindi:"राइस ब्रान तेल",
    aliases:["rice bran oil"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,32.3,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"palm_oil", name:"Oil, palm", hindi:"पाम तेल",
    aliases:["palm oil"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,15.9,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"corn_oil", name:"Oil, corn", hindi:"मक्के का तेल",
    aliases:["corn oil","makke ka tel"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17.2,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"canola_oil", name:"Oil, canola", hindi:"कैनोला तेल",
    aliases:["canola oil","rapeseed oil"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,9.1,0,0,0,0,0,0,0,17.5,0,0,0,0,71.3,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"vanaspati", name:"Oil, vanaspati (hydrogenated vegetable)", hindi:"वनस्पति",
    aliases:["vanaspati","dalda","hydrogenated oil","vegetable shortening"],
    category:"Oil",
    baseNutrients: n(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.0,0,0,0,0,0,0,0,0,0,884),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
  {
    id:"makhan", name:"Butter, without salt", hindi:"मक्खन",
    aliases:["butter","makhan","white butter","unsalted butter"],
    category:"Oil",
    baseNutrients: n(0,0,0,24,0,0,0,684,0,0,0,0,0,0,0,0,0,2.32,0,0,0,0,7,0,0,0.85,0,717),
    states:["raw"],
    serving100g:"1 tbsp (14g = 1 serving)"
  },
];

// ── MEAT, POULTRY, FISH & EGG ────────────────────────────────
const MEAT_EGG: BaseFoodData[] = [
  {
    id:"egg", name:"Egg, whole, raw, fresh", hindi:"अंडा",
    aliases:["egg","anda","whole egg","chicken egg"],
    category:"Protein",
    baseNutrients: n(1.75,0.89,2.0,56,12,1.29,0,160,47,0.1,30.7,0.17,138,198,0.04,0.457,0.075,1.05,0,0.072,0.028,0,0.3,1.53,10,12.6,0,143),
    states:["raw"],
    serving100g:"2 eggs (100g)"
  },
  {
    id:"chicken", name:"Chicken, breast, meat only, raw", hindi:"चिकन",
    aliases:["chicken","murgi","poultry","chicken breast"],
    category:"Protein",
    baseNutrients: n(0.7,0.3,0.1,5,25,0.9,0,0,4,0.02,24,0.6,256,210,0.07,0.1,10,0.3,0,0.04,0.018,0,2,0.9,0,23,0,120),
    states:["raw"],
    serving100g:"100g piece"
  },
  {
    id:"fish", name:"Fish, rohu, raw", hindi:"मछली (रोहू)",
    aliases:["fish","machli","rohu","freshwater fish","seafood"],
    category:"Protein",
    baseNutrients: n(0.5,2.9,2.0,30,25,1.2,0,0,10,0.3,12.6,0.2,300,190,0.05,0.07,2.5,0.5,0,0.03,0.02,0,0.1,0.6,0,16.6,0,97),
    states:["raw"],
    serving100g:"100g fillet"
  },
  {
    id:"mutton", name:"Goat, raw (Mutton)", hindi:"मटन",
    aliases:["mutton","goat meat","lamb","gosht"],
    category:"Protein",
    baseNutrients: n(3.2,1.66,0,11,22,4.2,0,0,8,0.02,6.2,0.3,385,205,0.1,0.3,5.6,0.2,0,0.16,0.03,0,0,0.6,0,21,0,143),
    states:["raw"],
    serving100g:"100g piece"
  },
];

// ── SWEETENERS ───────────────────────────────────────────────
const SWEETENERS: BaseFoodData[] = [
  {
    id:"jaggery", name:"Sugars, jaggery (gur)", hindi:"गुड़",
    aliases:["jaggery","gur","gud","cane jaggery"],
    category:"Sweetener",
    baseNutrients: n(11,0,0,40,70,0.2,0,0,0,0,0,0,1050,22,0.01,0,0,0,0,0.35,0.2,0,0,0,0,0.4,0,383),
    states:["raw"],
    serving100g:"1 small piece (20g)"
  },
  {
    id:"sugar", name:"Sugars, granulated, white", hindi:"चीनी",
    aliases:["sugar","white sugar","chini","cane sugar","granulated sugar"],
    category:"Sweetener",
    baseNutrients: n(0.01,0,0,1,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,387),
    states:["raw"],
    serving100g:"1 tbsp (12g)"
  },
  {
    id:"honey", name:"Honey", hindi:"शहद",
    aliases:["honey","shahad","raw honey"],
    category:"Sweetener",
    baseNutrients: n(0.42,0,0,6,2,0.22,0.5,0,2,0,0.8,0.02,52,4,0,0.04,0.12,0,0,0.036,0.08,0,0,0.07,0,0.3,0.2,304),
    states:["raw"],
    serving100g:"1 tbsp (21g)"
  },
];

export const COMPREHENSIVE_FOOD_DB: FoodItem[] = [
  ...DALS.flatMap(generateItems),
  ...VEGETABLES.flatMap(generateItems),
  ...FRUITS.flatMap(generateItems),
  ...NUTS.flatMap(generateItems),
  ...DRY_FRUITS.flatMap(generateItems),
  ...GRAINS.flatMap(generateItems),
  ...DAIRY.flatMap(generateItems),
  ...OILS.flatMap(generateItems),
  ...MEAT_EGG.flatMap(generateItems),
  ...SWEETENERS.flatMap(generateItems),
];

// Export raw base foods for search (deduplicated by base name)
export const COMPREHENSIVE_FOOD_DB_RAW: FoodItem[] = [
  ...DALS.map(b => generateItems(b)[0]),
  ...VEGETABLES.map(b => generateItems(b)[0]),
  ...FRUITS.map(b => generateItems(b)[0]),
  ...NUTS.map(b => generateItems(b)[0]),
  ...DRY_FRUITS.map(b => generateItems(b)[0]),
  ...GRAINS.map(b => generateItems(b)[0]),
  ...DAIRY.map(b => generateItems(b)[0]),
  ...OILS.map(b => generateItems(b)[0]),
  ...MEAT_EGG.map(b => generateItems(b)[0]),
  ...SWEETENERS.map(b => generateItems(b)[0]),
];

// All aliases for search
export const ALL_FOOD_ALIASES: Record<string, string> = {};
[...DALS, ...VEGETABLES, ...FRUITS, ...NUTS, ...DRY_FRUITS, ...GRAINS, ...DAIRY, ...OILS, ...MEAT_EGG, ...SWEETENERS].forEach((b) => {
  b.aliases.forEach((alias) => { ALL_FOOD_ALIASES[alias.toLowerCase()] = b.id; });
});
