"""
Multi-Label XGBoost Nutrient Deficiency Classifier
Trains one binary XGBoost classifier per nutrient, then wraps in a single
predict() function that returns deficiency probabilities for all nutrients.
"""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

DATA_DIR  = Path(__file__).parent / "processed"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

NUTRIENT_LABELS = [
    "iron", "vitamin_d", "vitamin_b12", "folate", "calcium",
    "magnesium", "zinc", "selenium", "copper",
    "vitamin_c", "vitamin_a", "vitamin_e", "vitamin_k",
    "vitamin_b1", "vitamin_b2", "vitamin_b3", "vitamin_b6",
    "potassium", "phosphorus", "manganese", "omega3",
]

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading training data...")
df = pd.read_csv(DATA_DIR / "nhanes_training.csv")
print(f"  Shape: {df.shape}")

# Identify feature columns (everything that's not a label)
label_cols   = [c for c in NUTRIENT_LABELS if c in df.columns]
feature_cols = [c for c in df.columns if c not in NUTRIENT_LABELS]
print(f"  Features: {len(feature_cols)}, Labels present: {label_cols}")

X = df[feature_cols].copy()
Y = df[label_cols].copy()

# ── Train one XGBoost per nutrient ───────────────────────────────────────────
models      = {}
thresholds  = {}
auc_scores  = {}
meta        = {}

XGB_PARAMS = dict(
    n_estimators     = 400,
    max_depth        = 5,
    learning_rate    = 0.05,
    subsample        = 0.8,
    colsample_bytree = 0.7,
    min_child_weight = 10,
    gamma            = 1,
    reg_alpha        = 0.5,
    reg_lambda       = 2.0,
    use_label_encoder= False,
    eval_metric      = "logloss",
    random_state     = 42,
    n_jobs           = -1,
)

# Dietary labels: map nutrient → its direct dietary column (remove to prevent leakage)
DIETARY_DIRECT_COL = {
    "vitamin_b12": ["d_vitamin_b12", "d_vitamin_b12_per2k"],
    "vitamin_c":   ["d_vitamin_c",   "d_vitamin_c_per2k"],
    "vitamin_a":   ["d_vitamin_a",   "d_vitamin_a_per2k"],
    "vitamin_e":   ["d_vitamin_e",   "d_vitamin_e_per2k"],
    "vitamin_k":   ["d_vitamin_k",   "d_vitamin_k_per2k"],
    "vitamin_b1":  ["d_vitamin_b1",  "d_vitamin_b1_per2k"],
    "vitamin_b2":  ["d_vitamin_b2",  "d_vitamin_b2_per2k"],
    "vitamin_b3":  ["d_vitamin_b3",  "d_vitamin_b3_per2k"],
    "vitamin_b6":  ["d_vitamin_b6",  "d_vitamin_b6_per2k"],
    "magnesium":   ["d_magnesium",   "d_magnesium_per2k"],
    "zinc":        ["d_zinc",        "d_zinc_per2k"],
    "selenium":    ["d_selenium",    "d_selenium_per2k"],
    "copper":      ["d_copper",      "d_copper_per2k"],
    "potassium":   ["d_potassium",   "d_potassium_per2k"],
    "omega3":      ["d_omega3",      "d_omega3_per2k", "d_ala_g", "d_epa_g", "d_dpa_g", "d_dha_g",
                    "d_ala_g_per2k", "d_epa_g_per2k", "d_dpa_g_per2k", "d_dha_g_per2k", "d_pufa", "d_pufa_per2k"],
}

print("\nTraining per-nutrient classifiers...")
for nutrient in label_cols:
    y = Y[nutrient].copy()
    valid = y.notna()
    Xv = X[valid].copy()
    yv = y[valid].copy()

    if yv.sum() < 20:
        print(f"  [{nutrient:20s}] SKIP — only {int(yv.sum())} positive cases")
        continue

    pos_rate = yv.mean()
    scale_pos_weight = (1 - pos_rate) / pos_rate

    # Remove direct dietary column for this nutrient to prevent data leakage
    leak_cols = DIETARY_DIRECT_COL.get(nutrient, [])
    Xv_clean = Xv.drop(columns=[c for c in leak_cols if c in Xv.columns])

    pipe = Pipeline([
        ("imp",   SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf",   xgb.XGBClassifier(
            **XGB_PARAMS,
            scale_pos_weight=scale_pos_weight,
        )),
    ])

    # 5-fold CV AUC (on leak-free features)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_aucs = cross_val_score(pipe, Xv_clean, yv, cv=cv, scoring="roc_auc", n_jobs=-1)
    mean_auc = cv_aucs.mean()
    auc_scores[nutrient] = mean_auc

    # Final fit on all data (leak-free)
    pipe.fit(Xv_clean, yv)
    models[nutrient] = (pipe, leak_cols)

    # Calibrated threshold: maximize F1 on training set
    proba = pipe.predict_proba(Xv_clean)[:, 1]
    best_t, best_f1 = 0.5, 0
    for t in np.arange(0.20, 0.80, 0.05):
        pred = (proba >= t).astype(int)
        tp = ((pred == 1) & (yv == 1)).sum()
        fp = ((pred == 1) & (yv == 0)).sum()
        fn = ((pred == 0) & (yv == 1)).sum()
        if tp + fp == 0 or tp + fn == 0: continue
        p = tp / (tp + fp)
        r = tp / (tp + fn)
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        if f1 > best_f1:
            best_f1, best_t = f1, t
    thresholds[nutrient] = float(best_t)

    print(f"  [{nutrient:20s}] AUC={mean_auc:.3f}  prevalence={pos_rate*100:.1f}%  threshold={best_t:.2f}")
    meta[nutrient] = {"auc": round(mean_auc, 4), "prevalence": round(pos_rate, 4), "threshold": best_t}

# ── Save everything ───────────────────────────────────────────────────────────
print("\nSaving models...")
for nutrient, (pipe, leak_cols) in models.items():
    joblib.dump({"pipeline": pipe, "leak_cols": leak_cols}, MODEL_DIR / f"{nutrient}.pkl", compress=3)

joblib.dump(list(feature_cols), MODEL_DIR / "feature_cols.pkl")
joblib.dump(thresholds,          MODEL_DIR / "thresholds.pkl")

with open(MODEL_DIR / "meta.json", "w") as f:
    json.dump(meta, f, indent=2)

print(f"\nSaved {len(models)} models to {MODEL_DIR}")
print("\nModel AUC summary:")
for n, auc in sorted(auc_scores.items(), key=lambda x: -x[1]):
    print(f"  {n:20s}: {auc:.3f}")

mean_auc_all = np.mean(list(auc_scores.values()))
print(f"\nMean AUC across all nutrients: {mean_auc_all:.3f}")
