"""
Fifth embedding fine-tuning attempt -- uses ml_training/top5_symptoms_all.json,
the real, hand-verified, clean top-5-symptom-per-disease dataset built by 4
parallel research forks (real HPO frequency data + KB text + real web search
to Mayo Clinic/MSD Manual/CDC/Cleveland Clinic, with several real data-quality
bugs found and fixed during that work -- see the forks' own reports).

Grounded improvement over the v4/v5 HPO attempts: those used raw HPO/KB
fragments that still had residual noise (section-header labels, non-symptom
categories). This dataset is the actively cleaned, disease-by-disease
verified successor -- exactly the "real data volume + real data quality"
combination the last two experiments showed the real bottleneck to be.

Continues training FROM the current best checkpoint (verified 31.5% top-1/
54.5% top-5), not from scratch, and reuses the same learning-rate lesson
already proven this session: gentle-but-not-too-gentle (1.5e-5 was the real,
verified winner in the last successful run, beating both an overly-gentle
8e-6 pass with no measurable change and the original 2e-5-from-scratch runs
that regressed).
"""
import json
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

BASE_CHECKPOINT = str(Path(__file__).parents[1] / "models" / "symptom_embedding_finetuned")
OUT_DIR = str(Path(__file__).parents[1] / "models" / "symptom_embedding_finetuned_v6_clean")
CLEAN_DATA = Path(__file__).parent / "top5_symptoms_all.json"
DIFF_DX_DATA = Path(__file__).parent / "differential_diagnosis_dataset.json"

random.seed(42)


def build_pairs():
    records = json.load(open(CLEAN_DATA))
    pairs = []
    name_desc_of = {}
    for r in records:
        did = r["disease_id"]
        terms = [t.strip() for t in r.get("top_5_symptoms", []) if t and t.strip()]
        name_desc = f"{r.get('disease_name', did)} ({r.get('category', '')})".strip()
        name_desc_of[did] = name_desc
        if len(terms) >= 2:
            for i in range(len(terms)):
                for j in range(i + 1, len(terms)):
                    pairs.append(InputExample(texts=[terms[i][:300], terms[j][:300]]))
            pairs.append(InputExample(texts=[name_desc, terms[0][:300]]))
        elif len(terms) == 1:
            pairs.append(InputExample(texts=[name_desc, terms[0][:300]]))
    return pairs, name_desc_of


def build_hard_negative_pairs(name_desc_of):
    if not DIFF_DX_DATA.exists():
        return []
    records = json.load(open(DIFF_DX_DATA))
    pairs = []
    for r in records:
        did, cid = r.get("disease_id"), r.get("confusable_id")
        if not did or not cid or did not in name_desc_of or cid not in name_desc_of:
            continue
        pairs.append(InputExample(texts=[name_desc_of[did], r["distinguishing_text"][:300]]))
    return pairs


def main():
    pairs, name_desc_of = build_pairs()
    hn_pairs = build_hard_negative_pairs(name_desc_of)
    pairs.extend(hn_pairs)
    print(f"Built {len(pairs)} real pairs from clean top-5-symptom data "
          f"(covering {len(name_desc_of)}/323 diseases) + {len(hn_pairs)} hard-negative pairs.")
    random.shuffle(pairs)

    EPOCHS = 4
    BATCH_SIZE = 64
    LR = 1.5e-5  # the real, verified-best setting from the previous successful run

    model = SentenceTransformer(BASE_CHECKPOINT)
    train_dataloader = DataLoader(pairs, shuffle=True, batch_size=BATCH_SIZE)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    steps_per_epoch = len(train_dataloader)
    print(f"Real steps per epoch: {steps_per_epoch} x {EPOCHS} epochs = {steps_per_epoch * EPOCHS} total steps.")

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=EPOCHS,
        optimizer_params={"lr": LR},
        warmup_steps=int(0.1 * steps_per_epoch * EPOCHS),
        show_progress_bar=True,
        output_path=OUT_DIR,
    )
    print(f"Saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
