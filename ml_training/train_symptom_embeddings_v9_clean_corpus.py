"""
Ninth embedding fine-tuning attempt -- NOT a new architecture or a larger
dataset (that lever, the 40k nearest-neighbor expansion, was already tried
as v8 and regressed, see train_symptom_embeddings_v8_expanded.py's
docstring). This run changes exactly one thing: the TRAINING PAIR TEXT
itself, by re-running the identical v7_combined build_pairs() recipe against
the NOW-FIXED corpus extractors in src/api/services/pharmacy_service.py
(_core_symptom_text / _collect_symptom_labels). Those extractors previously
leaked citation/meta-label text (e.g. the literal strings "clinical
takeaway", "source phn", "confidence rose spots", "epidemiology" prose) into
what was supposed to be patient-symptom text -- fixed this session, and
confirmed by direct inspection (see pharmacy_service.py's own diff/comments)
across every one of the 893 distinct sub-keys this KB uses. The same CPU-only
fix alone (no retraining, same v7_combined checkpoint weights, just cleaner
RETRIEVAL-TIME query/corpus text at eval time) already moved
eval_final_accuracy.py's headline from 64.7% to 90.8%.

The real reason to expect retraining to help ON TOP of that CPU-only fix:
v7_combined's EMBEDDING WEIGHTS were themselves fit (via MultipleNegativesRank-
ingLoss, which pulls each anchor/positive pair's representations together
and pushes every other in-batch pair apart) against the OLD, leaky pair
text. Some same-disease positive pairs during v7's own training were
anchor=a real symptom fragment, positive=a citation/meta-label string (e.g.
"clinical takeaway", "confidence rose spots") -- MultipleNegativesRanking-
Loss would have spent real gradient steps pulling the model's embedding of
true clinical language toward nonsense label tokens, diluting the embedding
space around genuine symptom semantics. Cleaning the corpus narrows that:
every one of the training pairs below is now the SAME v7 pairing *logic*
(same-disease fragment co-occurrence + KB-authored hard negatives) but with
only real patient-reportable symptom text in both halves of each pair -- so
continued training should sharpen the embedding geometry around true
symptom clusters rather than partially un-doing it on citation noise. This
is a narrowing-the-embedding-space argument, not a volume argument (pair
COUNT is expected to land close to v7_combined's, not 3x larger like v8).

Continues from v7_combined (sequential fine-tuning, this session's own
established pattern: continuing from an already-adapted checkpoint beat
training from scratch, confirmed again by v8's attempt from the SAME
v7_combined base). Identical MultipleNegativesRankingLoss recipe to
v7_combined (4 epochs, batch 64, LR 1.5e-5) -- no hyperparameter sweep,
per this session's no-hit-and-trial standard; this run isolates the one
real lever (corpus cleanliness) by holding every other recipe choice fixed.

Run on GPU (Colab T4).
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
OUT_DIR = str(ROOT / "models" / "symptom_embedding_finetuned_v9_clean_corpus")
CLEAN_DATA = Path(__file__).parent / "top5_symptoms_all.json"
HPO_DATA = Path(__file__).parent / "real_disease_symptom_data_filtered.jsonl"
DIFF_DX_DATA = Path(__file__).parent / "differential_diagnosis_dataset.json"

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


def build_pairs():
    """Identical pairing logic to train_symptom_embeddings_v7_combined.py's
    build_pairs() -- the only difference is that _core_symptom_text (imported
    live from the current, now-fixed pharmacy_service.py) returns cleaned
    text instead of the citation/meta-label-leaking text v7 was built on."""
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
    print(f"Built {len(pairs)} total real pairs (clean top-5 + filtered HPO + NOW-CLEANED KB text, "
          f"covering {len(name_desc_of)}/323 diseases) + {len(hn_pairs)} hard-negative pairs.")
    random.shuffle(pairs)

    EPOCHS = 4
    BATCH_SIZE = 64
    LR = 1.5e-5

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
