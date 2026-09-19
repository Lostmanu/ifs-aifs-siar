"""Verificación: (1) recálculo independiente con Decimal de MAE_rel y efectos puntuales (ventana primaria, agregado y por estación)
desde los ficheros crudos (derived.json de SiAR y respuestas de la API), sin numpy; (2) pruebas automatizadas; (3) integridad de recibos.
Uso: python verificar.py [--resultados F] [--forecasts D] [--state F] [--out F]
"""
from comun import *
from decimal import Decimal, getcontext
from datetime import date, timedelta
import argparse, unittest, io, math

getcontext().prec = 40
D = Decimal
SERIES = ['IFS_00', 'IFS_06', 'AIFS_00', 'AIFS_06']
COMP = {'H1': ('IFS_00', 'IFS_06'), 'H2': ('IFS_00', 'AIFS_00'), 'S1': ('AIFS_00', 'AIFS_06'), 'S2': ('IFS_06', 'AIFS_06')}


def h0(lat_deg, d):
    # misma fórmula, en float (solo para la regla de validez, que es la congelada)
    J = d.timetuple().tm_yday
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * J / 365)
    delta = 0.409 * math.sin(2 * math.pi * J / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return (24 * 60 / math.pi) * 0.0820 * dr * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))


def obs_decimal(sp):
    """Observaciones válidas desde los derived.json crudos: dict codigo -> {fecha: Decimal Wh/m²}."""
    out = {}
    for st in sp['estaciones']['seleccion']:
        code = st['codigo']
        path = next((RAW / 'siar' / code).glob('diarios_*/derived.json'))
        rows = load(path)['rows']
        seen, vals = {}, {}
        for r in rows:
            dd, mm, yy = r['fechaStr'].split(' ')[0].split('/')
            fch = f'{yy}-{mm}-{dd}'
            seen[fch] = seen.get(fch, 0) + 1
            v = next(x for x in r['resultadoVariable'] if x['nombreCampoTablaDatos'] == 'Radiacion')['valor']
            try:
                x = D(str(v))
            except Exception:
                continue
            if not x.is_finite():
                continue
            kt = float(x) / h0(st['latitud'], date.fromisoformat(fch))
            if 0.03 <= kt <= 1.0:
                vals[fch] = x * D(1000) / D('3.6')
        out[code] = {k: v for k, v in vals.items() if seen[k] == 1}
    return out


def forecasts_decimal(sp, fdir, state, days):
    """Totales diarios Decimal por serie: dict serie -> {codigo: {fecha: Decimal}}."""
    codes = [s['codigo'] for s in sp['estaciones']['seleccion']]
    out = {s: {c: {} for c in codes} for s in SERIES}
    dayset = set(days)
    for key, st in state['peticiones'].items():
        if st.get('estado') != 'ok':
            continue
        run, model = st['run'], st['model']
        target = (date.fromisoformat(run[:10]) + timedelta(days=1)).isoformat()
        if target not in dayset:
            continue
        series = ('IFS' if model == 'ecmwf_ifs025' else 'AIFS') + '_' + run[11:13]
        body = json.loads((Path(fdir) / f'{key}.json').read_text(encoding='utf-8'))
        if isinstance(body, dict):
            body = [body]
        d = date.fromisoformat(target)
        wanted = [f'{target}T{h:02d}:00' for h in range(1, 24)] + [f'{(d + timedelta(days=1)).isoformat()}T00:00']
        for i, loc in enumerate(body):
            h = loc['hourly']; pos = {t: j for j, t in enumerate(h['time'])}
            tot = D(0); ok = True
            for w in wanted:
                j = pos.get(w)
                v = h['shortwave_radiation'][j] if j is not None else None
                if v is None or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 or v > 1500:
                    ok = False; break
                tot += D(str(v))
            if ok:
                out[series][codes[i]][target] = tot
    return out


