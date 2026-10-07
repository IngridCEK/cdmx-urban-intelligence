# Reportes de calidad

Esta carpeta conserva reportes pequenos de validacion para documentar la trazabilidad sin versionar los archivos de datos procesados.

- `censo_2020_ageb_reporte_calidad.json`: reporte de la salida de Persona B para Censo 2020.
- `denue_2026_reporte_calidad.json`: reporte base de la salida DENUE 05/2026 de Persona B. Fue generado antes de cambiar la tolerancia compartida de borde de 100 km a 10 km. Los 11 puntos tolerados del DENUE estan a un maximo de 2.189 km, por lo que la clasificacion esperada no cambia; el campo de tolerancia debe actualizarse regenerando el reporte con el ETL actual.
- El reporte de delitos debe agregarse aqui despues de regenerar `src.etl.crime` con la regla compartida de 10 km. No se inventa un reporte sin ejecutar los datos fuente.

Los archivos grandes generados en `data/processed/` permanecen ignorados por Git.
