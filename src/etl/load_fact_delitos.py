"""Carga fact_delitos desde la salida procesada del ETL de delitos."""

import geopandas as gpd
import pandas as pd
from sqlalchemy import text

from src.config import PROCESSED_DIR
from src.db import get_engine

GPKG = PROCESSED_DIR / "delitos_2023_ageb.gpkg"
LAYER = "delitos"


def nullable(value):
    return None if pd.isna(value) else value


def run():
    if not GPKG.exists():
        raise FileNotFoundError(f"No existe {GPKG}. Ejecuta primero src.etl.crime.")

    print("Leyendo delitos...")
    gdf = gpd.read_file(GPKG, layer=LAYER).to_crs("EPSG:32614")
    print(f"Registros leidos: {len(gdf)}")

    rows = []
    for row in gdf.itertuples(index=False):
        fecha_hecho = nullable(row.fecha_hecho)
        hora = nullable(row.hora)
        geom = row.geometry
        rows.append(
            {
                "source_id": str(row._id),
                "fecha_inicio": nullable(row.fecha_inicio),
                "fecha_hecho": fecha_hecho,
                "hora_hecho": nullable(row.hora_hecho),
                "hora": None if hora is None else int(hora),
                "fecha_key": None if fecha_hecho is None else int(pd.Timestamp(fecha_hecho).strftime("%Y%m%d")),
                "hora_key": None if hora is None else int(hora),
                "categoria_delito": nullable(row.categoria_delito),
                "delito": nullable(row.delito),
                "cvegeo": None if pd.isna(row.CVEGEO) else str(row.CVEGEO),
                "alcaldia_catalogo": nullable(row.alcaldia_catalogo),
                "alcaldia_geo": nullable(row.alcaldia_geo),
                "latitud": nullable(row.latitud),
                "longitud": nullable(row.longitud),
                "estatus_asignacion": str(row.estatus_asignacion),
                "geometry_wkt": None if geom is None or geom.is_empty else geom.wkt,
            }
        )

    sql = text("""
        INSERT INTO dw.fact_delitos (
            source_id, fecha_inicio, fecha_hecho, hora_hecho, hora,
            fecha_key, hora_key, delito_key, CVEGEO, delito, categoria_delito,
            alcaldia_catalogo, alcaldia_geo, latitud, longitud,
            estatus_asignacion, geometry, incident_count
        )
        SELECT
            :source_id, :fecha_inicio, :fecha_hecho, :hora_hecho, :hora,
            :fecha_key, :hora_key, d.delito_key, :cvegeo, :delito,
            :categoria_delito, :alcaldia_catalogo, :alcaldia_geo,
            :latitud, :longitud, :estatus_asignacion,
            CASE WHEN :geometry_wkt IS NULL THEN NULL
                 ELSE ST_GeomFromText(:geometry_wkt, 32614) END,
            1
        FROM (SELECT 1) AS seed
        LEFT JOIN dw.dim_delito d
          ON d.categoria_delito IS NOT DISTINCT FROM :categoria_delito
         AND d.delito IS NOT DISTINCT FROM :delito
        ON CONFLICT (source_id) DO UPDATE SET
            fecha_inicio = EXCLUDED.fecha_inicio,
            fecha_hecho = EXCLUDED.fecha_hecho,
            hora_hecho = EXCLUDED.hora_hecho,
            hora = EXCLUDED.hora,
            fecha_key = EXCLUDED.fecha_key,
            hora_key = EXCLUDED.hora_key,
            delito_key = EXCLUDED.delito_key,
            CVEGEO = EXCLUDED.CVEGEO,
            delito = EXCLUDED.delito,
            categoria_delito = EXCLUDED.categoria_delito,
            alcaldia_catalogo = EXCLUDED.alcaldia_catalogo,
            alcaldia_geo = EXCLUDED.alcaldia_geo,
            latitud = EXCLUDED.latitud,
            longitud = EXCLUDED.longitud,
            estatus_asignacion = EXCLUDED.estatus_asignacion,
            geometry = EXCLUDED.geometry
    """)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(sql, rows)
        total = conn.execute(text("SELECT COUNT(*) FROM dw.fact_delitos")).scalar()

    print(f"Registros en fact_delitos: {total}")
    print("Carga de fact_delitos completada.")


if __name__ == "__main__":
    run()
