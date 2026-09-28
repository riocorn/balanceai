"""
Fusion Inference — 5 layer signals → trained model → deficiency prediction
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, Optional

MODEL_DIR = Path(__file__).parent / "fusion_models"

_models    = {}
_features  = []
_thresholds= {}
_loaded    = False

FEATURES = ["blood_sig", "symptom_sig", "food_sig", "history_sig", "visual_sig", "age", "female", "bmi"]


def _load():
    global _models, _features, _thresholds, _loaded
    if _loaded: return
    _features   = joblib.load(MODEL_DIR / "feature_cols.pkl")
    _thresholds = joblib.load(MODEL_DIR / "thresholds.pkl")
    for pkl in MODEL_DIR.glob("*.pkl"):
        n = pkl.stem
        if n in ("feature_cols", "thresholds"): continue
        obj = joblib.load(pkl)
        if isinstance(obj, dict) and "pipeline" in obj:
            _models[n] = (obj["pipeline"], obj["features"])
        else:
            _models[n] = (obj, FEATURES)
    _loaded = True


def fuse_signals(
    age: float,
    female: int,
    bmi: Optional[float],
    signals: Dict[str, Dict[str, Optional[float]]],
) -> Dict[str, Dict]:
    """
    signals = {
      "iron":      {"blood": 0.8, "symptom": 0.3, "food": 0.5, "history": None, "visual": None},
      "vitamin_d": {"blood": None, "symptom": 0.2, "food": 0.6, "history": None, "visual": None},
      ...
    }
    Returns: { nutrient: { probability, deficient, threshold } }
    """
    _load()
    out = {}
    for nutrient, (pipe, feats) in _models.items():
        sigs = signals.get(nutrient, {})
        row = {
            "blood_sig":   sigs.get("blood"),
            "symptom_sig": sigs.get("symptom"),
            "food_sig":    sigs.get("food"),
            "history_sig": sigs.get("history"),
            "visual_sig":  sigs.get("visual"),
            "age":         age,
            "female":      float(female),
            "bmi":         bmi,
        }
        X = pd.DataFrame([row])[feats].astype(float)
        prob = float(pipe.predict_proba(X)[0, 1])
        thr  = _thresholds.get(nutrient, 0.5)

        # Signal coverage — kitne layer signals available hain (NaN nahi)
        signal_feats = [f for f in feats if f.endswith("_sig")]
        n_available  = int(X[signal_feats].notna().sum(axis=1).iloc[0])
        n_total      = len(signal_feats)

        # Jab koi signal nahi → sirf demographics se prediction → low confidence
        # Probability ko base_rate ki taraf pull karo (shrinkage)
        if n_available == 0:
            base_rate = 0.30   # conservative prior — signal ke bina zyada confident nahi
            prob = prob * 0.4 + base_rate * 0.6

        out[nutrient] = {
            "probability":      round(prob, 4),
            "deficient":        prob >= thr,
            "threshold":        thr,
            "signals_available": n_available,
            "signals_total":    n_total,
        }
    return out


if __name__ == "__main__":
    result = fuse_signals(
        age=32, female=1, bmi=22,
        signals={
            "iron":      {"blood": 0.7, "symptom": 0.4, "food": 0.6, "history": 0.3, "visual": None},
            "vitamin_d": {"blood": 0.5, "symptom": None, "food": 0.4, "history": None, "visual": None},
            "calcium":   {"blood": None, "symptom": 0.2, "food": 0.3, "history": None, "visual": None},
        }
    )
    print("\nFusion prediction (32F, iron signals present):")
    for n, v in sorted(result.items(), key=lambda x: -x[1]["probability"]):
        flag = "⚠ DEFICIENT" if v["deficient"] else "   ok"
        print(f"  {n:20s}: {v['probability']:.3f}  {flag}")
