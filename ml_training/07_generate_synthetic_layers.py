"""
Synthetic Layer Generator
Layer 1 + 2 = NHANES real data
Layer 3 (symptoms), Layer 4 (visual signs), Layer 5 (food photos proxy)
= medically-realistic synthetic signals generated from known deficiency labels.

Logic:
  - P(signal | deficient) = high (0.40-0.85) + Gaussian noise
  - P(signal | adequate)  = low  (0.03-0.15) — noise / other causes
  - Multiple deficiencies → stronger signal (comorbidity effect)
  - Final per-nutrient signal = -1 (excess) … 0 (unknown) … +1 (deficient)
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

DATA    = Path(__file__).parent / "processed" / "nhanes_training.csv"
XPT_DIR = Path(__file__).parent / "nhanes_data"
OUT     = Path(__file__).parent / "processed"

import pyreadstat

def read_xpt(name):
    path = XPT_DIR / name
    if not path.exists(): return pd.DataFrame()
    try:
        df, _ = pyreadstat.read_xport(str(path))
        df.columns = df.columns.str.upper()
        return df
    except: return pd.DataFrame()

print("Loading NHANES data...")
base = pd.read_csv(DATA)

# Load raw labs for Layer 2 blood signals
fertin  = read_xpt("FERTIN_J.XPT")
cbc     = read_xpt("CBC_J.XPT")
vid     = read_xpt("VID_J.XPT")
folate  = read_xpt("FOLATE_J.XPT")
biopro  = read_xpt("BIOPRO_J.XPT")
demo    = read_xpt("DEMO_J.XPT")

# Rebuild with lab columns
if demo.shape[0]:
    demo2 = demo[["SEQN","RIDAGEYR","RIAGENDR"]].copy()
    demo2["age"]    = demo2["RIDAGEYR"]
    demo2["female"] = (demo2["RIAGENDR"] == 2).astype(float)
    demo2 = demo2[demo2["age"] >= 18]
    lab_merge = demo2[["SEQN","age","female"]].copy()
    for ldf in [fertin[["SEQN","LBXFER"]] if "LBXFER" in fertin.columns else pd.DataFrame(columns=["SEQN"]),
                cbc[["SEQN","LBXHGB","LBXMCVSI","LBXMC"]] if "LBXHGB" in cbc.columns else pd.DataFrame(columns=["SEQN"]),
                vid[["SEQN","LBXVIDMS"]] if "LBXVIDMS" in vid.columns else pd.DataFrame(columns=["SEQN"]),
                folate[["SEQN","LBDRFO"]] if "LBDRFO" in folate.columns else pd.DataFrame(columns=["SEQN"]),
                biopro[["SEQN"] + [c for c in ["LBXSCA","LBXSPH","LBXSALB","LBXSAL"] if c in biopro.columns]] if biopro.shape[0] else pd.DataFrame(columns=["SEQN"])]:
        if "SEQN" in ldf.columns and len(ldf.columns) > 1:
            lab_merge = lab_merge.merge(ldf, on="SEQN", how="left")
    df = pd.concat([lab_merge.reset_index(drop=True), base[[c for c in base.columns if c not in ["age","female"]]].reset_index(drop=True)], axis=1)
else:
    df = base.copy()

print(f"  Shape: {df.shape}")

# ── Nutrient labels (ground truth) ───────────────────────────────────────────
NUTRIENTS = [
    "iron","calcium","vitamin_d","folate","vitamin_b12","vitamin_c","vitamin_a",
    "vitamin_e","vitamin_k","vitamin_b1","vitamin_b2","vitamin_b3","vitamin_b6",
    "magnesium","zinc","selenium","copper","potassium","phosphorus","omega3",
]
label_cols = [n for n in NUTRIENTS if n in df.columns]
N = len(df)

RDA = {
    "iron":18,"calcium":800,"vitamin_d":15,"folate":400,"vitamin_b12":2.4,
    "vitamin_c":90,"vitamin_a":800,"vitamin_e":15,"vitamin_k":120,"vitamin_b1":1.2,
    "vitamin_b2":1.3,"vitamin_b3":16,"vitamin_b6":1.7,"magnesium":350,"zinc":11,
    "selenium":55,"copper":0.9,"potassium":3500,"phosphorus":700,"omega3":1600,
}
DIETARY_COL = {
    "iron":"d_iron","calcium":"d_calcium","vitamin_d":"d_vitamin_d","folate":"d_folate",
    "vitamin_b12":"d_vitamin_b12","vitamin_c":"d_vitamin_c","vitamin_a":"d_vitamin_a",
    "vitamin_e":"d_vitamin_e","vitamin_k":"d_vitamin_k","vitamin_b1":"d_vitamin_b1",
    "vitamin_b2":"d_vitamin_b2","vitamin_b3":"d_vitamin_b3","vitamin_b6":"d_vitamin_b6",
    "magnesium":"d_magnesium","zinc":"d_zinc","selenium":"d_selenium","copper":"d_copper",
    "potassium":"d_potassium","phosphorus":"d_phosphorus","omega3":"d_omega3",
}

# ── LAYER 2: Blood signals (real) ─────────────────────────────────────────────
print("\nComputing Layer 2 (blood) signals...")

def sig_range(val, low_def, low_mild, ok_low, ok_high, high_mild=None, high_def=None):
    """Map a continuous lab value to signal -1..+1"""
    if pd.isna(val): return np.nan
    if val < low_def:  return  0.90
    if val < low_mild: return  0.55
    if val < ok_low:   return  0.15
    if high_mild is None or val <= ok_high: return -0.10
    if val <= high_mild: return -0.35
    return -0.70

blood_sigs = {}
# Iron
hgb = df.get("LBXHGB", pd.Series(np.nan, index=df.index))
fer = df.get("LBXFER", pd.Series(np.nan, index=df.index))
is_f = df.get("female", pd.Series(0, index=df.index)) == 1
h_sig = pd.Series(np.nan, index=df.index)
h_sig[is_f]  = hgb[is_f].apply(lambda v: sig_range(v, 9, 10, 12, 15))
h_sig[~is_f] = hgb[~is_f].apply(lambda v: sig_range(v, 10, 11, 13, 16))
f_sig = fer.apply(lambda v: sig_range(v, 12, 20, 30, 150))
blood_sigs["iron"] = h_sig.combine(f_sig, lambda a,b: np.nanmean([x for x in [a,b] if not np.isnan(x)]) if not (np.isnan(a) and np.isnan(b)) else np.nan)

# Vitamin D
vitd = df.get("LBXVIDMS", pd.Series(np.nan, index=df.index))
blood_sigs["vitamin_d"] = vitd.apply(lambda v: sig_range(v, 30, 50, 75, 125, 150, 200))

# Folate
fol = df.get("LBDRFO", pd.Series(np.nan, index=df.index))
blood_sigs["folate"] = fol.apply(lambda v: sig_range(v, 100, 140, 200, 600))

# Calcium
ca = df.get("LBXSCA", pd.Series(np.nan, index=df.index))
blood_sigs["calcium"] = ca.apply(lambda v: sig_range(v, 7.5, 8.5, 9.0, 10.2, 10.5, 11.0))

# Phosphorus
ph = df.get("LBXSPH", pd.Series(np.nan, index=df.index))
blood_sigs["phosphorus"] = ph.apply(lambda v: sig_range(v, 2.0, 2.5, 3.0, 4.5, 4.8, 5.5))

# All others: NaN (not in NHANES blood panel)
for n in label_cols:
    if n not in blood_sigs:
        blood_sigs[n] = pd.Series(np.nan, index=df.index)

# ── LAYER 5: Food photo signal (synthetic — models 7-day food photo AI analysis) ─
print("Computing Layer 5 (food photo) synthetic signals...")
# Layer 5 = food photos se AI jo last 7 din ka pattern detect karta hai
# 7-day pattern symptoms se zyada reliable hai — P_def=0.55, P_adeq=0.10
# Synthetic (not dietary recall) so no leakage → used for ALL nutrients
FOOD_PHOTO_PROBS = {
    # nutrient → [(food_marker, p_if_deficient, p_if_adequate, signal_strength)]
    # Food photos: lowest reliability tier (with visual signs)
    # Reason: photo se portion size, nutrient content, absorption estimate karna hard hai
    # p_def=0.22-0.32, p_adeq=0.12-0.18 → low SNR → model gives least weight
    "iron":       [("low_meat_fish",0.28,0.14,0.42),("low_leafy_greens",0.24,0.15,0.38),("low_legumes",0.22,0.16,0.35)],
    "vitamin_d":  [("low_fatty_fish",0.25,0.13,0.40),("low_eggs_dairy",0.22,0.15,0.36),("low_fortified",0.20,0.16,0.32)],
    "vitamin_b12":[("low_meat_fish",0.30,0.13,0.42),("low_dairy_eggs",0.26,0.13,0.38),("veg_pattern",0.24,0.10,0.42)],
    "folate":     [("low_leafy_greens",0.28,0.13,0.40),("low_legumes",0.24,0.15,0.36)],
    "calcium":    [("low_dairy",0.30,0.13,0.44),("low_seeds_nuts",0.22,0.16,0.34)],
    "magnesium":  [("low_nuts_seeds",0.26,0.13,0.40),("low_whole_grains",0.22,0.15,0.36),("low_leafy_greens",0.20,0.16,0.33)],
    "zinc":       [("low_meat_shellfish",0.28,0.13,0.42),("low_seeds",0.24,0.15,0.36)],
    "selenium":   [("low_seafood",0.25,0.13,0.38),("low_brazil_nuts",0.22,0.13,0.36)],
    "vitamin_c":  [("low_citrus_vegs",0.30,0.13,0.42),("low_berries",0.24,0.15,0.36)],
    "vitamin_a":  [("low_orange_vegs",0.28,0.13,0.40),("low_dairy_eggs",0.22,0.15,0.34)],
    "vitamin_e":  [("low_nuts_seeds",0.25,0.13,0.38),("low_plant_oils",0.22,0.15,0.34)],
    "vitamin_k":  [("low_leafy_greens",0.30,0.13,0.44),("low_fermented_food",0.20,0.16,0.32)],
    "vitamin_b1": [("low_whole_grains",0.26,0.13,0.40),("high_refined_carbs",0.22,0.16,0.35)],
    "vitamin_b2": [("low_dairy",0.26,0.13,0.40),("low_meat_fish",0.22,0.15,0.36)],
    "vitamin_b3": [("low_meat_fish",0.26,0.13,0.40),("low_whole_grains",0.22,0.15,0.34)],
    "vitamin_b6": [("low_meat_fish",0.26,0.13,0.38),("low_legumes",0.22,0.15,0.34)],
    "omega3":     [("low_fatty_fish",0.30,0.13,0.42),("no_fish_week",0.26,0.10,0.44)],
    "potassium":  [("low_fruits_vegs",0.28,0.13,0.40),("low_bananas_potatoes",0.22,0.15,0.34)],
    "phosphorus": [("low_dairy_meat",0.24,0.13,0.36),("low_legumes",0.20,0.16,0.32)],
    "copper":     [("low_shellfish_nuts",0.22,0.13,0.36),("low_seeds",0.20,0.15,0.32)],
}

def generate_food_signal(def_labels_row, nutrient):
    """7-day food photo AI signal — more reliable than today's symptoms"""
    markers = FOOD_PHOTO_PROBS.get(nutrient, [])
    if not markers: return np.nan
    is_deficient = def_labels_row.get(nutrient, np.nan)
    if pd.isna(is_deficient): return np.nan

    total_signal = 0.0; total_weight = 0.0
    for marker, p_def, p_adeq, strength in markers:
        p = p_def if is_deficient == 1 else p_adeq
        present = np.random.random() < p
        noise = np.random.normal(0, 0.10)
        if present:
            total_signal += (strength + noise)
        else:
            total_signal += max(0, noise * 0.25)
        total_weight += strength

    if total_weight == 0: return np.nan
    raw = total_signal / total_weight
    signal = (raw - 0.12) * 2.0
    return float(np.clip(signal, -1.0, 1.0))

