"""SOLO PARA PROBAR EL CÓDIGO: fabrica respuestas sintéticas con el formato multiubicación de la Single Runs API
a partir de las observaciones reales más ruido, con un efecto conocido, en state/sim/. Nunca alimenta resultados reales.
"""
from comun import *
from metodo import dias
from datetime import date, datetime, timedelta
import numpy as np, sys

sp = spec()
stations = sp['estaciones']['seleccion']
obs = load(DATOS / 'observaciones_diarias.json')
rng = np.random.default_rng(7)
SIM = STATE / 'sim'
(SIM / 'forecasts').mkdir(parents=True, exist_ok=True)
state = {'peticiones': {}, 'llamadas_contadas': []}
first = date.fromisoformat(sp['ventanas']['pasadas_a_descargar']['primera'][:10])
last = date.fromisoformat(sp['ventanas']['pasadas_a_descargar']['ultima'][:10])
# efectos simulados: IFS_06 mejor que IFS_00 (ruido 0,9×), AIFS_00 peor (ruido 1,15×), AIFS_06 = AIFS_00 × 0,95
noise = {('ecmwf_ifs025', '00'): 1.0, ('ecmwf_ifs025', '06'): 0.9, ('ecmwf_aifs025_single', '00'): 1.15, ('ecmwf_aifs025_single', '06'): 1.09}
d = first
obs_by = {s['codigo']: {r['fecha']: r['wh_m2'] for r in obs[s['codigo']] if r['valido']} for s in stations}
while d <= last:
    for cyc in ('00', '06'):
        for model in sp['ventanas']['pasadas_a_descargar']['modelos']:
            run = f'{d.isoformat()}T{cyc}:00'
            key = f'{run.replace(":", "")}_{model}'
            if d == date(2026, 4, 2) and cyc == '06':
                state['peticiones'][key] = {'run': run, 'model': model, 'estado': 'unavailable'}
                continue
            t0 = datetime(d.year, d.month, d.day)
            times = [(t0 + timedelta(hours=h)).strftime('%Y-%m-%dT%H:%M') for h in range(72)]
            body = []
            for i, s in enumerate(stations):
                target = (d + timedelta(days=1)).isoformat()
                daily = obs_by[s['codigo']].get(target)
                if daily is None:
                    daily = 6000.0
                # perfil diurno simple: seno entre 05 y 19 UTC, escalado al total con sesgo +6 % y ruido diario
                day_sigma = 0.12 * noise[(model, cyc)]
                scale = 1.06 * (1 + rng.normal(0, day_sigma))
                sw, cc = [], []
                for h in range(72):
                    hod = h % 24
                    prof = max(0.0, np.sin(np.pi * (hod - 5) / 14)) if 5 < hod < 19 else 0.0
                    sw.append(None if (cyc == '06' and h < 6) else round(prof / 8.913 * daily * scale / 1.0, 1))
                    cc.append(None if (cyc == '06' and h < 6) else round(float(rng.uniform(0, 100)), 1))
                body.append({'latitude': round(s['latitud'] * 4) / 4, 'longitude': round(s['longitud'] * 4) / 4, 'elevation': 100.0, 'utc_offset_seconds': 0, 'timezone': 'GMT', 'location_id': i,
                             'hourly_units': {'time': 'iso8601', 'shortwave_radiation': 'W/m²', 'cloud_cover': '%'}, 'hourly': {'time': times, 'shortwave_radiation': sw, 'cloud_cover': cc}})
            (SIM / 'forecasts' / f'{key}.json').write_text(json.dumps(body), encoding='utf-8')
            state['peticiones'][key] = {'run': run, 'model': model, 'estado': 'ok'}
    d += timedelta(days=1)
dump(SIM / 'descarga_pronosticos.json', state)
print('simulados:', len(state['peticiones']))
