"""
Signal Dataset Builder
5 layer signals compute karo NHANES data se → training features banao.
Features: [blood_sig, symptom_sig, food_sig, history_sig, visual_sig, age, gender, bmi]
Labels: same ground truth (lab-confirmed + dietary proxy)
"""
import pandas as pd
import numpy as np
import pyreadstat
from pathlib import Path

PROCESSED = Path(__file__).parent / "processed" / "nhanes_training.csv"
XPT_DIR   = Path(__file__).parent / "nhanes_data"
OUT       = Path(__file__).parent / "processed"


def read_xpt(name):
    path = XPT_DIR / name
    if not path.exists(): return pd.DataFrame()
    try:
        df, _ = pyreadstat.read_xport(str(path))
        df.columns = df.columns.str.upper()
        return df
    except: return pd.DataFrame()


print("Loading NHANES data...")
base = pd.read_csv(PROCESSED)

# Load raw lab columns needed for blood signals
fertin  = read_xpt("FERTIN_J.XPT")[["SEQN","LBXFER"]]  if read_xpt("FERTIN_J.XPT").shape[0] else pd.DataFrame(columns=["SEQN"])
cbc     = read_xpt("CBC_J.XPT")[["SEQN","LBXHGB"]]     if read_xpt("CBC_J.XPT").shape[0] else pd.DataFrame(columns=["SEQN"])
vid     = read_xpt("VID_J.XPT")[["SEQN","LBXVIDMS"]]   if read_xpt("VID_J.XPT").shape[0] else pd.DataFrame(columns=["SEQN"])
folate  = read_xpt("FOLATE_J.XPT")[["SEQN","LBDRFO"]]  if read_xpt("FOLATE_J.XPT").shape[0] else pd.DataFrame(columns=["SEQN"])
biopro  = read_xpt("BIOPRO_J.XPT")
biopro  = biopro[["SEQN"] + [c for c in ["LBXSCA","LBXSPH"] if c in biopro.columns]] if biopro.shape[0] else pd.DataFrame(columns=["SEQN"])
demo    = read_xpt("DEMO_J.XPT")[["SEQN","RIDAGEYR","RIAGENDR"]] if read_xpt("DEMO_J.XPT").shape[0] else pd.DataFrame(columns=["SEQN"])

# Re-build merged with lab columns
df = base.copy()
for lab_df in [fertin, cbc, vid, folate, biopro, demo]:
    if "SEQN" in lab_df.columns and len(lab_df.columns) > 1:
        # Try to match on index (base CSV dropped SEQN, so use positional merge via row count)
        pass  # handled below

# Simpler: re-merge from scratch using SEQN
demo2 = read_xpt("DEMO_J.XPT")
if demo2.shape[0]:
    demo2 = demo2[["SEQN","RIDAGEYR","RIAGENDR"]].copy()
    demo2["age"]    = demo2["RIDAGEYR"]
    demo2["female"] = (demo2["RIAGENDR"] == 2).astype(float)
    demo2 = demo2[demo2["age"] >= 18]

    lab_merge = demo2[["SEQN","age","female"]].copy()
    for lab_df in [fertin, cbc, vid, folate, biopro]:
        if "SEQN" in lab_df.columns and len(lab_df.columns) > 1:
            lab_merge = lab_merge.merge(lab_df, on="SEQN", how="left")

    # Merge dietary from base (which has d_* columns and labels)
    base_cols = ["age","female","bmi"] + [c for c in base.columns if c.startswith("d_")]
    label_cols_present = [c for c in base.columns if not c.startswith("d_") and c not in ["age","female","bmi"]]
    all_labels = [c for c in label_cols_present if base[c].isin([0.0,1.0,np.nan]).all()]

    # Build final df: lab columns + base dietary + labels aligned by row index
    # base and lab_merge both filtered to age>=18, same NHANES cycle → align on row count
    df = pd.concat([
        lab_merge.reset_index(drop=True),
        base[[c for c in base.columns if c not in ["age","female"]]].reset_index(drop=True)
    ], axis=1)
else:
    df = base.copy()

print(f"  Shape: {df.shape}")
print(f"  Lab columns present: {[c for c in df.columns if c.startswith('LBX') or c.startswith('LBD')]}")

