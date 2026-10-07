-- ============================================================
-- 03_views.sql
-- Vistas analíticas y KPIs del proyecto
-- CDMX Urban Intelligence
-- ============================================================


-- ============================================================
-- 1. Delitos por AGEB
-- ============================================================

DROP VIEW IF EXISTS dw.vw_delitos_por_ageb;

CREATE VIEW dw.vw_delitos_por_ageb AS
SELECT
    g.cvegeo,
    g.nomgeo,
    COUNT(f.delito_fact_key) AS total_delitos,
    SUM(f.incident_count) AS total_incidentes,
    COUNT(DISTINCT f.delito_key) AS tipos_delito,
    COUNT(DISTINCT f.fecha_key) AS dias_con_delitos
FROM dw.dim_geografia g
LEFT JOIN dw.fact_delitos f
    ON g.cvegeo = f.cvegeo
GROUP BY
    g.cvegeo,
    g.nomgeo;


-- ============================================================
-- 2. Población por AGEB
-- ============================================================

DROP VIEW IF EXISTS dw.vw_poblacion_por_ageb;

CREATE VIEW dw.vw_poblacion_por_ageb AS
SELECT
    g.cvegeo,
    g.nomgeo,
    p.pob_total,
    p.pob_0_14,
    p.pob_15_64,
    p.pob_65_mas,
    p.pob_12_mas,
    p.pea,
    p.fuente,
    p.fecha_corte
FROM dw.dim_geografia g
LEFT JOIN dw.fact_poblacion p
    ON g.cvegeo = p.cvegeo;


-- ============================================================
-- 3. Establecimientos por AGEB
-- ============================================================

DROP VIEW IF EXISTS dw.vw_establecimientos_por_ageb;

CREATE VIEW dw.vw_establecimientos_por_ageb AS
SELECT
    g.cvegeo,
    g.nomgeo,
    COUNT(e.establecimiento_key) AS total_establecimientos,
    COUNT(DISTINCT e.actividad_key) AS actividades_economicas,
    COUNT(DISTINCT e.tamano_key) AS tamanos_registrados
FROM dw.dim_geografia g
LEFT JOIN dw.fact_establecimientos e
    ON g.cvegeo = e.cvegeo
GROUP BY
    g.cvegeo,
    g.nomgeo;


-- ============================================================
-- 4. Resumen integrado por AGEB
-- ============================================================
--
-- Importante:
-- Cada hecho se agrega primero por CVEGEO.
-- Después se unen los resultados para evitar
-- multiplicar registros por joins entre tablas de hechos.
-- ============================================================

DROP VIEW IF EXISTS dw.vw_resumen_ageb;

CREATE VIEW dw.vw_resumen_ageb AS
WITH delitos AS (
    SELECT
        cvegeo,
        COUNT(*) AS total_delitos,
        SUM(incident_count) AS total_incidentes
    FROM dw.fact_delitos
    WHERE cvegeo IS NOT NULL
    GROUP BY cvegeo
),
establecimientos AS (
    SELECT
        cvegeo,
        COUNT(*) AS total_establecimientos
    FROM dw.fact_establecimientos
    WHERE cvegeo IS NOT NULL
    GROUP BY cvegeo
)
SELECT
    g.cvegeo,
    g.nomgeo,
    g.area_km2,

    p.pob_total AS poblacion_total,
    p.pob_0_14 AS poblacion_0_14,
    p.pob_15_64 AS poblacion_15_64,
    p.pob_65_mas AS poblacion_65_mas,
    p.pea AS pea,

    COALESCE(d.total_delitos, 0) AS total_delitos,
    COALESCE(d.total_incidentes, 0) AS total_incidentes,

    COALESCE(e.total_establecimientos, 0) AS total_establecimientos,

    CASE
        WHEN COALESCE(p.pob_total, 0) > 0
        THEN ROUND(
            COALESCE(d.total_incidentes, 0)::numeric
            / p.pob_total * 1000,
            2
        )
        ELSE NULL
    END AS delitos_por_1000_habitantes,

    CASE
        WHEN g.area_km2 > 0
        THEN ROUND(
            COALESCE(d.total_incidentes, 0)::numeric
            / g.area_km2,
            2
        )
        ELSE NULL
    END AS delitos_por_km2

FROM dw.dim_geografia g
LEFT JOIN dw.fact_poblacion p
    ON g.cvegeo = p.cvegeo
LEFT JOIN delitos d
    ON g.cvegeo = d.cvegeo
LEFT JOIN establecimientos e
    ON g.cvegeo = e.cvegeo;


-- ============================================================
-- 5. Delitos por categoría
-- ============================================================

DROP VIEW IF EXISTS dw.vw_delitos_por_categoria;

CREATE VIEW dw.vw_delitos_por_categoria AS
SELECT
    categoria_delito,
    COUNT(*) AS total_delitos
FROM dw.fact_delitos
GROUP BY categoria_delito
ORDER BY total_delitos DESC;


-- ============================================================
-- 6. Delitos por hora
-- ============================================================

DROP VIEW IF EXISTS dw.vw_delitos_por_hora;

CREATE VIEW dw.vw_delitos_por_hora AS
SELECT
    h.hora,
    h.franja_horaria,
    h.parte_dia,
    COUNT(f.delito_fact_key) AS total_delitos
FROM dw.dim_hora h
LEFT JOIN dw.fact_delitos f
    ON h.hora_key = f.hora_key
