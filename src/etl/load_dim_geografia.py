import geopandas as gpd
from sqlalchemy import text

from src.db import get_engine


AGEB_PATH = "/work/data/raw/09_ciudaddemexico/conjunto_de_datos/09a.shp"
MUN_PATH = "/work/data/raw/09_ciudaddemexico/conjunto_de_datos/09mun.shp"


def main():
    print("Leyendo AGEB urbanas...")
    ageb = gpd.read_file(AGEB_PATH)

    print("Leyendo alcaldias...")
    municipios = gpd.read_file(MUN_PATH)

    # Agregar el nombre de la alcaldia usando CVE_ENT + CVE_MUN.
    municipios = municipios[
        ["CVE_ENT", "CVE_MUN", "NOMGEO"]
    ].drop_duplicates()

    ageb = ageb.merge(
        municipios,
        on=["CVE_ENT", "CVE_MUN"],
        how="left"
    )

    print(f"AGEB leidas: {len(ageb)}")

    # El DW almacena las geometrías en EPSG:32614.
    ageb = ageb.to_crs(epsg=32614)

    # Asegurar MultiPolygon para coincidir con el esquema PostGIS.
    ageb["geometry"] = ageb.geometry.apply(
        lambda geom: geom
        if geom.geom_type == "MultiPolygon"
        else __import__("shapely").geometry.MultiPolygon([geom])
    )

    # Calcular area después de reproyectar a metros.
    ageb["area_km2"] = ageb.geometry.area / 1_000_000

    insert_sql = text("""
        INSERT INTO dw.dim_geografia
            (CVEGEO, NOMGEO, area_km2, geometry)
        VALUES
            (
                :cvegeo,
                :nomgeo,
                :area_km2,
                ST_Multi(
                    ST_GeomFromText(:geometry_wkt, 32614)
                )
            )
        ON CONFLICT (CVEGEO) DO UPDATE SET
            NOMGEO = EXCLUDED.NOMGEO,
            area_km2 = EXCLUDED.area_km2,
            geometry = EXCLUDED.geometry
    """)

    print("Insertando dim_geografia...")

    engine = get_engine()

    with engine.begin() as conn:
        for _, row in ageb.iterrows():
            conn.execute(
                insert_sql,
                {
                    "cvegeo": str(row["CVEGEO"]),
                    "nomgeo": row["NOMGEO"],
                    "area_km2": float(row["area_km2"]),
                    "geometry_wkt": row["geometry"].wkt,
                }
            )

    print(f"Carga de dim_geografia completada: {len(ageb)} registros.")


if __name__ == "__main__":
    main()
