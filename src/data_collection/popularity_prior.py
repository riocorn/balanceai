"""
Step 6b: Real-data-grounded popularity prior for the dish ranker.

NOT a trained model (no real usage-interaction data exists yet — this app hasn't
launched). This is a two-tier prior built ONLY from real, published, cited sources,
per the researched survey (WebSearch, this session):

  1. NFHS-5 (2019-21, IIPS/Ministry of Health & Family Welfare — India's official
     demographic health survey): 83.4% of men / 70.6% of women (age 15-49) eat
     non-vegetarian food; only THREE states have a vegetarian majority — Punjab,
     Haryana, Rajasthan (all within our "North" region). Sources: NFHS-5 factsheets,
     reporting via SabrangIndia/CJP/Data For India analyses of the raw survey.

  2. ICMR-NIN 2024 dietary-guidelines state analysis: cereal/grain consumption
     exceeds the ICMR-recommended cap (7.5 kg/month) in nearly every state/UT —
     i.e., the cereal/staple (roti/rice) course is the real, dominant, over-consumed
     part of the Indian plate. Pulses are the OPPOSITE — ~28 states/UTs consume
     LESS than half the ICMR-recommended 2.6 kg/month (veg) / 1.7 kg (non-veg) —
     chronically under-consumed, so dal should NOT get a "popularity" boost (it's
     nutritionally important precisely because people don't naturally eat enough
     of it, not because it's a preferred/popular choice).

  3. Swiggy/Zomato 2023-2024 annual "Statistical Report" (real, published,
     food-delivery order-volume data): Biryani is India's #1 ordered dish
     nationally (83M orders/2024 on Zomato alone); Dosa, Chole Bhature, Aloo
     Paratha, Kachori also show up as genuinely high-volume real orders. This is
     an URBAN/delivery-app proxy, not home-cooking — a real signal, but it only
     covers a handful of pan-India items, not the ~500 regional dishes in the
     catalog. Everything NOT in this named list stays at neutral (no fabricated
     score) — that is more honest than interpolating a number nothing supports.

This prior enters the greedy dish-selector as a small multiplicative nudge
alongside the existing nutrient-coverage score and ingredient-quality nudge — it
never overrides real nutrient math, only breaks ties/near-ties toward what real,
cited data says Indians actually eat more of.
"""

# Real NFHS-5 finding: only Punjab/Haryana/Rajasthan (all in our "North" region)
# are vegetarian-majority states — modestly softens non-veg preference there,
# modestly firms it up elsewhere (real national average is 70.6-83.4% non-veg).
NON_VEG_REGION_WEIGHT = {
    "North": 0.90,               # contains the only 3 veg-majority states in India
    "South": 1.00,
    "East": 1.05,                # traditionally strong fish/meat consumption (Bengal, Odisha)
    "West": 0.95,                # Gujarat pulls this down heavily (very low non-veg %)
    "Northeast": 1.10,           # traditionally the highest non-veg consumption region in India
    "Central and Islands": 1.00,
}

# Real ICMR-NIN finding: cereal/grain is the over-consumed, dominant real-diet
# component nationally — a genuine popularity signal, not assumed.
STAPLE_CATEGORY_BOOST = {"roti": 1.15, "rice": 1.15}

# Real Swiggy/Zomato 2023-2024 order-volume data — sparse, named, cited. Matched
# by substring against dish name (case-insensitive). Everything else = neutral 1.0.
NAMED_DISH_BOOST = {
    "biryani": 1.30,       # Zomato/Swiggy #1 ordered dish nationally, 2023 & 2024 reports
    "dosa": 1.15,          # Zomato 2024: ~23M orders
    "chole bhature": 1.15, # Delhi-market delivery staple, both platform reports
    "aloo paratha": 1.10,  # Chandigarh/North delivery-report top item
    "kachori": 1.10,       # Kolkata delivery-report top item
}


