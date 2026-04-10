"""
Application configuration.
Centralized settings for database, file paths, and runtime options.
"""

import os
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────
# Root of the backend package
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Root of the entire project (one level above backend/)
PROJECT_ROOT = BACKEND_DIR.parent

# Database
DB_PATH = PROJECT_ROOT / "master_data_v2.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ML model files
ML_MODEL_DIR = str(PROJECT_ROOT / "models")

# Temporary uploaded files
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Schedule log for ML training
SCHEDULE_LOG_PATH = PROJECT_ROOT / "schedule_log.csv"

# ─── Server ──────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 8000
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ─── GA-VNS Defaults ────────────────────────────────────────────────
GA_POP_SIZE = 50
GA_MAX_GEN = 50
GA_TIGHTNESS_FACTOR = 1.5

# ─── CORS ────────────────────────────────────────────────────────────
CORS_ORIGINS = [
    "http://localhost:3000",    # Vite dev server
    "http://localhost:5173",    # Vite default
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "app://*",                  # Electron
]
