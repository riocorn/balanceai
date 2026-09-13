import pandas as pd
import numpy as np
import json
import os

DATA = "/home/abhay/Downloads/medical/balanceai/data/nhanes"
OUT = "/home/abhay/Downloads/medical/balanceai/data/nhanes/nhanes_training_dataset.json"

os.chdir(DATA)

demo = pd.read_sas("DEMO_J.xpt", format="xport", encoding="utf-8")[["SEQN","RIAGENDR","RIDAGEYR","RIDRETH3","INDFMPIR"]]
demo.columns = ["seqn","sex","age","race","poverty_ratio"]

vid = pd.read_sas("VID_J.xpt", format="xport", encoding="utf-8")[["SEQN","LBXVIDMS"]]
vid.columns = ["seqn","vitd_nmol"]

ferritin = pd.read_sas("FERTIN_J.xpt", format="xport", encoding="utf-8")[["SEQN","LBXFER"]]
ferritin.columns = ["seqn","ferritin_ug"]

folate = pd.read_sas("FOLATE_J.xpt", format="xport", encoding="utf-8")[["SEQN","LBDRFO"]]
folate.columns = ["seqn","rbc_folate_nmol"]

biopro = pd.read_sas("BIOPRO_J.xpt", format="xport", encoding="utf-8")
biopro_cols = {
    "SEQN": "seqn",
    "LBXSCA": "calcium_mg",    # calcium mg/dL
    "LBXSPH": "phosphorus_mg", # phosphorus mg/dL
    "LBXSKSI": "potassium_mmol",
    "LBXSNASI": "sodium_mmol",
    "LBXSTP": "total_protein_g",
    "LBXSUA": "uric_acid_mg",
    "LBXSGB": "globulin_g",
}
biopro = biopro[[c for c in biopro_cols if c in biopro.columns]].rename(columns=biopro_cols)

iron = pd.read_sas("FETIB_J.xpt", format="xport", encoding="utf-8")
iron_cols_map = {c: c for c in iron.columns[:6]}
iron.columns = iron.columns[:len(iron.columns)]

vitaec = pd.read_sas("VITAEC_J.xpt", format="xport", encoding="utf-8")

vic = pd.read_sas("VIC_J.xpt", format="xport", encoding="utf-8")
vic = vic[["SEQN"] + [c for c in vic.columns if "LBXV" in c or "LBX" in c][:3]]
vic.columns = ["seqn"] + [f"vitc_{i}" for i in range(len(vic.columns)-1)]

slq = pd.read_sas("SLQ_J.xpt", format="xport", encoding="utf-8")
slq = slq[["SEQN"] + [c for c in slq.columns if c not in ["SEQN"]][:5]]
slq.columns = ["seqn"] + [f"sleep_{i}" for i in range(len(slq.columns)-1)]

mcq = pd.read_sas("MCQ_J.xpt", format="xport", encoding="utf-8")

df = demo.copy()
for other in [vid, ferritin, folate, biopro]:
    df = df.merge(other, on="seqn", how="left")

print(f"Merged dataset: {df.shape}")
print(f"Columns: {list(df.columns)}")

def classify_deficiency(row):
    labels = {}

    vd = row.get("vitd_nmol", np.nan)
    if pd.notna(vd):
        labels["vitamin_d"] = 1 if vd < 50 else (0.5 if vd < 75 else 0)

    fer = row.get("ferritin_ug", np.nan)
    age = row.get("age", 30)
    sex = row.get("sex", 2)
    if pd.notna(fer):
        threshold = 12 if sex == 2 else 20
        labels["iron"] = 1 if fer < threshold else (0.5 if fer < threshold * 1.5 else 0)

    fol = row.get("rbc_folate_nmol", np.nan)
    if pd.notna(fol):
        labels["folate"] = 1 if fol < 305 else (0.5 if fol < 400 else 0)

    ca = row.get("calcium_mg", np.nan)
    if pd.notna(ca):
        labels["calcium"] = 1 if ca < 8.5 else 0

    return labels


DEFICIENCY_LIST = ["vitamin_d","iron","vitamin_b12","zinc","calcium","magnesium",
                   "vitamin_c","vitamin_a","folate","iodine","omega3","selenium","vitamin_b6","potassium","copper"]

training_records = []
for _, row in df.iterrows():
    row_dict = row.to_dict()
    def_labels = classify_deficiency(row_dict)

    features = {}
    features["age"] = float(row_dict.get("age", 30) or 30)
    features["sex_female"] = 1 if row_dict.get("sex") == 2 else 0
    features["poverty_ratio"] = float(row_dict.get("poverty_ratio", 2) or 2)

    vd = row_dict.get("vitd_nmol", np.nan)
    features["vitd_level"] = float(vd) if pd.notna(vd) else -1
    fer = row_dict.get("ferritin_ug", np.nan)
    features["ferritin_level"] = float(fer) if pd.notna(fer) else -1
    fol = row_dict.get("rbc_folate_nmol", np.nan)
    features["folate_level"] = float(fol) if pd.notna(fol) else -1
    ca = row_dict.get("calcium_mg", np.nan)
    features["calcium_level"] = float(ca) if pd.notna(ca) else -1

    label_vector = [def_labels.get(d, 0.1) for d in DEFICIENCY_LIST]

    training_records.append({
        "features": features,
        "deficiency_labels": {d: def_labels.get(d, 0.1) for d in DEFICIENCY_LIST},
    })

with open(OUT, "w") as f:
    json.dump({"records": training_records[:5000], "total": len(training_records), "deficiency_list": DEFICIENCY_LIST}, f)

print(f"\nTraining records created: {len(training_records)}")
print(f"Saved: {OUT}")

vd_def = sum(1 for r in training_records if r["deficiency_labels"]["vitamin_d"] == 1)
iron_def = sum(1 for r in training_records if r["deficiency_labels"]["iron"] == 1)
folate_def = sum(1 for r in training_records if r["deficiency_labels"]["folate"] == 1)
print(f"\nPrevalence in NHANES 2017-18:")
print(f"  Vitamin D deficient (<50 nmol/L): {vd_def}/{len(training_records)} = {vd_def/len(training_records)*100:.1f}%")
print(f"  Iron deficient (low ferritin): {iron_def}/{len(training_records)} = {iron_def/len(training_records)*100:.1f}%")
print(f"  Folate deficient: {folate_def}/{len(training_records)} = {folate_def/len(training_records)*100:.1f}%")
