"""Figuras: figura_principal.png (efecto por estación con IC95 L=7, H1 y H2) y figura_sensibilidad.png
(Monte Carlo por estación + determinista con k común + curva del efecto frente a k).
Ejecutar con el intérprete que tenga matplotlib. Uso: python figuras.py [--resultados F] [--outdir D]
"""
from comun import *
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
VERDE, ROJO = '#216e6a', '#a54c34'


def principal(res, est, outdir):
    pr = res['primaria']
    codes = [e['codigo'] for e in est['estaciones']]
    lat = {e['codigo']: e['latitud'] for e in est['estaciones']}
    order = sorted(codes, key=lambda c: lat[c])
    fig, axes = plt.subplots(1, 2, figsize=(12, 10), sharey=True)
    for ax, (h, title, col) in zip(axes, (('H1', 'H1: IFS 00 → 06 UTC (valor de la actualización)', VERDE), ('H2', 'H2: IFS 00 → AIFS 00 UTC (IA frente a física)', ROJO))):
        y = np.arange(len(order))
        g = lambda c, k: pr['por_estacion'][c][h]['por_bloque']['7'][k]
        ef = np.array([g(c, 'efecto') if g(c, 'efecto') is not None else np.nan for c in order])
        lo = np.array([g(c, 'ic95')[0] if g(c, 'ic95')[0] is not None else np.nan for c in order])
        hi = np.array([g(c, 'ic95')[1] if g(c, 'ic95')[1] is not None else np.nan for c in order])
        pooled = pr['comparaciones'][h]['por_bloque']['7']
        k95 = res['sensibilidad_determinista']['por_k']['0.95']['comparaciones'][h]['7']
        ax.axvline(0, color='#444', lw=1)
        if pooled['efecto'] is not None:
            ax.axvspan(pooled['ic95'][0], pooled['ic95'][1], color=col, alpha=0.12, label=f'agregado: {pooled["efecto"]:.2f} % IC95 [{pooled["ic95"][0]:.2f}; {pooled["ic95"][1]:.2f}]'.replace('.', ','))
            ax.axvline(pooled['efecto'], color=col, lw=1.5)
        ax.axvline(k95['efecto'], color='#444', lw=1.5, ls=':', label=f'agregado con k = 0,95: {k95["efecto"]:.2f} %'.replace('.', ','))
        ax.errorbar(ef, y, xerr=[ef - lo, hi - ef], fmt='o', color=col, ecolor=col, elinewidth=1, capsize=2, ms=4, label='estación: efecto e IC95 (bloques de 7 días)')
        ax.set_yticks(y, [f'{c} ({lat[c]:.1f}°N)' for c in order])
        ax.set_title(title, loc='left', fontsize=10, fontweight='bold')
        ax.set_xlabel('Reducción relativa de MAE (%). Positivo = la segunda serie es mejor')
        ax.grid(axis='x', alpha=0.2); ax.set_axisbelow(True)
        ax.set_ylim(-1.5, len(order) - 0.5)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fontsize=8, frameon=False)
    fig.suptitle('Efecto por estación, ventana primaria (14 mayo–31 agosto 2026), estaciones ordenadas por latitud', x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, 0.004, 'Comparaciones relativas contra la misma observación SiAR. La comparación no es invariante a cambios de escala de la observación:\nla línea punteada es el mismo agregado si la red midiera un 5 % de menos (secciones 5 y 7). Intervalos bootstrap por días completos.', fontsize=8, va='bottom')
    fig.tight_layout(rect=[0, 0.042, 1, 0.96])
    fig.savefig(Path(outdir) / 'figura_principal.png', dpi=160)
    plt.close(fig)


