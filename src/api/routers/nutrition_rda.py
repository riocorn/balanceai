"""
Layer 6 API — Personalized Daily Nutrition Requirements
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from layer6_rda_calculator import calculate_requirements

router = APIRouter(prefix="/api/nutrition/rda", tags=["Layer 6 - RDA"])


class RDARequest(BaseModel):
    age: int                    = Field(..., ge=1,   le=120)
    gender: Literal["male", "female"]
    weight_kg: float            = Field(..., ge=20,  le=250)
    height_cm: float            = Field(..., ge=100, le=250)
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = "moderate"
    life_stage: Literal["normal", "pregnant", "lactating"] = "normal"


class RDAResponse(BaseModel):
    # Energy
    bmr_kcal: float
    tdee_kcal: float

    # Macros
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    water_ml: float

    # Vitamins
    vitamin_a_ug: float
    vitamin_d_ug: float
    vitamin_e_mg: float
    vitamin_k_ug: float
    vitamin_c_mg: float
    vitamin_b1_mg: float
    vitamin_b2_mg: float
    vitamin_b3_mg: float
    vitamin_b6_mg: float
    vitamin_b12_ug: float
    folate_ug: float

    # Minerals
    calcium_mg: float
    phosphorus_mg: float
    magnesium_mg: float
    iron_mg: float
    zinc_mg: float
    selenium_ug: float
    copper_mg: float
    potassium_mg: float
    iodine_ug: float

    # Omega-3
    omega3_mg: float

    # Meta
    activity_level: str
    life_stage: str
    notes: list[str]

    # Vitamin D in IU for display
    vitamin_d_iu: float


@router.post("/calculate", response_model=RDAResponse)
def calculate_rda(req: RDARequest):
    if req.life_stage in ("pregnant", "lactating") and req.gender == "male":
        raise HTTPException(status_code=400, detail="Pregnant/lactating only applicable to female")

    r = calculate_requirements(
        age=req.age,
        gender=req.gender,
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        activity_level=req.activity_level,
        life_stage=req.life_stage,
    )
    return RDAResponse(
        bmr_kcal      = r.bmr_kcal,
        tdee_kcal     = r.tdee_kcal,
        protein_g     = r.protein_g,
        carbs_g       = r.carbs_g,
        fat_g         = r.fat_g,
        fiber_g       = r.fiber_g,
        water_ml      = r.water_ml,
        vitamin_a_ug  = r.vitamin_a_ug,
        vitamin_d_ug  = r.vitamin_d_ug,
        vitamin_d_iu  = round(r.vitamin_d_ug * 40, 0),
        vitamin_e_mg  = r.vitamin_e_mg,
        vitamin_k_ug  = r.vitamin_k_ug,
        vitamin_c_mg  = r.vitamin_c_mg,
        vitamin_b1_mg = r.vitamin_b1_mg,
        vitamin_b2_mg = r.vitamin_b2_mg,
        vitamin_b3_mg = r.vitamin_b3_mg,
        vitamin_b6_mg = r.vitamin_b6_mg,
        vitamin_b12_ug= r.vitamin_b12_ug,
        folate_ug     = r.folate_ug,
        calcium_mg    = r.calcium_mg,
        phosphorus_mg = r.phosphorus_mg,
        magnesium_mg  = r.magnesium_mg,
        iron_mg       = r.iron_mg,
        zinc_mg       = r.zinc_mg,
        selenium_ug   = r.selenium_ug,
        copper_mg     = r.copper_mg,
        potassium_mg  = r.potassium_mg,
        iodine_ug     = r.iodine_ug,
        omega3_mg     = r.omega3_mg,
        activity_level= r.activity_level,
        life_stage    = r.life_stage,
        notes         = r.notes,
    )
