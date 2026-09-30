"""
Real before/after evaluation of the cross-encoder + Bayes reranking layer
(src/api/services/retrieval_rerank.py), on the SAME 292-case held-out query
set used throughout this session (same methodology as eval_symptom_embeddings.py
/ the eval_top15 harness: one real symptom fragment per disease is held out as
the query and excluded from that disease's own corpus text, so the model/
scorer never sees the held-out fragment matched to its disease during the
eval -- this is what makes it a real generalization test rather than a
memorization/lookup test).

IMPORTANT, found and fixed during this eval's own development: a first
version of this script built the disease-level "document" side (embedding
vector, cross-encoder candidate text, Bayes term counts) straight from the
live disease_master.json via the same functions production uses
(pharmacy_service._disease_embeddings / _core_symptom_text), WITHOUT
excluding the held-out fragment first. That is real data leakage -- the
query text for disease D was still present verbatim inside D's own
document/count data, so the eval was partly measuring lookup, not retrieval.
Concretely, this is the same leak the original eval_symptom_embeddings.py /
eval_top15.py harness explicitly avoids (its own docstring: "the model has
never seen the held-out fragment matched to anything during this eval").
Fixed here by rebuilding the TRUE disease's embedding row / cross-encoder
text / Bayes counts leave-one-out (excluding the held-out fragment) for
every query, while leaving all 322 other (non-true) diseases' data as-is
(they were never at risk of leaking the held-out disease's own text).

Difference from eval_symptom_embeddings.py's fragment-level corpus: the
production disease-matching pipeline (pharmacy_service._embedding_shortlist,
medical_understanding._get_candidates) retrieves at DISEASE granularity --
one embedding vector per disease (name + category + core symptoms +
findings) -- not one vector per symptom fragment, and cross-encoder/Bayes
reranking is applied on top of that same disease-level candidate list in
production. So this eval measures retrieval quality at the SAME granularity
the reranking layer actually acts on, with the SAME 292 held-out queries.

Usage: python3 eval_retrieval_rerank.py [top_n_to_rerank]
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

from services.pharmacy_service import (  # noqa: E402
    load_kb, _core_symptom_text, _flatten_findings, _normalize_tokens,
    _disease_embeddings, _embedding_model,
)
from services import retrieval_rerank as rr  # noqa: E402
import numpy as np

RERANK_TOP_N = int(sys.argv[1]) if len(sys.argv) > 1 else 25


def build_eval_queries():
    """Same held-out-fragment methodology as eval_symptom_embeddings.py /
    eval_top15.py: hold out the LAST core-symptom fragment per disease (only
    for diseases with >=2 fragments, so at least one real fragment remains).
    Returns (disease_id, query_text[<=300 chars, used to encode/score the
    query], held_out_full[untruncated, used to exactly exclude this fragment
    from its own disease's document/count data])."""
    kb = load_kb()
    diseases = kb["diseases"]
    queries = []
    for did, dz in diseases.items():
        terms = _core_symptom_text(dz)
        if len(terms) >= 2:
            held_out_full = terms[-1]
            queries.append((did, held_out_full[:300], held_out_full))
    return queries


def _loo_core_and_findings(dz, held_out_full):
    core = [t for t in _core_symptom_text(dz) if t != held_out_full]
    findings = []
    _flatten_findings(dz.get("symptoms", {}), findings, limit=8)
    findings = [f for f in findings if f != held_out_full]
    return core, findings


def loo_embedding_text(dz, held_out_full):
    """Same text-construction formula as pharmacy_service._disease_embeddings,
    with the held-out fragment excluded from both the core-symptom and the
    flattened-findings components (it can independently appear in either)."""
    core, findings = _loo_core_and_findings(dz, held_out_full)
    text = " ".join([dz.get("name", ""), dz.get("category", "")] + core + findings)[:1500]
    return text


def loo_ce_text(dz, did, held_out_full):
    core, _ = _loo_core_and_findings(dz, held_out_full)
    snippet = "; ".join(t[:150] for t in core[:6])
    return f"{dz.get('name', did)} ({dz.get('category', '')}). {snippet}".strip()


def loo_bayes_counts(dz, held_out_full):
    """Same counting method as ml_training/build_bayes_cooccurrence.py
    (one count per phrase a term appears in, not per raw occurrence), with
    the held-out fragment excluded."""
    core, _ = _loo_core_and_findings(dz, held_out_full)
    name_cat = f"{dz.get('name', '')} {dz.get('category', '')}".strip()
    phrases = list(core)
    if name_cat:
        phrases.append(name_cat)
    counts = {}
    for phrase in phrases:
        for t in _normalize_tokens(phrase):
            counts[t] = counts.get(t, 0) + 1
    return {"total": sum(counts.values()), "counts": counts}


def default_ce_text(kb, did):
    dz = kb["diseases"][did]
    terms = _core_symptom_text(dz)[:6]
    snippet = "; ".join(t[:150] for t in terms)
    return f"{dz.get('name', did)} ({dz.get('category', '')}). {snippet}".strip()


def rank_of(did, ordered_ids):
    try:
        return ordered_ids.index(did) + 1
    except ValueError:
        return None


def main():
    kb = load_kb()
    queries = build_eval_queries()
    print(f"Eval set: {len(queries)} held-out queries (disease-level candidate pool: 323 diseases).")
    print(f"Leave-one-out: each query's own disease has its held-out fragment excluded from its "
          f"embedding row / cross-encoder text / Bayes counts for that query.")
    print(f"Reranking the embedding's own top-{RERANK_TOP_N} candidates per query.\n")

    model = _embedding_model()
    ids, matrix = _disease_embeddings()
    assert model is not None and ids is not None, "embedding model / disease matrix failed to load"
    id_index = {did: i for i, did in enumerate(ids)}

    bayes_model = rr._bayes_model()
    assert bayes_model is not None, "Bayes model artifact missing -- run build_bayes_cooccurrence.py first"

    baseline_top1 = baseline_top5 = baseline_top15 = 0
    reranked_top1 = reranked_top5 = reranked_top15 = 0
    ce_only_top1 = ce_only_top5 = ce_only_top15 = 0
    bayes_only_top1 = bayes_only_top5 = bayes_only_top15 = 0
    n = len(queries)

    t0 = time.time()
    for i, (true_did, query_text, held_out_full) in enumerate(queries):
        dz = kb["diseases"][true_did]
        true_idx = id_index[true_did]

        # --- Leave-one-out substitution for the query's own disease -------
        original_row = matrix[true_idx].copy()
        loo_text = loo_embedding_text(dz, held_out_full)
        loo_row = model.encode([loo_text], normalize_embeddings=True)[0]
        matrix[true_idx] = loo_row

        original_bayes_entry = bayes_model["diseases"].get(true_did)
        bayes_model["diseases"][true_did] = loo_bayes_counts(dz, held_out_full)

        try:
            q_emb = model.encode([query_text], normalize_embeddings=True)[0]
            sims = matrix @ q_emb
            order = np.argsort(-sims)
            full_ranked_ids = [ids[j] for j in order]

            baseline_rank = rank_of(true_did, full_ranked_ids)
            if baseline_rank == 1:
                baseline_top1 += 1
            if baseline_rank is not None and baseline_rank <= 5:
                baseline_top5 += 1
            if baseline_rank is not None and baseline_rank <= 15:
                baseline_top15 += 1

            top_n_candidates = [(ids[j], float(sims[j])) for j in order[:RERANK_TOP_N]]

            def text_fn(did, _true_did=true_did, _dz=dz, _held_out=held_out_full):
                if did == _true_did:
                    return loo_ce_text(_dz, did, _held_out)
                return default_ce_text(kb, did)

            reranked = rr.rerank_candidates(query_text, top_n_candidates, text_fn)
            reranked_ids = [did for did, _ in reranked]
            if true_did not in reranked_ids and baseline_rank is not None and baseline_rank <= RERANK_TOP_N:
                raise AssertionError(f"true disease {true_did} dropped by reranker despite being in its input window")

            reranked_rank = rank_of(true_did, reranked_ids)
            if reranked_rank is None:
                reranked_rank = baseline_rank  # true disease wasn't even in the top-N embedding window

            # Diagnostic: standalone accuracy of each signal alone (within the
            # SAME top-N embedding window), to characterize whether the
            # combined signal's regression traces to one specific weak
            # component rather than guessing at a fix.
            window_ids = [did for did, _ in top_n_candidates]
            ce_scores = rr.cross_encoder_scores(query_text, [text_fn(did) for did in window_ids])
            ce_rank = None
            if ce_scores is not None:
                ce_ordered = [did for did, _ in sorted(zip(window_ids, ce_scores), key=lambda x: -x[1])]
                ce_rank = rank_of(true_did, ce_ordered)
                if ce_rank is None:
                    ce_rank = baseline_rank

            bayes_sc = rr.bayes_scores(query_text, window_ids)
            bayes_rank = None
            if bayes_sc is not None:
                bayes_ordered = sorted(window_ids, key=lambda d: -bayes_sc.get(d, float("-inf")))
                bayes_rank = rank_of(true_did, bayes_ordered)
                if bayes_rank is None:
                    bayes_rank = baseline_rank
        finally:
            matrix[true_idx] = original_row
            if original_bayes_entry is not None:
                bayes_model["diseases"][true_did] = original_bayes_entry
            else:
                bayes_model["diseases"].pop(true_did, None)

        if reranked_rank == 1:
            reranked_top1 += 1
        if reranked_rank is not None and reranked_rank <= 5:
            reranked_top5 += 1
        if reranked_rank is not None and reranked_rank <= 15:
            reranked_top15 += 1

        if ce_rank == 1:
            ce_only_top1 += 1
        if ce_rank is not None and ce_rank <= 5:
            ce_only_top5 += 1
        if ce_rank is not None and ce_rank <= 15:
            ce_only_top15 += 1

        if bayes_rank == 1:
            bayes_only_top1 += 1
        if bayes_rank is not None and bayes_rank <= 5:
            bayes_only_top5 += 1
        if bayes_rank is not None and bayes_rank <= 15:
            bayes_only_top15 += 1

        if (i + 1) % 50 == 0:
            print(f"  ...{i + 1}/{n} queries, {time.time() - t0:.0f}s elapsed")

    print(f"\nDone in {time.time() - t0:.0f}s.\n")
    print("BEFORE (embedding-only ranking over all 323 diseases, leave-one-out):")
    print(f"  top-1  recall: {baseline_top1 / n:.3f} ({baseline_top1}/{n})")
    print(f"  top-5  recall: {baseline_top5 / n:.3f} ({baseline_top5}/{n})")
    print(f"  top-15 recall: {baseline_top15 / n:.3f} ({baseline_top15}/{n})")
    print(f"\nAFTER (embedding top-{RERANK_TOP_N} reranked by combined embedding+cross-encoder+Bayes "
          f"signal, leave-one-out):")
    print(f"  top-1  recall: {reranked_top1 / n:.3f} ({reranked_top1}/{n})")
    print(f"  top-5  recall: {reranked_top5 / n:.3f} ({reranked_top5}/{n})")
    print(f"  top-15 recall: {reranked_top15 / n:.3f} ({reranked_top15}/{n})")
    print(f"\nDIAGNOSTIC -- cross-encoder ALONE re-ranking the same top-{RERANK_TOP_N} window (leave-one-out):")
    print(f"  top-1  recall: {ce_only_top1 / n:.3f} ({ce_only_top1}/{n})")
    print(f"  top-5  recall: {ce_only_top5 / n:.3f} ({ce_only_top5}/{n})")
    print(f"  top-15 recall: {ce_only_top15 / n:.3f} ({ce_only_top15}/{n})")
    print(f"\nDIAGNOSTIC -- Bayes co-occurrence ALONE re-ranking the same top-{RERANK_TOP_N} window (leave-one-out):")
    print(f"  top-1  recall: {bayes_only_top1 / n:.3f} ({bayes_only_top1}/{n})")
    print(f"  top-5  recall: {bayes_only_top5 / n:.3f} ({bayes_only_top5}/{n})")
    print(f"  top-15 recall: {bayes_only_top15 / n:.3f} ({bayes_only_top15}/{n})")


if __name__ == "__main__":
    main()