def sensibilidad(res, dg, outdir):
    mc = res['sensibilidad_montecarlo']['comparaciones']
    pr = res['primaria']['comparaciones']
    dk = res['sensibilidad_determinista']['por_k']
    fig = plt.figure(figsize=(12, 8.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.15], hspace=0.45, wspace=0.2)
    for j, (h, title, col) in enumerate((('H1', 'H1: IFS 00 → 06 UTC', VERDE), ('H2', 'H2: IFS 00 → AIFS 00 UTC', ROJO))):
        ax = fig.add_subplot(gs[0, j])
        e = np.array(mc[h]['efectos'])
        k95 = dk['0.95']['comparaciones'][h]['7']['efecto']; k105 = dk['1.05']['comparaciones'][h]['7']['efecto']
        ef = pr[h]['por_bloque']['7']['efecto']
        lo = min(e.min(), k95, 0) - 1.5; hi = max(e.max(), k105, 0) + 1.5
        ax.hist(e, bins=40, color=col, alpha=0.75, label=f'1.000 sorteos de k por estación (preespecificado)')
        ax.axvline(0, color='#444', lw=1)
        ax.axvline(ef, color='black', lw=1.5, ls='--', label=f'observación tal cual: {ef:.2f} %'.replace('.', ','))
        for kv, val, ls in ((0.95, k95, ':'), (1.05, k105, '-.')):
            ax.axvline(val, color='#444', lw=1.6, ls=ls, label=f'toda la red con k = {kv:.2f}: {val:.2f} %'.replace('.', ','))
        ax.set_xlim(lo, hi)
        ax.set_title(title, loc='left', fontsize=10, fontweight='bold')
        ax.set_xlabel('Reducción relativa de MAE (%)'); ax.set_ylabel('sorteos')
        ax.legend(fontsize=7.5, frameon=True, facecolor='white', framealpha=0.95, edgecolor='none', loc='upper left')
    ax = fig.add_subplot(gs[1, :])
    for h, col, lab in (('H1', VERDE, 'H1: IFS 00 → 06 UTC'), ('H2', ROJO, 'H2: IFS 00 → AIFS 00 UTC')):
        cu = dg['cruce_k_comun'][h]['curva']
        ks = np.array([float(k) for k in cu]); vs = np.array([cu[k] for k in cu])
        o = np.argsort(ks); ks, vs = ks[o], vs[o]
        ax.plot(ks, vs, color=col, lw=2, label=lab)
        kc = dg['cruce_k_comun'][h]['k_cruce']
        if kc:
            ax.plot([kc], [0], 'o', color=col, ms=7, mfc='white', mew=2)
            xt, yt = (kc + 0.004, 4.0) if h == 'H1' else (kc + 0.004, -6.5)
            ax.annotate(f'cruza cero en k = {kc:.3f}: cambio de observación del {100*(1/kc-1):.2f} %'.replace('.', ','),
                        xy=(kc, 0), xytext=(xt, yt), fontsize=8, color=col, ha='left',
                        arrowprops=dict(arrowstyle='-', color=col, lw=0.8, shrinkA=0, shrinkB=4))
    ax.axhline(0, color='#444', lw=1)
    # la auditoria mide d = (satelite - medida)/medida, luego k = 1/(1+d), no 1-d
    k_lo, k_hi = 1 / (1 + 0.1575), 1 / (1 + 0.0263)
    ax.axvspan(0.95, 1.05, color='#8a6d3b', alpha=0.13, label='banda de sensibilidad fijada: k de 0,95 a 1,05 (no intervalo estimado)')
    ax.axvline(1.0, color='#888', lw=1, ls='--')
    ax.set_xlim(0.855, 1.10); ax.set_xlabel('k: factor del escenario (observación usada = observación publicada / k; no estima el error del sensor)')
    ax.set_ylabel('Reducción relativa de MAE (%)')
    ax.set_title('Efecto frente al factor común k (diagnóstico posterior; no estima el k real)', loc='left', fontsize=10, fontweight='bold')
    ax.grid(alpha=0.2); ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc='upper left')
    fig.suptitle('Sensibilidad de escala en la ventana primaria (14 mayo–31 agosto 2026)', x=0.01, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, 0.005, 'Arriba, el Monte Carlo preespecificado sortea un factor independiente en cada estación: sus efectos se muestran bajo esa hipótesis de independencia.\nLas líneas punteadas son el análisis determinista con un mismo factor en toda la red, que invierte H2. Abajo, el efecto en función de ese factor común. Dividir la observación por k\nes algebraicamente idéntico a multiplicar los pronósticos por k: el eje no distingue el sensor del pronóstico (§5).', fontsize=8, va='bottom')
    fig.tight_layout(rect=[0, 0.045, 1, 0.95])
    fig.savefig(Path(outdir) / 'figura_sensibilidad.png', dpi=160)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resultados', default=str(OUT / 'resultados.json'))
    ap.add_argument('--outdir', default=str(OUT))
    args = ap.parse_args()
    res = load(args.resultados)
    est = load(OUT / 'estaciones.json')
    dg = load(DATOS / 'diagnostico_posterior.json')
    principal(res, est, args.outdir)
    sensibilidad(res, dg, args.outdir)
    print('figuras en', args.outdir)


if __name__ == '__main__':
    main()