# ── RDA reference (ICMR-NIN + WHO) ───────────────────────────────────────────
RDA = {
    "iron":        18.0,   # mg (women avg; men 8 mg)
    "calcium":     800.0,  # mg
    "vitamin_d":   15.0,   # µg (600 IU)
    "folate":      400.0,  # µg DFE
    "vitamin_b12": 2.4,    # µg
    "vitamin_c":   90.0,   # mg
    "vitamin_a":   800.0,  # µg RAE
    "vitamin_e":   15.0,   # mg
    "vitamin_k":   120.0,  # µg
    "vitamin_b1":  1.2,    # mg
    "vitamin_b2":  1.3,    # mg
    "vitamin_b3":  16.0,   # mg NE
    "vitamin_b6":  1.7,    # mg
    "magnesium":   350.0,  # mg
    "zinc":        11.0,   # mg
    "selenium":    55.0,   # µg
    "copper":      0.9,    # mg
    "potassium":   3500.0, # mg
    "phosphorus":  700.0,  # mg
    "omega3":      1600.0, # mg
}

# Dietary columns per nutrient
DIETARY_COL = {
    "iron":        "d_iron",
    "calcium":     "d_calcium",
    "vitamin_d":   "d_vitamin_d",
    "folate":      "d_folate",
    "vitamin_b12": "d_vitamin_b12",
    "vitamin_c":   "d_vitamin_c",
    "vitamin_a":   "d_vitamin_a",
    "vitamin_e":   "d_vitamin_e",
    "vitamin_k":   "d_vitamin_k",
    "vitamin_b1":  "d_vitamin_b1",
    "vitamin_b2":  "d_vitamin_b2",
    "vitamin_b3":  "d_vitamin_b3",
    "vitamin_b6":  "d_vitamin_b6",
    "magnesium":   "d_magnesium",
    "zinc":        "d_zinc",
    "selenium":    "d_selenium",
    "copper":      "d_copper",
    "potassium":   "d_potassium",
    "phosphorus":  "d_phosphorus",
    "omega3":      "d_omega3",
}

# ── Layer 2: Blood signal ─────────────────────────────────────────────────────
def blood_signal_iron(df):
    sig = pd.Series(np.nan, index=df.index)
    ferritin = df.get("LBXFER", pd.Series(np.nan, index=df.index)) if "LBXFER" in df.columns else pd.Series(np.nan, index=df.index)
    hgb      = df.get("LBXHGB", pd.Series(np.nan, index=df.index)) if "LBXHGB" in df.columns else pd.Series(np.nan, index=df.index)

    # ferritin signal
    f_sig = pd.Series(np.nan, index=df.index)
    f_sig[ferritin < 12]  = 0.90
    f_sig[(ferritin >= 12) & (ferritin < 20)] = 0.50
    f_sig[(ferritin >= 20) & (ferritin < 30)] = 0.10
    f_sig[ferritin >= 30] = -0.20

    # hemoglobin signal
    h_sig = pd.Series(np.nan, index=df.index)
    cutoff_f = 12; cutoff_m = 13
    is_f = df.get("female", pd.Series(0, index=df.index)) == 1
    h_sig[is_f  & (hgb < cutoff_f - 2)] = 0.90
    h_sig[is_f  & (hgb >= cutoff_f - 2) & (hgb < cutoff_f)] = 0.50
    h_sig[is_f  & (hgb >= cutoff_f)] = -0.10
    h_sig[~is_f & (hgb < cutoff_m - 2)] = 0.90
    h_sig[~is_f & (hgb >= cutoff_m - 2) & (hgb < cutoff_m)] = 0.50
    h_sig[~is_f & (hgb >= cutoff_m)] = -0.10

    # Average available signals
    both = f_sig.notna() & h_sig.notna()
    only_f = f_sig.notna() & h_sig.isna()
    only_h = f_sig.isna() & h_sig.notna()
    sig[both]   = (f_sig[both] + h_sig[both]) / 2
    sig[only_f] = f_sig[only_f]
    sig[only_h] = h_sig[only_h]
    return sig

def blood_signal_vitd(df):
    if "LBXVIDMS" not in df.columns: return pd.Series(np.nan, index=df.index)
    v = df["LBXVIDMS"]
    sig = pd.Series(np.nan, index=df.index)
    sig[v < 30]  = 0.90
    sig[(v >= 30) & (v < 50)] = 0.55
    sig[(v >= 50) & (v < 75)] = 0.10
    sig[v >= 75] = -0.25
    return sig

