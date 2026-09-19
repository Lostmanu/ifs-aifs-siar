# Revisión de la crítica: encuadre correcto, conclusión sobre calibración todavía no demostrada

13 de septiembre de 2026. Auditoría posterior a la crítica con los mismos datos. Sin nuevas descargas meteorológicas, sin alterar exclusiones ni los informes originales.

**La crítica principal es válida: el experimento 00 → 06 no estima el efecto de la latencia.** Es una comparación de actualizaciones con menor horizonte y nueva información meteorológica. Debí mantener ese resultado en su papel de diagnóstico y exigir antes la prueba de disponibilidad en una decisión concreta. Un 8 % de mejora meteorológica no responde cuánto vale recibir antes un dato idéntico.

**La conclusión de que el sesgo es mayoritariamente corregible y constituye ya un hallazgo publicable no está justificada.** Para comprobarla he realizado una calibración temporal sencilla. Mejora AIFS en A Capela, pero empeora los cuatro pronósticos en La Mojonera. El resultado no permite afirmar que calibrar siempre supere a actualizar ni que hayamos descubierto un defecto general de AIFS en Galicia.

## 1. Latencia, ciclos y cierre de mercado

El ciclo 06 usa otra inicialización y tiene seis horas menos de horizonte para el mismo instante válido. La comparación no mantiene constante el contenido. Que su error mejore en esta muestra es un dato válido de actualización, pero no una identificación causal de latencia; tampoco se puede afirmar sin un referente cuantitativo que exactamente el 8,5 % fuera lo esperado.

