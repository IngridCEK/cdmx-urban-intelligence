# Data Warehouse Design

## 1. Purpose

The Data Warehouse integrates geographic, demographic, economic, and crime information for urban intelligence analysis in Mexico City (CDMX).

The selected unit of analysis is the **urban AGEB**. The main geographic integration key is `CVEGEO`.

The dimensional model is designed to support the required KPIs while preserving the original grain of each analytical process.

---

## 2. Geographic Unit and Integration Key

The main geographic unit is the **urban AGEB** from the INEGI Marco Geoestadístico, Census 2020, entity 09.

The main integration key is:

* `CVEGEO`: geographic identifier of the urban AGEB.

Crime records containing `latitud` and `longitud` are converted into points in EPSG:4326 and spatially joined to the urban AGEB polygons. DENUE establishments are also assigned to an AGEB using their geographic coordinates.

The geographic dimension stores the AGEB geometry as a `MultiPolygon` with an explicitly defined SRID. A spatial GiST index will be created on the geometry column.

---

## 3. Dimension Tables

### 3.1 `dim_geografia`

**Purpose:** Stores the geographic context used by the analytical facts.

**Grain:** One row represents one urban AGEB.

**Main attributes:**

* `CVEGEO`
* AGEB identifier
* alcaldía (`NOMGEO`)
* `area_km2`
* geometry (`MultiPolygon`)
* geometry SRID

**Role in the model:** Central geographic dimension shared by crime, population, and establishment facts.

---

### 3.2 `dim_fecha`

**Purpose:** Provides calendar attributes for temporal analysis.

**Grain:** One row represents one calendar date.

**Main attributes:**

* date
* day
* month
* month name
* quarter
* year

**Temporal coverage:** The date dimension must cover the complete range of `fecha_hecho` used by the 2023 crime dataset, including incidents with events occurring in 2022 but records opened in 2023.

For crime analysis, the selected event date is **`fecha_hecho`**, because the KPIs describe when the crime occurred rather than when the investigation was opened.

---

### 3.3 `dim_hora`

**Purpose:** Provides temporal attributes for analysis of incidents by time of day.

**Grain:** One row represents one hour or defined time interval.

**Main attributes:**

* hour
* time interval / time band
* part of day

**Role in the model:** Supports the KPI **Incidents by Type and Time** together with `dim_delito`.

---

### 3.4 `dim_delito`

**Purpose:** Stores descriptive information about crime classifications.

**Grain:** One row represents one distinct crime classification.

**Main attributes:**

* `categoria_delito`
* `delito`

**Role in the model:** Allows crime incidents to be analyzed by category and type.

---

### 3.5 `dim_actividad_economica`

**Purpose:** Stores the economic activity classification of DENUE establishments.

**Grain:** One row represents one economic activity classification.

**Main attributes:**

* SCIAN activity code
* SCIAN activity description
* economic sector
* business classification
* retail/service classification

**Retail classification:** Establishments whose SCIAN activity belongs to **Sector 46, Comercio al por menor**, are classified as Retail.

**Service classification:** Service establishments will be identified through an explicit SCIAN sector mapping defined during ETL. Retail establishments are identified by SCIAN Sector 46 (Comercio al por menor). The final service-sector mapping must be validated against the project source data and documented so the same classification rule is used consistently in all KPI calculations.

**Role in the model:** Supports Business Density, Retail Density, Service Density, and Dominant Economic Activity.

---

### 3.6 `dim_tamano`

**Purpose:** Stores establishment-size classifications from DENUE.

**Grain:** One row represents one establishment-size category.

**Main attributes:**

* size category
* size description

**Role in the model:** Allows establishment analysis by business size.

---

## 4. Fact Tables

### 4.1 `fact_delitos`

**Purpose:** Stores crime incidents from FGJ CDMX.

**Grain:** **One row represents one crime incident/case recorded in the source dataset.**

**Main attributes and measures:**

* technical incident identifier
* `CVEGEO`
* date key
* hour key
* crime type key
* `fecha_hecho`
* `hora_hecho`
* latitude
* longitude
* incident count

**Relationships:**

