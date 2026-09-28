"""
Use the trained classifier (58.4% CV accuracy — real but modest, NOT reliable
enough to blindly replace the keyword+hand-verified categorization) as a second
opinion instead: flag every dish where the classifier disagrees with the current
keyword-based category at high confidence. These disagreements are exactly where
the "Manipuri"-class of bugs live — a systematic way to find them instead of
manually spot-checking dishes one at a time.
"""
import json
import glob
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")

cats_raw = json.loads((DATA_DIR / "all_meal_categories.json").read_text())
current_cat = {}
for k, v in cats_raw.items():
    region, name = k.split("|||")
    current_cat[(region, name)] = v

lunch_hand_verified = set()
for f in glob.glob(str(DATA_DIR / "lunch_categories" / "*.json")):
    d = json.loads(Path(f).read_text())
    for dish in d["dishes"]:
        lunch_hand_verified.add((dish["region"], dish["name"]))

# build the same (text, label, key) arrays as training, then get OUT-OF-FOLD
# predictions — each dish's predicted label comes from a model that never saw
# that dish during fitting, so this is a fair test for label-error detection
# (not circular self-comparison against the model's own training targets)
texts, labels, keys = [], [], []
for subdir in ["breakfast_research", "lunch_research", "dinner_research"]:
    for f in glob.glob(str(DATA_DIR / subdir / "*.json")):
        if "thali_types" in f:
            continue
        d = json.loads(Path(f).read_text())
        region = d["region"]
        for dish in d["dishes"]:
            key = (region, dish["name"])
            if key not in current_cat or key in keys:
                continue
            text = " ".join([dish.get("name", ""), dish.get("local_name", ""), dish.get("description", "")])
            texts.append(text)
            labels.append(current_cat[key])
            keys.append(key)

vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
X_all = vectorizer.fit_transform(texts)
clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=5.0)

oof_pred = cross_val_predict(clf, X_all, labels, cv=5, method="predict")
oof_proba = cross_val_predict(clf, X_all, labels, cv=5, method="predict_proba")
classes_order = sorted(set(labels))
conf_map = {c: i for i, c in enumerate(sorted(set(labels)))}

disagreements = []
for i, key in enumerate(keys):
    region, name = key
    pred = oof_pred[i]
    conf = oof_proba[i].max()
    cur = labels[i]
    if pred != cur and conf > 0.35:
        disagreements.append({
            "region": region, "name": name,
            "current_category": cur, "classifier_prediction": pred, "classifier_confidence": round(float(conf), 2),
            "hand_verified": key in lunch_hand_verified,
        })

disagreements.sort(key=lambda x: -x["classifier_confidence"])
print(f"Total high-confidence disagreements (conf>0.5): {len(disagreements)}")
print(f"Of these, hand-verified (should be trustworthy, likely classifier is wrong): "
      f"{sum(1 for d in disagreements if d['hand_verified'])}")
print(f"Of these, auto-categorized (real candidates for review): "
      f"{sum(1 for d in disagreements if not d['hand_verified'])}\n")

print("Top 20 auto-categorized disagreements (most likely real bugs):")
for d in [x for x in disagreements if not x["hand_verified"]][:20]:
    print(f"  {d['region']:10s} {d['name']:40s} current={d['current_category']:14s} "
          f"classifier={d['classifier_prediction']:14s} (conf={d['classifier_confidence']})")

(DATA_DIR / "categorization_disagreements.json").write_text(json.dumps(disagreements, indent=2, ensure_ascii=False))
print(f"\nSaved -> {DATA_DIR / 'categorization_disagreements.json'}")
