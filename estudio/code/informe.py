"""Genera informe.md a partir de resultados.json, estaciones.json, metodo_fijado.json y el diagnostico posterior.
No calcula nada nuevo: solo formatea cifras ya calculadas.

Uso: python informe.py [--resultados F] [--out F]
"""
from comun import *
from contexto_cierre import secundaria, antecedentes, descomposicion
from datetime import date, timedelta
import argparse


def f(x, nd=2, pct=False):
    if x is None:
        return 'n/d'
    s = f'{x:,.{nd}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s + (' %' if pct else '')


def ic(b):
    if not b or b.get('ic95') is None or b['ic95'][0] is None:
        return 'n/d'
    return f'[{f(b["ic95"][0])}; {f(b["ic95"][1])}]'


def pval(p):
    if p is None:
        return 'n/d'
    return '< 0,0002' if p < 0.0002 else f(p, 4)


def pausentes(sp):
    """Pasadas ausentes: (clave, pasada, dia objetivo, serie, dentro de la primaria)."""
    st = load(STATE / 'descarga_pronosticos.json')
    p0, p1 = sp['ventanas']['primaria']['dias_objetivo']
    out = []
    for k, v in sorted(st['peticiones'].items()):
        if v.get('estado') == 'ok':
            continue
        run, model = v['run'], v['model']
        tgt = (date.fromisoformat(run[:10]) + timedelta(days=1)).isoformat()
        serie = ('IFS' if model == 'ecmwf_ifs025' else 'AIFS') + '_' + run[11:13]
        out.append({'clave': k, 'run': run, 'objetivo': tgt, 'serie': serie, 'estado': v.get('estado'), 'dentro': p0 <= tgt <= p1})
    return out


def titular(res, sp, dg):
    pr = res['primaria']
    n_st = len(pr['por_estacion']) - len(res['estaciones_excluidas_por_cobertura'])
    n_days = pr['n_dias_calendario']
    h = pr['holm']
    mc = res['sensibilidad_montecarlo']['comparaciones']
    det = res['sensibilidad_determinista']
    dk = det['por_k']
    apoy = {k: all(h[L][k]['apoyada'] for L in ('1', '7', '14')) for k in ('H1', 'H2')}
    e1 = pr['comparaciones']['H1']['por_bloque']['7']; e2 = pr['comparaciones']['H2']['por_bloque']['7']
    k95 = {k: dk['0.95']['comparaciones'][k]['7'] for k in ('H1', 'H2')}
    cruce = dg['cruce_k_comun'] if dg else None
    robustas = [k for k in ('H1', 'H2') if det['veredicto'][k]['robusto_al_instrumento']]
    L = []
    if not robustas:
        L.append(f'**Las mejoras de las dos comparaciones primarias no superan todos los escenarios de sensibilidad de escala preespecificados, aunque las dos superan la corrección de multiplicidad con la observación tal cual; medido en {n_st} estaciones SiAR y {n_days} días objetivo de mayo a agosto de 2026, con una sola versión de cada modelo y sin invierno.**')
    elif len(robustas) == 1:
        otra = 'H2' if robustas[0] == 'H1' else 'H1'
        L.append(f'**{otra} no sobrevive al análisis de sensibilidad de escala; {robustas[0]} sí; medido en {n_st} estaciones SiAR y {n_days} días objetivo de mayo a agosto de 2026, sin invierno.**')
    else:
        L.append(f'**Las dos hipótesis primarias sobreviven al análisis de sensibilidad de escala, en {n_st} estaciones SiAR y {n_days} días objetivo de mayo a agosto de 2026, sin invierno.**')
    L.append('Con la observación tal cual, del 14 de mayo al 31 de agosto de 2026:')
    v1 = 'reduce' if (e1['efecto'] or 0) > 0 else 'aumenta'
    L.append(f'actualizar IFS del ciclo 00 al 06 UTC {v1} el MAE un {f(abs(e1["efecto"]))} % (IC95 con bloques de 7 días {ic(e1)}, {"supera" if apoy["H1"] else "no supera"} Holm) y AIFS mejora a IFS a igual ciclo un {f(e2["efecto"])} % ({ic(e2)}, {"supera" if apoy["H2"] else "no supera"} Holm).')
    L.append(f'Las dos fallan de maneras distintas al dividir la observación por un factor de escala común k: con k = 0,95 la actualización cae a {f(k95["H1"]["efecto"])} % y pierde el intervalo {ic(k95["H1"])} sin cambiar de signo, mientras que la ventaja de AIFS se invierte a {f(k95["H2"]["efecto"])} % {ic(k95["H2"])}.')
    if cruce:
        d2 = cruce['H2']['discrepancia_equivalente_pct']; d1 = cruce['H1']['discrepancia_equivalente_pct']
        L.append('La sensibilidad no estima el error real de los sensores. El resultado es una mejora condicionada a la referencia SiAR que no supera todos los escenarios de escala preespecificados; tampoco demuestra ausencia de capacidad predictiva.')
    s1 = {k: mc[k]['supervivencia_nivel1_signo'] for k in ('H1', 'H2')}
    L.append(f'Con errores independientes de ±5 % por estación (el Monte Carlo preespecificado) el signo sobrevive en el {f(100 * s1["H1"], 1)} % y el {f(100 * s1["H2"], 1)} % de los 1.000 sorteos, bajo una hipótesis de factores independientes y centrados en 1 que no incluye un desplazamiento común de red.')
    L.append('Y ese eje no está identificado: dividir la observación por k es algebraicamente idéntico a multiplicar los cuatro pronósticos por k, de modo que estos datos no distinguen un sensor que mide de menos de unos pronósticos que vienen altos.')
    L.append('La inversión de H2 no aparece en el escenario k=0,95 de la ventana secundaria: sus efectos puntuales son H1 +2,36 % y H2 +5,33 %. Esa extensión de escala es posterior; cambia la lectura entre ventanas, no el veredicto primario. La diferencia de periodo y versiones impide atribuirla solo a la estación del año. Véanse §6.2 bis y los antecedentes restituidos en §7.1.')
    return ' '.join(L)