* `CVEGEO` → `dim_geografia`
* date → `dim_fecha`
* hour → `dim_hora`
* crime type → `dim_delito`

**Non-AGEB records:**

All source crime records are retained in the fact table for traceability. Records that cannot be assigned to an urban AGEB have a null `CVEGEO` and an assignment-status attribute indicating the reason, such as:

* missing or invalid coordinates
* outside CDMX
* inside CDMX but outside an urban AGEB

For geographic KPIs, only records with a valid `CVEGEO` are included. The ETL validation must reconcile the source total of **242,392 records** with the assigned and non-assigned categories.

---

### 4.2 `fact_poblacion`

**Purpose:** Stores demographic measures from the INEGI Census.

**Grain:** **One row represents one urban AGEB.**

This design follows the Census geographic grain and avoids mixing geographic and demographic grains in the same fact table.

**Main measures and attributes:**

* `CVEGEO`
* total population (`pob_total`)
* population by age group
* population age 12 years and older
* economically active population (`pea`)
* source
* source cutoff date

**Relationships:**

* `CVEGEO` → `dim_geografia`

**KPI support:**

* Total Population
* Population by Age Group
* Economically Active Population Rate
* Crime Rate
* Population Density

For the Economically Active Population Rate, the denominator is the **population aged 12 years and older**, not total population.

---

### 4.3 `fact_establecimientos`

**Purpose:** Stores economic establishments from INEGI DENUE assigned to urban AGEBs.

**Grain:** **One row represents one economic establishment registered in an urban AGEB.**

**Main attributes and measures:**

* establishment identifier
* `CVEGEO`
* economic activity key
* establishment-size key
* SCIAN activity
* establishment count
* point geometry
* source
* source cutoff date

The establishment point is stored as a geographic point with an explicitly defined SRID.

**Relationships:**

* `CVEGEO` → `dim_geografia`
* economic activity → `dim_actividad_economica`
* establishment size → `dim_tamano`

**KPI support:**

* Business Density
* Retail Density
* Service Density
* Total Businesses
* Businesses per 1,000 Residents
* Dominant Economic Activity
* Crime relative to Business Activity

---

## 5. Data Lineage and Source Information

The fact tables include source and cutoff-date information to preserve temporal traceability.

| Data                    | Source                                   | Reference period / cutoff |
| ----------------------- | ---------------------------------------- | ------------------------- |
| Geography               | INEGI Marco Geoestadístico / Census 2020 | Census 2020               |
| Population              | INEGI Census                             | Census 2020               |
| Economic establishments | INEGI DENUE                              | 05/2026                   |
| Crime incidents         | FGJ CDMX                                 | 2023                      |

The different reference periods must be preserved because the datasets do not represent exactly the same point in time.

---

## 6. KPI Support

The proposed model supports the following **14 required KPIs**:

| KPI                                 | Calculation                                                                                | Supporting tables                                                   |
| ----------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Total Crime Incidents               | Count of valid crime incidents by `CVEGEO`                                                 | `fact_delitos`, `dim_geografia`                                     |
| Crime Rate                          | Crime incidents / population × 1,000                                                       | `fact_delitos`, `fact_poblacion`                                    |
| Population Density                  | Total population / `area_km2`                                                              | `fact_poblacion`, `dim_geografia`                                   |
| Business Density                    | Businesses / `area_km2`                                                                    | `fact_establecimientos`, `dim_geografia`                            |
| Retail Density                      | Retail businesses / `area_km2`                                                             | `fact_establecimientos`, `dim_actividad_economica`, `dim_geografia` |
| Service Density                     | Service businesses / `area_km2`                                                            | `fact_establecimientos`, `dim_actividad_economica`, `dim_geografia` |
| Total Population                    | Sum of `pob_total` by `CVEGEO`                                                             | `fact_poblacion`                                                    |
| Economically Active Population Rate | PEA / population aged 12+ × 100                                                            | `fact_poblacion`                                                    |
| Population by Age Group             | Population grouped by age group                                                            | `fact_poblacion`                                                    |
| Total Businesses                    | Count of establishments by `CVEGEO`                                                        | `fact_establecimientos`                                             |
| Businesses per 1,000 Residents      | Businesses / population × 1,000                                                            | `fact_establecimientos`, `fact_poblacion`                           |
| Dominant Economic Activity          | Economic activity with the highest establishment count in an AGEB                          | `fact_establecimientos`, `dim_actividad_economica`                  |
| Incidents by Type and Time          | Count of incidents grouped by crime type and date/hour or time band                        | `fact_delitos`, `dim_delito`, `dim_fecha`, `dim_hora`               |
| Crime Relative to Business Activity | Crime incidents relative to the number of businesses, using a documented rate per business | `fact_delitos`, `fact_establecimientos`                             |

