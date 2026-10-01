"""
Builds the pre-authored discriminating-question bank for the 121 real
KB-authored hard-negative disease pairs (differential_diagnosis_dataset.json),
per the deep-research finding that real production systems (Ada Health,
Isabel Healthcare, SmartTriage) get better disambiguation from a pre-authored,
clinician-grounded question bank keyed to the specific symptom axes that
separate commonly-confused disease pairs, vs an LLM composing open-ended
clarifying questions on the fly.

For each real pair, the LLM (HuatuoGPT, GPU-hosted via the Colab/cloudflared
tunnel -- OLLAMA_BASE_URL must point at it, no CPU fallback) is given ONLY
real KB text for both diseases plus the KB's own real distinguishing_text,
and asked to phrase ONE concrete, plain-language, patient-answerable
yes/no-or-short-phrase question that uses that real distinguishing
information -- never invented, never an exam/lab/imaging finding a patient
can't self-report.

Output: ml_training/discriminating_questions.json, one record per pair:
{disease_a, disease_b, question, expected_answer_if_a, expected_answer_if_b,
 source, validated}
"""
import json
import os
import re
import sys
import time
from pathlib import Path

TUNNEL_URL = sys.argv[1] if len(sys.argv) > 1 else None
if not TUNNEL_URL:
    raise SystemExit("Usage: build_discriminating_question_bank.py <ollama_tunnel_base_url>")
os.environ["OLLAMA_BASE_URL"] = TUNNEL_URL

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "api"))

import requests  # noqa: E402
from services.pharmacy_service import load_kb, _core_symptom_text  # noqa: E402

ROOT = Path(__file__).parents[1]
DIFF_DX_DATA = Path(__file__).parent / "differential_diagnosis_dataset.json"
OUT_PATH = Path(__file__).parent / "discriminating_questions.json"

OLLAMA_CHAT_URL = f"{TUNNEL_URL}/api/chat"
MODEL = "hf.co/bartowski/HuatuoGPT-o1-8B-GGUF:Q5_K_M"
TIMEOUT_S = 150

EXAM_ONLY_BANNED_TERMS = [
    "murmur", "auscult", "palpat", "percuss", "biopsy", "scan", "mri",
    "x-ray", "xray", "ultrasound", "ecg", "ekg", "eeg", " ct ", "ct scan",
    "blood test", "lab result", "laboratory", "echocardiogram", "echo ",
    "endoscopy", "colonoscopy", "angiogram", "catheter", "doppler",
    "reflex test", "babinski", "spirometry", "pulmonary function",
    "blood pressure reading", "oxygen saturation reading", "pulse oximetry",
    "stethoscope", "examination reveals", "on examination", "radiograph",
    "imaging", "histology", "pathology report", "culture result",
    "serum level", "titer", "antibody test", "biomarker",
    "whooshing sound", "hear a sound in your chest", "hear your heart",
    "feel your pulse at", "sound when the doctor", "clicking sound in your",
]


def build_context_block(did, dz):
    name = dz.get("name", did)
    category = dz.get("category", "")
    terms = _core_symptom_text(dz)[:8]
    sym_text = "; ".join(t[:200] for t in terms)
    return f"{name} ({category}). Known real symptoms: {sym_text}"


def ollama_chat_json(system, user):
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=TIMEOUT_S)
    resp.raise_for_status()
    data = resp.json()
    content = data["message"]["content"]
    text = content.strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    return json.loads(text)


def is_exam_only(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in EXAM_ONLY_BANNED_TERMS)


QUESTION_SYSTEM_PROMPT = (
    "You are a doctor designing a short patient-facing questionnaire. You will be given two real "
    "diseases that are commonly confused with each other, real symptom information for both from a "
    "medical knowledge base, and a real clinical note explaining how to tell them apart. Your job: "
    "write ONE single concrete question that a PATIENT (not a doctor) can answer about their own body "
    "or symptoms -- a plain yes/no question or a short-phrase question. The question must be answerable "
    "from the patient's own experience/observation only, in everyday language. The question MUST probe "
    "the SPECIFIC distinguishing feature named in the clinical note below -- never a generic symptom the "
    "two diseases share (if both diseases cause the same symptom, asking about it will not discriminate "
    "between them, so do not ask about it). NEVER ask about exam findings only a doctor can detect with "
    "a stethoscope, reflex hammer, or hands-on exam (e.g. a heart murmur, an abnormal reflex, a feel of "
    "the pulse at a specific point, a sound only audible with a stethoscope) -- patients cannot hear "
    "their own heart murmurs or feel their own reflexes, so never phrase a question as if they can. NEVER "
    "ask about any test, scan, lab value, imaging, or biopsy result. NEVER invent a symptom not grounded "
    "in the text given. Also give the expected patient answer to this question if they truly have disease "
    "A, and the expected answer if they truly have disease B -- these must be clearly different from each "
    "other and must follow directly from the distinguishing clinical note given.\n"
    'Respond ONLY as compact JSON: {"question": "...", "expected_answer_if_a": "...", '
    '"expected_answer_if_b": "..."}'
)


