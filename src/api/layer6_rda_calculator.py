"""
Layer 6 — Personalized Daily Nutrition & Calorie Requirements
Sources:
  - ICMR-NIN 2020 "Nutrient Requirements for Indians" (primary for India)
  - WHO/FAO 2004 "Vitamin and Mineral Requirements in Human Nutrition"
  - IOM/USDA DRI 2019-2023
  - Mifflin-St Jeor equation for BMR (most validated)
"""
from dataclasses import dataclass, field
from typing import Literal, Optional

ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
Gender        = Literal["male", "female"]
LifeStage     = Literal["normal", "pregnant", "lactating"]

PAL = {
    "sedentary":   1.20,
    "light":       1.375,
    "moderate":    1.55,
    "active":      1.725,
    "very_active": 1.90,
}


@dataclass
class NutritionRequirements:
    bmr_kcal: float;  tdee_kcal: float
    protein_g: float; carbs_g: float; fat_g: float; fiber_g: float; water_ml: float
    vitamin_a_ug: float; vitamin_d_ug: float; vitamin_e_mg: float; vitamin_k_ug: float
    vitamin_c_mg: float; vitamin_b1_mg: float; vitamin_b2_mg: float
    vitamin_b3_mg: float; vitamin_b6_mg: float; vitamin_b12_ug: float; folate_ug: float
    calcium_mg: float; phosphorus_mg: float; magnesium_mg: float; iron_mg: float
    zinc_mg: float; selenium_ug: float; copper_mg: float; potassium_mg: float
    iodine_ug: float; omega3_mg: float
    activity_level: str; life_stage: str
    notes: list = field(default_factory=list)


def calculate_requirements(
    age: int, gender: Gender, weight_kg: float, height_cm: float,
    activity_level: ActivityLevel = "moderate", life_stage: LifeStage = "normal",
) -> NutritionRequirements:

    notes = []
    bmr = (10*weight_kg + 6.25*height_cm - 5*age + 5) if gender=="male" else (10*weight_kg + 6.25*height_cm - 5*age - 161)
    tdee = bmr * PAL[activity_level]
    if life_stage == "pregnant":  tdee += 350; notes.append("Pregnancy: +350 kcal/day")
    if life_stage == "lactating": tdee += 600; notes.append("Lactation: +600 kcal/day")

    pg = {"sedentary":0.80,"light":0.90,"moderate":1.00,"active":1.20,"very_active":1.50}[activity_level]
    if age >= 60: pg = max(pg, 1.10); notes.append("Age ≥60: min 1.1g/kg protein")
    if life_stage == "pregnant":  pg += 0.25
    if life_stage == "lactating": pg += 0.30
    protein_g = weight_kg * pg
    rem = tdee - protein_g * 4
    carbs_g = (rem * 0.60) / 4;  fat_g = (rem * 0.27) / 9
    fiber_g = min(round(40 * tdee / 2000, 1), 50)
    water_ml = weight_kg * 35 + (500 if activity_level in ("active","very_active") else 0)

    vitamin_a = 600;
    if life_stage=="pregnant": vitamin_a=800
    if life_stage=="lactating": vitamin_a=950

    vitamin_d = 20.0 if age>=60 else 15.0
    if age>=60: notes.append("Age ≥60: Vitamin D 20µg (800 IU)")

    vitamin_e = (10 if gender=="male" else 8) + (2 if activity_level in ("active","very_active") else 0)
    vitamin_k = (65 if gender=="male" else 55) + (10 if age>=60 else 0)

    vitamin_c = {"normal":65,"pregnant":80,"lactating":115}[life_stage] + (15 if activity_level in ("active","very_active") else 0)

    vitamin_b1 = max(0.5*tdee/1000, 1.0 if gender=="female" else 1.2)
    vitamin_b2 = max(0.6*tdee/1000, 1.1 if gender=="female" else 1.4)
    vitamin_b3 = max(6.6*tdee/1000, 11.0 if gender=="female" else 14.0)

    vitamin_b6 = 2.2 if life_stage=="pregnant" else 2.0 if life_stage=="lactating" else (1.7 if age>=51 else 1.6)
    vitamin_b12 = 1.9 if life_stage=="pregnant" else 2.0 if (life_stage=="lactating" or age>=60) else 1.2
    if age>=60: notes.append("Age ≥60: B12 2.0µg (reduced absorption)")
    folate = {"normal":200,"pregnant":500,"lactating":300}[life_stage]

    calcium = (1200 if life_stage in ("pregnant","lactating") else 1000 if (age<=18 or age>50) else 800)
    phosphorus = 1200 if life_stage!="normal" else 800
    magnesium = (340 if gender=="male" else 310) + (10 if age>=30 else 0) + (50 if life_stage!="normal" else 0) + (30 if activity_level in ("active","very_active") else 0)

    if gender=="male":
        iron = 11.0 if age>=60 else 17.0
    else:
        iron = 35.0 if life_stage=="pregnant" else 21.0 if (life_stage=="lactating" or age<=50) else 11.0
        if activity_level in ("active","very_active") and age<=50:
            iron += 3; notes.append("High activity female: +3mg iron")

    zinc = (12 if gender=="male" else 10) + (4 if life_stage!="normal" else 0) + (1.5 if activity_level in ("active","very_active") else 0)
    selenium = 40 if life_stage=="normal" else (65 if life_stage=="pregnant" else 75)
    copper = 2.5 if life_stage!="normal" else 2.0
    potassium = 4000 if activity_level in ("active","very_active") else 3500
    iodine = 200 if life_stage!="normal" else 150
    omega3 = ((1600 if gender=="male" else 1100) + 400) if life_stage=="normal" else 2600
    if activity_level in ("active","very_active"): omega3 += 200

    r = lambda v, d=1: round(v * 10**d) / 10**d
    return NutritionRequirements(
        bmr_kcal=r(bmr), tdee_kcal=r(tdee),
        protein_g=r(protein_g), carbs_g=r(carbs_g), fat_g=r(fat_g),
        fiber_g=fiber_g, water_ml=round(water_ml),
        vitamin_a_ug=vitamin_a, vitamin_d_ug=vitamin_d, vitamin_e_mg=vitamin_e,
        vitamin_k_ug=vitamin_k, vitamin_c_mg=vitamin_c,
        vitamin_b1_mg=r(vitamin_b1,2), vitamin_b2_mg=r(vitamin_b2,2),
        vitamin_b3_mg=r(vitamin_b3), vitamin_b6_mg=vitamin_b6,
        vitamin_b12_ug=vitamin_b12, folate_ug=folate,
        calcium_mg=calcium, phosphorus_mg=phosphorus, magnesium_mg=magnesium,
        iron_mg=iron, zinc_mg=zinc, selenium_ug=selenium, copper_mg=copper,
        potassium_mg=potassium, iodine_ug=iodine, omega3_mg=omega3,
        activity_level=activity_level, life_stage=life_stage, notes=notes,
    )
