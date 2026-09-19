"""Análisis principal según metodo_fijado.json. Lee observaciones preparadas y pronósticos descargados; escribe resultados.

Uso: python analizar.py [--forecasts DIR] [--state FILE] [--out FILE] [--replicas N] [--sorteos N]
Los parámetros opcionales solo sirven para pruebas con datos sintéticos; el análisis real usa los valores congelados.
"""
from comun import *
from metodo import *
from datetime import date, timedelta
import argparse, math, re
import numpy as np


class Panel:
    def __init__(self, sp, calendar):
        self.sp = sp
        self.stations = sp['estaciones']['seleccion']
        self.codes = [s['codigo'] for s in self.stations]
        self.calendar = calendar
        self.day_index = {d: i for i, d in enumerate(calendar)}
        n_s, n_d = len(self.stations), len(calendar)
        self.obs = np.full((n_s, n_d), np.nan)
        self.F = {s: np.full((n_s, n_d), np.nan) for s in SERIES}
        self.cloud = {s: np.full((n_s, n_d), np.nan) for s in ('IFS_00', 'AIFS_00')}
        self.cells = {}
        self.run_status = {}

    def load_obs(self, tabla):
        for i, code in enumerate(self.codes):
            for r in tabla[code]:
                j = self.day_index.get(r['fecha'])
                if j is not None and r['valido']:
                    self.obs[i, j] = r['wh_m2']

    def load_forecasts(self, fdir, state):
        n_ok = 0
        for key, st in state['peticiones'].items():
            self.run_status[key] = st.get('estado')
            if st.get('estado') != 'ok':
                continue
            run, model = st['run'], st['model']
            cyc = run[11:13]
            fam = 'IFS' if model == 'ecmwf_ifs025' else 'AIFS'
            series = f'{fam}_{cyc}'
            target = (date.fromisoformat(run[:10]) + timedelta(days=1)).isoformat()
            j = self.day_index.get(target)
            if j is None:
                continue
            body = json.loads((Path(fdir) / f'{key}.json').read_text(encoding='utf-8'))
            if isinstance(body, dict):
                body = [body]
            assert len(body) == len(self.stations), key
            for i, loc in enumerate(body):
                lid = loc.get('location_id')
                assert (i if lid is None else lid) == i, (key, i)
                cell = (loc.get('latitude'), loc.get('longitude'), loc.get('elevation'))
                prev = self.cells.setdefault(self.codes[i], cell)
                if prev != cell:
                    raise ValueError(f'celda distinta para {self.codes[i]}: {prev} vs {cell} en {key}')
                h = loc['hourly']
                t = self.F[series]
                v = total_diario(h['time'], h['shortwave_radiation'], target)
                if v is not None:
                    t[i, j] = v
                if series in self.cloud and h.get('cloud_cover'):
                    c = nubosidad_diurna(h['time'], h['cloud_cover'], target)
                    if c is not None:
                        self.cloud[series][i, j] = c
            n_ok += 1
        return n_ok


def ventana(panel, first, last):
    days = [d for d in dias(first, last) if d in panel.day_index]
    return days, np.array([panel.day_index[d] for d in days])


def sumas(panel, idx, A, B, k, mask_extra=None, obs_mean=None):
    """Sumas por día de |r_A|, |r_B| y recuento, sobre estación-días válidos para obs, A y B (y máscara extra)."""
    obs = panel.obs[:, idx] / k[:, None]
    if obs_mean is None:
        with np.errstate(invalid='ignore'):
            obs_mean = np.nanmean(obs, axis=1)
    fa, fb = panel.F[A][:, idx], panel.F[B][:, idx]
    mask = np.isfinite(obs) & np.isfinite(fa) & np.isfinite(fb) & np.isfinite(obs_mean)[:, None]
    if mask_extra is not None:
        mask = mask & mask_extra
    ra = np.where(mask, np.abs(fa - obs) / obs_mean[:, None], 0.0)
    rb = np.where(mask, np.abs(fb - obs) / obs_mean[:, None], 0.0)
    return ra.sum(axis=0), rb.sum(axis=0), mask.sum(axis=0).astype(float), mask


