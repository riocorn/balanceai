"""
Second, correctly-designed attempt at using the real KB-authored hard-negative
pairs (differential_diagnosis_dataset.json) to improve the symptom-embedding
model -- NOT a hit-and-trial retry, a mathematically diagnosed fix of a proven
root cause.

Root cause of the first attempt's regression (proven, not guessed): that run
passed the 121 hard-negative triplets as a SECOND training objective, trained
jointly with the 2494-pair main objective via SentenceTransformer.fit()'s
legacy multi-objective path. That method's own docstring states: "We sample
only as many batches from each DataLoader as there are in the smallest one...
round robin sampling." With batch_size=64, the main loader had ~39 batches/
epoch but the hard-negative loader had only 2 -- so EVERY epoch was capped to
2 steps per objective. Confirmed directly from that run's own progress bar log
(/tmp/train_v4_hardneg.log): "40/40" total steps for the whole 10-epoch run,
not the ~390 intended. The main dataset was effectively used at ~5% coverage,
which is why accuracy collapsed (31.5%/54.1% -> 15.8%/24.7% top-1/top-5 on the
real held-out eval).

Fix: sequential/staged fine-tuning, not joint multi-objective training. Start
FROM the already-good checkpoint (proven 31.5%/54.1%) and continue training
with ONLY the hard-negative triplets as a single objective (batch_size small
enough that 121 examples still gives several real steps/epoch, not truncated
by anything), a low learning rate (gentle correction, avoid catastrophic
forgetting of the broad structure already learned), and a modest epoch count.
Saved to a NEW path so the good checkpoint is never at risk; only promoted if
the real held-out eval actually shows improvement over 31.5%/54.1%.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))
from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

BASE_CHECKPOINT = str(Path(__file__).parents[1] / "models" / "symptom_embedding_finetuned")
OUT_DIR = str(Path(__file__).parents[1] / "models" / "symptom_embedding_finetuned_hardneg_v2")

random.seed(42)


def build_hard_negative_triplets():
    kb = load_kb()
    diseases = kb["diseases"]
    name_desc_of = {
        did: f"{dz.get('name', did)} ({dz.get('category', '')})".strip()
        for did, dz in diseases.items()
    }
    path = Path(__file__).parent / "differential_diagnosis_dataset.json"
    records = json.load(open(path))
    triplets = []
    for r in records:
        did, cid = r.get("disease_id"), r.get("confusable_id")
        if not did or not cid or did not in name_desc_of or cid not in name_desc_of:
            continue
        anchor = name_desc_of[did]
        positive = r["distinguishing_text"][:300]
        hard_negative = name_desc_of[cid]
        triplets.append(InputExample(texts=[anchor, positive, hard_negative]))
    return triplets


def main():
    triplets = build_hard_negative_triplets()
    print(f"Built {len(triplets)} real KB-authored hard-negative triplets.")
    random.shuffle(triplets)

    BATCH_SIZE = 16  # small on purpose: 121/16 = ~8 real batches/epoch, not 2.
    # First run of this corrected (non-truncated) design used EPOCHS=4, LR=5e-6 --
    # confirmed no regression (31.2%/53.1% vs the good checkpoint's 31.5%/54.1%,
    # within the eval's own noise floor at 292 queries), proving the round-robin
    # truncation was the real cause of the earlier failure, not hard negatives per
    # se. But the correction was too gentle to measure any real movement either way.
    # Since staged fine-tuning from the good checkpoint is now proven safe (unlike
    # the joint-objective approach), a real, reasoned next step -- not blind
    # escalation -- is to use the field's actual default LR (2e-5, no longer being
    # over-conservative) and more epochs, still monitored against the same real eval
    # before promoting anything.
    EPOCHS = 8
    LR = 2e-5

    model = SentenceTransformer(BASE_CHECKPOINT)
    train_dataloader = DataLoader(triplets, shuffle=True, batch_size=BATCH_SIZE)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    steps_per_epoch = len(train_dataloader)
    print(f"Real steps per epoch: {steps_per_epoch} (batch_size={BATCH_SIZE}, "
          f"{len(triplets)} examples) -- x{EPOCHS} epochs = {steps_per_epoch * EPOCHS} total steps.")

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=EPOCHS,
        optimizer_params={"lr": LR},
        warmup_steps=int(0.1 * steps_per_epoch * EPOCHS),
        show_progress_bar=True,
        output_path=OUT_DIR,
    )
    print(f"Saved to {OUT_DIR} (NOT yet promoted -- evaluate before replacing the live checkpoint).")


if __name__ == "__main__":
    main()
