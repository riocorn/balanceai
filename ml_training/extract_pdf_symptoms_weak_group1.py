import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))
from services.pharmacy_service import load_kb, _normalize_tokens  # noqa: E402

OUT_PATH = Path(__file__).parent / "top5_symptoms_group1.json"
TXT_PATH = Path("/tmp/disease_report.txt")
KB = load_kb()["diseases"]

WEAK_IDS = [
    "cardiogenic_shock", "hypertension", "bronchial_asthma", "pneumonia",
    "diabetes_mellitus", "thyroid_disorders", "chronic_kidney_disease",
    "dyslipidemia", "cirrhosis", "peptic_ulcer_disease",
    "inflammatory_bowel_disease", "acute_pancreatitis", "celiac_disease",
    "migraine", "breast_cancer", "major_depressive_disorder",
    "colorectal_cancer", "prostate_cancer", "generalized_anxiety_disorder", "bppv",
]


def get_disease_sections():
    lines = TXT_PATH.read_text().splitlines()
    header_re = re.compile(r"Disease\s+(\d+):\s*(.+)")
    headers = []
    for i, line in enumerate(lines):
        m = header_re.search(line.strip())
        if m:
            headers.append((i, m.group(2).strip()))
    # Dedup consecutive near-identical headers (TOC + real section both match);
    # keep the LATER occurrence of each disease name since that's the real
    # full section, not the table-of-contents line.
    by_name = {}
    for i, name in headers:
        by_name[name] = i  # later overwrites earlier -> keeps last occurrence
    sorted_starts = sorted(by_name.items(), key=lambda x: x[1])
    sections = []
    for idx, (name, start) in enumerate(sorted_starts):
        end = sorted_starts[idx + 1][1] if idx + 1 < len(sorted_starts) else len(lines)
        sections.append((name, start, end, "\n".join(lines[start:end])))
    return sections


def find_section_for_disease(disease_name, sections):
    target_tokens = _normalize_tokens(disease_name)
    best, best_score = None, 0
    for name, start, end, text in sections:
        score = len(target_tokens & _normalize_tokens(name))
        if score > best_score:
            best_score, best = score, (name, text)
    return best if best_score >= 1 else None


def extract_symptoms_from_section(text):
    """Real extraction: look for a 'Symptom' heading block in the section and
    pull short lines that look like real symptom names (not full paragraphs)."""
    lines = text.splitlines()
    candidates = []
    in_symptom_block = False
    for line in lines:
        stripped = line.strip()
        if re.search(r"symptom", stripped, re.IGNORECASE) and len(stripped) < 60:
            in_symptom_block = True
            continue
        if in_symptom_block:
            if not stripped:
                continue
            if re.match(r"^(Exact medicine|Effectiveness|Why \(biological)", stripped):
                break
            word_count = len(stripped.split())
            if 1 <= word_count <= 12 and not stripped.startswith(("-", "•")):
                candidates.append(stripped.lstrip("-• "))
            elif stripped.startswith(("-", "•")):
                candidates.append(stripped.lstrip("-• "))
            if len(candidates) >= 8:
                break
    return candidates[:5]


def main():
    sections = get_disease_sections()
    print(f"Found {len(sections)} real disease sections in the PDF.")

    data = json.load(open(OUT_PATH))
    by_id = {e["disease_id"]: e for e in data}
    updated = 0

    for did in WEAK_IDS:
        dz = KB.get(did)
        if not dz:
            continue
        name = dz.get("name", did)
        match = find_section_for_disease(name, sections)
        if not match:
            print(f"  {did}: no PDF section match found")
            continue
        matched_name, section_text = match
        symptoms = extract_symptoms_from_section(section_text)
        if len(symptoms) >= 3:
            entry = by_id[did]
            existing = entry.get("top_5_symptoms", [])
            combined = existing + [s for s in symptoms if s not in existing]
            entry["top_5_symptoms"] = combined[:5]
            entry["sources_used"] = entry.get("sources_used", []) + [
                f"PDF: BalanceAI_Disease_Prescription_Report (matched section: {matched_name})"
            ]
            entry["confidence_note"] = f"supplemented with real PDF symptom section ({len(symptoms)} extracted)"
            updated += 1
            print(f"  {did}: matched '{matched_name}', extracted {symptoms}")
        else:
            print(f"  {did}: matched '{matched_name}' but extraction found only {len(symptoms)} usable items")

    with open(OUT_PATH, "w") as f:
        json.dump(list(by_id.values()), f, indent=2)
    print(f"Updated {updated}/{len(WEAK_IDS)} weak diseases from the real PDF.")


if __name__ == "__main__":
    main()
