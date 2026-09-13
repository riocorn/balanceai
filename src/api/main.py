from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time, sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "models"))
sys.path.insert(0, str(Path(__file__).parents[1] / "voice"))

from core.config import settings
from routers.checkin import router as checkin_router
from routers.users import router as users_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered micronutrient deficiency detection from symptoms, camera, and voice — no blood tests needed",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(round(time.time() - start, 3))
    return response


app.include_router(checkin_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "endpoints": {
            "text_checkin": "POST /checkin/text",
            "voice_checkin": "POST /checkin/voice",
            "camera_nail": "POST /checkin/camera/nail",
            "camera_tongue": "POST /checkin/camera/tongue",
            "camera_eye": "POST /checkin/camera/eye",
            "full_checkin": "POST /checkin/full",
            "predict_only": "POST /checkin/predict-only",
            "user_history": "GET /users/{id}/history",
            "balance_trend": "GET /users/{id}/trend",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok", "model_cache_size": "see /docs"}


@app.get("/knowledge/deficiencies")
def list_deficiencies():
    from services.ml_service import get_knowledge_base, DEFICIENCIES
    kb = get_knowledge_base()
    return {
        "deficiencies": DEFICIENCIES,
        "count": len(DEFICIENCIES),
        "deficiency_detail": kb.get("deficiency_map", {}),
    }


@app.get("/knowledge/state/{state_name}")
def get_state_diet(state_name: str):
    from services.ml_service import get_knowledge_base
    kb = get_knowledge_base()
    state_db = kb.get("state_diet", {})
    if state_name not in state_db:
        available = list(state_db.keys())
        return JSONResponse(status_code=404, content={"error": f"State not found. Available: {available}"})
    return state_db[state_name]


@app.get("/knowledge/rda")
def get_rda():
    from services.ml_service import get_knowledge_base
    kb = get_knowledge_base()
    return kb.get("rda", {})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
