"""Control técnico de las respuestas descargadas. NO calcula errores ni efectos: solo estructura, celdas, ejes temporales y cobertura.
Uso: python preflight_pronosticos.py
"""
from comun import *
from metodo import total_diario, nubosidad_diurna, dias, SERIES
from datetime import date, timedelta
import collections

sp = spec()
stations = sp['estaciones']['seleccion']
codes = [s['codigo'] for s in stations]
state = load(STATE / 'descarga_pronosticos.json')
p0, p1 = sp['ventanas']['primaria']['dias_objetivo']
s0, s1 = sp['ventanas']['secundaria']['dias_objetivo']
prim, sec = set(dias(p0, p1)), set(dias(s0, s1))
cells = {}
problems = []
axis = collections.Counter()
nulls = collections.Counter()
valid = {s: collections.Counter() for s in SERIES}   # serie -> ventana -> nº estación-días válidos
cloud_ok = collections.Counter()
n_ok = 0
for key, st in sorted(state['peticiones'].items()):
    if st.get('estado') != 'ok':
        continue
    n_ok += 1
    run, model = st['run'], st['model']
    series = ('IFS' if model == 'ecmwf_ifs025' else 'AIFS') + '_' + run[11:13]
    target = (date.fromisoformat(run[:10]) + timedelta(days=1)).isoformat()
    win = 'primaria' if target in prim else 'secundaria' if target in sec else 'fuera'
    body = json.loads((RAW / 'forecasts' / f'{key}.json').read_text(encoding='utf-8'))
    if len(body) != 34:
        problems.append((key, f'{len(body)} ubicaciones')); continue
    for i, loc in enumerate(body):
        lid = loc.get('location_id'); lid = i if lid is None else lid
        if lid != i:
            problems.append((key, f'location_id {lid} en {i}'))
        cell = (loc['latitude'], loc['longitude'], loc.get('elevation'))
        prev = cells.setdefault(codes[i], cell)
        if prev != cell:
            problems.append((key, f'celda cambia para {codes[i]}: {prev} -> {cell}'))
        h = loc['hourly']
        axis[(series, h['time'][0][11:], len(h['time']))] += 1
        sw = h['shortwave_radiation']
        nulls[(series, sum(v is None for v in sw))] += 1
        if total_diario(h['time'], sw, target) is not None:
            valid[series][win] += 1
        if series in ('IFS_00', 'AIFS_00') and h.get('cloud_cover') and nubosidad_diurna(h['time'], h['cloud_cover'], target) is not None:
            cloud_ok[series] += 1
print('peticiones ok leídas:', n_ok)
print('problemas estructurales:', problems[:10], '(total', len(problems), ')')
print('ejes (serie, primera marca, longitud) -> peticiones:', dict(axis))
print('nulos de radiación por respuesta-ubicación (serie, nº nulos) -> recuento:', dict(sorted(nulls.items())))
print('estación-días con total diario válido por serie y ventana:', {s: dict(v) for s, v in valid.items()})
print('nubosidad diurna válida (estación-días):', dict(cloud_ok))
dist = []
for c, (la, lo, el) in cells.items():
    s = next(x for x in stations if x['codigo'] == c)
    dist.append((c, round(abs(la - s['latitud']), 3), round(abs(lo - s['longitud']), 3), el, s['ficha_altitud'] if 'ficha_altitud' in s else None))
worst = max(dist, key=lambda x: max(x[1], x[2]))
print('celdas: máxima separación estación-celda (grados):', worst[:3], '| todas ≤ 0.125°:', all(max(d[1], d[2]) <= 0.1251 for d in dist))
est = load(OUT / 'estaciones.json')
alts = {e['codigo']: e['ficha'].get('altitud') for e in est['estaciones']}
print('elevación celda vs altitud ficha (m), diferencias > 300:', [(c, cells[c][2], alts[c]) for c in codes if c in cells and alts[c] is not None and abs(cells[c][2] - alts[c]) > 300])
dump(STATE / 'preflight_pronosticos.json', {'generado_utc': now(), 'peticiones_ok': n_ok, 'problemas': problems, 'ejes': {str(k): v for k, v in axis.items()}, 'nulos': {str(k): v for k, v in nulls.items()},
      'validos_por_serie_ventana': {s: dict(v) for s, v in valid.items()}, 'nubosidad_ok': dict(cloud_ok), 'celdas': {c: {'lat': v[0], 'lon': v[1], 'elev': v[2]} for c, v in cells.items()}})
