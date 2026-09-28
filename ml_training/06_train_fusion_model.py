"""
Fusion Model Trainer
5 layer signals → XGBoost → deficiency prediction.
Ek model per nutrient, features = [blood_sig, symptom_sig, food_sig, history_sig, visual_sig, age, female, bmi]
"""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_val_score
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

DATA      = Path(__file__).parent / "processed" / "nhanes_5layer_signals.csv"
MODEL_DIR = Path(__file__).parent / "fusion_models"
MODEL_DIR.mkdir(exist_ok=True)

FEATURES = ["blood_sig", "symptom_sig", "food_sig", "history_sig", "visual_sig", "age", "female", "bmi"]

# Lab-confirmed labels: label comes from real blood test → blood_sig = leakage → exclude from model
# food_sig, symptom_sig, history_sig, visual_sig are ALL synthetic → no leakage for any
LAB_CONFIRMED = {"iron", "vitamin_d", "calcium", "phosphorus", "folate"}

def get_features(nutrient):
    feats = list(FEATURES)
    if nutrient in LAB_CONFIRMED:
        feats = [f for f in feats if f != "blood_sig"]
    return feats

print("Loading signal dataset...")
df = pd.read_csv(DATA)
print(f"  Shape: {df.shape}")
print(f"  Nutrients: {df['nutrient'].unique().tolist()}")

XGB_PARAMS = dict(
    n_estimators     = 300,
    max_depth        = 4,
    learning_rate    = 0.05,
    subsample        = 0.8,
    colsample_bytree = 0.8,
    min_child_weight = 5,
    reg_alpha        = 0.3,
    reg_lambda       = 1.5,
    use_label_encoder= False,
    eval_metric      = "logloss",
    random_state     = 42,
    n_jobs           = -1,
)

models     = {}
thresholds = {}
auc_scores = {}
meta       = {}

print("\nTraining per-nutrient fusion models...")
for nutrient, grp in df.groupby("nutrient"):
    feats = get_features(nutrient)
    X = grp[feats].copy()
    y = grp["label"].copy()

    if y.sum() < 20:
        print(f"  [{nutrient:20s}] SKIP — only {int(y.sum())} positives")
        continue

    pos_rate = y.mean()
    spw = (1 - pos_rate) / pos_rate

    clf = xgb.XGBClassifier(**XGB_PARAMS, scale_pos_weight=spw)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    aucs = cross_val_score(clf, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    mean_auc = aucs.mean()
    auc_scores[nutrient] = mean_auc

    clf.fit(X, y)
    models[nutrient] = (clf, feats)

    # F1-optimal threshold
    proba = clf.predict_proba(X)[:, 1]
    best_t, best_f1 = 0.5, 0
    for t in np.arange(0.20, 0.80, 0.05):
        pred = (proba >= t).astype(int)
        tp = ((pred == 1) & (y == 1)).sum()
        fp = ((pred == 1) & (y == 0)).sum()
        fn = ((pred == 0) & (y == 1)).sum()
        if tp + fp == 0 or tp + fn == 0: continue
        p = tp / (tp + fp); r = tp / (tp + fn)
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        if f1 > best_f1: best_f1, best_t = f1, t
    thresholds[nutrient] = float(best_t)

    print(f"  [{nutrient:20s}] AUC={mean_auc:.3f}  prev={pos_rate*100:.1f}%  thr={best_t:.2f}")
    meta[nutrient] = {"auc": round(mean_auc, 4), "prevalence": round(pos_rate, 4), "threshold": best_t, "features": feats}

# Save
print("\nSaving fusion models...")
for nutrient, (clf, feats) in models.items():
    joblib.dump({"pipeline": clf, "features": feats}, MODEL_DIR / f"{nutrient}.pkl", compress=3)

joblib.dump(FEATURES,   MODEL_DIR / "feature_cols.pkl")
joblib.dump(thresholds, MODEL_DIR / "thresholds.pkl")
with open(MODEL_DIR / "meta.json", "w") as f:
    json.dump(meta, f, indent=2)

mean_auc_all = np.mean(list(auc_scores.values()))
print(f"\nSaved {len(models)} fusion models to {MODEL_DIR}")
print(f"Mean AUC: {mean_auc_all:.3f}")
print("\nPer-nutrient AUC:")
for n, auc in sorted(auc_scores.items(), key=lambda x: -x[1]):
    print(f"  {n:20s}: {auc:.3f}")
