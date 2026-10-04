# Data Warehouse Design

## 1. Purpose

The Data Warehouse is designed to integrate geographic, demographic, economic, and crime information for the analysis of urban intelligence in Mexico City (CDMX).

The selected unit of analysis is the **urban AGEB**, identified by `CVEGEO`. This key allows the integration of the different datasets and supports the calculation of crime, population, business, retail, and service indicators.

The model follows a dimensional design with fact tables containing measurable events or values and dimension tables providing descriptive context.

---

## 2. Geographic Unit and Integration Key

The main geographic unit is the **urban AGEB** from the INEGI Marco Geoestadístico.

The main integration key is:

* `CVEGEO`: unique geographic identifier of the urban AGEB.

The geographic dimension also contains the AGEB geometry, its area in square kilometers, and the corresponding alcaldía.

Crime records containing latitude and longitude are converted to geographic points and assigned to an urban AGEB using a spatial join. DENUE establishments are also associated with the corresponding AGEB.

---

## 3. Dimension Tables

### 3.1 `dim_geografia`

**Purpose:** Stores the geographic context used by all analytical facts.

**Grain:** One row represents one urban AGEB.

**Main attributes:**

* `CVEGEO`
* `NOMGEO` or alcaldía
* AGEB identifier and geographic attributes
* `area_km2`
* AGEB geometry

**Role in the model:** This is the main geographic dimension and the common link between crime, population, and economic information.

---

### 3.2 `dim_fecha`

**Purpose:** Provides temporal information for time-based analysis.

**Grain:** One row represents one calendar date.

**Main attributes:**

* date
* day
* month
* month name
* quarter
* year

**Role in the model:** Used by the crime fact table to analyze incidents by date and time period.

---

### 3.3 `dim_delito`

**Purpose:** Stores descriptive information about crime types.

**Grain:** One row represents one distinct crime classification.

**Main attributes:**

* `categoria_delito`
* `delito`

**Role in the model:** Allows crime incidents to be grouped and compared by category and type.

---

### 3.4 `dim_actividad_economica`

**Purpose:** Stores the economic activity classification of establishments from DENUE.

**Grain:** One row represents one economic activity classification used to categorize establishments.

**Main attributes:**

* SCIAN activity code
* SCIAN activity description
* economic sector
* classification for retail, services, or other business activities

**Role in the model:** Allows establishments to be classified as businesses, retail, and services for density calculations.

---

## 4. Fact Tables

### 4.1 `fact_delitos`

**Purpose:** Stores individual crime incidents assigned to urban AGEBs.

**Grain:** **One row represents one crime incident/case recorded by the FGJ CDMX.**

**Main measures and attributes:**

* crime incident identifier
* `CVEGEO`
* date key
* crime type key
* `fecha_hecho`
* `hora_hecho`
* latitude
* longitude
* incident count

**Relationships:**

* `CVEGEO` → `dim_geografia`
* date → `dim_fecha`
* crime type → `dim_delito`

**KPI support:**

* Total Crime Incidents
* Crime Rate

The grain at the individual incident level allows crime records to be counted by AGEB, crime type, date, or other dimensions.

---

### 4.2 `fact_poblacion`

**Purpose:** Stores demographic population measures from the INEGI Census.

**Grain:** **One row represents the population of one urban AGEB for a specific demographic breakdown.**

**Main measures and attributes:**

* `CVEGEO`
* total population
* population by age group
* economically active population
* demographic classification keys when applicable

**Relationships:**

* `CVEGEO` → `dim_geografia`

**KPI support:**

* Crime Rate
* Population Density

The total population measure is used as the denominator for Crime Rate, while population divided by geographic area is used for Population Density.

---

### 4.3 `fact_establecimientos`

**Purpose:** Stores economic establishments from INEGI DENUE assigned to urban AGEBs.

**Grain:** **One row represents one economic establishment registered in an urban AGEB.**

**Main measures and attributes:**

* establishment identifier
* `CVEGEO`
* economic activity key
* establishment size
* SCIAN activity
* establishment count

**Relationships:**

* `CVEGEO` → `dim_geografia`
* economic activity → `dim_actividad_economica`

**KPI support:**

* Business Density
* Retail Density
* Service Density

The establishment-level grain allows establishments to be counted by AGEB and economic activity and then divided by `area_km2`.

---

## 5. KPI Support

The proposed dimensional model supports the required KPIs as follows:

| KPI                   | Required information                    | Supporting tables                                                   |
| --------------------- | --------------------------------------- | ------------------------------------------------------------------- |
| Total Crime Incidents | Count of crime incidents by `CVEGEO`    | `fact_delitos`, `dim_geografia`                                     |
| Crime Rate            | Crime incidents and total population    | `fact_delitos`, `fact_poblacion`, `dim_geografia`                   |
| Population Density    | Total population and `area_km2`         | `fact_poblacion`, `dim_geografia`                                   |
| Business Density      | Number of establishments and `area_km2` | `fact_establecimientos`, `dim_geografia`                            |
| Retail Density        | Retail establishments and `area_km2`    | `fact_establecimientos`, `dim_actividad_economica`, `dim_geografia` |
| Service Density       | Service establishments and `area_km2`   | `fact_establecimientos`, `dim_actividad_economica`, `dim_geografia` |

### KPI formulas

**Total Crime Incidents**

Count of crime incident records grouped by `CVEGEO`.

**Crime Rate**

Crime incidents divided by total population, multiplied by 1,000.

**Population Density**

Total population divided by `area_km2`.

**Business Density**

Number of establishments divided by `area_km2`.

**Retail Density**

Number of retail establishments divided by `area_km2`.

**Service Density**

Number of service establishments divided by `area_km2`.

---

## 6. Model Summary

The proposed model uses `dim_geografia` as the central geographic dimension and integrates three main analytical processes:

1. Crime incidents from FGJ CDMX.
2. Population information from the INEGI Census.
3. Economic establishments from INEGI DENUE.

The model keeps the original event or observation grain in each fact table. Crime and establishment records remain at the individual-record level, while population is stored at the geographic and demographic level.

This design provides the required information to calculate the project KPIs while allowing future analysis by geography, time, crime type, demographic characteristics, and economic activity.
