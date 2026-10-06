"""ETL del DENUE 05_2026 (INEGI) por AGEB urbana.

Conserva los 462,732 establecimientos y asigna un estatus:
    asignado, dentro_cdmx_sin_ageb, fuera_cdmx, sin_coordenadas_validas.
"""

import argparse
import json
import geopandas as gpd
import pandas as pd
from src.config import BORDER_TOLERANCE_M, PROCESSED_DIR, RAW_DIR, ROOT
from src.geo.polygons import load_agebs, load_municipios

DEFAULT_CSV = "denue_09_csv/conjunto_de_datos/denue_inegi_09_.csv"
STUDY_ENT_KEY = "09"
STATUS_ORDER = ["asignado", "dentro_cdmx_sin_ageb", "fuera_cdmx", "sin_coordenadas_validas"]
REQUIRED_COLUMNS = [
    "id",
    "codigo_act",
    "nombre_act",
    "per_ocu",
    "tipoUniEco",
    "cve_ent",
    "cve_mun",
    "cve_loc",
    "ageb",
    "manzana",
    "latitud",
    "longitud",
]
# Solo lo necesario para los KPIs. Nombre, razon social, telefono, correo, web y
# domicilio no se leen ni se guardan (ver docs/kpi_variables.md).
SOURCE_COLUMNS = REQUIRED_COLUMNS + ["fecha_alta"]
SCIAN_CATALOG = ROOT / "data" / "catalogos" / "scian_sectores.csv"
DERIVED_COLUMNS = [
    "CVEGEO_DENUE",
    "sector",
    "grupo_actividad",
    "alcaldia_geo",
    "CVEGEO",
    "estatus_asignacion",
    "geometry",
]
OUTPUT_COLUMNS = SOURCE_COLUMNS + DERIVED_COLUMNS


