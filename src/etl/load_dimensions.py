import geopandas as gpd
from sqlalchemy import create_engine, text
from src.config import DB_URL

GPKG = "/work/data/processed/denue_2023_ageb.gpkg"

engine = create_engine(DB_URL)

print("Leyendo DENUE...")

gdf = gpd.read_file(
    GPKG,
    columns=["codigo_act", "nombre_act", "per_ocu"]
)

# ---------------------------------------------------------
# 1. Cargar tamaño de establecimiento
# ---------------------------------------------------------

print("Cargando dim_tamano...")

tamanos = (
    gdf[["per_ocu"]]
    .drop_duplicates()
    .dropna()
)

with engine.begin() as conn:

    for i, categoria in enumerate(tamanos["per_ocu"], start=1):

        conn.execute(
            text("""
                INSERT INTO dw.dim_tamano
                    (tamano_key, categoria_tamano, descripcion)
                VALUES
                    (:key, :categoria, :descripcion)
                ON CONFLICT (tamano_key)
                DO UPDATE SET
                    categoria_tamano = EXCLUDED.categoria_tamano,
                    descripcion = EXCLUDED.descripcion
            """),
            {
                "key": i,
                "categoria": categoria,
                "descripcion": f"Establecimientos con {categoria}"
            }
        )

    total_tamanos = conn.execute(
        text("SELECT COUNT(*) FROM dw.dim_tamano")
    ).scalar()

print(f"Registros en dim_tamano: {total_tamanos}")

# ---------------------------------------------------------
# 2. Cargar actividades económicas
# ---------------------------------------------------------

print("Cargando dim_actividad_economica...")

actividades = (
    gdf[["codigo_act", "nombre_act"]]
    .drop_duplicates()
    .dropna(subset=["codigo_act"])
)

with engine.begin() as conn:

    for _, row in actividades.iterrows():

        codigo = str(row["codigo_act"]).strip()

        conn.execute(
            text("""
                INSERT INTO dw.dim_actividad_economica
                    (codigo_act, nombre_act)
                VALUES
                    (:codigo, :nombre)
                ON CONFLICT (codigo_act)
                DO UPDATE SET
                    nombre_act = EXCLUDED.nombre_act
            """),
            {
                "codigo": codigo,
                "nombre": row["nombre_act"]
            }
        )

    total_actividades = conn.execute(
        text("SELECT COUNT(*) FROM dw.dim_actividad_economica")
    ).scalar()

print(f"Registros en dim_actividad_economica: {total_actividades}")

print("Carga de dimensiones DENUE completada.")