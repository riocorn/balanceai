"""
Real, quantified retrieval-accuracy evaluation for the symptom-checker's
embedding model -- not a guess, a held-out top-1/top-5 accuracy number.

Methodology: for each disease with >=2 real symptom fragments (from
_core_symptom_text), hold out ONE fragment as a "query" and use every
OTHER fragment across the whole 323-disease KB as the "document" corpus
(so the model has never seen the held-out fragment matched to anything
during this eval). Encode query and corpus, rank corpus by cosine
similarity, check whether the top-1 / top-5 nearest documents belong to
the CORRECT disease_id. This is genuine retrieval accuracy on held-out
text, not training-set accuracy.

Usage: python3 eval_symptom_embeddings.py <model_name_or_path> [<model2> ...]
Reports top-1 and top-5 accuracy for each model given, so a before/after
comparison is a real side-by-side number.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402
from sentence_transformers import SentenceTransformer
import numpy as np

random.seed(7)


def build_eval_set():
    kb = load_kb()
    diseases = kb["diseases"]
    queries = []       # (disease_id, held_out_text)
    corpus_texts = []  # doc text
    corpus_dids = []   # doc's disease_id
    for did, dz in diseases.items():
        terms = _core_symptom_text(dz)
        name_desc = f"{dz.get('name', did)} ({dz.get('category', '')})".strip()
        if len(terms) >= 2:
            held_out = terms[-1][:300]
            remaining = terms[:-1]
            queries.append((did, held_out))
            for t in remaining:
                corpus_texts.append(t[:300])
                corpus_dids.append(did)
            corpus_texts.append(name_desc)
            corpus_dids.append(did)
        elif len(terms) == 1:
            # No fragment to hold out without losing the disease from the
            # corpus entirely -- use name/category as the sole document
            # instead, and skip as a query (can't evaluate what was never
            # held out).
            corpus_texts.append(name_desc)
            corpus_dids.append(did)
    return queries, corpus_texts, corpus_dids


def evaluate(model_path, queries, corpus_texts, corpus_dids):
    model = SentenceTransformer(model_path)
    corpus_emb = model.encode(corpus_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    query_texts = [q[1] for q in queries]
    query_dids = [q[0] for q in queries]
    query_emb = model.encode(query_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)

    sims = query_emb @ corpus_emb.T  # (n_queries, n_docs)
    top1_correct = 0
    top5_correct = 0
    for i, did in enumerate(query_dids):
        order = np.argsort(-sims[i])
        top5_dids = [corpus_dids[j] for j in order[:5]]
        if top5_dids[0] == did:
            top1_correct += 1
        if did in top5_dids:
            top5_correct += 1
    n = len(queries)
    return top1_correct / n, top5_correct / n, n


def main():
    models = sys.argv[1:]
    if not models:
        models = ["sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"]
    queries, corpus_texts, corpus_dids = build_eval_set()
    print(f"Eval set: {len(queries)} held-out queries, {len(corpus_texts)} corpus documents.\n")
    for m in models:
        top1, top5, n = evaluate(m, queries, corpus_texts, corpus_dids)
        print(f"{m}\n  top-1 accuracy: {top1:.3f} ({int(top1*n)}/{n})\n  top-5 accuracy: {top5:.3f} ({int(top5*n)}/{n})\n")


if __name__ == "__main__":
    main()
