# CDMX Urban Intelligence - Geospatial Data Warehouse

> Proyecto Unidad 2 - Business Intelligence, Universidad Politecnica de Yucatan.

## 1. Project overview and analytical objective
_TODO_

## 2. Data sources (original grain and relevant variables)
| Capa | Fuente | Grano original | Variables clave | Fecha de descarga |
|---|---|---|---|---|
| Demografica | INEGI Censo 2020, Principales resultados por AGEB y manzana urbana (entidad 09) | Una fila por entidad, municipio, localidad, AGEB y manzana (68,941 filas); se usan las 2,433 filas de total por AGEB (`MZA`=000) | `POBTOT`, `POB0_14`, `POB15_64`, `POB65_MAS`, `P_18A24`, `P_12YMAS`, `PEA`, `POCUPADA`, `PDESOCUP`, `PE_INAC`, `VIVTOT`, `TVIVHAB`, `GRAPROES`; clave `ENTIDAD`+`MUN`+`LOC`+`AGEB` -> `CVEGEO` | 4 oct 2026 |
| Economica | INEGI DENUE 05_2026 (CDMX) | Una fila por establecimiento (462,732) con lat/lon y claves de AGEB | `id`, `codigo_act` (SCIAN 2018), `nombre_act`, `per_ocu`, `tipoUniEco`, `fecha_alta`, `latitud`, `longitud`, `cve_ent`, `cve_mun`, `cve_loc`, `ageb`, `manzana` | 4 oct 2026 |
| Geografica | INEGI Marco Geoestadistico, Censo 2020 (entidad 09) | Un poligono por AGEB urbana | `CVEGEO`, geometria (`09a.shp`), alcaldias (`09mun.shp`) | 4 oct 2026 |
| Seguridad | FGJ CDMX - Carpetas de investigacion 2023 | Una fila por carpeta de investigacion (242,392) | `categoria_delito`, `fecha_hecho`, `hora_hecho`, `alcaldia_catalogo`, `latitud`, `longitud` | 4 oct 2026 |Carpeta/incidente con lat/lon | categoria_delito, fecha_hecho, hora_hecho, latitud, longitud | |

## 3. Geographic strategy
Alternativas consideradas, unidad elegida y integracion lat/lon -> poligono. 
**Unidad de analisis elegida: AGEB urbana** (INEGI, Marco Geoestadistico del Censo 2020, entidad 09). El analisis cubre 2,431 AGEB urbanas.

### Alternativas consideradas
| Unidad | Motivo de descarte |
|---|---|
| Alcaldia | Solo 16 unidades; demasiado gruesa para medir autocorrelacion espacial |
| Colonia | No existe poligono oficial de INEGI ni datos censales a ese nivel |
| Codigo postal | No es cartografia oficial de INEGI y el Censo no se publica por CP, habria que interpolar |
| Manzana | El Censo suprime valores menores a 3 por privacidad y los delitos quedarian dispersos, con muchos ceros |
| **AGEB urbana** | Poligono y Censo oficiales; los puntos de delitos y DENUE se integran por spatial join |

### Prueba de claves Censo vs `09a.shp`

Se comparó la `CVEGEO` del Censo 2020 contra la capa `09a.shp` del Marco Geoestadístico. La capa geográfica contiene **2,431 AGEB** y el Censo contiene **2,433 filas de total por AGEB**.

- **CVEGEO coincidentes:** 2,431
- **AGEB del Censo sin coincidencia en `09a.shp`:** 2
- **Claves sin coincidencia:** `0901101101107` y `0901201351227`
- **AGEB presentes en `09a.shp` y ausentes del Censo:** 0

Las dos claves adicionales del Censo se conservan en `censo_2020_ageb.csv` porque forman parte de las 2,433 filas de total por AGEB; no se eliminan del ETL.

