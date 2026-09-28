"""
Inference module — loaded by FastAPI to serve predictions.
Input: a dict of dietary intake + demographics
Output: per-nutrient deficiency probability + classification
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, Optional

MODEL_DIR = Path(__file__).parent / "models"

_models      = {}
_feature_cols = []
_thresholds  = {}
_loaded      = False


def _load():
    global _models, _feature_cols, _thresholds, _loaded
    if _loaded:
        return
    _feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
    _thresholds   = joblib.load(MODEL_DIR / "thresholds.pkl")
    for pkl in MODEL_DIR.glob("*.pkl"):
        nutrient = pkl.stem
        if nutrient in ("feature_cols", "thresholds"):
            continue
        obj = joblib.load(pkl)
        if isinstance(obj, dict) and "pipeline" in obj:
            _models[nutrient] = (obj["pipeline"], obj.get("leak_cols", []))
        else:
            _models[nutrient] = (obj, [])
    _loaded = True


def predict_deficiencies(
    age: float,
    female: int,
    bmi: Optional[float],
    # Dietary intake (mg/µg/g per day)
    d_iron: Optional[float] = None,
    d_calcium: Optional[float] = None,
    d_zinc: Optional[float] = None,
    d_vitamin_b12: Optional[float] = None,
    d_folate: Optional[float] = None,
    d_vitamin_d: Optional[float] = None,
    d_magnesium: Optional[float] = None,
    d_potassium: Optional[float] = None,
    d_vitamin_b6: Optional[float] = None,
    d_vitamin_e: Optional[float] = None,
    d_vitamin_c: Optional[float] = None,
    d_vitamin_a: Optional[float] = None,
    d_vitamin_b1: Optional[float] = None,
    d_vitamin_b2: Optional[float] = None,
    d_vitamin_b3: Optional[float] = None,
    d_vitamin_k: Optional[float] = None,
    d_phosphorus: Optional[float] = None,
    d_selenium: Optional[float] = None,
    d_manganese: Optional[float] = None,
    d_copper: Optional[float] = None,
    d_omega3: Optional[float] = None,
    d_kcal: Optional[float] = 2000,
) -> Dict[str, Dict]:
    _load()

    row = {
        "age":          age,
        "female":       float(female),
        "bmi":          bmi,
        "d_iron":       d_iron,
        "d_calcium":    d_calcium,
        "d_zinc":       d_zinc,
        "d_vitamin_b12": d_vitamin_b12,
        "d_folate":     d_folate,
        "d_vitamin_d":  d_vitamin_d,
        "d_magnesium":  d_magnesium,
        "d_potassium":  d_potassium,
        "d_vitamin_b6": d_vitamin_b6,
        "d_vitamin_e":  d_vitamin_e,
        "d_vitamin_c":  d_vitamin_c,
        "d_vitamin_a":  d_vitamin_a,
        "d_vitamin_b1": d_vitamin_b1,
        "d_vitamin_b2": d_vitamin_b2,
        "d_vitamin_b3": d_vitamin_b3,
        "d_vitamin_k":  d_vitamin_k,
        "d_phosphorus": d_phosphorus,
        "d_selenium":   d_selenium,
        "d_manganese":  d_manganese,
        "d_copper":     d_copper,
        "d_omega3":     d_omega3,
        "d_kcal":       d_kcal or 2000,
        "d_epa":        None,
        "d_dha":        None,
        "d_protein":    None,
        "d_carb":       None,
        "d_fat":        None,
    }

    # Per-2000-kcal normalised features
    kcal = row["d_kcal"] or 2000
    for key in list(row.keys()):
        if key.startswith("d_") and key not in ("d_kcal", "d_epa", "d_dha"):
            row[f"{key}_per2k"] = (row[key] / kcal * 2000) if row[key] is not None else None

    X = pd.DataFrame([row])
    # Align to training feature columns — fill missing with NaN
    for col in _feature_cols:
        if col not in X.columns:
            X[col] = np.nan
    X = X[_feature_cols]

    out = {}
    for nutrient, (pipe, leak_cols) in _models.items():
        Xn = X.drop(columns=[c for c in leak_cols if c in X.columns])
        prob = float(pipe.predict_proba(Xn)[0, 1])
        thr  = _thresholds.get(nutrient, 0.5)
        out[nutrient] = {
            "probability": round(prob, 4),
            "deficient":   prob >= thr,
            "threshold":   thr,
        }
    return out


if __name__ == "__main__":
    result = predict_deficiencies(
        age=32, female=1, bmi=22,
        d_iron=8, d_calcium=600, d_zinc=7,
        d_vitamin_b12=1.5, d_folate=200, d_vitamin_d=3,
        d_magnesium=280, d_kcal=1800,
    )
    print("\nSample prediction (32F, low iron diet):")
    for n, v in sorted(result.items(), key=lambda x: -x[1]["probability"]):
        flag = "⚠ DEFICIENT" if v["deficient"] else "   ok"
        print(f"  {n:20s}: {v['probability']:.3f}  {flag}")
