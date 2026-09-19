"""Descarga reanudable de pasadas individuales (Single Runs API), una petición en vuelo, con cuota propia y espera exponencial.

Uso: python descargar_pronosticos.py [--max-hours H] [--dry-run]
Estado en state/descarga_pronosticos.json; registro en state/descarga_pronosticos.log; cuerpos y recibos en raw/forecasts/.
"""
from comun import *
from datetime import date, timedelta
from urllib.parse import urlencode
import argparse, random, sys, time

LOG = STATE / 'descarga_pronosticos.log'
STATE_FILE = STATE / 'descarga_pronosticos.json'
ENDPOINT = 'https://single-runs-api.open-meteo.com/v1/forecast'
LIMITS = {'minuto': (60, 550), 'hora': (3600, 4800), 'dia': (86400, 9500)}


def runs(sp):
    first = date.fromisoformat(sp['ventanas']['pasadas_a_descargar']['primera'][:10])
    last = date.fromisoformat(sp['ventanas']['pasadas_a_descargar']['ultima'][:10])
    out = []
    d = first
    while d <= last:
        for cyc in ('00', '06'):
            for model in sp['ventanas']['pasadas_a_descargar']['modelos']:
                out.append((f'{d.isoformat()}T{cyc}:00', model))
        d += timedelta(days=1)
    return out


def build_url(sp, run, model, stations):
    params = {'latitude': ','.join(f'{s["latitud"]:.6f}' for s in stations), 'longitude': ','.join(f'{s["longitud"]:.6f}' for s in stations),
              'models': model, 'hourly': 'shortwave_radiation,cloud_cover', 'run': run, 'forecast_days': 3, 'timezone': 'UTC', 'cell_selection': 'nearest'}
    return ENDPOINT + '?' + urlencode(params)


def key(run, model):
    return f'{run.replace(":", "")}_{model}'


def load_state():
    if STATE_FILE.exists():
        return load(STATE_FILE)
    return {'peticiones': {}, 'llamadas_contadas': [], 'creado_utc': now()}


def quota_wait(state, n_calls):
    """Segundos a esperar para que las ventanas deslizantes admitan n_calls más."""
    t = time.time()
    state['llamadas_contadas'] = [x for x in state['llamadas_contadas'] if t - x[0] < 86400]
    waits = [0.0]
    for name, (window, cap) in LIMITS.items():
        recent = [x for x in state['llamadas_contadas'] if t - x[0] < window]
        used = sum(x[1] for x in recent)
        if used + n_calls > cap and recent:
            # esperar a que salga de la ventana la llamada más antigua necesaria
            need = used + n_calls - cap
            acc = 0
            for ts, n in sorted(recent):
                acc += n
                if acc >= need:
                    waits.append(window - (t - ts) + 1)
                    break
    return max(waits)


def classify(status, body):
    if status == 200:
        # La API multiubicación devuelve 200 con texto plano cuando la pasada no está archivada
        # (p. ej. «Unexpected error while streaming data: modelRunUnavailable(...)»); la petición de una
        # sola ubicación devuelve 400 para la misma pasada. Se trata como pasada ausente, no como transitorio.
        if body[:40].startswith(b'Unexpected error') and b'modelRunUnavailable' in body:
            return 'unavailable'
        return 'ok'
    if status == 400:
        try:
            reason = json.loads(body).get('reason', '')
        except Exception:
            reason = body[:200].decode('utf-8', 'replace')
        if 'not available' in reason:
            return 'unavailable'
        return 'bad_request'
    return 'transient'


