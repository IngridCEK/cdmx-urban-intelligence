-- ============================================================
-- 01_schema.sql
-- Esquema del Data Warehouse: CDMX Urban Intelligence
-- ============================================================

CREATE SCHEMA IF NOT EXISTS dw;


-- ============================================================
-- DIMENSION: GEOGRAFIA
-- GRANO: una fila por AGEB urbana de la Ciudad de Mexico.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.dim_geografia (
    CVEGEO      VARCHAR(13) PRIMARY KEY,
    NOMGEO      VARCHAR(150),
    area_km2    NUMERIC(12,6),
    geometry    geometry(MultiPolygon, 32614)
);

CREATE INDEX IF NOT EXISTS idx_dim_geografia_geometry
    ON dw.dim_geografia
    USING GIST (geometry);


-- ============================================================
-- DIMENSION: FECHA
-- GRANO: una fila por fecha calendario.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.dim_fecha (
    fecha_key       INTEGER PRIMARY KEY,
    fecha           DATE NOT NULL UNIQUE,
    dia             INTEGER NOT NULL,
    mes             INTEGER NOT NULL,
    nombre_mes      VARCHAR(20) NOT NULL,
    trimestre       INTEGER NOT NULL,
    anio            INTEGER NOT NULL
);

ALTER TABLE dw.dim_fecha
    ADD CONSTRAINT chk_dim_fecha_mes
    CHECK (mes BETWEEN 1 AND 12);

ALTER TABLE dw.dim_fecha
    ADD CONSTRAINT chk_dim_fecha_trimestre
    CHECK (trimestre BETWEEN 1 AND 4);


-- ============================================================
-- DIMENSION: HORA
-- GRANO: una fila por hora del dia (0-23).
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.dim_hora (
    hora_key        INTEGER PRIMARY KEY,
    hora            INTEGER NOT NULL UNIQUE,
    franja_horaria  VARCHAR(30) NOT NULL,
    parte_dia       VARCHAR(20) NOT NULL
);

ALTER TABLE dw.dim_hora
    ADD CONSTRAINT chk_dim_hora_hora
    CHECK (hora BETWEEN 0 AND 23);


-- ============================================================
-- DIMENSION: DELITO
-- GRANO: una fila por combinacion de categoria y tipo de delito.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.dim_delito (
    delito_key          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria_delito    VARCHAR(200),
    delito              VARCHAR(300),

    CONSTRAINT uq_dim_delito
        UNIQUE (categoria_delito, delito)
);


-- ============================================================
-- DIMENSION: ACTIVIDAD ECONOMICA
-- GRANO: una fila por clasificacion economica SCIAN.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.dim_actividad_economica (
    actividad_key       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_act          VARCHAR(10) NOT NULL UNIQUE,
    nombre_act          VARCHAR(300),
    sector_scian        VARCHAR(2),
    subsector_scian     VARCHAR(3),
    sector_economico    VARCHAR(100),
    clasificacion       VARCHAR(30)
);


-- ============================================================
-- DIMENSION: TAMANO
-- GRANO: una fila por categoria de tamano de establecimiento.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.dim_tamano (
    tamano_key          INTEGER PRIMARY KEY,
    categoria_tamano    VARCHAR(50) NOT NULL UNIQUE,
    descripcion         VARCHAR(200)
);


