"""
Personalized Today's Nutrition Target API
Combines: AI Model deficiency probabilities + Layer 6 RDA → today's targets
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from layer6_rda_calculator import calculate_requirements

router = APIRouter(prefix="/api/nutrition/targets", tags=["Personalized Targets"])

# UL caps (ICMR-NIN 2020 + IOM DRI)
UL = {
    "vitamin_a_ug":   3000.0,
    "vitamin_d_ug":   100.0,
    "vitamin_e_mg":   1000.0,
    "vitamin_c_mg":   2000.0,
    "vitamin_b3_mg":  35.0,
    "vitamin_b6_mg":  100.0,
    "folate_ug":      1000.0,
    "calcium_mg":     2500.0,
    "phosphorus_mg":  4000.0,
    "magnesium_mg":   350.0,
    "iron_mg":        45.0,
    "zinc_mg":        40.0,
    "selenium_ug":    400.0,
    "copper_mg":      10.0,
    "iodine_ug":      1100.0,
    "omega3_mg":      3000.0,
    "potassium_mg":   4700.0,   # WHO safe upper limit (kidney toxicity above)
    "vitamin_k_ug":   500.0,    # conservative cap (no official UL but excessive anticoagulation risk)
}

MULTIPLIER = {
    "normal":   1.0,
    "mild":     1.5,
    "moderate": 2.0,
    "severe":   2.5,
}

AI_TO_RDA = {
    "iron":        "iron_mg",
    "calcium":     "calcium_mg",
    "vitamin_d":   "vitamin_d_ug",
    "folate":      "folate_ug",
    "vitamin_b12": "vitamin_b12_ug",
    "vitamin_c":   "vitamin_c_mg",
    "vitamin_a":   "vitamin_a_ug",
    "vitamin_e":   "vitamin_e_mg",
    "vitamin_k":   "vitamin_k_ug",
    "vitamin_b1":  "vitamin_b1_mg",
    "vitamin_b2":  "vitamin_b2_mg",
    "vitamin_b3":  "vitamin_b3_mg",
    "vitamin_b6":  "vitamin_b6_mg",
    "magnesium":   "magnesium_mg",
    "zinc":        "zinc_mg",
    "selenium":    "selenium_ug",
    "copper":      "copper_mg",
    "potassium":   "potassium_mg",
    "phosphorus":  "phosphorus_mg",
    "omega3":      "omega3_mg",
    "iodine":      "iodine_ug",
}


class AIDeficiency(BaseModel):
    probability: float = Field(..., ge=0, le=1)
    deficient:   bool
    threshold:   float = 0.5


class TargetRequest(BaseModel):
    # User profile (for Layer 6)
    age:            int   = Field(..., ge=1, le=120)
    gender:         Literal["male", "female"]
    weight_kg:      float = Field(..., ge=20, le=250)
    height_cm:      float = Field(..., ge=100, le=250)
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = "moderate"
    life_stage:     Literal["normal", "pregnant", "lactating"] = "normal"

    # AI model output (Layer 1-5 fusion result)
    deficiencies: Dict[str, AIDeficiency] = {}


class NutrientTarget(BaseModel):
    rda:              float
    target:           float
    deficiency_level: str
    probability:      float
    multiplier:       float
    capped_at_ul:     bool
    needs_supplement: bool
    unit:             str


class TargetResponse(BaseModel):
    calories_kcal:  float
    protein_g:      NutrientTarget
    carbs_g:        NutrientTarget
    fat_g:          NutrientTarget
    fiber_g:        NutrientTarget
    vitamin_a_ug:   NutrientTarget
    vitamin_d_ug:   NutrientTarget
    vitamin_e_mg:   NutrientTarget
    vitamin_k_ug:   NutrientTarget
    vitamin_c_mg:   NutrientTarget
    vitamin_b1_mg:  NutrientTarget
    vitamin_b2_mg:  NutrientTarget
    vitamin_b3_mg:  NutrientTarget
    vitamin_b6_mg:  NutrientTarget
    vitamin_b12_ug: NutrientTarget
    folate_ug:      NutrientTarget
    calcium_mg:     NutrientTarget
    phosphorus_mg:  NutrientTarget
    magnesium_mg:   NutrientTarget
    iron_mg:        NutrientTarget
    zinc_mg:        NutrientTarget
    selenium_ug:    NutrientTarget
    copper_mg:      NutrientTarget
    potassium_mg:   NutrientTarget
    iodine_ug:      NutrientTarget
    omega3_mg:      NutrientTarget
    supplement_needed: list[str]


UNITS = {
    "protein_g":"g","carbs_g":"g","fat_g":"g","fiber_g":"g",
    "vitamin_a_ug":"µg RAE","vitamin_d_ug":"µg","vitamin_e_mg":"mg",
    "vitamin_k_ug":"µg","vitamin_c_mg":"mg","vitamin_b1_mg":"mg",
    "vitamin_b2_mg":"mg","vitamin_b3_mg":"mg NE","vitamin_b6_mg":"mg",
    "vitamin_b12_ug":"µg","folate_ug":"µg DFE","calcium_mg":"mg",
    "phosphorus_mg":"mg","magnesium_mg":"mg","iron_mg":"mg",
    "zinc_mg":"mg","selenium_ug":"µg","copper_mg":"mg",
    "potassium_mg":"mg","iodine_ug":"µg","omega3_mg":"mg",
}


def _level(prob: float, thr: float) -> str:
    if prob < thr:    return "normal"
    if prob < 0.70:   return "mild"
    if prob < 0.85:   return "moderate"
    return "severe"


def _make_target(rda_key: str, rda_val: float, ai_key: str, deficiencies: dict) -> NutrientTarget:
    d      = deficiencies.get(ai_key)
    prob   = d.probability if d else 0.0
    thr    = d.threshold   if d else 0.5
    level  = _level(prob, thr)
    mult   = MULTIPLIER[level]
    ideal  = rda_val * mult
    ul     = UL.get(rda_key)
    capped = ul is not None and ideal > ul
    target = ul if capped else ideal
    needs_supp = level == "severe" and capped

    return NutrientTarget(
        rda              = round(rda_val, 1),
        target           = round(target, 1),
        deficiency_level = level,
        probability      = round(prob, 3),
        multiplier       = mult,
        capped_at_ul     = capped,
        needs_supplement = needs_supp,
        unit             = UNITS.get(rda_key, ""),
    )


@router.post("/calculate", response_model=TargetResponse)
def calculate_targets(req: TargetRequest):
    rda = calculate_requirements(
        age=req.age, gender=req.gender,
        weight_kg=req.weight_kg, height_cm=req.height_cm,
        activity_level=req.activity_level, life_stage=req.life_stage,
    )

    defs = {k: v for k, v in req.deficiencies.items()}

    def t(rda_key: str, rda_val: float, ai_key: str):
        return _make_target(rda_key, rda_val, ai_key, defs)

    targets = TargetResponse(
        calories_kcal  = rda.tdee_kcal,
        protein_g      = t("protein_g",      rda.protein_g,      "protein"),
        carbs_g        = t("carbs_g",         rda.carbs_g,         "carbs"),
        fat_g          = t("fat_g",           rda.fat_g,           "fat"),
        fiber_g        = t("fiber_g",         rda.fiber_g,         "fiber"),
        vitamin_a_ug   = t("vitamin_a_ug",    rda.vitamin_a_ug,    "vitamin_a"),
        vitamin_d_ug   = t("vitamin_d_ug",    rda.vitamin_d_ug,    "vitamin_d"),
        vitamin_e_mg   = t("vitamin_e_mg",    rda.vitamin_e_mg,    "vitamin_e"),
        vitamin_k_ug   = t("vitamin_k_ug",    rda.vitamin_k_ug,    "vitamin_k"),
        vitamin_c_mg   = t("vitamin_c_mg",    rda.vitamin_c_mg,    "vitamin_c"),
        vitamin_b1_mg  = t("vitamin_b1_mg",   rda.vitamin_b1_mg,   "vitamin_b1"),
        vitamin_b2_mg  = t("vitamin_b2_mg",   rda.vitamin_b2_mg,   "vitamin_b2"),
        vitamin_b3_mg  = t("vitamin_b3_mg",   rda.vitamin_b3_mg,   "vitamin_b3"),
        vitamin_b6_mg  = t("vitamin_b6_mg",   rda.vitamin_b6_mg,   "vitamin_b6"),
        vitamin_b12_ug = t("vitamin_b12_ug",  rda.vitamin_b12_ug,  "vitamin_b12"),
        folate_ug      = t("folate_ug",        rda.folate_ug,        "folate"),
        calcium_mg     = t("calcium_mg",       rda.calcium_mg,       "calcium"),
        phosphorus_mg  = t("phosphorus_mg",    rda.phosphorus_mg,    "phosphorus"),
        magnesium_mg   = t("magnesium_mg",     rda.magnesium_mg,     "magnesium"),
        iron_mg        = t("iron_mg",          rda.iron_mg,          "iron"),
        zinc_mg        = t("zinc_mg",          rda.zinc_mg,          "zinc"),
        selenium_ug    = t("selenium_ug",      rda.selenium_ug,      "selenium"),
        copper_mg      = t("copper_mg",        rda.copper_mg,        "copper"),
        potassium_mg   = t("potassium_mg",     rda.potassium_mg,     "potassium"),
        iodine_ug      = t("iodine_ug",        rda.iodine_ug,        "iodine"),
        omega3_mg      = t("omega3_mg",        rda.omega3_mg,        "omega3"),
        supplement_needed=[],
    )

    targets.supplement_needed = [
        k for k, v in targets.__dict__.items()
        if isinstance(v, NutrientTarget) and v.needs_supplement
    ]

    return targets
