import requests, os, time, shutil, json
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import random, numpy as np

DERMNET = Path("/home/abhay/Downloads/medical/balanceai/data/dermnet")
TRAIN_ROOT = Path("/home/abhay/Downloads/medical/balanceai/data/training")

# nail model: 3 classes
NAIL_CLASSES = {
    "nail_normal": [],
    "nail_iron_deficiency": ["nail_dystrophy"],       # koilonychia proxy
    "nail_zinc_deficiency": ["nail_melanonychia"],    # pigment/spot proxy
}

# tongue model: 3 classes
TONGUE_CLASSES = {
    "tongue_normal": [],
    "tongue_b12_iron": ["tongue_glossitis", "mouth_angular_cheilitis"],
    "tongue_folate_b12": ["tongue_geographic"],
}

# skin model: 3 classes
SKIN_CLASSES = {
    "skin_normal": [],
    "skin_vitA_deficiency": ["skin_follicular_hyperkeratosis"],
    "skin_iron_pallor": ["skin_pallor", "skin_dry_xerosis"],
}

TARGET = 400
IMG_SIZE = (224, 224)


def fetch_normal_isic(label, n=120):
    out_dir = DERMNET / label
    out_dir.mkdir(exist_ok=True)
    existing = len(list(out_dir.glob("*.jpg")))
    if existing >= n:
        print(f"  SKIP {label}: {existing} already")
        return

    query = "melanocytic nevi" if "nail" in label else "seborrheic keratosis" if "tongue" in label else "normal skin"
    url = f"https://api.isic-archive.com/api/v2/images/?limit=100&query={query}"
    try:
        r = requests.get(url, timeout=15)
        items = r.json().get("results", [])
        count = 0
        for item in items:
            if count >= n: break
            img_url = (item.get("files", {}).get("thumbnail_256", {}) or {}).get("url")
            if not img_url: continue
            fname = out_dir / f"normal_{item.get('isic_id', count)}.jpg"
            if fname.exists(): count += 1; continue
            try:
                resp = requests.get(img_url, timeout=10)
                if resp.status_code == 200 and len(resp.content) > 3000:
                    with open(fname, "wb") as f: f.write(resp.content)
                    count += 1
                    time.sleep(0.25)
            except: pass
        print(f"  Fetched {count} normal images for {label}")
    except Exception as e:
        print(f"  ISIC error: {e}")


def augment_image(img):
    augs = []
    augs.append(img.transpose(Image.FLIP_LEFT_RIGHT))
    augs.append(img.rotate(random.choice([15, 30, -15, -30, 90, 180, 270])))
    augs.append(ImageEnhance.Brightness(img).enhance(random.uniform(0.7, 1.35)))
    augs.append(ImageEnhance.Contrast(img).enhance(random.uniform(0.8, 1.25)))
    augs.append(ImageEnhance.Color(img).enhance(random.uniform(0.75, 1.3)))
    augs.append(img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.2))))
    w, h = img.size
    cf = random.uniform(0.82, 0.94)
    cw, ch = int(w*cf), int(h*cf)
    l, t = random.randint(0, w-cw), random.randint(0, h-ch)
    augs.append(img.crop((l, t, l+cw, t+ch)).resize((w, h)))
    augs.append(ImageEnhance.Sharpness(img).enhance(random.uniform(0.5, 2.0)))
    augs.append(ImageOps.autocontrast(img))
    # slight hue shift via HSV
    arr = np.array(img).astype(np.float32)
    arr[:,:,0] = np.clip(arr[:,:,0] + random.uniform(-15, 15), 0, 255)
    augs.append(Image.fromarray(arr.astype(np.uint8)))
    return augs


def build_split(model_name, class_map):
    print(f"\n=== Building {model_name} training data ===")
    for cls_label, src_folders in class_map.items():
        out_dir = TRAIN_ROOT / model_name / cls_label
        out_dir.mkdir(parents=True, exist_ok=True)
        existing = len(list(out_dir.glob("*.jpg")))
        if existing >= TARGET:
            print(f"  SKIP {cls_label}: {existing} images already")
            continue

        # Gather source images
        src_imgs = []
        for folder in src_folders:
            src = DERMNET / folder
            if src.exists():
                src_imgs += list(src.glob("*.jpg")) + list(src.glob("*.png"))

        if not src_imgs:
            print(f"  WARNING: No source images for {cls_label}")
            continue

        print(f"  {cls_label}: {len(src_imgs)} source images → augmenting to {TARGET}")

        # Copy originals first
        count = 0
        for p in src_imgs:
            try:
                img = Image.open(p).convert("RGB").resize(IMG_SIZE)
                img.save(str(out_dir / f"orig_{p.stem}.jpg"), quality=92)
                count += 1
            except: pass

        # Augment to target
        idx = 0
        while count < TARGET:
            src = random.choice(src_imgs)
            try:
                img = Image.open(src).convert("RGB").resize(IMG_SIZE)
                for aug in augment_image(img):
                    if count >= TARGET: break
                    aug.resize(IMG_SIZE).save(str(out_dir / f"aug_{idx:05d}.jpg"), quality=88)
                    count += 1
                    idx += 1
            except: pass

        print(f"  Done: {count} images in {out_dir}")

    # Train/val split 80/20
    val_dir = TRAIN_ROOT / (model_name + "_val")
    train_dir = TRAIN_ROOT / (model_name + "_train")
    for cls_label in class_map:
        src = TRAIN_ROOT / model_name / cls_label
        t_dir = train_dir / cls_label
        v_dir = val_dir / cls_label
        t_dir.mkdir(parents=True, exist_ok=True)
        v_dir.mkdir(parents=True, exist_ok=True)
        imgs = list(src.glob("*.jpg"))
        if not imgs: continue
        random.shuffle(imgs)
        n_val = max(20, int(len(imgs) * 0.2))
        for p in imgs[:n_val]:
            shutil.copy(str(p), str(v_dir / p.name))
        for p in imgs[n_val:]:
            shutil.copy(str(p), str(t_dir / p.name))
        print(f"  Split {cls_label}: {len(imgs)-n_val} train, {n_val} val")


if __name__ == "__main__":
    print("Step 1: Fetching normal images from ISIC...")
    fetch_normal_isic("nail_normal", n=120)
    fetch_normal_isic("tongue_normal", n=120)
    fetch_normal_isic("skin_normal", n=120)

    print("\nStep 2: Building training splits with augmentation...")
    build_split("nail_model", NAIL_CLASSES)
    build_split("tongue_model", TONGUE_CLASSES)
    build_split("skin_model", SKIN_CLASSES)

    print("\nFinal dataset summary:")
    for model in ["nail_model_train", "tongue_model_train", "skin_model_train"]:
        d = TRAIN_ROOT / model
        if d.exists():
            for cls in d.iterdir():
                n = len(list(cls.glob("*.jpg")))
                print(f"  {model}/{cls.name}: {n}")
