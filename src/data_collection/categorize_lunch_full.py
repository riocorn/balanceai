"""
Full Indian-meal-course categorization of all 169 lunch-compendium dishes.
Categories (real Indian thali/meal taxonomy):
  roti        - bread/flatbread, including baked-dumpling+bread combos (baati/bafla/tingmo)
  sabzi       - dry/semi-dry vegetable preparation
  dal         - lentil/legume-based curry (incl. legume-forward stews like sambar/dalma/huli)
  veg_curry   - wet/gravy vegetable curry (not dry sabzi, not lentil-based)
  non_veg_curry - meat/fish/poultry/egg main dish
  kadhi       - yogurt-gram-flour (or buttermilk) based curry
  rice        - rice-based one-pot/mixed/combo dish
  soup_stew   - thin broth/soup/light stew
  salad       - raw or tossed salad
  sweet       - dessert
  snack       - fritters/pancakes/steamed cakes/condiments (side items, not a full course)
  drink       - cooling beverage/liquid accompaniment

This is a hand-verified mapping against known Indian culinary identity of each dish
(not keyword/regex guessing) — the earlier keyword pass caused false positives
(e.g. "Kolhapuri"/"Manipuri" matching "puri") and can't reliably distinguish
dal vs kadhi vs veg_curry vs soup, which need real dish knowledge.
"""
import json
from pathlib import Path

RESEARCH_DIR = Path("/home/abhay/Downloads/medical/balanceai/data/lunch_research")
OUT_DIR = RESEARCH_DIR.parent / "lunch_categories"
OUT_DIR.mkdir(exist_ok=True)

REGION_FILES = ["north.json", "south.json", "east.json", "west.json", "northeast.json", "central_islands.json"]

# Dishes already correctly bucketed by the first pass (name -> category), carried forward as-is.
CARRY_FORWARD_ROTI = {
    "Sarson da Saag with Makki di Roti", "Bajra Roti with Sabzi", "Obbattu", "Litti Chokha",
    "Sattu Paratha", "Chilka Roti", "Pithla Bhakri", "Puran Poli",
}
CARRY_FORWARD_SABZI = {
    "Bhindi Masala", "Gatte ki Sabzi", "Bharwa Baingan", "Hak Saag", "Poriyal", "Kootu", "Avial",
    "Thoran", "Olan", "Palya", "Gongura Pachadi", "Bagara Baingan", "Bengali Aloo Dum",
    "Korola Bhaja", "Shukto", "Ghanta Tarkari", "Baingan Bharta (Bihari)", "Ol/Yam Achaar and Chutney",
    "Rugra Sabzi", "Undhiyu", "Umbadiyu", "Chura Sabji", "Papad Ki Sabji", "Dubki Kadhi", "Chana Bhaji",
}

# Reclassify a few from the old "roti" false positives (regex bug) and dry-veg items
# that keyword pass 1 missed, into their correct bucket.
MOVE_TO_SABZI = {"Ker Sangri", "Aloo ke Gutke", "Aloo Posto", "Mochar Ghonto", "Bharli Vangi",
                 "Ringan no Olo", "Aloo Pitika"}
MOVE_TO_ROTI = {"Khambir"}

