"""Carga y validacion de los poligonos del Marco Geoestadistico (INEGI)."""
import geopandas as gpd

from src.config import RAW_DIR, STUDY_ENT, WORK_CRS


def _geo_dir():
    """Busca data/raw/<ENT>_*/conjunto_de_datos (p. ej. 09_ciudaddemexico)."""
    matches = sorted(RAW_DIR.glob(f"{STUDY_ENT}_*/conjunto_de_datos"))
    if not matches:
        raise FileNotFoundError(
            f"No se encontro data/raw/{STUDY_ENT}_*/conjunto_de_datos. "
            "Descomprime el zip del Marco Geoestadistico en data/raw/."
        )
    return matches[0]


def _read_layer(suffix: str) -> gpd.GeoDataFrame:
    path = _geo_dir() / f"{STUDY_ENT}{suffix}.shp"
    if not path.exists():
        raise FileNotFoundError(f"No existe la capa {path}")
    return gpd.read_file(path)


def load_agebs() -> gpd.GeoDataFrame:
    """AGEB urbanas con geometria valida, CVEGEO unica (13 caracteres) y area_km2."""
    agebs = _read_layer("a")

    invalid = int((~agebs.is_valid).sum())
    if invalid:
        agebs["geometry"] = agebs.make_valid()

    if not agebs["CVEGEO"].is_unique:
        raise ValueError("CVEGEO duplicada en la capa de AGEB")
    if not (agebs["CVEGEO"].str.len() == 13).all():
        raise ValueError("Hay CVEGEO que no tienen 13 caracteres")

    agebs["area_km2"] = agebs.to_crs(WORK_CRS).area / 1e6
    agebs.attrs["geometrias_corregidas"] = invalid
    return agebs


def load_municipios() -> gpd.GeoDataFrame:
    """Alcaldias (municipios) con geometria valida."""
    munis = _read_layer("mun")
    if (~munis.is_valid).any():
        munis["geometry"] = munis.make_valid()
    return munis
