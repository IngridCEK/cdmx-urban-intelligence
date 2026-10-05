"""Carga a PostGIS (esquema `staging`) las salidas del ETL de poligonos y delitos.

Tablas que crea (se reemplazan en cada corrida, por eso es repetible):
    staging.stg_agebs    una fila por AGEB urbana (MultiPolygon)
    staging.stg_delitos  una fila por carpeta de investigacion (Point, nulo si no hay coordenadas)

Son tablas de PASO: el sql/02_load.sql las transforma en las dimensiones y los hechos
del warehouse. Todos los nombres de columna quedan en minusculas (cvegeo, no CVEGEO).
Todas las geometrias se guardan en WORK_CRS (por defecto EPSG:32614, UTM 14N).

Uso (dentro del contenedor, con PostGIS levantado y el ETL de delitos ya corrido):
    python -m src.etl.load_staging
    python -m src.etl.load_staging --delitos delitos_2022_ageb.gpkg
"""
import argparse

import geopandas as gpd
from shapely.geometry import MultiPolygon
from sqlalchemy import text

from src.config import PROCESSED_DIR, WORK_CRS
from src.db import get_engine
from src.geo.polygons import load_agebs, load_municipios

SCHEMA = "staging"
DEFAULT_GPKG = "delitos_2023_ageb.gpkg"
SRID = int(WORK_CRS.split(":")[1])


def _multi(geom):
    """PostGIS exige un solo tipo de geometria por columna: todo MultiPolygon."""
    if geom is None or geom.is_empty:
        return geom
    return MultiPolygon([geom]) if geom.geom_type == "Polygon" else geom


def build_agebs() -> gpd.GeoDataFrame:
    """AGEB urbanas con nombre de alcaldia, area_km2 y geometria en WORK_CRS."""
    agebs = load_agebs()
    munis = load_municipios()

    agebs["cve_mun"] = agebs["CVEGEO"].str[2:5]
    if "CVE_MUN" in munis.columns:
        munis["cve_mun"] = munis["CVE_MUN"].astype(str).str.zfill(3)
    else:
        munis["cve_mun"] = munis["CVEGEO"].astype(str).str[-3:]
    nombres = munis[["cve_mun", "NOMGEO"]].drop_duplicates("cve_mun")

    agebs = agebs.merge(nombres, on="cve_mun", how="left")
    agebs = agebs[["CVEGEO", "cve_mun", "NOMGEO", "area_km2", "geometry"]]
    agebs.columns = [c.lower() for c in agebs.columns]
    agebs = gpd.GeoDataFrame(agebs, geometry="geometry", crs=agebs.crs).to_crs(WORK_CRS)
    agebs["geometry"] = agebs["geometry"].map(_multi)
    return agebs


def build_delitos(gpkg_name: str) -> gpd.GeoDataFrame:
    path = PROCESSED_DIR / gpkg_name
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}. Corre antes: python -m src.etl.crime")
    delitos = gpd.read_file(path, layer="delitos")
    delitos.columns = [c.lower() for c in delitos.columns]
    return delitos.to_crs(WORK_CRS)


def write_table(gdf, name, engine):
    gdf.to_postgis(name, engine, schema=SCHEMA, if_exists="replace", index=False, chunksize=20000)


def add_indexes(engine):
    with engine.begin() as conn:
        conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS stg_agebs_cvegeo_ux ON {SCHEMA}.stg_agebs (cvegeo)"))
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS stg_delitos_cvegeo_ix ON {SCHEMA}.stg_delitos (cvegeo)"))
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS stg_delitos_estatus_ix ON {SCHEMA}.stg_delitos (estatus_asignacion)"))


def validate(engine, n_agebs, n_delitos):
    """Cuenta filas, SRID, geometrias validas y llaves huerfanas. Falla si algo no cuadra."""
    q = lambda sql: conn.execute(text(sql)).scalar()
    with engine.connect() as conn:
        r = {
            "agebs_en_bd": q(f"SELECT COUNT(*) FROM {SCHEMA}.stg_agebs"),
            "delitos_en_bd": q(f"SELECT COUNT(*) FROM {SCHEMA}.stg_delitos"),
            "agebs_srid": q(f"SELECT ST_SRID(geometry) FROM {SCHEMA}.stg_agebs LIMIT 1"),
            "agebs_geom_invalidas": q(f"SELECT COUNT(*) FROM {SCHEMA}.stg_agebs WHERE NOT ST_IsValid(geometry)"),
            "agebs_sin_alcaldia": q(f"SELECT COUNT(*) FROM {SCHEMA}.stg_agebs WHERE nomgeo IS NULL"),
            "delitos_cvegeo_huerfana": q(
                f"SELECT COUNT(*) FROM {SCHEMA}.stg_delitos d "
                f"LEFT JOIN {SCHEMA}.stg_agebs a ON a.cvegeo = d.cvegeo "
                f"WHERE d.cvegeo IS NOT NULL AND a.cvegeo IS NULL"
            ),
        }
        estatus = conn.execute(text(
            f"SELECT estatus_asignacion, COUNT(*) FROM {SCHEMA}.stg_delitos GROUP BY 1 ORDER BY 2 DESC"
        )).all()

    problemas = []
    if r["agebs_en_bd"] != n_agebs:
        problemas.append(f"AGEB en BD ({r['agebs_en_bd']}) != esperado ({n_agebs})")
    if r["delitos_en_bd"] != n_delitos:
        problemas.append(f"Delitos en BD ({r['delitos_en_bd']}) != esperado ({n_delitos})")
    if r["agebs_srid"] != SRID:
        problemas.append(f"SRID de AGEB es {r['agebs_srid']}, se esperaba {SRID}")
    if r["delitos_cvegeo_huerfana"]:
        problemas.append(f"{r['delitos_cvegeo_huerfana']} delitos con CVEGEO que no existe en stg_agebs")
    return r, estatus, problemas


def run(gpkg_name: str = DEFAULT_GPKG):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))

    agebs = build_agebs()
    delitos = build_delitos(gpkg_name)

    write_table(agebs, "stg_agebs", engine)
    write_table(delitos, "stg_delitos", engine)
    add_indexes(engine)

    resultado, estatus, problemas = validate(engine, len(agebs), len(delitos))
    print("Validacion:")
    for k, v in resultado.items():
        print(f"  {k}: {v}")
    print("  estatus_asignacion:", {s: n for s, n in estatus})
    if resultado["agebs_geom_invalidas"]:
        print("  AVISO: hay geometrias invalidas en stg_agebs")
    if resultado["agebs_sin_alcaldia"]:
        print("  AVISO: hay AGEB sin nombre de alcaldia")
    if problemas:
        raise RuntimeError("La carga no cuadra: " + "; ".join(problemas))
    print("Carga completa en el esquema", SCHEMA)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga a PostGIS (staging)")
    parser.add_argument("--delitos", default=DEFAULT_GPKG, help="gpkg dentro de data/processed/")
    run(parser.parse_args().delitos)
