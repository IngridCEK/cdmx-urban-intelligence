"""Configuracion central. Todo se lee de variables de entorno (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

DB_USER = os.getenv("DB_USER", "dw_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "dw_pass")
DB_NAME = os.getenv("DB_NAME", "urban_dw")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Area de estudio (claves INEGI)
STUDY_ENT = os.getenv("STUDY_ENT", "09")   # 09 = Ciudad de Mexico
STUDY_MUN = os.getenv("STUDY_MUN", "")      # vacio = todas las alcaldias
WORK_CRS = os.getenv("WORK_CRS", "EPSG:32614")  # CRS proyectado para areas/distancias

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
