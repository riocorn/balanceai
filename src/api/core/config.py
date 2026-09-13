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
    CNN_MODEL_PATH: str = str(BASE_DIR / "models" / "best_efficientnet_b3.pt")
    PREDICTOR_MODEL_PATH: str = str(BASE_DIR / "models" / "best_predictor.pt")

    DATA_DIR: str = str(BASE_DIR / "data")
    ICMR_RDA_PATH: str = str(BASE_DIR / "data" / "icmr" / "icmr_rda_clean.json")
    USDA_PATH: str = str(BASE_DIR / "data" / "usda" / "indian_foods_usda.json")
    STATE_DIET_PATH: str = str(BASE_DIR / "data" / "state_diets" / "state_diet_database.json")
    DEFICIENCY_MAP_PATH: str = str(BASE_DIR / "data" / "state_diets" / "deficiency_symptom_mapping.json")

    JWT_SECRET: str = "balanceai-dev-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]

    class Config:
        env_file = ".env"

settings = Settings()
