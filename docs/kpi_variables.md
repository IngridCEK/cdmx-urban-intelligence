# Variables fuente requeridas por los KPIs

## Geografía (Marco Geoestadístico, Persona A)
| Variable | Origen | Uso en KPIs |
|---|---|---|
| `CVEGEO` | `09a.shp` | Clave de enlace entre todas las capas |
| `area_km2` | Calculada con la geometría en EPSG:32614 | Densidad de población, de negocios, de comercio y de servicios |
| `NOMGEO` (alcaldía) | `09mun.shp` | Agrupar y comparar por alcaldía |

## Delitos (FGJ CDMX, Persona A)
| Variable | Uso en KPIs |
|---|---|
| `latitud`, `longitud` | Crear el punto y asignarlo a una AGEB (spatial join) |
| `CVEGEO` (derivada del join) | Total de delitos por AGEB |
| `categoria_delito`, `delito` | Tipo de delito |
| `fecha_hecho`, `hora_hecho` | Atributos temporales |

| KPI | Cálculo | Fuentes |
|---|---|---|
| Total Crime Incidents | Conteo de delitos por `CVEGEO` | Delitos |
| Crime Rate | Delitos / población × 1,000 | Delitos + Censo (población total) |
| Population Density | Población / `area_km2` | Censo + Geografía |
| Business Density, Retail Density, Service Density | Establecimientos / `area_km2` | DENUE + Geografía |

## Censo y DENUE (Persona B)

### Censo 2020 (`RESAGEBURB_09CSV20.csv`)
Se usan solo las filas de total por AGEB: `AGEB` distinto de `0000` y `MZA` = `000`. Los valores `*` se tratan como faltantes (NULL), no como cero.

| Variable | Descripción | Uso en KPIs |
|---|---|---|
| `ENTIDAD`, `MUN`, `LOC`, `AGEB` | Claves geográficas | Se concatenan para formar `CVEGEO` |
| `NOM_MUN` | Nombre de la alcaldía | Agrupar y comparar por alcaldía |
| `POBTOT` | Población total | Total Population; denominador de Population Density, Crime Rate y Businesses per 1,000 Residents |
| `POB0_14` | Población de 0 a 14 años | Population by Age Group |
| `POB15_64` | Población de 15 a 64 años | Population by Age Group |
| `POB65_MAS` | Población de 65 años y más | Population by Age Group |
| `P_18A24` | Población de 18 a 24 años (opcional) | Grupo joven, por si se quiere comparar con delitos |
| `P_12YMAS` | Población de 12 años y más | Base (denominador) de la tasa de PEA |
| `PEA` | Población económicamente activa | Economically Active Population Rate = `PEA` / `P_12YMAS` |
| `POCUPADA`, `PDESOCUP` | Población ocupada y desocupada (opcionales) | Detalle de la PEA |
| `PE_INAC` | Población no económicamente activa (opcional) | Complemento de la PEA |
| `VIVTOT`, `TVIVHAB`, `GRAPROES` (opcionales) | Viviendas totales, viviendas habitadas, grado promedio de escolaridad | Indicadores de vivienda y contexto (el enunciado pide "housing and related indicators") |

Grupos de edad: `POB0_14`, `POB15_64` y `POB65_MAS` son excluyentes y cubren casi toda la población. Para las proporciones se divide entre `POBTOT`. Hay columnas más finas (`P_0A2`, `P_3A5`, `P_6A11`, `P_12A14`, `P_15A17`, `P_18A24`, `P_60YMAS`) si el equipo prefiere otros cortes, pero tienen más suprimidos.

Cuidados:
- `POBTOT` no tiene valores suprimidos; `PEA` y `P_12YMAS` tienen 10 AGEB con `*`, y los grupos de edad entre 10 y 22.
- 17 AGEB tienen `POBTOT` = 0: proteger las divisiones (Population Density, Crime Rate, Businesses per 1,000 Residents).
- `PEA` + `PE_INAC` no siempre suma `P_12YMAS` (hay población con condición de actividad no especificada), por eso la tasa se calcula contra `P_12YMAS` y no contra la suma.
- Los tres grupos de edad no siempre suman `POBTOT` (edad no especificada); en 455 AGEB la diferencia es positiva, y en 24 pasa de 50 personas.

### DENUE (`denue_inegi_09_.csv`)

| Variable | Descripción | Uso en KPIs |
|---|---|---|
| `id` | Identificador único del establecimiento | Llave del hecho; evita duplicados |
| `codigo_act` | Clave SCIAN 2018 a 6 dígitos | Sector = primeros 2 dígitos; subsector = primeros 3. Retail Density, Service Density, Dominant Economic Activity |
| `nombre_act` | Nombre de la clase SCIAN | Descripción de la actividad (dimensión SCIAN) |
| `per_ocu` | Estrato de personal ocupado (7 categorías) | Tamaño del establecimiento |
| `latitud`, `longitud` | Coordenadas | Spatial join a AGEB (mismo método que los delitos) |
| `cve_ent`, `cve_mun`, `cve_loc`, `ageb`, `manzana` | Claves geográficas del propio DENUE | Reconstruir `CVEGEO` y validar el spatial join |
| `fecha_alta` | Mes de alta en el directorio | Referencia temporal |
| `tipoUniEco` | Fijo o semifijo | Opcional, para excluir ambulantes si se decide |

No se necesitan para los KPIs: `nom_estab`, `raz_social`, `telefono`, `correoelec`, `www` ni las columnas de domicilio.

KPIs de DENUE:

| KPI | Cálculo | Variables |
|---|---|---|
| Total Businesses | Conteo de `id` por `CVEGEO` | `id` |
| Business Density | Establecimientos / `area_km2` | `id`, `area_km2` |
| Businesses per 1,000 Residents | Establecimientos / `POBTOT` × 1,000 | `id`, `POBTOT` |
| Retail Density | Establecimientos con sector SCIAN 46 / `area_km2` | `codigo_act` |
| Service Density | Establecimientos de sectores de servicios / `area_km2` | `codigo_act` |
| Dominant Economic Activity | Sector (2 dígitos) con más establecimientos en la AGEB | `codigo_act` |
| Crime relative to Business Activity | Delitos / establecimientos | Delitos + `id` |
| Incidents by Type and Time | Conteo de delitos asignados por tipo y por fecha/hora | Delitos (categoria_delito, delito, fecha_hecho, hora) |

Propuesta de agrupación SCIAN (a confirmar con el equipo antes de calcular):
- **Comercio al por menor (retail):** sector 46 (212,251 establecimientos, 45.9% del total).
- **Servicios:** sectores 51, 52, 53, 54, 55, 56, 61, 62, 71, 72 y 81 (192,925 establecimientos).
- **Fuera de ambos grupos:** sector 43 (comercio al por mayor), 31-33 (manufactura), 11, 21, 22, 23, 48, 49 y 93 (gobierno). El 93 se excluye porque son instituciones públicas.

Cuidados:
- `per_ocu` es un estrato, no un número. Para ordenarlo hay que mapearlo a una escala (1 a 7) en la dimensión de tamaño.
- `codigo_act` tiene 931 valores distintos; el catálogo de nombres de sector no viene en el CSV y se arma desde el SCIAN 2018.
- Leer `ageb`, `manzana`, `cve_loc` y `codigo_act` como texto (`dtype=str`). Hay `ageb` con letras en 39,979 registros.
- Eliminar los 3 registros con coordenadas fuera de la CDMX antes del spatial join.
