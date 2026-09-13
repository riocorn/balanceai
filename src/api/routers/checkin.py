from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[1]))

from services.ml_service import process_full_checkin, analyze_image, run_deficiency_prediction, compute_balance_score, get_food_recommendations

router = APIRouter(prefix="/checkin", tags=["Check-In"])


class TextCheckinRequest(BaseModel):
    user_id: Optional[int] = None
    voice_text: str
    state: Optional[str] = None
    is_vegetarian: bool = False
    history: Optional[List[dict]] = None


class PredictRequest(BaseModel):
    symptoms: List[str]
    diet: dict
    visual_signs: List[str] = []
    state: Optional[str] = None
    is_vegetarian: bool = False


@router.post("/text")
async def checkin_text(req: TextCheckinRequest):
    result = process_full_checkin(
        voice_text=req.voice_text,
        user_state=req.state,
        is_vegetarian=req.is_vegetarian,
        history=req.history,
    )
    return JSONResponse(content=result)


@router.post("/voice")
async def checkin_voice(
    audio: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    state: Optional[str] = Form(None),
    is_vegetarian: bool = Form(False),
):
    if not audio.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".webm")):
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    audio_bytes = await audio.read()
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file too large (max 25MB)")

    result = process_full_checkin(
        audio_bytes=audio_bytes,
        user_state=state,
        is_vegetarian=is_vegetarian,
    )
    return JSONResponse(content=result)


@router.post("/camera/{modality}")
async def checkin_camera(
    modality: str,
    image: UploadFile = File(...),
):
    if modality not in ["nail", "tongue", "eye", "skin"]:
        raise HTTPException(status_code=400, detail="Modality must be: nail, tongue, eye, skin")

    content_type = image.content_type or ""
    if not any(t in content_type for t in ["jpeg", "jpg", "png", "webp"]):
        raise HTTPException(status_code=400, detail="Image must be JPEG, PNG or WebP")

    img_bytes = await image.read()
    if len(img_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    result = analyze_image(img_bytes, modality)
    return JSONResponse(content=result)


@router.post("/full")
async def checkin_full(
    voice_text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    nail_image: Optional[UploadFile] = File(None),
    tongue_image: Optional[UploadFile] = File(None),
    eye_image: Optional[UploadFile] = File(None),
    state: Optional[str] = Form(None),
    is_vegetarian: bool = Form(False),
    user_id: Optional[int] = Form(None),
):
    audio_bytes = await audio.read() if audio else None
    nail_bytes = await nail_image.read() if nail_image else None
    tongue_bytes = await tongue_image.read() if tongue_image else None
    eye_bytes = await eye_image.read() if eye_image else None

    result = process_full_checkin(
        voice_text=voice_text,
        audio_bytes=audio_bytes,
        nail_image=nail_bytes,
        tongue_image=tongue_bytes,
        eye_image=eye_bytes,
        user_state=state,
        is_vegetarian=is_vegetarian,
    )
    return JSONResponse(content=result)


@router.post("/predict-only")
async def predict_only(req: PredictRequest):
    predictions = run_deficiency_prediction(req.symptoms, req.diet, req.visual_signs)
    balance = compute_balance_score(predictions)
    recommendations = get_food_recommendations(
        balance["high_risk_deficiencies"],
        balance["medium_risk_deficiencies"],
        state=req.state,
        is_vegetarian=req.is_vegetarian,
    )
    return JSONResponse(content={
        "deficiency_predictions": predictions[:10],
        "balance_score": balance,
        "recommendations": recommendations,
    })
