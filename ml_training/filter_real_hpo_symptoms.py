"""
Real, ontology-grounded fix (not a keyword guess) for the finding that the
first HPO training run underperformed: some HPO annotations paired with a
disease are not real reportable symptoms at all (e.g. "Autosomal dominant
inheritance"), diluting the training signal.

HPO's own ontology graph (hp.json, downloaded from hpo.jax.org) has an
authoritative answer for this: every term is connected by real "is_a" edges
into a hierarchy rooted under top-level categories, and "Phenotypic
abnormality" (HP:0000118) is specifically the branch for genuine observable
signs/symptoms -- separate from "Mode of inheritance" (HP:0000005),
"Clinical modifier", "Frequency", "Past medical history", etc. This script
does a real graph traversal (not a keyword blocklist) to find every term that
IS a real descendant of HP:0000118, and filters real_disease_symptom_data.jsonl
down to only those rows.
"""
import json
from pathlib import Path
from collections import defaultdict

HP_JSON = "/tmp/hp.json"
IN_PATH = Path(__file__).parent / "real_disease_symptom_data.jsonl"
OUT_PATH = Path(__file__).parent / "real_disease_symptom_data_filtered.jsonl"

PHENOTYPIC_ABNORMALITY = "http://purl.obolibrary.org/obo/HP_0000118"


def hp_id_to_uri(hp_id: str) -> str:
    # "HP:0000118" -> ".../HP_0000118"
    return f"http://purl.obolibrary.org/obo/{hp_id.replace(':', '_')}"


def main():
    graph = json.load(open(HP_JSON))["graphs"][0]

    children = defaultdict(list)
    for e in graph["edges"]:
        if e.get("pred") == "is_a":
            children[e["obj"]].append(e["sub"])

    real_symptom_uris = set()
    stack = [PHENOTYPIC_ABNORMALITY]
    while stack:
        node = stack.pop()
        if node in real_symptom_uris:
            continue
        real_symptom_uris.add(node)
        stack.extend(children.get(node, []))

    print(f"Real descendant count of 'Phenotypic abnormality' in the HPO graph: {len(real_symptom_uris)}")

    kept, dropped = 0, 0
    drop_examples = []
    with open(IN_PATH) as fin, open(OUT_PATH, "w") as fout:
        for line in fin:
            r = json.loads(line)
            uri = hp_id_to_uri(r["hpo_id"])
            if uri in real_symptom_uris:
                fout.write(line)
                kept += 1
            else:
                dropped += 1
                if len(drop_examples) < 15:
                    drop_examples.append((r["symptom"], r["hpo_id"]))

    print(f"Kept (real symptom terms): {kept}")
    print(f"Dropped (non-symptom HPO categories -- inheritance/frequency/clinical-modifier/etc): {dropped}")
    print("Sample dropped rows (real, not guessed):")
    for sym, hid in drop_examples:
        print(f"  {sym!r} ({hid})")
    print(f"Saved filtered real data to {OUT_PATH}")


if __name__ == "__main__":
    main()
