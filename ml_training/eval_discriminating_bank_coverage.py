"""
Real coverage measurement: of the 292-case held-out eval set (same
leave-one-out methodology as eval_retrieval_rerank.py / eval_symptom_embeddings.py),
how many cases actually have the true disease's real embedding-based
clarify-flow shortlist (medical_understanding._get_candidates, top
CLARIFY_MAX_CANDIDATES=8, the SAME function production uses) contain at
least one OTHER disease that forms one of the 121 real KB-authored
confusable pairs with it. This is the honest denominator for "how many of
the 292 eval cases does the discriminating-question bank actually touch" --
121 pairs is a small fraction of all possible shortlist combinations, so
most eval cases will NOT be touched; this script measures exactly how many
are, rather than assuming.

Caveat (stated honestly): _get_candidates uses medical_understanding's own
cached embedding index (data/disease_master.json.understanding_embeddings.npy),
built from the full (non-leave-one-out) corpus text -- unlike
eval_retrieval_rerank.py this script does NOT rebuild that index per-query
with the held-out fragment excluded, so there is a small risk a query's own
held-out fragment indirectly influenced its disease's cached embedding row.
This is a coverage/smoke measurement over a downstream decision step, not
the primary retrieval-accuracy metric, so this caveat is accepted and
disclosed rather than engineering a second leave-one-out index rebuild.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402
from services import medical_understanding as mu  # noqa: E402

DIFF_DX_DATA = Path(__file__).parent / "differential_diagnosis_dataset.json"
QUESTIONS_PATH = Path(__file__).parent / "discriminating_questions.json"


def build_eval_queries():
    kb = load_kb()
    diseases = kb["diseases"]
    queries = []
    for did, dz in diseases.items():
        terms = _core_symptom_text(dz)
        if len(terms) >= 2:
            held_out_full = terms[-1]
            queries.append((did, held_out_full[:300]))
    return queries


def load_all_kb_pairs():
    records = json.load(open(DIFF_DX_DATA))
    pairs = set()
    for r in records:
        a, b = r.get("disease_id"), r.get("confusable_id")
        if a and b:
            pairs.add(frozenset((a, b)))
    return pairs


def load_validated_pairs():
    if not QUESTIONS_PATH.exists():
        return set()
    records = json.load(open(QUESTIONS_PATH))
    pairs = set()
    for r in records:
        if r.get("validated"):
            a, b = r.get("disease_a"), r.get("disease_b")
            if a and b:
                pairs.add(frozenset((a, b)))
    return pairs


def main():
    mu._ensure_index()
    queries = build_eval_queries()
    print(f"Eval set: {len(queries)} held-out queries.")

    all_kb_pairs = load_all_kb_pairs()
    validated_pairs = load_validated_pairs()
    print(f"Total KB-authored pairs (valid disease_id/confusable_id): {len(all_kb_pairs)}")
    print(f"Validated (patient-answerable) pairs in the bank: {len(validated_pairs)}")

    touched_any_kb_pair = []
    touched_validated_pair = []
    for true_did, query_text in queries:
        candidates = mu._get_candidates(query_text, query_text)
        shown = candidates[: mu.CLARIFY_MAX_CANDIDATES]
        ids = [did for did, _ in shown]
        if true_did not in ids:
            continue  # true disease not even in the clarify shortlist for this query
        for other in ids:
            if other == true_did:
                continue
            key = frozenset((true_did, other))
            if key in all_kb_pairs:
                touched_any_kb_pair.append((true_did, other, query_text))
            if key in validated_pairs:
                touched_validated_pair.append((true_did, other, query_text))

    print(f"\nQueries whose real clarify-shortlist contains a KB-authored pair partner: "
          f"{len(touched_any_kb_pair)}/{len(queries)}")
    print(f"Queries whose real clarify-shortlist contains a VALIDATED bank pair partner: "
          f"{len(touched_validated_pair)}/{len(queries)}")
    print("\nTouched (validated) cases:")
    for true_did, other, qt in touched_validated_pair:
        print(f"  true={true_did}  shortlist_partner={other}  query={qt[:80]!r}")

    out = {
        "n_eval_queries": len(queries),
        "n_touched_any_kb_pair": len(touched_any_kb_pair),
        "n_touched_validated_pair": len(touched_validated_pair),
        "touched_validated_cases": [
            {"true_disease": t, "shortlist_partner": o, "query_text": qt}
            for t, o, qt in touched_validated_pair
        ],
    }
    out_path = Path(__file__).parent / "discriminating_bank_coverage.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