def tabla_estaciones(est):
    lines = ['| Orden | Código | Nombre | Lat | Lon | Alt (m) | Celda | Dist. centro (km) | Piranómetro | Días válidos primaria (de 110) | Días válidos secundaria (de 40) | Excluida |', '|---|---|---|---:|---:|---:|---|---:|---|---:|---:|---|']
    for e in est['estaciones']:
        c = e['celda']
        cel = f'({c["centro_lat"]}, {c["centro_lon"]})' if c else 'Canarias'
        dist = f(c['distancia_km'], 1) if c else '—'
        cov = e['cobertura']
        lines.append(f'| {e["orden"]} | {e["codigo"]} | {e["nombre"]} | {f(e["latitud"], 3)} | {f(e["longitud"], 3)} | {e["ficha"].get("altitud")} | {cel} | {dist} | {e["ficha"].get("modeloPiranometro") or "sin dato en la ficha"} | {cov["dias_validos_primaria"]} | {cov["dias_validos_secundaria"]} | {"sí" if cov["excluida_por_cobertura"] else "no"} |')
    return '\n'.join(lines)


def tabla_comparacion(comp):
    lines = ['| Comparación | N estación-días | MAE_rel A | MAE_rel B | Efecto | IC95 L=1 | IC95 L=7 | IC95 L=14 | p L=1 | p L=7 | p L=14 |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for cname, c in comp.items():
        b = c['por_bloque']; b7 = b['7']
        n = c.get('n_estacion_dias', c.get('n'))
        lines.append(f'| {cname}: {c["series"][0]} → {c["series"][1]} | {n} | {f(100 * b7["mae_a"]) if b7["mae_a"] is not None else "n/d"} % | {f(100 * b7["mae_b"]) if b7["mae_b"] is not None else "n/d"} % | {f(b7["efecto"])} % | {ic(b["1"])} | {ic(b["7"])} | {ic(b["14"])} | {pval(b["1"]["p"])} | {pval(b["7"]["p"])} | {pval(b["14"]["p"])} |')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resultados', default=str(OUT / 'resultados.json'))
    ap.add_argument('--out', default=str(OUT / 'informe.md'))
    args = ap.parse_args()
    res = load(args.resultados)
    sp = spec()
    est = load(OUT / 'estaciones.json')
    rec = load(STATE / 'metodo_fijado_recibo.json')
    dgp = DATOS / 'diagnostico_posterior.json'
    dg = load(dgp) if dgp.exists() else None
    pr = res['primaria']
    aus = pausentes(sp)
    L = []
    L.append('# Medición a escala: valor de la actualización (IFS 00→06 UTC) e IA frente a física (AIFS vs IFS)\n')
    L.append(f'Informe generado el {now()[:19]} UTC · radiación global diaria · observaciones SiAR · pronósticos ECMWF servidos por Open-Meteo (Single Runs API)\n')
    L.append((f'Cálculo de `resultados.json`: {res["generado_utc"][:19]} UTC; ninguna cifra preespecificada ha cambiado desde entonces. Posteriores a ese cálculo, y por tanto escritos sabiendo ya el resultado: el anexo A entero ({dg["generado_utc"][:10] if dg else "n/d"}); '
              'la redacción del titular de §1; el párrafo sobre el alcance del Monte Carlo de §5; la tabla de pasadas ausentes de §3; las desviaciones declaradas de §2; las viñetas de §7 sobre las magnitudes medidas de la discrepancia, sobre la dispersión del sesgo por estación, sobre la identificación del eje k y la corrección sobre la interpolación horaria; '
              'y las dos figuras, que añaden la línea y el panel del análisis determinista. El veredicto de §1 lo produce la regla congelada de sensibilidad, no la redacción.\n') if dg else '')
    L.append('Revisión de cierre del 19-09-2026: se corrigen atribuciones causales, el alcance del centrado y las rutas de reproducción. No cambian datos, selección, método congelado ni resultados numéricos; el informe original queda conservado. Ver revision/cambios.json.\n')
    L.append('Corrección v1.0.1: se restituye contexto omitido y se declara el cambio de vocabulario. Los cálculos preespecificados permanecen intactos. Las nuevas comprobaciones de escala secundaria están separadas en datos/sensibilidad_secundaria_posterior.json.\n')
    L.append('## 1. Resultado en una frase\n')
    L.append(titular(res, sp, dg) + '\n')

    L.append('## 2. Qué se decidió antes de medir\n')
    L.append(f'- Especificación congelada: `metodo_fijado.json`, SHA-256 `{rec["sha256"]}`, escrita el {rec["congelado_en_utc"][:26]} UTC. El primer programa de descarga (observaciones SiAR) arrancó el {(rec.get("descargas_iniciadas_en_utc") or "n/d")[:26]} UTC, encadenado en el mismo comando que la congelación; la primera petición de pronósticos fue a las 14:44:50 UTC. Es una marca local y un hash, no un prerregistro externo. Encargo v2 con SHA-256 `{sp["encargo"]["sha256"]}`.')
    L.append(f'- Selección de estaciones por regla: rejilla 1,5°×1,5° (centros de latitud {sp["estaciones"]["rejilla"]["celdas_lat"]} y longitud {sp["estaciones"]["rejilla"]["celdas_lon"]}), la estación activa más próxima al centro de cada celda con estación ({sp["estaciones"]["rejilla"]["celdas_con_estacion"]} celdas), más la primera de Canarias por orden alfabético. Catálogo SiAR del 2026-09-14 07:41 UTC (SHA-256 `{sp["estaciones"]["catalogo"]["sha256"]}`), 520 estaciones activas, heredado de un trabajo previo del mismo día y anterior a la congelación. Ninguna sustitución tras ver datos; exclusión solo por < 80 % de días válidos en la ventana primaria.')
    L.append('- Hipótesis primarias: H1, reducción de MAE de IFS_00 → IFS_06 > 0; H2, reducción de MAE de IFS_00 → AIFS_00 > 0. Corrección de Holm-Bonferroni (α = 0,05) sobre los dos p bootstrap bilaterales. Secundarias exploratorias: AIFS_00 → AIFS_06, IFS_06 → AIFS_06, la ventana secundaria y la restricción 06-18 UTC.')
    L.append('- Ventanas definidas por la hora de inicialización de las pasadas, no por el día objetivo: el cambio de versión (IFS 50r1 y AIFS Single v2) ocurre en la pasada del 2026-05-12 06 UTC; la primaria son los días objetivo del 14 de mayo al 31 de agosto (110 días, todas las pasadas de la versión nueva) y la secundaria del 3 de abril al 12 de mayo (versión anterior; el archivo de Open-Meteo empieza el 2 de abril de 2026). El 13 de mayo es mixto y se excluye. El encargo escribía 12 de mayo–31 de agosto; se corrigió antes de descargar (C1 de la especificación).')
    L.append('- Bootstrap por días completos (todas las estaciones de cada día remuestreado), bloques circulares de 1, 7 y 14 días, 10.000 réplicas, semilla 20260914. Sensibilidad de escala: k ∈ {0,95; 1,00; 1,05} global y 1.000 sorteos de k_i ~ U(0,95; 1,05) por estación, semilla 20260915.')
    L.append('- Métrica: error relativo r = (pronóstico − observación)/media de la observación de la estación; MAE_rel = media de |r|; efecto = (MAE_A − MAE_B)/MAE_A × 100 sobre los mismos estación-días (pares completos por comparación).')
    L.append('')
    L.append('**Desviaciones respecto a la especificación congelada, y exposición previa a los datos:**\n')
    L.append('- *Regla de pasada ausente.* La especificación preveía que una pasada no archivada devolvería HTTP 400 con «model run is not available». El servicio devuelve, para peticiones de varias ubicaciones, HTTP 200 con un cuerpo de texto plano «Unexpected error while streaming data: modelRunUnavailable(...)», que el programa trataba como error transitorio y reintentaba sin fin. El 15 de septiembre a las 12:54 UTC se añadió al clasificador la regla «HTTP 200 con ese texto ⇒ pasada ausente», después de 12 reintentos de la misma pasada. Afecta a la clasificación de 5 peticiones, no a ningún dato descargado. La alternativa de la especificación (descargar por estación tras 12 fallos seguidos) no se ejecutó: esas pasadas no están en el archivo.')
    L.append('- *Exposición previa.* Dos de las 34 estaciones, AL10 y LU01, aparecen en la auditoría de vecinas del 14 de septiembre y sus semihorarios del 16 de junio al 31 de julio ya se habían descargado antes de la congelación; son 92 de los 3.731 estación-días observacionales de la ventana primaria (2,5 %). Las estaciones del piloto y de la réplica anteriores (AL01, C01, M01) no están entre las 34 salvo por la sección 6.5, que las usa explícitamente. La regla de rejilla se fijó y se aplicó sin sustituciones, pero el resultado del piloto (una mejora del orden del 8 % al actualizar el ciclo) era conocido al redactar las hipótesis.')
    L.append('- *Recuento por celda.* El programa de selección aplica «estación activa de huso 30 más próxima al centro», pero no implementa el filtro C5 (excluir nombres con «Invernadero» o «(malla)»). El recuento publicado de estaciones dentro de la celda (39,0, 0,0) es 33 e incluye una estación inelegible; bajo C5 serían 32. La estación seleccionada no cambia en ninguna celda, ni la canaria.')
    L.append(f'- *Anexo A.* Las métricas alternativas, el LOSO, la curva frente a k y la comparación de sorteos del anexo A no están en la especificación congelada; se calcularon el {dg["generado_utc"][:10] if dg else "n/d"}, después de ver los resultados, y no entran en las hipótesis ni en Holm.')
    L.append('- *Cambio de vocabulario posterior al resultado (v1.0.1).* La especificación denomina el criterio «robusto al instrumento»; el informe usa «robustez frente a escenarios de escala» porque k no identifica el instrumento. Se conservan la fórmula, los tres k, la regla de decisión y la clave JSON robusto_al_instrumento, sin reescribir el método congelado. La extensión de escala a la ventana secundaria y su rejilla ampliada de cruces se calculan después de los resultados y se identifican como exploratorias. Se restituyen además antecedentes bibliográficos, el contraste con MeteoGalicia y la descomposición del MSE, sin nuevos datos.\n')
    L.append('- *Figuras.* La especificación fija `figura_principal` como «efecto por estación con intervalo L = 7 y el efecto agregado» y `figura_sensibilidad` como «histograma del efecto de H1 y H2 en los 1.000 sorteos». Las dos añaden el análisis determinista: la primera, la línea del agregado con k = 0,95; la segunda, las marcas de k = 0,95 y k = 1,05 y un panel con la curva del efecto frente a k. Son adiciones posteriores al cálculo y no cambian ninguna cifra.\n')

    L.append('## 3. Muestra\n')
    exc = res['estaciones_excluidas_por_cobertura']
    L.append(f'{est["n_seleccionadas"]} estaciones seleccionadas; {len(exc)} excluidas por cobertura{(": " + ", ".join(exc)) if exc else ""}. Observaciones válidas en la ventana primaria: {res["cobertura_pronosticos"]["primaria"]["obs"]} estación-días de {res["cobertura_pronosticos"]["primaria"]["dias"] * est["n_seleccionadas"]} posibles. Pronósticos válidos (estación-días) en la primaria: ' + ', '.join(f'{s} {res["cobertura_pronosticos"]["primaria"][s]}' for s in ('IFS_00', 'IFS_06', 'AIFS_00', 'AIFS_06')) + f'. Peticiones a la API: {res["pronosticos"]["peticiones_ok"]} correctas de {res["pronosticos"]["peticiones_totales"]}.\n')
    L.append(tabla_estaciones(est) + '\n')
    tabla_obs = load(DATOS / 'observaciones_diarias.json')
    p0w, p1w = sp['ventanas']['primaria']['dias_objetivo']; s0w, s1w = sp['ventanas']['secundaria']['dias_objetivo']
    mot = {'primaria': {}, 'secundaria': {}, 'fuera de las dos ventanas': {}}
    for code, filas in tabla_obs.items():
        for r in filas:
            if r['valido'] or not r['motivo']:
                continue
            w = 'primaria' if p0w <= r['fecha'] <= p1w else ('secundaria' if s0w <= r['fecha'] <= s1w else 'fuera de las dos ventanas')
            mot[w].setdefault(code, {}); mot[w][code][r['motivo']] = mot[w][code].get(r['motivo'], 0) + 1
    for w in ('primaria', 'secundaria', 'fuera de las dos ventanas'):
        txt = '; '.join(f'{c}: ' + ', '.join(f'{k} ×{v}' for k, v in d.items()) for c, d in sorted(mot[w].items())) or 'ninguno'
        L.append(f'- Días observacionales no válidos, ventana {w}: {txt}.')
    L.append(f'\nLos {res["cobertura_pronosticos"]["primaria"]["obs"]} estación-días válidos de la primaria son 3.740 menos los no válidos de esa ventana. Los recuentos del catálogo de `estaciones.json` se refieren al rango descargado completo (1 de abril a 1 de septiembre) y por eso son mayores.\n')
    L.append('**Pasadas que el archivo del proveedor no tiene** (registradas como ausentes, sin sustituir por otro ciclo):\n')
    L.append('| Pasada | Día objetivo | Serie que falta | Efecto |\n|---|---|---|---|')
    for a in aus:
        if not a['dentro']:
            efe = 'ninguno: el 13 de mayo está excluido de las dos ventanas por mixto'
        else:
            efe = f'los {34 if a["objetivo"] == "2026-06-12" else 33} estación-días de ese día quedan sin {a["serie"]}'
        L.append(f'| {a["run"]} UTC | {a["objetivo"]} | {a["serie"]} | {efe} |')
    n_comp = {c: pr['comparaciones'][c]['n_estacion_dias'] for c in ('H1', 'H2', 'S1', 'S2')}
    L.append(f'\nPor eso N difiere entre comparaciones: H1 {n_comp["H1"]}, H2 {n_comp["H2"]}, S1 {n_comp["S1"]}, S2 {n_comp["S2"]}, frente a los {res["cobertura_pronosticos"]["primaria"]["obs"]} estación-días con observación válida. Cada comparación usa solo los estación-días en que sus dos series existen.\n')

    L.append('## 4. Resultado primario (ventana primaria, 14 mayo–31 agosto 2026)\n')
    L.append('Positivo = la segunda serie tiene menor MAE. MAE_rel en % de la observación media de cada estación; contaminado por la escala del instrumento y solo interpretable en la comparación.\n')
    L.append(tabla_comparacion({k: v for k, v in pr['comparaciones'].items() if k in ('H1', 'H2')}) + '\n')
    L.append('Veredicto tras Holm (α = 0,05), por largo de bloque:\n')
    L.append('| Largo de bloque | H1 p ajustado | H1 apoyada | H2 p ajustado | H2 apoyada |\n|---|---:|---|---:|---|')
    for Lb in ('1', '7', '14'):
        h = pr['holm'][Lb]
        L.append(f'| {Lb} {"día" if Lb == "1" else "días"} | {pval(h["H1"]["p_ajustado"])} | {"sí" if h["H1"]["apoyada"] else "no"} | {pval(h["H2"]["p_ajustado"])} | {"sí" if h["H2"]["apoyada"] else "no"} |')
    L.append('\n![Efecto por estación](figura_principal.png)\n')

    L.append('## 5. Robustez frente a escenarios de escala\n')
    L.append('Esta sección aplica el criterio congelado a la ventana primaria. Se evalúa O/k: k < 1 aumenta la observación usada para puntuar. Es un escenario de escala, no una afirmación sobre el sensor ni una estimación de k.\n')
    if dg and dg.get('identificacion_del_eje_k'):
        idt = dg['identificacion_del_eje_k']
        L.append(f'**Qué mide en realidad el eje k, y qué no.** Como el error relativo es |pronóstico − observación/k| dividido por la media de observación/k, el factor sale fuera y la expresión equivale a |k × pronóstico − observación| dividido por la media de la observación. Es decir, dividir la observación por k es *algebraicamente idéntico* a multiplicar los cuatro pronósticos por k: comprobado numéricamente en las cuatro comparaciones y en k ∈ {{0,95; 1,00; 1,05}}, con diferencia máxima {idt["diferencia_maxima"]:.1e}. Este análisis mide, pues, la sensibilidad a un factor multiplicativo común entre pronóstico y observación, y **no distingue un sensor que mide de menos de unos pronósticos que vienen altos** (sin identificar su origen). Ni este cálculo ni las comparaciones con otras referencias citadas en §7 identifican la causa en las 34 estaciones y el periodo evaluado. Esta comprobación es posterior al cálculo (anexo A).\n')
    det = res['sensibilidad_determinista']
    L.append('Determinista (observación de todas las estaciones dividida por k; todo recalculado, incluidas las medias por estación, los intervalos y Holm):\n')
    L.append('| k | H1 efecto | H1 IC95 L=1 | L=7 | L=14 | H1 apoyada (L=7) | H2 efecto | H2 IC95 L=1 | L=7 | L=14 | H2 apoyada (L=7) |\n|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|')
    for kk, v in det['por_k'].items():
        c1, c2 = v['comparaciones']['H1'], v['comparaciones']['H2']
        L.append(f'| {kk.replace(".", ",")} | {f(c1["7"]["efecto"])} % | {ic(c1["1"])} | {ic(c1["7"])} | {ic(c1["14"])} | {"sí" if v["holm"]["7"]["H1"]["apoyada"] else "no"} | {f(c2["7"]["efecto"])} % | {ic(c2["1"])} | {ic(c2["7"])} | {ic(c2["14"])} | {"sí" if v["holm"]["7"]["H2"]["apoyada"] else "no"} |')
    L.append('\nVeredicto determinista: ' + '; '.join(f'{k}: {"ROBUSTO" if v["robusto_al_instrumento"] else "NO robusto"} (signo invariante: {"sí" if v["signo_invariante"] else "no"}; conclusión de los intervalos invariante: {"sí" if v["conclusion_intervalos_invariante"] else "no"})' for k, v in det['veredicto'].items()) + '.\n')
    mc = res['sensibilidad_montecarlo']
    L.append(f'Monte Carlo ({mc["sorteos"]} sorteos de k_i ~ U(0,95; 1,05) independiente por estación, semilla {mc["semilla"]}):\n')
    L.append('| Comparación | Efecto medio | Desv. | P2,5 | Mediana | P97,5 | Fracción con signo positivo | Supervivencia nivel 1 (signo) | Nivel 2 (signo e intervalo) L=1 / L=7 / L=14 |\n|---|---:|---:|---:|---:|---:|---:|---:|---|')
    for k, v in mc['comparaciones'].items():
        s2 = v.get('supervivencia_nivel2_signo_e_intervalo')
        L.append(f'| {k} | {f(v["efecto_media"])} % | {f(v["efecto_desv"])} | {f(v["efecto_p2_5"])} | {f(v["efecto_mediana"])} | {f(v["efecto_p97_5"])} | {f(100 * v["fraccion_signo_positivo"], 1)} % | {f(100 * v["supervivencia_nivel1_signo"], 1) + " %" if "supervivencia_nivel1_signo" in v else "—"} | {(" / ".join(f(100 * s2[Lb], 1) + " %" for Lb in ("1", "7", "14"))) if s2 else "—"} |')
    if dg:
        kk = dg['k_comun_vs_independiente']
        L.append('**El Monte Carlo y el escenario común responden a preguntas distintas.** El sorteo preespecificado asigna factores independientes k_i ~ U(0,95; 1,05) a las 34 estaciones. La media de esos factores se concentra alrededor de 1 (desviación 0,0049, frente a 0,0288 para el factor común del diagnóstico posterior). Eso no convierte el efecto sobre el MAE en una función de la media: intervienen los 34 factores, sus pesos y los errores diarios. La supervivencia del signo es del 100 % en ese Monte Carlo; la supervivencia del signo y del intervalo es la que figura en la tabla. El contraste posterior con un único k aleatorio invierte el signo de H2 en el 25,8 % de los sorteos y el de H1 en el 0,0 %. Son probabilidades condicionadas a leyes de simulación, no probabilidades de error real de la red. El criterio determinista de tres valores de k estaba congelado y sigue siendo el que decide el veredicto.\n')
    L.append('![Sensibilidad de escala](figura_sensibilidad.png)\n')

    L.append('## 6. Secundarias y estratos (exploratorio, sin corrección)\n')
    L.append('### 6.1 Comparaciones secundarias, ventana primaria\n')
    L.append(tabla_comparacion({k: v for k, v in pr['comparaciones'].items() if k in ('S1', 'S2')}) + '\n')
    L.append('### 6.2 Ventana secundaria (versión anterior de los modelos)\n')
    sec = res['secundaria']
    if 'comparaciones' in sec:
        L.append(f'Días objetivo {sec["dias"][0]} a {sec["dias"][1]} ({sec["n_dias_calendario"]} días; inicio ajustado al primer día con las cuatro pasadas archivadas: {sec.get("inicio_ajustado")}). No se mezcla con la primaria.\n')
        L.append(tabla_comparacion(sec['comparaciones']) + '\n')
    else:
        L.append(f'{sec}\n')
    L.append(secundaria())
    L.append('### 6.3 Estratos de la ventana primaria (efecto puntual e IC95 con bloques de 7 días; los tres largos están en resultados.json)\n')
    L.append('| Estrato | N (H1) | H1 efecto | H1 IC95 L7 | H2 efecto | H2 IC95 L7 | S1 efecto | S2 efecto |\n|---|---:|---:|---:|---:|---:|---:|---:|')
    for name, v in pr['estratos'].items():
        if not isinstance(v, dict) or 'H1' not in v:
            continue
        extra = ''
        if 'estaciones' in v:
            extra = f' ({len(v["estaciones"])} estaciones)'
        if 'cortes_pct' in v:
            extra = f' (cortes {f(v["cortes_pct"][0], 1)} / {f(v["cortes_pct"][1], 1)} %, fuente {v["fuente_nubosidad"]})'
        L.append(f'| {name}{extra} | {v["H1"]["n"]} | {f(v["H1"]["por_bloque"]["7"]["efecto"])} % | {ic(v["H1"]["por_bloque"]["7"])} | {f(v["H2"]["por_bloque"]["7"]["efecto"])} % | {ic(v["H2"]["por_bloque"]["7"])} | {f(v["S1"]["por_bloque"]["7"]["efecto"])} % | {f(v["S2"]["por_bloque"]["7"]["efecto"])} % |')
    L.append('\n### 6.4 Por estación (ventana primaria; IC95 con bloques de 7 días)\n')
    L.append('| Estación | N (H1) | Obs. media (Wh/m²) | H1 efecto | H1 IC95 L7 | H2 efecto | H2 IC95 L7 | S1 efecto | S2 efecto |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|')
    for code, v in pr['por_estacion'].items():
        L.append(f'| {code} | {v["H1"]["n"]} | {f(v["obs_media_wh_m2"], 0)} | {f(v["H1"]["por_bloque"]["7"]["efecto"])} % | {ic(v["H1"]["por_bloque"]["7"])} | {f(v["H2"]["por_bloque"]["7"]["efecto"])} % | {ic(v["H2"]["por_bloque"]["7"])} | {f(v["S1"]["por_bloque"]["7"]["efecto"])} % | {f(v["S2"]["por_bloque"]["7"]["efecto"])} % |')
    L.append('\n### 6.5 Restricción a 06-18 UTC con semihorarios ya existentes (enlace con el trabajo anterior)\n')
    en = res.get('enlace_06_18', {})
    if 'comparaciones' in en:
        L.append(f'Estaciones {", ".join(en["estaciones"])}; días {en["calendario"][0]} a {en["calendario"][1]} dentro de la primaria ({en["n_dias"]} días de calendario, con el hueco del 1 al 9 de agosto). Días con observación 06-18 válida: {en["dias_obs_validos"]}. {en["nota"]}.\n')
        L.append('| Comparación | N | Efecto | IC95 L=1 | IC95 L=7 | IC95 L=14 | p L=7 |\n|---|---:|---:|---:|---:|---:|---:|')
        for cname, c in en['comparaciones'].items():
            b = c['por_bloque']
            L.append(f'| {cname} | {c["n"]} | {f(b["7"]["efecto"])} % | {ic(b["1"])} | {ic(b["7"])} | {ic(b["14"])} | {pval(b["7"]["p"])} |')
        L.append('\nPor estación (H1, L=7): ' + '; '.join(f'{code}: {f(v["H1"]["por_bloque"]["7"]["efecto"])} % {ic(v["H1"]["por_bloque"]["7"])} (N={v["H1"]["n"]})' for code, v in en['por_estacion'].items()) + '.\n')
    else:
        L.append(f'No calculado: {en}\n')
    L.append('### 6.6 Contexto: MAE y sesgo por serie (NO son resultado; el encargo prohíbe medir el sesgo absoluto del modelo)\n')
    L.append('La decisión D2 del encargo prohíbe medir el sesgo absoluto del modelo, precisamente porque contra estos sensores no es identificable. Se listan aquí, y se usan en §7 y en el anexo A, con un solo fin: explicar por qué un error de escala común a la red no se cancela en la comparación. No son un resultado ni respaldan ninguna afirmación sobre la calidad de un modelo.\n')
    L.append('| Serie | N | MAE (Wh/m²) | MAE relativo | Sesgo (Wh/m²) | Sesgo relativo |\n|---|---:|---:|---:|---:|---:|')
    for s, v in pr['series_contexto'].items():
        if v:
            L.append(f'| {s} | {v["n"]} | {f(v["mae_wh_m2"], 0)} | {f(v["mae_relativo_pct"])} % | {f(v["sesgo_wh_m2"], 0)} | {f(v["sesgo_relativo_pct"])} % |')

    L.append('\n## 7. Limitaciones\n')
    L.append('- Ventana corta y sin invierno: 110 días de mayo a agosto de 2026 con una sola versión; la ventana secundaria (versión anterior, 40 días de primavera) se reporta aparte y no se mezcla. Nada aquí habla de otoño ni invierno.')
    L.append('- El error del sensor se acepta como dato: no se valida ningún piranómetro (D1). Por eso solo se interpretan comparaciones relativas; MAE y sesgo por serie se listan como contexto y no son resultado.')
    sc = pr['series_contexto']
    L.append('- La comparación de errores absolutos no es, en general, invariante a un factor común aplicado a la observación. La sensibilidad calculada documenta esa dependencia. Los residuos medios de §6.6 mezclan modelo, referencia y representatividad; su signo por sí solo no explica el signo de la diferencia de MAE.')
    if dg:
        d2 = dg['cruce_k_comun']['H2']['discrepancia_equivalente_pct']; d1 = dg['cruce_k_comun']['H1']['discrepancia_equivalente_pct']
        L.append('- Los antecedentes de escala histórica y de contraste entre redes se restituyen íntegramente en §7.1. No se usan para recalibrar k ni para cambiar el criterio congelado.')
    if dg:
        se = dg['sesgo_por_estacion']['IFS_00']
        L.append('- **La distribución del error instrumental no está identificada.** IFS_00 presenta una desviación entre estaciones de sus residuos medios relativos del 6,42 %; AIFS_00, del 6,19 %. Esa dispersión no es una medida del error de los sensores: un residuo compartido también puede proceder de errores comunes de los modelos o de la representatividad punto-celda. No permite aceptar ni rechazar la distribución de k_i del Monte Carlo. Su independencia y centrado son supuestos de sensibilidad.')
    L.append('- **Tratamiento temporal del proveedor.** Se comparan las series horarias servidas por Open-Meteo. Compartir un procedimiento de interpolación dentro de un modelo no garantiza que sus efectos se cancelen entre ciclos en una comparación de MAE: depende de los campos de cada pasada y de la agregación. El archivo conservado no permite verificar la conservación del total diario frente a los campos nativos. No se cuantifica ni se atribuye a ese tratamiento la diferencia observada entre modelos.')
    L.append('- La celda usada es la de 0,25° más próxima (`cell_selection=nearest`), que en costa puede ser marina; es la misma para las dos series de cada comparación, pero la representatividad punto-celda no se corrige.')
    L.append('- La hora de inicialización no es la hora de disponibilidad: este encargo no mide latencia de publicación ni valor económico.')
    L.append('- La red SiAR no cubre la cornisa cantábrica, País Vasco, La Rioja ni Cataluña; el mapa queda sesgado al sur, centro y este. Canarias entra con una sola estación.')
    L.append('- Estratos, secundarias, el enlace 06-18 UTC y el anexo A son exploratorios, sin corrección por multiplicidad; el enlace usa cinco estaciones y un calendario con hueco.')
    L.append('- Bloques de 1, 7 y 14 días con 110 días: la dependencia temporal se aproxima, no se estima; se reportan los tres largos sin elegir.')
    L.append(f'- Cinco pasadas no están en el archivo del proveedor (tabla de la sección 3); ningún ciclo se sustituye por otro y por eso N difiere entre comparaciones.')
    L.append('- Por D4 no se investigan: la calibración de estaciones concretas, la causa de los días inválidos, la diferencia entre productos de referencia, ni la física de los errores.\n')

    L.append(antecedentes())
    L.append('## 8. Reproducción\n')
    L.append(f'- `metodo_fijado.json` SHA-256 `{rec["sha256"]}`; `resultados.json` y `estaciones.json` los generan `code/analizar.py` y `code/preparar_observaciones.py` desde los recibos de `raw/`.')
    L.append('- Esta revisión se entrega en `datos_y_analisis_portable_v1.0.1.zip`, con respuestas y recibos originales, especificación congelada, motor numérico sin cambios, textos y figuras corregidos, manifiesto de integridad y `reproducir_offline.py`. La carpeta `revision/` identifica los cambios y conserva los resultados de la reproducción. El ZIP anterior se conserva intacto.')
    L.append('- Extraer el ZIP en una carpeta nueva y ejecutar `python reproducir_offline.py` desde su raíz (Python 3.12 y NumPy; matplotlib opcional para las figuras). El lanzador verifica el manifiesto y ejecuta en una copia local dentro de `reproduccion/`, con conexión de red bloqueada en el proceso. Compara todos los resultados numéricos y los huecos con los entregados; solo excluye marcas de generación. No escribe sobre los archivos entregados ni fuera de la carpeta extraída. Ver `LEEME.md`.')
    L.append('- Los recibos de `raw/heredado/` son del 13 de septiembre porque son datos de los trabajos previos; el manifiesto que documenta su copia es del 14 a las 14:52 UTC, posterior a la congelación. Se usan solo en la sección 6.5.')
    L.append('- Gasto contratado en datos y servicios durante todo el encargo: 0 €. No se han comprado datos ni usado claves de pago.\n')

    if dg:
        L.append('## Anexo A. Diagnóstico posterior (no preespecificado, no es resultado)\n')
        nrep = f'{dg["replicas_bootstrap"]:,}'.replace(',', '.'); nmed = f'{dg["replicas_mediana"]:,}'.replace(',', '.')
        L.append(f'Calculado el {dg["generado_utc"][:19]} UTC, después de ver los resultados, para interpretar la sensibilidad de escala de la sección 5. No entra en las hipótesis, no se corrige por multiplicidad y no cambia ningún veredicto. Los intervalos usan el mismo bootstrap por días completos, semilla y largos de bloque que el análisis principal ({nrep} réplicas; {nmed} para la mediana).\n')
        L.append('**A.1 El mismo efecto medido de otras maneras** (efecto, IC95 con bloques de 7 días y p bilateral):\n')
        L.append('| Comparación | MAE relativo (oficial) | MAE absoluto | RMSE | Mediana del error absoluto | MAE relativo con el sesgo de cada serie restado por estación |\n|---|---|---|---|---|---|')
        for c in ('H1', 'H2', 'S1', 'S2'):
            m = dg['metricas_alternativas'][c]['7']
            cel = lambda key: f'{f(m[key]["efecto"])} % {ic(m[key])} p={pval(m[key]["p"])}'
            L.append(f'| {c} | {cel("mae_rel")} | {cel("mae_abs")} | {cel("rmse")} | {cel("mediana_abs")} | {cel("sin_sesgo_rel")} |')
        L.append('')
        sd = dg['sesgo_dispersion']
        ma = dg['metricas_alternativas']
        L.append('- **Centrar los residuos elimina un desplazamiento aditivo, no la sensibilidad multiplicativa.** Tras restar el residuo medio de cada serie y estación, H2 queda en 0,63 % [-2,96; 4,18] y H1 en 0,79 % [-0,96; 2,54] para k = 1. Estos intervalos incluyen cero; no prueban igualdad ni ausencia de habilidad. Para un factor k, el residuo centrado es (F − media(F)) − (O − media(O))/k, por lo que aún depende de k. El propio diagnóstico guardado da, para k = 0,95; 1; 1,05, H1 = 0,8545; 0,7912; 0,7582 % y H2 = 0,6988; 0,6308; 0,4570 %. El centrado usa toda la muestra de evaluación: no es una corrección predictiva validada fuera de muestra.')
        L.append(descomposicion(dg))
        L.append(f'- Con la mediana del error absoluto, menos sensible a la magnitud de los extremos, H2 queda en {f(ma["H2"]["7"]["mediana_abs"]["efecto"])} % {ic(ma["H2"]["7"]["mediana_abs"])} y H1 en {f(ma["H1"]["7"]["mediana_abs"]["efecto"])} % {ic(ma["H1"]["7"]["mediana_abs"])}.')
        cr = dg['cruce_k_comun']; kc = dg['k_comun_vs_independiente']
        L.append('')
        L.append('**A.2 El efecto en función de un factor de escala común k** (escenario de observación O/k; no estimación de k):\n')
        L.append('Positivo = la segunda serie es mejor. La columna de cambio de observación traduce el k de cruce a d = 100 × (1/k − 1): aumento o reducción relativos a la observación publicada. No estima el error del sensor. Para k < 1, el supuesto déficit relativo a la verdad sería 100 × (1 − k), que usa otro denominador.\n')
        L.append('| Comparación | k = 0,90 | k = 0,95 | k = 1,00 | k = 1,05 | k = 1,10 | k en que cruza cero | Cambio de la observación que anula el efecto | Sorteos con signo contrario, k común | Ídem, k independiente |\n|---|---:|---:|---:|---:|---:|---:|---|---:|---:|')
        for c in ('H1', 'H2', 'S1', 'S2'):
            cu = cr[c]['curva']; kx = cr[c]['k_cruce']
            sent = '—' if kx is None else (f'{"aumentar" if kx < 1 else "reducir"} {f(abs(cr[c]["discrepancia_equivalente_pct"]), 2)} %')
            L.append(f'| {c} | {f(cu["0.9000"])} % | {f(cu["0.9500"])} % | {f(cu["1.0000"])} % | {f(cu["1.0500"])} % | {f(cu["1.1000"])} % | {f(kx, 4) if kx else "no cruza"} | {sent} | {f(100 * kc[c]["comun"]["fraccion_signo_contrario"], 1)} % | {f(100 * kc[c]["independiente"]["fraccion_signo_contrario"], 1)} % |')
        L.append('')
        lo = dg['loso']; pe = dg['por_estacion_peso_igual']; pm = dg['por_mes']; red = dg['redundancia_espacial']
        for h, num in (('H1', 'A.3'), ('H2', 'A.4')):
            rg = ma[h]['rango_todas_las_metricas_L7']; cru = cr[h]
            meses = ' · '.join(f'{m} {f(v)} %' for m, v in pm[h].items() if not m.startswith('sin_'))
            extra = f' Sin agosto queda en {f(pm[h]["sin_2026-08"])} %.' if h == 'H1' else ''
            L.append(f'- **{num} Estabilidad de {h}.** Según la métrica, el efecto va de {f(rg["min"])} % ({rg["min_metrica"]}) a {f(rg["max"])} % ({rg["max_metrica"]}), sobre las cinco de A.1. Quitando una estación cualquiera, {f(lo[h]["min"])} % a {f(lo[h]["max"])} %; con peso igual por estación, {f(pe[h]["media"])} % y {pe[h]["negativas"]} de {pe[h]["de"]} estaciones negativas. Por meses: {meses}.{extra} Frente al factor de escala común, el efecto {"no cambia de signo dentro de la banda ±5 %" if not cru["cambia_de_signo_en_banda_5pct"] else "cambia de signo dentro de la banda ±5 %"} y su máximo cae en k = {f(cru["k_argmax"], 4)}, con la rejilla de 0,0025 usada aquí.')
        L.append(f'- **A.5 Redundancia espacial.** Los errores diarios brutos de IFS_00 entre estaciones distintas correlacionan {f(red["error_bruto_IFS_00"]["correlacion_media"], 3)} de media, unas {f(red["error_bruto_IFS_00"]["estaciones_efectivas"], 1)} estaciones efectivas de 34. Pero el estadístico que se compara no es el error bruto sino la diferencia de errores absolutos entre las dos series, mucho menos correlacionada: {f(red["H1"]["correlacion_media_diferencia_abs"], 3)} en H1 y {f(red["H2"]["correlacion_media_diferencia_abs"], 3)} en H2, lo que da {f(red["H1"]["estaciones_efectivas"], 1)} y {f(red["H2"]["estaciones_efectivas"], 1)} estaciones efectivas. La cifra se acota en 34: con correlación media nula o negativa la fórmula devuelve más de 34, y eso no significa más información que estaciones hay. El bootstrap por días completos ya respeta la dependencia sinóptica; el número de estaciones no debe leerse como 34 réplicas independientes.')
        L.append('- **A.6 Límites de este anexo.** El centrado resta el residuo medio por estación calculado sobre toda la muestra; los intervalos están condicionados a esos valores y no los vuelven a estimar en cada réplica. No son intervalos de una corrección operativa fuera de muestra. La mediana usa 2.000 réplicas y las demás métricas 10.000. El cruce de k se interpola sobre una rejilla de 0,0025; es un diagnóstico posterior, no una calibración de la referencia. Las cifras de estaciones efectivas de A.5 son aproximaciones descriptivas basadas en correlaciones medias y no tamaños muestrales certificados.\n')

    L.append('*Posible continuación, no ejecutada:* repetir la misma medición cuando el archivo cubra otoño e invierno de la misma versión de modelo.')
    Path(args.out).write_text('\n'.join(x for x in L if x is not None) + '\n', encoding='utf-8')
    print('informe escrito:', args.out, len('\n'.join(L)), 'caracteres')


if __name__ == '__main__':
    main()
