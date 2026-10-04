"""Prueba rapida: verifica que la BD responde y que PostGIS esta activo.
Uso:  docker compose exec app python -m src.check_db
"""
from sqlalchemy import text

from src.db import get_engine

with get_engine().connect() as conn:
    print("PostgreSQL:", conn.execute(text("SELECT version()")).scalar())
    print("PostGIS   :", conn.execute(text("SELECT PostGIS_Version()")).scalar())
