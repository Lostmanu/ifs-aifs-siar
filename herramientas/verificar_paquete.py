"""Comprueba SHA-256 del ZIP completo antes de extraerlo. No necesita red."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo', type=Path, help='ZIP o carpeta que contenga un único ZIP')
    args = parser.parse_args()
    path = args.archivo
    if path.is_dir():
        files = list(path.glob('*.zip'))
        if len(files) != 1:
            parser.error('La carpeta debe contener exactamente un ZIP.')
        path = files[0]
    if not path.is_file():
        parser.error('No existe el archivo indicado.')
    reference = json.loads((ROOT / 'docs/integridad_git.json').read_text(encoding='utf-8'))
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    print(f'Versión esperada: {reference["version"]}')
    print(f'SHA-256: {actual}')
    if actual != reference['origen_paquete']:
        print('FAIL: no coincide con el paquete registrado. No lo extraiga como esa versión.')
        return 1
    print('PASS: coincide con el SHA-256 registrado del paquete completo.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