-- ============================================================
-- FACT: DELITOS
-- GRANO: una fila por carpeta de investigacion / incidente.
-- Se conservan TODOS los registros del origen FGJ.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.fact_delitos (
    delito_fact_key         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_id               VARCHAR(100) NOT NULL UNIQUE,

    fecha_inicio            TIMESTAMP,
    fecha_hecho             TIMESTAMP,
    hora_hecho              TIME,
    hora                    INTEGER,

    fecha_key               INTEGER,
    hora_key                INTEGER,
    delito_key              INTEGER,
    CVEGEO                  VARCHAR(13),

    delito                  VARCHAR(300),
    categoria_delito        VARCHAR(200),

    alcaldia_catalogo       VARCHAR(150),
    alcaldia_geo            VARCHAR(150),

    latitud                 NUMERIC(10,7),
    longitud                NUMERIC(10,7),

    estatus_asignacion      VARCHAR(40) NOT NULL,

    geometry                geometry(Point, 32614),

    incident_count          INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT fk_fact_delitos_geografia
        FOREIGN KEY (CVEGEO)
        REFERENCES dw.dim_geografia(CVEGEO),

    CONSTRAINT fk_fact_delitos_fecha
        FOREIGN KEY (fecha_key)
        REFERENCES dw.dim_fecha(fecha_key),

    CONSTRAINT fk_fact_delitos_hora
        FOREIGN KEY (hora_key)
        REFERENCES dw.dim_hora(hora_key),

    CONSTRAINT fk_fact_delitos_delito
        FOREIGN KEY (delito_key)
        REFERENCES dw.dim_delito(delito_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_delitos_cvegeo
    ON dw.fact_delitos (CVEGEO);

CREATE INDEX IF NOT EXISTS idx_fact_delitos_fecha
    ON dw.fact_delitos (fecha_key);

CREATE INDEX IF NOT EXISTS idx_fact_delitos_hora
    ON dw.fact_delitos (hora_key);

CREATE INDEX IF NOT EXISTS idx_fact_delitos_delito
    ON dw.fact_delitos (delito_key);

CREATE INDEX IF NOT EXISTS idx_fact_delitos_geometry
    ON dw.fact_delitos
    USING GIST (geometry);

ALTER TABLE dw.fact_delitos
    ADD CONSTRAINT chk_fact_delitos_hora
    CHECK (hora IS NULL OR hora BETWEEN 0 AND 23);

ALTER TABLE dw.fact_delitos
    ADD CONSTRAINT chk_fact_delitos_estatus
    CHECK (
        estatus_asignacion IN (
            'asignado',
            'dentro_cdmx_sin_ageb',
            'fuera_cdmx',
            'sin_coordenadas_validas'
        )
    );


-- ============================================================
-- FACT: POBLACION
-- GRANO: una fila por AGEB urbana.
-- Fuente: INEGI Censo 2020.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.fact_poblacion (
    CVEGEO          VARCHAR(13) PRIMARY KEY,

    pob_total       BIGINT,
    pob_0_14        BIGINT,
    pob_15_64       BIGINT,
    pob_65_mas      BIGINT,

    pob_12_mas      BIGINT,
    pea             BIGINT,

    fuente          VARCHAR(100),
    fecha_corte     DATE,

    CONSTRAINT fk_fact_poblacion_geografia
        FOREIGN KEY (CVEGEO)
        REFERENCES dw.dim_geografia(CVEGEO)
);


-- ============================================================
-- FACT: ESTABLECIMIENTOS
-- GRANO: una fila por establecimiento economico registrado
-- dentro de una AGEB urbana.
-- Fuente: INEGI DENUE.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.fact_establecimientos (
    establecimiento_key     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    establishment_id        VARCHAR(100) NOT NULL UNIQUE,

    CVEGEO                  VARCHAR(13),

    actividad_key           INTEGER,
    tamano_key              INTEGER,

    codigo_act              VARCHAR(10),
    fecha_alta              DATE,

    establecimiento_count   INTEGER NOT NULL DEFAULT 1,

    latitud                 NUMERIC(10,7),
    longitud                NUMERIC(10,7),

    geometry                geometry(Point, 32614),

    fuente                  VARCHAR(100),
    fecha_corte             DATE,

    CONSTRAINT fk_fact_estab_geografia
        FOREIGN KEY (CVEGEO)
        REFERENCES dw.dim_geografia(CVEGEO),

    CONSTRAINT fk_fact_estab_actividad
        FOREIGN KEY (actividad_key)
        REFERENCES dw.dim_actividad_economica(actividad_key),

    CONSTRAINT fk_fact_estab_tamano
        FOREIGN KEY (tamano_key)
        REFERENCES dw.dim_tamano(tamano_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_estab_cvegeo
    ON dw.fact_establecimientos (CVEGEO);

CREATE INDEX IF NOT EXISTS idx_fact_estab_actividad
    ON dw.fact_establecimientos (actividad_key);

CREATE INDEX IF NOT EXISTS idx_fact_estab_tamano
    ON dw.fact_establecimientos (tamano_key);

CREATE INDEX IF NOT EXISTS idx_fact_estab_geometry
    ON dw.fact_establecimientos
    USING GIST (geometry);