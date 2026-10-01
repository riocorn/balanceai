"""
Expand the discriminating-pair training data from the 121 hand-authored
KB confusable pairs (differential_diagnosis_dataset.json) to a much larger
set covering all 323 diseases, WITHOUT fabricating anything.

Method (real, grounded, non-exhaustive):
1. For every disease, build its real aggregated symptom-term pool the SAME
   way train_symptom_embeddings_v7_combined.py does (KB core-symptom text +
   filtered HPO terms + hand-verified top5 clean terms).
2. Encode each disease's pool with the CURRENT production embedding model
   (models/symptom_embedding_finetuned_v7_combined) to get one real
   disease-level vector, then find each disease's top-K nearest OTHER
   diseases by cosine similarity -- this is "confusable enough to matter"
   by construction (not a random/exhaustive 323x322 pairing), and it is
   computed from the model's own real learned signal, not guessed.
3. For every such (disease_a, disease_b) neighbor pair, compute the REAL
   KB terms that are specific to disease_a and NOT present (after normalized
   token overlap) in disease_b's term pool, and vice versa. These real,
   KB-sourced "unique" terms become InputExample(anchor=name_desc, positive=
   unique_term) training pairs -- the same mechanism already proven in
   build_hard_negative_pairs() in train_symptom_embeddings_v7_combined.py
   (anchor = disease description, positive = text that is specifically
   true of/distinguishing for that disease), just generalized from the 121
   hand-authored pairs to every real nearest-neighbor pair found by the
   model/KB overlap, with NO LLM call and NO invented text anywhere.
4. The 121 KB-authored hard-negative pairs (with their hand-written
   distinguishing_text) are always included on top of this, unchanged.

Output: ml_training/expanded_confusable_pairs.json -- a list of
{disease_a, disease_b, source, a_unique_terms, b_unique_terms} records
(for inspection/audit), and ml_training/expanded_training_pairs_meta.json
with counts. The actual InputExample pairs are rebuilt at train time by
train_symptom_embeddings_v8_expanded.py from this same real term data
(kept here as plain text so it's auditable, not a pickle).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))
from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402

from sentence_transformers import SentenceTransformer
import numpy as np

ROOT = Path(__file__).parents[1]
MODEL_PATH = str(ROOT / "models" / "symptom_embedding_finetuned_v7_combined")
CLEAN_DATA = Path(__file__).parent / "top5_symptoms_all.json"
HPO_DATA = Path(__file__).parent / "real_disease_symptom_data_filtered.jsonl"
DIFF_DX_DATA = Path(__file__).parent / "differential_diagnosis_dataset.json"
OUT_PAIRS = Path(__file__).parent / "expanded_confusable_pairs.json"
OUT_META = Path(__file__).parent / "expanded_training_pairs_meta.json"

MAX_HPO_PER_DISEASE = 40
TOP_K_NEIGHBORS = 9          # per disease -- "nearest real neighbors", not exhaustive
MAX_UNIQUE_TERMS_PER_SIDE = 12  # cap terms contributed per disease-pair side

STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "with", "and", "or", "to", "from",
    "is", "are", "be", "mild", "severe", "occasional", "mainly", "often",
    "usually", "may", "typically",
}


def norm_tokens(text):
    toks = re.findall(r"[a-z]+", text.lower())
    return {t for t in toks if t not in STOPWORDS and len(t) > 2}


def load_hpo_by_disease():
    by_disease = {}
    with open(HPO_DATA) as f:
        for line in f:
            r = json.loads(line)
            did = r.get("balanceai_disease_id")
            if not did:
                continue
            by_disease.setdefault(did, []).append(r["symptom"])
    import random
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


def build_term_pools():
    kb = load_kb()
    diseases = kb["diseases"]
    hpo_by_disease = load_hpo_by_disease()
    clean_by_disease, clean_name_desc = load_clean_by_disease()
    pools = {}
    name_desc_of = {}
    for did, dz in diseases.items():
        kb_terms = _core_symptom_text(dz)
        hpo_terms = hpo_by_disease.get(did, [])
        clean_terms = clean_by_disease.get(did, [])
        all_terms = list({t.strip() for t in (kb_terms + hpo_terms + clean_terms) if t and t.strip()})
        pools[did] = all_terms
        name_desc_of[did] = clean_name_desc.get(did) or f"{dz.get('name', did)} ({dz.get('category', '')})".strip()
    return pools, name_desc_of


def existing_kb_pairs():
    if not DIFF_DX_DATA.exists():
        return set()
    records = json.load(open(DIFF_DX_DATA))
    out = set()
    for r in records:
        did, cid = r.get("disease_id"), r.get("confusable_id")
        if did and cid:
            out.add(tuple(sorted([did, cid])))
    return out


def main():
    pools, name_desc_of = build_term_pools()
    dids = sorted(pools.keys())
    print(f"Diseases: {len(dids)}")

    model = SentenceTransformer(MODEL_PATH)
    disease_texts = [name_desc_of[d] + " " + " ".join(pools[d][:30]) for d in dids]
    embs = model.encode(disease_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
    sims = embs @ embs.T
    np.fill_diagonal(sims, -1.0)

    already_kb = existing_kb_pairs()
    found_pairs = {}  # (a,b) sorted -> sim
    for i, did in enumerate(dids):
        order = np.argsort(-sims[i])[:TOP_K_NEIGHBORS]
        for j in order:
            other = dids[j]
            key = tuple(sorted([did, other]))
            if key not in found_pairs or sims[i][j] > found_pairs[key]:
                found_pairs[key] = float(sims[i][j])

    print(f"Nearest-neighbor confusable disease-pairs found (top-{TOP_K_NEIGHBORS}/disease): {len(found_pairs)}")
    print(f"  of which already in the 121 KB-authored set: {sum(1 for k in found_pairs if k in already_kb)}")

    token_pools = {d: {t: norm_tokens(t) for t in pools[d]} for d in dids}

    out_records = []
    total_training_pairs = 0
    for (a, b), sim in found_pairs.items():
        a_terms = pools.get(a, [])
        b_terms = pools.get(b, [])
        b_all_tokens = set()
        for toks in token_pools.get(b, {}).values():
            b_all_tokens |= toks
        a_all_tokens = set()
        for toks in token_pools.get(a, {}).values():
            a_all_tokens |= toks

        a_unique = []
        for t in a_terms:
            toks = token_pools[a][t]
            if toks and not (toks <= b_all_tokens):
                a_unique.append(t)
        b_unique = []
        for t in b_terms:
            toks = token_pools[b][t]
            if toks and not (toks <= a_all_tokens):
                b_unique.append(t)

        a_unique = a_unique[:MAX_UNIQUE_TERMS_PER_SIDE]
        b_unique = b_unique[:MAX_UNIQUE_TERMS_PER_SIDE]
        if not a_unique and not b_unique:
            continue

        out_records.append({
            "disease_a": a,
            "disease_b": b,
            "embedding_similarity": round(sim, 4),
            "source": "kb_authored" if (a, b) in already_kb else "symptom_overlap_nearest_neighbor",
            "a_unique_terms": a_unique,
            "b_unique_terms": b_unique,
        })
        total_training_pairs += len(a_unique) + len(b_unique)

    OUT_PAIRS.write_text(json.dumps(out_records, indent=2))
    meta = {
        "n_diseases": len(dids),
        "top_k_neighbors_per_disease": TOP_K_NEIGHBORS,
        "n_confusable_disease_pairs": len(out_records),
        "n_kb_authored_overlap": sum(1 for r in out_records if r["source"] == "kb_authored"),
        "n_nearest_neighbor_new": sum(1 for r in out_records if r["source"] == "symptom_overlap_nearest_neighbor"),
        "n_real_training_pairs_from_this_set": total_training_pairs,
    }
    OUT_META.write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
