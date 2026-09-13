import shutil, random
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

DERMNET = Path("/home/abhay/Downloads/medical/balanceai/data/dermnet")
TRAIN_ROOT = Path("/home/abhay/Downloads/medical/balanceai/data/training")
TARGET = 400
IMG_SIZE = (224, 224)

def augment_image(img):
    augs = [img.transpose(Image.FLIP_LEFT_RIGHT)]
    augs.append(img.rotate(random.choice([15, 30, -15, -30, 90, 180, 270])))
    augs.append(ImageEnhance.Brightness(img).enhance(random.uniform(0.7, 1.35)))
    augs.append(ImageEnhance.Contrast(img).enhance(random.uniform(0.8, 1.25)))
    augs.append(ImageEnhance.Color(img).enhance(random.uniform(0.75, 1.3)))
    w, h = img.size
    cf = random.uniform(0.82, 0.94)
    cw, ch = int(w*cf), int(h*cf)
    l, t = random.randint(0, w-cw), random.randint(0, h-ch)
    augs.append(img.crop((l, t, l+cw, t+ch)).resize((w, h)))
    augs.append(ImageEnhance.Sharpness(img).enhance(random.uniform(0.5, 2.0)))
    return augs

for model_name, normal_key in [("nail_model","nail_normal"), ("tongue_model","tongue_normal"), ("skin_model","skin_normal")]:
    src = DERMNET / normal_key
    out_dir = TRAIN_ROOT / model_name / normal_key
    out_dir.mkdir(parents=True, exist_ok=True)

    src_imgs = list(src.glob("*.jpg")) + list(src.glob("*.png"))
    print(f"{normal_key}: {len(src_imgs)} source images → augmenting to {TARGET}")

    count = 0
    for p in src_imgs:
        try:
            img = Image.open(p).convert("RGB").resize(IMG_SIZE)
            img.save(str(out_dir / f"orig_{p.stem}.jpg"), quality=92)
            count += 1
        except: pass

    idx = 0
    while count < TARGET:
        src_p = random.choice(src_imgs)
        try:
            img = Image.open(src_p).convert("RGB").resize(IMG_SIZE)
            for aug in augment_image(img):
                if count >= TARGET: break
                aug.resize(IMG_SIZE).save(str(out_dir / f"aug_{idx:05d}.jpg"), quality=88)
                count += 1; idx += 1
        except: pass

    print(f"  Done: {count} images")

    # train/val split
    t_dir = TRAIN_ROOT / f"{model_name}_train" / normal_key
    v_dir = TRAIN_ROOT / f"{model_name}_val" / normal_key
    t_dir.mkdir(parents=True, exist_ok=True)
    v_dir.mkdir(parents=True, exist_ok=True)

    imgs = list(out_dir.glob("*.jpg"))
    random.shuffle(imgs)
    n_val = max(20, int(len(imgs) * 0.2))
    for p in imgs[:n_val]: shutil.copy(str(p), str(v_dir / p.name))
    for p in imgs[n_val:]: shutil.copy(str(p), str(t_dir / p.name))
    print(f"  Split: {len(imgs)-n_val} train, {n_val} val")

print("\nFinal count:")
for model in ["nail_model_train","tongue_model_train","skin_model_train"]:
    d = TRAIN_ROOT / model
    if d.exists():
        for cls in sorted(d.iterdir()):
            n = len(list(cls.glob("*.jpg")))
            print(f"  {model}/{cls.name}: {n}")