food_sigs = {}  # will be filled in the main loop below

# ── LAYER 3: Symptoms (synthetic, medically realistic) ───────────────────────
print("Generating Layer 3 (symptoms) synthetic signals...")

# P(symptom_score contribution | nutrient_deficient)
# symptom_score ∈ [0,1] → converted to signal at end
SYMPTOM_DEFICIENCY_PROBS = {
    # nutrient → [(symptom_name, p_if_deficient, p_if_adequate, signal_strength)]
    # LAST 7 DAYS symptoms — 7-din ka pattern, aaj ka nahi
    # p_def=0.40-0.55 (7-day reduces random noise), p_adeq=0.12-0.16
    # Still less reliable than food (food = direct causal, symptoms = many confounders)
    "iron":       [("fatigue_7d",0.52,0.14,0.58),("breathlessness_7d",0.42,0.10,0.52),
                   ("brain_fog_7d",0.38,0.13,0.48),("pale_skin_7d",0.46,0.11,0.55),
                   ("hair_fall_7d",0.35,0.13,0.45),("brittle_nails_7d",0.32,0.11,0.42)],
    "vitamin_d":  [("fatigue_7d",0.48,0.14,0.52),("bone_pain_7d",0.42,0.11,0.56),
                   ("muscle_weakness_7d",0.38,0.12,0.50),("mood_issues_7d",0.35,0.15,0.46),
                   ("sleep_problems_7d",0.32,0.16,0.42),("freq_infections_7d",0.35,0.13,0.46)],
    "vitamin_b12":[("fatigue_7d",0.50,0.14,0.55),("numbness_7d",0.45,0.08,0.58),
                   ("brain_fog_7d",0.42,0.13,0.52),("mouth_ulcers_7d",0.32,0.11,0.46),
                   ("mood_issues_7d",0.35,0.15,0.46)],
    "folate":     [("fatigue_7d",0.46,0.14,0.50),("mouth_ulcers_7d",0.38,0.11,0.48),
                   ("brain_fog_7d",0.35,0.13,0.45)],
    "calcium":    [("muscle_cramps_7d",0.48,0.13,0.56),("joint_pain_7d",0.38,0.15,0.48),
                   ("brittle_nails_7d",0.32,0.11,0.42),("numbness_7d",0.30,0.09,0.46)],
    "magnesium":  [("muscle_cramps_7d",0.52,0.13,0.58),("sleep_problems_7d",0.46,0.16,0.52),
                   ("anxiety_7d",0.42,0.16,0.50),("fatigue_7d",0.38,0.14,0.48),
                   ("irr_heartbeat_7d",0.25,0.06,0.55)],
    "zinc":       [("hair_fall_7d",0.42,0.15,0.50),("poor_wound_healing_7d",0.38,0.08,0.55),
                   ("loss_appetite_7d",0.35,0.13,0.46),("freq_infections_7d",0.46,0.15,0.52)],
    "selenium":   [("fatigue_7d",0.38,0.14,0.46),("hair_fall_7d",0.32,0.15,0.42),
                   ("muscle_weakness_7d",0.30,0.11,0.42),("brain_fog_7d",0.28,0.13,0.38)],
    "vitamin_c":  [("bleeding_gums_7d",0.48,0.08,0.60),("poor_wound_healing_7d",0.42,0.08,0.56),
                   ("fatigue_7d",0.38,0.14,0.48),("freq_infections_7d",0.42,0.15,0.50)],
    "vitamin_a":  [("night_blindness_7d",0.55,0.05,0.62),("dry_skin_7d",0.46,0.15,0.52),
                   ("freq_infections_7d",0.38,0.15,0.48)],
    "vitamin_e":  [("dry_skin_7d",0.38,0.15,0.48),("muscle_weakness_7d",0.32,0.11,0.42),
                   ("mood_issues_7d",0.28,0.15,0.38)],
    "vitamin_k":  [("bleeding_gums_7d",0.42,0.08,0.52),("poor_wound_healing_7d",0.35,0.08,0.48),
                   ("bone_pain_7d",0.30,0.11,0.42)],
    "vitamin_b1": [("fatigue_7d",0.46,0.14,0.52),("numbness_7d",0.38,0.08,0.52),
                   ("brain_fog_7d",0.35,0.13,0.46),("loss_appetite_7d",0.30,0.13,0.42)],
    "vitamin_b2": [("mouth_ulcers_7d",0.42,0.11,0.50),("dry_skin_7d",0.35,0.15,0.46),
                   ("fatigue_7d",0.38,0.14,0.48)],
    "vitamin_b3": [("fatigue_7d",0.42,0.14,0.50),("mood_issues_7d",0.35,0.15,0.46),
                   ("dry_skin_7d",0.30,0.15,0.42)],
    "vitamin_b6": [("mood_issues_7d",0.42,0.15,0.50),("numbness_7d",0.38,0.08,0.50),
                   ("fatigue_7d",0.38,0.14,0.48)],
    "omega3":     [("dry_skin_7d",0.38,0.15,0.46),("brain_fog_7d",0.35,0.15,0.44),
                   ("joint_pain_7d",0.32,0.15,0.42),("mood_issues_7d",0.30,0.15,0.42)],
    "potassium":  [("muscle_cramps_7d",0.50,0.13,0.56),("fatigue_7d",0.42,0.14,0.50),
                   ("irr_heartbeat_7d",0.30,0.06,0.55)],
    "phosphorus": [("fatigue_7d",0.38,0.14,0.46),("bone_pain_7d",0.30,0.11,0.42),
                   ("muscle_weakness_7d",0.28,0.11,0.38)],
    "copper":     [("fatigue_7d",0.35,0.14,0.42),("freq_infections_7d",0.30,0.13,0.42),
                   ("bone_pain_7d",0.25,0.11,0.36)],
}

