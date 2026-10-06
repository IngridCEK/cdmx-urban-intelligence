# Diccionario de datos

Documento compartido. Cada integrante describe las tablas de sus fuentes en su propia sección. Los nombres de columnas deben coincidir con `sql/01_schema.sql`; si cambian, se actualiza aquí.

---

## 1. Geografía: AGEB urbanas (`dim_geografia`)

**Fuente:** INEGI, Marco Geoestadístico del Censo 2020 (entidad 09), capas `09a.shp` (AGEB urbanas) y `09mun.shp` (alcaldías).
**Grano:** una fila por AGEB urbana (2,431 polígonos).
**Responsable:** Persona A.

| Columna | Tipo | Descripción |
|---|---|---|
| `CVEGEO` | texto (13) | Clave de la AGEB: entidad (2) + municipio (3) + localidad (4) + AGEB (4). Puede contener letras. Llave de integración de todas las capas |
| `NOMGEO` | texto | Nombre de la alcaldía. Proviene de `09mun.shp` y se asigna a cada AGEB por su clave de municipio |
| `area_km2` | decimal | Área de la AGEB en km², calculada con la geometría reproyectada a EPSG:32614 (UTM 14N) |
| `geometry` | polígono | Geometría de la AGEB. Se conserva el CRS original del Marco Geoestadístico |

**Notas:**
- Solo incluye AGEB urbanas; las zonas rurales no tienen polígono en `09a.shp`.
- Las geometrías inválidas se corrigen con `make_valid()` al cargar (`src/geo/polygons.py`).

---

## 2. Delitos (`fact_delitos`)

**Fuente:** FGJ CDMX, Carpetas de investigación 2023 (`carpetas_fgj_2023.csv`).
**Grano:** una fila por carpeta de investigación (242,392 registros). Se conservan todos, aunque no se puedan ubicar.
**Responsable:** Persona A (`src/etl/crime.py`).

| Columna | Origen | Descripción |
|---|---|---|
| `_id` | CSV | Identificador del registro en el archivo |
| `fecha_inicio` | CSV | Fecha en que se abrió la carpeta |
| `fecha_hecho` | CSV | Fecha en que ocurrió el hecho. Es la fecha usada en el análisis; algunos hechos son de 2022 |
| `hora_hecho` | CSV | Hora del hecho (HH:MM:SS) |
| `hora` | Derivada | Hora entera (0 a 23) extraída de `hora_hecho`. Nula si el formato es inválido |
| `delito` | CSV | Descripción del delito |
| `categoria_delito` | CSV | Categoría o impacto del delito |
| `alcaldia_catalogo` | CSV | Alcaldía según el catálogo de la FGJ |
| `latitud`, `longitud` | CSV | Coordenadas en grados decimales. Pueden estar vacías |
| `alcaldia_geo` | Derivada | Alcaldía obtenida por spatial join contra `09mun.shp`. Nula si el punto no cae en la CDMX o no hay coordenadas |
| `CVEGEO` | Derivada | AGEB asignada por spatial join (`within`). Nula si no se asigna |
| `estatus_asignacion` | Derivada | Resultado de la asignación (ver abajo) |
| `geometry` | Derivada | Punto del delito, en el CRS de los polígonos. Nulo si no hay coordenadas útiles |

Se conservan además las demás columnas originales del CSV (por ejemplo `fiscalia`, `agencia`, `colonia_hecho`).

**Valores de `estatus_asignacion` (reconciliación de 242,392 registros):**

| Valor | Significado | Registros |
|---|---|---|
| `asignado` | Cae dentro de una AGEB urbana | 227,837 |
| `dentro_cdmx_sin_ageb` | Dentro de la CDMX o a <=10 km del limite, fuera de toda AGEB urbana | 408 |
| `fuera_cdmx` | Tiene coordenadas y queda a mas de 10 km del limite de la CDMX | 0 |
| `sin_coordenadas_validas` | Sin latitud/longitud útiles (nulas, cero o fuera de rango) | 14,147 |

Los KPIs por AGEB usan solo los registros `asignado`. La tolerancia cartografica compartida es de 10 km (`BORDER_TOLERANCE_M=10000`) y se aplica tanto a delitos como a DENUE.

---

## 3. Censo (`fact_poblacion`) — Persona B

**Fuente:** INEGI Censo 2020, Principales resultados por AGEB y manzana urbana, entidad 09.
**Grano:** una fila por AGEB de total (`AGEB` distinto de `0000` y `MZA` = `000`), 2,433 filas.
**ETL:** `src/etl/census.py`. Lee con `dtype=str` y `encoding="utf-8-sig"`; los `*` se convierten a NULL, nunca a cero.

