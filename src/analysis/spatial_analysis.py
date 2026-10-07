"""Analisis espacial final - Fase 3.

Lee los indicadores directamente del Data Warehouse PostgreSQL/PostGIS
y realiza:
1. Correlaciones de Spearman.
2. Moran Global para dos indicadores.
3. Moran Local (LISA).
4. Moran Bivariado.
5. Exportacion de resultados, figuras y mapas.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from esda.moran import Moran, Moran_BV, Moran_Local
from libpysal.weights import Queen
from scipy.stats import spearmanr
from sqlalchemy import create_engine

from src.config import DB_URL, ROOT


# ---------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------

FIGURES_DIR = ROOT / "outputs" / "figures"
MAPS_DIR = ROOT / "outputs" / "maps"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
MAPS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
PERMUTATIONS = 999


# ---------------------------------------------------------------------
# Carga de datos desde PostgreSQL/PostGIS
# ---------------------------------------------------------------------

def load_kpis():
    """Carga KPIs y geometria de las AGEB desde el Data Warehouse."""

    engine = create_engine(DB_URL)

    query = """
        SELECT
            k.cvegeo,
            k.nomgeo,
            k.total_crime_incidents,
            k.total_population,
            k.total_businesses,
            k.crime_rate_per_1000,
            k.population_density,
            k.business_density,
            k.economically_active_population_rate,
            k.businesses_per_1000_residents,
            g.geometry
        FROM dw.vw_kpi_ageb AS k
        INNER JOIN dw.dim_geografia AS g
            ON k.cvegeo = g.cvegeo
        ORDER BY k.cvegeo;
    """

    gdf = gpd.read_postgis(
        query,
        engine,
        geom_col="geometry",
        crs="EPSG:32614",
    )

    numeric_cols = [
        "total_crime_incidents",
        "total_population",
        "total_businesses",
        "crime_rate_per_1000",
        "population_density",
        "business_density",
        "economically_active_population_rate",
        "businesses_per_1000_residents",
    ]

    for col in numeric_cols:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce")

    engine.dispose()

    return gdf


# ---------------------------------------------------------------------
# Correlaciones
# ---------------------------------------------------------------------

def calculate_correlations(gdf):
    """Calcula tres relaciones usando correlacion de Spearman."""

    relationships = [
        (
            "crime_rate_per_1000",
            "business_density",
            "Tasa de delitos vs densidad de establecimientos",
        ),
        (
            "crime_rate_per_1000",
            "population_density",
            "Tasa de delitos vs densidad de poblacion",
        ),
        (
            "business_density",
            "population_density",
            "Densidad de establecimientos vs densidad de poblacion",
        ),
    ]

    results = []

    print("\n=== CORRELACIONES DE SPEARMAN ===")

    for x, y, description in relationships:

        data = gdf[[x, y]].dropna()

        rho, p_value = spearmanr(
            data[x],
            data[y],
        )

        results.append(
            {
                "relationship": description,
                "x": x,
                "y": y,
                "n": len(data),
                "spearman_rho": rho,
                "p_value": p_value,
            }
        )

        print(
            f"{description}: "
            f"rho={rho:.4f}, "
            f"p={p_value:.6g}, "
            f"n={len(data)}"
        )

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        FIGURES_DIR / "correlaciones_spearman.csv",
        index=False,
    )

    return results_df


# ---------------------------------------------------------------------
# Pesos espaciales Queen
# ---------------------------------------------------------------------

def build_spatial_weights(gdf):
    """
    Construye Queen usando solamente AGEB con datos validos
    para las variables utilizadas en Moran.

    Los valores NULL no se convierten a cero porque NULL significa
    que el indicador no puede calcularse, no ausencia del fenomeno.
    """

    required_variables = [
        "crime_rate_per_1000",
        "business_density",
    ]

    # Eliminar solamente las observaciones que no tienen los KPI
    # necesarios para el analisis espacial.
    spatial_gdf = (
        gdf.dropna(subset=required_variables)
        .copy()
        .reset_index(drop=True)
    )

    excluded_nulls = len(gdf) - len(spatial_gdf)

    print("\n=== VECINDAD ESPACIAL ===")
    print(f"AGEB totales: {len(gdf)}")
    print(f"AGEB excluidas por KPI nulo: {excluded_nulls}")

    # Construccion inicial para detectar islas dentro de la
    # muestra estadistica valida.
    w_initial = Queen.from_dataframe(
        spatial_gdf,
        use_index=False,
        silence_warnings=True,
    )

    islands = list(w_initial.islands)

    print(f"Islas Queen: {len(islands)}")

    if islands:

        island_codes = (
            spatial_gdf
            .iloc[islands]["cvegeo"]
            .tolist()
        )

        print(
            "CVEGEO de islas:",
            ", ".join(island_codes),
        )

        mask = np.ones(
            len(spatial_gdf),
            dtype=bool,
        )

        mask[islands] = False

        spatial_gdf = (
            spatial_gdf.loc[mask]
            .copy()
            .reset_index(drop=True)
        )

    # Reconstruir la matriz despues de retirar las islas.
    w = Queen.from_dataframe(
        spatial_gdf,
        use_index=False,
        silence_warnings=True,
    )

    # Pesos estandarizados por fila.
    w.transform = "R"

    print(
        f"AGEB usadas en Moran/LISA: "
        f"{len(spatial_gdf)}"
    )

    print(
        f"Vecinos promedio: "
        f"{w.mean_neighbors:.2f}"
    )

    print(
        f"Componentes conectados: "
        f"{w.n_components}"
    )

    # Comprobacion adicional.
    if w.islands:
        print(
            "Advertencia: despues del filtrado "
            f"permanecen {len(w.islands)} islas."
        )

    return spatial_gdf, w


# ---------------------------------------------------------------------
# Moran Global
# ---------------------------------------------------------------------

def calculate_global_moran(gdf, w):
    """Calcula Moran Global para dos indicadores."""

    indicators = [
        "crime_rate_per_1000",
        "business_density",
    ]

    results = []

    print("\n=== MORAN GLOBAL ===")

    for indicator in indicators:

        values = gdf[indicator].to_numpy()

        if np.isnan(values).any():
            raise ValueError(
                f"{indicator} contiene valores nulos "
                "despues del filtrado."
            )

        moran = Moran(
            values,
            w,
            permutations=PERMUTATIONS,
        )

        results.append(
            {
                "indicator": indicator,
                "n": len(values),
                "moran_i": moran.I,
                "expected_i": moran.EI,
                "p_sim": moran.p_sim,
                "z_sim": moran.z_sim,
                "permutations": PERMUTATIONS,
            }
        )

        print(
            f"{indicator}: "
            f"I={moran.I:.4f}, "
            f"E[I]={moran.EI:.4f}, "
            f"p_sim={moran.p_sim:.4f}, "
            f"n={len(values)}"
        )

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        FIGURES_DIR / "moran_global.csv",
        index=False,
    )

    return results_df


# ---------------------------------------------------------------------
# Moran Local / LISA
# ---------------------------------------------------------------------

def calculate_lisa(gdf, w):
    """
    Calcula Moran Local para la tasa de delitos y clasifica
    clusters HH, LH, LL y HL con p < 0.05.
    """

    variable = "crime_rate_per_1000"

    lisa = Moran_Local(
        gdf[variable].to_numpy(),
        w,
        permutations=PERMUTATIONS,
        seed=RANDOM_SEED,
    )

    result = gdf.copy()

    result["lisa_i"] = lisa.Is
    result["lisa_p"] = lisa.p_sim
    result["lisa_quadrant"] = lisa.q

    labels = {
        1: "HH",
        2: "LH",
        3: "LL",
        4: "HL",
    }

    result["lisa_cluster"] = [
        labels.get(q, "NS")
        if p < 0.05
        else "NS"
        for q, p in zip(
            lisa.q,
            lisa.p_sim,
        )
    ]

    print(
        "\n=== LISA: "
        "TASA DE DELITOS ==="
    )

    print(
        result["lisa_cluster"]
        .value_counts()
        .to_string()
    )

    # Guardar resultados tabulares.
    result[
        [
            "cvegeo",
            variable,
            "lisa_i",
            "lisa_p",
            "lisa_quadrant",
            "lisa_cluster",
        ]
    ].to_csv(
        FIGURES_DIR / "lisa_crime_rate.csv",
        index=False,
    )

    # Mapa LISA.
    fig, ax = plt.subplots(
        figsize=(9, 9)
    )

    result.plot(
        column="lisa_cluster",
        categorical=True,
        legend=True,
        ax=ax,
        edgecolor="white",
        linewidth=0.15,
        missing_kwds={
            "label": "Sin datos"
        },
    )

    ax.set_title(
        "LISA - Tasa de delitos por 1,000 habitantes\n"
        "Contigüidad Queen, p < 0.05"
    )

    ax.set_axis_off()

    fig.tight_layout()

    fig.savefig(
        MAPS_DIR / "lisa_crime_rate.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    return result


# ---------------------------------------------------------------------
# Moran Bivariado
# ---------------------------------------------------------------------

def calculate_bivariate_moran(gdf, w):
    """
    Calcula Moran bivariado entre la tasa de delitos de una AGEB
    y el rezago espacial de la densidad de establecimientos.
    """

    x_name = "crime_rate_per_1000"
    y_name = "business_density"

    x = gdf[x_name].to_numpy()
    y = gdf[y_name].to_numpy()

    moran_bv = Moran_BV(
        x,
        y,
        w,
        permutations=PERMUTATIONS,
    )

    print("\n=== MORAN BIVARIADO ===")

    print(
        "Tasa de delitos vs rezago espacial de "
        "densidad de establecimientos: "
        f"I={moran_bv.I:.4f}, "
        f"p_sim={moran_bv.p_sim:.4f}, "
        f"n={len(gdf)}"
    )

    result = pd.DataFrame(
        [
            {
                "x": x_name,
                "spatial_lag_y": y_name,
                "n": len(gdf),
                "moran_bivariate_i": moran_bv.I,
                "p_sim": moran_bv.p_sim,
                "permutations": PERMUTATIONS,
            }
        ]
    )

    result.to_csv(
        FIGURES_DIR / "moran_bivariado.csv",
        index=False,
    )

    return result


# ---------------------------------------------------------------------
# Mapas descriptivos
# ---------------------------------------------------------------------

def create_descriptive_maps(gdf):
    """Genera mapas descriptivos de tres indicadores principales."""

    variables = [
        (
            "crime_rate_per_1000",
            "Tasa de delitos por 1,000 habitantes",
            "crime_rate_per_1000.png",
        ),
        (
            "business_density",
            "Densidad de establecimientos por km2",
            "business_density.png",
        ),
        (
            "population_density",
            "Densidad de poblacion por km2",
            "population_density.png",
        ),
    ]

    print("\n=== MAPAS DESCRIPTIVOS ===")

    for variable, title, filename in variables:

        fig, ax = plt.subplots(
            figsize=(9, 9)
        )

        gdf.plot(
            column=variable,
            legend=True,
            ax=ax,
            edgecolor="white",
            linewidth=0.15,
            missing_kwds={
                "label": "Sin datos"
            },
        )

        ax.set_title(title)
        ax.set_axis_off()

        fig.tight_layout()

        output_path = (
            MAPS_DIR / filename
        )

        fig.savefig(
            output_path,
            dpi=180,
            bbox_inches="tight",
        )

        plt.close(fig)

        print(
            f"Mapa generado: {filename}"
        )


# ---------------------------------------------------------------------
# Resumen de resultados
# ---------------------------------------------------------------------

def save_analysis_summary(
    gdf,
    spatial_gdf,
    correlations,
    global_moran,
    bivariate_moran,
):
    """Guarda un resumen general de la ejecucion."""

    summary = {
        "total_agebs_dw": len(gdf),
        "agebs_spatial_analysis": len(spatial_gdf),
        "excluded_from_spatial_analysis": (
            len(gdf) - len(spatial_gdf)
        ),
        "spatial_rule": (
            "Queen de primer orden, "
            "pesos estandarizados por fila"
        ),
        "permutations": PERMUTATIONS,
        "significance_level_lisa": 0.05,
        "correlations_calculated": len(correlations),
        "global_moran_indicators": len(global_moran),
        "bivariate_moran_calculated": len(bivariate_moran),
        "note": (
            "La asociacion espacial y las correlaciones "
            "no implican causalidad."
        ),
    }

    summary_df = pd.DataFrame(
        list(summary.items()),
        columns=["metric", "value"],
    )

    summary_df.to_csv(
        FIGURES_DIR / "analysis_summary.csv",
        index=False,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    np.random.seed(RANDOM_SEED)

    print(
        "=== ANALISIS ESPACIAL - FASE 3 ==="
    )

    # 1. Cargar Data Warehouse.
    gdf = load_kpis()

    print(
        f"\nAGEB cargadas desde el DW: "
        f"{len(gdf)}"
    )

    print(
        f"CRS: {gdf.crs}"
    )

    # 2. Correlaciones.
    correlations = (
        calculate_correlations(gdf)
    )

    # 3. Muestra espacial y pesos Queen.
    spatial_gdf, w = (
        build_spatial_weights(gdf)
    )

    # 4. Moran Global.
    global_moran = (
        calculate_global_moran(
            spatial_gdf,
            w,
        )
    )

    # 5. LISA.
    calculate_lisa(
        spatial_gdf,
        w,
    )

    # 6. Moran bivariado.
    bivariate_moran = (
        calculate_bivariate_moran(
            spatial_gdf,
            w,
        )
    )

    # 7. Mapas descriptivos.
    create_descriptive_maps(gdf)

    # 8. Resumen reproducible.
    save_analysis_summary(
        gdf,
        spatial_gdf,
        correlations,
        global_moran,
        bivariate_moran,
    )

    print(
        "\n=== ANALISIS COMPLETADO ==="
    )

    print(
        f"Figuras/tablas: "
        f"{FIGURES_DIR}"
    )

    print(
        f"Mapas: "
        f"{MAPS_DIR}"
    )

    print(
        "\nNota: correlacion y asociacion "
        "espacial no implican causalidad."
    )


if __name__ == "__main__":
    main()