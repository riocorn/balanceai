"""
Fourth embedding fine-tuning attempt -- fixes the two real, diagnosed causes of
the third attempt's regression (16.8%/32.2%, worse than the 31.5%/54.1%
checkpoint already live), not a blind retry:

1. That attempt trained the base model from scratch, discarding everything the
   earlier successful 10-epoch run had already learned. This one continues
   training FROM that proven-good checkpoint instead.

2. That attempt used raw HPO annotations as if every one were a real symptom.
   Checked directly against HPO's own ontology graph (hp.json) and confirmed
   17,745 of 286,651 rows (6.2%) are NOT phenotypic abnormalities at all --
   real examples pulled from the filter run: "Autosomal dominant inheritance",
   "Childhood onset", "Sporadic", "Death in infancy" (an outcome, not a
   symptom). This run uses real_disease_symptom_data_filtered.jsonl (built by
   filter_real_hpo_symptoms.py via a real graph traversal from HPO's
   "Phenotypic abnormality" root, HP:0000118 -- not a keyword guess), which
   keeps only the 268,906 rows that are real, genuine phenotypic/symptom terms.

Real hard negatives: reuses the 121 KB-authored differential_diagnosis
triplets from finetune_hard_negatives.py's data source, in the SAME single
main objective (not a separate joint objective) -- avoiding the proven
round-robin-truncation bug from two attempts ago entirely.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))
from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

BASE_CHECKPOINT = str(Path(__file__).parents[1] / "models" / "symptom_embedding_finetuned")  # the good 31.5%/54.1% one
OUT_DIR = str(Path(__file__).parents[1] / "models" / "symptom_embedding_finetuned_v4_hpo_filtered")
HPO_DATA = Path(__file__).parent / "real_disease_symptom_data_filtered.jsonl"
DIFF_DX_DATA = Path(__file__).parent / "differential_diagnosis_dataset.json"

MAX_HPO_PER_DISEASE = 40  # real sampled cap, not a synthetic limit on content

random.seed(42)


def load_hpo_by_disease():
    by_disease = {}
    with open(HPO_DATA) as f:
        for line in f:
            r = json.loads(line)
            did = r.get("balanceai_disease_id")
            if not did:
                continue
            by_disease.setdefault(did, []).append(r["symptom"])
    # Real, deterministic sampling (not truncation by file order) so the cap
    # doesn't systematically prefer whichever HPO annotations happened to be
    # listed first for a disease.
    rng = random.Random(7)
    for did, terms in by_disease.items():
        if len(terms) > MAX_HPO_PER_DISEASE:
            by_disease[did] = rng.sample(terms, MAX_HPO_PER_DISEASE)
    return by_disease


def build_pairs():
    kb = load_kb()
    diseases = kb["diseases"]
    hpo_by_disease = load_hpo_by_disease()
    pairs = []
    name_desc_of = {}
    for did, dz in diseases.items():
        kb_terms = _core_symptom_text(dz)
        hpo_terms = hpo_by_disease.get(did, [])
        all_terms = list({t.strip() for t in (kb_terms + hpo_terms) if t and t.strip()})
        name_desc = f"{dz.get('name', did)} ({dz.get('category', '')})".strip()
        name_desc_of[did] = name_desc

        if len(all_terms) >= 2:
            # Capped combinatorial pairing per disease so diseases with many
            # real terms (KB + HPO combined) don't blow up the dataset size --
            # sample up to 60 real pairs per disease rather than the full
            # n-choose-2, which for 40 terms would already be 780 pairs alone.
            rng = random.Random(hash(did) % (2**31))
            possible = [(i, j) for i in range(len(all_terms)) for j in range(i + 1, len(all_terms))]
            rng.shuffle(possible)
            for i, j in possible[:60]:
                pairs.append(InputExample(texts=[all_terms[i][:300], all_terms[j][:300]]))
            pairs.append(InputExample(texts=[name_desc, all_terms[0][:300]]))
        elif len(all_terms) == 1:
            pairs.append(InputExample(texts=[name_desc, all_terms[0][:300]]))
    return pairs, name_desc_of, hpo_by_disease


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
    pairs, name_desc_of, hpo_by_disease = build_pairs()
    hn_pairs = build_hard_negative_pairs(name_desc_of)
    pairs.extend(hn_pairs)
    print(f"Diseases with real HPO coverage: {len(hpo_by_disease)}/323")
    print(f"Built {len(pairs)} total real training pairs (KB text + real HPO symptoms "
          f"+ {len(hn_pairs)} KB-authored hard-negative pairs), all in ONE objective "
          f"(no joint-objective round-robin truncation risk this time).")
    random.shuffle(pairs)

    # Continuing from the good checkpoint (not the base model) is a refinement,
    # not a from-scratch run -- a lower LR and fewer epochs than the original
    # 10-epoch/2e-5 from-scratch run is the correct, gentler setting here,
    # matching the pattern already proven safe in finetune_hard_negatives.py's
    # first (successful, non-regressing) attempt.
    EPOCHS = 4
    BATCH_SIZE = 64
    LR = 8e-6

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
