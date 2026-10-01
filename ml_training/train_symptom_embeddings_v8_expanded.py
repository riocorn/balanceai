"""
Continued fine-tuning of the symptom embedding model, from the CURRENT
production checkpoint (v7_combined, real measured 30.5% top-1 / 57.2% top-5
/ 77.1% top-15 on the 292-case held-out eval -- see
ml_training/eval_symptom_embeddings.py + the eval_top15 harness), using the
SAME real same-disease symptom-fragment pairs v7_combined was trained on,
PLUS the expanded ~40k real discriminating training pairs built by
build_expanded_confusable_pairs.py (2042 nearest-neighbor confusable
disease-pairs across all 323 diseases, not just the 121 hand-authored
ones -- see that script's docstring for exactly how those pairs are
derived from real KB/HPO text with no fabrication).

Per this session's own established, proven pattern: CONTINUE from the
already-good v7_combined checkpoint (sequential fine-tuning) -- a
from-scratch GPU run on a similarly-sized combined dataset was already
tried this session and underperformed v7_combined, so this script does
NOT repeat that mistake.

Run on GPU (Colab T4 via the ollama/cloudflared tunnel session) -- CPU
fine-tuning of this scale is not attempted per the GPU-only instruction
for this task.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))
from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

ROOT = Path(__file__).parents[1]
BASE_CHECKPOINT = str(ROOT / "models" / "symptom_embedding_finetuned_v7_combined")
OUT_DIR = str(ROOT / "models" / "symptom_embedding_v8_expanded")
CLEAN_DATA = Path(__file__).parent / "top5_symptoms_all.json"
HPO_DATA = Path(__file__).parent / "real_disease_symptom_data_filtered.jsonl"
DIFF_DX_DATA = Path(__file__).parent / "differential_diagnosis_dataset.json"
EXPANDED_PAIRS = Path(__file__).parent / "expanded_confusable_pairs.json"

MAX_HPO_PER_DISEASE = 40
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
    rng = random.Random(7)
    for did, terms in by_disease.items():
        if len(terms) > MAX_HPO_PER_DISEASE:
            by_disease[did] = rng.sample(terms, MAX_HPO_PER_DISEASE)
    return by_disease


def load_clean_by_disease():
    records = json.load(open(CLEAN_DATA))
    by_disease = {}
    name_desc_of = {}
    for r in records:
        did = r["disease_id"]
        terms = [t.strip() for t in r.get("top_5_symptoms", []) if t and t.strip()]
        by_disease[did] = terms
        name_desc_of[did] = f"{r.get('disease_name', did)} ({r.get('category', '')})".strip()
    return by_disease, name_desc_of


def build_same_disease_pairs():
    """Identical to train_symptom_embeddings_v7_combined.py's build_pairs()
    -- same real same-disease symptom-fragment pairs that produced
    v7_combined, so this run does not lose that signal."""
    kb = load_kb()
    diseases = kb["diseases"]
    hpo_by_disease = load_hpo_by_disease()
    clean_by_disease, clean_name_desc = load_clean_by_disease()
    pairs = []
    name_desc_of = {}

    for did, dz in diseases.items():
        kb_terms = _core_symptom_text(dz)
        hpo_terms = hpo_by_disease.get(did, [])
        clean_terms = clean_by_disease.get(did, [])
        all_terms = list({t.strip() for t in (kb_terms + hpo_terms + clean_terms) if t and t.strip()})
        name_desc = clean_name_desc.get(did) or f"{dz.get('name', did)} ({dz.get('category', '')})".strip()
        name_desc_of[did] = name_desc

        if len(all_terms) >= 2:
            rng = random.Random(hash(did) % (2**31))
            possible = [(i, j) for i in range(len(all_terms)) for j in range(i + 1, len(all_terms))]
            rng.shuffle(possible)
            for i, j in possible[:60]:
                pairs.append(InputExample(texts=[all_terms[i][:300], all_terms[j][:300]]))
            pairs.append(InputExample(texts=[name_desc, all_terms[0][:300]]))
        elif len(all_terms) == 1:
            pairs.append(InputExample(texts=[name_desc, all_terms[0][:300]]))
    return pairs, name_desc_of


def build_kb_hard_negative_pairs(name_desc_of):
    """Same as v7_combined: the 121 hand-authored KB distinguishing_text
    pairs, unchanged."""
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


def build_expanded_nn_pairs(name_desc_of):
    """The new ~40k real training pairs from build_expanded_confusable_pairs.py
    -- for every nearest-neighbor confusable disease-pair (a, b), each real
    KB/HPO term specific to a (not shared with b, and vice versa) is paired
    with a's own name/description as anchor -- same anchor-positive shape as
    the proven KB hard-negative pairs above, generalized to 2042 real
    nearest-neighbor pairs instead of just the 121 hand-authored ones."""
    if not EXPANDED_PAIRS.exists():
        return []
    records = json.load(open(EXPANDED_PAIRS))
    pairs = []
    for r in records:
        a, b = r["disease_a"], r["disease_b"]
        a_desc = name_desc_of.get(a)
        b_desc = name_desc_of.get(b)
        if a_desc:
            for t in r.get("a_unique_terms", []):
                pairs.append(InputExample(texts=[a_desc, t[:300]]))
        if b_desc:
            for t in r.get("b_unique_terms", []):
                pairs.append(InputExample(texts=[b_desc, t[:300]]))
    return pairs


def main():
    same_disease_pairs, name_desc_of = build_same_disease_pairs()
    kb_hn_pairs = build_kb_hard_negative_pairs(name_desc_of)
    expanded_pairs = build_expanded_nn_pairs(name_desc_of)

    all_pairs = same_disease_pairs + kb_hn_pairs + expanded_pairs
    print(f"same-disease pairs: {len(same_disease_pairs)}")
    print(f"KB hand-authored hard-negative pairs: {len(kb_hn_pairs)}")
    print(f"expanded nearest-neighbor discriminating pairs: {len(expanded_pairs)}")
    print(f"TOTAL training pairs: {len(all_pairs)}")
    random.shuffle(all_pairs)

    EPOCHS = 2  # fewer than v7_combined's 4 -- dataset is ~3x larger and we are
    # continuing an already-good checkpoint, not starting fresh; avoids
    # over-steering/catastrophic forgetting of v7_combined's real gains.
    BATCH_SIZE = 64
    LR = 1.5e-5  # same proven LR as v7_combined

    model = SentenceTransformer(BASE_CHECKPOINT)
    train_dataloader = DataLoader(all_pairs, shuffle=True, batch_size=BATCH_SIZE)
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
