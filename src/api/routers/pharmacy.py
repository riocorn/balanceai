from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[1]))

from services.pharmacy_service import (
    match_disease_with_ai,
    get_medicine_payload,
    build_whatsapp_link,
)

router = APIRouter(prefix="/pharmacy", tags=["Pharmacy"])


class MatchRequest(BaseModel):
    text: str


class WhatsappLinkRequest(BaseModel):
    disease_id: str
    disease_name: str
    medicine_names: List[str] = []
    patient_text: Optional[str] = ""


@router.post("/match")
async def match_symptoms(req: MatchRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Please describe your problem.")
    result = match_disease_with_ai(req.text.strip())
    return result


@router.get("/medicine/{disease_id}")
async def medicine_detail(disease_id: str):
    payload = get_medicine_payload(disease_id)
    if not payload.get("found"):
        raise HTTPException(status_code=404, detail="Disease not found in knowledge base.")
    return payload


@router.post("/whatsapp-link")
async def whatsapp_link(req: WhatsappLinkRequest):
    link = build_whatsapp_link(req.disease_name, req.medicine_names, req.patient_text or "")
    return {"link": link}
