"""Contexto restituido en v1.0.1. Solo formatea datos y diagnósticos identificados."""
from comun import DATOS, load

def f(x,n=2): return f'{x:,.{n}f}'.replace(',','X').replace('.',',').replace('X','.')
def ci(x,n=2): return '['+f(x[0],n)+'; '+f(x[1],n)+']'

def secundaria():
    x=load(DATOS/'sensibilidad_secundaria_posterior.json')
    lines=['### 6.2 bis. Escala en la ventana secundaria: extensión posterior al resultado', '',
      '**La ventana estaba preespecificada; este cálculo adicional de escala es posterior, solicitado al corregir el cierre.** Se reutilizan sus fechas y pares, sin modificar resultados.json ni el veredicto primario. Los IC de esta tabla son exploratorios, sin Holm; usan 10.000 réplicas y los mismos bloques y semilla que el método original.', '',
      '| Ventana y versiones | Contraste | N | Efecto con k=0,95 | IC95 L=7 | Cruce de k, posterior |',
      '|---|---|---:|---:|---:|---:|']
    for w,label in [('primaria','Primaria, 110 días, versiones nuevas'),('secundaria','Secundaria, 40 días, versiones anteriores')]:
        for h,v in x['ventanas'][w]['comparaciones'].items():
            p=v['por_k']['0.95']['7']
            lines.append(f'| {label} | {h} | {v["n_pares"]} | {f(p["efecto"])} % | {ci(p["ic95"])} | {f(v["cruces"][0],3) if v["cruces"] else "sin cruce en la rejilla"} |')
    lines+=['',
      'En la secundaria los puntos de H1 y H2 permanecen positivos en los tres escenarios k=0,95; 1; 1,05. H1 sigue teniendo un intervalo que incluye cero con k=0,95. Por tanto, conservar el signo no equivale a demostrar robustez inferencial de ambas comparaciones.',
      'La inversión de H2 con k=0,95 se observa en la ventana primaria y no en la secundaria. Cambian simultáneamente periodo del año, duración y versiones de los modelos; no se puede atribuir esa diferencia solo al verano o solo a la versión. El veredicto congelado sobre la primaria se conserva.',
      'Los cruces se interpolan en una rejilla 0,80–1,10 de paso 0,0025, ampliada después de recibir la objeción para comprobar los valores alegados. Son descripciones posteriores, no valores estimados del error instrumental. Datos y controles: `datos/sensibilidad_secundaria_posterior.json`.', '']
    return '\n'.join(lines)