### KPI details

**Total Crime Incidents**

Count of crime incidents assigned to an urban AGEB.

**Crime Rate**

Crime incidents divided by total population and multiplied by 1,000.

**Population Density**

Total population divided by AGEB area in square kilometers.

**Business Density**

Total establishments divided by AGEB area in square kilometers.

**Retail Density**

Retail establishments divided by AGEB area in square kilometers.

**Service Density**

Service establishments divided by AGEB area in square kilometers.

**Total Population**

Total population recorded for each urban AGEB.

**Economically Active Population Rate**

Economically active population divided by population aged 12 years and older, multiplied by 100.

**Population by Age Group**

Population summarized according to the available Census age groups.

**Total Businesses**

Count of DENUE establishments assigned to each urban AGEB.

**Businesses per 1,000 Residents**

Number of businesses divided by total population, multiplied by 1,000.

**Dominant Economic Activity**

The SCIAN activity with the largest number of establishments within an AGEB.

**Incidents by Type and Time**

Count of crime incidents grouped by crime type and time information, using `fecha_hecho` and `hora_hecho`.

**Crime Relative to Business Activity**

Crime incidents relative to the number of businesses, using the formula defined by the project KPI specification. The aggregation must be performed by AGEB before combining crime and business results.

## 7. Aggregation and KPI Calculation Rules

The fact tables have different grains and must not be joined directly at the individual-record level.

For KPIs combining multiple facts, the calculation process must first aggregate each fact independently by `CVEGEO` and then join the aggregated results.

For example:

1. Aggregate crime incidents by `CVEGEO`.
2. Aggregate establishments by `CVEGEO`.
3. Aggregate population by `CVEGEO`.
4. Join the resulting AGEB-level summaries.

This prevents row multiplication and incorrect KPI values.

---

## 8. Data Quality and Edge Cases

### Division by zero

KPI calculations must protect against division by zero.

* If `area_km2 = 0`, density KPIs return null.
* If population is zero or null, population-based rates return null.
* If the number of businesses is zero, crime-relative-to-business calculations return null.

### Census suppressed values

Census values represented by asterisks or suppression markers must be converted to `NULL` during ETL rather than interpreted as zero.

Null values must be handled explicitly in KPI calculations.

### Crime spatial assignment

The ETL must preserve the reconciliation of the 242,392 source crime records:

* 227,837 assigned to an urban AGEB
* 14,147 without valid coordinates
* 357 inside CDMX but outside an urban AGEB
* 51 outside CDMX

The exact validation totals must be preserved in the ETL documentation.

---

## 9. PostGIS Design

`dim_geografia` stores AGEB polygons as `MultiPolygon` geometry with an explicitly defined SRID and a GiST spatial index.

`fact_delitos` stores the crime location as a point geometry.

`fact_establecimientos` stores the establishment location as a point geometry.

The spatial geometry allows the ETL process to perform the required point-in-polygon spatial joins and supports future geographic analysis.

---

## 10. Model Summary

The proposed dimensional model uses `dim_geografia` as the central geographic dimension and integrates three analytical processes:

1. Crime incidents from FGJ CDMX.
2. Population information from the INEGI Census.
3. Economic establishments from INEGI DENUE.

The model preserves a clear grain for every fact table:

* `fact_delitos`: one row per crime incident.
* `fact_poblacion`: one row per urban AGEB.
* `fact_establecimientos`: one row per economic establishment.

The design supports all 14 required KPIs and establishes rules for temporal analysis, spatial assignment, economic classification, source traceability, aggregation, null values, and division by zero.

SQL implementation should be performed only after this design has been reviewed and approved.