def parse_check(body, stations, model):
    """Comprueba estructura: lista de 34 objetos con location_id en orden, 72 marcas horarias, unidades."""
    try:
        obj = json.loads(body)
    except Exception as e:
        return f'JSON inválido o truncado ({type(e).__name__}: {str(e)[:80]}; {len(body)} bytes)'
    if isinstance(obj, dict):
        obj = [obj]
    if len(obj) != len(stations):
        return f'{len(obj)} ubicaciones en la respuesta, se esperaban {len(stations)}'
    for i, o in enumerate(obj):
        lid = o.get('location_id')
        if lid is None:
            lid = i  # Open-Meteo omite location_id en la primera ubicación
        if lid != i:
            return f'location_id {lid} en posición {i}'
        h = o.get('hourly', {})
        if 'shortwave_radiation' not in h or 'time' not in h:
            return f'ubicación {i}: faltan variables'
        if len(h['time']) != len(h['shortwave_radiation']):
            return f'ubicación {i}: longitudes distintas'
        if o.get('utc_offset_seconds') != 0:
            return f'ubicación {i}: utc_offset {o.get("utc_offset_seconds")}'
        if o.get('hourly_units', {}).get('shortwave_radiation') not in ('W/m²', 'W/m2'):
            return f'ubicación {i}: unidad {o.get("hourly_units")}'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-hours', type=float, default=10.0)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--only-unavailable', action='store_true', help='reintentar una vez las pasadas marcadas ausentes')
    args = ap.parse_args()
    sp = spec()
    stations = sp['estaciones']['seleccion']
    todo = runs(sp)
    state = load_state()
    rec = load(STATE / 'metodo_fijado_recibo.json')
    if rec.get('descargas_iniciadas_en_utc') is None and not args.dry_run:
        rec['descargas_iniciadas_en_utc'] = now()
        dump(STATE / 'metodo_fijado_recibo.json', rec)
        dump(OUT / 'metodo_fijado_recibo.json', rec)
    pending = []
    for run, model in todo:
        st = state['peticiones'].get(key(run, model), {})
        if st.get('estado') == 'ok':
            continue
        if st.get('estado') == 'unavailable' and not args.only_unavailable:
            continue
        if st.get('estado') == 'unavailable' and st.get('reintentado_final'):
            continue
        pending.append((run, model))
    log(LOG, f'inicio: {len(todo)} peticiones en total, {len(pending)} pendientes, max {args.max_hours} h, dry_run={args.dry_run}')
    if args.dry_run:
        print(build_url(sp, *pending[0], stations) if pending else 'nada pendiente')
        return
    t_end = time.time() + args.max_hours * 3600
    consecutive = 0
    timing = []
    for run, model in pending:
        k = key(run, model)
        url = build_url(sp, run, model, stations)
        while True:
            if time.time() > t_end:
                log(LOG, f'límite de horas alcanzado; {k} queda pendiente'); dump(STATE_FILE, state); return
            w = quota_wait(state, len(stations))
            if w > 0:
                log(LOG, f'cuota: espera {w:.0f} s'); time.sleep(min(w, 3600)); continue
            attempt = state['peticiones'].get(k, {}).get('intentos', 0) + 1
            t0 = time.time()
            status, body, error = http(url, timeout=180)
            dt = time.time() - t0
            kind = classify(status, body)
            if kind == 'ok':
                problem = parse_check(body, stations, model)
                if problem:
                    kind = 'transient'; error = f'respuesta 200 con estructura inválida: {problem}'
            path = RAW / 'forecasts' / f'{k}.json'
            if kind in ('ok', 'unavailable', 'bad_request'):
                path.write_bytes(body)
                receipt = {'url': url, 'method': 'GET', 'run': run, 'model': model, 'requested_at_utc': datetime.fromtimestamp(t0, timezone.utc).isoformat(), 'received_at_utc': now(),
                           'status': status, 'error': error, 'seconds': round(dt, 3), 'sha256': sha256_bytes(body), 'bytes': len(body),
                           'counted_calls': len(stations) if kind == 'ok' else 0, 'n_locations': len(stations), 'intento': attempt}
                dump(path.with_name(path.name + '.receipt.json'), receipt)
            else:
                (RAW / 'forecasts' / 'errores').mkdir(parents=True, exist_ok=True)
                (RAW / 'forecasts' / 'errores' / f'{k}.intento{attempt}.txt').write_bytes(body[:2000] + f'\n\nstatus={status} error={error} seconds={dt:.1f}'.encode())
            entry = state['peticiones'].setdefault(k, {'run': run, 'model': model})
            entry.update(intentos=attempt, ultimo_estado=status, ultimo_error=error, ultimo_utc=now(), segundos=round(dt, 2))
            if kind == 'ok':
                entry['estado'] = 'ok'
                state['llamadas_contadas'].append([time.time(), len(stations)])
                consecutive = 0
                timing.append(dt)
                if len(timing) <= 20:
                    log(LOG, f'OK {k} en {dt:.1f} s ({len(body)} bytes) [medición inicial {len(timing)}/20]')
                elif len(timing) % 20 == 0:
                    log(LOG, f'OK {k} en {dt:.1f} s; completadas en esta sesión {len(timing)}')
                dump(STATE_FILE, state)
                time.sleep(2.0)
                break
            if kind in ('unavailable', 'bad_request'):
                entry['estado'] = kind
                if args.only_unavailable:
                    entry['reintentado_final'] = True
                log(LOG, f'{kind.upper()} {k}: {body[:160]!r}')
                dump(STATE_FILE, state)
                time.sleep(2.0)
                break
            consecutive += 1
            entry['estado'] = 'pending'
            wait = min(1800, 30 * 2 ** min(consecutive - 1, 6)) * (0.75 + 0.5 * random.random())
            log(LOG, f'TRANSITORIO {k} intento {attempt}: status={status} error={error} ({dt:.1f} s); fallos seguidos={consecutive}; espera {wait:.0f} s')
            dump(STATE_FILE, state)
            time.sleep(wait)
    dump(STATE_FILE, state)
    ok = sum(1 for v in state['peticiones'].values() if v.get('estado') == 'ok')
    log(LOG, f'fin de pasada: ok={ok}/{len(todo)}; ausentes={sum(1 for v in state["peticiones"].values() if v.get("estado") == "unavailable")}')


if __name__ == '__main__':
    main()