def efectos_decimal(obs, fc, codes, days, restrict=None):
    """Recalcula Ō_i, MAE_rel y efecto por comparación (agregado y por estación) con Decimal."""
    dayset = set(days)
    om = {}
    for c in codes:
        vals = [v for f, v in obs[c].items() if f in dayset]
        om[c] = (sum(vals) / D(len(vals))) if vals else None
    res = {}
    for cname, (A, B) in COMP.items():
        sa = sb = D(0); n = 0
        per = {}
        for c in codes:
            if om[c] is None:
                continue
            sa_c = sb_c = D(0); n_c = 0
            for f in days:
                o = obs[c].get(f); a = fc[A][c].get(f); b = fc[B][c].get(f)
                if o is None or a is None or b is None:
                    continue
                sa_c += abs(a - o) / om[c]; sb_c += abs(b - o) / om[c]; n_c += 1
            if n_c:
                ma, mb = sa_c / D(n_c), sb_c / D(n_c)
                per[c] = {'n': n_c, 'efecto': float((ma - mb) / ma * 100)}
            sa += sa_c; sb += sb_c; n += n_c
        if n:
            ma, mb = sa / D(n), sb / D(n)
            res[cname] = {'n': n, 'mae_a': float(ma), 'mae_b': float(mb), 'efecto': float((ma - mb) / ma * 100), 'por_estacion': per}
        else:
            res[cname] = {'n': 0}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resultados', default=str(OUT / 'resultados.json'))
    ap.add_argument('--forecasts', default=str(RAW / 'forecasts'))
    ap.add_argument('--state', default=str(STATE / 'descarga_pronosticos.json'))
    ap.add_argument('--out', default=str(OUT / 'verificacion.json'))
    args = ap.parse_args()
    sp = spec()
    res = load(args.resultados)
    state = load(args.state)
    codes = [s['codigo'] for s in sp['estaciones']['seleccion']]
    excl = set(res['estaciones_excluidas_por_cobertura'])
    codes_ok = [c for c in codes if c not in excl]
    p0, p1 = sp['ventanas']['primaria']['dias_objetivo']
    d0, d1 = date.fromisoformat(p0), date.fromisoformat(p1)
    days = [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]
    obs = obs_decimal(sp)
    fc = forecasts_decimal(sp, args.forecasts, state, days)
    dec = efectos_decimal(obs, fc, codes_ok, days)
    comparacion = {}
    max_abs = 0.0
    for cname, r in dec.items():
        ref = res['primaria']['comparaciones'][cname]['por_bloque']['7']
        entry = {'n_decimal': r.get('n'), 'n_numpy': ref['n'], 'efecto_decimal': r.get('efecto'), 'efecto_numpy': ref['efecto']}
        if r.get('n') and ref['efecto'] is not None:
            entry['diferencia_abs'] = abs(r['efecto'] - ref['efecto'])
            entry['mae_a_diff'] = abs(r['mae_a'] - ref['mae_a']); entry['mae_b_diff'] = abs(r['mae_b'] - ref['mae_b'])
            max_abs = max(max_abs, entry['diferencia_abs'], entry['mae_a_diff'], entry['mae_b_diff'])
            per_diff = []
            for c, v in r['por_estacion'].items():
                ref_c = res['primaria']['por_estacion'][c][cname]['por_bloque']['7']
                if ref_c['efecto'] is not None:
                    per_diff.append(abs(v['efecto'] - ref_c['efecto']))
                    if v['n'] != ref_c['n']:
                        entry.setdefault('n_por_estacion_discrepante', []).append(c)
            entry['max_diff_por_estacion'] = max(per_diff) if per_diff else None
            max_abs = max(max_abs, entry['max_diff_por_estacion'] or 0.0)
        comparacion[cname] = entry
    # pruebas automatizadas
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromName('test_metodo')
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    pruebas = {'ejecutadas': result.testsRun, 'fallos': len(result.failures), 'errores': len(result.errors), 'salida': stream.getvalue()[-600:]}
    # integridad de recibos
    bad, n_rec = [], 0
    for rec_path in list((RAW / 'forecasts').glob('*.receipt.json')) + list((RAW / 'siar').rglob('*.receipt.json')):
        rec = load(rec_path); body = rec_path.with_name(rec_path.name.replace('.receipt.json', ''))
        n_rec += 1
        if not body.exists():
            bad.append(str(rec_path)); continue
        h = sha256_file(body)
        expected = rec.get('sha256') or rec.get('saved_sha256')
        if h != expected:
            bad.append(str(rec_path))
    # paquete reproducible: existencia, manifiesto (de disco Y el embebido), cobertura en los dos sentidos,
    # coincidencia de cada entrada, hash declarado, y que el codigo del zip pueda encontrar la especificacion.
    zp = OUT / 'datos_y_analisis.zip'; man = BASE / 'manifest_sha256.json'; integ = OUT / 'integridad_paquete.json'
    if not zp.exists():
        # Caso normal al reproducir desde un paquete ya extraido: el zip no puede contenerse a si mismo.
        paquete = {'estado': 'NO_APLICA', 'motivo': 'no hay datos_y_analisis.zip en la carpeta de salida; es lo esperado al reproducir desde un paquete extraido, porque el zip no viaja dentro de si mismo', 'zip': str(zp)}
    elif not man.exists():
        paquete = {'estado': 'FAIL', 'motivo': 'hay zip pero falta manifest_sha256.json en la raiz del trabajo', 'zip': str(zp)}
    else:
        import zipfile
        m = load(man)
        malos, faltan, fallos = [], [], []
        with zipfile.ZipFile(zp) as z:
            nombres = set(z.namelist())
            for arc, h in m.items():
                if arc not in nombres:
                    faltan.append(arc)
                elif sha256_bytes(z.read(arc)) != h:
                    malos.append(arc)
            extra = sorted(nombres - set(m) - {'manifest_sha256.json'})
            emb = None
            if 'manifest_sha256.json' in nombres:
                try:
                    emb = json.loads(z.read('manifest_sha256.json').decode('utf-8'))
                except Exception as e:
                    fallos.append(f'manifiesto embebido ilegible: {e}')
            spec_en_zip = [a for a in ('outputs/metodo_fijado.json', 'metodo_fijado.json') if a in nombres]
        paquete = {'zip': str(zp), 'bytes': zp.stat().st_size, 'sha256_zip': sha256_file(zp),
                   'entradas_en_manifiesto': len(m), 'entradas_en_zip': len(nombres),
                   'faltan_en_zip': faltan, 'hash_no_coincide': malos, 'en_zip_sin_manifiesto': extra,
                   'manifiesto_embebido_igual_al_de_disco': (emb == m) if emb is not None else None,
                   'especificacion_en_el_zip': spec_en_zip,
                   'sha256_declarado_en_integridad': (load(integ)['sha256'] if integ.exists() else None)}
        if faltan:
            fallos.append(f'{len(faltan)} ficheros del manifiesto no estan en el zip')
        if malos:
            fallos.append(f'{len(malos)} ficheros del zip no coinciden con su hash')
        if extra:
            fallos.append(f'{len(extra)} ficheros en el zip sin entrada en el manifiesto')
        if emb is None:
            fallos.append('el zip no lleva manifest_sha256.json dentro')
        elif emb != m:
            fallos.append('el manifiesto embebido en el zip difiere del de disco')
        if len(m) < 100:
            fallos.append(f'manifiesto sospechosamente corto ({len(m)} entradas)')
        if not integ.exists():
            fallos.append('falta integridad_paquete.json')
        elif paquete['sha256_declarado_en_integridad'] != paquete['sha256_zip']:
            fallos.append('el SHA-256 de integridad_paquete.json no coincide con el zip actual')
        if 'outputs/metodo_fijado.json' not in spec_en_zip:
            fallos.append('el zip no lleva outputs/metodo_fijado.json, que es donde comun.spec() la busca primero')
        # el zip frente al DISCO: detecta que algo se regenero despues de empaquetar
        desincronizados = []
        for arc, h in m.items():
            disco = (OUT / arc[len('outputs/'):]) if arc.startswith('outputs/') else (BASE / arc)
            if disco.exists() and sha256_file(disco) != h:
                desincronizados.append(arc)
        paquete['desincronizados_con_el_disco'] = desincronizados
        if desincronizados:
            fallos.append(f'{len(desincronizados)} ficheros del arbol de trabajo han cambiado desde que se construyo el zip: {desincronizados[:5]}')
        paquete['fallos'] = fallos
        paquete['estado'] = 'PASS' if not fallos else 'FAIL'
    ok_paq = paquete['estado'] in ('PASS', 'NO_APLICA')
    out = {'generado_utc': now(), 'metodo_sha256': load(STATE / 'metodo_fijado_recibo.json')['sha256'],
           'recalculo_decimal': {'ventana': 'primaria', 'comparaciones': comparacion, 'diferencia_maxima_abs': max_abs, 'tolerancia': 1e-9, 'coincide': bool(max_abs < 1e-9)},
           'pruebas': pruebas, 'recibos': {'comprobados': n_rec, 'fallidos': bad}, 'paquete': paquete,
           'estado': 'PASS' if (max_abs < 1e-9 and not bad and not result.failures and not result.errors and ok_paq) else 'FAIL'}
    dump(args.out, out)
    print(json.dumps({k: v for k, v in out.items() if k != 'recalculo_decimal'}, ensure_ascii=False, indent=1)[:1500])
    print('recalculo:', json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'n_por_estacion_discrepante'} for k, v in comparacion.items()}, indent=1)[:1500])


if __name__ == '__main__':
    main()