def generate_symptom_signal(def_labels_row, nutrient):
    """Generate symptom signal for one person-nutrient pair"""
    syms = SYMPTOM_DEFICIENCY_PROBS.get(nutrient, [])
    if not syms: return np.nan

    is_deficient = def_labels_row.get(nutrient, np.nan)
    if pd.isna(is_deficient): return np.nan

    total_signal = 0.0
    total_weight = 0.0

    for sym_name, p_def, p_adeq, strength in syms:
        p = p_def if is_deficient == 1 else p_adeq
        # Probabilistic symptom presence + noise
        present = np.random.random() < p
        noise = np.random.normal(0, 0.08)
        if present:
            total_signal += (strength + noise)
        else:
            total_signal += max(0, noise * 0.3)
        total_weight += strength

    if total_weight == 0: return np.nan
    raw = total_signal / total_weight        # 0..1 roughly
    # Map to -1..+1: 0 → adequate side, high → deficient side
    signal = (raw - 0.15) * 2.0             # center around 0 for adequate person
    return float(np.clip(signal, -1.0, 1.0))

# ── LAYER 4: Visual signs (synthetic) ────────────────────────────────────────
print("Generating Layer 4 (visual signs) synthetic signals...")

VISUAL_DEFICIENCY_PROBS = {
    # LOWEST reliability — camera se dekh ke nutrition deficiency identify karna bahut mushkil hai
    # p_def=0.12-0.25, p_adeq=0.10-0.18 → near-random signal → model gives minimum weight
    "iron":       [("pale_conjunctiva",0.22,0.12,0.55),("pale_nails",0.18,0.12,0.48),
                   ("spoon_nails",0.12,0.06,0.52),("pale_tongue",0.16,0.10,0.45)],
    "vitamin_b12":[("pale_tongue",0.18,0.10,0.48),("glossy_tongue",0.15,0.08,0.50),
                   ("pale_conjunctiva",0.14,0.10,0.42)],
    "folate":     [("glossy_tongue",0.15,0.08,0.45),("pale_tongue",0.14,0.10,0.42)],
    "zinc":       [("white_nail_spots",0.16,0.12,0.42),("dry_skin_visual",0.14,0.14,0.38),
                   ("hair_thinning",0.18,0.16,0.40)],
    "vitamin_a":  [("dry_skin_visual",0.20,0.14,0.48),("dull_eyes",0.18,0.10,0.50)],
    "vitamin_e":  [("dry_skin_visual",0.16,0.14,0.40),("dull_skin",0.14,0.14,0.36)],
    "vitamin_c":  [("bleeding_gums_visual",0.22,0.08,0.52),("skin_bruising",0.16,0.10,0.45)],
    "vitamin_k":  [("bleeding_gums_visual",0.18,0.08,0.48),("skin_bruising",0.18,0.10,0.48)],
    "calcium":    [("brittle_nails_visual",0.15,0.12,0.40)],
    "magnesium":  [("muscle_twitching",0.14,0.10,0.40)],
    "vitamin_b2": [("cracked_lips",0.20,0.12,0.48),("red_tongue",0.16,0.10,0.45)],
    "vitamin_b3": [("skin_rash",0.18,0.12,0.45),("red_skin",0.15,0.10,0.42)],
    "omega3":     [("dry_skin_visual",0.15,0.14,0.38),("dull_skin",0.13,0.14,0.35)],
    "selenium":   [("hair_thinning",0.14,0.16,0.36),("pale_skin",0.12,0.10,0.34)],
    "copper":     [("pale_skin",0.12,0.10,0.36),("hair_thinning",0.12,0.16,0.32)],
    "vitamin_d":  [("bowed_legs",0.10,0.04,0.52),("pale_skin",0.12,0.10,0.32)],
    "vitamin_b1": [("puffiness",0.12,0.08,0.38)],
    "vitamin_b6": [("cracked_lips",0.14,0.12,0.36)],
    "potassium":  [("muscle_twitching",0.12,0.10,0.38)],
    "phosphorus": [("pale_skin",0.10,0.10,0.30)],
}

