import os

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@db:5432/virtual_trader"
BACKEND_URL = os.getenv("BACKEND_URL") or "http://backend:8000"
