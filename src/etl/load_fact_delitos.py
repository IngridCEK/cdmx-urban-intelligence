import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from src.config import DB_URL

GPKG = "/work/data/processed/delitos_2023_ageb.gpkg"

engine = create_engine(DB_URL)

print("Leyendo delitos...")

gdf = gpd.read_file(GPKG)

print(f"Registros leídos: {len(gdf)}")

# ---------------------------------------------------------
# Transformar geometrías al CRS de trabajo
# ---------------------------------------------------------

gdf = gdf.to_crs("EPSG:32614")

print(f"CRS transformado: {gdf.crs}")

# ---------------------------------------------------------
# Preparar columnas
# ---------------------------------------------------------

gdf["source_id"] = gdf["_id"].astype(str)

# Fecha clave
gdf["fecha_key"] = None

mask_fecha = gdf["fecha_hecho"].notna()

gdf.loc[mask_fecha, "fecha_key"] = (
    gdf.loc[mask_fecha, "fecha_hecho"]
    .dt.strftime("%Y%m%d")
    .astype(int)
)

# Hora clave
gdf["hora_key"] = gdf["hora"].where(
    gdf["hora"].notna(),
    None
)

print("Columnas preparadas.")

# ---------------------------------------------------------
# SQL de inserción
# ---------------------------------------------------------

insert_sql = text("""
    INSERT INTO dw.fact_delitos (
        source_id,
        fecha_inicio,
        fecha_hecho,
        hora_hecho,
        hora,
        fecha_key,
        hora_key,
        delito_key,
        cvegeo,
        delito,
        categoria_delito,
        alcaldia_catalogo,
        alcaldia_geo,
        latitud,
        longitud,
        estatus_asignacion,
        geometry,
        incident_count
    )
    SELECT
        :source_id,
        :fecha_inicio,
        :fecha_hecho,
        :hora_hecho,
        :hora,
        :fecha_key,
        :hora_key,
        (
            SELECT delito_key
            FROM dw.dim_delito
            WHERE categoria_delito = :categoria_delito
              AND delito = :delito
        ),
        :cvegeo,
        :delito,
        :categoria_delito,
        :alcaldia_catalogo,
        :alcaldia_geo,
        :latitud,
        :longitud,
        :estatus_asignacion,
        ST_GeomFromText(:geometry_wkt, 32614),
        1
    ON CONFLICT (source_id) DO NOTHING
""")

# ---------------------------------------------------------
# Cargar registros
# ---------------------------------------------------------

print("Insertando registros...")

with engine.begin() as conn:

    for i, row in gdf.iterrows():

        # Convertir geometría a WKT
        geometry_wkt = None

        if row.geometry is not None and not row.geometry.is_empty:
            geometry_wkt = row.geometry.wkt

        # Convertir valores faltantes de Pandas a None
        fecha_inicio = (
            None
            if pd.isna(row["fecha_inicio"])
            else row["fecha_inicio"]
        )

        fecha_hecho = (
            None
            if pd.isna(row["fecha_hecho"])
            else row["fecha_hecho"]
        )

        hora_hecho = (
            None
            if pd.isna(row["hora_hecho"])
            else row["hora_hecho"]
        )

        hora = (
            None
            if pd.isna(row["hora"])
            else int(row["hora"])
        )

        fecha_key = (
            None
            if pd.isna(row["fecha_key"])
            else int(row["fecha_key"])
        )

        hora_key = (
            None
            if pd.isna(row["hora_key"])
            else int(row["hora_key"])
        )

        cvegeo = (
            None
            if pd.isna(row["CVEGEO"])
            else str(row["CVEGEO"])
        )

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

        alcaldia_catalogo = (
            None
            if pd.isna(row["alcaldia_catalogo"])
            else row["alcaldia_catalogo"]
        )

        alcaldia_geo = (
            None
            if pd.isna(row["alcaldia_geo"])
            else row["alcaldia_geo"]
        )

        delito = (
            None
            if pd.isna(row["delito"])
            else row["delito"]
        )

        categoria_delito = (
            None
            if pd.isna(row["categoria_delito"])
            else row["categoria_delito"]
        )

        estatus_asignacion = (
            None
            if pd.isna(row["estatus_asignacion"])
            else row["estatus_asignacion"]
        )

        params = {
            "source_id": row["source_id"],
            "fecha_inicio": fecha_inicio,
            "fecha_hecho": fecha_hecho,
            "hora_hecho": hora_hecho,
            "hora": hora,
            "fecha_key": fecha_key,
            "hora_key": hora_key,
            "categoria_delito": categoria_delito,
            "delito": delito,
            "cvegeo": cvegeo,
            "alcaldia_catalogo": alcaldia_catalogo,
            "alcaldia_geo": alcaldia_geo,
            "latitud": latitud,
            "longitud": longitud,
            "estatus_asignacion": estatus_asignacion,
            "geometry_wkt": geometry_wkt
        }

        conn.execute(insert_sql, params)

        if (i + 1) % 10000 == 0:
            print(f"Procesados: {i + 1}")

print("Carga de fact_delitos completada.")