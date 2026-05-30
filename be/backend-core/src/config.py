from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Virtual Trader Backend Core"
    API_V1_STR: str = "/api"
    
    # Database connection URL - Default fallback to local SQLite for easy development/testing
    DATABASE_URL: str = "sqlite:///./virtual_trader.db"
    
    # Gemini API Key for semantic embeddings and swarm agent calls
    GEMINI_API_KEY: Optional[str] = None
    
    # CORS Origins allowed to hit the API
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
