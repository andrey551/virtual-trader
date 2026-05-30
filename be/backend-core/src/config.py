import os
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Explicitly point to the unified be/.env file
ENV_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", ".env"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "Virtual Trader Backend Core"
    API_V1_STR: str = "/api"
    
    # Database connection URL - Default fallback to local SQLite for easy development/testing
    DATABASE_URL: str = "sqlite:///./virtual_trader.db"
    
    # Gemini API Key for semantic embeddings and swarm agent calls
    GEMINI_API_KEY: Optional[str] = None
    
    # CORS Origins allowed to hit the API
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Use Docker to run Playwright MCP crawler in container environment
    MCP_USE_DOCKER: bool = False
    
    class Config:
        env_file = ENV_PATH
        case_sensitive = True

settings = Settings()
