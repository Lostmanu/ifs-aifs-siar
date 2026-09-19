"""Comprueba los enlaces internos de todos los Markdown versionados del repositorio.

Falla si encuentra un enlace relativo que no existe, o una ruta absoluta de la maquina donde se
hizo el trabajo. No comprueba enlaces http: eso exigiria red.

Uso: python herramientas/comprobar_enlaces.py     (desde la raiz del repositorio)
"""
import re, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENLACE = re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
ABSOLUTA = re.compile(r'^[A-Za-z]:[/\\]|^/(?:home|Users)/')


def versionados():
    r = subprocess.run(['git', 'ls-files', '*.md'], cwd=RAIZ, capture_output=True, text=True)
    if r.returncode != 0:
        return sorted(p.relative_to(RAIZ).as_posix() for p in RAIZ.rglob('*.md') if '.git' not in p.parts)
    return [l for l in r.stdout.splitlines() if l.strip()]


def main():
    fallos = []
    n_arch = n_enl = 0
    for rel in versionados():
        p = RAIZ / rel
        if not p.exists():
            continue
        n_arch += 1
        for i, linea in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            for m in ENLACE.finditer(linea):
                destino = m.group(1)
                n_enl += 1
                if destino.startswith(('http://', 'https://', 'mailto:', '#')):
                    continue
                if ABSOLUTA.match(destino):
                    fallos.append(f'{rel}:{i}: ruta absoluta de una maquina concreta -> {destino}')
                    continue
                objetivo = (p.parent / destino.split('#')[0]).resolve()
                if not objetivo.exists():
                    fallos.append(f'{rel}:{i}: enlace roto -> {destino}')
    print(f'{n_arch} ficheros Markdown, {n_enl} enlaces revisados')
    if fallos:
        print(f'FAIL: {len(fallos)} problemas')
        for f in fallos:
            print('  -', f)
        return 1
    print('PASS: ningun enlace roto ni ruta absoluta')
    return 0


if __name__ == '__main__':
    sys.exit(main())
