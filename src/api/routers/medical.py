"""
routers/medical.py

Medical-standard API endpoint wiring together:
  - services/medical_understanding.py (Part 1) -- patient free text -> disease_id,
    including the real clarifying-question flow for symptom-style input.
  - services/medicine_lookup.py       (Part 2) -- disease_id -> real, KB-ordered medicines
  - services/pharmacy_service.py      -- real WhatsApp doctor-contact link builder,
    reused here (not re-implemented) for every doctor-fallback case.

This router does NOT re-implement any matching, ranking, or question-generation
logic itself. It only calls the services above and shapes the combined result
into documented Pydantic responses.

Founder directive, 2026-09-28 (and same-day refinements): this product is a
disease-NAME lookup AI, not a free-text symptom checker.
  1. A direct, specific disease name (fast alias/fuzzy match, no LLM) is
     answered immediately, exactly as before.
  2. Text that reads as a real symptom description is never diagnosed by an
     LLM guessing from the raw sentence. Instead the patient is asked a
     small, real, KB-grounded set of clarifying questions (2-4) to narrow a
     real candidate shortlist, and only resolved once that Q&A gives enough
     signal -- this is a two-turn flow (`need_more_info` -> re-POST with
     `qa_history` filled in).
  3. Gibberish/off-topic input, or a clarifying round that still doesn't
     resolve, falls back to a real WhatsApp doctor-contact link -- never a
     guessed disease. No diagnostic test is ever mentioned or suggested
     anywhere in this flow.
hard_emergency_flag/possible_emergency are computed independently of all of
the above (see medical_understanding._hard_emergency_scan) and are always
returned, on every turn, regardless of which path is taken.
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.config import settings
from services.medical_understanding import (
    identify_disease,
    generate_clarifying_questions,
    resolve_clarified_disease,
    get_disease_meta,
    hard_emergency_scan,
)
from services.medicine_lookup import get_ranked_medicines
from services.pharmacy_service import build_whatsapp_link

logger = logging.getLogger("medical_router")

router = APIRouter(prefix="/medical", tags=["Medical"])

DISCLAIMER = (
    "Yeh AI-assisted information hai, jo ek real medical knowledge base se li gayi hai -- "
    "yeh koi diagnosis nahi hai. Koi bhi dawai lene se pehle ek doctor se zaroor confirm karein. "
    "(This is AI-assisted information from a real medical knowledge base, not a diagnosis -- "
    "a doctor must confirm before taking any medicine.)"
)

NOT_A_DISEASE_NAME_MESSAGE = (
    "Humein aapke input se koi specific bimari confidently pehchaan nahi aayi. Kripya neeche diye "
    "WhatsApp link se seedhe ek doctor se baat karein. "
    "(We couldn't confidently recognize a specific condition from what you entered. Please use the "
    "WhatsApp link below to talk to a doctor directly.)"
)


_disease_master_cache: Optional[dict] = None


def _load_disease_master() -> dict:
    global _disease_master_cache
    if _disease_master_cache is None:
        with open(settings.DISEASE_MASTER_PATH, "r", encoding="utf-8") as f:
            _disease_master_cache = json.load(f)["diseases"]
    return _disease_master_cache


def _disease_name(disease_id: str) -> str:
    diseases = _load_disease_master()
    d = diseases.get(disease_id) or {}
    return d.get("name") or disease_id


def _normalize_emergency_rule(rule) -> Optional[str]:
    """disease_master.json stores EMERGENCY_OVERRIDE_RULE as a plain string for
    most diseases, but as a dict (e.g. {"rule": "...", "confidence": "high"})
    for some (verified: 38/261 diseases with this field, e.g. pneumonia,
    tuberculosis, malaria, dengue_fever). Show the real rule text as-is either
    way -- never generate or alter it."""
    if rule is None:
        return None
    if isinstance(rule, str):
        return rule
    if isinstance(rule, dict):
        text = rule.get("rule")
        if isinstance(text, str) and text.strip():
            return text
        return json.dumps(rule, ensure_ascii=False)
    return str(rule)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class QAPair(BaseModel):
    question: str
    answer: str


class MedicalQueryRequest(BaseModel):
    text: str = Field(..., description="Patient's free-text complaint, in any language.")
    qa_history: List[QAPair] = Field(
        default_factory=list,
        description=(
            "Answers to a previous need_more_info response's clarifying_questions, in the same order. "
            "Leave empty on the first call for a given `text`."
        ),
    )
    candidate_ids: List[str] = Field(
        default_factory=list,
        description="Echo back exactly the candidate_ids from the prior need_more_info response.",
    )
    translated_text: Optional[str] = Field(
        None, description="Echo back exactly the translated_text from the prior need_more_info response.",
    )


class DiseaseOut(BaseModel):
    id: str
    name: str


class MedicineOut(BaseModel):
    name: str
    effectiveness_pct: Optional[float] = None
    is_curative: bool
    simple_explanation: str
    sources: List[str] = []


class MedicalQueryResponse(BaseModel):
    matched: bool = Field(..., description="True if a confident disease match was found.")
    disease: Optional[DiseaseOut] = None
    understood_as: Optional[str] = None
    confidence: float = 0.0
    medicines: List[MedicineOut] = []
    doctor_verification_required: bool = True
    disclaimer: str = DISCLAIMER
    hard_emergency_flag: bool = False
    possible_emergency: bool = False
    emergency_override_rule: Optional[str] = None
    diagnostic_reasoning: Optional[str] = Field(
        None,
        description=(
            "The LLM's real candidate-by-candidate differential-diagnosis reasoning behind this match "
            "(id: fits/doesn't fit -- why, for each candidate considered), surfaced for patient trust. "
            "Only present on a resolved match from the clarifying-Q&A flow; None when missing/unparseable "
            "or when this turn didn't resolve to a final disease -- never a placeholder or guessed text."
        ),
    )
    message: Optional[str] = Field(
        None, description="Present when no confident disease match was found."
    )
    need_more_info: bool = Field(
        False, description="True when the patient should be asked clarifying_questions before this resolves."
    )
    clarifying_questions: List[str] = Field(
        default_factory=list,
        description="2-4 real, KB-grounded clarifying questions. Only present when need_more_info is true.",
    )
    candidate_ids: List[str] = Field(
        default_factory=list,
        description="Echo this back verbatim in the next call's candidate_ids field.",
    )
    translated_text: Optional[str] = Field(
        None, description="Echo this back verbatim in the next call's translated_text field.",
    )
    redirect_to_whatsapp: bool = Field(
        False,
        description=(
            "True when the patient's text was not a direct, specific disease name and could not be "
            "resolved via clarifying questions either -- whatsapp_link should be shown to the patient."
        ),
    )
    whatsapp_link: Optional[str] = Field(
        None, description="Real wa.me doctor-contact link. Present whenever redirect_to_whatsapp is true."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _whatsapp_fallback(
    text: str,
    message: str,
    hard_emergency_flag: bool,
    possible_emergency: bool,
    understood_as: Optional[str] = None,
) -> MedicalQueryResponse:
    try:
        link = build_whatsapp_link("", [], text)
    except Exception:
        logger.exception("build_whatsapp_link failed")
        link = None
    return MedicalQueryResponse(
        matched=False,
        disease=None,
        understood_as=understood_as,
        confidence=0.0,
        medicines=[],
        doctor_verification_required=True,
        disclaimer=DISCLAIMER,
        hard_emergency_flag=hard_emergency_flag,
        possible_emergency=possible_emergency,
        emergency_override_rule=None,
        message=message,
        need_more_info=False,
        clarifying_questions=[],
        candidate_ids=[],
        translated_text=None,
        redirect_to_whatsapp=True,
        whatsapp_link=link,
    )


def _matched_response(disease_id: str, understanding: dict) -> MedicalQueryResponse:
    hard_emergency_flag = bool(understanding.get("hard_emergency_flag", False))
    possible_emergency = bool(understanding.get("possible_emergency", False))
    understood_as = understanding.get("understood_as")
    confidence = float(understanding.get("confidence") or 0.0)

    try:
        medicines = get_ranked_medicines(disease_id)
    except Exception:
        logger.exception("get_ranked_medicines failed")
        raise HTTPException(
            status_code=503,
            detail="Medicine lookup service is currently unavailable. Please try again shortly.",
        )

    return MedicalQueryResponse(
        matched=True,
        disease=DiseaseOut(id=disease_id, name=_disease_name(disease_id)),
        understood_as=understood_as,
        confidence=confidence,
        medicines=[MedicineOut(**m) for m in medicines],
        doctor_verification_required=True,
        disclaimer=DISCLAIMER,
        hard_emergency_flag=hard_emergency_flag,
        possible_emergency=possible_emergency,
        emergency_override_rule=_normalize_emergency_rule(understanding.get("emergency_override_rule")),
        diagnostic_reasoning=understanding.get("differential_reasoning"),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/query", response_model=MedicalQueryResponse)
def medical_query(payload: MedicalQueryRequest) -> MedicalQueryResponse:
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must not be empty.")

    # Hard, deterministic emergency scan: independent of every branch below,
    # never skipped, never suppressed -- runs on the raw text on every turn.
    raw_hard_emergency = hard_emergency_scan(text)

    # -----------------------------------------------------------------
    # Turn 2+: the patient already answered a prior need_more_info round.
    # -----------------------------------------------------------------
    if payload.qa_history:
        if not payload.candidate_ids or not payload.translated_text:
            raise HTTPException(
                status_code=400,
                detail="candidate_ids and translated_text must be echoed back from the prior need_more_info response.",
            )
        try:
            qa_pairs = [(qa.question, qa.answer) for qa in payload.qa_history]
            resolved = resolve_clarified_disease(text, payload.translated_text, payload.candidate_ids, qa_pairs)
        except Exception:
            logger.exception("resolve_clarified_disease failed")
            resolved = {"mode": "no_match"}

        if resolved.get("mode") == "matched" and resolved.get("disease_id"):
            resolved["hard_emergency_flag"] = bool(resolved.get("hard_emergency_flag")) or raw_hard_emergency
            resolved["possible_emergency"] = bool(resolved.get("possible_emergency")) or raw_hard_emergency
            return _matched_response(resolved["disease_id"], resolved)

        # Still genuinely ambiguous after real Q&A -- final fallback is a
        # real doctor over WhatsApp, never a guessed disease.
        return _whatsapp_fallback(
            text, NOT_A_DISEASE_NAME_MESSAGE, raw_hard_emergency, raw_hard_emergency, understood_as=text,
        )

    # -----------------------------------------------------------------
    # Turn 1
    # -----------------------------------------------------------------
    try:
        understanding = identify_disease(text)
    except Exception:
        logger.exception("identify_disease failed")
        raise HTTPException(
            status_code=503,
            detail="Medical understanding service is currently unavailable. Please try again shortly.",
        )

    mode = understanding.get("mode")
    hard_emergency_flag = bool(understanding.get("hard_emergency_flag", False)) or raw_hard_emergency
    possible_emergency = bool(understanding.get("possible_emergency", False)) or raw_hard_emergency

    if mode == "matched":
        understanding["hard_emergency_flag"] = hard_emergency_flag
        understanding["possible_emergency"] = possible_emergency
        return _matched_response(understanding["disease_id"], understanding)

    if mode == "no_match":
        return _whatsapp_fallback(
            text, NOT_A_DISEASE_NAME_MESSAGE, hard_emergency_flag, possible_emergency,
            understood_as=understanding.get("understood_as"),
        )

    # mode == "clarify": real symptom-style text with a real candidate
    # shortlist -- generate real, KB-grounded clarifying questions (or a real
    # needs-test signal) before resolving anything.
    translated = understanding["translated"]
    candidates = understanding["candidates"]
    try:
        disease_meta = get_disease_meta()
        clarify = generate_clarifying_questions(text, translated, candidates, disease_meta)
    except Exception:
        logger.exception("generate_clarifying_questions failed")
        clarify = {"questions": []}

    questions = clarify.get("questions") or []
    if len(questions) < 2:
        # Not enough real distinguishing signal to ask a safe clarifying
        # question set -- fall back to the doctor rather than guessing.
        return _whatsapp_fallback(
            text, NOT_A_DISEASE_NAME_MESSAGE, hard_emergency_flag, possible_emergency,
            understood_as=understanding.get("understood_as"),
        )

    return MedicalQueryResponse(
        matched=False,
        disease=None,
        understood_as=understanding.get("understood_as"),
        confidence=0.0,
        medicines=[],
        doctor_verification_required=True,
        disclaimer=DISCLAIMER,
        hard_emergency_flag=hard_emergency_flag,
        possible_emergency=possible_emergency,
        emergency_override_rule=None,
        message=None,
        need_more_info=True,
        clarifying_questions=questions,
        candidate_ids=[did for did, _score in candidates],
        translated_text=translated,
        redirect_to_whatsapp=False,
        whatsapp_link=None,
    )