def obs_means(panel, idx, k):
    with np.errstate(invalid='ignore'):
        return np.nanmean(panel.obs[:, idx] / k[:, None], axis=1)


def resumen(r, keep_reps=False):
    out = {k: v for k, v in r.items() if k != 'replicas'}
    if r.get('efecto') is not None:
        out['conclusion_ic'] = conclusion_intervalo(r['ic95'])
    return out


def analizar_ventana(panel, nombre, first, last, Ws_cache, replicas, seed, k_global=1.0, con_estratos=True, con_estaciones=True):
    days, idx = ventana(panel, first, last)
    N = len(days)
    k = np.full(len(panel.stations), k_global)
    om = obs_means(panel, idx, k)
    Ws = Ws_cache.setdefault((nombre, N), {L: pesos_bootstrap(N, L, replicas, seed) for L in (1, 7, 14)})
    res = {'ventana': nombre, 'dias': [first, last], 'n_dias_calendario': N, 'k_global': k_global, 'comparaciones': {}}
    masks = {}
    for cname, (A, B) in COMPARACIONES.items():
        sA, sB, n, mask = sumas(panel, idx, A, B, k, obs_mean=om)
        masks[cname] = mask
        entry = {'series': [A, B], 'n_estacion_dias': int(n.sum()), 'por_bloque': {}}
        for L, W in Ws.items():
            entry['por_bloque'][str(L)] = resumen(comparar(sA, sB, n, W))
        res['comparaciones'][cname] = entry
    # Holm sobre primarias, por largo de bloque
    res['holm'] = {}
    for L in (1, 7, 14):
        p = {h: res['comparaciones'][h]['por_bloque'][str(L)]['p'] for h in ('H1', 'H2')}
        hh = holm(p)
        for h in ('H1', 'H2'):
            ef = res['comparaciones'][h]['por_bloque'][str(L)]['efecto']
            hh[h]['efecto'] = ef
            hh[h]['apoyada'] = bool(hh[h]['rechaza'] and ef is not None and ef > 0)
        res['holm'][str(L)] = hh
    # MAE relativo y sesgo por serie (contexto; contaminado por la escala del instrumento)
    obs = panel.obs[:, idx] / k[:, None]
    res['series_contexto'] = {}
    for s in SERIES:
        f = panel.F[s][:, idx]
        m = np.isfinite(obs) & np.isfinite(f)
        if m.sum() == 0:
            res['series_contexto'][s] = None; continue
        e = np.where(m, f - obs, 0.0)
        res['series_contexto'][s] = {'n': int(m.sum()), 'mae_wh_m2': float(np.abs(e).sum() / m.sum()), 'mae_relativo_pct': float(np.abs(e).sum() / obs[m].sum() * 100),
                                     'sesgo_wh_m2': float(e.sum() / m.sum()), 'sesgo_relativo_pct': float(e.sum() / obs[m].sum() * 100)}
    if con_estaciones:
        res['por_estacion'] = {}
        for i, code in enumerate(panel.codes):
            st = {}
            m_st = np.zeros_like(masks['H1'], dtype=bool); m_st[i, :] = True
            for cname, (A, B) in COMPARACIONES.items():
                sA, sB, n, _ = sumas(panel, idx, A, B, k, mask_extra=m_st, obs_mean=om)
                st[cname] = {'n': int(n.sum()), 'por_bloque': {str(L): resumen(comparar(sA, sB, n, W)) for L, W in Ws.items()}}
            with np.errstate(invalid='ignore'):
                st['obs_media_wh_m2'] = float(om[i]) if np.isfinite(om[i]) else None
            st['dias_obs_validos'] = int(np.isfinite(obs[i]).sum())
            res['por_estacion'][code] = st
    if con_estratos:
        res['estratos'] = {}
        # mes
        meses = {}
        for j, d in enumerate(days):
            meses.setdefault(d[:7], []).append(j)
        for mes, cols in sorted(meses.items()):
            m_ex = np.zeros_like(masks['H1'], dtype=bool); m_ex[:, cols] = True
            res['estratos'][f'mes_{mes}'] = estrato(panel, idx, k, om, m_ex, Ws)
        # latitud: terciles de la latitud de las estaciones
        lats = np.array([s['latitud'] for s in panel.stations])
        q1, q2 = np.percentile(lats, [100 / 3, 200 / 3])
        for name, sel in (('latitud_sur', lats < q1), ('latitud_centro', (lats >= q1) & (lats < q2)), ('latitud_norte', lats >= q2)):
            m_ex = np.zeros_like(masks['H1'], dtype=bool); m_ex[sel, :] = True
            res['estratos'][name] = estrato(panel, idx, k, om, m_ex, Ws, extra={'estaciones': [c for c, b in zip(panel.codes, sel) if b], 'cortes_latitud': [float(q1), float(q2)]})
        # nubosidad prevista (IFS_00; si vacía, AIFS_00): terciles sobre los estación-días del conjunto de H1
        for src in ('IFS_00', 'AIFS_00'):
            cl = panel.cloud[src][:, idx]
            base = masks['H1'] & np.isfinite(cl)
            if base.sum() >= 30:
                c1, c2 = np.percentile(cl[base], [100 / 3, 200 / 3])
                for name, sel in (('nubosidad_baja', cl < c1), ('nubosidad_media', (cl >= c1) & (cl < c2)), ('nubosidad_alta', cl >= c2)):
                    res['estratos'][name] = estrato(panel, idx, k, om, sel & np.isfinite(cl), Ws, extra={'fuente_nubosidad': src, 'cortes_pct': [float(c1), float(c2)]})
                res['estratos']['nubosidad_fuente'] = src
                break
        else:
            res['estratos']['nubosidad_fuente'] = None
    return res


