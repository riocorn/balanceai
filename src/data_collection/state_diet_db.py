import json, os

STATE_DIETS = {
    "Punjab": {
        "region": "North",
        "staple_grain": ["wheat", "makki"],
        "common_dishes": ["sarson_da_saag", "makki_di_roti", "dal_makhani", "chole", "lassi", "paneer_bhurji", "kheer", "pinni"],
        "common_proteins": ["dal_mash", "dal_chana", "paneer", "chicken", "fish_rahu"],
        "common_vegetables": ["sarson", "bathua", "methi", "gobhi", "mooli", "gajar"],
        "common_fruits": ["kinnow", "amrood", "aam", "lichi"],
        "dairy": ["lassi", "dahi", "makhan", "ghee"],
        "deficiency_risk": ["vitamin_d", "calcium"],
        "notes": "High dairy but low sun exposure in winter; wheat-heavy diet, low iron absorption"
    },
    "Haryana": {
        "region": "North",
        "staple_grain": ["wheat", "bajra"],
        "common_dishes": ["bajra_roti", "kachri_ki_sabzi", "kadhi", "khichdi", "singri_ki_sabzi"],
        "common_proteins": ["dal_arhar", "dal_moong", "dahi", "chicken"],
        "common_vegetables": ["kachri", "sangri", "methi", "palak", "bathua"],
        "common_fruits": ["ber", "amrood", "aam"],
        "dairy": ["dahi", "lassi", "ghee"],
        "deficiency_risk": ["iron", "folate"],
        "notes": "Bajra has good iron but with phytates; low green vegetable variety in dry regions"
    },
    "Uttar_Pradesh": {
        "region": "North",
        "staple_grain": ["wheat", "rice"],
        "common_dishes": ["dal_baati", "tehri", "bedai", "kachori", "litti", "chokha"],
        "common_proteins": ["dal_arhar", "dal_chana", "paneer"],
        "common_vegetables": ["aloo", "baingan", "lauki", "tinda", "parwal"],
        "common_fruits": ["aam", "amrood", "kela"],
        "dairy": ["dahi", "lassi", "rabri"],
        "deficiency_risk": ["vitamin_b12", "iron", "zinc"],
        "notes": "Large vegetarian population; low B12 risk due to limited animal products"
    },
    "Rajasthan": {
        "region": "North",
        "staple_grain": ["bajra", "jowar", "wheat"],
        "common_dishes": ["dal_baati_churma", "gatte_ki_sabzi", "ker_sangri", "laal_maas", "ghevar"],
        "common_proteins": ["dal_moong", "dal_chana", "goat_meat"],
        "common_vegetables": ["ker", "sangri", "cactus", "methi"],
        "common_fruits": ["ber", "kair", "amrood"],
        "dairy": ["dahi", "lassi", "khoa"],
        "deficiency_risk": ["vitamin_a", "vitamin_c", "iodine"],
        "notes": "Arid region; limited fresh vegetables; high salt but low iodized salt historically"
    },
    "Gujarat": {
        "region": "West",
        "staple_grain": ["wheat", "jowar", "bajra"],
        "common_dishes": ["dhokla", "thepla", "undhiyu", "kadhi", "dal_dhokli", "fafda", "jalebi"],
        "common_proteins": ["dal_toor", "dal_moong", "groundnut", "dairy"],
        "common_vegetables": ["surti_papdi", "valor", "ringan", "dudhi", "methi"],
        "common_fruits": ["chiku", "aamla", "aam", "kela"],
        "dairy": ["dahi", "chaas", "shrikhand"],
        "deficiency_risk": ["vitamin_b12", "iron", "omega3"],
        "notes": "High vegetarianism (Jain influence); fermented foods (dhokla) improve iron absorption"
    },
    "Maharashtra": {
        "region": "West",
        "staple_grain": ["rice", "jowar", "bajra"],
        "common_dishes": ["puran_poli", "varan_bhaat", "sabudana_khichdi", "missal_pav", "bhakri", "modak"],
        "common_proteins": ["dal_toor", "moong", "fish", "chicken", "mutton"],
        "common_vegetables": ["drumstick", "karela", "dudhi", "tendli", "ambadi"],
        "common_fruits": ["aamla", "chiku", "aam", "kokum"],
        "dairy": ["dahi", "taak"],
        "deficiency_risk": ["vitamin_d", "calcium"],
        "notes": "Coastal areas have fish (omega-3 rich); urban Maharashtra high processed food"
    },
    "Goa": {
        "region": "West",
        "staple_grain": ["rice"],
        "common_dishes": ["fish_curry_rice", "xacuti", "sorpotel", "bebinca", "vindaloo"],
        "common_proteins": ["fish_kingfish", "prawns", "pork", "chicken"],
        "common_vegetables": ["drumstick", "jackfruit", "breadfruit", "kokum"],
        "common_fruits": ["coconut", "jackfruit", "mango", "cashew"],
        "dairy": ["coconut_milk"],
        "deficiency_risk": ["calcium", "folate"],
        "notes": "High seafood = good omega-3 and B12; but low dairy calcium"
    },
    "Kerala": {
        "region": "South",
        "staple_grain": ["rice"],
        "common_dishes": ["fish_curry", "appam", "puttu", "sadya", "avial", "sambar", "payasam"],
        "common_proteins": ["fish", "coconut", "dal", "chicken", "beef"],
        "common_vegetables": ["raw_banana", "yam", "drumstick", "bitter_gourd", "jackfruit"],
        "common_fruits": ["coconut", "banana", "mango", "tamarind"],
        "dairy": ["coconut_milk"],
        "deficiency_risk": ["vitamin_d", "calcium"],
        "notes": "Low dairy; high coconut oil; good fish omega-3; Vitamin D deficiency despite sunny climate due to indoor lifestyle"
    },
    "Tamil_Nadu": {
        "region": "South",
        "staple_grain": ["rice"],
        "common_dishes": ["idli", "dosa", "sambar", "rasam", "pongal", "curd_rice", "kootu", "kuzhambu"],
        "common_proteins": ["dal", "fish", "chicken", "eggs"],
        "common_vegetables": ["drumstick", "raw_banana", "cluster_beans", "bitter_gourd", "ash_gourd"],
        "common_fruits": ["banana", "mango", "tamarind", "coconut"],
        "dairy": ["dahi", "buttermilk"],
        "deficiency_risk": ["iron", "calcium"],
        "notes": "Fermented rice (idli/dosa) = good bioavailability; sambar = iron from lentils + Vitamin C from tamarind"
    },
    "Andhra_Pradesh": {
        "region": "South",
        "staple_grain": ["rice"],
        "common_dishes": ["pesarattu", "gongura_pickle", "pulusu", "avakaya", "hyderabadi_biryani"],
        "common_proteins": ["dal", "fish", "chicken", "mutton"],
        "common_vegetables": ["gongura", "raw_mango", "brinjal", "ridge_gourd", "cluster_beans"],
        "common_fruits": ["mango", "tamarind", "banana", "guava"],
        "dairy": ["dahi", "neyyi"],
        "deficiency_risk": ["calcium", "vitamin_b12"],
        "notes": "Gongura (sorrel) = high iron + Vitamin C; spicy food may reduce zinc absorption"
    },
    "Telangana": {
        "region": "South",
        "staple_grain": ["rice", "jowar"],
        "common_dishes": ["sarva_pindi", "jonna_rotte", "boti_curry", "gongura_mutton", "sakinalu"],
        "common_proteins": ["dal", "mutton", "chicken", "fish"],
        "common_vegetables": ["gongura", "brinjal", "raw_banana", "yam"],
        "common_fruits": ["mango", "tamarind", "banana"],
        "dairy": ["dahi", "ghee"],
        "deficiency_risk": ["calcium", "vitamin_d"],
        "notes": "Jowar roti = good iron, magnesium; high spice consumption"
    },
    "Karnataka": {
        "region": "South",
        "staple_grain": ["rice", "ragi", "jowar"],
        "common_dishes": ["bisi_bele_bath", "ragi_mudde", "jolada_rotti", "kodubale", "holige", "neer_dosa"],
        "common_proteins": ["dal", "fish", "chicken", "mutton"],
        "common_vegetables": ["raw_banana", "drumstick", "brinjal", "pumpkin"],
        "common_fruits": ["coconut", "banana", "mango", "jackfruit"],
        "dairy": ["dahi", "butter", "ghee"],
        "deficiency_risk": ["vitamin_d"],
        "notes": "Ragi (finger millet) = highest calcium grain in India (344mg/100g); ragi mudde = key food"
    },
    "West_Bengal": {
        "region": "East",
        "staple_grain": ["rice"],
        "common_dishes": ["macher_jhol", "shorshe_ilish", "aloo_posto", "shukto", "mishti_doi", "rasgulla"],
        "common_proteins": ["fish_rohu", "fish_hilsa", "chicken", "eggs", "lentils"],
        "common_vegetables": ["posto", "sheem", "potol", "lau", "jhinge"],
        "common_fruits": ["aam", "kola", "narkol", "litchi"],
        "dairy": ["mishti_doi", "chhana", "ghee"],
        "deficiency_risk": ["vitamin_d", "iodine"],
        "notes": "Fish = high omega-3; hilsa = high Vitamin D; mustard oil = omega-3; coastal iodine deficiency historical"
    },
    "Odisha": {
        "region": "East",
        "staple_grain": ["rice"],
        "common_dishes": ["pakhala_bhata", "dalma", "macha_besara", "chhena_poda", "rasabali"],
        "common_proteins": ["fish", "dal", "crab", "chicken"],
        "common_vegetables": ["raw_papaya", "raw_banana", "drumstick", "pumpkin"],
        "common_fruits": ["coconut", "mango", "jackfruit", "banana"],
        "dairy": ["chhena", "dahi"],
        "deficiency_risk": ["iron", "vitamin_a", "iodine"],
        "notes": "Tribal areas: high Vitamin A deficiency; pakhala (fermented rice water) = probiotic but low nutrients"
    },
    "Bihar": {
        "region": "East",
        "staple_grain": ["rice", "wheat", "maize"],
        "common_dishes": ["litti_chokha", "sattu_paratha", "thekua", "dal_pitha", "mutton_curry"],
        "common_proteins": ["sattu", "dal_arhar", "chicken", "fish"],
        "common_vegetables": ["aloo", "brinjal", "kathal", "parwal", "saag"],
        "common_fruits": ["mango", "guava", "litchi", "banana"],
        "dairy": ["dahi", "ghee"],
        "deficiency_risk": ["iron", "folate", "iodine", "vitamin_a"],
        "notes": "High malnutrition burden; sattu = dense protein+iron; litti chokha = complete meal"
    },
    "Jharkhand": {
        "region": "East",
        "staple_grain": ["rice", "maize", "millets"],
        "common_dishes": ["rugra_curry", "handia", "dhuska", "litti", "mandi"],
        "common_proteins": ["forest_mushrooms", "fish", "chicken", "dal"],
        "common_vegetables": ["forest_greens", "bamboo_shoots", "mahua_flowers", "raw_mango"],
        "common_fruits": ["mahua", "ber", "jackfruit", "mango"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "vitamin_d", "iodine", "vitamin_b12"],
        "notes": "Tribal cuisine; forest foods = diverse micronutrients; low dairy = calcium risk"
    },
    "Assam": {
        "region": "Northeast",
        "staple_grain": ["rice"],
        "common_dishes": ["masor_tenga", "khar", "pitika", "duck_curry", "pitha"],
        "common_proteins": ["fish", "duck", "chicken", "pork"],
        "common_vegetables": ["arum", "banana_flower", "bamboo_shoots", "jackfruit"],
        "common_fruits": ["assam_lemon", "elephant_apple", "mango", "coconut"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "vitamin_d"],
        "notes": "Khar (alkali cooking) = unique; fermented fish = B12; but low dairy"
    },
    "Manipur": {
        "region": "Northeast",
        "staple_grain": ["rice"],
        "common_dishes": ["eromba", "singju", "chamthong", "kangsoi", "ngari_chutney"],
        "common_proteins": ["fish", "pork", "chicken", "fermented_fish_ngari"],
        "common_vegetables": ["kangkong", "banana_flower", "bamboo_shoots", "yam"],
        "common_fruits": ["citrus", "mango", "pineapple"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "iodine"],
        "notes": "Fermented foods = B12 and probiotics; ngari = fermented fish rich in B12"
    },
    "Meghalaya": {
        "region": "Northeast",
        "staple_grain": ["rice"],
        "common_dishes": ["jadoh", "dohneiiong", "tungrymbai", "kwai"],
        "common_proteins": ["pork", "chicken", "fish", "soya_fermented"],
        "common_vegetables": ["bamboo_shoots", "fern", "wild_greens", "turmeric"],
        "common_fruits": ["pineapple", "jackfruit", "citrus", "banana"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "iodine", "vitamin_d"],
        "notes": "Low solar radiation = Vitamin D risk; fermented soya = good protein"
    },
    "Nagaland": {
        "region": "Northeast",
        "staple_grain": ["rice"],
        "common_dishes": ["smoked_pork_bamboo", "axone_pork", "galho", "anishi"],
        "common_proteins": ["pork", "beef", "chicken", "fermented_soya_axone"],
        "common_vegetables": ["bamboo_shoots", "wild_greens", "fern", "yam"],
        "common_fruits": ["citrus", "banana", "pineapple"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "iodine"],
        "notes": "High protein intake; axone = fermented soya = B12; low dairy calcium"
    },
    "Himachal_Pradesh": {
        "region": "North_Hill",
        "staple_grain": ["wheat", "barley", "buckwheat"],
        "common_dishes": ["dham", "sidu", "babru", "tudkiya_bhath", "chha_gosht"],
        "common_proteins": ["dal", "chicken", "lamb", "trout_fish"],
        "common_vegetables": ["rajma", "turnip", "cabbage", "cauliflower", "local_greens"],
        "common_fruits": ["apple", "apricot", "plum", "pear", "walnut"],
        "dairy": ["dahi", "makhan", "ghee"],
        "deficiency_risk": ["vitamin_d", "iodine"],
        "notes": "High altitude = Vitamin D synthesis impaired; apples = quercetin; walnuts = omega-3"
    },
    "Uttarakhand": {
        "region": "North_Hill",
        "staple_grain": ["wheat", "mandua", "jhingora"],
        "common_dishes": ["kafuli", "aloo_gutuk", "chainsoo", "thechwani", "bhaang_ki_chutney"],
        "common_proteins": ["bhatt_dal", "gahat_dal", "chicken"],
        "common_vegetables": ["palak", "methi", "local_ferns", "turnip", "radish"],
        "common_fruits": ["malta", "kafal", "buransh", "apricot"],
        "dairy": ["dahi", "ghee", "makhan"],
        "deficiency_risk": ["iodine", "vitamin_d", "calcium"],
        "notes": "Mandua (finger millet) = calcium; gahat dal = kidney beans = iron; high altitude iodine risk"
    },
    "Delhi": {
        "region": "North_Urban",
        "staple_grain": ["wheat", "rice"],
        "common_dishes": ["chole_bhature", "butter_chicken", "dal_makhani", "paratha", "chaat"],
        "common_proteins": ["chicken", "dal", "paneer", "eggs"],
        "common_vegetables": ["aloo", "gobhi", "palak", "methi", "mooli"],
        "common_fruits": ["aam", "amrood", "kela", "kinnow"],
        "dairy": ["dahi", "lassi", "paneer"],
        "deficiency_risk": ["vitamin_d", "zinc"],
        "notes": "Urban processed food = micronutrient poor; pollution = Vitamin D impaired synthesis; high stress"
    },
    "Madhya_Pradesh": {
        "region": "Central",
        "staple_grain": ["wheat", "jowar", "rice"],
        "common_dishes": ["daal_bafla", "mawa_bati", "poha", "bhutte_ki_kees", "chakki_ki_shaak"],
        "common_proteins": ["dal_arhar", "chicken", "goat"],
        "common_vegetables": ["aloo", "baingan", "parwal", "saag"],
        "common_fruits": ["aam", "ber", "amrood", "kela"],
        "dairy": ["dahi", "ghee"],
        "deficiency_risk": ["iron", "folate", "vitamin_a"],
        "notes": "Tribal areas = high malnutrition; bhutte ki kees = corn = good vitamin B; poha = iron (if fortified)"
    },
    "Chhattisgarh": {
        "region": "Central",
        "staple_grain": ["rice", "maize", "kutki_millet"],
        "common_dishes": ["chila", "aamat", "muthia", "farra", "bore_baasi"],
        "common_proteins": ["small_fish", "forest_mushrooms", "dal"],
        "common_vegetables": ["forest_greens", "bamboo_shoots", "colocasia", "raw_mango"],
        "common_fruits": ["mahua", "ber", "jackfruit", "mango"],
        "dairy": ["minimal"],
        "deficiency_risk": ["vitamin_a", "iron", "iodine", "calcium"],
        "notes": "Tribal regions = high burden; bore baasi (fermented rice) = probiotic; forest foods = diverse"
    },
    "Jammu_Kashmir": {
        "region": "North_Hill",
        "staple_grain": ["rice", "maize"],
        "common_dishes": ["rogan_josh", "yakhni", "dum_aloo", "haakh", "modur_pulao", "sheermal"],
        "common_proteins": ["mutton", "chicken", "fish_trout", "paneer"],
        "common_vegetables": ["haakh_greens", "nadru_lotus_stem", "turnip", "collard"],
        "common_fruits": ["apple", "walnut", "cherry", "apricot", "saffron"],
        "dairy": ["noon_chai", "dahi"],
        "deficiency_risk": ["vitamin_d", "iodine"],
        "notes": "Kashmiri saffron = antioxidants; walnuts = omega-3; haakh = greens = folate; high altitude Vit D risk"
    },
    "Sikkim": {
        "region": "Northeast",
        "staple_grain": ["rice", "corn", "millet"],
        "common_dishes": ["momo", "thukpa", "gundruk_soup", "chhurpi", "phagshapa"],
        "common_proteins": ["pork", "chicken", "yak_cheese_chhurpi", "fish"],
        "common_vegetables": ["gundruk_fermented_greens", "bamboo_shoots", "fern", "nettle"],
        "common_fruits": ["large_cardamom", "mandarin", "buckwheat"],
        "dairy": ["chhurpi", "yak_butter"],
        "deficiency_risk": ["vitamin_d", "iodine"],
        "notes": "Chhurpi = unique hard cheese = high calcium; gundruk = fermented = probiotics + iron"
    },
    "Tripura": {
        "region": "Northeast",
        "staple_grain": ["rice"],
        "common_dishes": ["berma_chutney", "wahan_mosdeng", "chakhwi", "gudok"],
        "common_proteins": ["fermented_fish_berma", "pork", "chicken", "bamboo_fish"],
        "common_vegetables": ["bamboo_shoots", "banana_flower", "wild_greens", "colocasia"],
        "common_fruits": ["pineapple", "jackfruit", "banana"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "vitamin_d", "iodine"],
        "notes": "Fermented fish = B12; bamboo shoots = low calorie micronutrient dense"
    },
    "Mizoram": {
        "region": "Northeast",
        "staple_grain": ["rice"],
        "common_dishes": ["bai", "sawhchiar", "vawksa_rep", "bamboo_shoot_fry"],
        "common_proteins": ["pork", "fish", "chicken", "fermented_pork"],
        "common_vegetables": ["bamboo_shoots", "wild_greens", "banana_flower", "squash"],
        "common_fruits": ["pineapple", "passion_fruit", "banana"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "iodine"],
        "notes": "Diverse forest ingredients; low dairy = calcium risk; high fermented foods"
    },
    "Arunachal_Pradesh": {
        "region": "Northeast",
        "staple_grain": ["rice", "millet", "maize"],
        "common_dishes": ["pika_pila", "ngatok", "lukter", "apong_rice_beer"],
        "common_proteins": ["fish", "pork", "chicken", "mithun_beef", "insects"],
        "common_vegetables": ["fern", "bamboo_shoots", "colocasia", "wild_greens"],
        "common_fruits": ["kiwi", "passion_fruit", "banana", "citrus"],
        "dairy": ["minimal"],
        "deficiency_risk": ["calcium", "iodine", "vitamin_d"],
        "notes": "Most diverse tribal food in India; insects = B12 + iron + zinc; low dairy"
    },
}

