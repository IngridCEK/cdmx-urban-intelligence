# Clasificación SCIAN para DENUE

## Regla reproducible

`codigo_act` se interpreta como una clave SCIAN de 6 dígitos. El sector se obtiene con los primeros dos dígitos de `codigo_act`.

- **Comercio al por menor:** sector **46**.
- **Servicios:** sectores **51, 52, 53, 54, 55, 56, 61, 62, 71, 72 y 81**.
- **Otro:** cualquier sector restante.

El catálogo reproducible de sectores está en `data/catalogos/scian_sectores.csv`. El catálogo incluye los 20 sectores/rangos sectoriales utilizados por SCIAN para este proyecto; los sectores 31-33 y 48-49 se representan como rangos porque SCIAN agrupa esos códigos en una sola denominación sectorial.

### Justificación

La clasificación separa el comercio minorista del resto de actividades comerciales para construir `Retail Density`, y agrupa como servicios las actividades terciarias de servicios requeridas por el análisis. El comercio al por mayor (sector 43), manufactura (31-33), construcción (23), actividades primarias, gobierno (93) y los demás sectores se mantienen como `otro` para evitar mezclarlos con retail o servicios.

## Decisiones analíticas

### Dominant Economic Activity

Para cada AGEB se cuenta el número de establecimientos asignados por sector SCIAN. La actividad dominante es el sector con mayor número de establecimientos. **En caso de empate, se elige el sector con el código numérico menor**; esto hace que el resultado sea determinista y reproducible. Una AGEB sin establecimientos se etiqueta **`sin_establecimientos`** y no se fuerza una actividad dominante.

### `tipoUniEco` (fijo o semifijo)

Se **incluyen tanto unidades Fijas como Semifijas**. No se excluyen los establecimientos semifijos porque el DENUE los registra como unidades económicas y el KPI de actividad económica pretende contar el universo disponible de establecimientos. En el archivo 05_2026, los valores observados de `tipoUniEco` son `Fijo` y `Semifijo`; no aparece una tercera categoría de ambulante que deba eliminarse.