GROUP BY
    h.hora,
    h.franja_horaria,
    h.parte_dia
ORDER BY h.hora;


-- ============================================================
-- 7. Delitos por fecha
-- ============================================================

DROP VIEW IF EXISTS dw.vw_delitos_por_fecha;

CREATE VIEW dw.vw_delitos_por_fecha AS
SELECT
    d.fecha,
    d.mes,
    d.nombre_mes,
    d.trimestre,
    d.anio,
    COUNT(f.delito_fact_key) AS total_delitos
FROM dw.dim_fecha d
LEFT JOIN dw.fact_delitos f
    ON d.fecha_key = f.fecha_key
GROUP BY
    d.fecha,
    d.mes,
    d.nombre_mes,
    d.trimestre,
    d.anio
ORDER BY d.fecha;

-- ============================================================
-- 8. KPIs integrados por AGEB
-- Los hechos se agregan por separado antes de combinarse.
-- Tasas sin denominador valido devuelven NULL, no cero.
-- ============================================================

DROP VIEW IF EXISTS dw.vw_kpi_ageb;

CREATE VIEW dw.vw_kpi_ageb AS
WITH delitos AS (
    SELECT CVEGEO, SUM(incident_count) AS total_crime_incidents
    FROM dw.fact_delitos
    WHERE CVEGEO IS NOT NULL
    GROUP BY CVEGEO
),
negocios AS (
    SELECT
        e.CVEGEO,
        COUNT(*) AS total_businesses,
        COUNT(*) FILTER (WHERE a.clasificacion = 'comercio al por menor') AS retail_businesses,
        COUNT(*) FILTER (WHERE a.clasificacion = 'servicios') AS service_businesses
    FROM dw.fact_establecimientos e
    LEFT JOIN dw.dim_actividad_economica a ON a.actividad_key = e.actividad_key
    WHERE e.CVEGEO IS NOT NULL
    GROUP BY e.CVEGEO
),
sector_counts AS (
    SELECT e.CVEGEO, a.sector_scian, COUNT(*) AS n
    FROM dw.fact_establecimientos e
    JOIN dw.dim_actividad_economica a ON a.actividad_key = e.actividad_key
    WHERE e.CVEGEO IS NOT NULL
    GROUP BY e.CVEGEO, a.sector_scian
),
sector_rank AS (
    SELECT
        CVEGEO,
        sector_scian,
        ROW_NUMBER() OVER (
            PARTITION BY CVEGEO
            ORDER BY n DESC, sector_scian ASC
        ) AS rn
    FROM sector_counts
)
SELECT
    g.CVEGEO,
    g.NOMGEO,
    g.area_km2,
    COALESCE(d.total_crime_incidents, 0) AS total_crime_incidents,
    p.pob_total AS total_population,
    p.pob_0_14,
    p.pob_15_64,
    p.pob_65_mas,
    p.pob_12_mas,
    p.pea,
    COALESCE(n.total_businesses, 0) AS total_businesses,
    COALESCE(n.retail_businesses, 0) AS retail_businesses,
    COALESCE(n.service_businesses, 0) AS service_businesses,
    CASE WHEN p.pob_total > 0
         THEN ROUND(COALESCE(d.total_crime_incidents, 0)::numeric / p.pob_total * 1000, 2)
         ELSE NULL END AS crime_rate_per_1000,
    CASE WHEN g.area_km2 > 0 AND p.pob_total IS NOT NULL
         THEN ROUND(p.pob_total::numeric / g.area_km2, 2)
         ELSE NULL END AS population_density,
    CASE WHEN g.area_km2 > 0
         THEN ROUND(COALESCE(n.total_businesses, 0)::numeric / g.area_km2, 2)
         ELSE NULL END AS business_density,
    CASE WHEN g.area_km2 > 0
         THEN ROUND(COALESCE(n.retail_businesses, 0)::numeric / g.area_km2, 2)
         ELSE NULL END AS retail_density,
    CASE WHEN g.area_km2 > 0
         THEN ROUND(COALESCE(n.service_businesses, 0)::numeric / g.area_km2, 2)
         ELSE NULL END AS service_density,
    CASE WHEN p.pob_12_mas > 0 AND p.pea IS NOT NULL
         THEN ROUND(p.pea::numeric / p.pob_12_mas * 100, 2)
         ELSE NULL END AS economically_active_population_rate,
    CASE WHEN p.pob_total > 0
         THEN ROUND(COALESCE(n.total_businesses, 0)::numeric / p.pob_total * 1000, 2)
         ELSE NULL END AS businesses_per_1000_residents,
    COALESCE(sr.sector_scian, 'sin_establecimientos') AS dominant_economic_activity,
    CASE WHEN COALESCE(n.total_businesses, 0) > 0
         THEN ROUND(COALESCE(d.total_crime_incidents, 0)::numeric / n.total_businesses, 4)
         ELSE NULL END AS crime_per_business
FROM dw.dim_geografia g
LEFT JOIN dw.fact_poblacion p ON p.CVEGEO = g.CVEGEO
LEFT JOIN delitos d ON d.CVEGEO = g.CVEGEO
LEFT JOIN negocios n ON n.CVEGEO = g.CVEGEO
LEFT JOIN sector_rank sr ON sr.CVEGEO = g.CVEGEO AND sr.rn = 1;
