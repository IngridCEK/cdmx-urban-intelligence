# Inventario de fuentes - Ciudad de Mexico (entidad 09)
_Completar por fuente: version/fecha, formato, grano, licencia, fecha de descarga, responsable._

| Capa | URL | Que bajar | Responsable |
|---|---|---|---|
| Censo 2020 por AGEB y manzana urbana | https://www.inegi.org.mx/programas/ccpv/2020/ | Tabulados "Principales resultados por AGEB y manzana urbana", entidad 09 (CSV) | B |
| Marco Geoestadistico (cierre Censo 2020) | https://www.inegi.org.mx/temas/mg/ | Shapefiles de CDMX: AGEB urbanas y alcaldias | A |
| DENUE | https://www.inegi.org.mx/app/descarga/ | Archivos de CDMX (CSV y/o SHP) | B |
| Delitos (FGJ CDMX) | https://datos.cdmx.gob.mx/dataset/carpetas-de-investigacion-fgj-de-la-ciudad-de-mexico | CSV con latitud/longitud | A |

## Claves INEGI
- CDMX = entidad `09`; alcaldias = municipios `002` a `017`.
- `CVEGEO` de AGEB = entidad (2) + municipio (3) + localidad (4) + AGEB (4) = 13 caracteres.
- Censo: usar las filas de total por AGEB (manzana = `000`), no las de manzana.

## Cuidados conocidos (documentar en README)
- Censo por AGEB solo cubre AGEB **urbanas**; los delitos en zonas rurales (p. ej. Milpa Alta, Tlalpan, Xochimilco) pueden caer fuera de todo poligono.
- Indicadores con menos de 3 unidades vienen con asterisco en el Censo -> tratar como faltantes.
- No todas las carpetas de delitos traen latitud/longitud; algunas traen coordenadas invalidas o fuera de la CDMX.
- Desfase temporal: Censo 2020, DENUE reciente y delitos de otra ventana. Definir y justificar la ventana de delitos.
- Verificar el CRS en el `.prj` de los shapefiles; para areas y distancias usar `WORK_CRS` (EPSG:32614).
