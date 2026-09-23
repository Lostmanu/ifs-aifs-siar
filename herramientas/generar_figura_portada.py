"""Vista SVG determinista de resultados ya publicados; no recalcula el análisis.

Python estándar, sin red ni bibliotecas gráficas. --check detecta imágenes o datos
de portada desactualizados. Los informes y las figuras científicas se conservan.
"""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'estudio/outputs/resultados.json'
OUT = ROOT / 'docs/assets'
INK, MUTED, GRID = '#183137', '#465c62', '#dce5e6'
COLORS = {'H1': '#216e6a', 'H2': '#a54c34'}


def number(x):
    return f'{x:+.2f}'.replace('.', ',').replace('-', '−')


def dataset():
    result = json.loads(SOURCE.read_text(encoding='utf-8'))
    rows = []
    for hypothesis in ['H1', 'H2']:
        for scenario in ['publicada', 'k095']:
            if scenario == 'publicada':
                pointer = f'/primaria/comparaciones/{hypothesis}/por_bloque/7'
                value = result['primaria']['comparaciones'][hypothesis]['por_bloque']['7']
            else:
                pointer = f'/sensibilidad_determinista/por_k/0.95/comparaciones/{hypothesis}/7'
                value = result['sensibilidad_determinista']['por_k']['0.95']['comparaciones'][hypothesis]['7']
            rows.append({'hipotesis': hypothesis, 'escenario': scenario, 'efecto': value['efecto'],
                         'ic95': value['ic95'], 'n': value['n'], 'json_pointer': pointer})
    return {'fuente': SOURCE.relative_to(ROOT).as_posix(),
            'sha256_fuente': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'ventana': result['primaria']['dias'], 'bloque_dias': 7,
            'nota': 'Vista de resultados existentes. IC percentiles, no simultáneos. No estima el k real.',
            'filas': rows}


