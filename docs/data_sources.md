# Inventario de fuentes - Ciudad de México (entidad 09)

## 1. Polígonos: Marco Geoestadístico (INEGI)
- **Producto:** Marco Geoestadístico, Censo de Población y Vivienda 2020 (metadato `mg_cpyv2020_09`)
- **Archivo original:** `09_ciudaddemexico.zip`
- **URL de descarga:** https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/marcogeo/889463807469/09_ciudaddemexico.zip
- **Copia local:** `data/raw/09_ciudaddemexico/` (descomprimido)
- **Fecha de descarga:** 4 de octubre de 2026
- **Formato:** Shapefile
- **Capas usadas:** `09a.shp` (AGEB urbanas) y `09mun.shp` (alcaldías)
- **Grano:** un polígono por AGEB urbana (<N_AGEB> en total)
- **CRS original:** <CRS>
- **Clave de enlace:** `CVEGEO` (13 caracteres)
- **Responsable:** <tu nombre>

## 2. Delitos: Carpetas de investigación FGJ CDMX
- **Portal:** https://datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico
- **Recurso:** Carpetas de Investigación (2023), del 01 de enero al 31 de diciembre de 2023
- **Archivo original:** `carpetadeinvestigacion2023.csv`
- **Copia local:** `data/raw/carpetas_fgj_2023.csv` (70 MB)
- **Fecha de descarga:** 4 de octubre de 2026
- **Formato:** CSV
- **Grano:** una fila por carpeta de investigación (242,392 registros)
- **Variables clave:** `delito`, `categoria_delito`, `fecha_inicio`, `fecha_hecho`, `alcaldia_catalogo`, `latitud`, `longitud`
- **Responsable:** <tu nombre>

**Por qué 2023:** es el año completo más reciente disponible (2024 solo cubre hasta julio), evita los años afectados por la pandemia (2020 y 2021) y mantiene un volumen manejable para procesar.

## 3. Censo 2020 por AGEB (INEGI)
Pendiente (Persona B).
- URL: https://www.inegi.org.mx/programas/ccpv/2020/
- Qué bajar: tabulados "Principales resultados por AGEB y manzana urbana", entidad 09 (CSV)

## 4. DENUE (INEGI)
Pendiente (Persona B).
- URL: https://www.inegi.org.mx/app/descarga/
- Qué bajar: archivos de CDMX (CSV y/o SHP)

## Claves INEGI
- CDMX = entidad `09`; alcaldías = municipios `002` a `017`.
- `CVEGEO` de AGEB = entidad (2) + municipio (3) + localidad (4) + AGEB (4) = 13 caracteres.
- Censo: usar las filas de total por AGEB (manzana = `000`), no las de manzana.

## Limitaciones conocidas
- El Censo por AGEB solo cubre AGEB **urbanas**; 357 delitos caen en la CDMX pero fuera de toda AGEB urbana (zonas rurales o sin AGEB).
- Indicadores del Censo con menos de 3 unidades vienen con asterisco -> se tratan como faltantes.
- 14,147 registros de delitos (5.84%) no traen coordenadas válidas y 51 caen fuera de la CDMX.
- El archivo está organizado por fecha de inicio de la carpeta (`anio_inicio`), no por fecha del hecho: algunos hechos son de 2022.
- Desfase temporal entre fuentes: Censo 2020, DENUE reciente y delitos de 2023.
- Para áreas y distancias se usa `WORK_CRS` (EPSG:32614).
- Los datos crudos no se suben a Git (`data/raw/` está en `.gitignore`).