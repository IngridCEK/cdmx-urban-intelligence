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
Pendiente: población total, grupos de edad, población económicamente activa, y de DENUE la actividad SCIAN y el tamaño del establecimiento.