def generate_question(disease_a_id, disease_a_ctx, disease_b_id, disease_b_ctx, distinguishing_text,
                       retry_feedback=None):
    user = (
        f"Disease A: {disease_a_id}\n{disease_a_ctx}\n\n"
        f"Disease B: {disease_b_id}\n{disease_b_ctx}\n\n"
        f"Real clinical distinguishing note (how to tell A and B apart): {distinguishing_text}\n\n"
        "Write the one patient-answerable discriminating question now."
    )
    if retry_feedback:
        user += (
            f"\n\nYour previous attempt was rejected: {retry_feedback}. Fix this specific problem and "
            "write a new question, still grounded only in the distinguishing note above."
        )
    return ollama_chat_json(QUESTION_SYSTEM_PROMPT, user)


def main():
    kb = load_kb()
    diseases = kb["diseases"]
    records = json.load(open(DIFF_DX_DATA))
    valid_pairs = [
        r for r in records
        if r.get("disease_id") and r.get("confusable_id")
        and r["disease_id"] != r["confusable_id"]
        # A handful of differential_diagnosis_dataset.json entries have
        # confusable_id == disease_id -- real KB cases where the "confusable"
        # entity (confusable_name_raw) is a variant/subtype not itself one of
        # the 323 diseases (e.g. "partially treated bacterial meningitis"),
        # so entity-linking fell back to the same id. These can't form a real
        # two-different-diseases discriminating pair (the same disease can't
        # appear twice in a shortlist), so they're excluded here.
    ]
    print(f"Found {len(valid_pairs)} valid KB-authored cross-disease pairs to process "
          f"(excluding same-disease-id variant entries).")

    out = []
    n_ok, n_rejected, n_failed = 0, 0, 0
    t0 = time.time()
    for i, r in enumerate(valid_pairs):
        a_id, b_id = r["disease_id"], r["confusable_id"]
        distinguishing_text = r["distinguishing_text"]
        dz_a = diseases.get(a_id)
        dz_b = diseases.get(b_id)
        if not dz_a or not dz_b:
            n_failed += 1
            continue
        ctx_a = build_context_block(a_id, dz_a)
        ctx_b = build_context_block(b_id, dz_b)

        record = {
            "disease_a": a_id,
            "disease_b": b_id,
            "source": f"KB differential reasoning for {a_id} vs {b_id}",
            "distinguishing_text": distinguishing_text,
        }
        retry_feedback = None
        attempt_error = None
        for attempt in range(2):  # one real attempt + one grounded retry on validation failure
            try:
                result = generate_question(a_id, ctx_a, b_id, ctx_b, distinguishing_text, retry_feedback)
                question = (result.get("question") or "").strip()
                ans_a = (result.get("expected_answer_if_a") or "").strip()
                ans_b = (result.get("expected_answer_if_b") or "").strip()
                attempt_error = None
                if not question or not ans_a or not ans_b:
                    attempt_error = "missing field(s) in model output"
                elif is_exam_only(question):
                    attempt_error = "question references an exam/lab/imaging-only finding a patient cannot self-report"
                elif ans_a.strip().lower() == ans_b.strip().lower():
                    attempt_error = "expected answers were identical for both diseases (not discriminating)"
                if attempt_error is None:
                    record["question"] = question
                    record["expected_answer_if_a"] = ans_a
                    record["expected_answer_if_b"] = ans_b
                    record["validated"] = True
                    n_ok += 1
                    break
                record["question"] = question
                retry_feedback = attempt_error
            except Exception as e:
                attempt_error = f"generation error: {e}"
                retry_feedback = attempt_error

        if attempt_error is not None:
            record["validated"] = False
            record["reject_reason"] = attempt_error
            if attempt_error.startswith("generation error"):
                n_failed += 1
            else:
                n_rejected += 1

        out.append(record)
        if (i + 1) % 10 == 0:
            print(f"  ...{i+1}/{len(valid_pairs)} done ({time.time()-t0:.0f}s elapsed), "
                  f"ok={n_ok} rejected={n_rejected} failed={n_failed}")

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"\nDone in {time.time()-t0:.0f}s.")
    print(f"Total pairs: {len(valid_pairs)}  validated_ok: {n_ok}  rejected: {n_rejected}  failed: {n_failed}")
    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
