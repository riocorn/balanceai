"""
NHANES 2017-2018 Data Downloader
Downloads the exact XPT files needed for nutrient deficiency model training.
"""
import urllib.request
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "nhanes_data"
DATA_DIR.mkdir(exist_ok=True)

BASE = "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018"

FILES = {
    # Demographics — age, gender, BMI
    "DEMO_J.XPT":   f"{BASE}/DEMO_J.XPT",
    # Dietary recall Day 1 — actual nutrient intake
    "DR1TOT_J.XPT": f"{BASE}/DR1TOT_J.XPT",
    # Lab: Vitamin D (25-OH-D serum) — gold standard
    "VID_J.XPT":    f"{BASE}/VID_J.XPT",
    # Lab: Ferritin (iron stores) — gold standard for iron
    "FERTIN_J.XPT": f"{BASE}/FERTIN_J.XPT",
    # Lab: CBC — hemoglobin
    "CBC_J.XPT":    f"{BASE}/CBC_J.XPT",
    # Lab: B12 + Folate — gold standard
    "FOLATE_J.XPT": f"{BASE}/FOLATE_J.XPT",
    # Lab: Biochemistry panel — calcium, magnesium, phosphorus, albumin
    "BIOPRO_J.XPT": f"{BASE}/BIOPRO_J.XPT",
    # Lab: Copper, Selenium, Zinc
    "CUSEZN_J.XPT": f"{BASE}/CUSEZN_J.XPT",
    # Body measures — weight, height, BMI
    "BMX_J.XPT":    f"{BASE}/BMX_J.XPT",
}

def download(name, url):
    dest = DATA_DIR / name
    if dest.exists():
        print(f"  [skip] {name} already exists ({dest.stat().st_size // 1024} KB)")
        return
    print(f"  [dl]   {name}  ...", end="", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print(f" done ({dest.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f" FAILED: {e}")

if __name__ == "__main__":
    print("Downloading NHANES 2017-2018 files...\n")
    for name, url in FILES.items():
        download(name, url)
    print("\nDone.")
