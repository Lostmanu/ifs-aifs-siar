"""Construye la tabla de observaciones diarias válidas (reglas congeladas) y estaciones.json.

No lee pronósticos. Reglas (metodo_fijado.json → observacion.validez_dia):
  fecha única; valor numérico finito; 0,03 ≤ H/H0 ≤ 1,00 (H0 FAO-56 ec. 21); tieneDatos registrado, no filtrante.
Exclusión de estación: < 88 días válidos en la ventana primaria (80 % de 110).
"""
from comun import *
from datetime import date, timedelta
import math

MJ_TO_WH = 1000.0 / 3.6
GSC = 0.0820  # MJ m-2 min-1


def h0_fao56(lat_deg, d):
    """Irradiación extraterrestre diaria sobre superficie horizontal, MJ/m² (FAO-56, ec. 21-25)."""
    J = d.timetuple().tm_yday
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * J / 365)
    delta = 0.409 * math.sin(2 * math.pi * J / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return (24 * 60 / math.pi) * GSC * dr * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))


def parse_rows(rows):
    """Devuelve dict fecha_iso -> lista de (valor_str, tieneDatos)."""
    out = {}
    for r in rows:
        dd, mm, yy = r['fechaStr'].split(' ')[0].split('/')
        f = f'{yy}-{mm}-{dd}'
        assert r['fecha'][:10] == f, (r['fecha'], r['fechaStr'])
        rv = next(v for v in r['resultadoVariable'] if v['nombreCampoTablaDatos'] == 'Radiacion')
        out.setdefault(f, []).append((rv['valor'], bool(r['tieneDatos'])))
    return out


def main():
    sp = spec()
    stations = sp['estaciones']['seleccion']
    crude = load(DATOS / 'observaciones_diarias_crudas.json')
    fichas = {f['sestacionCorto']: f for f in load(DATOS / 'fichas_siar.json')}
    p0, p1 = [date.fromisoformat(x) for x in sp['ventanas']['primaria']['dias_objetivo']]
    s0, s1 = [date.fromisoformat(x) for x in sp['ventanas']['secundaria']['dias_objetivo']]
    n_prim = (p1 - p0).days + 1
    umbral = math.ceil(0.8 * n_prim)
    tabla, cobertura, est_out = {}, {}, []
    for st in stations:
        code = st['codigo']
        rows = crude[code]['rows']
        byday = parse_rows(rows)
        recs = []
        d = date.fromisoformat(crude[code]['rango'][0])
        last = date.fromisoformat(crude[code]['rango'][1])
        motivos = {}
        while d <= last:
            f = d.isoformat()
            entries = byday.get(f, [])
            rec = {'fecha': f, 'publicado': None, 'tieneDatos': None, 'mj_m2': None, 'wh_m2': None, 'h0_mj_m2': round(h0_fao56(st['latitud'], d), 4), 'kt': None, 'valido': False, 'motivo': None}
            if not entries:
                rec['motivo'] = 'sin fila publicada'
            elif len(entries) > 1:
                rec['motivo'] = f'fecha duplicada ({len(entries)} filas)'
                rec['publicado'] = [e[0] for e in entries]
            else:
                val, td = entries[0]
                rec['publicado'] = val
                rec['tieneDatos'] = td
                try:
                    x = float(val)
                    if not math.isfinite(x):
                        raise ValueError
                except (TypeError, ValueError):
                    rec['motivo'] = 'valor vacío o no numérico'
                else:
                    rec['mj_m2'] = x
                    rec['wh_m2'] = x * MJ_TO_WH
                    rec['kt'] = x / rec['h0_mj_m2']
                    if rec['kt'] < 0.03:
                        rec['motivo'] = 'kt < 0,03'
                    elif rec['kt'] > 1.0:
                        rec['motivo'] = 'kt > 1,00'
                    else:
                        rec['valido'] = True
            if rec['motivo']:
                motivos[rec['motivo']] = motivos.get(rec['motivo'], 0) + 1
            recs.append(rec)
            d += timedelta(days=1)
        tabla[code] = recs
        vp = sum(1 for r in recs if r['valido'] and p0 <= date.fromisoformat(r['fecha']) <= p1)
        vs = sum(1 for r in recs if r['valido'] and s0 <= date.fromisoformat(r['fecha']) <= s1)
        td_false = sum(1 for r in recs if r['tieneDatos'] is False)
        excluida = vp < umbral
        cobertura[code] = {'dias_validos_primaria': vp, 'de': n_prim, 'umbral': umbral, 'dias_validos_secundaria': vs, 'de_secundaria': (s1 - s0).days + 1,
                           'tieneDatos_false': td_false, 'motivos_no_valido': motivos, 'excluida_por_cobertura': excluida}
        fi = fichas.get(code, {})
        est_out.append({**{k: v for k, v in st.items()}, 'ficha': {k: fi.get(k) for k in ['altitud', 'municipio', 'paraje', 'estado', 'fechaInstalacion', 'fechaCalibracion', 'fechaUltMod', 'ultimoDato', 'modeloPiranometro', 'fabricantePiranometro', 'modeloDatalogger', 'coordenadas']},
                        'coordenadas_ficha_vs_catalogo_m': None, 'cobertura': cobertura[code]})
        if fi.get('coordenadas'):
            c = fi['coordenadas']
            dlat = (c['lat'] - st['latitud']) * 111_195
            dlon = (c['lng'] - st['longitud']) * 111_195 * math.cos(math.radians(st['latitud']))
            est_out[-1]['coordenadas_ficha_vs_catalogo_m'] = round(math.hypot(dlat, dlon), 2)
    dump(DATOS / 'observaciones_diarias.json', tabla)
    dump(DATOS / 'cobertura_observaciones.json', cobertura)
    out = {'generado_utc': now(), 'metodo_sha256': load(STATE / 'metodo_fijado_recibo.json')['sha256'],
           'catalogo': sp['estaciones']['catalogo'], 'regla': {k: v for k, v in sp['estaciones'].items() if k != 'seleccion'},
           'n_seleccionadas': len(est_out), 'n_excluidas_por_cobertura': sum(1 for e in est_out if e['cobertura']['excluida_por_cobertura']),
           'estaciones': est_out}
    dump(OUT / 'estaciones.json', out)
    print(json.dumps({c: {k: v for k, v in cobertura[c].items() if k in ['dias_validos_primaria', 'dias_validos_secundaria', 'motivos_no_valido', 'excluida_por_cobertura', 'tieneDatos_false']} for c in cobertura}, ensure_ascii=False, indent=1))
    print('coordenadas ficha vs catálogo (m):', {e['codigo']: e['coordenadas_ficha_vs_catalogo_m'] for e in est_out})
    print('piranómetros:', {e['codigo']: e['ficha']['modeloPiranometro'] for e in est_out})


if __name__ == '__main__':
    main()