def blood_signal_folate(df):
    if "LBDRFO" not in df.columns: return pd.Series(np.nan, index=df.index)
    f = df["LBDRFO"]
    sig = pd.Series(np.nan, index=df.index)
    sig[f < 140] = 0.80
    sig[(f >= 140) & (f < 200)] = 0.30
    sig[f >= 200] = -0.20
    return sig

def blood_signal_calcium(df):
    if "LBXSCA" not in df.columns: return pd.Series(np.nan, index=df.index)
    c = df["LBXSCA"]
    sig = pd.Series(np.nan, index=df.index)
    sig[c < 8.5] = 0.80
    sig[(c >= 8.5) & (c < 9.0)] = 0.20
    sig[(c >= 9.0) & (c <= 10.5)] = -0.15
    sig[c > 10.5] = -0.70
    return sig

def blood_signal_phosphorus(df):
    if "LBXSPH" not in df.columns: return pd.Series(np.nan, index=df.index)
    p = df["LBXSPH"]
    sig = pd.Series(np.nan, index=df.index)
    sig[p < 2.5] = 0.80
    sig[(p >= 2.5) & (p < 3.0)] = 0.20
    sig[(p >= 3.0) & (p <= 4.5)] = -0.10
    sig[p > 4.5] = -0.60
    return sig

BLOOD_SIGNAL_FNS = {
    "iron":       blood_signal_iron,
    "vitamin_d":  blood_signal_vitd,
    "folate":     blood_signal_folate,
    "calcium":    blood_signal_calcium,
    "phosphorus": blood_signal_phosphorus,
}

# ── Layer 5: Food signal ──────────────────────────────────────────────────────
def food_signal(intake_series, rda):
    pct = intake_series / rda
    sig = pd.Series(np.nan, index=intake_series.index)
    sig[pct < 0.40] = 0.85
    sig[(pct >= 0.40) & (pct < 0.60)] = 0.65
    sig[(pct >= 0.60) & (pct < 0.80)] = 0.35
    sig[(pct >= 0.80) & (pct < 1.00)] = 0.10
    sig[(pct >= 1.00) & (pct < 1.50)] = -0.15
    sig[pct >= 1.50] = -0.35
    sig[intake_series.isna()] = np.nan
    return sig

# ── Build signal features ─────────────────────────────────────────────────────
print("\nComputing 5-layer signals per nutrient...")
NUTRIENTS = [n for n in RDA.keys() if n in df.columns or n in DIETARY_COL]

signal_rows = []
label_cols  = [n for n in NUTRIENTS if n in df.columns]

for nutrient in label_cols:
    # Layer 2: Blood
    if nutrient in BLOOD_SIGNAL_FNS:
        b_sig = BLOOD_SIGNAL_FNS[nutrient](df)
    else:
        b_sig = pd.Series(np.nan, index=df.index)

    # Layer 5: Food
    dcol = DIETARY_COL.get(nutrient)
    if dcol and dcol in df.columns:
        f_sig = food_signal(df[dcol], RDA[nutrient])
    else:
        f_sig = pd.Series(np.nan, index=df.index)

    # Layer 1, 3, 4: Not in NHANES → NaN (model treats as "no data")
    h_sig = pd.Series(np.nan, index=df.index)  # history
    s_sig = pd.Series(np.nan, index=df.index)  # symptoms
    v_sig = pd.Series(np.nan, index=df.index)  # visual

    label = df[nutrient]
    mask  = label.notna() & (b_sig.notna() | f_sig.notna())

    tmp = pd.DataFrame({
        "nutrient":      nutrient,
        "blood_sig":     b_sig,
        "symptom_sig":   s_sig,
        "food_sig":      f_sig,
        "history_sig":   h_sig,
        "visual_sig":    v_sig,
        "age":           df["age"],
        "female":        df["female"],
        "bmi":           df.get("bmi", pd.Series(np.nan, index=df.index)),
        "label":         label,
    })[mask]
    signal_rows.append(tmp)
    print(f"  {nutrient:20s}: {mask.sum()} rows  blood={b_sig.notna().sum()}  food={f_sig.notna().sum()}")

signal_df = pd.concat(signal_rows, ignore_index=True)
print(f"\nTotal signal rows: {len(signal_df)}")
print(f"Nutrients: {signal_df['nutrient'].unique().tolist()}")

out_path = OUT / "nhanes_signals.csv"
signal_df.to_csv(out_path, index=False)
print(f"Saved → {out_path}")
