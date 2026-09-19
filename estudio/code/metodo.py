"""Funciones puras del método congelado (metodo_fijado.json). Sin E/S.

- agregación diaria de series horarias (marcas D 01:00 … D+1 00:00, medias de la hora precedente)
- nubosidad diurna (marcas 06:00 … 18:00)
- bootstrap por bloques circulares de días (matriz de pesos)
- MAE relativo, efecto (reducción relativa de MAE), intervalos y p bilateral
- Holm-Bonferroni
"""
from datetime import date, datetime, timedelta
import math
import numpy as np

SERIES = ['IFS_00', 'IFS_06', 'AIFS_00', 'AIFS_06']
MODEL_OF = {'IFS': 'ecmwf_ifs025', 'AIFS': 'ecmwf_aifs025_single'}
COMPARACIONES = {'H1': ('IFS_00', 'IFS_06'), 'H2': ('IFS_00', 'AIFS_00'), 'S1': ('AIFS_00', 'AIFS_06'), 'S2': ('IFS_06', 'AIFS_06')}
MJ_TO_WH = 1000.0 / 3.6


def dias(first, last):
    d0, d1 = date.fromisoformat(first), date.fromisoformat(last)
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


def total_diario(times, values, target_day):
    """Suma de las 24 marcas target_day 01:00 … target_day+1 00:00. None si falta alguna o está fuera de [0, 1500]."""
    d = date.fromisoformat(target_day)
    wanted = [f'{d.isoformat()}T{h:02d}:00' for h in range(1, 24)] + [f'{(d + timedelta(days=1)).isoformat()}T00:00']
    pos = {t: i for i, t in enumerate(times)}
    total = 0.0
    for w in wanted:
        i = pos.get(w)
        if i is None:
            return None
        v = values[i]
        if v is None or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 or v > 1500:
            return None
        total += float(v)
    return total


def nubosidad_diurna(times, values, target_day):
    """Media simple de las 13 marcas target_day 06:00 … 18:00; None si falta alguna o está fuera de [0, 100]."""
    wanted = [f'{target_day}T{h:02d}:00' for h in range(6, 19)]
    pos = {t: i for i, t in enumerate(times)}
    acc = 0.0
    for w in wanted:
        i = pos.get(w)
        if i is None:
            return None
        v = values[i]
        if v is None or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 or v > 100:
            return None
        acc += float(v)
    return acc / 13.0


def suma_0618(times, values, target_day):
    """Suma de las 12 marcas target_day 07:00 … 18:00 (medias de la hora precedente ⇒ 06-18 UTC). None si falta alguna."""
    wanted = [f'{target_day}T{h:02d}:00' for h in range(7, 19)]
    pos = {t: i for i, t in enumerate(times)}
    total = 0.0
    for w in wanted:
        i = pos.get(w)
        if i is None:
            return None
        v = values[i]
        if v is None or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 or v > 1500:
            return None
        total += float(v)
    return total


def pesos_bootstrap(n_dias, L, replicas, seed):
    """Matriz (replicas × n_dias) con el número de veces que cada día entra en cada réplica.
    Bloques circulares móviles de longitud L, ceil(n/L) bloques, inicio uniforme, truncado a n días."""
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(n_dias / L)
    starts = rng.integers(0, n_dias, size=(replicas, n_blocks))
    idx = (starts[:, :, None] + np.arange(L)[None, None, :]) % n_dias
    idx = idx.reshape(replicas, n_blocks * L)[:, :n_dias]
    W = np.zeros((replicas, n_dias), dtype=np.float64)
    rows = np.repeat(np.arange(replicas), n_dias)
    np.add.at(W, (rows, idx.ravel()), 1.0)
    return W


def efecto(mae_a, mae_b):
    return (mae_a - mae_b) / mae_a * 100.0


def p_bilateral(reps):
    reps = np.asarray(reps, dtype=float)
    reps = reps[np.isfinite(reps)]
    if reps.size == 0:
        return None
    lo = float(np.mean(reps <= 0))
    hi = float(np.mean(reps >= 0))
    return float(min(1.0, max(0.0, 2.0 * min(lo, hi))))


def comparar(sumA, sumB, n, W):
    """sumA, sumB, n: vectores por día (suma de |r| y número de estación-días). W: pesos bootstrap.
    Devuelve dict con MAE puntuales, efecto, intervalo 95 %, p y réplicas del efecto."""
    N = float(n.sum())
    if N == 0 or sumA.sum() == 0:
        return {'n': int(N), 'mae_a': None, 'mae_b': None, 'efecto': None, 'ic95': [None, None], 'p': None, 'replicas': None}
    mae_a = float(sumA.sum() / N)
    mae_b = float(sumB.sum() / N)
    ef = efecto(mae_a, mae_b)
    Wn = W @ n
    with np.errstate(divide='ignore', invalid='ignore'):
        ra = (W @ sumA) / Wn
        rb = (W @ sumB) / Wn
        reps = (ra - rb) / ra * 100.0
    ok = np.isfinite(reps)
    lo, hi = (np.percentile(reps[ok], [2.5, 97.5]) if ok.any() else (np.nan, np.nan))
    return {'n': int(N), 'mae_a': mae_a, 'mae_b': mae_b, 'efecto': ef, 'ic95': [float(lo), float(hi)], 'p': p_bilateral(reps), 'replicas': reps}


def holm(pvals, alpha=0.05):
    """pvals: dict nombre -> p. Devuelve dict nombre -> {'p': p, 'p_ajustado': q, 'rechaza': bool}."""
    items = [(k, v) for k, v in pvals.items() if v is not None]
    m = len(items)
    items.sort(key=lambda kv: kv[1])
    out, running = {}, 0.0
    for rank, (k, p) in enumerate(items):
        adj = min(1.0, (m - rank) * p)
        running = max(running, adj)
        out[k] = {'p': p, 'p_ajustado': running, 'rechaza': bool(running < alpha)}
    for k, v in pvals.items():
        if v is None:
            out[k] = {'p': None, 'p_ajustado': None, 'rechaza': False}
    return out


def conclusion_intervalo(ic):
    lo, hi = ic
    if lo is None or hi is None or not (math.isfinite(lo) and math.isfinite(hi)):
        return 'indefinido'
    if lo > 0:
        return 'positivo'
    if hi < 0:
        return 'negativo'
    return 'incluye_cero'


def h0_fao56(lat_deg, d):
    J = d.timetuple().tm_yday
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * J / 365)
    delta = 0.409 * math.sin(2 * math.pi * J / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return (24 * 60 / math.pi) * 0.0820 * dr * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
