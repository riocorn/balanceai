"""
Seasonal ingredient availability for India
Keys: ingredient_id (snake_case)
seasons: list of Indian season names (or "all")
regions: list of Indian region names (or "all")
"""

ALL_SEASONS = ["Summer", "Monsoon", "Autumn", "Winter", "Spring",
               "Southwest Monsoon", "Northeast Monsoon", "Pre-monsoon",
               "Mild Winter", "Post-monsoon", "Extreme Summer"]

SUMMER   = ["Summer", "Extreme Summer", "Pre-monsoon"]
MONSOON  = ["Monsoon", "Southwest Monsoon", "Northeast Monsoon"]
AUTUMN   = ["Autumn", "Post-monsoon"]
WINTER   = ["Winter", "Mild Winter"]
SPRING   = ["Spring"]

NORTH     = ["north"]
SOUTH     = ["south"]
EAST      = ["east"]
NORTHEAST = ["northeast"]
WEST      = ["west"]
CENTRAL   = ["central"]
ALL_REG   = ["north", "south", "east", "northeast", "west", "central"]

INGREDIENTS: dict[str, dict] = {

    # ── ALWAYS AVAILABLE (staples) ─────────────────────────────────────────
    "rice":            {"seasons": "all", "regions": "all", "name": "Rice"},
    "wheat_flour":     {"seasons": "all", "regions": "all", "name": "Wheat Flour (Atta)"},
    "toor_dal":        {"seasons": "all", "regions": "all", "name": "Toor Dal"},
    "moong_dal":       {"seasons": "all", "regions": "all", "name": "Moong Dal"},
    "chana_dal":       {"seasons": "all", "regions": "all", "name": "Chana Dal"},
    "urad_dal":        {"seasons": "all", "regions": "all", "name": "Urad Dal"},
    "rajma":           {"seasons": "all", "regions": "all", "name": "Rajma"},
    "chickpea":        {"seasons": "all", "regions": "all", "name": "Chickpea (Chole)"},
    "onion":           {"seasons": "all", "regions": "all", "name": "Onion"},
    "garlic":          {"seasons": "all", "regions": "all", "name": "Garlic"},
    "ginger":          {"seasons": "all", "regions": "all", "name": "Ginger"},
    "tomato":          {"seasons": "all", "regions": "all", "name": "Tomato"},
    "potato":          {"seasons": "all", "regions": "all", "name": "Potato"},
    "milk":            {"seasons": "all", "regions": "all", "name": "Milk"},
    "curd":            {"seasons": "all", "regions": "all", "name": "Curd (Dahi)"},
    "paneer":          {"seasons": "all", "regions": "all", "name": "Paneer"},
    "egg":             {"seasons": "all", "regions": "all", "name": "Egg"},
    "ghee":            {"seasons": "all", "regions": "all", "name": "Ghee"},
    "oil":             {"seasons": "all", "regions": "all", "name": "Cooking Oil"},
    "cumin":           {"seasons": "all", "regions": "all", "name": "Cumin (Jeera)"},
    "mustard_seeds":   {"seasons": "all", "regions": "all", "name": "Mustard Seeds"},
    "turmeric":        {"seasons": "all", "regions": "all", "name": "Turmeric"},
    "coriander_pwd":   {"seasons": "all", "regions": "all", "name": "Coriander Powder"},
    "chili_pwd":       {"seasons": "all", "regions": "all", "name": "Red Chili Powder"},
    "garam_masala":    {"seasons": "all", "regions": "all", "name": "Garam Masala"},
    "coriander_leaves":{"seasons": "all", "regions": "all", "name": "Coriander Leaves"},
    "salt":            {"seasons": "all", "regions": "all", "name": "Iodized Salt"},
    "black_pepper":    {"seasons": "all", "regions": "all", "name": "Black Pepper (Kali Mirch)"},
    "cardamom":        {"seasons": "all", "regions": "all", "name": "Cardamom (Elaichi)"},
    "cooking_oil":     {"seasons": "all", "regions": "all", "name": "Cooking Oil (Sarson/Sunflower/Groundnut)"},
    "saffron":         {"seasons": "all", "regions": NORTH + CENTRAL, "name": "Saffron (Kesar)"},
    "jaggery":         {"seasons": "all", "regions": "all", "name": "Jaggery (Gud)"},
    "sugar":           {"seasons": "all", "regions": "all", "name": "Sugar"},
    "banana":          {"seasons": "all", "regions": "all", "name": "Banana"},
    "papaya":          {"seasons": "all", "regions": "all", "name": "Papaya"},
    "lemon":           {"seasons": "all", "regions": "all", "name": "Lemon"},
    "green_chili":     {"seasons": "all", "regions": "all", "name": "Green Chili"},
    "curry_leaves":    {"seasons": "all", "regions": ALL_REG, "name": "Curry Leaves"},
    "poha":            {"seasons": "all", "regions": "all", "name": "Poha (Flattened Rice)"},
    "semolina":        {"seasons": "all", "regions": "all", "name": "Semolina (Suji/Rava)"},
    "besan":           {"seasons": "all", "regions": "all", "name": "Besan (Gram Flour)"},
    "oats":            {"seasons": "all", "regions": "all", "name": "Oats"},
    "peanut":          {"seasons": "all", "regions": "all", "name": "Peanuts"},
    "sesame":          {"seasons": "all", "regions": "all", "name": "Sesame (Til)"},
    "sesame_seeds":    {"seasons": "all", "regions": "all", "name": "Sesame Seeds (Til)"},
    "sunflower_seeds": {"seasons": "all", "regions": "all", "name": "Sunflower Seeds"},
    "pumpkin_seeds":   {"seasons": "all", "regions": "all", "name": "Pumpkin Seeds (Kaddu ke Beej)"},
    "flaxseeds":       {"seasons": "all", "regions": NORTH + CENTRAL + WEST, "name": "Flaxseeds (Alsi)"},
    "chia_seeds":      {"seasons": "all", "regions": "all", "name": "Chia Seeds"},
    "almonds":         {"seasons": "all", "regions": "all", "name": "Almonds (Badam)"},
    "walnuts":         {"seasons": "all", "regions": NORTH + CENTRAL, "name": "Walnuts (Akhrot)"},
    "cashews":         {"seasons": "all", "regions": "all", "name": "Cashews (Kaju)"},
    "pistachios":      {"seasons": "all", "regions": "all", "name": "Pistachios (Pista)"},
    "coconut":         {"seasons": "all", "regions": SOUTH + WEST + NORTHEAST + EAST, "name": "Coconut"},
    "coconut_dried":   {"seasons": "all", "regions": "all", "name": "Dried Coconut"},
    "tamarind":        {"seasons": "all", "regions": SOUTH + WEST + CENTRAL, "name": "Tamarind"},
    "dry_fruits":      {"seasons": "all", "regions": "all", "name": "Dry Fruits (almonds, cashews)"},
    "chicken":         {"seasons": "all", "regions": "all", "name": "Chicken"},
    "mutton":          {"seasons": "all", "regions": "all", "name": "Mutton"},
    "fish_dried":      {"seasons": "all", "regions": SOUTH + EAST + NORTHEAST + WEST, "name": "Dried Fish"},

    # ── SUMMER ────────────────────────────────────────────────────────────
    "raw_mango":       {"seasons": SUMMER + SPRING, "regions": "all", "name": "Raw Mango (Kaccha Aam)"},
    "mango":           {"seasons": SUMMER, "regions": "all", "name": "Ripe Mango"},
    "watermelon":      {"seasons": SUMMER, "regions": "all", "name": "Watermelon"},
    "muskmelon":       {"seasons": SUMMER, "regions": "all", "name": "Muskmelon (Kharbooja)"},
    "cucumber":        {"seasons": SUMMER + MONSOON, "regions": "all", "name": "Cucumber"},
    "bottle_gourd":    {"seasons": SUMMER + MONSOON, "regions": "all", "name": "Bottle Gourd (Lauki)"},
    "ridge_gourd":     {"seasons": SUMMER + MONSOON, "regions": "all", "name": "Ridge Gourd (Turai)"},
    "bitter_gourd":    {"seasons": SUMMER + MONSOON, "regions": "all", "name": "Bitter Gourd (Karela)"},
    "drumstick":       {"seasons": SUMMER + SPRING, "regions": SOUTH + WEST + CENTRAL, "name": "Drumstick (Sahjan)"},
    "jackfruit_raw":   {"seasons": SUMMER, "regions": SOUTH + EAST + NORTHEAST + WEST, "name": "Raw Jackfruit"},
    "kokum":           {"seasons": SUMMER + MONSOON, "regions": WEST + SOUTH, "name": "Kokum"},
    "mint":            {"seasons": SUMMER + SPRING + MONSOON, "regions": "all", "name": "Mint (Pudina)"},
    "rose_water":      {"seasons": SUMMER + SPRING, "regions": "all", "name": "Rose Water"},
    "sattu":           {"seasons": SUMMER, "regions": NORTH + EAST + CENTRAL, "name": "Sattu"},
    "lychee":          {"seasons": SUMMER, "regions": NORTH + EAST + NORTHEAST, "name": "Lychee"},
    "tinda":           {"seasons": SUMMER, "regions": NORTH + CENTRAL, "name": "Tinda (Apple Gourd)"},
    "parwal":          {"seasons": SUMMER + MONSOON, "regions": NORTH + EAST + CENTRAL, "name": "Parwal"},
    "raw_banana":      {"seasons": "all", "regions": SOUTH + EAST + NORTHEAST + WEST, "name": "Raw Banana"},
    "tender_coconut":  {"seasons": SUMMER + MONSOON, "regions": SOUTH + WEST + NORTHEAST, "name": "Tender Coconut"},

    # ── MONSOON ──────────────────────────────────────────────────────────
    "corn":            {"seasons": MONSOON, "regions": "all", "name": "Corn (Makka)"},
    "jamun":           {"seasons": MONSOON, "regions": "all", "name": "Jamun"},
    "arbi":            {"seasons": MONSOON + AUTUMN, "regions": "all", "name": "Arbi (Colocasia)"},
    "cluster_beans":   {"seasons": MONSOON, "regions": "all", "name": "Cluster Beans (Gavar)"},
    "flat_beans":      {"seasons": MONSOON, "regions": "all", "name": "Flat Beans (Sem)"},
    "pear":            {"seasons": MONSOON + AUTUMN, "regions": NORTH + CENTRAL, "name": "Pear"},
    "peach":           {"seasons": MONSOON, "regions": NORTH, "name": "Peach"},
    "fresh_fish":      {"seasons": MONSOON + AUTUMN, "regions": EAST + NORTHEAST + SOUTH + WEST, "name": "Fresh River Fish"},
    "yam":             {"seasons": MONSOON + AUTUMN, "regions": SOUTH + EAST + NORTHEAST, "name": "Yam (Suran)"},
    "elephant_yam":    {"seasons": MONSOON + AUTUMN, "regions": SOUTH + WEST + EAST, "name": "Elephant Yam"},
    "bamboo_shoots":   {"seasons": MONSOON, "regions": NORTHEAST + EAST, "name": "Bamboo Shoots"},
    "tulsi":           {"seasons": MONSOON + AUTUMN, "regions": "all", "name": "Tulsi Leaves"},

    # ── AUTUMN / POST-MONSOON ─────────────────────────────────────────────
    "pomegranate":     {"seasons": AUTUMN + WINTER, "regions": "all", "name": "Pomegranate (Anar)"},
    "guava":           {"seasons": AUTUMN + WINTER, "regions": "all", "name": "Guava (Amrood)"},
    "sweet_potato":    {"seasons": AUTUMN + WINTER, "regions": "all", "name": "Sweet Potato (Shakarkandi)"},
    "beetroot":        {"seasons": AUTUMN + WINTER + SPRING, "regions": "all", "name": "Beetroot"},
    "carrot":          {"seasons": AUTUMN + WINTER + SPRING, "regions": "all", "name": "Carrot (Gajar)"},
    "cauliflower":     {"seasons": AUTUMN + WINTER + SPRING, "regions": "all", "name": "Cauliflower (Gobhi)"},
    "apple":           {"seasons": AUTUMN + WINTER, "regions": NORTH, "name": "Apple"},
    "fig":             {"seasons": AUTUMN, "regions": NORTH + WEST + CENTRAL, "name": "Fig (Anjeer)"},

    # ── WINTER ───────────────────────────────────────────────────────────
    "mustard_greens":  {"seasons": WINTER, "regions": NORTH + EAST + CENTRAL, "name": "Sarson (Mustard Greens)"},
    "methi_leaves":    {"seasons": WINTER + SPRING, "regions": "all", "name": "Methi (Fenugreek Leaves)"},
    "spinach":         {"seasons": WINTER + SPRING, "regions": "all", "name": "Spinach (Palak)"},
    "peas":            {"seasons": WINTER + SPRING, "regions": "all", "name": "Green Peas (Matar)"},
    "radish":          {"seasons": WINTER + SPRING + AUTUMN, "regions": "all", "name": "Radish (Mooli)"},
    "turnip":          {"seasons": WINTER, "regions": NORTH + CENTRAL, "name": "Turnip (Shalgam)"},
    "cabbage":         {"seasons": WINTER + SPRING + AUTUMN, "regions": "all", "name": "Cabbage (Patta Gobhi)"},
    "orange":          {"seasons": WINTER, "regions": "all", "name": "Orange (Santra)"},
    "strawberry":      {"seasons": WINTER + SPRING, "regions": NORTH + WEST + SOUTH, "name": "Strawberry"},
    "amla":            {"seasons": WINTER + AUTUMN, "regions": "all", "name": "Amla (Indian Gooseberry)"},
    "dates":           {"seasons": WINTER, "regions": "all", "name": "Dates (Khajoor)"},
    "til_seeds":       {"seasons": WINTER, "regions": "all", "name": "Til (Sesame Seeds, white)"},
    "green_garlic":    {"seasons": WINTER + SPRING, "regions": NORTH + CENTRAL + WEST, "name": "Green Garlic"},
    "bathua":          {"seasons": WINTER, "regions": NORTH + CENTRAL, "name": "Bathua (Chenopodium)"},
    "sarson_oil":      {"seasons": WINTER, "regions": NORTH + EAST, "name": "Mustard Oil"},
    "broccoli":        {"seasons": WINTER + SPRING, "regions": "all", "name": "Broccoli"},
    "knol_khol":       {"seasons": WINTER, "regions": NORTH + CENTRAL + SOUTH, "name": "Knol Khol (Kohlrabi)"},

    # ── SPRING ───────────────────────────────────────────────────────────
    "spring_onion":    {"seasons": SPRING + WINTER, "regions": "all", "name": "Spring Onion"},
    "new_potato":      {"seasons": SPRING, "regions": "all", "name": "New Potato"},
}


def get_available_ingredients(season: str, region: str) -> set[str]:
    available = set()
    for ing_id, data in INGREDIENTS.items():
        s = data["seasons"]
        r = data["regions"]
        season_ok = s == "all" or season in s
        region_ok = r == "all" or region in r
        if season_ok and region_ok:
            available.add(ing_id)
    return available


def ingredient_name(ing_id: str) -> str:
    return INGREDIENTS.get(ing_id, {}).get("name", ing_id)
