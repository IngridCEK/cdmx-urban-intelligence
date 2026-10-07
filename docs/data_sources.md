# Inventario de fuentes - Ciudad de México (entidad 09)

## 1. Polígonos: Marco Geoestadístico (INEGI)
- **Producto:** Marco Geoestadístico, Censo de Población y Vivienda 2020 (metadato `mg_cpyv2020_09`)
- **Archivo original:** `09_ciudaddemexico.zip`
- **URL de descarga:** https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/marcogeo/889463807469/09_ciudaddemexico.zip
- **Copia local:** `data/raw/09_ciudaddemexico/` (descomprimido)
- **Fecha de descarga:** 4 de octubre de 2026
- **Formato:** Shapefile
- **Capas usadas:** `09a.shp` (AGEB urbanas) y `09mun.shp` (alcaldías)
- **Grano:** un polígono por AGEB urbana (2,431 en total)
- **CRS original:** name: MEXICO_ITRF_2008_LCC
                         epsg: None
- **Clave de enlace:** `CVEGEO` (13 caracteres)
- **Responsable:** INGRID CASTILLO

## 2. Delitos: Carpetas de investigación FGJ CDMX
- **Portal:** https://datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico
- **Recurso:** Carpetas de Investigación (2023), del 01 de enero al 31 de diciembre de 2023
- **Archivo original:** `carpetadeinvestigacion2023.csv`
- **Copia local:** `data/raw/carpetas_fgj_2023.csv` (70 MB)
- **Fecha de descarga:** 4 de octubre de 2026
- **Formato:** CSV
- **Grano:** una fila por carpeta de investigación (242,392 registros)
- **Variables clave:** `delito`, `categoria_delito`, `fecha_inicio`, `fecha_hecho`, `alcaldia_catalogo`, `latitud`, `longitud`
- **Responsable:** INGRID CASTILLO

**Por qué 2023:** es el año completo más reciente disponible (2024 solo cubre hasta julio), evita los años afectados por la pandemia (2020 y 2021) y mantiene un volumen manejable para procesar.

## 3. Censo 2020 por AGEB (INEGI)
- **Producto:** Censo de Población y Vivienda 2020, "Principales resultados por AGEB y manzana urbana", entidad 09
- **Archivo original:** `resageburb_09csv20.zip` (contiene `RESAGEBURB_09CSV20.csv`)
- **URL de descarga:** https://www.inegi.org.mx/programas/ccpv/2020/#tabulados
- **Copia local:** `data/raw/resageburb_09csv20/RESAGEBURB_09CSV20.csv` (44 MB, descomprimido)
- **Fecha de descarga:** 4 de octubre de 2026
- **Formato:** CSV, UTF-8 con BOM, 230 columnas, 68,941 filas
- **Grano original:** una fila por unidad geográfica en distintos niveles: 1 total de la entidad, 16 totales de municipio, 35 totales de localidad, 2,433 totales de AGEB (`MZA` = `000`) y 66,456 manzanas
- **Grano usado:** una fila por AGEB urbana (`AGEB` distinto de `0000` y `MZA` = `000`): 2,433 filas
- **Clave de enlace:** `CVEGEO` = `ENTIDAD` + `MUN` + `LOC` + `AGEB` (13 caracteres). Se debe leer el CSV con todo como texto (`dtype=str`) para no perder los ceros a la izquierda; 222 AGEB traen letras en su clave
- **Variables clave:** `POBTOT`, `POB0_14`, `POB15_64`, `POB65_MAS`, `P_12YMAS`, `PEA`, `POCUPADA`, `PE_INAC` (detalle en `docs/kpi_variables.md`)
- **Datos faltantes:** los valores suprimidos por confidencialidad vienen como `*` (20,181 celdas en las filas de AGEB). `POBTOT` no tiene ninguno; `PEA` y `P_12YMAS` tienen 10 cada uno
- **Responsable:** Joel Pérez

## 4. DENUE (INEGI)
- **Producto:** Directorio Estadístico Nacional de Unidades Económicas (DENUE) 05_2026, Ciudad de México (fecha de actualización del conjunto: 20 de mayo de 2026)
- **Archivo original:** `denue_09_csv.zip` (contiene `conjunto_de_datos/denue_inegi_09_.csv`, `diccionario_de_datos/denue_diccionario_de_datos.csv` y `metadatos/metadatos_denue.txt`)
- **URL de descarga:** https://www.inegi.org.mx/app/descarga/?ti=6
- **Copia local:** `data/raw/denue_09_csv/` (descomprimido; el CSV pesa 260 MB)
- **Fecha de descarga:** 4 de octubre de 2026
- **Formato:** CSV, codificación ISO-8859-1 (leer con `encoding="latin-1"`), 42 columnas, 462,732 filas
- **Grano:** una fila por establecimiento (`id` es único)
- **Ubicación:** `latitud` y `longitud` en grados decimales, más las claves `cve_ent`, `cve_mun`, `cve_loc`, `ageb` y `manzana`. `cve_ent` + `cve_mun` + `cve_loc` + `ageb` reconstruye el `CVEGEO` de la AGEB
- **Variables clave:** `id`, `codigo_act` (SCIAN 2018 a 6 dígitos), `nombre_act`, `per_ocu` (estrato de personal ocupado), `latitud`, `longitud`, `ageb`, `manzana`
- **Período de alta:** `fecha_alta` va de 2010-07 a 2026-04
- **Responsable:** Joel Pérez

**Nota de calidad (DENUE):**
- 3 registros tienen coordenadas fuera de la CDMX (latitud hasta 32.5, longitud hasta -116.9); se descartan o se corrigen en el ETL.
- 1,140 registros (0.25%) traen una clave de AGEB que no existe en el Censo (localidades no urbanas); y 13 AGEB del Censo no tienen ningún establecimiento.
- `per_ocu` es texto con 7 estratos (de "0 a 5 personas" a "251 y más personas"), no un número de empleados.
- Las columnas de nombre, razón social, teléfono, correo y sitio web no se necesitan para los KPIs.
- El conjunto es una foto de 2026 y el Censo es de 2020 (ver desfase temporal abajo).

## Claves INEGI
- CDMX = entidad `09`; alcaldías = municipios `002` a `017`.
- `CVEGEO` de AGEB = entidad (2) + municipio (3) + localidad (4) + AGEB (4) = 13 caracteres.
- Censo: usar las filas de total por AGEB (manzana = `000`), no las de manzana.

## Limitaciones conocidas
- El Censo por AGEB solo cubre AGEB **urbanas**; 357 delitos caen en la CDMX pero fuera de toda AGEB urbana (zonas rurales o sin AGEB).
- Indicadores del Censo con menos de 3 unidades vienen con asterisco -> se tratan como faltantes.
- 14,147 registros de delitos (5.84%) no traen coordenadas válidas. Los 51 puntos que quedaban apenas fuera del polígono administrativo están a 1.2 m o menos del límite y, con la tolerancia cartográfica compartida de 10 km, se conservan como `dentro_cdmx_sin_ageb`.
- El archivo está organizado por fecha de inicio de la carpeta (`anio_inicio`), no por fecha del hecho: algunos hechos son de 2022.
- Desfase temporal entre fuentes: Censo 2020, DENUE reciente y delitos de 2023.
- Para áreas y distancias se usa `WORK_CRS` (EPSG:32614).
- Los datos crudos no se suben a Git (`data/raw/` está en `.gitignore`).