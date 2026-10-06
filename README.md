# CDMX Urban Intelligence - Geospatial Data Warehouse

> Proyecto Unidad 2 - Business Intelligence, Universidad Politécnica de Yucatán.

## 1. Project overview and analytical objective

This project develops a geospatial Data Warehouse for analyzing crime, population, and economic activity in Mexico City (CDMX). The main geographic unit of analysis is the urban AGEB (Área Geoestadística Básica), which allows the integration of demographic, crime, economic, and geographic information at a detailed spatial level.

The analytical objective is to identify and compare patterns of crime, population, and economic activity across urban AGEBs. The Data Warehouse supports indicators such as crime rates, population density, business density, crime by type and time, and the relationship between crime and economic activity.

The architecture uses PostgreSQL with PostGIS and a dimensional model composed of geographic, temporal, crime, economic activity, and business-size dimensions, together with fact tables for crime incidents, population, and establishments.

## 2. Data sources (original grain and relevant variables)

| Layer | Source | Original grain | Key variables | Download date |
|---|---|---|---|---|
| Demographic | INEGI Censo 2020, principal results by AGEB and urban block (entity 09) | One row per entity, municipality, locality, AGEB, and block (68,941 rows); 2,433 AGEB total rows are used | `POBTOT`, `POB0_14`, `POB15_64`, `POB65_MAS`, `P_12YMAS`, `PEA`; `ENTIDAD` + `MUN` + `LOC` + `AGEB` -> `CVEGEO` | 4 Oct 2026 |
| Economic | INEGI DENUE 05_2026 (CDMX) | One row per establishment (475,331) with coordinates and economic activity information | `id`, `codigo_act`, `nombre_act`, `per_ocu`, `latitud`, `longitud`, `ageb` | 4 Oct 2026 |
| Geographic | INEGI Marco Geoestadístico, Censo 2020 (entity 09) | One polygon per urban AGEB | `CVEGEO`, geometry, municipality information | 4 Oct 2026 |
| Security | FGJ CDMX - Carpetas de investigación 2023 | One row per investigation record (242,392) | `categoria_delito`, `fecha_hecho`, `hora_hecho`, `alcaldia_catalogo`, `latitud`, `longitud` | 4 Oct 2026 |

## 3. Geographic strategy

### Selected unit of analysis

The selected unit of analysis is the **urban AGEB**, based on the INEGI Marco Geoestadístico for Census 2020, entity 09. The analysis covers **2,431 urban AGEBs** that are compatible with the geographic dimension.

AGEB was selected because it provides an official polygon and is also available as a geographic unit in Census data. This allows crime and economic establishments to be integrated using spatial joins while preserving a detailed geographic level.

### Alternatives considered

| Unit | Reason for rejection |
|---|---|
| Municipality | Only 16 units in CDMX, which is too coarse for detailed spatial analysis |
| Neighborhood | No single official INEGI polygon and census data are not consistently available at this level |
| Postal code | Not the official INEGI geographic unit and census data are not published by postal code |
| Urban block | Census values may be suppressed for confidentiality and crime records would be highly dispersed |
| **Urban AGEB** | Official polygon and census unit; crime and DENUE points can be integrated through spatial joins |

### Integration of latitude/longitude with polygons

Crime and establishment coordinates are initially handled in EPSG:4326 and then transformed to the working coordinate reference system used by the geographic polygons. Points are assigned to an urban AGEB using a spatial join with the `within` predicate.

The main integration key is `CVEGEO`, a 13-character geographic code.

### Crime spatial integration results

| Category | Records | Percentage |
|---|---:|---:|
| Total | 242,392 | 100.00% |
| Assigned to an urban AGEB | 227,837 | 94.00% |
| Without valid coordinates | 14,147 | 5.84% |
| Inside CDMX but outside an urban AGEB | 357 | 0.15% |
| Coordinates outside CDMX | 51 | 0.02% |

The validation comparing the municipality recorded in the crime source with the municipality obtained through the spatial join shows **99.86% agreement**.

## 4. ETL pipeline

The general flow is:

**RAW -> CLEAN -> SPATIAL JOIN -> POSTGRESQL DATA WAREHOUSE**

Raw files stored in `data/raw/` are not modified.

### 4.1 Polygons and crime data

The main ETL process is implemented in `src/etl/crime.py`.

| Step | Code | Description |
|---|---|---|
| Extract | `src/etl/crime.py` | Reads the FGJ CSV and validates required columns |
| Polygons | `src/geo/polygons.py` | Loads urban AGEB and municipality polygons and prepares geographic information |
| Clean | `crime.py` | Removes duplicates, converts data types and dates, and cleans text |
| Points | `crime.py` | Validates coordinates and creates point geometries |
| Spatial join | `crime.py` | Assigns municipality and `CVEGEO` using a spatial join |
| Output | `data/processed/` | Generates the processed GeoPackage and quality report |

