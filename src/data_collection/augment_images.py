import os, random
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import torchvision.transforms.functional as TF
import torch

IMG_ROOT = "/home/abhay/Downloads/medical/balanceai/data/dermnet"
AUG_ROOT = "/home/abhay/Downloads/medical/balanceai/data/dermnet_augmented"
TARGET_PER_CLASS = 300

def augment_one(img):
    ops = []

    ops.append(TF.hflip(img))
    ops.append(TF.vflip(img))

    for angle in [15, 30, 45, -15, -30, -45, 90, 180, 270]:
        ops.append(TF.rotate(img, angle))

    for brightness in [0.7, 0.85, 1.15, 1.3]:
        ops.append(ImageEnhance.Brightness(img).enhance(brightness))

    for contrast in [0.8, 1.2]:
        ops.append(ImageEnhance.Contrast(img).enhance(contrast))

    for saturation in [0.7, 1.3]:
        ops.append(ImageEnhance.Color(img).enhance(saturation))

    ops.append(img.filter(ImageFilter.GaussianBlur(radius=1)))
    ops.append(img.filter(ImageFilter.SHARPEN))

    w, h = img.size
    for crop_factor in [0.85, 0.9]:
        cw, ch = int(w * crop_factor), int(h * crop_factor)
        left = random.randint(0, w - cw)
        top = random.randint(0, h - ch)
        cropped = img.crop((left, top, left + cw, top + ch)).resize((w, h))
        ops.append(cropped)

    ops.append(TF.adjust_gamma(img, gamma=0.7))
    ops.append(TF.adjust_gamma(img, gamma=1.4))

    return ops


def augment_class(src_dir, dst_dir, target_count=TARGET_PER_CLASS):
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    imgs = list(src_dir.glob("*.jpg")) + list(src_dir.glob("*.png"))
    if not imgs:
        return 0

    count = 0
    for src in imgs:
        try:
            img = Image.open(src).convert("RGB").resize((300, 300))
            dst = dst_dir / f"orig_{src.stem}.jpg"
            if not dst.exists():
                img.save(str(dst), quality=90)
                count += 1
        except:
            continue

    aug_idx = 0
    while count < target_count:
        src = random.choice(imgs)
        try:
            img = Image.open(src).convert("RGB").resize((300, 300))
            augmented = augment_one(img)
            for aug_img in augmented:
                if count >= target_count:
                    break
                dst = dst_dir / f"aug_{aug_idx:05d}.jpg"
                if not dst.exists():
                    aug_img.save(str(dst), quality=85)
                    count += 1
                aug_idx += 1
        except:
            continue

    return count


def split_train_val(aug_root, output_root, val_ratio=0.2):
    aug_root = Path(aug_root)
    output_root = Path(output_root)
    (output_root / "train").mkdir(parents=True, exist_ok=True)
    (output_root / "val").mkdir(parents=True, exist_ok=True)

    for class_dir in aug_root.iterdir():
        if not class_dir.is_dir():
            continue
        imgs = list(class_dir.glob("*.jpg"))
        random.shuffle(imgs)
        n_val = max(1, int(len(imgs) * val_ratio))
        val_imgs = imgs[:n_val]
        train_imgs = imgs[n_val:]

        (output_root / "train" / class_dir.name).mkdir(exist_ok=True)
        (output_root / "val" / class_dir.name).mkdir(exist_ok=True)

        for img in train_imgs:
            dst = output_root / "train" / class_dir.name / img.name
            if not dst.exists():
                img.rename(dst)
        for img in val_imgs:
            dst = output_root / "val" / class_dir.name / img.name
            if not dst.exists():
                img.rename(dst)

        print(f"  {class_dir.name}: {len(train_imgs)} train, {len(val_imgs)} val")


if __name__ == "__main__":
    print("=== Data Augmentation Pipeline ===")
    src_root = Path(IMG_ROOT)
    aug_root = Path(AUG_ROOT)

    for class_dir in src_root.iterdir():
        if not class_dir.is_dir():
            continue
        src_imgs = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
        print(f"Augmenting {class_dir.name}: {len(src_imgs)} source → {TARGET_PER_CLASS} target")
        n = augment_class(class_dir, aug_root / class_dir.name)
        print(f"  Done: {n} images")

    print("\n=== Creating train/val split ===")
    split_train_val(
        AUG_ROOT,
        "/home/abhay/Downloads/medical/balanceai/data/dermnet_split"
    )
    print("Done.")
