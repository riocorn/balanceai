import requests, os, json, time
from pathlib import Path

IMG_ROOT = "/home/abhay/Downloads/medical/balanceai/data/dermnet"
os.makedirs(IMG_ROOT, exist_ok=True)

DERMNET_BASE = "https://dermnetnz.org"
KNOWN_IMAGES = [
    ("nail_koilonychia", [
        "/assets/Uploads/koilonychia-028.jpg",
        "/assets/Uploads/site-age-specific/perleche7.jpg",
    ]),
    ("nail_iron_deficiency", [
        "/assets/Uploads/koilonychia-028.jpg",
        "/assets/Uploads/systemic/iron-stain1.jpg",
    ]),
]

def download_image(url, dest_path, headers=None):
    try:
        h = headers or {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        r = requests.get(url, headers=h, timeout=15, stream=True)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(dest_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"  Error: {e}")
    return False

def collect_isic_images(query, label, n=100):
    out_dir = Path(IMG_ROOT) / label
    out_dir.mkdir(exist_ok=True)
    existing = len(list(out_dir.glob("*.jpg")))
    if existing >= n:
        print(f"  SKIP {label}: {existing} images already")
        return existing

    url = f"https://api.isic-archive.com/api/v2/images/?limit=50&query={query}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            print(f"  ISIC API error: {r.status_code}")
            return 0
        data = r.json()
        results = data.get("results", [])
        count = 0
        for item in results:
            img_url = item.get("files", {}).get("full", {}).get("url") or \
                      item.get("files", {}).get("thumbnail_256", {}).get("url")
            if not img_url:
                continue
            fname = out_dir / f"{label}_{item.get('isic_id', count)}.jpg"
            if fname.exists():
                count += 1
                continue
            if download_image(img_url, str(fname)):
                count += 1
                time.sleep(0.3)
        print(f"  ISIC {label}: {count}/{len(results)} downloaded")
        return count
    except Exception as e:
        print(f"  ISIC error for {label}: {e}")
        return 0

ISIC_QUERIES = [
    ("melanonychia", "nail_melanonychia"),
    ("nail dystrophy", "nail_dystrophy"),
    ("glossitis", "tongue_glossitis"),
    ("geographic tongue", "tongue_geographic"),
    ("angular cheilitis", "mouth_angular_cheilitis"),
    ("pallor", "skin_pallor"),
    ("follicular hyperkeratosis", "skin_follicular_hyperkeratosis"),
    ("xerosis", "skin_dry_xerosis"),
]

print("=== Collecting ISIC images ===")
totals = {}
for query, label in ISIC_QUERIES:
    out_dir = Path(IMG_ROOT) / label
    out_dir.mkdir(exist_ok=True)
    url = f"https://api.isic-archive.com/api/v2/images/?limit=100&query={query}"
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        print(f"  ERROR {label}: {r.status_code}")
        continue
    data = r.json()
    results = data.get("results", [])
    count = 0
    for item in results[:50]:
        img_url = (item.get("files", {}).get("thumbnail_256", {}) or {}).get("url") or \
                  (item.get("files", {}).get("full", {}) or {}).get("url")
        if not img_url:
            continue
        fname = out_dir / f"{label}_{item.get('isic_id', count)}.jpg"
        if fname.exists():
            count += 1
            continue
        if download_image(img_url, str(fname)):
            count += 1
            time.sleep(0.2)
    print(f"  {label}: {count} images")
    totals[label] = count

print("\n=== Summary ===")
for k, v in totals.items():
    print(f"  {k}: {v} images")
print("Done.")
