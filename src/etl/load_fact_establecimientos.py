import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from src.config import DB_URL

GPKG = "/work/data/processed/denue_2023_ageb.gpkg"

engine = create_engine(DB_URL)

print("Leyendo DENUE...")

gdf = gpd.read_file(GPKG)

print(f"Registros leÃ­dos: {len(gdf)}")

# ---------------------------------------------------------
# Transformar geometrÃ­as al CRS de trabajo
# ---------------------------------------------------------

gdf = gdf.to_crs("EPSG:32614")

print(f"CRS transformado: {gdf.crs}")

# ---------------------------------------------------------
# Preparar columnas
# ---------------------------------------------------------

gdf["establishment_id"] = gdf["id"].astype(str)

print("Columnas preparadas.")

# ---------------------------------------------------------
# SQL de inserciÃ³n
# ---------------------------------------------------------

insert_sql = text("""
    INSERT INTO dw.fact_establecimientos (
        establishment_id,
        cvegeo,
        actividad_key,
        tamano_key,
        codigo_act,
        fecha_alta,
        establecimiento_count,
        latitud,
        longitud,
        geometry,
        estatus_asignacion,
        fuente,
        fecha_corte
    )
    SELECT
        :establishment_id,
        :cvegeo,
        (
            SELECT actividad_key
            FROM dw.dim_actividad_economica
            WHERE codigo_act = :codigo_act
        ),
        (
            SELECT tamano_key
            FROM dw.dim_tamano
            WHERE categoria_tamano = :per_ocu
        ),
        :codigo_act,
        :fecha_alta,
        1,
        :latitud,
        :longitud,
        ST_GeomFromText(:geometry_wkt, 32614),
        :estatus_asignacion,
        'DENUE 2023',
        '2023-11-01'
    ON CONFLICT (establishment_id) DO NOTHING
""")

# ---------------------------------------------------------
# Cargar registros
# ---------------------------------------------------------

print("Insertando establecimientos...")

with engine.begin() as conn:

    for i, row in gdf.iterrows():

        # GeometrÃ­a
        geometry_wkt = None

        if row.geometry is not None and not row.geometry.is_empty:
            geometry_wkt = row.geometry.wkt

        # CVEGEO
        cvegeo = (
            None
            if pd.isna(row["cvegeo_ageb"])
            else str(row["cvegeo_ageb"])
        )

        # CÃ³digo de actividad
        codigo_act = (
            None
            if pd.isna(row["codigo_act"])
            else str(row["codigo_act"]).strip()
        )

        # TamaÃ±o
        per_ocu = (
            None
            if pd.isna(row["per_ocu"])
            else str(row["per_ocu"]).strip()
        )

        # Fecha de alta
        fecha_alta = (
            None
            if pd.isna(row["fecha_alta"])
            else row["fecha_alta"]
        )

        # Coordenadas
        latitud = (
            None
            if pd.isna(row["latitud"])
            else row["latitud"]
        )

        longitud = (
            None
            if pd.isna(row["longitud"])
            else row["longitud"]
        )

        # Estado de asignaciÃ³n
        estatus_asignacion = (
            "sin_coordenadas_validas"
            if pd.isna(row["estatus_asignacion"])
            else str(row["estatus_asignacion"]).strip()
        )

        params = {
            "establishment_id": row["establishment_id"],
            "cvegeo": cvegeo,
            "codigo_act": codigo_act,
            "per_ocu": per_ocu,
            "fecha_alta": fecha_alta,
            "latitud": latitud,
            "longitud": longitud,
            "geometry_wkt": geometry_wkt,
            "estatus_asignacion": estatus_asignacion
        }

        conn.execute(insert_sql, params)

        if (i + 1) % 10000 == 0:
            print(f"Procesados: {i + 1}")

print("Carga de fact_establecimientos completada.")
