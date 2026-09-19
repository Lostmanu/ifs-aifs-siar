"""DIAGNOSTICO POSTERIOR, FUERA DE LA ESPECIFICACION CONGELADA. No es un resultado del estudio.

Se calculo DESPUES de ver los resultados, para interpretar la sensibilidad al instrumento preespecificada.
No entra en las hipotesis, no cambia ningun veredicto y no se corrige por multiplicidad.

Contiene: metricas alternativas CON intervalo bootstrap (mismo esquema y semilla que el analisis),
descomposicion sesgo/dispersion, distribucion del sesgo por estacion, curva del efecto frente a un factor
de escala comun k y su cruce por cero, comparacion de k comun frente a k independiente, LOSO, y
redundancia espacial tanto del error bruto como del estadistico comparado.

Escribe datos/diagnostico_posterior.json. Lee panel_analisis.json y metodo_fijado.json.
"""
from comun import *
from metodo import pesos_bootstrap, p_bilateral, conclusion_intervalo
import math
import numpy as np

COMPS = {'H1': ('IFS_00', 'IFS_06'), 'H2': ('IFS_00', 'AIFS_00'), 'S1': ('AIFS_00', 'AIFS_06'), 'S2': ('IFS_06', 'AIFS_06')}
REPLICAS_MEDIANA = 2000


