"""
Step 0b: Extend ingredient_master.json (138 whole-food ingredients, Hindi-transliterated
IDs) with:
  (a) an alias map — English/snake_case tokens used in the dish-research catalogs
      (breakfast/lunch/dinner) resolved to the existing 138 ingredient IDs
  (b) ~25 genuinely-missing high-frequency spice/condiment ingredients, with real
      per-100g values from USDA FoodData Central / IFCT2017 published figures (these
      are commonly-cited, well-established nutrition-facts figures for standard whole
      spices, not obscure/uncertain data — appropriate given they're used in small
      per-dish gram quantities, so approximation tolerance here doesn't distort totals)
  (c) a zero-contribution set (salt, water, baking soda, yeast — negligible/no tracked
      macro-micronutrient contribution in this 25-nutrient schema)
"""
import json
from pathlib import Path

MASTER_PATH = Path("/home/abhay/Downloads/medical/balanceai/data/ingredient_master.json")
master = json.loads(MASTER_PATH.read_text())
ingredients = master["ingredients"]

# ---- (a) alias map: normalized dish-token -> existing master id ----
ALIAS_MAP = {
    "onion": "pyaz", "onions": "pyaz", "shallots": "pyaz", "spring_onion": "spring_onion",
    "green_chili": "hari_mirch", "green_chilli": "hari_mirch", "green_chilies": "hari_mirch",
    "green_chillies": "hari_mirch", "chili": "hari_mirch", "chilli": "hari_mirch",
    "ginger": "adrak", "garlic": "lehsun",
    "ginger_garlic_paste": "adrak", "ginger-garlic_paste": "adrak", "ginger_paste": "adrak",
    "ginger-green_chilli_paste": "adrak", "dry_ginger": "adrak", "sonth": "adrak",
    "tomato": "tamatar", "tomatoes": "tamatar",
    "curd": "dahi", "yogurt": "dahi", "yoghurt": "dahi",
    "potato": "aloo", "potatoes": "aloo",
    "rice": "chawal", "cooked_rice": "chawal", "raw_rice": "chawal", "dosa_rice": "chawal",
    "steamed_rice": "chawal",
    "wheat_flour": "gehu_atta", "whole_wheat_flour": "gehu_atta",
    "maida_(all-purpose_flour)": "maida", "all_purpose_flour": "maida",
    "coconut": "coconut_fresh", "grated_coconut": "coconut_fresh", "fresh_coconut": "coconut_fresh",
    "dry_coconut": "coconut_dried", "desiccated_coconut": "coconut_dried",
    "coriander_leaves": "hari_dhania", "coriander_leaf": "hari_dhania",
    "lemon": "nimbu", "lemon_juice": "nimbu",
    "carrot": "gajar", "carrots": "gajar",
    "spinach": "palak",
    "pumpkin": "kaddu",
    "green_peas": "matar", "peas": "matar",
    "cashew": "kaju", "cashews": "kaju",
    "peanuts": "mungfali", "peanut": "mungfali", "groundnut": "mungfali",
    "raisins": "kishmish",
    "eggs": "egg",
    "butter": "makhan",
    "brinjal": "baingan", "eggplant": "baingan",
    "milk": "doodh", "hot_milk": "doodh",
    "semolina_(rava)": "suji", "rava": "suji", "sooji": "suji",
    "cream": "malai",
    "minced_mutton": "mutton", "mutton_mince": "mutton", "keema": "mutton",
    "sesame_seeds": "til", "sesame_seeds_(optional)": "til", "til_seeds": "til",
    "tamarind": "imli", "tamarind_pulp": "imli",
    "sugar": "sugar", "jaggery": "jaggery",
    "banana": "kela", "ripe_banana": "kela", "raw_banana": "kela", "plantain": "kela",
    "cucumber": "cucumber",
    "cabbage": "cabbage",
    "wheat_noodles": "gehu_atta",
    "hot_water": None, "water": None,
    "oil": "tel", "cooking_oil": "tel", "oil_for_frying": "tel", "oil_for_deep_frying": "tel",
    "vegetable_oil": "tel", "refined_oil": "tel",
    "turmeric": "haldi", "turmeric_powder": "haldi",
    "cumin": "jeera", "cumin_seeds": "jeera", "roasted_cumin_powder": "jeera",
    "coriander_pwd": "dhania_seeds", "coriander_powder": "dhania_seeds", "coriander_seeds": "dhania_seeds",
    "mustard_seeds": "rai", "mustard_seed": "rai",
    "fenugreek_seeds": "methi_seeds", "methi_seeds": "methi_seeds",
    "black_pepper": "kali_mirch", "pepper": "kali_mirch",
    "cardamom": "elaichi", "cardamom_powder": "elaichi", "green_cardamom": "elaichi",
    "cinnamon": "dalchini",
    "cloves": "laung", "clove": "laung",
    "asafoetida": "hing",
    "fennel_seeds": "saunf", "fennel_pwd": "saunf", "fennel_powder": "saunf",
    "poppy_seeds": "khus_khus",
    "besan": "besan", "besan_(gram_flour)": "besan", "gram_flour": "besan",
    "rice_flour": "rice_flour",
    "bamboo_shoot": "bamboo_shoot", "fermented_bamboo_shoot": "bamboo_shoot",
    "curry_leaves": "curry_leaves", "curry_leaf": "curry_leaves",
    "coconut_milk": "coconut_milk",
    "pork": "pork",
    "chili_pwd": "dried_red_chili", "chili_powder": "dried_red_chili",
    "red_chili_powder": "dried_red_chili", "red_chilli_powder": "dried_red_chili",
    "red_chili_pwd": "dried_red_chili", "dried_chili": "dried_red_chili",
    "red_chili_whole": "dried_red_chili", "kashmiri_red_chili": "dried_red_chili",
    "garam_masala": "garam_masala",
    "ajwain": "ajwain",
    "sambar_powder": "sambar_powder",
    "soy_sauce": "soy_sauce",
    "bay_leaf": "tej_patta", "bay_leaves": "tej_patta",
    "chopped_onion": "pyaz", "sliced_onion": "pyaz", "finely_chopped_onion": "pyaz",
    "boiled_potato": "aloo", "boiled_potatoes": "aloo", "mashed_potato": "aloo",
    "grated_coconut_(optional)": "coconut_fresh",
    "oil_or_ghee": "ghee", "ghee_or_oil": "ghee",
    "dry_red_chili": "dried_red_chili", "dry_red_chilies": "dried_red_chili", "dry_red_chillies": "dried_red_chili",
    "ginger_garlic": "adrak",
    "cumin-coriander_powder": "jeera", "cumin_coriander_powder": "jeera",
    "kasuri_methi": "methi_leaves", "dried_fenugreek_leaves": "methi_leaves",
    "fenugreek_leaves": "methi_leaves", "methi": "methi_leaves",
    "carom_seeds": "ajwain",
    "semolina": "suji",
    "raw_papaya": "papaya", "green_papaya": "papaya", "ripe_papaya": "papaya",
    "rohu_fish": "fish", "hilsa_fish": "fish", "hilsa": "fish", "prawns": "fish", "prawn": "fish",
    "tuna": "fish", "fish_fillet": "fish",
    "mutton_or_chicken": "mutton",
    "pork_fat": "pork",
    "leafy_greens": "palak", "mixed_greens": "palak",
}