# Hand-verified category for every remaining dish (region, name) -> category
MANUAL_CATEGORY = {
    ("North", "Dal Tadka"): "dal",
    ("North", "Dal Makhani"): "dal",
    ("North", "Rajma Chawal"): "rice",
    ("North", "Chole (Chana Masala)"): "dal",
    ("North", "Kadhi Pakora"): "kadhi",
    ("North", "Butter Chicken"): "non_veg_curry",
    ("North", "Kachumber Salad"): "salad",
    ("North", "Dal Baati Churma"): "roti",
    ("North", "Laal Maas"): "non_veg_curry",
    ("North", "Rajasthani Kadhi"): "kadhi",
    ("North", "Baati Chokha"): "roti",
    ("North", "Vegetable Kofta Curry"): "veg_curry",
    ("North", "Tehri"): "rice",
    ("North", "Nimona"): "veg_curry",
    ("North", "Awadhi Biryani"): "rice",
    ("North", "Nihari"): "non_veg_curry",
    ("North", "Rogan Josh"): "non_veg_curry",
    ("North", "Yakhni"): "non_veg_curry",
    ("North", "Dum Aloo Kashmiri"): "veg_curry",
    ("North", "Gushtaba"): "non_veg_curry",
    ("North", "Himachali Dham (Rajma/Chana Madra Thali)"): "veg_curry",
    ("North", "Kullu Trout Curry"): "non_veg_curry",
    ("North", "Kafuli"): "veg_curry",
    ("North", "Bhatt ki Churkani"): "dal",
    ("North", "Phaanu"): "dal",
    ("North", "Chainsoo"): "dal",
    ("North", "Thukpa (vegetable/meat)"): "soup_stew",
    ("North", "Skyu"): "soup_stew",
    ("North", "Tingmo with Dal"): "roti",

    ("South", "Sambar"): "dal",
    ("South", "Rasam"): "soup_stew",
    ("South", "Vatha Kuzhambu"): "veg_curry",
    ("South", "Thayir Sadam"): "rice",
    ("South", "Chettinad Chicken Curry"): "non_veg_curry",
    ("South", "Chettinad Mutton Curry"): "non_veg_curry",
    ("South", "Kaalan"): "kadhi",
    ("South", "Erissery"): "veg_curry",
    ("South", "Parippu Curry"): "dal",
    ("South", "Meen Curry"): "non_veg_curry",
    ("South", "Bisi Bele Bath"): "rice",
    ("South", "Huli"): "dal",
    ("South", "Kosambari"): "salad",
    ("South", "Mudda Pappu with Avakaya"): "dal",
    ("South", "Gongura Pappu"): "dal",
    ("South", "Pulusu"): "veg_curry",
    ("South", "Andhra Chicken Curry"): "non_veg_curry",
    ("South", "Fish Assad Curry"): "non_veg_curry",
    ("South", "Poulet Vindaye"): "non_veg_curry",

    ("East", "Shorshe Ilish"): "non_veg_curry",
    ("East", "Rui Machher Kalia"): "non_veg_curry",
    ("East", "Machher Jhol"): "non_veg_curry",
    ("East", "Chingri Malai Curry"): "non_veg_curry",
    ("East", "Cholar Dal"): "dal",
    ("East", "Dhokar Dalna"): "dal",
    ("East", "Kosha Mangsho"): "non_veg_curry",
    ("East", "Bhapa Ilish"): "non_veg_curry",
    ("East", "Dalma"): "dal",
    ("East", "Santula"): "veg_curry",
    ("East", "Pakhala Bhata"): "rice",
    ("East", "Macha Jhola"): "non_veg_curry",
    ("East", "Chungdi Malai"): "non_veg_curry",
    ("East", "Besara"): "veg_curry",
    ("East", "Bihari Kadhi Badi"): "kadhi",
    ("East", "Chana Ghugni"): "dal",
    ("East", "Bihari Mutton Curry"): "non_veg_curry",
    ("East", "Dhuska"): "snack",
    ("East", "Bamboo Shoot Curry"): "veg_curry",
    ("East", "Pittha (savory)"): "snack",

    ("West", "Varan Bhaat"): "dal",
    ("West", "Amti"): "dal",
    ("West", "Kolhapuri Chicken"): "non_veg_curry",
    ("West", "Masale Bhaat"): "rice",
    ("West", "Sol Kadhi"): "drink",
    ("West", "Dal Dhokli"): "dal",
    ("West", "Gujarati Kadhi"): "kadhi",
    ("West", "Handvo"): "snack",
    ("West", "Fish Curry Rice (Xitt Kodi)"): "non_veg_curry",
    ("West", "Chicken Xacuti"): "non_veg_curry",
    ("West", "Prawn Balchão"): "non_veg_curry",
    ("West", "Sorpotel"): "non_veg_curry",
    ("West", "Tonak"): "dal",
    ("West", "Daman Fish Curry"): "non_veg_curry",
    ("West", "Khichdi Kadhi"): "rice",

    ("Northeast", "Khar"): "veg_curry",
    ("Northeast", "Masor Tenga"): "non_veg_curry",
    ("Northeast", "Hagra Mangxo (Duck Meat Curry)"): "non_veg_curry",
    ("Northeast", "Eromba"): "non_veg_curry",
    ("Northeast", "Chamthong (Kangshoi)"): "soup_stew",
    ("Northeast", "Singju"): "salad",
    ("Northeast", "Chak-hao Kheer"): "sweet",
    ("Northeast", "Naga Smoked Pork with Bamboo Shoot"): "non_veg_curry",
    ("Northeast", "Anishi with Pork"): "non_veg_curry",
    ("Northeast", "Axone Pork Curry"): "non_veg_curry",
    ("Northeast", "Bai"): "soup_stew",
    ("Northeast", "Vawksa Rep"): "non_veg_curry",
    ("Northeast", "Sawhchiar"): "rice",
    ("Northeast", "Jadoh"): "rice",
    ("Northeast", "Dohkhleh"): "salad",
    ("Northeast", "Tungrymbai"): "non_veg_curry",
    ("Northeast", "Minil Songa"): "rice",
    ("Northeast", "Mui Borok"): "non_veg_curry",
    ("Northeast", "Muya Awandru"): "non_veg_curry",
    ("Northeast", "Muya Bai Wahan"): "non_veg_curry",
    ("Northeast", "Gundruk ko Jhol"): "soup_stew",
    ("Northeast", "Sinki Soup"): "soup_stew",
    ("Northeast", "Thukpa"): "soup_stew",
    ("Northeast", "Khaow Nam Paak"): "rice",
    ("Northeast", "Kaaji"): "rice",
    ("Northeast", "Pika Pila with Rice"): "snack",

    ("Central and Islands", "Dal Bafla"): "roti",
    ("Central and Islands", "Bhopali Gosht Korma"): "non_veg_curry",
    ("Central and Islands", "Bhopali Paya"): "non_veg_curry",
    ("Central and Islands", "Bundelkhandi Bara"): "kadhi",
    ("Central and Islands", "Malwai Kadhi"): "kadhi",
    ("Central and Islands", "Chila"): "snack",
    ("Central and Islands", "Bara"): "snack",
    ("Central and Islands", "Aamat"): "veg_curry",
    ("Central and Islands", "Chhattisgarhi Dal Bhat"): "dal",
    ("Central and Islands", "Faraa"): "snack",
    ("Central and Islands", "Andaman Coconut Fish Curry"): "non_veg_curry",
    ("Central and Islands", "Grilled Tuna in Banana Leaf"): "non_veg_curry",
    ("Central and Islands", "Prawn Coconut Curry"): "non_veg_curry",
    ("Central and Islands", "Nicobarese Bamboo Shoot Curry"): "veg_curry",
    ("Central and Islands", "Mus Kavaab"): "non_veg_curry",
    ("Central and Islands", "Lakshadweep Tuna Fish Curry"): "non_veg_curry",
    ("Central and Islands", "Lakshadweep Coconut Rice"): "rice",
    ("Central and Islands", "Kilanji"): "rice",
}