def generate_visual_signal(def_labels_row, nutrient):
    signs = VISUAL_DEFICIENCY_PROBS.get(nutrient, [])
    if not signs: return np.nan
    is_deficient = def_labels_row.get(nutrient, np.nan)
    if pd.isna(is_deficient): return np.nan
    total_signal = 0.0; total_weight = 0.0
    for sign_name, p_def, p_adeq, strength in signs:
        p = p_def if is_deficient == 1 else p_adeq
        present = np.random.random() < p
        noise = np.random.normal(0, 0.06)
        if present:
            total_signal += (strength + noise)
        else:
            total_signal += max(0, noise * 0.2)
        total_weight += strength
    if total_weight == 0: return np.nan
    raw = total_signal / total_weight
    signal = (raw - 0.10) * 2.2
    return float(np.clip(signal, -1.0, 1.0))

# ── LAYER 1: Health history (from NHANES demographics + medical proxy) ────────
print("Computing Layer 1 (history) signals...")

def history_signal(row_label, age, female, bmi, nutrient):
    """
    Layer 1: 3-month health history proxy.
    Uses deficiency label + demographic risk factors.
    More reliable than today's symptoms — 3-month pattern.
    p_def=0.55, p_adeq=0.10 → moderate-high SNR, second after food.
    """
    is_deficient = row_label
    if pd.isna(is_deficient):
        return np.nan

    # Base probability from deficiency status (3-month accumulated evidence)
    p = 0.70 if is_deficient == 1 else 0.08
    noise_scale = 0.10  # less noise than symptoms and food

    # Demographic risk boosts reliability for known patterns
    demo_boost = 0.0
    if nutrient in ["iron","folate"] and female == 1 and age < 50:
        demo_boost = 0.10   # menstruating women: stronger history signal for iron
    if nutrient in ["vitamin_d","calcium"] and age > 50:
        demo_boost = 0.10
    if nutrient == "vitamin_b12" and age > 60:
        demo_boost = 0.10
    if nutrient in ["zinc","selenium"] and bmi is not None and bmi < 18.5:
        demo_boost = 0.08

    p_effective = min(p + demo_boost, 0.80)
    present = np.random.random() < p_effective
    noise = np.random.normal(0, noise_scale)

    if present:
        raw = 0.65 + noise
    else:
        raw = 0.05 + abs(noise) * 0.3

    return float(np.clip(raw * 2.0 - 1.0, -1.0, 1.0))

