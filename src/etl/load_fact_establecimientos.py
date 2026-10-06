"""Carga fact_establecimientos desde la salida procesada de DENUE 05/2026."""

import geopandas as gpd
import pandas as pd
from sqlalchemy import text

from src.config import PROCESSED_DIR
from src.db import get_engine

GPKG = PROCESSED_DIR / "denue_2026_ageb.gpkg"
LAYER = "establecimientos"
FECHA_CORTE = "2026-05-01"
FUENTE = "DENUE 05/2026 INEGI"


def _nullable(value):
    return None if pd.isna(value) else value


def run():
    if not GPKG.exists():
        raise FileNotFoundError(f"No existe {GPKG}. Ejecuta primero src.etl.denue.")

    print("Leyendo DENUE 05/2026...")
    gdf = gpd.read_file(GPKG, layer=LAYER).to_crs("EPSG:32614")
    print(f"Registros leidos: {len(gdf)}")

    # fecha_alta viene como periodo (AAAA-MM); PostgreSQL recibe el primer dia del mes.
    fechas = pd.to_datetime(gdf["fecha_alta"], errors="coerce")

    rows = []
    for pos, row in enumerate(gdf.itertuples(index=False)):
        geom = row.geometry
        cvegeo = _nullable(row.CVEGEO)
        if cvegeo is not None:
            cvegeo = str(cvegeo).strip()

        codigo = _nullable(row.codigo_act)
        if codigo is not None:
            codigo = str(codigo).strip()

        per_ocu = _nullable(row.per_ocu)
        if per_ocu is not None:
            per_ocu = str(per_ocu).strip()

        status = _nullable(row.estatus_asignacion)
        if status is None:
            raise ValueError(f"DENUE sin estatus_asignacion para id={row.id}")

        rows.append(
            {
                "establishment_id": str(row.id),
                "cvegeo": cvegeo,
                "codigo_act": codigo,
                "per_ocu": per_ocu,
                "fecha_alta": None if pd.isna(fechas.iloc[pos]) else fechas.iloc[pos].date(),
                "latitud": _nullable(row.latitud),
                "longitud": _nullable(row.longitud),
                "geometry_wkt": None if geom is None or geom.is_empty else geom.wkt,
                "estatus_asignacion": str(status).strip(),
                "fuente": FUENTE,
                "fecha_corte": FECHA_CORTE,
            }
        )

    sql = text("""
        INSERT INTO dw.fact_establecimientos (
            establishment_id, CVEGEO, actividad_key, tamano_key, codigo_act,
            fecha_alta, establecimiento_count, latitud, longitud, geometry,
            estatus_asignacion, fuente, fecha_corte
        )
        SELECT
            :establishment_id,
            :cvegeo,
            a.actividad_key,
            t.tamano_key,
            :codigo_act,
            :fecha_alta,
            1,
            :latitud,
            :longitud,
            CASE WHEN :geometry_wkt IS NULL THEN NULL
                 ELSE ST_GeomFromText(:geometry_wkt, 32614) END,
            :estatus_asignacion,
            :fuente,
            :fecha_corte
        FROM (SELECT 1) AS seed
        LEFT JOIN dw.dim_actividad_economica a ON a.codigo_act = :codigo_act
        LEFT JOIN dw.dim_tamano t ON t.categoria_tamano = :per_ocu
        ON CONFLICT (establishment_id) DO UPDATE SET
            CVEGEO = EXCLUDED.CVEGEO,
            actividad_key = EXCLUDED.actividad_key,
            tamano_key = EXCLUDED.tamano_key,
            codigo_act = EXCLUDED.codigo_act,
            fecha_alta = EXCLUDED.fecha_alta,
            latitud = EXCLUDED.latitud,
            longitud = EXCLUDED.longitud,
            geometry = EXCLUDED.geometry,
            estatus_asignacion = EXCLUDED.estatus_asignacion,
            fuente = EXCLUDED.fuente,
            fecha_corte = EXCLUDED.fecha_corte
    """)

    engine = get_engine()
    with engine.begin() as conn:
        # SQLAlchemy ejecuta esta lista como executemany, evitando un round-trip por fila.
        conn.execute(sql, rows)
        total = conn.execute(text("SELECT COUNT(*) FROM dw.fact_establecimientos")).scalar()

    print(f"Registros en fact_establecimientos: {total}")
    print("Carga de fact_establecimientos completada.")


if __name__ == "__main__":
    run()
