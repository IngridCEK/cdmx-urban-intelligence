"""ETL del DENUE 11/2023 para Ciudad de México."""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR, STUDY_ENT, WORK_CRS
from src.geo.polygons import load_agebs


DEFAULT_CSV = (
    RAW_DIR
    / "denue_09_csv"
    / "conjunto_de_datos"
    / "denue_inegi_09_.csv"
)

OUTPUT_GPKG = PROCESSED_DIR / "denue_2023_ageb.gpkg"
OUTPUT_REPORT = PROCESSED_DIR / "denue_2023_reporte_calidad.json"


REQUIRED_COLUMNS = [
    "id",
    "codigo_act",
    "nombre_act",
    "per_ocu",
    "cve_ent",
    "cve_mun",
    "cve_loc",
    "ageb",
    "manzana",
    "latitud",
    "longitud",
    "fecha_alta",
]


def extract(csv_path: Path = DEFAULT_CSV) -> pd.DataFrame:
    """Lee el CSV original del DENUE."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo DENUE: {csv_path}"
        )

    df = pd.read_csv(
        csv_path,
        encoding="latin-1",
        low_memory=False,
        dtype={
            "id": "string",
            "codigo_act": "string",
            "nombre_act": "string",
            "per_ocu": "string",
            "cve_ent": "string",
            "cve_mun": "string",
            "cve_loc": "string",
            "ageb": "string",
            "manzana": "string",
            "latitud": "string",
            "longitud": "string",
            "fecha_alta": "string",
        },
    )

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas en DENUE: {missing}"
        )

    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia tipos y construye claves geográficas."""

    df = df.copy()

    string_columns = [
        "id",
        "codigo_act",
        "nombre_act",
        "per_ocu",
        "cve_ent",
        "cve_mun",
        "cve_loc",
        "ageb",
        "manzana",
        "fecha_alta",
    ]

    for column in string_columns:
        df[column] = df[column].astype("string").str.strip()

    # Claves geográficas con ceros a la izquierda.
    df["cve_ent"] = df["cve_ent"].str.zfill(2)
    df["cve_mun"] = df["cve_mun"].str.zfill(3)
    df["cve_loc"] = df["cve_loc"].str.zfill(4)
    df["ageb"] = df["ageb"].str.upper()

    # CVEGEO = entidad + municipio + localidad + AGEB.
    df["cvegeo"] = (
        df["cve_ent"]
        + df["cve_mun"]
        + df["cve_loc"]
        + df["ageb"]
    )

    # Coordenadas numéricas.
    df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")

    # Fecha.
    df["fecha_alta"] = pd.to_datetime(
        df["fecha_alta"],
        errors="coerce",
        dayfirst=True,
    )

    return df


def validate_coordinates(df: pd.DataFrame) -> pd.Series:
    """Indica qué registros tienen coordenadas geográficas válidas."""

    return (
        df["latitud"].notna()
        & df["longitud"].notna()
        & df["latitud"].between(14, 34)
        & df["longitud"].between(-120, -85)
        & (df["latitud"] != 0)
        & (df["longitud"] != 0)
    )


def spatial_assign(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Asigna cada establecimiento a un AGEB mediante ubicación espacial."""

    valid = validate_coordinates(df)

    geo = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(
            df["longitud"],
            df["latitud"],
        ),
        crs="EPSG:4326",
    )

    geo["estatus_asignacion"] = "sin_coordenadas_validas"

    geo.loc[valid, "estatus_asignacion"] = "con_coordenadas_validas"

    agebs = load_agebs()[["CVEGEO", "geometry"]].copy()

    agebs = agebs.to_crs("EPSG:4326")

    valid_geo = geo.loc[valid].copy()

    joined = gpd.sjoin(
        valid_geo,
        agebs,
        how="left",
        predicate="within",
    )

    joined["cvegeo_ageb"] = joined["CVEGEO"]

    joined["estatus_asignacion"] = joined["cvegeo_ageb"].notna().map(
        {
            True: "asignado",
            False: "coordenada_sin_ageb",
        }
    )

    geo.loc[valid, "cvegeo_ageb"] = joined["cvegeo_ageb"].values
    geo.loc[valid, "estatus_asignacion"] = (
        joined["estatus_asignacion"].values
    )

    return geo


def build_report(
    raw_rows: int,
    cleaned_rows: int,
    geo: gpd.GeoDataFrame,
) -> dict:
    """Construye el reporte de calidad del ETL."""

    status_counts = (
        geo["estatus_asignacion"]
        .value_counts(dropna=False)
        .to_dict()
    )

    assigned = int(status_counts.get("asignado", 0))

    return {
        "registros_crudos": raw_rows,
        "registros_tras_limpieza": cleaned_rows,
        "establecimientos_asignados_a_ageb": assigned,
        "estatus_asignacion": {
            str(k): int(v)
            for k, v in status_counts.items()
        },
        "cvegeo_unicos": int(geo["cvegeo"].nunique()),
        "ageb_espacial_unicos": int(
            geo["cvegeo_ageb"].dropna().nunique()
        ),
        "coordenadas_validas": int(
            validate_coordinates(geo).sum()
        ),
        "coordenadas_invalidas": int(
            (~validate_coordinates(geo)).sum()
        ),
    }


def run() -> tuple[gpd.GeoDataFrame, dict]:
    """Ejecuta el ETL completo del DENUE."""

    raw = extract()

    cleaned = clean(raw)

    geo = spatial_assign(cleaned)

    report = build_report(
        raw_rows=len(raw),
        cleaned_rows=len(cleaned),
        geo=geo,
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_GPKG.exists():
        OUTPUT_GPKG.unlink()

    geo.to_file(
        OUTPUT_GPKG,
        layer="denue_2023_ageb",
        driver="GPKG",
    )

    OUTPUT_REPORT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Guardado: {OUTPUT_GPKG}")
    print(f"Reporte: {OUTPUT_REPORT}")

    return geo, report


if __name__ == "__main__":
    run()