La crítica cambia además de decisor: compara con el cierre del mercado diario de las 12:00, mientras la oportunidad de disponibilidad que veníamos auditando era principalmente **IDA1, a las 15:00 de Madrid**. En verano esto corresponde a 13:00 UTC. Una disponibilidad a las 12:27 UTC sería anterior a IDA1 y posterior al mercado diario. No es correcto concluir que el ciclo sea imposible para todo decisor del proyecto. Debe identificarse la sesión. [Reglas de mercado consultadas](https://www.boe.es/buscar/doc.php?id=BOE-A-2025-4908).

Pero hay un límite más fundamental: las 12:27 del registro previo correspondían a respuestas y metadatos del canal para los objetos observados; no probaban que el ciclo completo hubiera sido descargado y decodificado a esa hora, ni fijan un horario garantizado cada día del año. Esa prueba de usabilidad antes del cierre sigue pendiente.

`created_at` tampoco resuelve por sí solo el problema. En el código de Open-Meteo conservado, se asigna al construir el metadato, antes de la publicación remota. `LastModified` describe el objeto; no acredita que este equipo hubiera podido descargar y decodificar todos los campos necesarios antes del cierre. Se conservan como aproximaciones, no como un certificado de primera disponibilidad. [Código de Open-Meteo inspeccionado](https://raw.githubusercontent.com/open-meteo/open-meteo/9701689dd81ebef2d478800366c586c8a02c0c19/Sources/App/Helper/File/FullRunMetaJson.swift), [metadatos S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html).

## 2. La noche: el matiz es correcto, pero no vuelve falsa la métrica original

He sustituido los porcentajes solares teóricos de la crítica por las observaciones efectivamente usadas, manteniendo excluido el 17 de agosto en La Mojonera:

| Franja UTC | Energía observada, La Mojonera | Energía observada, A Capela |
|---|---:|---:|
| 00–06 | 0,091 % | 0,034 % |
| 06–12 | 46,713 % | 39,424 % |
| 12–18 | 52,670 % | 58,731 % |
| 18–24 | 0,526 % | 1,812 % |

La mayor parte de la información solar está en 06–18 UTC, como señala la crítica. Sin embargo, los otros bloques no son todos ceros exactos, y la franja 18–24 de A Capela supera el 1,5 % en las observaciones. Las reducciones relativas tampoco tienen por qué conservarse exactamente al retirar esas franjas.

| IFS 00 | MAE original, día completo | MAE en 06–18 UTC |
|---|---:|---:|
| La Mojonera | 19,55 W/m² equivalentes | 38,33 W/m² equivalentes |
| A Capela | 42,23 W/m² equivalentes | 82,61 W/m² equivalentes |

La métrica original se definió sobre los cuatro bloques del día y es aritméticamente correcta. La segunda responde a otra ventana temporal. Deben presentarse juntas para evitar que un lector interprete el promedio diario como error exclusivamente diurno. **No hay un factor dos universal de error al calcular euros:** la evaluación económica necesita energía y liquidación por intervalo, no convertir un MAE agregado en beneficios. Tampoco 06–18 UTC equivale exactamente a luz solar astronómica.

## 3. Sesgo/MAE no es la fracción de error que se puede eliminar

El sesgo es la media del error firmado y el MAE la media de su valor absoluto. Su cociente indica cuánto predomina un signo, pero no descompone el MAE en una parte sistemática y otra aleatoria. Incluso si todos los errores son positivos y el cociente es 100 %, pueden tener magnitudes distintas que una constante no elimina.

Restar el error medio anula el sesgo **en los datos utilizados para ajustarlo**, antes de restricciones como truncar en cero, y minimiza el error cuadrático entre correcciones aditivas constantes. Para minimizar error absoluto la referencia es la mediana. Ninguna de las dos garantiza mejorar datos posteriores. La estimación bajo normalidad que propone la crítica no sustituye esta evaluación, especialmente con una mezcla de noche y distintas condiciones de nubosidad.

### Comprobación realizada

Se fijó el método antes de calcular estos nuevos resultados, pero después de ver la crítica y los resultados anteriores. Por tanto, es una comprobación **exploratoria posterior**. La segunda mitad ya había sido inspeccionada en el piloto; no es una validación nueva y ciega.

- Ajuste: 10–24 de agosto; 14 días válidos en La Mojonera y 15 en A Capela.
- Evaluación: 25 de agosto–8 de septiembre; 15 días en ambas.
- Un único ajuste constante por modelo y ciclo: media de los residuos de los bloques 06–12 y 12–18 del periodo de ajuste, en energía por bloque.
- Se resta esa constante en los dos bloques correspondientes del periodo de evaluación, con suelo cero; el resto no cambia.
- Sensibilidad secundaria fijada simultáneamente: mediana en lugar de media. No se elige el método que más favorece cada resultado.

**Reducción del MAE en la segunda mitad: positivo mejora, negativo empeora.** Todas las comparaciones usan los mismos días, intervalos y exclusiones.

| Estación | Pronóstico calibrado | Ajuste con media | Ajuste con mediana |
|---|---|---:|---:|
| La Mojonera | IFS 00 | −24,79 % | −12,59 % |
| La Mojonera | IFS 06 | −12,25 % | −5,73 % |
| La Mojonera | AIFS 00 | −6,03 % | −5,79 % |
| La Mojonera | AIFS 06 | −4,27 % | −1,33 % |
| A Capela | IFS 00 | +9,52 % | +8,69 % |
| A Capela | IFS 06 | +8,27 % | +7,57 % |
| A Capela | AIFS 00 | +19,16 % | +9,64 % |
| A Capela | AIFS 06 | +17,78 % | +9,97 % |

Para comparar con actualizar el ciclo sobre ese mismo periodo: IFS 00 → 06 sin calibrar mejora **5,56 % en La Mojonera** y **10,35 % en A Capela**; AIFS mejora **−0,74 % y +3,19 %**, respectivamente. La calibración media supera a la actualización en el caso AIFS de A Capela, pero no en todos los casos. Esto se refiere a error meteorológico, no a valor económico ni a latencia.

Es una prueba concreta de dos métodos muy simples, no un veredicto sobre todas las calibraciones posibles. El fracaso de una constante no impide que un modelo condicionado por hora solar, nubosidad u otras variables funcione; desarrollar ese modelo requeriría separar ajuste, selección y evaluación en datos nuevos.

### El «13 % de AIFS en Galicia»

La normalización de la crítica usa una radiación diurna teórica que no coincide con la observada. En 06–18 UTC, A Capela tiene una media observada de **361,72 W/m²**. AIFS 00 presenta sesgo de **+65,08 W/m²**, equivalente al **17,99 %** de esa media; AIFS 06, **+16,64 %**. IFS 00, **+13,15 %**. Estos valores describen esta estación, mes, ventana y procesamiento del proveedor.

Un porcentaje mayor no fortalece por sí mismo una atribución causal. Puede intervenir representatividad de la celda, costa, orografía, medición o procesamiento, además del modelo. No se puede convertir esta comparación en «AIFS sobreestima Galicia de forma sistemática un 13 %». Se necesita confirmar en otras estaciones, periodos y referencias observacionales.

## 4. Agosto y dependencia temporal

La réplica es espacial dentro del mismo mes; no es una réplica temporal independiente. Esa limitación y el remuestreo conjunto por día ya estaban declarados y deben mantenerse.

No sabemos si la mejora de actualizar sería mayor en invierno. Un régimen más difícil puede elevar errores de ambos ciclos sin aumentar su diferencia. No hay base en esta muestra para afirmar que el 8,5 % esté sesgado a la baja. Tampoco se puede tratar toda España, incluida Galicia, como si tuviera el mismo régimen meteorológico de agosto.

Con 30 días, los bloques de siete días ofrecen poca información sobre la dependencia. Se deben mantener como sensibilidad previamente declarada, junto a los otros resultados y su fragilidad. Retirarlos ahora por su aspecto favorable o desfavorable no reforzaría la prueba. En un estudio futuro conviene fijar un tratamiento de incertidumbre acorde a una muestra más larga antes de analizarla.

## 5. El 17 de agosto: inspección de la hipótesis de duplicación

Hay **48 registros, 48 marcas horarias distintas y exactamente los 48 finales de media hora esperados**. No aparecen valores diurnos consecutivos exactamente iguales ni secuencias diurnas adyacentes idénticas de dos a seis registros. No hay evidencia de dos filas añadidas o de una duplicación consecutiva exacta en el fichero consultado.

El exceso sigue siendo 3,12804 MJ/m². Dividirlo por la duración de dos medias horas da 868,9 W/m², como sugiere la crítica. La compatibilidad de esa cifra con radiación alta no identifica el mecanismo: muchas discrepancias pueden producir una cantidad de ese orden. No se descartan valores sobrescritos, procesos aguas arriba o un total diario erróneo. El día sigue excluido.

Un punto de la crítica merece conservarse: **la integral diaria no valida todo el reloj**. Un desplazamiento dentro del día puede preservar exactamente la suma. Los controles astronómicos detectan errores gruesos, pero no garantizan que no existan desplazamientos pequeños. La comprobación de reloj necesita evidencia independiente si aparecen indicios de ese problema.

## 6. Publicabilidad y siguiente decisión

La calibración de radiación no es una línea inédita: existen trabajos sobre postprocesado de pronósticos solares y ECMWF ha descrito sesgos de radiación y corrección estadística. Eso no descarta una contribución nueva sobre AIFS y estaciones españolas, pero **la originalidad de nuestra afirmación no está establecida**. [Comparación de postprocesados solares, Solar Energy 2019](https://arxiv.org/abs/1904.07192), [ECMWF sobre sesgos cerca de superficie](https://www.ecmwf.int/en/newsletter/157/meteorology/addressing-biases-near-surface-forecasts).

Sí considero que evaluar calibración local es una pregunta más directamente comprobable con la infraestructura disponible. La hipótesis honesta sería: **¿cuándo mejora una calibración local sencilla a cada pronóstico sin calibrar, y cuándo falla al cambiar las condiciones?** No sería «demostraremos que el sesgo es corregible».

No construiría todavía un marcador público con conclusiones sobre ganadores. Primero fijaría modelos de referencia y calibraciones simples, métricas de día completo y periodo diurno, una separación temporal nueva y comprobaciones independientes de sensores. La prueba exploratoria actual serviría para diseñarlo, no como su resultado confirmatorio. Un registrador de disponibilidad puede ser un conjunto de datos complementario, pero aquí no se ha iniciado una captura de seis meses ni una automatización.

La revisión cambia el encuadre y añade evidencia real sin reemplazar un entusiasmo por otro. Tenemos una señal local de calibración útil en A Capela y una señal de fracaso de calibración constante en La Mojonera. **Esa heterogeneidad es lo comprobado; la ventaja general y la publicación excepcional siguen por demostrar.**