# ── Build complete 5-layer signal dataset ─────────────────────────────────────
print("\nBuilding complete 5-layer signal dataset...")

rows = []
bmi_col = df.get("bmi", pd.Series(np.nan, index=df.index))

for idx in df.index:
    def_labels = {n: df.at[idx, n] for n in label_cols if n in df.columns}
    age    = df.at[idx, "age"]    if "age"    in df.columns else np.nan
    female = df.at[idx, "female"] if "female" in df.columns else 0
    bmi    = bmi_col.at[idx]      if not pd.isna(bmi_col.at[idx]) else None

    for nutrient in label_cols:
        label = def_labels.get(nutrient, np.nan)
        if pd.isna(label): continue
        if blood_sigs[nutrient].at[idx] is np.nan and food_sigs[nutrient].at[idx] is np.nan:
            if pd.isna(blood_sigs[nutrient].at[idx]) and pd.isna(food_sigs[nutrient].at[idx]):
                continue

        b_sig = blood_sigs[nutrient].at[idx]
        f_sig = generate_food_signal(def_labels, nutrient)
        s_sig = generate_symptom_signal(def_labels, nutrient)
        v_sig = generate_visual_signal(def_labels, nutrient)
        h_sig = history_signal(label, age, female, bmi, nutrient)

        if pd.isna(b_sig) and pd.isna(f_sig): continue

        rows.append({
            "nutrient":    nutrient,
            "blood_sig":   b_sig,
            "symptom_sig": s_sig,
            "food_sig":    f_sig,
            "history_sig": h_sig,
            "visual_sig":  v_sig,
            "age":         age,
            "female":      float(female),
            "bmi":         bmi,
            "label":       label,
        })

    if idx % 500 == 0:
        print(f"  Processed {idx}/{len(df)} rows...")

out_df = pd.DataFrame(rows)
print(f"\nTotal rows: {len(out_df)}")
print(f"Nutrients: {out_df['nutrient'].unique().tolist()}")

# Signal coverage per layer
for layer in ["blood_sig","symptom_sig","food_sig","history_sig","visual_sig"]:
    pct = out_df[layer].notna().mean() * 100
    print(f"  {layer:15s}: {pct:.1f}% coverage")

# Deficiency prevalence
print("\nDeficiency prevalence:")
for n, grp in out_df.groupby("nutrient"):
    pct = grp["label"].mean() * 100
    print(f"  {n:20s}: {pct:.1f}%")

out_path = OUT / "nhanes_5layer_signals.csv"
out_df.to_csv(out_path, index=False)
print(f"\nSaved → {out_path}")
