"""
NHANES Dataset Builder
Merges lab values + dietary recall + demographics into a clean training CSV.
Creates binary deficiency labels (1=deficient, 0=ok) per nutrient.
"""
import pandas as pd
import numpy as np
import pyreadstat
from pathlib import Path

DATA  = Path(__file__).parent / "nhanes_data"
OUT   = Path(__file__).parent / "processed"
OUT.mkdir(exist_ok=True)


def read_xpt(name):
    path = DATA / name
    if not path.exists():
        print(f"  [MISSING] {name}")
        return pd.DataFrame()
    try:
        df, _ = pyreadstat.read_xport(str(path))
        df.columns = df.columns.str.upper()
        return df
    except Exception as e:
        print(f"  [SKIP] {name}: {e}")
        return pd.DataFrame()


# ── Load all files ────────────────────────────────────────────────────────────
print("Loading XPT files...")
demo   = read_xpt("DEMO_J.XPT")
dr1    = read_xpt("DR1TOT_J.XPT")
vid    = read_xpt("VID_J.XPT")
fertin = read_xpt("FERTIN_J.XPT")
cbc    = read_xpt("CBC_J.XPT")
folate = read_xpt("FOLATE_J.XPT")
biopro = read_xpt("BIOPRO_J.XPT")
cusezn = read_xpt("CUSEZN_J.XPT")
bmx    = read_xpt("BMX_J.XPT")

# ── Merge on SEQN (respondent ID) ────────────────────────────────────────────
print("Merging datasets on SEQN...")
dfs = [demo, dr1, vid, fertin, cbc, folate, biopro, cusezn, bmx]
df  = dfs[0][["SEQN"]]
for d in dfs:
    if d.empty: continue
    cols = ["SEQN"] + [c for c in d.columns if c != "SEQN"]
    df = df.merge(d[cols], on="SEQN", how="left")

print(f"  Merged shape: {df.shape}")

# ── Demographics features ─────────────────────────────────────────────────────
# RIAGENDR: 1=Male 2=Female
# RIDAGEYR: age in years
# BMXBMI: BMI
df["age"]    = df.get("RIDAGEYR", pd.Series(dtype=float))
df["female"] = (df.get("RIAGENDR", pd.Series(dtype=float)) == 2).astype(float)
df["bmi"]    = df.get("BMXBMI", pd.Series(dtype=float))

# Filter: adults 18+ only (children have different RDAs, different disease profiles)
df = df[df["age"] >= 18].copy()
print(f"  After adult filter: {len(df)} rows")

# ── Dietary intake features (from 24-hour recall Day 1) ──────────────────────
# Column mapping: NHANES DR1TOT column → our nutrient key
DIETARY_COLS = {
    "DR1TIRON":  "d_iron",
    "DR1TCALC":  "d_calcium",
    "DR1TZINC":  "d_zinc",
    "DR1TVB12":  "d_vitamin_b12",
    "DR1TFDFE":  "d_folate",          # Dietary Folate Equivalents (µg DFE)
    "DR1TVD":    "d_vitamin_d",       # µg (IU/40)
    "DR1TMAGN":  "d_magnesium",
    "DR1TPOTA":  "d_potassium",
    "DR1TVB6":   "d_vitamin_b6",
    "DR1TATOC":  "d_vitamin_e",
    "DR1TVC":    "d_vitamin_c",
    "DR1TVARA":  "d_vitamin_a",       # RAE µg
    "DR1TVB1":   "d_vitamin_b1",
    "DR1TVB2":   "d_vitamin_b2",
    "DR1TNIAC":  "d_vitamin_b3",
    "DR1TVK":    "d_vitamin_k",
    "DR1TPHOS":  "d_phosphorus",
    "DR1TSELE":  "d_selenium",
    "DR1TCOPP":  "d_copper",
    # omega3 = ALA (P183) + EPA (P205) + DPA (P225) + DHA (P226) — all in grams → convert to mg
    "DR1TP183":  "d_ala_g",
    "DR1TP205":  "d_epa_g",
    "DR1TP225":  "d_dpa_g",
    "DR1TP226":  "d_dha_g",
    "DR1TKCAL":  "d_kcal",
    "DR1TPROT":  "d_protein",
    "DR1TCARB":  "d_carb",
    "DR1TTFAT":  "d_fat",
    "DR1TPFAT":  "d_pufa",
    "DR1TSFAT":  "d_sfa",
}

for nhanes_col, our_col in DIETARY_COLS.items():
    df[our_col] = df.get(nhanes_col, pd.Series(np.nan, index=df.index))

# Omega3 total (grams → mg)
df["d_omega3"] = (
    df["d_ala_g"].fillna(0) + df["d_epa_g"].fillna(0) +
    df["d_dpa_g"].fillna(0) + df["d_dha_g"].fillna(0)
) * 1000

# Normalise dietary intake per 2000 kcal (removes body-size effect)
kcal = df["d_kcal"].replace(0, np.nan)
for col in [c for c in df.columns if c.startswith("d_") and c != "d_kcal"]:
    df[col + "_per2k"] = df[col] / kcal * 2000

