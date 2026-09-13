import requests, json, os, time

API_KEY = "DEMO_KEY"
BASE_URL = "https://api.nal.usda.gov/fdc/v1"
OUT = "/home/abhay/Downloads/medical/balanceai/data/usda"
os.makedirs(OUT, exist_ok=True)

INDIAN_FOODS = [
    "ragi", "bajra", "jowar", "amaranth", "quinoa",
    "moong dal", "masoor dal", "chana dal", "urad dal", "toor dal",
    "rice", "wheat flour", "cornmeal",
    "spinach", "fenugreek leaves", "drumstick leaves", "amaranth leaves",
    "sweet potato", "carrot", "pumpkin", "bitter gourd",
    "sesame seeds", "flaxseeds", "pumpkin seeds", "sunflower seeds",
    "almonds", "walnuts", "cashews", "groundnuts",
    "milk", "yogurt", "paneer", "ghee",
    "egg", "chicken", "fish mackerel", "salmon",
    "amla", "guava", "mango", "papaya", "banana",
    "turmeric", "ginger", "garlic", "coriander",
    "coconut", "mustard oil", "sesame oil",
]

NUTRIENTS_WANTED = {
    "1003": "protein_g",
    "1004": "fat_g",
    "1005": "carbs_g",
    "1008": "energy_kcal",
    "1087": "calcium_mg",
    "1089": "iron_mg",
    "1090": "magnesium_mg",
    "1091": "phosphorus_mg",
    "1092": "potassium_mg",
    "1095": "zinc_mg",
    "1098": "copper_mg",
    "1100": "selenium_mcg",
    "1106": "vitamin_a_mcg",
    "1109": "vitamin_e_mg",
    "1114": "vitamin_d_IU",
    "1162": "vitamin_c_mg",
    "1165": "thiamin_mg",
    "1166": "riboflavin_mg",
    "1167": "niacin_mg",
    "1175": "vitamin_b6_mg",
    "1177": "folate_mcg",
    "1178": "vitamin_b12_mcg",
    "1293": "omega3_g",
}

def search_food(query):
    url = f"{BASE_URL}/foods/search"
    params = {"query": query, "api_key": API_KEY, "pageSize": 3, "dataType": "Foundation,SR Legacy"}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    foods = data.get("foods", [])
    return foods[0] if foods else None

def extract_nutrients(food):
    result = {}
    for n in food.get("foodNutrients", []):
        nid = str(n.get("nutrientId") or n.get("nutrientNumber", ""))
        if nid in NUTRIENTS_WANTED:
            result[NUTRIENTS_WANTED[nid]] = n.get("value", 0)
    return result

all_foods = {}
for food_name in INDIAN_FOODS:
    out_file = f"{OUT}/{food_name.replace(' ', '_')}.json"
    if os.path.exists(out_file):
        print(f"  SKIP: {food_name}")
        with open(out_file) as f:
            all_foods[food_name] = json.load(f)
        continue
    try:
        food = search_food(food_name)
        if food:
            nutrients = extract_nutrients(food)
            entry = {
                "name": food.get("description", food_name),
                "fdc_id": food.get("fdcId"),
                "data_type": food.get("dataType"),
                "nutrients_per_100g": nutrients,
            }
            with open(out_file, "w") as f:
                json.dump(entry, f, indent=2)
            all_foods[food_name] = entry
            print(f"  OK: {food_name} — {len(nutrients)} nutrients")
        else:
            print(f"  NOT FOUND: {food_name}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  ERROR {food_name}: {e}")

with open(f"{OUT}/all_foods_combined.json", "w") as f:
    json.dump(all_foods, f, indent=2)

print(f"\nTotal foods: {len(all_foods)}")
print("Saved:", f"{OUT}/all_foods_combined.json")
