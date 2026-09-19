"""Construye datos_y_analisis.zip (código congelado, recibos, datos, resultados) con manifest_sha256.json, y lo verifica.
Uso: python empaquetar.py
"""
from comun import *
import zipfile

LEEME = """# Paquete reproducible: medicion a escala (actualizacion 00→06 UTC e IA frente a fisica)

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
"""


def main():
    target = OUT / 'datos_y_analisis.zip'
    (BASE / 'LEEME.md').write_text(LEEME, encoding='utf-8')
    files = []
    for sub in ('code', 'datos', 'raw', 'state'):
        for p in sorted((BASE / sub).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and 'sim' not in p.parts and p.suffix != '.pyc':
                files.append((p, str(p.relative_to(BASE)).replace('\\', '/')))
    for name in ('LEEME.md', 'metodo_fijado.json', 'encargo_v2.md'):
        files.append((BASE / name, name))
    # verificacion.json e integridad_paquete.json quedan FUERA: comprueban este zip y no pueden ir dentro de el.
    # metodo_fijado.json va DOS veces (raiz y outputs/) porque comun.spec() lo busca en outputs/ primero.
    for name in ('metodo_fijado.json', 'metodo_fijado_recibo.json', 'estaciones.json', 'resultados.json', 'panel_analisis.json', 'informe.md', 'figura_principal.png', 'figura_sensibilidad.png'):
        if (OUT / name).exists():
            files.append((OUT / name, 'outputs/' + name))
    manifest = {arc: sha256_file(p) for p, arc in files}
    dump(BASE / 'manifest_sha256.json', manifest)
    files.append((BASE / 'manifest_sha256.json', 'manifest_sha256.json'))
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for p, arc in files:
            z.write(p, arc)
    # verificación: leer el zip y comparar hashes
    bad = []
    with zipfile.ZipFile(target) as z:
        names = set(z.namelist())
        for arc, h in manifest.items():
            if arc not in names or sha256_bytes(z.read(arc)) != h:
                bad.append(arc)
    info = {'zip': str(target), 'bytes': target.stat().st_size, 'sha256': sha256_file(target), 'ficheros': len(files), 'manifiesto_ok': not bad, 'fallidos': bad, 'generado_utc': now()}
    dump(OUT / 'integridad_paquete.json', info)
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
