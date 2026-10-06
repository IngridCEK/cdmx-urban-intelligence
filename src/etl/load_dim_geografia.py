"""Carga dim_geografia con las AGEB urbanas y alcaldias de Persona A."""

import geopandas as gpd
from shapely.geometry import MultiPolygon
from sqlalchemy import text

from src.config import RAW_DIR
from src.db import get_engine

GEO_DIR = RAW_DIR / "09_ciudaddemexico" / "conjunto_de_datos"
AGEB_PATH = GEO_DIR / "09a.shp"
MUN_PATH = GEO_DIR / "09mun.shp"


def run():
    if not AGEB_PATH.exists() or not MUN_PATH.exists():
        raise FileNotFoundError(f"No se encontraron las capas geograficas en {GEO_DIR}")

    print("Leyendo AGEB urbanas y alcaldias...")
    ageb = gpd.read_file(AGEB_PATH)
    municipios = gpd.read_file(MUN_PATH)[["CVE_ENT", "CVE_MUN", "NOMGEO"]].drop_duplicates()

    ageb = ageb.merge(municipios, on=["CVE_ENT", "CVE_MUN"], how="left")
    if ageb["CVEGEO"].duplicated().any():
        raise ValueError("La capa de AGEB contiene CVEGEO duplicados")

    ageb = ageb.to_crs(epsg=32614)
    ageb["geometry"] = ageb.geometry.apply(
        lambda geom: geom if geom.geom_type == "MultiPolygon" else MultiPolygon([geom])
    )
    ageb["area_km2"] = ageb.geometry.area / 1_000_000

    rows = [
        {
            "cvegeo": str(row.CVEGEO),
            "nomgeo": row.NOMGEO,
            "area_km2": float(row.area_km2),
            "geometry_wkt": row.geometry.wkt,
        }
        for row in ageb.itertuples(index=False)
    ]

    sql = text("""
        INSERT INTO dw.dim_geografia (CVEGEO, NOMGEO, area_km2, geometry)
        VALUES (
            :cvegeo, :nomgeo, :area_km2,
            ST_Multi(ST_GeomFromText(:geometry_wkt, 32614))
        )
        ON CONFLICT (CVEGEO) DO UPDATE SET
            NOMGEO = EXCLUDED.NOMGEO,
            area_km2 = EXCLUDED.area_km2,
            geometry = EXCLUDED.geometry
    """)

    with get_engine().begin() as conn:
        conn.execute(sql, rows)

    print(f"Carga de dim_geografia completada: {len(rows)} registros.")


if __name__ == "__main__":
    run()
