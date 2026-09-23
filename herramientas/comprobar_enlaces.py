"""Comprueba los enlaces internos de Markdown versionados y nuevos no ignorados.

Falla si encuentra un enlace relativo que no existe, o una ruta absoluta de la maquina donde se
hizo el trabajo. No comprueba enlaces http: eso exigiria red.

Uso: python herramientas/comprobar_enlaces.py     (desde la raiz del repositorio)
"""
import re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import unquote
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENLACE = re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
ABSOLUTA = re.compile(r'^[A-Za-z]:[/\\]|^/(?:home|Users)/')


def versionados():
    r = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', '*.md'], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        roots = [RAIZ / 'docs', RAIZ / 'estudio', RAIZ / 'herramientas']
        files = list(RAIZ.glob('*.md'))
        for root in roots:
            if root.exists(): files.extend(root.rglob('*.md'))
        return sorted(p.relative_to(RAIZ).as_posix() for p in files if 'reproduccion' not in p.parts)
    return sorted(set(l for l in r.stdout.splitlines() if l.strip()))


class RecursosHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.destinos = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value and name in ('src', 'href'):
                self.destinos.append((self.getpos()[0], value))
            elif value and name == 'srcset':
                self.destinos.extend((self.getpos()[0], item.strip().split()[0])
                                     for item in value.split(',') if item.strip())


def main():
    fallos = []
    n_arch = n_enl = 0
    for rel in versionados():
        p = RAIZ / rel
        if not p.exists():
            continue
        n_arch += 1
        texto = p.read_text(encoding='utf-8', errors='replace')
        html = RecursosHTML()
        html.feed(texto)
        destinos = list(html.destinos)
        for i, linea in enumerate(texto.splitlines(), 1):
            destinos.extend((i, m.group(1)) for m in ENLACE.finditer(linea))
        for i, destino in destinos:
            n_enl += 1
            if destino.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            if ABSOLUTA.match(destino):
                fallos.append(f'{rel}:{i}: ruta absoluta de una maquina concreta -> {destino}')
                continue
            objetivo = (p.parent / unquote(destino.split('#')[0])).resolve()
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
