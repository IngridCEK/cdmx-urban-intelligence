"""ETL del Censo 2020 (INEGI): una fila por AGEB urbana.

El CSV "Principales resultados por AGEB y manzana urbana" mezcla varios
niveles en el mismo archivo (entidad, municipio, localidad, AGEB y manzana).
Este ETL se queda solo con las filas de TOTAL POR AGEB:
    AGEB distinto de '0000' y MZA igual a '000'

Reglas:
    - Todo se lee como texto (dtype=str) para no perder ceros ni letras de la clave.
    - CVEGEO = ENTIDAD + MUN + LOC + AGEB (13 caracteres), igual que en 09a.shp.
    - Los '*' (dato suprimido por confidencialidad) se convierten a NULO, nunca a cero.
    - Las columnas numericas que se usan se convierten a numero.

Uso (dentro del contenedor):
    python -m src.etl.census
    python -m src.etl.census --csv resageburb_09csv20/RESAGEBURB_09CSV20.csv
Entrada : data/raw/resageburb_09csv20/RESAGEBURB_09CSV20.csv   (no se modifica)
Salida  : data/processed/censo_2020_ageb.csv y censo_2020_ageb_reporte_calidad.json
"""
import argparse
import json

import numpy as np
import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR, STUDY_ENT

DEFAULT_CSV = "resageburb_09csv20/RESAGEBURB_09CSV20.csv"
SUPPRESSED = ["*", "N/D", ""]  # marcas de dato no disponible en el CSV del INEGI

KEY_COLUMNS = ["ENTIDAD", "MUN", "LOC", "AGEB", "MZA"]
ID_COLUMNS = ["CVEGEO", "ENTIDAD", "MUN", "LOC", "AGEB", "NOM_MUN"]

# Poblacion (KPIs de demografia y economia)
POPULATION_COLUMNS = [
    "POBTOT",     # poblacion total
    "POB0_14",    # grupo de edad 0 a 14
    "POB15_64",   # grupo de edad 15 a 64
    "POB65_MAS",  # grupo de edad 65 y mas
    "P_18A24",    # opcional: poblacion joven
    "P_12YMAS",   # base de la tasa de PEA
    "PEA",        # poblacion economicamente activa
    "POCUPADA",   # PEA ocupada
    "PDESOCUP",   # PEA desocupada
    "PE_INAC",    # poblacion no economicamente activa
]
# Vivienda (el PDF pide "housing and related indicators")
HOUSING_COLUMNS = [
    "VIVTOT",    # viviendas totales
    "TVIVHAB",   # viviendas habitadas
    "GRAPROES",  # grado promedio de escolaridad
]
NUMERIC_COLUMNS = POPULATION_COLUMNS + HOUSING_COLUMNS
DECIMAL_COLUMNS = ["GRAPROES"]  # el resto son conteos de personas o viviendas (enteros)
REQUIRED_COLUMNS = KEY_COLUMNS + ["NOM_MUN"] + NUMERIC_COLUMNS
AGE_GROUPS = ["POB0_14", "POB15_64", "POB65_MAS"]


def extract(csv_name: str = DEFAULT_CSV) -> pd.DataFrame:
    """Lee el CSV crudo como texto y valida que esten las columnas necesarias."""
    path = RAW_DIR / csv_name
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Descomprime resageburb_09csv20.zip dentro de data/raw/."
        )
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig", low_memory=False)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el CSV: {missing}")
    return df


def classify_level(df: pd.DataFrame) -> pd.Series:
    """Nivel geografico de cada fila (el CSV mezcla cinco niveles)."""
    level = pd.Series("manzana", index=df.index)
    level[df["MZA"] == "000"] = "ageb"
    level[(df["MZA"] == "000") & (df["AGEB"] == "0000")] = "localidad"
    level[(df["LOC"] == "0000") & (df["AGEB"] == "0000") & (df["MZA"] == "000")] = "municipio"
    level[(df["MUN"] == "000") & (df["LOC"] == "0000") & (df["AGEB"] == "0000") & (df["MZA"] == "000")] = "entidad"
    return level


