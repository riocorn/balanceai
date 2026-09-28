"""
ML-based nutrient deficiency prediction endpoint.
POST /nutrition/predict — returns per-nutrient deficiency probabilities
trained on NHANES 2017-2018 (n=5856 adults, AUC mean 0.873).
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "ml_training"))

from inference_service import predict_deficiencies  # type: ignore

router = APIRouter(prefix="/nutrition", tags=["Nutrition ML"])


class NutritionPredictRequest(BaseModel):
    age: float
    female: int                     # 1 = female, 0 = male
    bmi: Optional[float] = None
    # Daily dietary intake (mg or µg as noted; None = not available)
    d_iron: Optional[float]       = None   # mg
    d_calcium: Optional[float]    = None   # mg
    d_zinc: Optional[float]       = None   # mg
    d_vitamin_b12: Optional[float]= None   # µg
    d_folate: Optional[float]     = None   # µg DFE
    d_vitamin_d: Optional[float]  = None   # µg
    d_magnesium: Optional[float]  = None   # mg
    d_potassium: Optional[float]  = None   # mg
    d_vitamin_b6: Optional[float] = None   # mg
    d_vitamin_e: Optional[float]  = None   # mg
    d_vitamin_c: Optional[float]  = None   # mg
    d_vitamin_a: Optional[float]  = None   # µg RAE
    d_vitamin_b1: Optional[float] = None   # mg
    d_vitamin_b2: Optional[float] = None   # mg
    d_vitamin_b3: Optional[float] = None   # mg NE
    d_vitamin_k: Optional[float]  = None   # µg
    d_phosphorus: Optional[float] = None   # mg
    d_selenium: Optional[float]   = None   # µg
    d_copper: Optional[float]     = None   # mg
    d_omega3: Optional[float]     = None   # mg total n-3 (ALA+EPA+DHA)
    d_kcal: Optional[float]       = 2000


@router.post("/predict")
async def predict_nutrition(req: NutritionPredictRequest):
    try:
        result = predict_deficiencies(**req.model_dump())
        return JSONResponse(content={
            "predictions": result,
            "model": "xgboost-nhanes-2017",
            "n_train": 5856,
            "mean_auc": 0.873,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
