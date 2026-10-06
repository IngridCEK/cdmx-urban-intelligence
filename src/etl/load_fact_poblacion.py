import pandas as pd
from sqlalchemy import create_engine, text
from src.config import DB_URL

CSV = "/work/data/raw/ageb_mza_urbana_09_cpv2020/conjunto_de_datos/conjunto_de_datos_ageb_urbana_09_cpv2020.csv"

engine = create_engine(DB_URL)

print("Leyendo Censo 2020...")

df = pd.read_csv(
    CSV,
    encoding="utf-8-sig",
    usecols=[
        "ENTIDAD",
        "MUN",
        "LOC",
        "AGEB",
        "MZA",
        "POBTOT",
        "POB0_14",
        "POB15_64",
        "POB65_MAS",
        "P_12YMAS",
        "PEA",
        "GRAPROES",
        "VIVTOT",
        "TVIVHAB"
    ]
)

# Seleccionar Ãºnicamente los registros agregados a nivel AGEB
ageb = df[
    (df["AGEB"] != "0000") &
    (df["MZA"] == 0)
].copy()

# Construir CVEGEO
ageb["cvegeo"] = (
    ageb["ENTIDAD"].astype(int).astype(str).str.zfill(2)
    + ageb["MUN"].astype(int).astype(str).str.zfill(3)
    + ageb["LOC"].astype(int).astype(str).str.zfill(4)
    + ageb["AGEB"].astype(str).str.zfill(4)
)

# Obtener las geometrÃ­as disponibles
validas = pd.read_sql(
    text("SELECT cvegeo FROM dw.dim_geografia"),
    engine
)

validas = set(validas["cvegeo"].astype(str))

# Conservar Ãºnicamente las AGEB que tienen geometrÃ­a
ageb = ageb[ageb["cvegeo"].isin(validas)].copy()

print(f"AGEB compatibles con dim_geografia: {len(ageb)}")


def clean_int(value):
    if pd.isna(value) or value == "*":
        return None
    return int(value)


def clean_float(value):
    if pd.isna(value) or value == "*":
        return None
    return float(value)


insert_sql = text("""
    INSERT INTO dw.fact_poblacion (
        cvegeo,
        pob_total,
        pob_0_14,
        pob_15_64,
        pob_65_mas,
        pob_12_mas,
        pea,
        vivtot,
        tvivhab,
        graproes,
        fuente,
        fecha_corte
    )
    VALUES (
        :cvegeo,
        :pob_total,
        :pob_0_14,
        :pob_15_64,
        :pob_65_mas,
        :pob_12_mas,
        :pea,
        :vivtot,
        :tvivhab,
        :graproes,
        'Censo 2020 INEGI',
        '2020-03-15'
    )
    ON CONFLICT (cvegeo) DO UPDATE SET
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


print("Insertando poblaciÃ³n...")

with engine.begin() as conn:
    for _, row in ageb.iterrows():

        params = {
            "cvegeo": str(row["cvegeo"]),
            "pob_total": clean_int(row["POBTOT"]),
            "pob_0_14": clean_int(row["POB0_14"]),
            "pob_15_64": clean_int(row["POB15_64"]),
            "pob_65_mas": clean_int(row["POB65_MAS"]),
            "pob_12_mas": clean_int(row["P_12YMAS"]),
            "pea": clean_int(row["PEA"]),
            "vivtot": clean_int(row["VIVTOT"]),
            "tvivhab": clean_int(row["TVIVHAB"]),
            "graproes": clean_float(row["GRAPROES"])
        }

        conn.execute(insert_sql, params)

print("Carga de fact_poblacion completada.")

