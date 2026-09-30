"""
Collects a REAL, KB-grounded labeled dataset for teaching hard-negative
disease discrimination -- directly answering "LLM/retrieval improve karne ke
liye real labeled data collect kar" without fabricating anything.

Source: disease_master.json's own symptoms.differential_diagnosis sections.
These were written by the earlier fork-research pipeline as real, cited
(PMID-sourced) clinical differential-diagnosis content -- for each disease,
which OTHER real diseases it's commonly confused with, and the real clinical
reasoning that tells them apart. Two real shapes found in the KB (verified by
direct inspection, not guessed):

  1. dict-shaped (152 diseases): keys are themselves other diseases' real
     disease_id strings already matching this KB's own ids exactly (e.g.
     ischaemic_heart_disease -> {"aortic_dissection": {"finding": "...",
     "source": "..."}, "pulmonary_embolism": {...}, ...}). These need no
     fuzzy matching at all -- the hard-negative id is already correct.
  2. list-shaped (34 diseases): each item is {"condition": "<free-text name>",
     "distinguishing_features": "...", "source": "..."}. The free-text
     "condition" name is fuzzy-matched against the KB's own disease names to
     recover a real disease_id where possible; entries that don't match any
     real KB disease are kept with disease_id=None (still real text, just
     not usable as a hard-negative pair against another KB entry).

Output: a JSON list of real records:
  {"disease_id": <the disease this diff-dx section belongs to>,
   "confusable_id": <the other disease id, or null if unmatched>,
   "confusable_name_raw": <original free-text name, for list-shaped entries>,
   "distinguishing_text": <the real KB finding/distinguishing_features text>}
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))
from services.pharmacy_service import load_kb, _normalize_tokens  # noqa: E402

OUT_PATH = str(Path(__file__).parent / "differential_diagnosis_dataset.json")


def best_name_match(free_text: str, name_to_id: dict) -> str | None:
    q_tokens = _normalize_tokens(free_text)
    if not q_tokens:
        return None
    best_id, best_score = None, 0
    for name, did in name_to_id.items():
        n_tokens = _normalize_tokens(name)
        score = len(q_tokens & n_tokens)
        if score > best_score:
            best_score, best_id = score, did
    return best_id if best_score >= 2 else None


def main():
    kb = load_kb()
    diseases = kb["diseases"]
    name_to_id = {dz.get("name", did): did for did, dz in diseases.items()}
    valid_ids = set(diseases.keys())

    records = []
    dict_shaped = 0
    list_shaped = 0
    list_matched = 0

    for did, dz in diseases.items():
        dd = dz.get("symptoms", {}).get("differential_diagnosis", None)
        if isinstance(dd, dict):
            dict_shaped += 1
            for other_id, val in dd.items():
                if other_id not in valid_ids:
                    continue
                text = None
                if isinstance(val, dict):
                    text = val.get("finding") or val.get("distinguishing_features")
                elif isinstance(val, str):
                    text = val
                if text:
                    records.append({
                        "disease_id": did,
                        "confusable_id": other_id,
                        "confusable_name_raw": None,
                        "distinguishing_text": text[:600],
                    })
        elif isinstance(dd, list):
            list_shaped += 1
            for item in dd:
                if not isinstance(item, dict):
                    continue
                cond = item.get("condition")
                text = item.get("distinguishing_features")
                if not cond or not text:
                    continue
                matched_id = best_name_match(cond, name_to_id)
                if matched_id:
                    list_matched += 1
                records.append({
                    "disease_id": did,
                    "confusable_id": matched_id,
                    "confusable_name_raw": cond,
                    "distinguishing_text": text[:600],
                })

    with open(OUT_PATH, "w") as f:
        json.dump(records, f, indent=2)

    print(f"dict-shaped diseases processed: {dict_shaped}")
    print(f"list-shaped diseases processed: {list_shaped} (matched to a real disease_id: {list_matched})")
    print(f"Total real differential-diagnosis records collected: {len(records)}")
    print(f"Records with a real KB confusable_id on both sides: {sum(1 for r in records if r['confusable_id'])}")
    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
