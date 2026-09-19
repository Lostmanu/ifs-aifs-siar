"""Descarga observaciones diarias de SiAR (radiación MJ/m²) y la ficha oficial de cada estación seleccionada.

Requiere metodo_fijado.json congelado. Una consulta diaria por estación (2026-04-01 → 2026-09-01) y una ficha por estación.
Guarda cuerpos íntegros (campos de sesión omitidos en HTML) y recibos con SHA-256.
"""
from comun import *
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor
import sys, time

LOG = STATE / 'descarga_siar.log'
FIRST, LAST = '2026-04-01', '2026-09-01'


def session():
    op = build_opener(HTTPCookieProcessor(CookieJar()))
    rec, page = fetch_with_receipt('https://servicio.mapa.gob.es/siarweb/consultaDatos/inicio', RAW / 'siar' / 'formulario_inicio.html', op, redact=True, timeout=60, fresh=True)
    if rec['status'] != 200:
        raise SystemExit(f'formulario inicial: {rec}')
    hidden = Hidden()
    hidden.feed(page.decode('utf-8'))
    return op, hidden


def variable_diaria(op):
    rec, body = fetch_with_receipt('https://servicio.mapa.gob.es/siarweb/consultaDatos/cargarVariables?idTipoDatoVariable=2', RAW / 'siar' / 'variables_diarias.json', op, timeout=60)
    var = json.loads(body)
    rad = next(v for v in var if v['nombreCampoTablaDatos'] == 'Radiacion')
    return rad


def ficha(st, op, hidden):
    url = 'https://servicio.mapa.gob.es/siarweb/fichaEstacion/estacion/' + st['id_formulario'].replace('-', '/')
    dest = RAW / 'siar' / st['codigo'] / 'ficha.html'
    rec, page = fetch_with_receipt(url, dest, op, dict(hidden.fields), redact=True, timeout=60)
    if rec['status'] != 200:
        return {'codigo': st['codigo'], 'error': rec}
    m = re.search(r'const estacion = (\{.*?\});', page.decode('utf-8'))
    if not m:
        return {'codigo': st['codigo'], 'error': 'ficha sin objeto estacion'}
    obj = json.loads(m[1])
    out = {k: v for k, v in obj.items() if not k.lower().startswith('foto')}
    dump(RAW / 'siar' / st['codigo'] / 'ficha.json', out)
    return out


def diarios(st, rad, op, hidden):
    dest = RAW / 'siar' / st['codigo'] / f'diarios_{FIRST}_{LAST}'
    cached = dest / 'derived.json'
    if cached.exists():
        return load(cached)
    q = dict(hidden.fields)
    q.update(variablesSeleccionadas=str(rad['idVariable']), idEstaciones=st['id_formulario'], fechaInicial=FIRST, fechaFinal=LAST,
             tipoCalculo='2', tipoFiltroEstaciones='provincias', idProvs=st['id_formulario'].split('-')[0], idCCAA=st['region_formulario'],
             accionHidden='consultaDatos', consultaPersonalizada='false')
    rec, body = fetch_with_receipt('https://servicio.mapa.gob.es/siarweb/consultaDatosRest/validarResultadoDatos', dest / 'validation.json', op, q, timeout=60)
    valid = json.loads(body) if rec['status'] == 200 else {}
    if not valid.get('validated'):
        return {'codigo': st['codigo'], 'error': f'validación: {rec["status"]} {body[:300]!r}'}
    q['accionHidden'] = 'resultadoConsultaDatos'
    rec, page = fetch_with_receipt('https://servicio.mapa.gob.es/siarweb/consultaDatos/consultaDatos', dest / 'result.html', op, q, redact=True, timeout=120)
    if rec['status'] != 200:
        return {'codigo': st['codigo'], 'error': f'consulta: {rec}'}
    matches = re.findall(r'resultadoConsultaChart\.set\(("(?:[^"\\]|\\.)*"),(\[.*?\])\);', page.decode('utf-8'))
    if len(matches) != 1:
        return {'codigo': st['codigo'], 'error': f'{len(matches)} bloques de datos en la respuesta'}
    key, rows = matches[0]
    obj = {'codigo': st['codigo'], 'station_chart_key': json.loads(key), 'data_kind': 2, 'variable_definition': rad, 'rango': [FIRST, LAST], 'rows': json.loads(rows),
           'result_sha256': rec['saved_sha256']}
    if not obj['station_chart_key'].startswith(st['id_formulario'].replace('-', '_') + '_'):
        return {'codigo': st['codigo'], 'error': f'clave de gráfico inesperada {obj["station_chart_key"]}'}
    dump(cached, obj)
    return obj


def main():
    sp = spec()
    stations = sp['estaciones']['seleccion']
    rec = load(STATE / 'metodo_fijado_recibo.json')
    if rec.get('descargas_iniciadas_en_utc') is None:
        rec['descargas_iniciadas_en_utc'] = now()
        dump(STATE / 'metodo_fijado_recibo.json', rec)
        dump(OUT / 'metodo_fijado_recibo.json', rec)
    log(LOG, f'inicio descarga SiAR: {len(stations)} estaciones, {FIRST}→{LAST}')
    op, hidden = session()
    rad = variable_diaria(op)
    log(LOG, f'variable diaria: {rad["idVariable"]} {rad["nombreVariable"]} ({rad["unidad"]})')
    fichas, obs, errores = [], {}, []
    for st in stations:
        f = ficha(st, op, hidden)
        if 'error' in f:
            errores.append(f); log(LOG, f'FICHA ERROR {st["codigo"]}: {f["error"]}')
        else:
            fichas.append(f)
        time.sleep(1.0)
        d = diarios(st, rad, op, hidden)
        if 'error' in d:
            errores.append(d); log(LOG, f'DIARIOS ERROR {st["codigo"]}: {d["error"]}')
        else:
            obs[st['codigo']] = d
            log(LOG, f'{st["codigo"]} {st["nombre"]}: {len(d["rows"])} filas diarias; ficha altitud={f.get("altitud")} piranómetro={f.get("modeloPiranometro")}')
        time.sleep(1.0)
    dump(DATOS / 'fichas_siar.json', fichas)
    dump(DATOS / 'observaciones_diarias_crudas.json', obs)
    dump(STATE / 'descarga_siar_estado.json', {'terminado_utc': now(), 'estaciones': len(stations), 'fichas_ok': len(fichas), 'diarios_ok': len(obs), 'errores': errores})
    log(LOG, f'fin: fichas={len(fichas)} diarios={len(obs)} errores={len(errores)}')


if __name__ == '__main__':
    main()