buckets = {c: [] for c in
           ["roti", "sabzi", "dal", "veg_curry", "non_veg_curry", "kadhi", "rice",
            "soup_stew", "salad", "sweet", "snack", "drink"]}
missing = []

for fname in REGION_FILES:
    d = json.loads((RESEARCH_DIR / fname).read_text())
    region = d["region"]
    for dish in d["dishes"]:
        name = dish["name"]
        entry = {**dish, "region": region}
        if name in CARRY_FORWARD_ROTI or name in MOVE_TO_ROTI:
            buckets["roti"].append(entry)
        elif name in CARRY_FORWARD_SABZI or name in MOVE_TO_SABZI:
            buckets["sabzi"].append(entry)
        else:
            cat = MANUAL_CATEGORY.get((region, name))
            if cat:
                buckets[cat].append(entry)
            else:
                missing.append((region, name))

if missing:
    print("MISSING CATEGORY MAPPING FOR:")
    for r, n in missing:
        print(" -", r, "|", n)

total = 0
for cat, dishes in buckets.items():
    out = {"category": cat, "count": len(dishes), "dishes": dishes}
    (OUT_DIR / f"{cat}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"{cat}: {len(dishes)}")
    total += len(dishes)
print(f"TOTAL: {total}")

# remove the old rough files from the first pass
for stale in ["unclassified.json"]:
    p = OUT_DIR / stale
    if p.exists():
        p.unlink()
