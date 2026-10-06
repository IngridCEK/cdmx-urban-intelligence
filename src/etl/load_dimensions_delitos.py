"""Carga dim_fecha, dim_hora y dim_delito desde delitos procesados."""

import geopandas as gpd
import pandas as pd
from sqlalchemy import text

from src.config import PROCESSED_DIR
from src.db import get_engine

GPKG = PROCESSED_DIR / "delitos_2023_ageb.gpkg"


def clasificar_hora(hora):
    if 0 <= hora <= 5:
        return "00:00-05:59", "Madrugada"
    if 6 <= hora <= 11:
        return "06:00-11:59", "Manana"
    if 12 <= hora <= 17:
        return "12:00-17:59", "Tarde"
    return "18:00-23:59", "Noche"


def run():
    if not GPKG.exists():
        raise FileNotFoundError(f"No existe {GPKG}. Ejecuta primero src.etl.crime.")

    print("Leyendo delitos procesados...")
    gdf = gpd.read_file(GPKG, layer="delitos")

    fechas = (
        pd.to_datetime(gdf["fecha_hecho"], errors="coerce")
        .dropna().dt.normalize().drop_duplicates().sort_values()
    )
    nombres_mes = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    fecha_rows = [
        {
            "fecha_key": int(fecha.strftime("%Y%m%d")),
            "fecha": fecha.date(),
            "dia": int(fecha.day),
            "mes": int(fecha.month),
            "nombre_mes": nombres_mes[int(fecha.month)],
            "trimestre": int(fecha.quarter),
            "anio": int(fecha.year),
        }
        for fecha in fechas
    ]

    hora_rows = []
    for hora in range(24):
        franja, parte = clasificar_hora(hora)
        hora_rows.append({"hora_key": hora, "hora": hora, "franja": franja, "parte": parte})

    delitos = (
        gdf[["categoria_delito", "delito"]]
        .dropna(subset=["categoria_delito", "delito"])
        .drop_duplicates()
    )
    delito_rows = [
        {"categoria": str(r.categoria_delito).strip(), "delito": str(r.delito).strip()}
        for r in delitos.itertuples(index=False)
    ]

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO dw.dim_fecha
                (fecha_key, fecha, dia, mes, nombre_mes, trimestre, anio)
            VALUES
                (:fecha_key, :fecha, :dia, :mes, :nombre_mes, :trimestre, :anio)
            ON CONFLICT (fecha_key) DO UPDATE SET
                fecha = EXCLUDED.fecha, dia = EXCLUDED.dia, mes = EXCLUDED.mes,
                nombre_mes = EXCLUDED.nombre_mes, trimestre = EXCLUDED.trimestre,
                anio = EXCLUDED.anio
        """), fecha_rows)

        conn.execute(text("""
            INSERT INTO dw.dim_hora (hora_key, hora, franja_horaria, parte_dia)
            VALUES (:hora_key, :hora, :franja, :parte)
            ON CONFLICT (hora_key) DO UPDATE SET
                hora = EXCLUDED.hora,
                franja_horaria = EXCLUDED.franja_horaria,
                parte_dia = EXCLUDED.parte_dia
        """), hora_rows)

        conn.execute(text("""
            INSERT INTO dw.dim_delito (categoria_delito, delito)
            VALUES (:categoria, :delito)
            ON CONFLICT (categoria_delito, delito) DO NOTHING
        """), delito_rows)

    print(f"Fechas cargadas: {len(fecha_rows)}")
    print("Horas cargadas: 24")
    print(f"Delitos cargados: {len(delito_rows)}")
    print("Carga de dimensiones de delitos completada.")


if __name__ == "__main__":
    run()
