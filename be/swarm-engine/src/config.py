import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Explicitly point to the unified be/.env file
ENV_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", ".env"))
load_dotenv(ENV_PATH)

# Automatically target the virtual_trader.db in backend-core folder
DEFAULT_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "backend-core", "virtual_trader.db")).replace("\\", "/")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Configurable Gemini models with fallback defaults
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")
