import geopandas as gpd
import pandas as pd
from sqlalchemy import text

from src.db import get_engine

GPKG = "/work/data/processed/delitos_2023_ageb.gpkg"

engine = get_engine()

print("Leyendo delitos procesados...")
gdf = gpd.read_file(GPKG)

# ---------------------------------------------------------
# 1. Cargar dim_fecha
# ---------------------------------------------------------

print("Cargando dim_fecha...")

fechas = (
    pd.to_datetime(gdf["fecha_hecho"], errors="coerce")
    .dropna()
    .dt.normalize()
    .drop_duplicates()
    .sort_values()
)

nombres_mes = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

with engine.begin() as conn:
    for fecha in fechas:
        fecha_key = int(fecha.strftime("%Y%m%d"))
        mes = int(fecha.month)

        conn.execute(
            text("""
                INSERT INTO dw.dim_fecha (
                    fecha_key,
                    fecha,
                    dia,
                    mes,
                    nombre_mes,
                    trimestre,
                    anio
                )
                VALUES (
                    :fecha_key,
                    :fecha,
                    :dia,
                    :mes,
                    :nombre_mes,
                    :trimestre,
                    :anio
                )
                ON CONFLICT (fecha_key) DO NOTHING
            """),
            {
                "fecha_key": fecha_key,
                "fecha": fecha.date(),
                "dia": int(fecha.day),
                "mes": mes,
                "nombre_mes": nombres_mes[mes],
                "trimestre": int(fecha.quarter),
                "anio": int(fecha.year),
            }
        )

print(f"Fechas cargadas: {len(fechas)}")

# ---------------------------------------------------------
# 2. Cargar dim_hora
# ---------------------------------------------------------

print("Cargando dim_hora...")

def clasificar_hora(hora):
    if 0 <= hora <= 5:
        return "00:00-05:59", "Madrugada"
    elif 6 <= hora <= 11:
        return "06:00-11:59", "Manana"
    elif 12 <= hora <= 17:
        return "12:00-17:59", "Tarde"
    else:
        return "18:00-23:59", "Noche"


with engine.begin() as conn:
    for hora in range(24):
        franja, parte = clasificar_hora(hora)

        conn.execute(
            text("""
                INSERT INTO dw.dim_hora (
                    hora_key,
                    hora,
                    franja_horaria,
                    parte_dia
                )
                VALUES (
                    :hora_key,
                    :hora,
                    :franja,
                    :parte
                )
                ON CONFLICT (hora_key) DO NOTHING
            """),
            {
                "hora_key": hora,
                "hora": hora,
                "franja": franja,
                "parte": parte,
            }
        )

print("Horas cargadas: 24")

# ---------------------------------------------------------
# 3. Cargar dim_delito
# ---------------------------------------------------------

print("Cargando dim_delito...")

delitos = (
    gdf[["categoria_delito", "delito"]]
    .dropna(subset=["categoria_delito", "delito"])
    .drop_duplicates()
)

with engine.begin() as conn:
    for _, row in delitos.iterrows():
        conn.execute(
            text("""
                INSERT INTO dw.dim_delito (
                    categoria_delito,
                    delito
                )
                VALUES (
                    :categoria,
                    :delito
                )
                ON CONFLICT (categoria_delito, delito) DO NOTHING
            """),
            {
                "categoria": str(row["categoria_delito"]).strip(),
                "delito": str(row["delito"]).strip(),
            }
        )

print(f"Delitos cargados: {len(delitos)}")
print("Carga de dimensiones de delitos completada.")
