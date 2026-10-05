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
| `dentro_cdmx_sin_ageb` | Dentro de la CDMX, fuera de toda AGEB urbana | 357 |
| `fuera_cdmx` | Tiene coordenadas, pero fuera de la CDMX | 51 |
| `sin_coordenadas_validas` | Sin latitud/longitud útiles (nulas, cero o fuera de rango) | 14,147 |

Los KPIs por AGEB usan solo los registros `asignado`.

---

## 3. Censo (`fact_poblacion`) — Persona B
_Pendiente. Agregar aquí la descripción de columnas del Censo por AGEB._

---

## 4. DENUE (`fact_establecimientos`, `dim_actividad_economica`, `dim_tamano`) — Persona B
_Pendiente. Agregar aquí la descripción de columnas del DENUE y la clasificación SCIAN._

---

## 5. Dimensiones de tiempo y tipo de delito (`dim_fecha`, `dim_hora`, `dim_delito`) — Persona C
_Pendiente. Agregar aquí las columnas finales según `sql/01_schema.sql`._
