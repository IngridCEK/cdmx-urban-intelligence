"""Carga las dimensiones de actividad economica y tamano desde DENUE 05/2026."""

import geopandas as gpd
import pandas as pd
from sqlalchemy import text

from src.config import PROCESSED_DIR
from src.db import get_engine

GPKG = PROCESSED_DIR / "denue_2026_ageb.gpkg"
LAYER = "establecimientos"

# Orden oficial documentado en docs/tamano_per_ocu.md.
TAMANOS = {
    "0 a 5 personas": 1,
    "6 a 10 personas": 2,
    "11 a 30 personas": 3,
    "31 a 50 personas": 4,
    "51 a 100 personas": 5,
    "101 a 250 personas": 6,
    "251 y más personas": 7,
}


def run():
    if not GPKG.exists():
        raise FileNotFoundError(f"No existe {GPKG}. Ejecuta primero src.etl.denue.")

    print("Leyendo DENUE 05/2026...")
    gdf = gpd.read_file(
        GPKG,
        layer=LAYER,
        columns=["codigo_act", "nombre_act", "per_ocu", "sector", "grupo_actividad"],
    )

    categorias = set(gdf["per_ocu"].dropna().astype(str).str.strip())
    desconocidas = sorted(categorias - set(TAMANOS))
    if desconocidas:
        raise ValueError(f"Categorias per_ocu no documentadas: {desconocidas}")

    tamano_rows = [
        {
            "key": key,
            "categoria": categoria,
            "descripcion": f"Establecimientos con {categoria}",
        }
        for categoria, key in TAMANOS.items()
    ]

    actividades = (
        gdf[["codigo_act", "nombre_act", "sector", "grupo_actividad"]]
        .dropna(subset=["codigo_act"])
        .copy()
    )
    actividades["codigo_act"] = actividades["codigo_act"].astype(str).str.strip()
    actividades = actividades.drop_duplicates(subset=["codigo_act"])

    actividad_rows = []
    for row in actividades.itertuples(index=False):
        codigo = row.codigo_act
        actividad_rows.append(
            {
                "codigo": codigo,
                "nombre": None if pd.isna(row.nombre_act) else str(row.nombre_act),
                "sector_scian": codigo[:2],
                "subsector_scian": codigo[:3],
                "sector_economico": None if pd.isna(row.sector) else str(row.sector),
                "clasificacion": None if pd.isna(row.grupo_actividad) else str(row.grupo_actividad),
            }
        )

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO dw.dim_tamano
                    (tamano_key, categoria_tamano, descripcion)
                VALUES (:key, :categoria, :descripcion)
                ON CONFLICT (tamano_key) DO UPDATE SET
                    categoria_tamano = EXCLUDED.categoria_tamano,
                    descripcion = EXCLUDED.descripcion
            """),
            tamano_rows,
        )

        conn.execute(
            text("""
                INSERT INTO dw.dim_actividad_economica
                    (codigo_act, nombre_act, sector_scian, subsector_scian,
                     sector_economico, clasificacion)
                VALUES
                    (:codigo, :nombre, :sector_scian, :subsector_scian,
                     :sector_economico, :clasificacion)
                ON CONFLICT (codigo_act) DO UPDATE SET
                    nombre_act = EXCLUDED.nombre_act,
                    sector_scian = EXCLUDED.sector_scian,
                    subsector_scian = EXCLUDED.subsector_scian,
                    sector_economico = EXCLUDED.sector_economico,
                    clasificacion = EXCLUDED.clasificacion
            """),
            actividad_rows,
        )

        total_tamanos = conn.execute(text("SELECT COUNT(*) FROM dw.dim_tamano")).scalar()
        total_actividades = conn.execute(
            text("SELECT COUNT(*) FROM dw.dim_actividad_economica")
        ).scalar()

    print(f"Registros en dim_tamano: {total_tamanos}")
    print(f"Registros en dim_actividad_economica: {total_actividades}")
    print("Carga de dimensiones DENUE completada.")


if __name__ == "__main__":
    run()