# ── Ground-truth LABELS from lab values ──────────────────────────────────────
# Confirmed NHANES 2017-2018 column names from actual XPT inspection.

labels = {}

# Iron — ferritin < 15 ng/mL  OR  hemoglobin < 12 (women) / <13 (men)
ferritin_low = df.get("LBXFER", pd.Series(np.nan, index=df.index)) < 15
hgb          = df.get("LBXHGB", pd.Series(np.nan, index=df.index))
hgb_low      = ((df["female"] == 1) & (hgb < 12)) | ((df["female"] == 0) & (hgb < 13))
labels["iron"] = ((ferritin_low | hgb_low) & (ferritin_low.notna() | hgb_low.notna())).astype(float)
labels["iron"][labels["iron"].isna()] = np.nan

# Vitamin D — LBXVIDMS in nmol/L; < 50 nmol/L = deficient/insufficient
vitd = df.get("LBXVIDMS", pd.Series(np.nan, index=df.index))
labels["vitamin_d"] = (vitd < 50).astype(float)

# Folate — RBC Folate LBDRFO in ng/mL; < 140 ng/mL = deficient (WHO cutoff)
fol = df.get("LBDRFO", pd.Series(np.nan, index=df.index))
labels["folate"] = (fol < 140).astype(float)

# Calcium — LBXSCA in mg/dL; < 8.5 mg/dL = hypocalcemia
ca = df.get("LBXSCA", pd.Series(np.nan, index=df.index))
labels["calcium"] = (ca < 8.5).astype(float)

# Phosphorus — LBXSPH in mg/dL; < 2.5 mg/dL = hypophosphatemia
ph = df.get("LBXSPH", pd.Series(np.nan, index=df.index))
labels["phosphorus"] = (ph < 2.5).astype(float)

# ── Dietary-intake proxy labels (no serum data in this NHANES cycle) ─────────
# intake < 60% RDA = likely deficient (validated proxy from nutrition epidemiology)
DIETARY_LABELS = {
    "vitamin_b12": ("d_vitamin_b12", 2.4),    # µg
    "vitamin_c":   ("d_vitamin_c",   90),      # mg
    "vitamin_a":   ("d_vitamin_a",  800),      # µg RAE
    "vitamin_e":   ("d_vitamin_e",   15),      # mg
    "vitamin_k":   ("d_vitamin_k",  120),      # µg
    "vitamin_b1":  ("d_vitamin_b1",  1.2),     # mg
    "vitamin_b2":  ("d_vitamin_b2",  1.3),     # mg
    "vitamin_b3":  ("d_vitamin_b3",  16),      # mg NE
    "vitamin_b6":  ("d_vitamin_b6",  1.7),     # mg
    "magnesium":   ("d_magnesium",  350),      # mg
    "zinc":        ("d_zinc",        11),      # mg
    "selenium":    ("d_selenium",    55),      # µg
    "copper":      ("d_copper",      0.9),     # mg
    "potassium":   ("d_potassium", 3500),      # mg (WHO AI)
    "omega3":      ("d_omega3",    1600),      # mg total n-3 (ALA+EPA+DHA)
    # skip: manganese (column missing), vitamin_b5 (column missing)
}
for nutrient, (col, rda) in DIETARY_LABELS.items():
    intake = df.get(col, pd.Series(np.nan, index=df.index))
    pct    = intake / rda
    # <60% = deficient, skip if all NaN or all same value
    lbl = (pct < 0.60).astype(float)
    lbl[intake.isna()] = np.nan
    if lbl.mean() in (0.0, 1.0):
        print(f"  [skip label] {nutrient}: prevalence={lbl.mean()*100:.0f}% (no variation)")
        continue
    labels[nutrient] = lbl

# Nutrients without any data → skip (chromium, iodine, vitamin_b5, vitamin_b7)
# These will be handled by the rule-based layer, not ML

# ── Assemble training DataFrame ───────────────────────────────────────────────
feature_cols = (
    ["age", "female", "bmi"] +
    [c for c in df.columns if c.startswith("d_") and not c.endswith("_per2k") and c not in ("d_epa","d_dha")] +
    [c for c in df.columns if c.endswith("_per2k")]
)

# Only keep rows where at least 3 label columns are non-NaN
label_df = pd.DataFrame(labels, index=df.index)
valid_mask = label_df.notna().sum(axis=1) >= 3
df_final = df[valid_mask].copy()
label_df  = label_df[valid_mask]

# Merge features + labels
feature_df = df_final[[c for c in feature_cols if c in df_final.columns]]
out_df = pd.concat([feature_df, label_df], axis=1)

# Drop rows missing all features
out_df = out_df.dropna(subset=["age"])

print(f"  Final dataset: {len(out_df)} rows, {len(feature_df.columns)} features, {len(label_df.columns)} labels")
print(f"  Labels: {list(label_df.columns)}")
print(f"\nDeficiency prevalence:")
for col in label_df.columns:
    pct = label_df[col].mean() * 100
    print(f"  {col:20s}: {pct:.1f}%")

out_path = OUT / "nhanes_training.csv"
out_df.to_csv(out_path, index=False)
print(f"\nSaved → {out_path}")
