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

    COALESCE(p.pob_total, 0) AS poblacion_total,
    COALESCE(p.pob_0_14, 0) AS poblacion_0_14,
    COALESCE(p.pob_15_64, 0) AS poblacion_15_64,
    COALESCE(p.pob_65_mas, 0) AS poblacion_65_mas,
    COALESCE(p.pea, 0) AS pea,

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
        ELSE 0
    END AS delitos_por_1000_habitantes,

    CASE
        WHEN g.area_km2 > 0
        THEN ROUND(
            COALESCE(d.total_incidentes, 0)::numeric
            / g.area_km2,
            2
        )
        ELSE 0
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