DEFICIENCY_TO_SYMPTOMS = {
    "vitamin_d": {
        "symptoms": ["bone_pain", "muscle_weakness", "fatigue", "depression", "frequent_infections", "back_pain", "hair_loss", "slow_wound_healing"],
        "visual_signs": {"nail": ["brittle_nails"], "eye": ["none"], "tongue": ["none"], "skin": ["pale_skin"]},
        "blood_test": "25-OH Vitamin D < 20 ng/mL",
        "rda_india": "600 IU/day (ICMR 2020)",
        "food_sources_india": ["fish_mackerel", "egg_yolk", "mushroom_sunlight_dried", "fortified_milk"],
        "prevalence_india": "70-90% deficient (NMHS 2023)",
    },
    "iron": {
        "symptoms": ["fatigue", "pallor", "breathlessness", "cold_hands_feet", "headache", "brittle_nails", "pica", "restless_legs"],
        "visual_signs": {"nail": ["koilonychia_spoon_nails", "pale_nails", "brittle"], "eye": ["conjunctival_pallor"], "tongue": ["smooth_glossy_tongue", "atrophic_glossitis"], "skin": ["pallor"]},
        "blood_test": "Hb < 12 g/dL women, < 13 g/dL men; serum ferritin < 12 ug/L",
        "rda_india": "17 mg/day men, 21 mg/day women (ICMR)",
        "food_sources_india": ["lotus_seeds", "garden_cress", "amaranth_leaves", "horse_gram", "bajra", "ragi"],
        "prevalence_india": "53% women, 20% men anemic (NFHS-5)",
    },
    "vitamin_b12": {
        "symptoms": ["fatigue", "numbness_tingling", "memory_issues", "depression", "balance_problems", "sore_tongue", "mouth_ulcers"],
        "visual_signs": {"nail": ["pale_nails"], "eye": ["optic_neuropathy_severe"], "tongue": ["hunter_glossitis", "beef_red_tongue"], "skin": ["hyperpigmentation_knuckles"]},
        "blood_test": "Serum B12 < 200 pg/mL",
        "rda_india": "1.2 mcg/day (ICMR)",
        "food_sources_india": ["curd", "paneer", "fish", "eggs", "milk", "fortified_cereals"],
        "prevalence_india": "47% vegetarians deficient (AIIMS study)",
    },
    "zinc": {
        "symptoms": ["hair_loss", "slow_wound_healing", "loss_of_taste_smell", "skin_rashes", "frequent_infections", "eye_inflammation", "white_spots_nails"],
        "visual_signs": {"nail": ["white_spots_leukonychia", "brittle"], "eye": ["night_blindness", "photophobia"], "tongue": ["smooth_tongue", "taste_loss"], "skin": ["acrodermatitis_enteropathica_rash"]},
        "blood_test": "Serum zinc < 70 mcg/dL",
        "rda_india": "12 mg/day men, 10 mg/day women (ICMR)",
        "food_sources_india": ["pumpkin_seeds", "sesame", "cashew", "chickpeas", "oyster", "egg"],
        "prevalence_india": "25% population at risk",
    },
    "calcium": {
        "symptoms": ["muscle_cramps", "numbness_tingling_face", "brittle_nails", "dental_problems", "bone_fractures", "insomnia"],
        "visual_signs": {"nail": ["brittle_ridged_nails"], "eye": ["none"], "tongue": ["none"], "skin": ["dry_skin"]},
        "blood_test": "Serum Ca < 8.5 mg/dL (hypocalcemia)",
        "rda_india": "600 mg/day adults (ICMR)",
        "food_sources_india": ["ragi", "sesame_seeds", "amaranth", "milk", "curd", "small_fish_with_bones"],
        "prevalence_india": "Average intake 429 mg/day vs 600 RDA",
    },
    "magnesium": {
        "symptoms": ["muscle_cramps", "anxiety", "insomnia", "irregular_heartbeat", "constipation", "headache", "fatigue"],
        "visual_signs": {"nail": ["none"], "eye": ["eye_twitching"], "tongue": ["none"], "skin": ["none"]},
        "blood_test": "Serum Mg < 1.8 mg/dL",
        "rda_india": "340 mg/day men, 310 mg/day women",
        "food_sources_india": ["bajra", "jowar", "groundnut", "rajma", "spinach", "dark_chocolate"],
        "prevalence_india": "Estimated 60% suboptimal intake",
    },
    "vitamin_c": {
        "symptoms": ["bleeding_gums", "slow_wound_healing", "fatigue", "joint_pain", "rough_dry_skin", "easy_bruising", "scurvy"],
        "visual_signs": {"nail": ["corkscrew_hairs_nails", "splinter_hemorrhages"], "eye": ["subconjunctival_hemorrhage"], "tongue": ["swollen_bleeding_gums"], "skin": ["perifollicular_hemorrhage", "ecchymosis"]},
        "blood_test": "Plasma vitamin C < 0.2 mg/dL",
        "rda_india": "40 mg/day (ICMR)",
        "food_sources_india": ["amla_highest_753mg", "guava", "capsicum", "drumstick_leaves", "lemon", "tomato"],
        "prevalence_india": "Rural populations at risk especially winter",
    },
    "vitamin_a": {
        "symptoms": ["night_blindness", "dry_eyes", "frequent_infections", "dry_skin", "poor_growth_children"],
        "visual_signs": {"nail": ["none"], "eye": ["bitots_spots", "night_blindness", "xerophthalmia", "dry_conjunctiva"], "tongue": ["none"], "skin": ["follicular_hyperkeratosis", "dry_rough_skin"]},
        "blood_test": "Serum retinol < 20 mcg/dL",
        "rda_india": "600 mcg RAE/day men, 500 mcg women",
        "food_sources_india": ["carrot", "sweet_potato", "drumstick_leaves", "mango", "papaya", "ghee", "egg_yolk"],
        "prevalence_india": "62% children subclinical deficiency (NNMB)",
    },
    "folate": {
        "symptoms": ["fatigue", "mouth_ulcers", "sore_tongue", "pale_skin", "shortness_of_breath", "neural_tube_defects_pregnancy"],
        "visual_signs": {"nail": ["pale_nails"], "eye": ["conjunctival_pallor"], "tongue": ["red_smooth_tongue", "glossitis"], "skin": ["pallor"]},
        "blood_test": "Serum folate < 3 ng/mL",
        "rda_india": "200 mcg/day; 400 mcg pregnancy",
        "food_sources_india": ["methi", "spinach", "sprouted_moong", "drumstick", "beetroot", "orange"],
        "prevalence_india": "High in pregnant women; 37% antenatal women",
    },
    "iodine": {
        "symptoms": ["goiter", "fatigue", "weight_gain", "cold_intolerance", "hair_loss", "dry_skin", "brain_fog"],
        "visual_signs": {"nail": ["brittle_nails"], "eye": ["puffy_eyes"], "tongue": ["enlarged_tongue_macroglossia"], "skin": ["dry_skin", "puffy_face"]},
        "blood_test": "Urine iodine < 100 mcg/L",
        "rda_india": "150 mcg/day adults",
        "food_sources_india": ["iodized_salt", "fish", "milk", "eggs", "seaweed"],
        "prevalence_india": "350 million at risk; many still use non-iodized salt",
    },
    "omega3": {
        "symptoms": ["dry_skin", "dry_eyes", "brain_fog", "depression", "joint_pain", "poor_memory", "dry_brittle_hair"],
        "visual_signs": {"nail": ["dry_brittle_nails"], "eye": ["dry_eyes", "decreased_visual_acuity"], "tongue": ["none"], "skin": ["dry_flaky_skin", "eczema_like"]},
        "blood_test": "Omega-3 index < 4%",
        "rda_india": "1.6 g ALA men, 1.1 g ALA women + 250 mg EPA+DHA",
        "food_sources_india": ["flaxseeds", "walnuts", "mustard_oil", "fish_mackerel_rohu", "hemp_seeds"],
        "prevalence_india": "Most Indians below optimal; vegetarians high risk",
    },
}

OUT_DIR = "/home/abhay/Downloads/medical/balanceai/data/state_diets"
os.makedirs(OUT_DIR, exist_ok=True)

with open(f"{OUT_DIR}/state_diet_database.json", "w", encoding="utf-8") as f:
    json.dump(STATE_DIETS, f, indent=2, ensure_ascii=False)

with open(f"{OUT_DIR}/deficiency_symptom_mapping.json", "w", encoding="utf-8") as f:
    json.dump(DEFICIENCY_TO_SYMPTOMS, f, indent=2, ensure_ascii=False)

print(f"States saved: {len(STATE_DIETS)}")
print(f"Deficiencies mapped: {len(DEFICIENCY_TO_SYMPTOMS)}")
print("Files written to:", OUT_DIR)
