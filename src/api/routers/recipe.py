"""
Supplement Report API
POST /api/supplement/report -> per-nutrient "without supplement" vs "with supplement"
comparison + real ICMR-NIN/WHO/AIIMS-protocol supplement recommendations.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # src/api/ — layer6_rda_calculator

from layer6_rda_calculator import calculate_requirements

router = APIRouter(prefix="/api/supplement", tags=["Supplement Report"])

# Real whole-food ingredient database (163 ingredients, ICMR-NIN/USDA-sourced,
# built in the Dish Maker AI pipeline) — used to show a genuine real food source
# per deficient nutrient alongside the supplement, exactly like balance.it lists
# real food ingredients (turkey, sweet potato) together with the supplement line.
_BALANCEAI_ROOT = Path(__file__).parent.parent.parent.parent
_ING_MASTER_PATH = _BALANCEAI_ROOT / "data" / "ingredient_master.json"
_WHOLE_FOOD_CATEGORIES = {"Dal", "Vegetable", "Fruit", "Grain", "Meat", "Dairy", "Nuts", "Dry Fruits"}
try:
    _ING_MASTER = json.loads(_ING_MASTER_PATH.read_text())["ingredients"]
except FileNotFoundError:
    _ING_MASTER = {}


def _best_food_source(nutrient_key: str):
    best_id, best_val = None, 0.0
    for iid, info in _ING_MASTER.items():
        if info.get("category") not in _WHOLE_FOOD_CATEGORIES:
            continue
        val = info.get("per_100g_raw", {}).get(nutrient_key, 0.0)
        if val > best_val:
            best_id, best_val = iid, val
    if not best_id:
        return None
    display = best_id.replace("_", " ").title()
    return {"name": display, "amount_g": 100, "per_100g_value": round(best_val, 2)}


class AIDeficiency(BaseModel):
    probability: float = Field(..., ge=0, le=1)
    deficient: bool
    threshold: float = 0.5


class ReportRequest(BaseModel):
    age: int = Field(..., ge=1, le=120)
    gender: Literal["male", "female"]
    weight_kg: float = Field(..., ge=20, le=250)
    height_cm: float = Field(..., ge=100, le=250)
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = "moderate"
    life_stage: Literal["normal", "pregnant", "lactating"] = "normal"
    deficiencies: Dict[str, AIDeficiency] = {}


SEVERITY_THRESHOLDS = {"severe": 0.85, "moderate": 0.70, "mild": 0.0}
MULTIPLIER = {"normal": 1.0, "mild": 1.5, "moderate": 2.0, "severe": 2.5}
UL = {
    "vitamin_a_ug": 3000, "vitamin_d_ug": 100, "vitamin_e_mg": 1000,
    "vitamin_c_mg": 2000, "vitamin_b3_mg": 35, "vitamin_b6_mg": 100,
    "folate_ug": 1000, "calcium_mg": 2500, "phosphorus_mg": 4000,
    "magnesium_mg": 350, "iron_mg": 45, "zinc_mg": 40, "selenium_ug": 400,
    "copper_mg": 10, "iodine_ug": 1100, "omega3_mg": 3000, "potassium_mg": 4700,
}
AI_TO_RDA = {
    "iron": "iron_mg", "calcium": "calcium_mg", "vitamin_d": "vitamin_d_ug",
    "folate": "folate_ug", "vitamin_b12": "vitamin_b12_ug", "vitamin_c": "vitamin_c_mg",
    "vitamin_a": "vitamin_a_ug", "vitamin_e": "vitamin_e_mg", "vitamin_k": "vitamin_k_ug",
    "vitamin_b1": "vitamin_b1_mg", "vitamin_b2": "vitamin_b2_mg", "vitamin_b3": "vitamin_b3_mg",
    "vitamin_b6": "vitamin_b6_mg", "magnesium": "magnesium_mg", "zinc": "zinc_mg",
    "selenium": "selenium_ug", "copper": "copper_mg", "potassium": "potassium_mg",
    "phosphorus": "phosphorus_mg", "omega3": "omega3_mg",
}
NUTRIENT_DISPLAY = {
    "iron": "Iron", "calcium": "Calcium", "vitamin_d": "Vitamin D", "folate": "Folate",
    "vitamin_b12": "Vitamin B12", "vitamin_c": "Vitamin C", "vitamin_a": "Vitamin A",
    "vitamin_e": "Vitamin E", "vitamin_k": "Vitamin K", "vitamin_b1": "Vitamin B1",
    "vitamin_b2": "Vitamin B2", "vitamin_b3": "Vitamin B3", "vitamin_b6": "Vitamin B6",
    "magnesium": "Magnesium", "zinc": "Zinc", "selenium": "Selenium", "copper": "Copper",
    "potassium": "Potassium", "phosphorus": "Phosphorus", "omega3": "Omega-3",
}
UNITS = {
    "iron_mg": "mg", "calcium_mg": "mg", "vitamin_d_ug": "µg", "folate_ug": "µg DFE",
    "vitamin_b12_ug": "µg", "vitamin_c_mg": "mg", "vitamin_a_ug": "µg RAE",
    "vitamin_e_mg": "mg", "vitamin_k_ug": "µg", "vitamin_b1_mg": "mg", "vitamin_b2_mg": "mg",
    "vitamin_b3_mg": "mg NE", "vitamin_b6_mg": "mg", "magnesium_mg": "mg", "zinc_mg": "mg",
    "selenium_ug": "µg", "copper_mg": "mg", "potassium_mg": "mg", "phosphorus_mg": "mg",
    "omega3_mg": "mg",
}

# Real WHO / ICMR-NIN / AIIMS-protocol oral repletion doses, by severity tier.
SUPPLEMENT_DB = {
    "vitamin_d": {
        "name": "Vitamin D3 (Cholecalciferol)",
        "moderate": {
            "dose": "1000–2000 IU/day (25–50 µg)",
            "form": "Soft-gel capsule / oral drops",
            "duration": "3–6 months, then reassess",
            "note": "Take with a fatty meal for absorption. Recheck 25-OH-D after 3 months.",
        },
        "severe": {
            "dose": "60,000 IU/week for 8–12 weeks (loading), then 1000–2000 IU/day maintenance",
            "form": "Sachet (e.g. Calcirol 60K) or injection",
            "duration": "Loading 8–12 weeks, then maintenance",
            "note": "Consult a doctor. Combine with calcium. Monitor serum calcium and 25-OH-D.",
        },
        "why_food_fails": "Indian vegetarian food provides <2.5 µg/day vs the 15 µg RDA. Sunlight is blocked by pollution and clothing.",
    },
    "vitamin_b12": {
        "name": "Methylcobalamin (Vitamin B12)",
        "moderate": {
            "dose": "500–1000 µg/day oral",
            "form": "Sublingual tablet (Mecobalamin 500) or oral tablet",
            "duration": "3–6 months",
            "note": "Sublingual absorption bypasses the gut — preferred for vegetarians.",
        },
        "severe": {
            "dose": "1000 µg/day oral, or 1000 µg IM injection 3×/week for 4 weeks then monthly",
            "form": "IM injection (hydroxocobalamin) or high-dose oral",
            "duration": "Until serum B12 >300 pmol/L, then maintenance",
            "note": "Neurological symptoms (tingling, weakness): IM is mandatory.",
        },
        "why_food_fails": "B12 exists only in animal products — vegetarians/vegans have zero food source.",
    },
    "iron": {
        "name": "Ferrous Sulfate / Ferrous Ascorbate",
        "moderate": {
            "dose": "60–120 mg elemental iron/day",
            "form": "Ferrous sulfate 200 mg tablet (~65 mg elemental iron)",
            "duration": "3–6 months",
            "note": "Take on an empty stomach or with vitamin C. Avoid tea/coffee within 2 hours.",
        },
        "severe": {
            "dose": "150–200 mg elemental iron/day oral; IV iron if oral is not tolerated",
            "form": "Ferrous ascorbate 100 mg + folic acid, or IV iron sucrose",
            "duration": "Until Hb normalises, plus 3 months to replete stores",
            "note": "Hb <7 g/dL: consider IV iron or transfusion. Always co-prescribe vitamin C.",
        },
        "why_food_fails": "Plant (non-heme) iron absorption is only 3–8% — phytates in dal/roti block it.",
    },
    "omega3": {
        "name": "Omega-3 (EPA + DHA)",
        "moderate": {
            "dose": "1 g EPA+DHA/day",
            "form": "Fish oil capsule, or algae-based DHA for vegetarians",
            "duration": "Ongoing",
            "note": "Vegetarians: use algae-based DHA. Take with meals.",
        },
        "severe": {
            "dose": "2–4 g EPA+DHA/day",
            "form": "Prescription-strength omega-3 or high-dose fish oil",
            "duration": "3 months, then reassess",
            "note": "Doses >3 g/day: consult a doctor if on blood thinners.",
        },
        "why_food_fails": "Indian vegetarian food provides only ALA (mustard oil, flaxseed); ALA→EPA/DHA conversion is under 8%.",
    },
    "iodine": {
        "name": "Potassium Iodide / Iodized Salt",
        "moderate": {
            "dose": "150–300 µg/day via iodized salt",
            "form": "Iodized table salt",
            "duration": "Ongoing",
            "note": "Do not overcook — iodine is lost at high heat.",
        },
        "severe": {
            "dose": "150–300 µg/day potassium iodide supplement",
            "form": "Potassium iodide tablet or Lugol's iodine drops",
            "duration": "Until TSH normalises",
            "note": "Goiter/hypothyroidism: an endocrinologist consult is mandatory.",
        },
        "why_food_fails": "Soil iodine is depleted across most of inland/Himalayan India; food alone provides <50 µg/day vs the 150 µg RDA.",
    },
    "folate": {
        "name": "Folic Acid",
        "moderate": None,
        "severe": {
            "dose": "5 mg/day folic acid",
            "form": "Folic acid 5 mg tablet",
            "duration": "4 months for correction; lifelong if malabsorption",
            "note": "Rule out B12 deficiency before treating folate alone.",
        },
        "why_food_fails": "Food provides at most ~350 µg/day; therapeutic 5000 µg/day is impossible from diet alone.",
    },
    "calcium": {
        "name": "Calcium Carbonate / Calcium Citrate",
        "moderate": None,
        "severe": {
            "dose": "500–1000 mg elemental calcium/day",
            "form": "Calcium carbonate 500 mg or calcium citrate (better absorption)",
            "duration": "Ongoing; reassess bone density at 1 year",
            "note": "Always combine with vitamin D3 for absorption.",
        },
        "why_food_fails": "No dairy / lactose intolerant diets rarely exceed 400–500 mg/day.",
    },
    "zinc": {
        "name": "Zinc Sulfate / Zinc Gluconate",
        "moderate": {"dose": "15 mg/day", "form": "Zinc gluconate tablet", "duration": "8–12 weeks",
                     "note": "Take away from calcium/iron supplements — they compete for absorption."},
        "severe": {"dose": "25–30 mg/day for 8–12 weeks", "form": "Zinc sulfate tablet", "duration": "8–12 weeks, then reassess",
                   "note": "Monitor copper with prolonged high-dose use."},
        "why_food_fails": "Phytates in cereal-heavy Indian diets reduce zinc bioavailability substantially.",
    },
}


def _deficiency_level(prob: float, thr: float) -> str:
    if prob < thr:
        return "normal"
    if prob < 0.70:
        return "mild"
    if prob < 0.85:
        return "moderate"
    return "severe"


@router.post("/report")
def get_supplement_report(req: ReportRequest):
    rda = calculate_requirements(
        age=req.age, gender=req.gender,
        weight_kg=req.weight_kg, height_cm=req.height_cm,
        activity_level=req.activity_level, life_stage=req.life_stage,
    )
    rda_dict = rda.__dict__

    rows = []
    for ai_key, rda_key in AI_TO_RDA.items():
        d = req.deficiencies.get(ai_key)
        prob = d.probability if d else 0.0
        thr = d.threshold if d else 0.5
        level = _deficiency_level(prob, thr)
        if level == "normal":
            continue

        rda_val = rda_dict.get(rda_key, 0)
        mult = MULTIPLIER[level]
        ideal = rda_val * mult
        ul = UL.get(rda_key)
        target = min(ideal, ul) if ul and ideal > ul else ideal
        requirement_range = f"{round(rda_val, 1)} to {round(ul, 1) if ul else 'No Max'}"

        # Honest estimate, not a lab measurement: probability of deficiency maps
        # to how far below the target the person's real status likely sits.
        without_supplement_pct = round((1 - prob) * 100, 1)

        db = SUPPLEMENT_DB.get(ai_key)
        rec = db.get(level) if db else None

        rows.append({
            "nutrient": ai_key,
            "display_name": NUTRIENT_DISPLAY.get(ai_key, ai_key),
            "unit": UNITS.get(rda_key, ""),
            "rda": round(rda_val, 2),
            "target": round(target, 2),
            "requirement_range": requirement_range,
            "deficiency_level": level,
            "probability": round(prob, 3),
            "without_supplement_pct": without_supplement_pct,
            "with_supplement_pct": 100.0,
            "supplement": ({
                "name": db["name"],
                "dose": rec["dose"], "form": rec["form"],
                "duration": rec["duration"], "note": rec["note"],
                "why_food_fails": db["why_food_fails"],
            } if rec else None),
            "food_source": _best_food_source(ai_key),
        })

    rows.sort(key=lambda r: r["without_supplement_pct"])

    return {
        "calories_kcal": rda.tdee_kcal,
        "deficiency_count": len(rows),
        "rows": rows,
    }
