# CDMX Urban Intelligence - Geospatial Data Warehouse

> Proyecto Unidad 2 - Business Intelligence, Universidad Politecnica de Yucatan.

## 1. Project overview and analytical objective
_TODO_

## 2. Data sources (original grain and relevant variables)
| Capa | Fuente | Grano original | Variables clave | Fecha de descarga |
|---|---|---|---|---|
| Demografica | INEGI Censo 2020 (por AGEB/manzana) | | | |
| Economica | INEGI DENUE | | | |
| Geografica | INEGI Marco Geoestadistico | | | |
| Seguridad | FGJ CDMX - Carpetas de investigacion (Portal de Datos Abiertos CDMX) | Carpeta/incidente con lat/lon | categoria_delito, fecha_hecho, hora_hecho, latitud, longitud | |

## 3. Geographic strategy
Alternativas consideradas, unidad elegida y integracion lat/lon -> poligono. _TODO_

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
