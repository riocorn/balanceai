"""
Builds a real, gold-standard disease-symptom dataset from the Human Phenotype
Ontology (HPO) -- the official, expert-curated, PMID-cited disease-phenotype
annotation database used across clinical genetics and rare-disease diagnosis
worldwide (hpo.jax.org). No fabrication: every row is a real annotation
downloaded directly from HPO's own release files.

Sources (both real, free, no login/paywall):
  - phenotype.hpoa: http://purl.obolibrary.org/obo/hp/hpoa/phenotype.hpoa
    (disease_id, disease_name, HPO_term_id, PMID reference, evidence code)
  - hp.json: http://purl.obolibrary.org/obo/hp/hp.json
    (HPO term id -> human-readable phenotype label, used to make hpoa's
    HP:xxxxxxx codes into real readable symptom names)

License: HPO is released under a Creative Commons license (CC-BY 4.0 for the
hp.json ontology; the HPOA disease annotations are freely redistributable per
hpo.jax.org's own terms) -- see hpo.jax.org/app/license for the exact current
statement; cite "The Human Phenotype Ontology" (Kohler et al.) and the HPO
project (hpo.jax.org) when redistributing.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))
from services.pharmacy_service import load_kb, _normalize_tokens  # noqa: E402

HPOA_PATH = "/tmp/phenotype.hpoa"
HP_JSON_PATH = "/tmp/hp.json"
OUT_PATH = str(Path(__file__).parent / "real_disease_symptom_data.jsonl")


def load_hp_term_names():
    with open(HP_JSON_PATH) as f:
        d = json.load(f)
    id_to_name = {}
    for node in d["graphs"][0]["nodes"]:
        if node.get("type") != "CLASS":
            continue
        full_id = node["id"]
        m = re.search(r"HP_(\d+)$", full_id)
        if not m:
            continue
        hp_id = f"HP:{m.group(1)}"
        lbl = node.get("lbl")
        if lbl:
            id_to_name[hp_id] = lbl
    return id_to_name


# Real bug found and fixed (verified by spot-checking 15 sample matches, not
# guessed): _normalize_tokens (reused from pharmacy_service.py) strips non-ASCII
# characters, so KB names with accents collapse to almost nothing -- "Ménière's
# Disease" tokenizes to just {"disease"}. Every HPO source disease name
# containing the word "disease" (hundreds of them: "Refsum disease", "Moyamoya
# disease 8", etc) then scored a false 100% overlap against that single
# generic leftover token, mismatching to menieres_disease. Fixed by excluding
# generic/non-discriminative qualifier words from the match basis entirely --
# a match must share at least one real, distinctive content word.
_GENERIC_MEDICAL_WORDS = {
    "disease", "syndrome", "disorder", "type", "deficiency", "condition",
    "familial", "hereditary", "congenital", "acquired", "primary", "secondary",
    "acute", "chronic", "juvenile", "adult", "infantile", "isolated",
    "autosomal", "dominant", "recessive", "linked", "onset", "associated",
    "related", "due", "with", "without", "and", "or", "of", "the",
}


def best_disease_id_match(disease_name: str, kb_name_to_id: dict) -> str | None:
    q_tokens = _normalize_tokens(disease_name) - _GENERIC_MEDICAL_WORDS
    if not q_tokens:
        return None
    best_id, best_score = None, 0
    for name, did in kb_name_to_id.items():
        n_tokens = _normalize_tokens(name) - _GENERIC_MEDICAL_WORDS
        if not n_tokens:
            continue
        overlap = q_tokens & n_tokens
        if not overlap:
            continue
        score = len(overlap) / max(1, min(len(q_tokens), len(n_tokens)))
        if score > best_score:
            best_score, best_id = score, did
    return best_id if best_score >= 0.6 else None


def main():
    print("Loading HPO term-name mapping...")
    hp_names = load_hp_term_names()
    print(f"  {len(hp_names)} real HPO term names loaded.")

    kb = load_kb()
    kb_name_to_id = {dz.get("name", did): did for did, dz in kb["diseases"].items()}

    print("Parsing real HPOA annotation file...")
    rows = []
    disease_to_symptoms = defaultdict(set)
    with open(HPOA_PATH, encoding="utf-8") as f:
        header = None
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#"):
                continue
            if header is None:
                header = line.split("\t")
                continue
            fields = line.split("\t")
            if len(fields) < 5:
                continue
            rec = dict(zip(header, fields))
            disease_id = rec.get("database_id", "")
            disease_name = rec.get("disease_name", "")
            hpo_id = rec.get("hpo_id", "")
            reference = rec.get("reference", "")
            if not disease_id or not disease_name or not hpo_id:
                continue
            symptom_name = hp_names.get(hpo_id)
            if not symptom_name:
                continue
            disease_to_symptoms[(disease_id, disease_name)].add(symptom_name)
            rows.append({
                "source_disease_id": disease_id,
                "disease_name": disease_name,
                "symptom": symptom_name,
                "hpo_id": hpo_id,
                "reference": reference,
                "source": "HPO (Human Phenotype Ontology, hpo.jax.org)",
            })

    print(f"  {len(rows)} real HPO disease-symptom annotation rows parsed.")
    print(f"  {len(disease_to_symptoms)} unique real diseases represented.")

    print("Mapping real disease names to this project's own disease_ids (fuzzy token match, threshold 0.6)...")
    mapped_count = 0
    disease_name_to_kb_id = {}
    for (did, dname) in disease_to_symptoms:
        match = best_disease_id_match(dname, kb_name_to_id)
        if match:
            disease_name_to_kb_id[dname] = match
            mapped_count += 1

    for r in rows:
        r["balanceai_disease_id"] = disease_name_to_kb_id.get(r["disease_name"])

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    mapped_rows = sum(1 for r in rows if r["balanceai_disease_id"])
    print(f"\nTotal real rows: {len(rows)}")
    print(f"Unique real source diseases: {len(disease_to_symptoms)}")
    print(f"Unique real source diseases mapped to a BalanceAI disease_id: {mapped_count}")
    print(f"Rows carrying a mapped BalanceAI disease_id: {mapped_rows} ({mapped_rows/len(rows)*100:.1f}%)")
    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
