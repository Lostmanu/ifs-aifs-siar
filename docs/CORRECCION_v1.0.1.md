# Corrección del cierre — v1.0.1

Corrección solicitada por el usuario. El proyecto permanece cerrado; no hay nuevas descargas, estaciones, ajuste predictivo ni hipótesis primarias. Se conserva v1.0.0 y se entrega una versión corregida del informe y su paquete.

## Cambios aceptados y comprobados

1. **Contexto histórico restituido.** Se incorpora la desviación cercana al −1 % que Urraca et al. describen para la mayoría de los fotodiodos históricos desde 2010. No estima la escala común de esta muestra de 2026. k=0,95 es el borde de la banda de sensibilidad, no su centro ni un escenario cuya probabilidad se haya estimado. Fuente: [Urraca et al. (2019)](https://doi.org/10.3390/s19112483), texto completo conservado con recibo y hash.
2. **MeteoGalicia vuelve al contexto.** Se restituyen los cinco promedios en 546 fechas y los dos contrastes de residuos con A Capela, cada uno con 548 fechas e intervalos exploratorios que excluyen cero. Es información que cuestiona una explicación satelital uniforme, pero no identifica por sí sola error instrumental: difieren ubicación, altitud, nubes y representatividad.
3. **Ventana secundaria visible.** Se verifican los puntos de +2,36 % (H1) y +5,33 % (H2) con k=0,95, y los cruces aproximados 0,821 y 0,897. La ventana estaba fijada; esta extensión de escala, sus intervalos y la rejilla ampliada son posteriores al resultado. No cambian el veredicto primario.
4. **Terminología coherente.** La sección 5 pasa a «Robustez frente a escenarios de escala». Se declara expresamente que es un cambio de vocabulario posterior respecto a «robusto al instrumento», conservando fórmula, escenarios, regla y clave JSON originales.
5. **Descomposición del MSE restituida.** Se vuelve a mostrar la media global del residuo al cuadrado y la varianza global. Son las cifras originales, verificadas contra el panel. No se confunden con el centrado por estación ni con una descomposición del MAE.
6. **Alcance corregido.** El ensayo de pronósticos frente a MeteoGalicia era el encargo separado `evaluacion_meteogalicia`. Su ausencia no es un incumplimiento del estudio de 34 estaciones. Aquel paquete quedó incompleto y se conserva como antecedente independiente.

## Lo que permite decir la secundaria

| Ventana | H1 con k=0,95 | IC95 L=7 | H2 con k=0,95 | IC95 L=7 |
|---|---:|---:|---:|---:|
| Primaria: 110 días, versiones nuevas | +0,44 % | [−0,58; 1,39] | −5,64 % | [−10,08; −1,33] |
| Secundaria: 40 días, versiones anteriores | +2,36 % | [−0,87; 4,89] | +5,33 % | [0,73; 9,06] |

Los intervalos de la extensión secundaria son exploratorios y no llevan Holm. H1 conserva el signo, pero su intervalo incluye cero. La diferencia entre ventanas mezcla estación del año, duración y versión de modelos; no se identifica una causa estacional. Las dos ventanas mantienen sus propios pares y no se combinan.

## Límites que se mantienen

El −1 % histórico no es «la mejor estimación actual de k» para estas estaciones. Los contrastes entre redes tampoco certifican su calibración. El centrado por estación elimina desplazamientos aditivos constantes, pero no vuelve el error identificable ni independiente de k; un intervalo que incluye cero no demuestra equivalencia. Los intervalos del centrado original están condicionados a medias estimadas dentro de la muestra.

El hallazgo transferible se conserva explícitamente: en esta métrica normalizada, dividir la observación por k equivale a multiplicar los pronósticos por k. El eje de sensibilidad no separa sensor y pronóstico. La comparación sigue condicionada a la referencia y al producto horario servido.

## Conservación y reproducción

Los archivos `resultados.json`, `panel_analisis.json`, `estaciones.json`, las observaciones, el diagnóstico original y la especificación congelada no cambian. Los motores originales `metodo.py`, `analizar.py`, `preparar_observaciones.py` y `diagnostico_posterior.py` tampoco. La extensión escribe `datos/sensibilidad_secundaria_posterior.json`; el contexto procede de los archivos originales de la auditoría de referencia. Su procedencia y punteros se guardan en `datos/contexto_referencia_cierre.json`.

El lanzador incorpora la extensión posterior y compara siete archivos JSON, excluyendo cuatro marcas de generación. La reproducción histórica de 60.602 valores y sus tres exclusiones corresponde a v1.0.0 y sigue intacta. La verificación de v1.0.1 informa su recuento adicional por separado.

La cadena portable probada usa el lanzador y los archivos locales. El audit hook controla conexiones, procesos externos y aperturas de archivos para escritura; no intercepta todo borrado o renombrado ni aísla el sistema operativo. Los scripts auxiliares de selección y empaquetado conservan algunas rutas heredadas y no forman parte de esa cadena. En Windows conviene extraer en una ruta corta: el informe recibido menciona un límite aproximado de 141 caracteres para su configuración, no una garantía universal de portabilidad.

El texto recibido se conserva íntegro, pero su declaración de «auditoría independiente completa» no se convierte en una certificación de esta entrega. Las comprobaciones realizadas aquí tienen sus propios registros. Las limitaciones anteriores se documentan sin ampliar el experimento.
