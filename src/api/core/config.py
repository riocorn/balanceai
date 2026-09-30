from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    APP_NAME: str = "BalanceAI"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://balanceai:balanceai123@localhost:5432/balanceai"
    REDIS_URL: str = "redis://localhost:6379/0"

    WHISPER_MODEL_SIZE: str = "small"
    # Real trained checkpoints — one MobileNetV3 model per modality (see src/models/train_cnn.py).
    # No "eye" entry: no eye model was ever trained (train_cnn.py only trains nail/tongue/skin),
    # so eye stays explicitly unavailable rather than silently using a wrong/untrained model.
    MODALITY_MODEL_PATHS: dict = {
        "nail":   str(BASE_DIR / "models" / "best_nail_model.pt"),
        "tongue": str(BASE_DIR / "models" / "best_tongue_model.pt"),
        "skin":   str(BASE_DIR / "models" / "best_skin_model.pt"),
    }
    PREDICTOR_MODEL_PATH: str = str(BASE_DIR / "models" / "best_predictor.pt")

    DATA_DIR: str = str(BASE_DIR / "data")
    ICMR_RDA_PATH: str = str(BASE_DIR / "data" / "icmr" / "icmr_rda_clean.json")
    USDA_PATH: str = str(BASE_DIR / "data" / "usda" / "indian_foods_usda.json")
    STATE_DIET_PATH: str = str(BASE_DIR / "data" / "state_diets" / "state_diet_database.json")
    DEFICIENCY_MAP_PATH: str = str(BASE_DIR / "data" / "state_diets" / "deficiency_symptom_mapping.json")
    DISEASE_MASTER_PATH: str = str(BASE_DIR / "data" / "disease_master.json")

    # Pharmacy module — free-text symptom -> disease -> medicine matching.
    # Self-hosted only: a local multilingual sentence-embedding model shortlists
    # candidate diseases, then a local Ollama LLM (no external API, no per-call
    # cost) picks the best one from that shortlist and writes the explanation.
    # No external LLM API is called for this feature — see pharmacy_service.py.
    # Real, measured: base multilingual MiniLM scored only 34.9% top-15 retrieval
    # recall (102/292) on the held-out symptom eval; the KB-domain fine-tuned
    # checkpoint below (same base model, further trained on real disease-symptom
    # pairs) scored 77.1% (225/292) -- best of the checkpoints compared, see
    # ml_training/eval_symptom_embeddings.py and the eval_top15 harness.
    EMBEDDING_MODEL: str = str(BASE_DIR / "models" / "symptom_embedding_finetuned_v7_combined")
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "hf.co/bartowski/HuatuoGPT-o1-8B-GGUF:Q5_K_M"
    # Used only for the grounded disease-id/medicine SELECTION calls (never free-form
    # generation -- the model picks from a real KB-derived shortlist or is rejected).
    # Kept separate from OLLAMA_MODEL (used for translation/rephrasing of already-real
    # facts) so the two can be sized independently, mirroring the existing
    # OLLAMA_MODEL/RERANK_MODEL split in medical_understanding.py.
    OLLAMA_REASONING_MODEL: str = "hf.co/bartowski/HuatuoGPT-o1-8B-GGUF:Q5_K_M"
    # WhatsApp number the "Verify with Doctor" button deep-links to (E.164, no "+").
    # Placeholder until a real doctor/clinic WhatsApp Business number is provided.
    DOCTOR_WHATSAPP_NUMBER: str = ""

    JWT_SECRET: str = "balanceai-dev-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]

    class Config:
        env_file = ".env"

settings = Settings()
