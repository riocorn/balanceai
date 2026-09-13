from Bio import Entrez
import json, time, os

Entrez.email = "mrdabhay3@gmail.com"

QUERIES = [
    ("vitamin_d_deficiency", "vitamin D deficiency symptoms fatigue bone pain muscle weakness"),
    ("iron_deficiency", "iron deficiency anemia symptoms fatigue pallor nail changes tongue"),
    ("vitamin_b12_deficiency", "vitamin B12 deficiency symptoms fatigue neurological anemia"),
    ("zinc_deficiency", "zinc deficiency symptoms skin hair loss taste smell immunity"),
    ("calcium_deficiency", "calcium deficiency symptoms muscle cramps tetany bone density"),
    ("magnesium_deficiency", "magnesium deficiency symptoms cramps fatigue anxiety sleep"),
    ("vitamin_c_deficiency", "vitamin C deficiency scurvy symptoms bleeding gums fatigue"),
    ("vitamin_a_deficiency", "vitamin A deficiency night blindness skin symptoms India"),
    ("folate_deficiency", "folate folic acid deficiency symptoms anemia neural tube"),
    ("iodine_deficiency", "iodine deficiency goiter hypothyroid symptoms India"),
    ("vitamin_b6_deficiency", "vitamin B6 pyridoxine deficiency symptoms peripheral neuropathy"),
    ("omega3_deficiency", "omega-3 fatty acid deficiency symptoms dry skin brain fog India"),
    ("selenium_deficiency", "selenium deficiency symptoms thyroid muscle weakness India"),
    ("potassium_deficiency", "potassium deficiency hypokalemia symptoms fatigue cramps weakness"),
    ("copper_deficiency", "copper deficiency symptoms anemia neurological hair depigmentation"),
    ("nail_signs_deficiency", "nail changes signs micronutrient deficiency koilonychia leukonychia"),
    ("tongue_signs_deficiency", "tongue signs glossitis micronutrient deficiency B12 iron folate"),
    ("eye_signs_deficiency", "eye signs conjunctival pallor Bitot spots micronutrient deficiency"),
    ("skin_signs_deficiency", "skin manifestations micronutrient deficiency dermatitis pellagra"),
    ("indian_diet_deficiency", "micronutrient deficiency Indian population prevalence NFHS diet"),
]

OUT = "/home/abhay/Downloads/medical/balanceai/data/pubmed"
os.makedirs(OUT, exist_ok=True)

def fetch(query_name, query_str, max_results=50):
    out_file = f"{OUT}/{query_name}.json"
    if os.path.exists(out_file):
        print(f"  SKIP (exists): {query_name}")
        return

    handle = Entrez.esearch(db="pubmed", term=query_str, retmax=max_results, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    ids = record["IdList"]
    if not ids:
        print(f"  NO RESULTS: {query_name}")
        return

    time.sleep(0.4)
    handle = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="xml", retmode="xml")
    xml_data = handle.read()
    handle.close()

    from Bio import Medline
    import io
    handle2 = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="medline", retmode="text")
    records = list(Medline.parse(handle2))
    handle2.close()

    papers = []
    for r in records:
        papers.append({
            "pmid": r.get("PMID", ""),
            "title": r.get("TI", ""),
            "abstract": r.get("AB", ""),
            "authors": r.get("AU", []),
            "journal": r.get("JT", ""),
            "year": r.get("DP", "")[:4] if r.get("DP") else "",
            "keywords": r.get("OT", []),
            "mesh": r.get("MH", []),
        })

    with open(out_file, "w") as f:
        json.dump({"query": query_str, "count": len(papers), "papers": papers}, f, indent=2)
    print(f"  DONE: {query_name} — {len(papers)} papers")
    time.sleep(0.4)

print("=== PubMed Pull Starting ===")
for name, q in QUERIES:
    fetch(name, q)
print("=== Done ===")