### 4.2 Census and DENUE

Population and economic data are integrated into the Data Warehouse through dedicated ETL scripts.

Population processing uses the official INEGI Census 2020 AGEB-level records. The population loader aggregates the relevant AGEB records and loads them into `fact_poblacion`.

DENUE processing loads establishment records and assigns them to urban AGEBs using their geographic coordinates. Establishment activity and size information are connected to `dim_actividad_economica` and `dim_tamano`.

### ETL validation results

| Dataset | Total records | Assigned to AGEB | Not assigned |
|---|---:|---:|---:|
| Crime | 242,392 | 227,837 | 14,555 |
| Establishments | 475,331 | 474,167 | 1,164 |
| Population | 2,431 AGEBs | 2,431 | 0 |

All source identifiers are unique in the loaded fact tables.

## 5. PostgreSQL/PostGIS and Data Warehouse model

The Data Warehouse uses a dimensional model based on the **urban AGEB** as the main geographic unit of analysis. `CVEGEO` is the primary integration key between geographic, crime, demographic, and economic information.

### Dimensions

- `dim_geografia`: one row per urban AGEB, including `CVEGEO`, geographic attributes, area, and polygon geometry.
- `dim_fecha`: one row per calendar date.
- `dim_hora`: one row per hour, including time-of-day classification.
- `dim_delito`: crime classification and category information.
- `dim_actividad_economica`: SCIAN economic activity classifications.
- `dim_tamano`: establishment-size categories.

### Fact tables

- `fact_delitos`: one row per crime investigation record.
- `fact_poblacion`: one row per urban AGEB with population and demographic measures.
- `fact_establecimientos`: one row per economic establishment.

### Current warehouse counts

| Object | Rows |
|---|---:|
| `dim_geografia` | 2,431 |
| `dim_fecha` | 24,137 |
| `dim_hora` | 24 |
| `dim_delito` | 286 |
| `dim_actividad_economica` | 945 |
| `dim_tamano` | 7 |
| `fact_delitos` | 242,392 |
| `fact_poblacion` | 2,431 |
| `fact_establecimientos` | 475,331 |

The detailed grain, attributes, relationships, and KPI dependencies are documented in `docs/warehouse_design.md` and `docs/kpi_variables.md`.

## 6. KPI definitions and formulas

The Data Warehouse supports the following analytical KPIs:

| KPI | Formula / definition |
|---|---|
| Total Crime Incidents | Count of crime incidents by `CVEGEO` |
| Crime Rate | Crime incidents / total population x 1,000 |
| Population Density | Total population / `area_km2` |
| Business Density | Establishments / `area_km2` |
| Retail Density | Retail establishments / `area_km2` |
| Service Density | Service establishments / `area_km2` |
| Total Population | Sum of population by AGEB |
| Economically Active Population Rate | PEA / population of the corresponding population base |
| Population by Age Group | Population separated into 0-14, 15-64, and 65+ |
| Total Businesses | Count of establishments |
| Businesses per 1,000 Residents | Establishments / population x 1,000 |
| Dominant Economic Activity | Economic activity with the highest establishment count |
| Incidents by Type and Time | Crime incidents grouped by crime type and hour |
| Crime Relative to Business Activity | Crime indicators analyzed together with establishment activity |

When a density or rate cannot be calculated because its denominator is zero, the current SQL views return zero for that metric.

## 7. Assumptions, data-quality issues and limitations

The project keeps raw source files unchanged and performs transformations in the ETL pipeline before loading the Data Warehouse.

For crime data, all **242,392** source records are preserved. Records without valid coordinates or without an urban AGEB remain available in the fact table but cannot contribute to AGEB-level spatial KPIs.

The crime spatial integration assigned **227,837 records (94.00%)** to an urban AGEB. The remaining records include cases without valid coordinates, points inside CDMX but outside the available urban AGEB polygons, and coordinates outside CDMX.

For population data, the Census contains 2,433 AGEB-level records, while the geographic layer contains 2,431 compatible AGEBs. The two census records without a matching geographic polygon are excluded from the AGEB-level population fact table.

For DENUE, **475,331 establishments** are processed, with **474,167** assigned to an urban AGEB. The remaining 1,164 establishments have valid coordinates but could not be assigned to an available urban AGEB.

All tested foreign-key and dimension-integrity validations returned zero orphan records.

The main analytical limitation is that crime records without valid geographic assignment cannot be included in spatial comparisons between AGEBs. In addition, the results depend on the quality and geographic precision of the original source coordinates.

---

## Setup with Docker

### Requirements

- Docker Desktop
- Git

Python and PostgreSQL do not need to be installed directly on the host machine because they run through Docker.

```bash
git clone <url-del-repo>
cd cdmx-urban-intelligence
cp .env.example .env
docker compose up -d --build
docker compose exec app python -m src.check_db