| Columna | Tipo | Descripción |
|---|---|---|
| `CVEGEO` | texto (13) | Clave construida como `ENTIDAD` + `MUN` + `LOC` + `AGEB`; llave de integración con geografía y DENUE |
| `ENTIDAD`, `MUN`, `LOC`, `AGEB` | texto | Componentes de la clave geográfica original del Censo |
| `NOM_MUN` | texto | Nombre de la alcaldía/municipio según el Censo |
| `POBTOT` | entero nullable | Población total del AGEB |
| `POB0_14` | entero nullable | Población de 0 a 14 años |
| `POB15_64` | entero nullable | Población de 15 a 64 años |
| `POB65_MAS` | entero nullable | Población de 65 años y más |
| `P_18A24` | entero nullable | Población de 18 a 24 años |
| `P_12YMAS` | entero nullable | Población de 12 años y más; denominador para la tasa de PEA |
| `PEA` | entero nullable | Población económicamente activa |
| `POCUPADA` | entero nullable | Población ocupada |
| `PDESOCUP` | entero nullable | Población desocupada |
| `PE_INAC` | entero nullable | Población no económicamente activa |
| `VIVTOT` | entero nullable | Viviendas totales |
| `TVIVHAB` | entero nullable | Viviendas habitadas |
| `GRAPROES` | decimal nullable | Grado promedio de escolaridad |

**Calidad:** la salida contiene 2,433 filas; 17 AGEB tienen `POBTOT = 0`. Los valores suprimidos con `*` quedan como NULL y se reportan por columna en `censo_2020_ageb_reporte_calidad.json`.

---

## 4. DENUE (`fact_establecimientos`, `dim_actividad_economica`, `dim_tamano`) — Persona B

**Fuente:** INEGI DENUE 05_2026, Ciudad de México.
**Grano:** una fila por establecimiento, 462,732 registros.
**ETL:** `src/etl/denue.py`. Lee con `encoding="latin-1"` y `dtype=str`; convierte latitud/longitud a puntos y asigna AGEB mediante spatial join contra `09a.shp` usando `load_agebs()`.

| Columna | Origen | Descripción |
|---|---|---|
| `id` | DENUE | Identificador único del establecimiento |
| `codigo_act` | DENUE | Código SCIAN de 6 dígitos; sus primeros dos dígitos determinan el sector |
| `nombre_act` | DENUE | Nombre de la actividad económica |
| `per_ocu` | DENUE | Estrato de personal ocupado; se conserva como categoría y se ordena 1–7 en `dim_tamano` |
| `tipoUniEco` | DENUE | Tipo de unidad económica: `Fijo` o `Semifijo`; ambos se incluyen |
| `cve_ent`, `cve_mun`, `cve_loc`, `ageb`, `manzana` | DENUE | Claves geográficas originales del establecimiento |
| `CVEGEO_DENUE` | Derivada | Clave reconstruida con `cve_ent` + `cve_mun` + `cve_loc` + `ageb` |
| `latitud`, `longitud` | DENUE | Coordenadas en grados decimales usadas para construir los puntos |
| `CVEGEO` | Derivada | AGEB asignada por spatial join contra `09a.shp`; NULL cuando no se asigna |
| `alcaldia_geo` | Derivada | Alcaldía obtenida por spatial join contra `09mun.shp` |
| `estatus_asignacion` | Derivada | `asignado`, `dentro_cdmx_sin_ageb`, `fuera_cdmx` o `sin_coordenadas_validas` |
| `geometry` | Derivada | Punto reproyectado al CRS de los polígonos; NULL si no hay coordenadas válidas |

**Reconciliación:** se conservan los 462,732 registros. El reporte `denue_2026_reporte_calidad.json` verifica que la suma de los cuatro estatus sea exactamente 462,732 y compara `CVEGEO` espacial contra `CVEGEO_DENUE`.

**Clasificación SCIAN:** sector 46 = comercio al por menor; sectores 51–56, 61, 62, 71, 72 y 81 = servicios; el resto = otro. El catálogo reproducible está en `data/catalogos/scian_sectores.csv` y las decisiones analíticas están en `docs/scian_clasificacion.md`.

---

## 5. Dimensiones de tiempo y tipo de delito (`dim_fecha`, `dim_hora`, `dim_delito`) — Persona C

Estas dimensiones se cargan desde la salida procesada de delitos mediante `src/etl/load_dimensions_delitos.py`.

| Tabla | Grano | Columnas principales |
|---|---|---|
| `dim_fecha` | una fila por fecha calendario | `fecha_key`, `fecha`, `dia`, `mes`, `nombre_mes`, `trimestre`, `anio` |
| `dim_hora` | una fila por hora (0-23) | `hora_key`, `hora`, `franja_horaria`, `parte_dia` |
| `dim_delito` | una fila por combinación de categoría y delito | `delito_key`, `categoria_delito`, `delito` |

`fecha_key` usa el formato AAAAMMDD y `hora_key` coincide con la hora entera 0-23. Estas llaves se referencian desde `fact_delitos`.
