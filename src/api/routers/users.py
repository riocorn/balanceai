from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[1]))

from models.db import get_db, User, CheckIn, BalanceScore

router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    state: Optional[str] = None
    is_vegetarian: bool = False
    is_vegan: bool = False
    eats_fish: bool = False
    pregnant: bool = False
    lactating: bool = False


@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.phone == user.phone).first()
    if existing:
        return {"user_id": existing.id, "message": "User already exists"}
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"user_id": db_user.id, "message": "User created"}


@router.get("/{user_id}/history")
def get_user_history(user_id: int, limit: int = 30, db: Session = Depends(get_db)):
    checkins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id)
        .order_by(CheckIn.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": c.id,
            "date": c.created_at.isoformat(),
            "balance_score": c.balance_score,
            "top_deficiencies": c.top_deficiencies,
            "symptoms_detected": c.symptoms_detected,
        }
        for c in checkins
    ]


@router.get("/{user_id}/trend")
def get_balance_trend(user_id: int, days: int = 30, db: Session = Depends(get_db)):
    scores = (
        db.query(BalanceScore)
        .filter(BalanceScore.user_id == user_id)
        .order_by(BalanceScore.date.asc())
        .limit(days)
        .all()
    )
    return [
        {
            "date": s.date.isoformat(),
            "score": s.score,
            "high_risk": s.high_risk_deficiencies,
            "improvement": s.improvement_from_last,
        }
        for s in scores
    ]
