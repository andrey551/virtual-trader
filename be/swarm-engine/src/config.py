import os
from dotenv import load_dotenv

# Load env variables if present
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Automatically target the virtual_trader.db in backend-core folder
DEFAULT_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "backend-core", "virtual_trader.db")).replace("\\", "/")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