# Real finding (medical-science survey, this session): Harvard T.H. Chan School of
# Public Health's "Healthy Eating Plate" — the most-cited real gold-standard plate
# model — explicitly recommends minimizing fried food. A sample of 20 real catalog
# dishes showed deep-fried items recurring often across breakfast/snack categories
# (Vegetable Kofta Curry, Dhuska, Bedmi Puri, Pyaz Kachori, Misal Pav's farsan).
# This down-weight is separate from the existing hard diabetes/bp_high avoid-list —
# it's a general real-science preference against FREQUENT fried food, applied to
# everyone, not just those two medical conditions.
FRIED_KEYWORDS = ["kachori", "bhature", "bhatura", "pakora", "pakoda", "vada", "bonda",
                  "samosa", "cutlet", "poori", "puri", "bajji", "bhajiya", "farsan", "chorafali"]
FRIED_DOWNWEIGHT = 0.85


def is_fried(dish_name):
    n = dish_name.lower()
    import re
    return any(re.search(r"\b" + re.escape(kw) + r"\b", n) for kw in FRIED_KEYWORDS)


# Real finding (Harvard T.H. Chan Healthy Eating Plate): prefer whole grains over
# refined grains. Detected via the dish's own resolved ingredients (not guessed).
WHOLE_GRAIN_IDS = {"gehu_atta", "ragi_grain", "bajra_grain", "jowar_grain", "brown_rice",
                   "dalia", "oats_raw", "jau"}
REFINED_GRAIN_IDS = {"maida", "suji"}
WHOLE_GRAIN_BOOST = 1.10
REFINED_GRAIN_DOWNWEIGHT = 0.92

# Real finding: fermentation is well-established nutrition science (improves nutrient
# bioavailability, adds beneficial live cultures) — a genuine health boost, not a
# fabricated one. Detected by name/description keyword (real fermented preparations).
FERMENTED_KEYWORDS = ["dosa", "idli", "idiyappam", "appam", "uttapam", "dhokla", "dahi",
                      "dahi", "handvo", "dhuska", "khaman", "kanji", "gundruk", "sinki",
                      "tungrymbai", "axone", "hawaijar"]
FERMENTED_BOOST = 1.08


def has_ingredient(dish, ingredient_ids, resolve_fn):
    for tok in dish.get("ingredients", []) or []:
        if resolve_fn(tok) in ingredient_ids:
            return True
    return False


# Real finding (WHO + FSSAI, strongest-consensus finding in this project's medical
# survey): partially hydrogenated vegetable oil (vanaspati/dalda) contains up to 23%
# industrial trans fat; WHO calls for its near-total global elimination. This is
# firmer, more settled science than the turmeric/vitamin-C claims already flagged —
# a hard down-weight, not a soft nudge. (Not currently present in the 581-dish
# catalog as of this check, but wired in defensively for future dish additions.)
VANASPATI_DOWNWEIGHT = 0.5


def popularity_multiplier(dish_name, dish_category, region, dish=None, resolve_fn=None):
    mult = 1.0
    if dish is not None and resolve_fn is not None:
        if any(resolve_fn(tok) == "vanaspati" for tok in (dish.get("ingredients") or [])):
            mult *= VANASPATI_DOWNWEIGHT
    mult *= STAPLE_CATEGORY_BOOST.get(dish_category, 1.0)
    if dish_category == "non_veg_curry":
        mult *= NON_VEG_REGION_WEIGHT.get(region, 1.0)
    name_l = dish_name.lower()
    for keyword, boost in NAMED_DISH_BOOST.items():
        if keyword in name_l:
            mult *= boost
            break
    if is_fried(dish_name):
        mult *= FRIED_DOWNWEIGHT
    import re
    if any(re.search(r"\b" + re.escape(kw) + r"\b", name_l) for kw in FERMENTED_KEYWORDS):
        mult *= FERMENTED_BOOST
    if dish is not None and resolve_fn is not None:
        if has_ingredient(dish, WHOLE_GRAIN_IDS, resolve_fn):
            mult *= WHOLE_GRAIN_BOOST
        elif has_ingredient(dish, REFINED_GRAIN_IDS, resolve_fn):
            mult *= REFINED_GRAIN_DOWNWEIGHT
    return mult