def select_agebs(df: pd.DataFrame):
    """Filas de total por AGEB (AGEB != '0000' y MZA == '000') con CVEGEO."""
    report = {"registros_crudos": len(df)}
    level = classify_level(df)
    report["filas_por_nivel"] = {
        n: int((level == n).sum()) for n in ["entidad", "municipio", "localidad", "ageb", "manzana"]
    }

    entidades = sorted(df["ENTIDAD"].dropna().unique().tolist())
    if entidades != [STUDY_ENT]:
        raise ValueError(f"Se esperaba solo la entidad {STUDY_ENT}, hay: {entidades}")

    total_entidad = df.loc[level == "entidad", "POBTOT"]
    report["poblacion_total_entidad"] = int(float(total_entidad.iloc[0])) if len(total_entidad) else None

    out = df[(df["AGEB"] != "0000") & (df["MZA"] == "000")].copy()
    out["CVEGEO"] = out["ENTIDAD"] + out["MUN"] + out["LOC"] + out["AGEB"]

    if not (out["CVEGEO"].str.len() == 13).all():
        raise ValueError("Hay CVEGEO que no tienen 13 caracteres")
    if not out["CVEGEO"].is_unique:
        raise ValueError("CVEGEO duplicada entre las filas de AGEB")

    report["agebs_con_letras_en_clave"] = int(out["AGEB"].str.contains("[A-Za-z]").sum())
    report["filas_ageb"] = len(out)
    return out, report


def to_numeric(df: pd.DataFrame):
    """'*' -> nulo (no cero) y conversion a numero. Devuelve (df, asteriscos por columna)."""
    asteriscos = {}
    for col in NUMERIC_COLUMNS:
        raw = df[col].str.strip()
        asteriscos[col] = int((raw == "*").sum())
        clean = raw.where(~raw.isin(SUPPRESSED), np.nan)
        num = pd.to_numeric(clean, errors="raise")  # si aparece otro texto, que falle
        # Enteros con nulos ("Int64") para que el CSV diga 388 y no 388.0
        df[col] = num if col in DECIMAL_COLUMNS else num.astype("Int64")
    return df, asteriscos


def quality_report(df: pd.DataFrame, asteriscos: dict, report: dict) -> dict:
    """Nulos por columna, AGEB con poblacion cero y revisiones de consistencia."""
    n = len(df)
    nulos = {c: int(df[c].isna().sum()) for c in NUMERIC_COLUMNS}
    report["nulos_por_columna"] = nulos
    report["pct_nulos_por_columna"] = {c: round(v / n * 100, 2) for c, v in nulos.items()}
    report["asteriscos_convertidos_a_nulo"] = asteriscos

    report["agebs_poblacion_cero"] = int((df["POBTOT"] == 0).sum())
    report["agebs_poblacion_nula"] = int(df["POBTOT"].isna().sum())

    # Consistencia (no se corrige nada: solo se reporta para que el equipo lo conozca)
    suma_edad = df[AGE_GROUPS].sum(axis=1, min_count=len(AGE_GROUPS))
    dif = df["POBTOT"] - suma_edad
    report["consistencia"] = {
        "agebs_grupos_edad_menor_a_pobtot": int((dif > 0).sum()),
        "agebs_grupos_edad_mayor_a_pobtot": int((dif < 0).sum()),
        "agebs_pea_mayor_a_p12ymas": int((df["PEA"] > df["P_12YMAS"]).sum()),
        "agebs_viviendas_habitadas_mayor_a_totales": int((df["TVIVHAB"] > df["VIVTOT"]).sum()),
    }

    pob_ageb = int(df["POBTOT"].sum())
    report["poblacion_en_agebs_urbanas"] = pob_ageb
    if report.get("poblacion_total_entidad"):
        report["pct_poblacion_en_agebs_urbanas"] = round(pob_ageb / report["poblacion_total_entidad"] * 100, 2)
    report["agebs_por_alcaldia"] = {k: int(v) for k, v in df["NOM_MUN"].value_counts().sort_index().items()}
    report["filas_salida"] = n
    return report


def run(csv_name: str = DEFAULT_CSV):
    raw = extract(csv_name)
    agebs, report = select_agebs(raw)
    agebs, asteriscos = to_numeric(agebs)
    report = quality_report(agebs, asteriscos, report)

    final = agebs[ID_COLUMNS + NUMERIC_COLUMNS].sort_values("CVEGEO").reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = PROCESSED_DIR / "censo_2020_ageb.csv"
    out_json = PROCESSED_DIR / "censo_2020_ageb_reporte_calidad.json"
    final.to_csv(out_csv, index=False, encoding="utf-8")  # nulos quedan como celda vacia
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Guardado:", out_csv)
    return final, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL del Censo 2020 por AGEB")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="archivo dentro de data/raw/")
    run(parser.parse_args().csv)
