-- ============================================================
-- 02_load.sql
-- Validación y control de carga del Data Warehouse
-- Proyecto: CDMX Urban Intelligence
-- ============================================================

-- Este archivo documenta y valida las cargas realizadas
-- mediante los scripts ETL de Python.
--
-- Las cargas principales se ejecutan con:
--   src/etl/load_dimensions.py
--   src/etl/load_fact_delitos.py
--   src/etl/load_fact_establecimientos.py
--   src/etl/load_fact_poblacion.py


-- ============================================================
-- 1. VALIDACIÓN DE DIMENSIONES
-- ============================================================

SELECT 'dim_geografia' AS tabla, COUNT(*) AS registros
FROM dw.dim_geografia

UNION ALL

SELECT 'dim_fecha', COUNT(*)
FROM dw.dim_fecha

UNION ALL

SELECT 'dim_hora', COUNT(*)
FROM dw.dim_hora

UNION ALL

SELECT 'dim_delito', COUNT(*)
FROM dw.dim_delito

UNION ALL

SELECT 'dim_actividad_economica', COUNT(*)
FROM dw.dim_actividad_economica

UNION ALL

SELECT 'dim_tamano', COUNT(*)
FROM dw.dim_tamano;


-- ============================================================
-- 2. VALIDACIÓN DE TABLAS DE HECHOS
-- ============================================================

SELECT 'fact_delitos' AS tabla, COUNT(*) AS registros
FROM dw.fact_delitos

UNION ALL

SELECT 'fact_poblacion', COUNT(*)
FROM dw.fact_poblacion

UNION ALL

SELECT 'fact_establecimientos', COUNT(*)
FROM dw.fact_establecimientos;


-- ============================================================
-- 3. VALIDACIÓN DE RELACIÓN GEOGRAFÍA
-- ============================================================

SELECT
    COUNT(*) AS fact_poblacion_huerfanos
FROM dw.fact_poblacion p
LEFT JOIN dw.dim_geografia g
    ON p.cvegeo = g.cvegeo
WHERE g.cvegeo IS NULL;


-- ============================================================
-- 4. VALIDACIÓN DE DIMENSIONES DE DELITOS
-- ============================================================

SELECT
    COUNT(*) AS fechas_huerfanas
FROM dw.fact_delitos f
LEFT JOIN dw.dim_fecha d
    ON f.fecha_key = d.fecha_key
WHERE f.fecha_key IS NOT NULL
  AND d.fecha_key IS NULL;


SELECT
    COUNT(*) AS horas_huerfanas
FROM dw.fact_delitos f
LEFT JOIN dw.dim_hora h
    ON f.hora_key = h.hora_key
WHERE f.hora_key IS NOT NULL
  AND h.hora_key IS NULL;


SELECT
    COUNT(*) AS delitos_huerfanos
FROM dw.fact_delitos f
LEFT JOIN dw.dim_delito d
    ON f.delito_key = d.delito_key
WHERE f.delito_key IS NOT NULL
  AND d.delito_key IS NULL;


-- ============================================================
-- 5. VALIDACIÓN DE DIMENSIONES DE ESTABLECIMIENTOS
-- ============================================================

SELECT
    COUNT(*) AS actividades_huerfanas
FROM dw.fact_establecimientos f
LEFT JOIN dw.dim_actividad_economica a
    ON f.actividad_key = a.actividad_key
WHERE f.actividad_key IS NOT NULL
  AND a.actividad_key IS NULL;


SELECT
    COUNT(*) AS tamanos_huerfanos
FROM dw.fact_establecimientos f
LEFT JOIN dw.dim_tamano t
    ON f.tamano_key = t.tamano_key
WHERE f.tamano_key IS NOT NULL
  AND t.tamano_key IS NULL;


-- ============================================================
-- 6. RESUMEN DE POBLACIÓN
-- ============================================================

SELECT
    COUNT(*) AS ageb,
    SUM(pob_total) AS poblacion_total,
    SUM(pob_0_14) AS poblacion_0_14,
    SUM(pob_15_64) AS poblacion_15_64,
    SUM(pob_65_mas) AS poblacion_65_mas,
    SUM(pob_12_mas) AS poblacion_12_mas,
    SUM(pea) AS pea
FROM dw.fact_poblacion;


-- ============================================================
-- 7. RESUMEN DE DELITOS
-- ============================================================

SELECT
    COUNT(*) AS total_registros,
    SUM(incident_count) AS total_incidentes,
    COUNT(*) FILTER (
        WHERE cvegeo IS NOT NULL
    ) AS registros_con_ageb,
    COUNT(*) FILTER (
        WHERE cvegeo IS NULL
    ) AS registros_sin_ageb
FROM dw.fact_delitos;


-- ============================================================
-- 8. RESUMEN DE ESTABLECIMIENTOS
-- ============================================================

SELECT
    COUNT(*) AS total_establecimientos,
    COUNT(*) FILTER (
        WHERE cvegeo IS NOT NULL
    ) AS establecimientos_con_ageb,
    COUNT(*) FILTER (
        WHERE cvegeo IS NULL
    ) AS establecimientos_sin_ageb
FROM dw.fact_establecimientos;