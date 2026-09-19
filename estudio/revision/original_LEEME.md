# Paquete reproducible: medicion a escala (actualizacion 00→06 UTC e IA frente a fisica)

Contenido: `code/` (programas congelados), `metodo_fijado.json` + recibo, `estaciones.json`, `resultados.json`, `panel_analisis.json`,
`verificacion.json`, `datos/` (observaciones preparadas, fichas, manifiesto de datos heredados), `raw/siar/` (respuestas SiAR con campos de sesión omitidos y recibos),
`raw/forecasts/` (respuestas íntegras de la Single Runs API y recibos), `raw/heredado/` (semihorarios y pronósticos de trabajos previos, con procedencia),
`state/` (estado de las descargas y registros) y `manifest_sha256.json`.

`verificacion.json` e `integridad_paquete.json` NO van dentro del zip: comprueban este mismo zip y su hash, y
se entregan junto a el en la carpeta de salida.

Reproducir sin red (Python >= 3.12, numpy; matplotlib solo para figuras):

    python code/test_metodo.py
    python code/preparar_observaciones.py
    python code/analizar.py
    python code/diagnostico_posterior.py
    python code/informe.py
    python code/verificar.py

`analizar.py` reescribe `resultados.json` en outputs/…; para no tocar el original, copie el paquete a otra carpeta con la misma estructura
`qu/work/medicion_escala` y `qu/outputs/latencia_pronosticos/medicion_escala`, o ejecute con `--out`.
No ejecute los descargadores sobre un paquete entregado. Datos: MAPA/SiAR y ECMWF vía Open-Meteo, con sus condiciones.
