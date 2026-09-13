import pandas as pd
import numpy as np
import json
import os
import urllib.request

DATA = "/home/abhay/Downloads/medical/balanceai/data/nhanes"
OUT = "/home/abhay/Downloads/medical/balanceai/data/nhanes/nhanes_extended_dataset.json"
BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles"
BASE_URL_H = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles"

os.makedirs(DATA, exist_ok=True)
os.chdir(DATA)

def download(fname, cycle_url=BASE_URL):
    path = os.path.join(DATA, fname)
    if not os.path.exists(path):
        url = f"{cycle_url}/{fname}"
        print(f"  Downloading {fname}...")
        try:
            urllib.request.urlretrieve(url, path)
            print(f"  Done: {fname}")
        except Exception as e:
            print(f"  FAILED {fname}: {e}")
            return False
    else:
        print(f"  Already exists: {fname}")
    return True

print("=== Downloading NHANES extended lab files ===")
files_2017 = [
    "VITAEC_J.xpt",  # Vitamin A, E
    "VIC_J.xpt",     # Vitamin C
    "PBCD_J.xpt",    # Selenium, Manganese
    "UIO_J.xpt",     # Iodine (urine)
    "CBC_J.xpt",     # Hemoglobin
    "UM_J.xpt",      # Copper (urine)
    "TFR_J.xpt",     # Transferrin receptor
    "DEMO_J.xpt",
    "BIOPRO_J.xpt",  # Ca, K, Na, Phosphorus
    "FERTIN_J.xpt",
    "VID_J.xpt",
    "FOLATE_J.xpt",
]

for f in files_2017:
    download(f)

# B12 from 2013-14 cycle (correct filename)
print("\nDownloading B12 from 2013-14 cycle...")
download("DEMO_H.xpt", BASE_URL_H)
download("VITB12_H.xpt", BASE_URL_H)

print("\n=== Processing all files ===")

def safe_read(fname):
    try:
        return pd.read_sas(fname, format="xport", encoding="utf-8")
    except Exception as e:
        print(f"  Error reading {fname}: {e}")
        return None

demo = safe_read("DEMO_J.xpt")
if demo is not None:
    demo = demo[["SEQN","RIAGENDR","RIDAGEYR","RIDRETH3","INDFMPIR"]].copy()
    demo.columns = ["seqn","sex","age","race","poverty_ratio"]

# Vitamin D
vid = safe_read("VID_J.xpt")
if vid is not None:
    vid = vid[["SEQN","LBXVIDMS"]].rename(columns={"SEQN":"seqn","LBXVIDMS":"vitd_nmol"})

# Ferritin (Iron)
ferritin = safe_read("FERTIN_J.xpt")
if ferritin is not None:
    ferritin = ferritin[["SEQN","LBXFER"]].rename(columns={"SEQN":"seqn","LBXFER":"ferritin_ug"})

# RBC Folate
folate = safe_read("FOLATE_J.xpt")
if folate is not None:
    folate = folate[["SEQN","LBDRFO"]].rename(columns={"SEQN":"seqn","LBDRFO":"rbc_folate_nmol"})

# Biochemistry (Ca, Mg, K, P, Na)
biopro = safe_read("BIOPRO_J.xpt")
if biopro is not None:
    cols_map = {"SEQN":"seqn","LBXSCA":"calcium_mg","LBXSMG":"magnesium_mg",
                "LBXSKSI":"potassium_mmol","LBXSNASI":"sodium_mmol","LBXSTP":"total_protein_g",
                "LBXSPH":"phosphorus_mg"}
    avail = {k:v for k,v in cols_map.items() if k in biopro.columns}
    biopro = biopro[list(avail.keys())].rename(columns=avail)

# Vitamin A (retinol — LBXVIA in umol/L) and Vitamin E (alpha-tocopherol — LBXVIE in ug/dL)
vitaec = safe_read("VITAEC_J.xpt")
vita = vite = None
if vitaec is not None:
    if "LBXVIA" in vitaec.columns:
        vita = vitaec[["SEQN","LBXVIA"]].rename(columns={"SEQN":"seqn","LBXVIA":"vita_umol"})
    if "LBXVIE" in vitaec.columns:
        vite = vitaec[["SEQN","LBXVIE"]].rename(columns={"SEQN":"seqn","LBXVIE":"vite_ug_dl"})

# Vitamin C (LBXVIC in mg/dL)
vic = safe_read("VIC_J.xpt")
vitc = None
if vic is not None and "LBXVIC" in vic.columns:
    vitc = vic[["SEQN","LBXVIC"]].rename(columns={"SEQN":"seqn","LBXVIC":"vitc_mg_dl"})

# Selenium (LBXBSE in ug/L) and Manganese (LBXBMN in ug/L) from blood
pbcd = safe_read("PBCD_J.xpt")
selenium = manganese = None
if pbcd is not None:
    if "LBXBSE" in pbcd.columns:
        selenium = pbcd[["SEQN","LBXBSE"]].rename(columns={"SEQN":"seqn","LBXBSE":"selenium_ug"})
    if "LBXBMN" in pbcd.columns:
        manganese = pbcd[["SEQN","LBXBMN"]].rename(columns={"SEQN":"seqn","LBXBMN":"manganese_ug_l"})