def estrato(panel, idx, k, om, m_ex, Ws, extra=None):
    out = {}
    for cname, (A, B) in COMPARACIONES.items():
        sA, sB, n, _ = sumas(panel, idx, A, B, k, mask_extra=m_ex, obs_mean=om)
        out[cname] = {'n': int(n.sum()), 'por_bloque': {str(L): resumen(comparar(sA, sB, n, W)) for L, W in Ws.items()}}
    if extra:
        out.update(extra)
    return out


def sensibilidad_determinista(panel, first, last, Ws_cache, replicas, seed):
    out = {}
    for kg in (0.95, 1.00, 1.05):
        r = analizar_ventana(panel, 'primaria', first, last, Ws_cache, replicas, seed, k_global=kg, con_estratos=False, con_estaciones=False)
        out[f'{kg:.2f}'] = {'comparaciones': {c: {L: {kk: vv for kk, vv in b.items() if kk in ('efecto', 'ic95', 'p', 'conclusion_ic', 'n')} for L, b in v['por_bloque'].items()} for c, v in r['comparaciones'].items()}, 'holm': r['holm']}
    robust = {}
    for h in ('H1', 'H2'):
        signos = {kk: (np.sign(v['comparaciones'][h][L]['efecto']) if v['comparaciones'][h][L]['efecto'] is not None else None) for kk, v in out.items() for L in ('1', '7', '14')}
        concl = {(kk, L): v['comparaciones'][h][L]['conclusion_ic'] for kk, v in out.items() for L in ('1', '7', '14')}
        same_sign = len({s for s in signos.values()}) == 1
        same_concl = all(len({concl[(kk, L)] for kk in out}) == 1 for L in ('1', '7', '14'))
        robust[h] = {'signo_invariante': bool(same_sign), 'conclusion_intervalos_invariante': bool(same_concl), 'robusto_al_instrumento': bool(same_sign and same_concl)}
    return {'por_k': out, 'veredicto': robust}


