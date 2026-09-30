"""
Fine-tunes the sentence-embedding model used by the symptom-checker's
retrieval step (settings.EMBEDDING_MODEL, loaded in
src/api/services/pharmacy_service.py::_embedding_model / _disease_embeddings)
so that different real symptom descriptions of the SAME disease embed close
together, and different diseases embed apart -- directly targeting the
embedding shortlist step that feeds the LLM reranker.

Real, KB-derived training data only (no synthetic/fake text): for every
disease in disease_master.json, uses _core_symptom_text() (the same
extraction the production retrieval path uses, after the field-name-coverage
fix applied earlier this session -- 0/323 diseases now return empty) to pull
real symptom-description fragments, and forms positive pairs from different
real fragments describing the same disease. Diseases with only one real
fragment are paired with their own (name, category) string instead, since a
name/category description and a symptom description of the same disease
should also embed close together.

Loss: MultipleNegativesRankingLoss (standard sentence-transformers choice for
this exact "pull same-entity texts together, push other in-batch entities
apart" objective) -- other diseases in the same batch serve as in-batch
negatives, no explicit negative mining needed.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

BASE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OUT_DIR = str(Path(__file__).parents[1] / "models" / "symptom_embedding_finetuned")

random.seed(42)


def build_pairs():
    kb = load_kb()
    diseases = kb["diseases"]
    pairs = []
    for did, dz in diseases.items():
        terms = _core_symptom_text(dz)
        name_desc = f"{dz.get('name', did)} ({dz.get('category', '')})".strip()
        if len(terms) >= 2:
            # Positive pairs from different real symptom fragments of the same disease.
            for i in range(len(terms)):
                for j in range(i + 1, len(terms)):
                    pairs.append(InputExample(texts=[terms[i][:300], terms[j][:300]]))
            # Also anchor each fragment to the disease's own name/category once.
            pairs.append(InputExample(texts=[name_desc, terms[0][:300]]))
        elif len(terms) == 1:
            pairs.append(InputExample(texts=[name_desc, terms[0][:300]]))
    return pairs


def main():
    pairs = build_pairs()
    print(f"Built {len(pairs)} real KB-derived training pairs from {323} diseases.")
    random.shuffle(pairs)

    model = SentenceTransformer(BASE_MODEL)
    train_dataloader = DataLoader(pairs, shuffle=True, batch_size=32)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=4,
        warmup_steps=int(0.1 * len(train_dataloader) * 4),
        show_progress_bar=True,
        output_path=OUT_DIR,
    )
    print(f"Saved fine-tuned model to {OUT_DIR}")


if __name__ == "__main__":
    main()