# Iodine urine (URXUIO in ug/L)
uio = safe_read("UIO_J.xpt")
iodine = None
if uio is not None:
    icol = [c for c in uio.columns if "URXUIO" in c]
    if icol:
        iodine = uio[["SEQN", icol[0]]].rename(columns={"SEQN":"seqn", icol[0]:"iodine_ug_l"})

# CBC (hemoglobin — LBXHGB in g/dL)
cbc = safe_read("CBC_J.xpt")
hgb = None
if cbc is not None and "LBXHGB" in cbc.columns:
    hgb = cbc[["SEQN","LBXHGB"]].rename(columns={"SEQN":"seqn","LBXHGB":"hemoglobin_g_dl"})

# Urine metals — Copper (URXUCO ug/L), Zinc (URXUZN if exists)
um = safe_read("UM_J.xpt")
copper = zinc_u = None
if um is not None:
    if "URXUCO" in um.columns:
        copper = um[["SEQN","URXUCO"]].rename(columns={"SEQN":"seqn","URXUCO":"copper_ug_l"})
    zn_col = [c for c in um.columns if "ZN" in c.upper() and "URX" in c]
    if zn_col:
        zinc_u = um[["SEQN", zn_col[0]]].rename(columns={"SEQN":"seqn", zn_col[0]:"zinc_ug_l"})

# B12 from 2013-14 cycle
b12 = None
try:
    b12_raw = safe_read("VITB12_H.xpt")
    if b12_raw is not None:
        b12col = [c for c in b12_raw.columns if "B12" in c.upper() or "LBXB12" in c]
        if b12col:
            b12 = b12_raw[["SEQN", b12col[0]]].rename(columns={"SEQN":"seqn", b12col[0]:"b12_pmol"})
            print(f"  B12 records: {len(b12)}")
except Exception as e:
    print(f"  B12 load failed: {e}")

# Merge everything
print("\nMerging all datasets...")
df = demo.copy()
for other in [vid, ferritin, folate, biopro, vita, vite, vitc, selenium, manganese, iodine, hgb, copper, zinc_u, b12]:
    if other is not None:
        df = df.merge(other, on="seqn", how="left")