def sensibilidad_montecarlo(panel, first, last, Ws_cache, replicas, seed_boot, sorteos, seed_mc, principal):
    days, idx = ventana(panel, first, last)
    N = len(days)
    Ws = Ws_cache[('primaria', N)]
    rng = np.random.default_rng(seed_mc)
    K = rng.uniform(0.95, 1.05, size=(sorteos, len(panel.stations)))
    efectos = {c: np.full(sorteos, np.nan) for c in COMPARACIONES}
    surv1 = {h: 0 for h in ('H1', 'H2')}
    surv2 = {h: {str(L): 0 for L in (1, 7, 14)} for h in ('H1', 'H2')}
    ic_store = {h: {str(L): [] for L in (1, 7, 14)} for h in ('H1', 'H2')}
    base_sign = {h: np.sign(principal['comparaciones'][h]['por_bloque']['7']['efecto']) for h in ('H1', 'H2')}
    base_concl = {h: {str(L): principal['comparaciones'][h]['por_bloque'][str(L)]['conclusion_ic'] for L in (1, 7, 14)} for h in ('H1', 'H2')}
    for t in range(sorteos):
        k = K[t]
        om = obs_means(panel, idx, k)
        for cname, (A, B) in COMPARACIONES.items():
            sA, sB, n, _ = sumas(panel, idx, A, B, k, obs_mean=om)
            Ntot = n.sum()
            if Ntot == 0:
                continue
            ma, mb = sA.sum() / Ntot, sB.sum() / Ntot
            efectos[cname][t] = efecto(ma, mb)
            if cname in ('H1', 'H2'):
                if np.sign(efectos[cname][t]) == base_sign[cname]:
                    surv1[cname] += 1
                for L, W in Ws.items():
                    r = comparar(sA, sB, n, W)
                    concl = conclusion_intervalo(r['ic95'])
                    ic_store[cname][str(L)].append(r['ic95'])
                    if np.sign(efectos[cname][t]) == base_sign[cname] and concl == base_concl[cname][str(L)]:
                        surv2[cname][str(L)] += 1
    out = {'sorteos': sorteos, 'semilla': seed_mc, 'k_rango': [0.95, 1.05], 'k_por_estacion_primeros_3_sorteos': K[:3].round(4).tolist(), 'comparaciones': {}}
    for cname in COMPARACIONES:
        e = efectos[cname]; e = e[np.isfinite(e)]
        out['comparaciones'][cname] = {'efecto_media': float(e.mean()), 'efecto_desv': float(e.std(ddof=1)), 'efecto_p2_5': float(np.percentile(e, 2.5)), 'efecto_mediana': float(np.median(e)), 'efecto_p97_5': float(np.percentile(e, 97.5)),
                                      'efecto_min': float(e.min()), 'efecto_max': float(e.max()), 'fraccion_signo_positivo': float(np.mean(e > 0)), 'efectos': e.round(4).tolist()}
        if cname in ('H1', 'H2'):
            out['comparaciones'][cname]['supervivencia_nivel1_signo'] = surv1[cname] / sorteos
            out['comparaciones'][cname]['supervivencia_nivel2_signo_e_intervalo'] = {L: v / sorteos for L, v in surv2[cname].items()}
            out['comparaciones'][cname]['ic95_por_sorteo_L7_percentiles'] = {'lo_p2_5_p97_5': [float(np.percentile([x[0] for x in ic_store[cname]['7']], q)) for q in (2.5, 97.5)],
                                                                             'hi_p2_5_p97_5': [float(np.percentile([x[1] for x in ic_store[cname]['7']], q)) for q in (2.5, 97.5)]}
    return out


# ---------- enlace 06-18 UTC con semihorarios heredados ----------

def semihorario_0618(rows):
    """rows del gráfico SiAR (kind 1). Devuelve dict fecha -> Wh/m² (06-18 UTC) o None si incompleto."""
    labels = {f'{h}{m}' for h in range(6, 18) for m in ('30', '00')} | {'1800'}
    labels = {l.lstrip('0') if l != '000' else l for l in labels}
    wanted = set()
    for h in range(6, 19):
        for m in ('00', '30'):
            if h == 6 and m == '00':
                continue
            if h == 18 and m == '30':
                continue
            wanted.add(f'{h}{m}')
    byday = {}
    for r in rows:
        dd, mm, yy = r['fechaStr'].split(' ')[0].split('/')
        f = f'{yy}-{mm}-{dd}'
        rv = next(v for v in r['resultadoVariable'] if v['nombreCampoTablaDatos'] == 'Radiacion')
        byday.setdefault(f, {})[str(r['hora'])] = rv['valor']
    out = {}
    for f, d in byday.items():
        vals = []
        for lab in wanted:
            v = d.get(lab)
            try:
                x = float(v)
            except (TypeError, ValueError):
                vals = None; break
            if not math.isfinite(x) or x < 0 or x > 1500:
                vals = None; break
            vals.append(x)
        out[f] = (sum(vals) * 0.5) if vals is not None and len(vals) == 24 else None
    return out