def antecedentes():
    c=load(DATOS/'contexto_referencia_cierre.json')
    sec=load(DATOS/'sensibilidad_secundaria_posterior.json')
    lines=['### 7.1 Antecedentes recuperados: escala histórica y contraste entre redes', '',
      '[Urraca et al. (2019)](https://doi.org/10.3390/s19112483) citan una comparación previa de fotodiodos SiAR con patrones secundarios AEMET a menos de 20 km: aproximadamente ±15 % de incertidumbre diaria y ±5 % anual, después de excluir defectos y fotodiodos dudosos. También describen, desde 2010, una desviación negativa de alrededor del **−1 % para la mayoría de los fotodiodos estudiados**. Es un contrapeso histórico relevante: k=0,95 es el borde inferior de la banda fijada, no su centro. Esos datos no estiman el k de estas 34 estaciones en 2026 ni convierten la banda anual en una distribución uniforme de errores para esta muestra.', '',
      f'Como escenario descriptivo adicional, k=0,99 da efectos puntuales primarios de H1 {f(sec["ventanas"]["primaria"]["comparaciones"]["H1"]["efecto_k_0_99"])} % y H2 {f(sec["ventanas"]["primaria"]["comparaciones"]["H2"]["efecto_k_0_99"])} %. No se adopta k=0,99 como calibración ni como mejor estimación actual.', '',
      'La auditoría previa de referencias solicitó 25-feb-2025–12-sep-2026. En **546 fechas comunes** de Galicia encontró las siguientes diferencias SARAH-3 menos medida, expresadas como 100 × suma(SARAH-3 − medida)/suma(medida):', '',
      '| Estación | Red | Diferencia relativa |','|---|---|---:|']
    names={'C01':('A Capela','SiAR'),'C02':('Boimorto','SiAR'),'LU01':('Castro de Rei','SiAR'),
           'MG10141':('Aldea Nova','MeteoGalicia'),'MG10050':('CIS Ferrol','MeteoGalicia')}
    for code,(name,network) in names.items():
        lines.append(f'| {name} | {network} | {f(c["galicia_546"]["stations"][code]["relative_bias_percent"])} % |')
    lines+=['','Los contrastes emparejados de residuos `(SARAH-3 − medida)_A Capela − (SARAH-3 − medida)_vecina` también se conservan:', '',
       '| Pareja | Fechas comunes | Diferencia, kWh/m²/día | IC95 exploratorio |','|---|---:|---:|---:|']
    for p in c['pares']:
        lines.append(f'| A Capela − {names[p["neighbor"]][0]} | {p["n"]} | {f(p["mean_residual_difference_kwh_m2"],3)} | {ci(p["bootstrap_30days"]["ci95"],3)} |')
    lines+=['',
       'Son 5.000 remuestreos en bloques de 30 días, conservando huecos. Los pares tienen 548 fechas cada uno; no deben confundirse con las 546 fechas comunes de las cinco estaciones. Aldea Nova y CIS Ferrol están a 14,2 y 16,7 km de A Capela; sus altitudes son 278 y 37 m, frente a 374 m de A Capela.',
       'La diferencia entre redes cuestiona una explicación basada únicamente en un desplazamiento uniforme del satélite. Aporta información sobre la referencia, pero no separa por sí sola sensor, error local del satélite, relieve, nubes y representatividad. No es un ensayo con instrumentos colocados juntos. Los promedios próximos a cero de MeteoGalicia incluyen compensaciones estacionales; en enero y febrero de 2026 las diferencias mensuales frente al satélite rondaban +8 % a +14 %.',
       'Solo AL10 y LU01 de aquella auditoría coinciden con la muestra actual. El contraste entre redes es un antecedente; **la evaluación de pronósticos frente a MeteoGalicia pertenece al encargo separado `evaluacion_meteogalicia`, que quedó incompleto. Nunca fue un contraste previsto dentro del encargo de 34 estaciones.**',
       'Se restituyen antecedentes ya existentes, sin nueva descarga ni recalibración. Fuentes completas y hashes en `datos/contexto_referencia_cierre.json` y `revision/antecedentes_referencia/`.', '']
    return '\n'.join(lines)

def descomposicion(dg):
    s=dg['sesgo_dispersion']
    lines=['', '**A.1 bis. Descomposición descriptiva del error cuadrático, restituida**', '',
       'Para cada serie y sus pares válidos se usa MSE = media(residuo)² + varianza(residuo), con media y varianza **globales**, agrupando estaciones y días (ddof=0). No es una descomposición aditiva del MAE ni la misma operación que centrar por estación en A.1. Unidades: (Wh/m²)².', '',
       '| Serie | MSE | Media global del residuo² | Varianza global del residuo |','|---|---:|---:|---:|']
    for name,v in s.items(): lines.append(f'| {name} | {f(v["mse"],0)} | {f(v["mse_parte_sesgo"],0)} | {f(v["mse_parte_varianza"],0)} |')
    db=100*(1-s['AIFS_00']['mse_parte_sesgo']/s['IFS_00']['mse_parte_sesgo'])
    dv=100*(1-s['AIFS_00']['mse_parte_varianza']/s['IFS_00']['mse_parte_varianza'])
    lines+=['',f'En IFS_00→AIFS_00, sobre los mismos 3.697 pares, la componente de media global al cuadrado baja un {f(db,1)} % y la varianza global un {f(dv,1)} %. Son cifras del diagnóstico posterior original, ahora visibles de nuevo y verificadas contra el panel. No identifican qué parte corresponde al sensor o al modelo.',
       'El centrado por estación es invariante a desplazamientos aditivos constantes en cada estación. Los efectos centrados de H1 y H2, 0,79 % y 0,63 % con k=1, tienen intervalos que incluyen cero. Esa falta de significación no prueba equivalencia, no crea un componente causalmente identificable y no garantiza la misma inferencia para todo k. Los puntos centrados varían poco entre los tres k examinados, pero sí varían; los intervalos publicados son los de k=1.', '']
    return '\n'.join(lines)
