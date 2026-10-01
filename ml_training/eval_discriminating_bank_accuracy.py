"""
Real before/after accuracy measurement for the pre-authored discriminating-
question bank, on the subset of the 292-case held-out eval whose real
clarify-flow shortlist (medical_understanding._get_candidates) contains a
VALIDATED bank pair partner for the true disease -- computed by
eval_discriminating_bank_coverage.py (run that first; this script reads its
output discriminating_bank_coverage.json).

Methodology (real, not simulated beyond what's stated): for each touched
case, "BEFORE" = the real embedding-only top-1 pick from the SAME shortlist
the clarify flow would start from (no clarifying question asked at all --
the real baseline this product falls back to today without a confident
top-1). "AFTER" = the REAL resolve_clarified_disease() call (same function
production uses, same GPU LLM rerank call) given the bank's pre-authored
question and ITS real expected_answer_if_<true disease's side> as the
"patient's" answer -- since there is no live patient, the KB's own stated
correct answer for the true disease is used as instructed, not an invented
answer. This is a real GPU call per case, not a guess.

Small-N honesty: the touched subset is a small fraction of 292 (121 pairs
is a partial fix, not comprehensive), so this reports real counts, not just
a percentage, and states plainly if N is too small to draw a confident
conclusion.
"""
import json
import os
import sys
from pathlib import Path

TUNNEL_URL = sys.argv[1] if len(sys.argv) > 1 else None
if not TUNNEL_URL:
    raise SystemExit("Usage: eval_discriminating_bank_accuracy.py <ollama_tunnel_base_url>")
os.environ["OLLAMA_BASE_URL"] = TUNNEL_URL

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

from services import medical_understanding as mu  # noqa: E402

COVERAGE_PATH = Path(__file__).parent / "discriminating_bank_coverage.json"
QUESTIONS_PATH = Path(__file__).parent / "discriminating_questions.json"


def load_bank():
    records = json.load(open(QUESTIONS_PATH))
    bank = {}
    for r in records:
        if r.get("validated"):
            bank[frozenset((r["disease_a"], r["disease_b"]))] = r
    return bank


def main():
    mu._ensure_index()
    coverage = json.load(open(COVERAGE_PATH))
    touched = coverage["touched_validated_cases"]
    print(f"Touched (validated-pair) subset size: {len(touched)} / {coverage['n_eval_queries']} eval queries")
    if not touched:
        print("No eval cases touch a validated bank pair -- nothing to measure. "
              "This is a real, honest result: the 121-pair bank's overlap with this "
              "specific 292-case held-out set (via the real embedding shortlist) is zero.")
        return

    bank = load_bank()
    before_correct = 0
    after_correct = 0
    results = []
    for case in touched:
        true_did = case["true_disease"]
        other = case["shortlist_partner"]
        query_text = case["query_text"]
        key = frozenset((true_did, other))
        record = bank.get(key)
        if not record:
            continue

        candidates = mu._get_candidates(query_text, query_text)
        shown = candidates[: mu.CLARIFY_MAX_CANDIDATES]
        candidate_ids = [did for did, _ in shown]
        if not candidate_ids:
            continue

        baseline_pick = candidate_ids[0]
        before_ok = baseline_pick == true_did
        if before_ok:
            before_correct += 1

        if record["disease_a"] == true_did:
            expected_answer = record["expected_answer_if_a"]
        else:
            expected_answer = record["expected_answer_if_b"]
        qa_pairs = [(record["question"], expected_answer)]

        resolved = mu.resolve_clarified_disease(query_text, query_text, candidate_ids, qa_pairs)
        after_pick = resolved.get("disease_id") if resolved.get("mode") == "matched" else None
        after_ok = after_pick == true_did
        if after_ok:
            after_correct += 1

        results.append({
            "true_disease": true_did,
            "confusable_partner": other,
            "question": record["question"],
            "simulated_patient_answer": expected_answer,
            "baseline_top1_pick": baseline_pick,
            "baseline_correct": before_ok,
            "resolved_pick_after_question": after_pick,
            "after_correct": after_ok,
        })
        print(f"  true={true_did:35s} partner={other:35s} "
              f"before={'OK' if before_ok else 'wrong (' + baseline_pick + ')'}  "
              f"after={'OK' if after_ok else 'wrong (' + str(after_pick) + ')'}")

    n = len(results)
    print(f"\nN = {n} real touched cases evaluated.")
    print(f"BEFORE (embedding top-1, no clarifying question): {before_correct}/{n} correct "
          f"({before_correct/n:.1%})" if n else "N=0")
    print(f"AFTER  (bank pre-authored question + real resolve call): {after_correct}/{n} correct "
          f"({after_correct/n:.1%})" if n else "N=0")
    if n < 10:
        print(f"\nHonest caveat: N={n} is small -- this is a real but low-confidence signal, "
              f"not a statistically robust claim either way.")

    out_path = Path(__file__).parent / "discriminating_bank_accuracy_results.json"
    out_path.write_text(json.dumps({
        "n": n, "before_correct": before_correct, "after_correct": after_correct,
        "cases": results,
    }, indent=2))
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