def svg(data, mobile=False, dark=False):
    ink = '#e2edf0' if dark else INK
    muted = '#adc1c6' if dark else MUTED
    grid = '#30434b' if dark else GRID
    background = '#0d1117' if dark else '#fff'
    colors = {'H1': '#5bc0b8', 'H2': '#f09b7f'} if dark else COLORS
    width, height = (440, 720) if mobile else (960, 580)
    xmin, xmax = -12, 12
    left, right = (36, 404) if mobile else (270, 896)
    scale = lambda x: left + (x - xmin) / (xmax - xmin) * (right - left)
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
                '<title id="title">El resultado cambia con la escala de referencia</title>',
                '<desc id="desc">Mejora relativa del MAE e intervalos del 95 por ciento con bloques de siete días. H1: 1,47 por ciento con SiAR publicada y 0,44 con O/0,95. H2: 7,57 y menos 5,64. La escala no identifica error del sensor.</desc>',
                f'<rect width="{width}" height="{height}" fill="{background}"/>',
                '<g font-family="DejaVu Sans, Arial, sans-serif">']
    def text(x, y, value, size=18, weight=400, color=INK, anchor='start'):
        color = ink if color == INK else muted if color == MUTED else color
        elements.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>')
    def line(x1, y1, x2, y2, color=GRID, stroke=1, extra=''):
        color = grid if color == GRID else muted if color == MUTED else color
        elements.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{stroke}" {extra}/>')
    if mobile:
        text(28, 40, 'El resultado cambia', 27, 700)
        text(28, 75, 'con la referencia', 27, 700)
        text(28, 107, '34 estaciones · 110 días · 2026', 17, color=MUTED)
        titles = [(151, 'H1 · Actualizar IFS 00 → 06'), (377, 'H2 · IFS 00 → AIFS 00')]
        ys = [222, 293, 448, 519]
        plot_top, plot_bottom, axis_y = 185, 546, 572
    else:
        text(36, 49, 'El resultado cambia con la escala de referencia', 30, 700)
        text(36, 84, '34 estaciones SiAR · 14 mayo–31 agosto de 2026 · intervalos del 95 %', 18, color=MUTED)
        titles = [(132, 'H1 · Actualizar IFS de 00 a 06 UTC'), (303, 'H2 · Cambiar de IFS 00 a AIFS 00 UTC')]
        ys = [182, 237, 353, 408]
        plot_top, plot_bottom, axis_y = 159, 433, 465
    for tick in [-10, -5, 0, 5, 10]:
        x = scale(tick)
        # Dos paneles con la misma escala; la guía no invade los encabezados.
        if mobile:
            spans = [(190, 321), (416, 547)]
        else:
            spans = [(159, 255), (330, 427)]
        for start, end in spans:
            line(x, start, x, end, MUTED if tick == 0 else GRID, 1.4 if tick == 0 else 1)
        label = str(tick).replace('-', '−')
        text(x, axis_y, label, 17, color=MUTED, anchor='middle')
    for y, title in titles:
        text(28 if mobile else 36, y, title, 19 if mobile else 21, 700)
    for row, y in zip(data['filas'], ys):
        color = colors[row['hipotesis']]
        original = row['escenario'] == 'publicada'
        label = 'SiAR publicada' if original else 'Escenario O/0,95'
        if mobile:
            text(36, y - 23, label, 17, color=MUTED)
            text(404, y - 23, number(row['efecto']) + ' %', 18, 700, color, 'end')
        else:
            text(36, y + 6, label, 18, color=MUTED)
            text(scale(row['efecto']), y - 15, number(row['efecto']) + ' %', 20, 700, color, 'middle')
        low, high = row['ic95']
        assert xmin <= low <= row['efecto'] <= high <= xmax
        line(scale(low), y, scale(high), y, color, 3)
        for end in [low, high]: line(scale(end), y - 6, scale(end), y + 6, color, 2)
        if original:
            elements.append(f'<circle cx="{scale(row["efecto"]):.3f}" cy="{y}" r="6" fill="{color}"/>')
        else:
            elements.append(f'<rect x="{scale(row["efecto"])-5.5:.3f}" y="{y-5.5}" width="11" height="11" fill="{background}" stroke="{color}" stroke-width="2.5"/>')
    if mobile:
        text(220, 604, 'Reducción relativa del MAE (%)', 17, anchor='middle')
        text(220, 630, 'A la derecha de cero: menor error', 16, color=MUTED, anchor='middle')
        text(28, 677, 'La escala no identifica el error del sensor.', 16, color=MUTED)
        text(28, 701, 'IC95: bootstrap por días, bloques de 7.', 16, color=MUTED)
    else:
        text((left + right) / 2, 500, 'Reducción relativa del MAE (%)', 19, anchor='middle')
        text(36, 539, 'A la derecha de cero: menor error. H1 pierde un intervalo positivo; H2 invierte el signo.', 17, color=MUTED)
        text(36, 566, 'O/0,95 es un escenario de sensibilidad: no estima el error real del sensor.', 17, color=MUTED)
    elements.extend(['</g>', '</svg>'])
    return '\n'.join(elements) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = dataset()
    generated = {'resultado_principal.svg': svg(data), 'resultado_principal_movil.svg': svg(data, True),
                 'resultado_principal_oscuro.svg': svg(data, dark=True),
                 'resultado_principal_movil_oscuro.svg': svg(data, True, True),
                 'resultado_principal.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n'}
    if args.check:
        different = [name for name, content in generated.items()
                     if not (OUT / name).is_file() or (OUT / name).read_text(encoding='utf-8') != content]
        if different:
            parser.exit(1, 'FAIL: portada ausente o desactualizada: ' + ', '.join(different) + '\n')
        print('PASS: cuatro variantes SVG y cuatro resultados con sus intervalos coinciden con la fuente.')
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, content in generated.items():
            (OUT / name).write_text(content, encoding='utf-8', newline='\n')
        print('Generadas cuatro variantes SVG y sus cifras trazables; resultados originales intactos.')


if __name__ == '__main__':
    main()
