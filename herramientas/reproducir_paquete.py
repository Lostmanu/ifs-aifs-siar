"""Ejecuta el lanzador archivado tras inicializar las dependencias del entorno.

NumPy carga numpy.testing de forma diferida. En algunos entornos Windows esa
importación consulta platform.machine(), que puede ejecutar `ver`. Hacerlo antes
del audit hook evita bloquear la inicialización sin relajar el control posterior.
El paquete y su manifiesto permanecen intactos. No descarga archivos.
"""
import argparse
import os
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carpeta', type=Path, help='Raíz del paquete completo extraído')
    parser.add_argument('--figuras', action='store_true')
    args = parser.parse_args()
    folder = args.carpeta.resolve()
    launcher = folder / 'reproducir_offline.py'
    for required in (launcher, folder / 'manifest_portable_sha256.json', folder / 'raw'):
        if not required.exists():
            parser.error(f'Falta {required.name}: use el paquete completo extraído, no el clon.')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    sys.dont_write_bytecode = True
    # Solo inicialización. Ningún método del paquete se ejecuta antes de su guardián.
    import numpy.testing  # noqa: F401
    print('Dependencias inicializadas; se ejecuta el lanzador original con sus controles.', flush=True)
    sys.argv = [str(launcher)] + (['--figuras'] if args.figuras else [])
    runpy.run_path(str(launcher), run_name='__main__')


if __name__ == '__main__':
    main()