def extract(csv_name=DEFAULT_CSV):
    path = RAW_DIR / csv_name
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    df = pd.read_csv(
        path,
        encoding="latin-1",
        dtype=str,
        low_memory=False,
        usecols=lambda c: c in SOURCE_COLUMNS,
    )
    missing = [c for c in SOURCE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el CSV: {missing}")
    return df


def load_scian_catalog(path=SCIAN_CATALOG):
    """Catalogo de sectores -> dict {prefijo de 2 digitos: (sector, grupo)}.

    Los sectores agrupados del SCIAN vienen como rango en el catalogo ("31-33", "48-49"):
    se expanden para que codigo_act que empieza con 31, 32 o 33 caiga en "31-33".
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el catalogo SCIAN: {path}")
    cat = pd.read_csv(path, dtype=str, encoding="utf-8")
    lookup = {}
    for sector, grupo in zip(cat["sector"].str.strip(), cat["grupo"].str.strip()):
        first, _, last = sector.partition("-")
        for prefix in range(int(first), int(last or first) + 1):
            key = f"{prefix:02d}"
            if key in lookup:
                raise ValueError(f"Sector {key} repetido en el catalogo SCIAN")
            lookup[key] = (sector, grupo)
    return lookup


def classify_scian(df, lookup):
    """Agrega sector y grupo_actividad. Falla si algun codigo_act no esta en el catalogo."""
    prefix = df["codigo_act"].str.strip().str[:2]
    missing = sorted(set(prefix) - set(lookup))
    if missing:
        n = int((~prefix.isin(lookup)).sum())
        raise ValueError(
            f"{n} registros con codigo_act fuera del catalogo SCIAN (sectores {missing}). "
            f"Actualiza {SCIAN_CATALOG.name} antes de continuar."
        )
    out = df.copy()
    out["sector"] = prefix.map(lambda p: lookup[p][0])
    out["grupo_actividad"] = prefix.map(lambda p: lookup[p][1])
    return out


def clean(df):
    report = {"registros_crudos": len(df)}
    out = df.copy()
    dup = int(out["id"].duplicated().sum())
    if dup:
        raise ValueError(f"DENUE contiene {dup} IDs duplicados; no se eliminan registros")
    for c in ["latitud", "longitud"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ["cve_ent", "cve_mun", "cve_loc", "ageb"]:
        out[c] = out[c].fillna("").astype(str).str.strip()
    out["CVEGEO_DENUE"] = (
        out["cve_ent"].str.zfill(2)
        + out["cve_mun"].str.zfill(3)
        + out["cve_loc"].str.zfill(4)
        + out["ageb"].str.zfill(4)
    )
    bad = out[["cve_ent", "cve_mun", "cve_loc", "ageb"]].eq("").any(axis=1) | (
        out["CVEGEO_DENUE"].str.len() != 13
    )
    out.loc[bad, "CVEGEO_DENUE"] = pd.NA
    return out, report


def split_by_coordinates(df, target_crs):
    missing = df.latitud.isna() | df.longitud.isna()
    zero = (df.latitud == 0) | (df.longitud == 0)
    out_of_range = ~df.latitud.between(-90, 90) | ~df.longitud.between(-180, 180)
    valid = ~(missing | zero | out_of_range)
    report = {
        "sin_coordenadas": int(missing.sum()),
        "coordenadas_en_cero": int((zero & ~missing).sum()),
        "coordenadas_fuera_de_rango": int((out_of_range & ~missing & ~zero).sum()),
        "con_coordenadas_utiles": int(valid.sum()),
    }
    pts = gpd.GeoDataFrame(
        df.loc[valid].copy(),
        geometry=gpd.points_from_xy(df.loc[valid, "longitud"], df.loc[valid, "latitud"]),
        crs="EPSG:4326",
    ).to_crs(target_crs)
    return pts, df.loc[~valid].copy(), report


def _first_match(left, right, cols):
    j = gpd.sjoin(left[["geometry"]], right[cols + ["geometry"]], how="left", predicate="within")
    return j[~j.index.duplicated(keep="first")]


def assign_polygons(points, agebs, municipalities):
    jm = _first_match(points, municipalities, ["NOMGEO"])
    ja = _first_match(points, agebs, ["CVEGEO"])
    points["alcaldia_geo"] = jm["NOMGEO"]
    points["CVEGEO"] = ja["CVEGEO"]
    distance_m = points.to_crs(municipalities.crs).geometry.distance(
        municipalities.geometry.union_all()
    )
    near_border = points["cve_ent"].eq(STUDY_ENT_KEY) & distance_m.le(BORDER_TOLERANCE_M)
    inside = points["alcaldia_geo"].notna() | near_border
    points["estatus_asignacion"] = "fuera_cdmx"
    points.loc[inside, "estatus_asignacion"] = "dentro_cdmx_sin_ageb"
    points.loc[points.CVEGEO.notna(), "estatus_asignacion"] = "asignado"
    return points


def build_final(points, invalid, crs):
    invalid = invalid.copy()
    invalid["alcaldia_geo"] = pd.NA
    invalid["CVEGEO"] = pd.NA
    invalid["estatus_asignacion"] = "sin_coordenadas_validas"
    invalid = gpd.GeoDataFrame(
        invalid,
        geometry=gpd.GeoSeries([None] * len(invalid), index=invalid.index, crs=crs),
        crs=crs,
    )
    final = pd.concat([points, invalid]).sort_index()
    return gpd.GeoDataFrame(final, geometry="geometry", crs=crs)


def border_report(final, municipalities):
    """Puntos fuera del poligono de alcaldias: cuantos se toleran y a que distancia estan."""
    out = final[final.alcaldia_geo.isna() & final.geometry.notna()]
    cdmx = municipalities.to_crs(final.crs).union_all()
    dist = out.geometry.distance(cdmx) / 1000
    tol = out.estatus_asignacion != "fuera_cdmx"

    def span(d):
        return (
            {"min": round(float(d.min()), 3), "max": round(float(d.max()), 3)} if len(d) else None
        )

    return {
        "tolerancia_borde_km": BORDER_TOLERANCE_M / 1000,
        "puntos_fuera_del_poligono": int(len(out)),
        "tolerados_como_dentro_cdmx": int(tol.sum()),
        "fuera_cdmx": int((~tol).sum()),
        "distancia_km_tolerados": span(dist[tol]),
        "distancia_km_fuera_cdmx": span(dist[~tol]),
    }


def quality_report(final, report, agebs, municipalities):
    counts = final.estatus_asignacion.value_counts()
    status = {s: int(counts.get(s, 0)) for s in STATUS_ORDER}
    report.update(
        {
            "registros_salida": len(final),
            "estatus_asignacion": status,
            "suma_estatus": sum(status.values()),
        }
    )
    report["reconciliacion_ok"] = (
        report["suma_estatus"] == report["registros_crudos"] == report["registros_salida"]
    )
    a = final[final.estatus_asignacion == "asignado"].copy()
    eq = a.CVEGEO.astype("string") == a.CVEGEO_DENUE.astype("string")
    report["reconciliacion_clave_ageb"] = {
        "registros_asignados": len(a),
        "coinciden": int(eq.fillna(False).sum()),
        "no_coinciden": int((~eq.fillna(False)).sum()),
        "sin_clave_denue": int(a.CVEGEO_DENUE.isna().sum()),
    }
    report["fuera_del_poligono"] = border_report(final, municipalities)
    report["establecimientos_por_grupo_actividad"] = {
        k: int(v) for k, v in final["grupo_actividad"].value_counts().items()
    }
    report["establecimientos_por_sector"] = {
        k: int(v) for k, v in final["sector"].value_counts().sort_index().items()
    }
    report["agebs_con_establecimientos"] = int(a.CVEGEO.nunique())
    report["agebs_sin_establecimientos"] = int(len(set(agebs.CVEGEO) - set(a.CVEGEO.dropna())))
    if not report["reconciliacion_ok"]:
        raise RuntimeError("La reconciliación de estatus no cuadra con el universo DENUE")
    return report


def run(csv_name=DEFAULT_CSV):
    agebs = load_agebs()
    munis = load_municipios()
    df, report = clean(extract(csv_name))
    df = classify_scian(df, load_scian_catalog())
    pts, invalid, rep = split_by_coordinates(df, agebs.crs)
    pts = assign_polygons(pts, agebs, munis)
    final = build_final(pts, invalid, agebs.crs)[OUTPUT_COLUMNS]
    report.update(rep)
    report = quality_report(final, report, agebs, munis)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    gpkg = PROCESSED_DIR / "denue_2026_ageb.gpkg"
    js = PROCESSED_DIR / "denue_2026_reporte_calidad.json"
    gpkg.unlink(missing_ok=True)  # si no, SQLite conserva el tamano de la salida anterior
    final.to_file(gpkg, layer="establecimientos", driver="GPKG")
    js.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Guardado:", gpkg)
    return final, report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=DEFAULT_CSV)
    run(p.parse_args().csv)