def main():
    sp = spec()
    P = load(OUT / 'panel_analisis.json')
    cal, codes = P['calendario'], P['estaciones']
    arr = lambda k: np.array([[np.nan if v is None else v for v in row] for row in P[k]], dtype=float)
    obs = arr('obs_wh_m2'); F = {s: arr(s) for s in ['IFS_00', 'IFS_06', 'AIFS_00', 'AIFS_06']}
    p0, p1 = sp['ventanas']['primaria']['dias_objetivo']
    idx = np.array([i for i, d in enumerate(cal) if p0 <= d <= p1])
    O = obs[:, idx]; S = {s: F[s][:, idx] for s in F}
    nd = len(idx)
    replicas = sp['analisis']['bootstrap']['replicas']
    semilla = sp['analisis']['bootstrap']['semilla']
    W = {L: pesos_bootstrap(nd, L, replicas, semilla) for L in (1, 7, 14)}
    Wmed = {L: pesos_bootstrap(nd, L, REPLICAS_MEDIANA, semilla) for L in (1, 7, 14)}

    def piezas(a, b, k=None, quitar_sesgo=False):
        """Sumas por dia necesarias para cada metrica, sobre los pares completos de la comparacion."""
        kk = np.ones(len(codes)) if k is None else np.asarray(k, dtype=float)
        o = O / kk[:, None]
        with np.errstate(invalid='ignore'):
            om = np.nanmean(o, axis=1)
        fa, fb = S[a], S[b]
        m = np.isfinite(o) & np.isfinite(fa) & np.isfinite(fb)
        da = np.where(m, fa - o, np.nan); db = np.where(m, fb - o, np.nan)
        if quitar_sesgo:
            with np.errstate(invalid='ignore'):
                ba = np.nanmean(da, axis=1); bb = np.nanmean(db, axis=1)
            da = da - ba[:, None]; db = db - bb[:, None]
        ea = np.where(m, np.abs(da), 0.0); eb = np.where(m, np.abs(db), 0.0)
        rel_a_mat = np.where(m, ea / om[:, None], 0.0); rel_b_mat = np.where(m, eb / om[:, None], 0.0)
        return {'n': m.sum(axis=0).astype(float), 'mask': m,
                'abs_a': ea.sum(axis=0), 'abs_b': eb.sum(axis=0),
                'rel_a': rel_a_mat.sum(axis=0), 'rel_b': rel_b_mat.sum(axis=0),
                'rel_a_mat': rel_a_mat, 'rel_b_mat': rel_b_mat,
                'sq_a': (ea ** 2).sum(axis=0), 'sq_b': (eb ** 2).sum(axis=0),
                'ea': ea, 'eb': eb}

    def bootstrap_cociente(sa, sb, n, L, raiz=False):
        """Efecto puntual, IC95 y p para un estimador que es cociente de sumas (MAE rel/abs) o su raiz (RMSE)."""
        N = n.sum()
        f = (lambda x: math.sqrt(x)) if raiz else (lambda x: x)
        ma, mb = f(sa.sum() / N), f(sb.sum() / N)
        ef = (ma - mb) / ma * 100
        Wn = W[L] @ n
        with np.errstate(divide='ignore', invalid='ignore'):
            ra = (W[L] @ sa) / Wn; rb = (W[L] @ sb) / Wn
            if raiz:
                ra, rb = np.sqrt(ra), np.sqrt(rb)
            reps = (ra - rb) / ra * 100
        ok = np.isfinite(reps)
        lo, hi = np.percentile(reps[ok], [2.5, 97.5])
        return {'efecto': float(ef), 'ic95': [float(lo), float(hi)], 'p': p_bilateral(reps), 'conclusion_ic': conclusion_intervalo([float(lo), float(hi)]), 'n': int(N)}

    def bootstrap_mediana(pz, L):
        """Mediana ponderada del error absoluto por replica (menos replicas: coste de memoria)."""
        m = pz['mask']
        ii, jj = np.nonzero(m)
        va = pz['ea'][ii, jj]; vb = pz['eb'][ii, jj]
        oa = np.argsort(va); ob = np.argsort(vb)
        va_s, vb_s = va[oa], vb[ob]
        ja, jb = jj[oa], jj[ob]
        Wm = Wmed[L]
        wa = Wm[:, ja]; wb = Wm[:, jb]
        ca = np.cumsum(wa, axis=1); cb = np.cumsum(wb, axis=1)
        ha = ca[:, -1:] / 2.0; hb = cb[:, -1:] / 2.0
        ia = (ca >= ha).argmax(axis=1); ib = (cb >= hb).argmax(axis=1)
        reps = (va_s[ia] - vb_s[ib]) / va_s[ia] * 100
        reps = reps[np.isfinite(reps)]
        # el punto usa la MISMA definicion que las replicas (mediana ponderada inferior con pesos 1),
        # no np.median, que con N par interpola entre los dos centrales y seria otro estimador
        med_a = float(va_s[(len(va_s) - 1) // 2]); med_b = float(vb_s[(len(vb_s) - 1) // 2])
        ef = (med_a - med_b) / med_a * 100
        lo, hi = np.percentile(reps, [2.5, 97.5])
        return {'efecto': float(ef), 'ic95': [float(lo), float(hi)], 'p': p_bilateral(reps), 'conclusion_ic': conclusion_intervalo([float(lo), float(hi)]),
                'replicas': int(reps.size), 'definicion': 'mediana ponderada inferior, la misma en el punto y en las replicas', 'mediana_a': med_a, 'mediana_b': med_b}

    out = {'aviso': 'DIAGNOSTICO POSTERIOR fuera de la especificacion congelada; calculado despues de ver los resultados; no es resultado del estudio, no cambia ningun veredicto y no se corrige por multiplicidad',
           'generado_utc': now(), 'ventana': [p0, p1], 'replicas_bootstrap': replicas, 'replicas_mediana': REPLICAS_MEDIANA, 'semilla_bootstrap': semilla}

    # --- metricas alternativas con intervalo (L = 1, 7, 14) ---
    out['metricas_alternativas'] = {}
    out['nota_sin_sesgo'] = ('la columna "sin sesgo" resta a cada serie su sesgo medio por estacion estimado sobre la muestra completa; '
                             'sus intervalos NO propagan la incertidumbre de esos 34 sesgos estimados, de modo que son optimistas por construccion')
    for c, (a, b) in COMPS.items():
        pz = piezas(a, b); pzs = piezas(a, b, quitar_sesgo=True)
        ent = {}
        for L in (1, 7, 14):
            ent[str(L)] = {
                'mae_rel': bootstrap_cociente(pz['rel_a'], pz['rel_b'], pz['n'], L),
                'mae_abs': bootstrap_cociente(pz['abs_a'], pz['abs_b'], pz['n'], L),
                'rmse': bootstrap_cociente(pz['sq_a'], pz['sq_b'], pz['n'], L, raiz=True),
                'mediana_abs': bootstrap_mediana(pz, L),
                'sin_sesgo_rel': bootstrap_cociente(pzs['rel_a'], pzs['rel_b'], pz['n'], L),
                'sin_sesgo_abs': bootstrap_cociente(pzs['abs_a'], pzs['abs_b'], pz['n'], L),
            }
        # rango sobre TODAS las metricas, para que el informe no pueda elegir un par a mano
        vals = {k: v['efecto'] for k, v in ent['7'].items() if k != 'sin_sesgo_abs'}
        ent['rango_todas_las_metricas_L7'] = {'min': min(vals.values()), 'min_metrica': min(vals, key=vals.get),
                                              'max': max(vals.values()), 'max_metrica': max(vals, key=vals.get),
                                              'metricas': list(vals)}
        out['metricas_alternativas'][c] = ent

    # --- sesgo y dispersion por serie; descomposicion del error cuadratico ---
    out['sesgo_dispersion'] = {}
    for s in F:
        m = np.isfinite(O) & np.isfinite(S[s]); d = np.where(m, S[s] - O, np.nan)
        sesgo = float(np.nanmean(d)); var = float(np.nanvar(d))
        out['sesgo_dispersion'][s] = {'sesgo_wh_m2': sesgo, 'sesgo_rel_pct': float(sesgo / np.nanmean(np.where(m, O, np.nan)) * 100),
                                      'desv_wh_m2': float(math.sqrt(var)), 'mse': sesgo ** 2 + var, 'mse_parte_sesgo': sesgo ** 2, 'mse_parte_varianza': var,
                                      'mae_wh_m2': float(np.nanmean(np.abs(d))),
                                      'mae_sin_sesgo_por_estacion_wh_m2': float(np.nanmean(np.abs(d - np.nanmean(d, axis=1)[:, None])))}
    # sesgo relativo POR ESTACION (comun a los dos modelos => lado de la observacion)
    out['sesgo_por_estacion'] = {}
    for s in ('IFS_00', 'AIFS_00'):
        m = np.isfinite(O) & np.isfinite(S[s])
        with np.errstate(invalid='ignore'):
            br = np.array([np.nanmean(np.where(m[i], S[s][i] - O[i], np.nan)) / np.nanmean(np.where(m[i], O[i], np.nan)) * 100 for i in range(len(codes))])
        orden = np.argsort(br)
        out['sesgo_por_estacion'][s] = {'media_pct': float(np.mean(br)), 'desv_pct': float(np.std(br, ddof=1)),
                                        'min_pct': float(br.min()), 'estacion_min': codes[int(orden[0])],
                                        'max_pct': float(br.max()), 'estacion_max': codes[int(orden[-1])],
                                        'por_estacion_pct': {codes[i]: float(br[i]) for i in range(len(codes))}}

    # --- curva del efecto frente a k comun y cruce por cero ---
    out['cruce_k_comun'] = {}
    # el rango llega a 0,855 para cubrir la discrepancia maxima medida por la auditoria de referencia
    # (15,75 % por debajo => k = 1/1,1575 = 0,864)
    ks = np.round(np.arange(0.855, 1.1001, 0.0025), 4)
    for c, (a, b) in COMPS.items():
        es = []
        for kv in ks:
            pz = piezas(a, b, k=np.full(len(codes), float(kv)))
            N = pz['n'].sum()
            ma, mb = pz['rel_a'].sum() / N, pz['rel_b'].sum() / N
            es.append(float((ma - mb) / ma * 100))
        cruces = []
        for i in range(1, len(ks)):
            if es[i - 1] * es[i] < 0:
                cruces.append(float(ks[i - 1] + (ks[i] - ks[i - 1]) * abs(es[i - 1]) / (abs(es[i - 1]) + abs(es[i]))))
        cruce = cruces[0] if cruces else None
        # discrepancia equivalente EN LAS UNIDADES DE LA AUDITORIA DE REFERENCIA, que mide
        # (satelite - medida)/medida = d, de modo que k = 1/(1+d) y por tanto d = 1/k - 1.
        out['cruce_k_comun'][c] = {'k_cruce': cruce, 'cruces_todos': cruces,
                                   'discrepancia_equivalente_pct': None if cruce is None else float((1 / cruce - 1) * 100),
                                   'sentido': None if cruce is None else ('el sensor mediría de menos' if cruce < 1 else 'el sensor mediría de más'),
                                   'nota_unidades': 'discrepancia_equivalente_pct = 1/k - 1, en la misma base que la auditoria de referencia (diferencia relativa al valor medido). No confundir con (1-k), que usa otra base.',
                                   'k_argmax': float(ks[int(np.argmax(es))]), 'efecto_argmax': float(max(es)),
                                   'cambia_de_signo_en_banda_5pct': bool(any(0.95 <= x <= 1.05 for x in cruces)),
                                   'curva': {f'{float(kv):.4f}': float(e) for kv, e in zip(ks, es)}}
        # parte invariante al instrumento: efecto sin sesgo bajo varios k
        sin_k = {}
        for kv in (0.95, 1.0, 1.05):
            pzs = piezas(a, b, k=np.full(len(codes), kv), quitar_sesgo=True)
            N = pzs['n'].sum()
            ma, mb = pzs['rel_a'].sum() / N, pzs['rel_b'].sum() / N
            sin_k[f'{kv:.2f}'] = float((ma - mb) / ma * 100)
        out['cruce_k_comun'][c]['efecto_sin_sesgo_bajo_k'] = sin_k

    # --- k comun sorteado frente a k independiente (misma ley que el MC preespecificado) ---
    rng = np.random.default_rng(20260918)
    nsort = 1000
    kind = rng.uniform(0.95, 1.05, size=(nsort, len(codes))); kcom = rng.uniform(0.95, 1.05, size=nsort)
    out['k_comun_vs_independiente'] = {'sorteos': nsort, 'semilla': 20260918,
                                       'desv_del_k_medio_independiente': float(kind.mean(axis=1).std()),
                                       'desv_del_k_comun': float(kcom.std()),
                                       'nota': 'la media de 34 k_i independientes se concentra en 1: el MC preespecificado equivale a un error de red de unas decimas de punto, no a un sesgo comun de red'}
    for c, (a, b) in COMPS.items():
        def ef_k(kv):
            pz = piezas(a, b, k=kv); N = pz['n'].sum()
            ma, mb = pz['rel_a'].sum() / N, pz['rel_b'].sum() / N
            return (ma - mb) / ma * 100
        ei = np.array([ef_k(kind[t]) for t in range(nsort)]); ec = np.array([ef_k(np.full(len(codes), kcom[t])) for t in range(nsort)])
        out['k_comun_vs_independiente'][c] = {'independiente': {'media': float(ei.mean()), 'desv': float(ei.std()), 'fraccion_signo_contrario': float((ei * np.sign(ei.mean()) < 0).mean())},
                                              'comun': {'media': float(ec.mean()), 'desv': float(ec.std()), 'p2_5': float(np.percentile(ec, 2.5)), 'p97_5': float(np.percentile(ec, 97.5)),
                                                        'fraccion_signo_contrario': float((ec * np.sign(ei.mean()) < 0).mean())}}

    # --- peso igual por estacion y leave-one-station-out ---
    out['por_estacion_peso_igual'] = {}; out['loso'] = {}; out['por_mes'] = {}
    dias = [cal[i] for i in idx]
    for c, (a, b) in COMPS.items():
        pz = piezas(a, b)
        ef = []
        for i in range(len(codes)):
            if not pz['mask'][i].any():
                continue
            ra = pz['rel_a_mat'][i].sum(); rb = pz['rel_b_mat'][i].sum()
            ef.append(float((ra - rb) / ra * 100))
        out['por_estacion_peso_igual'][c] = {'media': float(np.mean(ef)), 'mediana': float(np.median(ef)), 'negativas': int(sum(1 for x in ef if x < 0)), 'de': len(ef)}
        loso = []
        for i in range(len(codes)):
            sel = np.ones(len(codes), dtype=bool); sel[i] = False
            # mismo estimador oficial (MAE relativo) sobre las 33 estaciones restantes
            ra = pz['rel_a_mat'][sel].sum(); rb = pz['rel_b_mat'][sel].sum()
            loso.append((codes[i], float((ra - rb) / ra * 100)))
        vals = [v for _, v in loso]
        out['loso'][c] = {'min': float(min(vals)), 'max': float(max(vals)), 'sin_estacion_min': min(loso, key=lambda x: x[1])[0], 'sin_estacion_max': max(loso, key=lambda x: x[1])[0], 'todos_mismo_signo': bool(all(v > 0 for v in vals) or all(v < 0 for v in vals))}
        pm = {}
        for mes in sorted({d[:7] for d in dias}):
            col = np.array([d[:7] == mes for d in dias])
            ra = pz['rel_a'][col].sum(); rb = pz['rel_b'][col].sum()
            pm[mes] = float((ra - rb) / ra * 100)
            colf = np.array([d[:7] != mes for d in dias])
            ra2 = pz['rel_a'][colf].sum(); rb2 = pz['rel_b'][colf].sum()
            pm[f'sin_{mes}'] = float((ra2 - rb2) / ra2 * 100)
        out['por_mes'][c] = pm

    # --- redundancia espacial: error bruto frente a estadistico comparado ---
    def neff(M):
        C = np.ma.corrcoef(np.ma.masked_invalid(M)).data
        n = M.shape[0]
        r = float(np.nanmean(C[~np.eye(n, dtype=bool)]))
        # con r <= 0 la formula da un numero mayor que n, que no tiene sentido como "estaciones efectivas":
        # se acota en n y se deja constancia de la correlacion cruda.
        bruto = n / (1 + (n - 1) * r)
        return r, float(min(bruto, n)), float(bruto)
    r_bruto, n_bruto, n_crudo = neff(np.where(np.isfinite(O) & np.isfinite(S['IFS_00']), S['IFS_00'] - O, np.nan))
    out['redundancia_espacial'] = {'error_bruto_IFS_00': {'correlacion_media': r_bruto, 'estaciones_efectivas': n_bruto, 'sin_acotar': n_crudo},
                                   'nota': 'el bootstrap remuestrea dias completos, que es la unidad correlacionada; el estadistico que se compara es la diferencia de errores absolutos, mucho menos correlacionada entre estaciones que el error bruto. La cifra se acota en 34: con correlacion media <= 0 la formula da mas de 34 y eso no significa mas informacion que estaciones hay.'}
    for c, (a, b) in COMPS.items():
        pz = piezas(a, b)
        D = np.where(pz['mask'], pz['ea'] - pz['eb'], np.nan)
        r, ne, crudo = neff(D)
        out['redundancia_espacial'][c] = {'correlacion_media_diferencia_abs': r, 'estaciones_efectivas': ne, 'sin_acotar': crudo}

    # --- identificacion: dividir la observacion por k es ALGEBRAICAMENTE multiplicar los pronosticos por k ---
    def ef_reescalando_pronosticos(a, b, k):
        om = np.nanmean(O, axis=1)
        fa, fb = S[a] * k, S[b] * k
        m = np.isfinite(O) & np.isfinite(fa) & np.isfinite(fb)
        ra = np.where(m, np.abs(fa - O) / om[:, None], 0.0).sum(); rb = np.where(m, np.abs(fb - O) / om[:, None], 0.0).sum()
        return float((ra - rb) / ra * 100)
    ident = {'explicacion': 'r = |f - obs/k| / media(obs/k) = |k*f - obs| / media(obs): el eje k no distingue un sensor que mide de menos de unos pronosticos que vienen altos',
             'comprobacion': {}}
    peor = 0.0
    for c, (a, b) in COMPS.items():
        fila = {}
        for kv in (0.95, 1.0, 1.05):
            v1 = float(out['cruce_k_comun'][c]['curva'][f'{kv:.4f}']); v2 = ef_reescalando_pronosticos(a, b, kv)
            fila[f'{kv:.2f}'] = {'dividiendo_la_observacion': v1, 'multiplicando_los_pronosticos': v2, 'diferencia_abs': abs(v1 - v2)}
            peor = max(peor, abs(v1 - v2))
        ident['comprobacion'][c] = fila
    ident['diferencia_maxima'] = peor
    ident['identico'] = bool(peor < 1e-9)
    out['identificacion_del_eje_k'] = ident

    dump(DATOS / 'diagnostico_posterior.json', out)
    for c in ('H1', 'H2'):
        m7 = out['metricas_alternativas'][c]['7']
        print(f"{c}: " + "  ".join(f"{k}={v['efecto']:+.2f}% [{v['ic95'][0]:+.2f};{v['ic95'][1]:+.2f}] p={v['p']:.3f}" for k, v in m7.items()))
        cr = out['cruce_k_comun'][c]
        print(f"   cruce k={cr['k_cruce']:.4f} (discrepancia equivalente {cr['discrepancia_equivalente_pct']:.2f}%); argmax en k={cr['k_argmax']}; cambia de signo en +-5%: {cr['cambia_de_signo_en_banda_5pct']}; k comun signo contrario {100*out['k_comun_vs_independiente'][c]['comun']['fraccion_signo_contrario']:.1f}% vs independiente {100*out['k_comun_vs_independiente'][c]['independiente']['fraccion_signo_contrario']:.1f}%")
    print('sesgo por estacion IFS_00:', {k: (round(v, 2) if isinstance(v, float) else v) for k, v in out['sesgo_por_estacion']['IFS_00'].items() if k != 'por_estacion_pct'})
    print('redundancia:', {k: (round(v['correlacion_media_diferencia_abs'], 3), round(v['estaciones_efectivas'], 1)) for k, v in out['redundancia_espacial'].items() if isinstance(v, dict) and 'correlacion_media_diferencia_abs' in v})


if __name__ == '__main__':
    main()
