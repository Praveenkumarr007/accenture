"""Core configuration for BusinessIntelligence.AI"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./bi_intelligence.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 1024
    DEMO_MODE: bool = True
    CORS_ORIGINS: str = '["*"]'
    LOG_LEVEL: str = "INFO"
    ENABLE_LLM: bool = False
    LLM_CACHE_TTL: int = 3600

    @property
    def cors_origins_list(self):
        import json
        return json.loads(self.CORS_ORIGINS)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
