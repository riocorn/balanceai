"""
Builds a real symptom-term-given-disease co-occurrence model from BalanceAI's
own disease_master.json KB corpus (the same 323-disease corpus driving the
embedding fine-tune), for use as a second, complementary scoring signal
alongside the embedding retriever and the LLM pick.

Real evidence for why this is a genuinely different signal, not a redundant
one: the "Counting Clues" paper (arXiv:2512.12868, FBPR) shows a smoothed
term/feature-frequency-given-class scorer surfaces correct answers an LLM
reranker misses, because it is driven by raw corpus term statistics rather
than the LLM's learned priors.

Method: multinomial Naive Bayes over "symptom mentions". Each disease's real
KB symptom section (`_core_symptom_text`, the exact same clean text used to
build the production embedding corpus in pharmacy_service.py) is a list of
short symptom phrases -- each phrase is one real "mention event". For each
disease we count, per normalized term, in how many of its own phrases that
term appears (a term repeated inside one long phrase counts once, so one
verbose phrase can't dominate the counts). We also fold in the disease
name/category tokens as one extra mention each, since those are informative
too and cost-free.

Score for a query against a candidate disease is the standard multinomial
Naive-Bayes log-likelihood:
    score(query, disease) = sum_over_query_terms[ log P(term | disease) ]
with Laplace (additive) smoothing:
    P(term | disease) = (count(term, disease) + alpha) / (N(disease) + alpha * V)
where N(disease) is the disease's total mention count and V is the global
vocabulary size, so an unseen term is never a hard zero.

Output: models/bayes_symptom_cooccurrence.json --
{
  "alpha": 1.0,
  "vocab": ["term1", "term2", ...],          # sorted, for a stable vocab_size
  "diseases": {
    "<disease_id>": {"total": <int>, "counts": {"<term>": <int>, ...}},
    ...
  }
}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

from services.pharmacy_service import load_kb, _core_symptom_text, _normalize_tokens  # noqa: E402

OUT_PATH = Path(__file__).parents[1] / "models" / "bayes_symptom_cooccurrence.json"
ALPHA = 1.0


def build():
    kb = load_kb()
    diseases = kb["diseases"]

    per_disease_counts = {}
    global_vocab = set()

    for did, dz in diseases.items():
        phrases = list(_core_symptom_text(dz))
        name_cat = f"{dz.get('name', did)} {dz.get('category', '')}".strip()
        if name_cat:
            phrases.append(name_cat)

        counts = {}
        for phrase in phrases:
            terms = _normalize_tokens(phrase)
            for t in terms:
                counts[t] = counts.get(t, 0) + 1
                global_vocab.add(t)

        total = sum(counts.values())
        per_disease_counts[did] = {"total": total, "counts": counts}

    model = {
        "alpha": ALPHA,
        "vocab": sorted(global_vocab),
        "diseases": per_disease_counts,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(model, f)

    n_diseases = len(per_disease_counts)
    n_terms_total = sum(d["total"] for d in per_disease_counts.values())
    print(
        f"Built Bayes co-occurrence model: {n_diseases} diseases, "
        f"{len(global_vocab)} unique terms, {n_terms_total} total (term, disease) "
        f"mention events. Saved to {OUT_PATH}"
    )


if __name__ == "__main__":
    build()