### Integracion de lat/lon con poligonos
Los delitos (columnas `latitud` y `longitud`) se convierten a puntos en EPSG:4326, se reproyectan al CRS de los poligonos (PROJCS["MEXICO_ITRF_2008_LCC",GEOGCS["ITRF2008",DATUM["International_Terrestrial_Reference_Frame_2008",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","1061"]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["latitude_of_origin",12],PARAMETER["central_meridian",-102],PARAMETER["standard_parallel_1",17.5],PARAMETER["standard_parallel_2",29.5],PARAMETER["false_easting",2500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]) y se asignan a una AGEB con un spatial join (`predicate="within"`). La clave de enlace es `CVEGEO` (13 caracteres).

### Resultados de la integracion (delitos 2023)
| Categoria | Registros | % |
|---|---|---|
| Total | 242,392 | 100 |
| Asignados a una AGEB urbana | 227,837 | 94.00 |
| Sin coordenadas validas | 14,147 | 5.84 |
| Dentro de la CDMX, fuera de AGEB urbana | 357 | 0.15 |
| Con coordenadas fuera de la CDMX | 51 | 0.02 |

**Validacion:** la alcaldia registrada en el CSV coincide con la obtenida por spatial join en el 99.86% de los casos.

## 4. ETL pipeline

Flujo general: **RAW → CLEAN → SPATIAL JOIN → POSTGRESQL DW**. Los archivos crudos de `data/raw/` nunca se modifican.

### 4.1 Poligonos y delitos
**Ejecucion:** `docker compose exec app python -m src.etl.crime` (parametro opcional `--csv` para otro año).

| Paso | Codigo | Que hace |
|---|---|---|
| Extract | `src/etl/crime.py` | Lee el CSV de la FGJ y valida las columnas requeridas |
| Poligonos | `src/geo/polygons.py` | Carga AGEB urbanas y alcaldias, corrige geometrias invalidas, verifica `CVEGEO` unica de 13 caracteres, calcula `area_km2` en EPSG:32614 |
| Clean | `crime.py` | Elimina duplicados por `_id`, convierte tipos y fechas, limpia texto |
| Puntos | `crime.py` | Descarta registros sin coordenadas o en cero y crea geometrias de punto (EPSG:4326, reproyectadas al CRS de los poligonos) |
| Spatial join | `crime.py` | Asigna alcaldia y `CVEGEO` con `predicate="within"` |
| Salida | `data/processed/` | GeoPackage de delitos con su AGEB y un reporte de calidad en JSON |

**Resultados (delitos 2023):** 242,392 registros crudos; 0 duplicados; 227,837 asignados a una AGEB urbana (94.00%); coincidencia de alcaldia con el poligono: 99.86%.

### 4.2 Censo y DENUE
**Ejecucion:**
```bash
docker compose exec app python -m src.etl.census
docker compose exec app python -m src.etl.denue      # parametro opcional --csv
```
Ambos ETL leen `data/raw/` sin modificarlo y escriben en `data/processed/` un archivo de datos y un reporte de calidad en JSON. El diccionario de columnas esta en `docs/data_dictionary.md` (secciones 3 y 4).

#### Censo 2020 (`src/etl/census.py`)
| Paso | Que hace |
|---|---|
| Extract | Lee `RESAGEBURB_09CSV20.csv` con `dtype=str` y `encoding="utf-8-sig"` y valida las columnas requeridas |
| Filtro | El CSV mezcla entidad, municipio, localidad, AGEB y manzana (68,941 filas). Se conservan solo las filas de total por AGEB: `AGEB` distinto de `0000` y `MZA` igual a `000` |
| Clave | `CVEGEO` = `ENTIDAD` + `MUN` + `LOC` + `AGEB` (13 caracteres); se conserva como texto porque 222 claves llevan letras |
| Limpieza | Los `*` (dato suprimido) pasan a nulo, nunca a cero; las 13 columnas usadas se convierten a numero (enteros con nulos, `GRAPROES` decimal) |
| Salida | `censo_2020_ageb.csv` (una fila por AGEB) y `censo_2020_ageb_reporte_calidad.json` |

**Resultados:** 2,433 AGEB (una fila cada una); 172 valores suprimidos convertidos a nulo (el mayor, `PDESOCUP`, con 56 nulos = 2.3%); 17 AGEB con `POBTOT` = 0; 9,145,632 personas en las AGEB, 99.3% de la poblacion de la entidad. Validaciones sin excepciones: ninguna AGEB con `PEA` > `P_12YMAS` ni con viviendas habitadas > viviendas totales.

#### DENUE 05_2026 (`src/etl/denue.py`)
| Paso | Que hace |
|---|---|
| Extract | Lee el CSV con `encoding="latin-1"` y `dtype=str`, solo las 14 columnas necesarias para los KPIs (no se guardan nombre, razon social, telefono ni correo) |
| Clean | Falla si hay `id` duplicados; convierte `latitud`/`longitud` a numero; reconstruye `CVEGEO_DENUE` = `cve_ent` + `cve_mun` + `cve_loc` + `ageb` |
| SCIAN | Agrega `sector` y `grupo_actividad` con `data/catalogos/scian_sectores.csv`; falla si algun `codigo_act` no esta en el catalogo |
| Puntos | Convierte lat/lon a puntos (EPSG:4326) y los reproyecta al CRS de `09a.shp` |
| Spatial join | `predicate="within"` contra `09a.shp` (AGEB, via `load_agebs()`) y `09mun.shp` (alcaldias) |
| Estatus | Cada establecimiento queda con `asignado`, `dentro_cdmx_sin_ageb`, `fuera_cdmx` o `sin_coordenadas_validas`; no se borra ningun registro |
| Salida | `denue_2026_ageb.gpkg` (capa `establecimientos`) y `denue_2026_reporte_calidad.json` |

**Resultados:** los 462,732 establecimientos se conservan y la suma de estatus cuadra.

| Estatus | Registros |
|---|---:|
| `asignado` | 461,221 |
| `dentro_cdmx_sin_ageb` | 1,508 |
| `fuera_cdmx` | 3 |
| `sin_coordenadas_validas` | 0 |

- **Clave espacial vs clave del DENUE:** de los 461,221 asignados, 460,430 (99.83%) tienen el mismo `CVEGEO` que `CVEGEO_DENUE` y 791 no (786 con clave existente en `09a.shp` pero el punto cae en otra AGEB; 5 con clave que no existe en la capa). La integracion usa la AGEB espacial (`CVEGEO`), igual que en delitos.
- **Cobertura:** 2,420 de las 2,431 AGEB tienen al menos un establecimiento; 11 no tienen ninguno.
- **Regla `fuera_cdmx`:** un punto es de la CDMX si cae en un poligono de alcaldia o, si queda fuera, a no mas de 100 km del limite con `cve_ent` = `09`. Se propone la misma regla para delitos (hoy `crime.py` usa solo el poligono) porque los puntos fuera del poligono son de borde: los 51 delitos estan a 1.2 m o menos y 11 de los 14 del DENUE a 2.2 km o menos; solo 3 (a 315, 1,525 y 2,274 km) son coordenadas erroneas. Evidencia en `notebooks/04_diagnostico_fuera_cdmx.ipynb`.

#### Clasificacion SCIAN (version 2018)
La version se confirmo con el diccionario de datos que viene con el DENUE 05_2026. El sector son los dos primeros digitos de `codigo_act`; los sectores agrupados se tratan como uno (`31-33` y `48-49`).

| `grupo_actividad` | Sectores | Establecimientos |
|---|---|---:|
| `comercio al por menor` | 46 | 212,251 |
| `servicios` | 51 a 56, 61, 62, 71, 72, 81 | 192,925 |
| `otro` | resto | 57,556 |

El catalogo esta en `data/catalogos/scian_sectores.csv` y la regla con su justificacion en `docs/scian_clasificacion.md`.

#### Decisiones tomadas
- **Dominant Economic Activity:** es el sector SCIAN con mas establecimientos en la AGEB. En caso de empate gana el codigo de sector numericamente menor. Una AGEB sin establecimientos recibe el valor `sin_establecimientos`; no se fuerza una actividad.
- **`tipoUniEco`:** se incluyen unidades Fijas (442,146) y Semifijas (20,586). No se excluye ninguna: el archivo solo trae esos dos valores y no hay categoria de ambulantes.
- **Estratos de tamano (`per_ocu`):** 7 valores exactos con clave de orden para `dim_tamano`:

| orden_tamano | per_ocu | Establecimientos |
|---:|---|---:|
| 1 | `0 a 5 personas` | 390,466 |
| 2 | `6 a 10 personas` | 32,397 |
| 3 | `11 a 30 personas` | 24,418 |
| 4 | `31 a 50 personas` | 5,786 |
| 5 | `51 a 100 personas` | 4,630 |
| 6 | `101 a 250 personas` | 2,999 |
| 7 | `251 y mas personas` | 2,036 |

La prueba de claves Censo vs `09a.shp` (2,431 coincidentes y 2 AGEB del Censo sin poligono) esta en la seccion 3.

## 5. PostgreSQL/PostGIS and Data Warehouse model
The Data Warehouse uses a dimensional model based on the urban AGEB as the main geographic unit of analysis. CVEGEO is the main integration key between geographic, crime, demographic, and economic information.

The proposed dimensions are:

dim_geografia: one row per urban AGEB, including CVEGEO, alcaldía, area, and geometry.
dim_fecha: one row per calendar date.
dim_delito: crime classification information.
dim_actividad_economica: SCIAN and economic activity classifications.

The proposed fact tables are:

fact_delitos: one row per crime incident/case.
fact_poblacion: population measures by urban AGEB and demographic breakdown.
fact_establecimientos: one row per economic establishment.

The detailed grain, attributes, relationships, and KPI support are documented in docs/warehouse_design.md.

## 6. KPI definitions and formulas
The Data Warehouse is designed to support the following KPIs:

KPI	Formula
Total Crime Incidents	Count of crime incidents by CVEGEO
Crime Rate	Crime incidents / total population × 1,000
Population Density	Total population / area_km2
Business Density	Establishments / area_km2
Retail Density	Retail establishments / area_km2
Service Density	Service establishments / area_km2

The required source variables and KPI dependencies are documented in docs/kpi_variables.md
## 7. Assumptions, data-quality issues and limitations

### 7.1 Censo y DENUE
- **Desfase temporal:** el Censo es de 2020 y el DENUE de mayo de 2026; los KPIs que cruzan ambos (por ejemplo establecimientos por habitante) comparan fechas distintas.
- **Datos suprimidos del Censo:** los `*` se convierten a nulo y no se imputan (172 valores; `PDESOCUP` es la columna mas afectada, 2.3%). En 455 AGEB la suma de los tres grupos de edad es menor que `POBTOT` y en ninguna es mayor.
- **Poblacion cero:** 17 AGEB tienen `POBTOT` = 0, asi que las tasas por habitante quedan indefinidas ahi y deben tratarse como nulo.
- **AGEB sin poligono:** 2 AGEB del Censo (`0901101101107` y `0901201351227`) no existen en `09a.shp`; se conservan en el CSV pero no se pueden mapear ni cruzar con puntos.
- **DENUE cuenta establecimientos, no personal:** `per_ocu` es un estrato, no un numero de empleados, por lo que no se pueden sumar empleos.
- **Establecimientos semifijos incluidos:** son 20,586 (4.4% del total) y se cuentan igual que los fijos.
- **Sin AGEB:** 1,508 establecimientos no caen en ninguna AGEB urbana pero se consideran de la CDMX (11 de ellos por tolerancia de borde) y 3 tienen coordenadas erroneas fuera de la CDMX; no se asignan a ninguna AGEB, aunque se conservan con su estatus.
- **Discrepancia de AGEB:** en 791 establecimientos la AGEB que trae el DENUE difiere de la espacial; se usa la espacial (`CVEGEO`) como clave de integracion.
- **Clasificacion SCIAN en tres grupos:** `otro` mezcla manufactura, comercio al por mayor, construccion, gobierno y actividades primarias.

_Pendiente: supuestos de delitos y del modelo dimensional (Personas A y C)._

---

## Setup con Docker

Requisitos: Docker Desktop y Git. No necesitas instalar Python ni PostgreSQL.

```bash
git clone <url-del-repo>
cd cdmx-urban-intelligence
cp .env.example .env                 # (Windows PowerShell: copy .env.example .env)
docker compose up -d --build         # levanta PostGIS + contenedor de Python/Jupyter
docker compose exec app python -m src.check_db   # debe imprimir version de PostGIS
```

- Jupyter Lab: http://localhost:8888
- Conectar con DBeaver/pgAdmin: host `localhost`, puerto `5432`, usuario/BD segun `.env`.
- Ejecutar un script SQL:
  `docker compose exec -T db psql -U dw_user -d urban_dw < sql/01_schema.sql`
- Apagar: `docker compose down` (los datos persisten). Borrar la BD: `docker compose down -v`.

## Descarga de datos
Los datos crudos NO se suben a Git. Descargalos segun `docs/data_sources.md`
y colocalos en `data/raw/` sin modificarlos.

## Estructura del repositorio
```
data/raw, data/processed   datos (ignorados por Git)
notebooks/                 analisis y exploracion
src/etl, src/geo, src/analysis   codigo del pipeline
sql/                       01_schema, 02_load, 03_views
docs/                      diccionario de datos y diagrama del modelo
outputs/maps, outputs/figures
```

## Flujo de trabajo del equipo
- Una rama por tarea (`feat/...`, `docs/...`) y Pull Request revisado por otro integrante.
- Fusionar con **merge commit o rebase**, no squash (para conservar commits individuales).
- Commits pequenos y frecuentes con mensajes claros (`feat:`, `fix:`, `docs:`, `chore:`).
- Cada integrante configura su `git config user.name` y `user.email` (el del GitHub).
