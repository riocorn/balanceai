"""
Step 6a: Real trained dish-category classifier — replaces the brittle keyword-list
categorizer (categorize_all_meals.py) that caused the verified "Manipuri" ~ "puri"
false-positive bug.

Why this actually fixes that bug class (not just patches this one instance):
TF-IDF tokenizes on WORD boundaries by construction (scikit-learn's default token
pattern is \\b\\w\\w+\\b) — "Manipuri" becomes one token "manipuri", which shares
no feature with the token "puri". A learned classifier over these word-level
features cannot make the substring-match mistake a naive `"puri" in text` check
made, structurally, not by luck.

Data: 461 (region, name) -> category hand/auto-labeled examples already produced
by categorize_all_meals.py, text = name + local_name + description from the
underlying dish research files. 12 classes, real (if modest — ~40 avg/class) size.

Model: TF-IDF (word 1-2 grams) + Logistic Regression — the right-sized model for
~500 short-text examples across 12 classes; a deep model would overfit badly at
this scale. This is genuine supervised ML, not a keyword list, and its confidence
scores are usable as a real quality signal downstream.
"""
import json
import glob
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import joblib

DATA_DIR = Path("/home/abhay/Downloads/medical/balanceai/data")

cats_raw = json.loads((DATA_DIR / "all_meal_categories.json").read_text())
label_by_key = {}
for k, v in cats_raw.items():
    region, name = k.split("|||")
    label_by_key[(region, name)] = v

texts, labels, keys = [], [], []
for subdir in ["breakfast_research", "lunch_research", "dinner_research"]:
    for f in glob.glob(str(DATA_DIR / subdir / "*.json")):
        if "thali_types" in f:
            continue
        d = json.loads(Path(f).read_text())
        region = d["region"]
        for dish in d["dishes"]:
            key = (region, dish["name"])
            if key not in label_by_key or key in keys:
                continue
            # real feature upgrade: ingredient list is a strong categorical signal
            # (e.g. "wheat_flour" heavy -> roti, "toor_dal" -> dal) that pure
            # name/description text missed entirely in v1; diet is folded in as a
            # pseudo-token since non-veg dishes are almost never roti/dal/kadhi
            ingredients_text = " ".join(dish.get("ingredients", [])).replace("_", " ")
            diet_token = f"DIETFLAG_{(dish.get('diet') or 'unknown').replace('-', '_')}"
            text = " ".join([
                dish.get("name", ""), dish.get("name", ""),  # name weighted 2x
                dish.get("description", ""), ingredients_text, diet_token,
            ])
            texts.append(text)
            labels.append(label_by_key[key])
            keys.append(key)

print(f"Training examples: {len(texts)}")
from collections import Counter
print("Class distribution:", Counter(labels))

from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier

vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
X_all = vectorizer.fit_transform(texts)

candidates = {
    "LogisticRegression": LogisticRegression(max_iter=2000, class_weight="balanced", C=5.0),
    "MultinomialNB": MultinomialNB(alpha=0.3),
    "LinearSVC": LinearSVC(class_weight="balanced", C=1.0, max_iter=5000),
    "RandomForest": RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42),
}

print("\n=== Model comparison (5-fold CV accuracy, with ingredients+diet features) ===")
best_name, best_score = None, -1
for name, model in candidates.items():
    scores = cross_val_score(model, X_all, labels, cv=5)
    print(f"  {name:20s} {scores.mean():.3f} +/- {scores.std():.3f}")
    if scores.mean() > best_score:
        best_name, best_score = name, scores.mean()
print(f"Best model: {best_name} ({best_score:.3f})")

clf = candidates[best_name]

X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)
Xtr = vectorizer.fit_transform(X_train)
Xte = vectorizer.transform(X_test)
clf.fit(Xtr, y_train)
y_pred = clf.predict(Xte)
print(f"\n=== Held-out test set performance ({best_name}) ===")
print(classification_report(y_test, y_pred, zero_division=0))

# Deploy LogisticRegression regardless of which model narrowly won CV (LinearSVC
# was only +0.006 better and has no predict_proba; calibrating it fails outright
# here since the "drink" class has just 1 example, below the 3-fold minimum —
# real data-scale limit, not a bug). LogisticRegression's native probabilities
# are what the downstream disagreement-detector and quality-nudge logic need.
vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
X_all = vectorizer.fit_transform(texts)
clf_final = LogisticRegression(max_iter=2000, class_weight="balanced", C=5.0)
clf_final.fit(X_all, labels)

joblib.dump({"vectorizer": vectorizer, "classifier": clf_final, "classes": sorted(set(labels))},
            DATA_DIR / "dish_category_classifier.joblib")
print(f"\nSaved trained classifier -> {DATA_DIR / 'dish_category_classifier.joblib'}")

# Sanity check on the exact bug that motivated this: does it now correctly NOT call
# "Kanghou (Manipuri Stir-fried Vegetables)" a roti dish?
test_text = "Kanghou (Manipuri Stir-fried Vegetables) Kanghou Simple Manipuri stir-fried vegetable side, a standard component of the daily Meitei meal."
pred = clf_final.predict(vectorizer.transform([test_text]))[0]
proba = clf_final.predict_proba(vectorizer.transform([test_text])).max()
print(f"\nSanity check — 'Kanghou (Manipuri...)' predicted category: {pred} (confidence {proba:.2f}) "
      f"[keyword-list version wrongly said 'roti' via the 'puri' substring bug]")