def enlace_0618(sp, panel_bulk, state_bulk, fdir=None):
    fdir = Path(fdir) if fdir else RAW / 'forecasts'
    man = load(DATOS / 'heredado_manifiesto.json')['fuentes']
    p0, p1 = sp['ventanas']['primaria']['dias_objetivo']
    cal = [d for d in dias(p0, p1) if ('2026-06-16' <= d <= '2026-07-31') or ('2026-08-10' <= d <= '2026-08-31')]
    stations_link = ['AL01', 'C01', 'M01', 'AL10', 'LU01']
    n_s, n_d = len(stations_link), len(cal)
    di = {d: j for j, d in enumerate(cal)}
    obs = np.full((n_s, n_d), np.nan)
    F = {s: np.full((n_s, n_d), np.nan) for s in SERIES}
    prov = {}
    # observaciones semihorarias
    src_obs = {'AL01': ['AL01_cal', 'AL01_rep'], 'C01': ['C01_cal', 'C01_rep'], 'M01': ['M01_pil'], 'AL10': ['AL10_nb'], 'LU01': ['LU01_nb']}
    for i, code in enumerate(stations_link):
        for tag in src_obs[code]:
            for o in man[tag]['obs']:
                if 'sha256' not in o:
                    continue
                rows = load(BASE / ruta(o['destino']))['rows']
                for f, v in semihorario_0618(rows).items():
                    j = di.get(f)
                    if j is not None and v is not None:
                        obs[i, j] = v
        prov[code] = src_obs[code]
    # pronósticos heredados (una ubicación por fichero, nombre YYYYMMDD_model_cc.json)
    src_fc = {'AL01': ['AL01_cal', 'AL01_rep'], 'C01': ['C01_cal', 'C01_rep'], 'M01': ['M01_pil']}
    for i, code in enumerate(stations_link):
        for tag in src_fc.get(code, []):
            for fobj in man[tag]['forecasts']:
                name = ruta(fobj['destino']).name
                m = re.match(r'(\d{8})_(ecmwf_ifs025|ecmwf_aifs025_single)_(00|06)\.json$', name)
                if not m:
                    continue
                target = f'{m[1][:4]}-{m[1][4:6]}-{m[1][6:]}'
                j = di.get(target)
                if j is None:
                    continue
                body = load(BASE / ruta(fobj['destino']))
                if 'error' in body:
                    continue
                rec = load(BASE / ruta(fobj['destino'] + '.receipt.json'))
                exp_run = (date.fromisoformat(target) - timedelta(days=1)).isoformat() + f'T{m[3]}%3A00'
                if exp_run not in rec['url']:
                    raise ValueError(f'pasada inesperada en {name}: {rec["url"]}')
                fam = 'IFS' if m[2] == 'ecmwf_ifs025' else 'AIFS'
                v = suma_0618(body['hourly']['time'], body['hourly']['shortwave_radiation'], target)
                if v is not None:
                    F[f'{fam}_{m[3]}'][i, j] = v
    # pronósticos de la descarga nueva para AL10 y LU01
    idx_bulk = {c: k for k, c in enumerate(panel_bulk.codes)}
    for key, st in state_bulk['peticiones'].items():
        if st.get('estado') != 'ok':
            continue
        run, model = st['run'], st['model']
        target = (date.fromisoformat(run[:10]) + timedelta(days=1)).isoformat()
        j = di.get(target)
        if j is None:
            continue
        body = json.loads((fdir / f'{key}.json').read_text(encoding='utf-8'))
        if isinstance(body, dict):
            body = [body]
        fam = 'IFS' if model == 'ecmwf_ifs025' else 'AIFS'
        for code in ('AL10', 'LU01'):
            if code in idx_bulk:
                loc = body[idx_bulk[code]]
                v = suma_0618(loc['hourly']['time'], loc['hourly']['shortwave_radiation'], target)
                if v is not None:
                    F[f'{fam}_{run[11:13]}'][stations_link.index(code), j] = v
    # análisis con la misma maquinaria
    class P: pass
    pn = P(); pn.obs = obs; pn.F = F; pn.stations = [{'codigo': c} for c in stations_link]; pn.codes = stations_link
    idx = np.arange(n_d)
    k = np.ones(n_s)
    om = obs_means(pn, idx, k)
    Ws = {L: pesos_bootstrap(n_d, L, sp['analisis']['bootstrap']['replicas'], sp['analisis']['bootstrap']['semilla']) for L in (1, 7, 14)}
    out = {'calendario': [cal[0], cal[-1]], 'n_dias': n_d, 'estaciones': stations_link, 'procedencia_obs': prov, 'nota': 'bootstrap circular sobre los días ordenados atravesando el hueco 1-9 de agosto; aproximación declarada',
           'dias_obs_validos': {c: int(np.isfinite(obs[i]).sum()) for i, c in enumerate(stations_link)},
           'dias_pronostico_validos': {s: {c: int(np.isfinite(F[s][i]).sum()) for i, c in enumerate(stations_link)} for s in SERIES}, 'comparaciones': {}, 'por_estacion': {}}
    for cname, (A, B) in COMPARACIONES.items():
        sA, sB, n, _ = sumas(pn, idx, A, B, k, obs_mean=om)
        out['comparaciones'][cname] = {'n': int(n.sum()), 'por_bloque': {str(L): resumen(comparar(sA, sB, n, W)) for L, W in Ws.items()}}
    for i, code in enumerate(stations_link):
        m_st = np.zeros((n_s, n_d), dtype=bool); m_st[i, :] = True
        out['por_estacion'][code] = {}
        for cname, (A, B) in COMPARACIONES.items():
            sA, sB, n, _ = sumas(pn, idx, A, B, k, mask_extra=m_st, obs_mean=om)
            out['por_estacion'][code][cname] = {'n': int(n.sum()), 'por_bloque': {str(L): resumen(comparar(sA, sB, n, W)) for L, W in Ws.items()}}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--forecasts', default=str(RAW / 'forecasts'))
    ap.add_argument('--state', default=str(STATE / 'descarga_pronosticos.json'))
    ap.add_argument('--out', default=str(OUT / 'resultados.json'))
    ap.add_argument('--replicas', type=int, default=None)
    ap.add_argument('--sorteos', type=int, default=None)
    ap.add_argument('--sin-enlace', action='store_true')
    ap.add_argument('--enlace-opcional', action='store_true',
                    help='no abortar si el enlace 06-18 UTC falla; marca el resultado como degradado')
    args = ap.parse_args()
    sp = spec()
    replicas = args.replicas or sp['analisis']['bootstrap']['replicas']
    sorteos = args.sorteos or sp['analisis']['sensibilidad_instrumento']['b_monte_carlo']['sorteos']
    seed_boot = sp['analisis']['bootstrap']['semilla']
    seed_mc = sp['analisis']['sensibilidad_instrumento']['b_monte_carlo']['semilla']
    s0, s1 = sp['ventanas']['secundaria']['dias_objetivo']
    p0, p1 = sp['ventanas']['primaria']['dias_objetivo']
    calendar = dias(s0, p1)
    panel = Panel(sp, calendar)
    panel.load_obs(load(DATOS / 'observaciones_diarias.json'))
    state = load(args.state)
    n_ok = panel.load_forecasts(args.forecasts, state)
    # exclusión de estaciones por cobertura (regla congelada): ya evaluada en estaciones.json
    est = load(OUT / 'estaciones.json')
    excluidas = [e['codigo'] for e in est['estaciones'] if e['cobertura']['excluida_por_cobertura']]
    for code in excluidas:
        i = panel.codes.index(code)
        panel.obs[i, :] = np.nan
    # inicio ajustable de la secundaria: primer día con las cuatro pasadas archivadas
    def runs_ok(d):
        r = (date.fromisoformat(d) - timedelta(days=1)).isoformat()
        return all(state['peticiones'].get(f'{r}T{c}00_{m}', {}).get('estado') == 'ok' for c in ('00', '06') for m in ('ecmwf_ifs025', 'ecmwf_aifs025_single'))
    sec_days = [d for d in dias(s0, s1) if runs_ok(d)]
    sec_first = sec_days[0] if sec_days else None
    Ws_cache = {}
    res = {'generado_utc': now(), 'metodo_sha256': load(STATE / 'metodo_fijado_recibo.json')['sha256'], 'replicas': replicas, 'sorteos': sorteos,
           'pronosticos': {'peticiones_ok': n_ok, 'peticiones_totales': len(state['peticiones']), 'estados': {}},
           'estaciones_excluidas_por_cobertura': excluidas, 'celdas': {c: {'lat': v[0], 'lon': v[1], 'elevacion': v[2]} for c, v in panel.cells.items()}}
    for v in state['peticiones'].values():
        res['pronosticos']['estados'][v.get('estado', 'pending')] = res['pronosticos']['estados'].get(v.get('estado', 'pending'), 0) + 1
    # cobertura de pronósticos por serie y ventana
    res['cobertura_pronosticos'] = {}
    for wname, (a, b) in (('primaria', (p0, p1)), ('secundaria', (sec_first or s0, s1))):
        _, idx = ventana(panel, a, b)
        res['cobertura_pronosticos'][wname] = {s: int(np.isfinite(panel.F[s][:, idx]).sum()) for s in SERIES}
        res['cobertura_pronosticos'][wname]['obs'] = int(np.isfinite(panel.obs[:, idx]).sum())
        res['cobertura_pronosticos'][wname]['dias'] = int(len(idx))
    res['primaria'] = analizar_ventana(panel, 'primaria', p0, p1, Ws_cache, replicas, seed_boot)
    res['sensibilidad_determinista'] = sensibilidad_determinista(panel, p0, p1, Ws_cache, replicas, seed_boot)
    res['sensibilidad_montecarlo'] = sensibilidad_montecarlo(panel, p0, p1, Ws_cache, replicas, seed_boot, sorteos, seed_mc, res['primaria'])
    if sec_first:
        res['secundaria'] = analizar_ventana(panel, 'secundaria', sec_first, s1, Ws_cache, replicas, seed_boot, con_estratos=False)
        res['secundaria']['inicio_ajustado'] = sec_first
    else:
        res['secundaria'] = {'estado': 'sin pasadas archivadas en la ventana secundaria'}
    if not args.sin_enlace:
        try:
            res['enlace_06_18'] = enlace_0618(sp, panel, state, args.forecasts)
        except Exception as e:
            # Hasta v1.0.1 este fallo se guardaba dentro de resultados.json y el programa
            # terminaba en 0, de modo que la seccion 6.5 desaparecia en silencio. Ahora
            # aborta salvo que se pida explicitamente tolerarlo.
            if not args.enlace_opcional:
                raise SystemExit(
                    f'ERROR: no se pudo construir el enlace 06-18 UTC ({type(e).__name__}: {e}).\n'
                    'Es la seccion 6.5 del informe y necesita los semihorarios heredados de raw/heredado.\n'
                    'Si de verdad quiere un resultado sin esa seccion, repita con --enlace-opcional.')
            res['enlace_06_18'] = {'error': f'{type(e).__name__}: {e}', 'degradado': True}
            print('AVISO: resultados degradados, sin enlace 06-18 UTC:', e, flush=True)
    dump(args.out, res)
    # panel para verificación independiente
    dump(Path(args.out).with_name('panel_analisis.json'), {'calendario': calendar, 'estaciones': panel.codes,
         'obs_wh_m2': [[None if not np.isfinite(x) else float(x) for x in row] for row in panel.obs],
         **{s: [[None if not np.isfinite(x) else float(x) for x in row] for row in panel.F[s]] for s in SERIES}})
    h7 = res['primaria']['holm']['7']
    print(json.dumps({'peticiones_ok': n_ok, 'H1_L7': res['primaria']['comparaciones']['H1']['por_bloque']['7'], 'H2_L7': res['primaria']['comparaciones']['H2']['por_bloque']['7'], 'holm_L7': h7}, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
