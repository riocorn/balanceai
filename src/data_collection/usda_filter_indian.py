import json, os

SRC = "/home/abhay/Downloads/medical/balanceai/data/usda/FoodData_Central_sr_legacy_food_json_2021-10-28.json"
OUT = "/home/abhay/Downloads/medical/balanceai/data/usda/indian_foods_usda.json"

INDIAN_KEYWORDS = [
    "ragi","finger millet","bajra","pearl millet","jowar","sorghum","amaranth",
    "moong","mung","masoor","lentil","chana","chickpea","urad","toor","pigeon pea",
    "rice","wheat","corn","maize","barley","buckwheat",
    "spinach","fenugreek","mustard greens","drumstick","moringa",
    "sweet potato","carrot","pumpkin","bitter gourd","ridge gourd","bottle gourd",
    "sesame","flaxseed","pumpkin seed","sunflower seed",
    "almond","walnut","cashew","peanut","groundnut","pistachio",
    "milk","yogurt","curd","cheese","butter","ghee",
    "egg","chicken","fish","mackerel","salmon","sardine","tilapia",
    "mango","guava","banana","papaya","amla","gooseberry","coconut",
    "turmeric","ginger","garlic","cumin","coriander","cardamom","clove","pepper",
    "mustard oil","coconut oil","sesame oil",
    "jaggery","tamarind","curry leaf","jackfruit","lotus",
]

NUTRIENT_MAP = {
    1003: "protein_g", 1004: "fat_g", 1005: "carbs_g", 1008: "energy_kcal",
    1087: "calcium_mg", 1089: "iron_mg", 1090: "magnesium_mg",
    1091: "phosphorus_mg", 1092: "potassium_mg", 1095: "zinc_mg",
    1098: "copper_mg", 1100: "selenium_mcg", 1106: "vitamin_a_mcg",
    1109: "vitamin_e_mg", 1114: "vitamin_d_IU", 1162: "vitamin_c_mg",
    1165: "thiamin_mg", 1166: "riboflavin_mg", 1167: "niacin_mg",
    1175: "vitamin_b6_mg", 1177: "folate_mcg", 1178: "vitamin_b12_mcg",
    1293: "omega3_g",
}

print("Loading USDA database (201MB)...")
with open(SRC, encoding="utf-8") as f:
    db = json.load(f)

foods = db.get("SRLegacyFoods", [])
print(f"Total foods in USDA SR Legacy: {len(foods)}")

matched = {}
for food in foods:
    name = food.get("description", "").lower()
    if any(kw in name for kw in INDIAN_KEYWORDS):
        nutrients = {}
        for n in food.get("foodNutrients", []):
            nid = n.get("nutrient", {}).get("id")
            if nid in NUTRIENT_MAP:
                nutrients[NUTRIENT_MAP[nid]] = n.get("amount", 0)
        matched[food["description"]] = {
            "fdc_id": food.get("fdcId"),
            "category": food.get("foodCategory", {}).get("description", ""),
            "nutrients_per_100g": nutrients,
        }

print(f"Indian-relevant foods matched: {len(matched)}")
with open(OUT, "w") as f:
    json.dump(matched, f, indent=2)
print(f"Saved: {OUT}")

top = sorted(matched.items(), key=lambda x: len(x[1]["nutrients_per_100g"]), reverse=True)[:10]
for name, data in top:
    print(f"  {name[:60]} — {len(data['nutrients_per_100g'])} nutrients")