print(f"Merged shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Deficiency classification
def classify_all(row):
    labels = {}
    sex = row.get("sex", 2)

    vd = row.get("vitd_nmol", np.nan)
    if pd.notna(vd):
        labels["vitamin_d"] = 1 if vd < 30 else (0.5 if vd < 50 else 0)

    fer = row.get("ferritin_ug", np.nan)
    if pd.notna(fer):
        thr = 12 if sex == 2 else 20
        labels["iron"] = 1 if fer < thr else (0.5 if fer < thr * 1.5 else 0)

    hb = row.get("hemoglobin_g_dl", np.nan)
    if pd.notna(hb) and "iron" not in labels:
        thr_hb = 12.0 if sex == 2 else 13.0
        labels["iron"] = 1 if hb < thr_hb else 0

    fol = row.get("rbc_folate_nmol", np.nan)
    if pd.notna(fol):
        labels["folate"] = 1 if fol < 305 else (0.5 if fol < 400 else 0)

    ca = row.get("calcium_mg", np.nan)
    if pd.notna(ca):
        labels["calcium"] = 1 if ca < 8.5 else 0

    mg = row.get("magnesium_mg", np.nan)
    if pd.notna(mg):
        labels["magnesium"] = 1 if mg < 0.75 else (0.5 if mg < 0.85 else 0)

    va = row.get("vita_umol", np.nan)
    if pd.notna(va):
        labels["vitamin_a"] = 1 if va < 0.7 else (0.5 if va < 1.05 else 0)

    vc = row.get("vitc_mg_dl", np.nan)
    if pd.notna(vc):
        labels["vitamin_c"] = 1 if vc < 0.2 else (0.5 if vc < 0.4 else 0)

    se = row.get("selenium_ug", np.nan)
    if pd.notna(se):
        labels["selenium"] = 1 if se < 85 else (0.5 if se < 100 else 0)

    io = row.get("iodine_ug_l", np.nan)
    if pd.notna(io):
        labels["iodine"] = 1 if io < 50 else (0.5 if io < 100 else 0)

    ve = row.get("vite_ug_dl", np.nan)
    if pd.notna(ve):
        labels["vitamin_e"] = 1 if ve < 500 else (0.5 if ve < 700 else 0)

    ph = row.get("phosphorus_mg", np.nan)
    if pd.notna(ph):
        labels["phosphorus"] = 1 if ph < 2.5 else (0.5 if ph < 3.0 else 0)

    mn = row.get("manganese_ug_l", np.nan)
    if pd.notna(mn):
        labels["manganese"] = 1 if mn < 4.0 else 0

    b12v = row.get("b12_pmol", np.nan)
    if pd.notna(b12v):
        labels["vitamin_b12"] = 1 if b12v < 148 else (0.5 if b12v < 221 else 0)

    zn = row.get("zinc_ug_l", np.nan)
    if pd.notna(zn):
        labels["zinc"] = 1 if zn < 560 else (0.5 if zn < 700 else 0)

    return labels

DEFICIENCY_LIST = [
    "vitamin_d","iron","vitamin_b12","zinc","calcium","magnesium",
    "vitamin_c","vitamin_a","folate","iodine","omega3","selenium",
    "vitamin_b6","potassium","copper",
    "vitamin_e","vitamin_b1","vitamin_b2","vitamin_b3","vitamin_b5",
    "vitamin_b7","vitamin_k","phosphorus","manganese","chromium",
]

print("\nClassifying deficiencies...")
training_records = []
deficiency_counts = {d: 0 for d in DEFICIENCY_LIST}

for _, row in df.iterrows():
    row_dict = row.to_dict()
    def_labels = classify_all(row_dict)

    features = {
        "age": float(row_dict.get("age", 30) or 30),
        "sex_female": 1 if row_dict.get("sex") == 2 else 0,
        "poverty_ratio": float(row_dict.get("poverty_ratio", 2) or 2),
    }
    for col in ["vitd_nmol","ferritin_ug","rbc_folate_nmol","calcium_mg",
                "magnesium_mg","vita_umol","vitc_mg_dl","selenium_ug",
                "iodine_ug_l","hemoglobin_g_dl","copper_ug_l","zinc_ug_l",
                "vite_ug_dl","phosphorus_mg","manganese_ug_l","b12_pmol"]:
        v = row_dict.get(col, np.nan)
        features[col] = float(v) if pd.notna(v) else -1

    label_dict = {d: def_labels.get(d, 0.1) for d in DEFICIENCY_LIST}
    for d in DEFICIENCY_LIST:
        if def_labels.get(d, 0) == 1:
            deficiency_counts[d] += 1

    training_records.append({"features": features, "deficiency_labels": label_dict})

# Supplement with 2013-14 B12 data (different SEQN pool, process standalone)
print("\nProcessing 2013-14 B12 supplement...")
try:
    demo_h = safe_read("DEMO_H.xpt")
    vitb12_h = safe_read("VITB12_H.xpt")
    if demo_h is not None and vitb12_h is not None:
        demo_h2 = demo_h[["SEQN","RIAGENDR","RIDAGEYR","INDFMPIR"]].copy()
        demo_h2.columns = ["seqn","sex","age","poverty_ratio"]
        b12col = [c for c in vitb12_h.columns if "B12" in c.upper() or "LBXB12" in c]
        if b12col:
            b12_h = vitb12_h[["SEQN", b12col[0]]].rename(columns={"SEQN":"seqn", b12col[0]:"b12_pmol"})
            df_b12 = demo_h2.merge(b12_h, on="seqn", how="inner")
            print(f"  B12 supplement records: {len(df_b12)}")
            for _, row in df_b12.iterrows():
                row_dict = row.to_dict()
                b12v = row_dict.get("b12_pmol", np.nan)
                if pd.isna(b12v):
                    continue
                def_labels = {}
                if b12v < 148:
                    def_labels["vitamin_b12"] = 1
                elif b12v < 221:
                    def_labels["vitamin_b12"] = 0.5
                else:
                    def_labels["vitamin_b12"] = 0
                if def_labels.get("vitamin_b12", 0) > 0:
                    features = {
                        "age": float(row_dict.get("age", 30) or 30),
                        "sex_female": 1 if row_dict.get("sex") == 2 else 0,
                        "poverty_ratio": float(row_dict.get("poverty_ratio", 2) or 2),
                        "b12_pmol": float(b12v),
                    }
                    for col in ["vitd_nmol","ferritin_ug","rbc_folate_nmol","calcium_mg",
                                "magnesium_mg","vita_umol","vitc_mg_dl","selenium_ug",
                                "iodine_ug_l","hemoglobin_g_dl","copper_ug_l","zinc_ug_l",
                                "vite_ug_dl","phosphorus_mg","manganese_ug_l"]:
                        features[col] = -1
                    label_dict = {d: def_labels.get(d, 0.1) for d in DEFICIENCY_LIST}
                    if def_labels.get("vitamin_b12", 0) == 1:
                        deficiency_counts["vitamin_b12"] += 1
                    training_records.append({"features": features, "deficiency_labels": label_dict})
except Exception as e:
    print(f"  B12 supplement failed: {e}")

print(f"\nTotal records: {len(training_records)}")
print("\nDeficiency prevalence (confirmed cases):")
for d, cnt in deficiency_counts.items():
    if cnt > 0:
        pct = cnt / len(training_records) * 100
        print(f"  {d}: {cnt} ({pct:.1f}%)")

with open(OUT, "w") as f:
    json.dump({
        "records": training_records,
        "total": len(training_records),
        "deficiency_list": DEFICIENCY_LIST,
        "deficiency_counts": deficiency_counts,
        "source": "NHANES 2017-18 + B12 from 2013-14 (VitD, Iron, Folate, Ca, VitA, VitC, VitE, Se, Mn, Iodine, Hgb, Phosphorus, B12)"
    }, f)

print(f"\nSaved: {OUT}")
