"""ETL de delitos (FGJ CDMX): limpieza, puntos y spatial join con AGEB.

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
    "_id", "fecha_inicio", "fecha_hecho", "delito", "categoria_delito",
    "alcaldia_catalogo", "latitud", "longitud",
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

    report["registros_tras_limpieza"] = len(df)
    return df, report


def to_points(df: pd.DataFrame, target_crs):
    """Convierte a puntos los registros con coordenadas utiles. Devuelve (gdf, reporte)."""
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
    return pts, report


def _first_match(left, right, cols):
    """sjoin 'within' y una sola fila por punto (si cae en el borde de dos poligonos)."""
    joined = gpd.sjoin(left[["geometry"]], right[cols + ["geometry"]], how="left", predicate="within")
    return joined[~joined.index.duplicated(keep="first")]


def assign_polygons(pts, agebs, munis):
    """Asigna alcaldia (poligono) y CVEGEO de AGEB a cada punto."""
    j_mun = _first_match(pts, munis, ["NOMGEO"])
    pts["dentro_cdmx"] = j_mun["NOMGEO"].notna()
    pts["alcaldia_geo"] = j_mun["NOMGEO"]

    j_ageb = _first_match(pts, agebs, ["CVEGEO"])
    pts["CVEGEO"] = j_ageb["CVEGEO"]
    return pts


def _norm(value):
    if pd.isna(value):
        return None
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return text.lower().strip()


def summarize(pts, report):
    dentro = pts[pts["dentro_cdmx"]]
    coinciden = dentro["alcaldia_catalogo"].map(_norm) == dentro["alcaldia_geo"].map(_norm)
    report["con_coordenadas_fuera_de_cdmx"] = int((~pts["dentro_cdmx"]).sum())
    report["dentro_de_cdmx_sin_ageb_urbana"] = int((pts["dentro_cdmx"] & pts["CVEGEO"].isna()).sum())
    report["asignados_a_ageb"] = int(pts["CVEGEO"].notna().sum())
    report["pct_asignados_a_ageb"] = round(report["asignados_a_ageb"] / report["registros_crudos"] * 100, 2)
    report["pct_coincidencia_alcaldia"] = round(float(coinciden.mean()) * 100, 2) if len(dentro) else None
    return report


def run(csv_name: str = DEFAULT_CSV):
    agebs = load_agebs()
    munis = load_municipios()

    df = extract(csv_name)
    df, rep_clean = clean(df)
    pts, rep_pts = to_points(df, agebs.crs)
    pts = assign_polygons(pts, agebs, munis)

    report = summarize(pts, {**rep_clean, **rep_pts})

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    stem = csv_name.rsplit(".", 1)[0].replace("carpetas_fgj_", "delitos_")
    out_gpkg = PROCESSED_DIR / f"{stem}_ageb.gpkg"
    out_json = PROCESSED_DIR / f"{stem}_reporte_calidad.json"
    pts.to_file(out_gpkg, layer="delitos", driver="GPKG")
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Guardado:", out_gpkg)
    return pts, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL de delitos FGJ CDMX")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="archivo dentro de data/raw/")
    run(parser.parse_args().csv)
