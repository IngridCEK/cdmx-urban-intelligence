# CDMX Urban Intelligence - Geospatial Data Warehouse

> Proyecto Unidad 2 - Business Intelligence, Universidad Politecnica de Yucatan.

## 1. Project overview and analytical objective
_TODO_

## 2. Data sources (original grain and relevant variables)
| Capa | Fuente | Grano original | Variables clave | Fecha de descarga |
|---|---|---|---|---|
| Demografica | INEGI Censo 2020 (por AGEB/manzana) | | | |
| Economica | INEGI DENUE | | | |
| Geografica | INEGI Marco Geoestadistico, Censo 2020 (entidad 09) | Un poligono por AGEB urbana | `CVEGEO`, geometria (`09a.shp`), alcaldias (`09mun.shp`) | 4 oct 2026 |
| Seguridad | FGJ CDMX - Carpetas de investigacion 2023 | Una fila por carpeta de investigacion (242,392) | `categoria_delito`, `fecha_hecho`, `hora_hecho`, `alcaldia_catalogo`, `latitud`, `longitud` | 4 oct 2026 |Carpeta/incidente con lat/lon | categoria_delito, fecha_hecho, hora_hecho, latitud, longitud | |

## 3. Geographic strategy
Alternativas consideradas, unidad elegida y integracion lat/lon -> poligono. 
**Unidad de analisis elegida: AGEB urbana** (INEGI, Marco Geoestadistico del Censo 2020, entidad 09). El analisis cubre <2431> AGEB urbanas.

### Alternativas consideradas
| Unidad | Motivo de descarte |
|---|---|
| Alcaldia | Solo 16 unidades; demasiado gruesa para medir autocorrelacion espacial |
| Colonia | No existe poligono oficial de INEGI ni datos censales a ese nivel |
| Codigo postal | No es cartografia oficial de INEGI y el Censo no se publica por CP, habria que interpolar |
| Manzana | El Censo suprime valores menores a 3 por privacidad y los delitos quedarian dispersos, con muchos ceros |
| **AGEB urbana** | Poligono y Censo oficiales; los puntos de delitos y DENUE se integran por spatial join |

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
_TODO_

## 5. PostgreSQL/PostGIS and Data Warehouse model
Hechos, dimensiones, grano y relaciones. _TODO_

## 6. KPI definitions and formulas
_TODO_

## 7. Assumptions, data-quality issues and limitations
_TODO_

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
