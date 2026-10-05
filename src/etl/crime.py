"""ETL de delitos (FGJ CDMX): limpieza, puntos y spatial join con AGEB.

Conserva TODOS los registros del CSV (trazabilidad). Cada uno recibe un
estatus de asignacion:
    asignado               -> cae dentro de una AGEB urbana (CVEGEO no nulo)
    dentro_cdmx_sin_ageb   -> dentro de la CDMX pero fuera de toda AGEB urbana
    fuera_cdmx             -> tiene coordenadas pero caen fuera de la CDMX
    sin_coordenadas_validas-> sin latitud/longitud utiles (nulas, cero o fuera de rango)

Uso (dentro del contenedor):
    python -m src.etl.crime
    python -m src.etl.crime --csv carpetas_fgj_2022.csv
Entrada : data/raw/<csv>            (no se modifica)
Salida  : data/processed/delitos_<anio>_ageb.gpkg y reporte de calidad .json
"""
import argparse
import json
import unicodedata

import geopandas as gpd
import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR
from src.geo.polygons import load_agebs, load_municipios

DEFAULT_CSV = "carpetas_fgj_2023.csv"
REQUIRED_COLUMNS = [
    "_id", "fecha_inicio", "fecha_hecho", "hora_hecho", "delito",
    "categoria_delito", "alcaldia_catalogo", "latitud", "longitud",
]
STATUS_ORDER = [
    "asignado", "dentro_cdmx_sin_ageb", "fuera_cdmx", "sin_coordenadas_validas",
]


def extract(csv_name: str) -> pd.DataFrame:
    """Lee el CSV crudo sin modificarlo en disco y valida las columnas."""
    path = RAW_DIR / csv_name
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    df = pd.read_csv(path, low_memory=False)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el CSV: {missing}")
    return df


def clean(df: pd.DataFrame):
    """Estandariza tipos y texto, quita duplicados. Devuelve (df, reporte)."""
    report = {"registros_crudos": len(df)}

    df = df.copy()
    n_dup = int(df["_id"].duplicated().sum())
    df = df.drop_duplicates(subset="_id")
    report["duplicados_eliminados"] = n_dup

    for col in ["latitud", "longitud"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["fecha_inicio", "fecha_hecho"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["delito", "categoria_delito", "alcaldia_catalogo"]:
        df[col] = df[col].astype("string").str.strip()

    # Hora entera (0-23) para dim_hora; la columna original se conserva
    df["hora"] = pd.to_datetime(df["hora_hecho"], format="%H:%M:%S", errors="coerce").dt.hour

    report["registros_tras_limpieza"] = len(df)
    return df, report


def split_by_coordinates(df: pd.DataFrame, target_crs):
    """Separa registros con coordenadas utiles (-> puntos) de los que no.

    Devuelve (puntos, sin_coordenadas, reporte).
    """
    sin_coord = df["latitud"].isna() | df["longitud"].isna()
    en_cero = (df["latitud"] == 0) | (df["longitud"] == 0)
    fuera_rango = ~df["latitud"].between(-90, 90) | ~df["longitud"].between(-180, 180)
    ok = ~(sin_coord | en_cero | fuera_rango)

    report = {
        "sin_coordenadas": int(sin_coord.sum()),
        "coordenadas_en_cero": int((en_cero & ~sin_coord).sum()),
        "coordenadas_fuera_de_rango": int((fuera_rango & ~sin_coord & ~en_cero).sum()),
        "con_coordenadas_utiles": int(ok.sum()),
    }

    valid = df[ok]
    pts = gpd.GeoDataFrame(
        valid,
        geometry=gpd.points_from_xy(valid["longitud"], valid["latitud"]),
        crs="EPSG:4326",
    ).to_crs(target_crs)
    return pts, df[~ok].copy(), report


def _first_match(left, right, cols):
    """sjoin 'within' y una sola fila por punto (si cae en el borde de dos poligonos)."""
    joined = gpd.sjoin(left[["geometry"]], right[cols + ["geometry"]], how="left", predicate="within")
    return joined[~joined.index.duplicated(keep="first")]


def assign_polygons(pts, agebs, munis):
    """Asigna alcaldia (poligono), CVEGEO de AGEB y estatus a cada punto."""
    j_mun = _first_match(pts, munis, ["NOMGEO"])
    dentro_cdmx = j_mun["NOMGEO"].notna()
    pts["alcaldia_geo"] = j_mun["NOMGEO"]

    j_ageb = _first_match(pts, agebs, ["CVEGEO"])
    pts["CVEGEO"] = j_ageb["CVEGEO"]

    pts["estatus_asignacion"] = "fuera_cdmx"
    pts.loc[dentro_cdmx, "estatus_asignacion"] = "dentro_cdmx_sin_ageb"
    pts.loc[pts["CVEGEO"].notna(), "estatus_asignacion"] = "asignado"
    return pts


def build_final(pts, sin_coord, crs):
    """Une puntos asignados y registros sin coordenadas en una sola tabla."""
    sin_coord = sin_coord.copy()
    sin_coord["alcaldia_geo"] = None
    sin_coord["CVEGEO"] = None
    sin_coord["estatus_asignacion"] = "sin_coordenadas_validas"
    sin_coord = gpd.GeoDataFrame(
        sin_coord, geometry=gpd.GeoSeries([None] * len(sin_coord), index=sin_coord.index, crs=crs)
    )
    final = pd.concat([pts, sin_coord]).sort_index()
    return gpd.GeoDataFrame(final, geometry="geometry", crs=crs)


def _norm(value):
    if pd.isna(value):
        return None
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return text.lower().strip()


def summarize(final, report):
    counts = final["estatus_asignacion"].value_counts()
    status = {s: int(counts.get(s, 0)) for s in STATUS_ORDER}
    report["estatus_asignacion"] = status
    report["reconciliacion_ok"] = sum(status.values()) == report["registros_tras_limpieza"]
    report["asignados_a_ageb"] = status["asignado"]
    report["pct_asignados_a_ageb"] = round(status["asignado"] / report["registros_crudos"] * 100, 2)

    dentro = final[final["estatus_asignacion"].isin(["asignado", "dentro_cdmx_sin_ageb"])]
    coinciden = dentro["alcaldia_catalogo"].map(_norm) == dentro["alcaldia_geo"].map(_norm)
    report["pct_coincidencia_alcaldia"] = round(float(coinciden.mean()) * 100, 2) if len(dentro) else None
    return report


def run(csv_name: str = DEFAULT_CSV):
    agebs = load_agebs()
    munis = load_municipios()

    df = extract(csv_name)
    df, rep_clean = clean(df)
    pts, sin_coord, rep_pts = split_by_coordinates(df, agebs.crs)
    pts = assign_polygons(pts, agebs, munis)
    final = build_final(pts, sin_coord, agebs.crs)

    report = summarize(final, {**rep_clean, **rep_pts})
    if not report["reconciliacion_ok"]:
        raise RuntimeError("La reconciliacion de registros no cuadra: revisa el reporte")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    stem = csv_name.rsplit(".", 1)[0].replace("carpetas_fgj_", "delitos_")
    out_gpkg = PROCESSED_DIR / f"{stem}_ageb.gpkg"
    out_json = PROCESSED_DIR / f"{stem}_reporte_calidad.json"
    final.to_file(out_gpkg, layer="delitos", driver="GPKG")
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Guardado:", out_gpkg)
    return final, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL de delitos FGJ CDMX")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="archivo dentro de data/raw/")
    run(parser.parse_args().csv)
