"""Carga fact_poblacion desde la salida procesada del Censo 2020 de Persona B."""

import pandas as pd
from sqlalchemy import text

from src.config import PROCESSED_DIR
from src.db import get_engine

CSV = PROCESSED_DIR / "censo_2020_ageb.csv"
EXPECTED_WITHOUT_POLYGON = {"0901101101107", "0901201351227"}


def clean_int(value):
    if pd.isna(value) or str(value).strip() == "*":
        return None
    return int(float(value))


def clean_float(value):
    if pd.isna(value) or str(value).strip() == "*":
        return None
    return float(value)


def run():
    if not CSV.exists():
        raise FileNotFoundError(f"No existe {CSV}. Ejecuta primero el ETL de Censo.")

    print("Leyendo Censo 2020 procesado...")
    df = pd.read_csv(CSV, dtype={"CVEGEO": str}, encoding="utf-8")
    if df["CVEGEO"].duplicated().any():
        raise ValueError("censo_2020_ageb.csv contiene CVEGEO duplicados")

    engine = get_engine()
    validas = set(
        pd.read_sql(text("SELECT CVEGEO FROM dw.dim_geografia"), engine)["cvegeo"].astype(str)
    )
    censo_keys = set(df["CVEGEO"].astype(str))
    sin_poligono = censo_keys - validas

    print(f"AGEB del Censo: {len(df)}")
    print(f"AGEB sin poligono en dim_geografia: {len(sin_poligono)}")
    if sin_poligono:
        print("CVEGEO sin poligono:", ", ".join(sorted(sin_poligono)))

    # La diferencia conocida entre Censo (2,433) y Marco Geoestadistico (2,431)
    # se valida explicitamente; no se descartan filas desconocidas en silencio.
    inesperadas = sin_poligono - EXPECTED_WITHOUT_POLYGON
    if inesperadas:
        raise ValueError(f"AGEB sin poligono no documentadas: {sorted(inesperadas)}")

    ageb = df[df["CVEGEO"].isin(validas)].copy()
    print(f"AGEB compatibles con dim_geografia: {len(ageb)}")

    rows = [
        {
            "cvegeo": str(row.CVEGEO),
            "pob_total": clean_int(row.POBTOT),
            "pob_0_14": clean_int(row.POB0_14),
            "pob_15_64": clean_int(row.POB15_64),
            "pob_65_mas": clean_int(row.POB65_MAS),
            "pob_12_mas": clean_int(row.P_12YMAS),
            "pea": clean_int(row.PEA),
            "vivtot": clean_int(row.VIVTOT),
            "tvivhab": clean_int(row.TVIVHAB),
            "graproes": clean_float(row.GRAPROES),
        }
        for row in ageb.itertuples(index=False)
    ]

    sql = text("""
        INSERT INTO dw.fact_poblacion (
            CVEGEO, pob_total, pob_0_14, pob_15_64, pob_65_mas,
            pob_12_mas, pea, vivtot, tvivhab, graproes, fuente, fecha_corte
        )
        VALUES (
            :cvegeo, :pob_total, :pob_0_14, :pob_15_64, :pob_65_mas,
            :pob_12_mas, :pea, :vivtot, :tvivhab, :graproes,
            'Censo 2020 INEGI', '2020-03-15'
        )
        ON CONFLICT (CVEGEO) DO UPDATE SET
            pob_total = EXCLUDED.pob_total,
            pob_0_14 = EXCLUDED.pob_0_14,
            pob_15_64 = EXCLUDED.pob_15_64,
            pob_65_mas = EXCLUDED.pob_65_mas,
            pob_12_mas = EXCLUDED.pob_12_mas,
            pea = EXCLUDED.pea,
            vivtot = EXCLUDED.vivtot,
            tvivhab = EXCLUDED.tvivhab,
            graproes = EXCLUDED.graproes,
            fuente = EXCLUDED.fuente,
            fecha_corte = EXCLUDED.fecha_corte
    """)

    with engine.begin() as conn:
        conn.execute(sql, rows)
        total = conn.execute(text("SELECT COUNT(*) FROM dw.fact_poblacion")).scalar()

    print(f"Registros en fact_poblacion: {total}")
    print("Carga de fact_poblacion completada.")


if __name__ == "__main__":
    run()