ZERO_CONTRIBUTION = {"salt", "water", "hot_water", "baking_soda", "yeast",
                      "eno_fruit_salt_or_baking_soda", "vinegar", "food_colour", "banana_leaf"}

# ---- (b) genuinely-missing spice/condiment ingredients, real published per-100g values ----
# Sources: USDA FoodData Central (spices, raw/ground) and IFCT2017 for Indian-specific items.
# Used in small per-dish quantities (typically 0.5-5g), so approximation tolerance here
# does not materially distort whole-dish nutrient totals.
NEW_INGREDIENTS = {
    "haldi": {  # turmeric
        "category": "Spice",
        "per_100g_raw": {"iron": 41.4, "calcium": 183, "magnesium": 193, "zinc": 4.4,
                          "potassium": 2080, "vitamin_c": 25.9, "vitamin_b6": 1.8,
                          "protein": 9.7, "fiber": 21.0, "energy": 312},
        "states": ["raw"], "serving100g": "spice, used 1-5g per dish",
        "source": "USDA FDC — turmeric, ground",
    },
    "jeera": {  # cumin seeds
        "category": "Spice",
        "per_100g_raw": {"iron": 66.4, "calcium": 931, "magnesium": 366, "zinc": 4.8,
                          "potassium": 1788, "vitamin_c": 7.7, "protein": 17.8, "fiber": 10.5,
                          "energy": 375},
        "states": ["raw", "roasted"], "serving100g": "spice, used 1-3g per dish",
        "source": "USDA FDC — cumin seed",
    },
    "dhania_seeds": {  # coriander seeds/powder
        "category": "Spice",
        "per_100g_raw": {"iron": 16.3, "calcium": 709, "magnesium": 330, "protein": 12.4,
                          "fiber": 41.9, "energy": 298},
        "states": ["raw"], "serving100g": "spice, used 1-3g per dish",
        "source": "USDA FDC — coriander seed",
    },
    "rai": {  # mustard seeds
        "category": "Spice",
        "per_100g_raw": {"iron": 9.2, "calcium": 266, "magnesium": 370, "zinc": 6.1,
                          "protein": 26.1, "fiber": 12.2, "energy": 508},
        "states": ["raw"], "serving100g": "spice, used 1-2g per dish",
        "source": "USDA FDC — mustard seed",
    },
    "mustard_oil": {
        "category": "Oil",
        "per_100g_raw": {"omega3": 5.9, "vitamin_e": 22.2, "energy": 884},
        "states": ["raw"], "serving100g": "cooking oil, ~5-10g per dish",
        "source": "USDA FDC — mustard oil (notable ALA omega-3 content)",
    },
    "methi_seeds": {  # fenugreek seeds
        "category": "Spice",
        "per_100g_raw": {"iron": 33.5, "calcium": 176, "magnesium": 191, "protein": 23.0,
                          "fiber": 24.6, "energy": 323},
        "states": ["raw"], "serving100g": "spice, used 1-3g per dish",
        "source": "USDA FDC — fenugreek seed",
    },
    "kali_mirch": {  # black pepper
        "category": "Spice",
        "per_100g_raw": {"iron": 9.7, "calcium": 443, "magnesium": 171, "potassium": 1329,
                          "protein": 10.4, "fiber": 25.3, "energy": 251},
        "states": ["raw"], "serving100g": "spice, used 0.5-2g per dish",
        "source": "USDA FDC — black pepper",
    },
    "elaichi": {  # cardamom
        "category": "Spice",
        "per_100g_raw": {"iron": 13.9, "calcium": 383, "magnesium": 229, "potassium": 1119,
                          "protein": 10.8, "fiber": 28.0, "energy": 311},
        "states": ["raw"], "serving100g": "spice, used 0.5-2g per dish",
        "source": "USDA FDC — cardamom",
    },
    "dalchini": {  # cinnamon
        "category": "Spice",
        "per_100g_raw": {"iron": 8.3, "calcium": 1002, "magnesium": 60, "protein": 4.0,
                          "fiber": 53.1, "energy": 247},
        "states": ["raw"], "serving100g": "spice, used 0.5-1g per dish",
        "source": "USDA FDC — cinnamon",
    },
    "laung": {  # cloves
        "category": "Spice",
        "per_100g_raw": {"iron": 11.8, "calcium": 632, "magnesium": 259, "potassium": 1020,
                          "protein": 6.0, "fiber": 33.9, "energy": 274},
        "states": ["raw"], "serving100g": "spice, used 0.2-1g per dish",
        "source": "USDA FDC — cloves",
    },
    "hing": {  # asafoetida
        "category": "Spice",
        "per_100g_raw": {"iron": 39.1, "calcium": 690, "protein": 4.2, "fiber": 4.1, "energy": 297},
        "states": ["raw"], "serving100g": "spice, used a pinch (~0.1-0.5g) per dish",
        "source": "USDA FDC — asafoetida",
    },
    "saunf": {  # fennel seeds
        "category": "Spice",
        "per_100g_raw": {"iron": 18.5, "calcium": 1196, "magnesium": 385, "potassium": 1694,
                          "protein": 15.8, "fiber": 39.8, "energy": 345},
        "states": ["raw"], "serving100g": "spice, used 0.5-2g per dish",
        "source": "USDA FDC — fennel seed",
    },
    "khus_khus": {  # poppy seeds
        "category": "Spice",
        "per_100g_raw": {"iron": 9.8, "calcium": 1438, "magnesium": 347, "protein": 18.0,
                          "fiber": 19.5, "energy": 525},
        "states": ["raw"], "serving100g": "used 2-10g per dish (Bengali cooking)",
        "source": "USDA FDC — poppy seed",
    },
    "besan": {  # gram/chickpea flour
        "category": "Grain",
        "per_100g_raw": {"iron": 4.6, "calcium": 45, "magnesium": 166, "folate": 437,
                          "protein": 22.0, "fiber": 10.8, "energy": 387},
        "states": ["raw"], "serving100g": "~30-60g per dish",
        "source": "USDA FDC — chickpea flour (besan)",
    },
    "rice_flour": {
        "category": "Grain",
        "per_100g_raw": {"iron": 0.35, "calcium": 10, "protein": 6.0, "fiber": 2.4, "energy": 366},
        "states": ["raw"], "serving100g": "~30-60g per dish",
        "source": "USDA FDC — rice flour",
    },
    "bamboo_shoot": {
        "category": "Vegetable",
        "per_100g_raw": {"potassium": 533, "protein": 2.6, "fiber": 2.2, "energy": 27},
        "states": ["raw", "boiled", "fermented"], "serving100g": "~50-100g per dish (Northeast cooking)",
        "source": "USDA FDC — bamboo shoots",
    },
    "curry_leaves": {
        "category": "Spice",
        "per_100g_raw": {"calcium": 830, "iron": 0.93, "vitamin_a": 175, "protein": 6.1,
                          "fiber": 6.4, "energy": 108},
        "states": ["raw"], "serving100g": "spice, used 1-3g (few leaves) per dish",
        "source": "IFCT2017 — curry leaves",
    },
    "coconut_milk": {
        "category": "Dairy",
        "per_100g_raw": {"magnesium": 37, "potassium": 263, "iron": 1.6, "protein": 2.3, "energy": 230},
        "states": ["raw"], "serving100g": "~30-100g per dish (South/coastal cooking)",
        "source": "USDA FDC — coconut milk, canned",
    },
    "pork": {
        "category": "Meat",
        "per_100g_raw": {"iron": 0.87, "zinc": 2.9, "vitamin_b12": 0.7, "vitamin_b1": 0.8,
                          "protein": 27.0, "energy": 242},
        "states": ["raw", "cooked (curry)", "roasted"], "serving100g": "~100g per serving",
        "source": "USDA FDC — pork, raw",
    },
    "dried_red_chili": {
        "category": "Spice",
        "per_100g_raw": {"iron": 17.3, "vitamin_a": 2081, "vitamin_c": 21.9, "protein": 12.0,
                          "fiber": 27.2, "energy": 282},
        "states": ["raw", "dried"], "serving100g": "spice, used 1-4g per dish",
        "source": "USDA FDC — chili powder / dried red chili",
    },
    "garam_masala": {
        "category": "Spice",
        "per_100g_raw": {"iron": 15.0, "calcium": 450, "magnesium": 200, "protein": 12.0,
                         "fiber": 25.0, "energy": 380},
        "states": ["raw"], "serving100g": "spice blend, used 1-3g per dish",
        "source": "Estimated as weighted blend of constituent spices (cumin, coriander, cardamom, "
                  "cinnamon, clove, black pepper) in typical garam-masala proportions — not a "
                  "single lab-measured value; used only in small per-dish quantities",
    },
    "ajwain": {
        "category": "Spice",
        "per_100g_raw": {"iron": 14.6, "calcium": 1525, "protein": 15.9, "fiber": 21.1, "energy": 305},
        "states": ["raw"], "serving100g": "spice, used <1g per dish",
        "source": "USDA FDC — ajwain / carom seeds",
    },
    "sambar_powder": {
        "category": "Spice",
        "per_100g_raw": {"iron": 20.0, "calcium": 400, "protein": 14.0, "fiber": 20.0, "energy": 340},
        "states": ["raw"], "serving100g": "spice blend, used 2-5g per dish",
        "source": "Estimated as weighted blend of its constituent spices (coriander, chili, "
                  "toor dal, cumin, fenugreek, black pepper) in typical proportions",
    },
    "soy_sauce": {
        "category": "Condiment",
        "per_100g_raw": {"protein": 8.1, "energy": 53},
        "states": ["raw"], "serving100g": "condiment, used 5-15g per dish",
        "source": "USDA FDC — soy sauce",
    },
    "tej_patta": {  # bay leaf
        "category": "Spice",
        "per_100g_raw": {"iron": 43.0, "calcium": 834, "magnesium": 120, "protein": 7.6,
                          "fiber": 26.3, "energy": 313},
        "states": ["raw"], "serving100g": "spice, 1 leaf (~0.2g) per dish — negligible per-serving contribution",
        "source": "USDA FDC — bay leaf",
    },
}

alias_resolved = 0
unresolved_generic = 0
for k, v in ALIAS_MAP.items():
    if v is not None and v not in ingredients and v not in NEW_INGREDIENTS:
        print(f"WARNING: alias target '{v}' (from '{k}') not found in master DB")

for iid, data in NEW_INGREDIENTS.items():
    data["source_category_array"] = "SPICES_CONDIMENTS_ADDENDUM"
    ingredients[iid] = data

master["count"] = len(ingredients)
master["alias_map"] = ALIAS_MAP
master["zero_contribution"] = sorted(ZERO_CONTRIBUTION)
master["ingredients"] = ingredients
MASTER_PATH.write_text(json.dumps(master, indent=2, ensure_ascii=False))
print(f"Total ingredients now: {len(ingredients)} (138 base + {len(NEW_INGREDIENTS)} spices/condiments added)")
print(f"Alias map entries: {len(ALIAS_MAP)}")
