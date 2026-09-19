# Cómo seguimos: una semana de prueba antes de ampliar

13 de septiembre de 2026.

**La siguiente meta es medir si disponer de un ciclo más reciente mejora la predicción de radiación, separando ese efecto de la calidad del modelo y del canal de distribución.** Se limita el piloto a siete días de trabajo y datos gratuitos. No exige esperar siete días nuevos: utilizaremos un mes histórico. Es una prueba para decidir si ampliar la investigación; no valida todavía una contribución excepcional.

## Diseño ya fijado

- Una estación inicial: M01, Center: Finca experimental. Sirve para probar el método; no representa a toda España. Sus coordenadas actuales deben verificarse antes de puntuar.
- Treinta días de evaluación: **10 de agosto–8 de septiembre de 2026**. Quedan fuera las fechas de septiembre que ya hemos inspeccionado para depurar el acceso.
- Cuatro pronósticos para cada fecha: **IFS 00, IFS 06, AIFS 00 y AIFS 06 UTC**, inicializados el día anterior.
- Mismos intervalos y observaciones para todos: radiación integrada en bloques de seis horas. Las series horarias interpoladas no se contarán como pronósticos nativos independientes.
- Comparación principal: IFS 00 frente a IFS 06, para medir el cambio al disponer de un ciclo más reciente dentro del mismo modelo. Después se informa AIFS 00 frente a 06 y la comparación entre modelos a igual ciclo.
- Métricas: error absoluto de energía por superficie, sesgo, diferencias por día y datos ausentes. Son magnitudes meteorológicas; todavía no son euros ni producción de una planta.

El protocolo detallado está en `protocolo.json`. Se registró localmente antes de descargar la muestra de evaluación; no es un prerregistro público. La selección de fechas es de viabilidad y no demuestra representatividad estacional. Se mantienen las dos mitades cronológicas de quince días y se informa también la dependencia temporal.

## Qué he avanzado hoy

**Lectura directa conseguida.** Descargué cuatro mensajes completos de radiación desde ECMWF —dos pasos para cada modelo— y los decodifiqué. Se verificaron variable, inicialización, horizonte, unidad y celda. Los campos descargados ocuparon 5,12 MB. Esto acredita que podemos leer el contenido ahora; no permite afirmar retrospectivamente que ya fuera utilizable antes de IDA1.

**Regla horaria respaldada por documentación y comprobación física.** El manual SiAR de septiembre de 2025, páginas 21 y 24, especifica UTC para las horas mostradas desde abril de 2014. El documento de formato de registro, página 2, indica que la hora corresponde al final del intervalo de promediado. Por ello se conserva la hora mostrada como UTC y se interpreta cada lectura como la media de los treinta minutos anteriores. [Manual SiAR](https://servicio.mapa.gob.es/siarweb/documentos/manuales/ManualUsoWebSiAR.pdf), [Formato de registro](https://servicio.mapa.gob.es/siarweb/documentos/masInfo/Formato-de-Registro.pdf).

En la muestra diagnóstica del 10 de septiembre, convertir literalmente el `+02:00` del gráfico sitúa una lectura de 59,53 W/m² con el Sol aproximadamente 9,9 grados por debajo del horizonte. La interpretación documentada no produce esa contradicción. Es una comprobación física independiente de los errores de los modelos, con la aproximación de posición solar de [NOAA](https://gml.noaa.gov/grad/solcalc/solareqns.PDF). Un día no acredita que todas las estaciones tengan bien el reloj.

**Detectada una segunda discrepancia de presentación.** La fila final aparece como «10/09/2026 24:00» en un campo del gráfico y como «11/09/2026, 24:00» en la tabla. Los 48 valores de radiación coinciden. Se conserva la discrepancia y se normaliza la medianoche una sola vez; las 47 filas restantes coinciden también en la fecha y hora mostradas. Debe comprobarse este caso al ampliar la muestra.

**Unidades contrastadas.** Los mensajes originales contienen energía acumulada en J/m². Para obtener radiación media de seis horas se resta la acumulación inicial de la final y se divide por 21.600 segundos. La API publica radiación media en W/m². En la misma celda, inicialización e intervalo 06–12 UTC del 12 de septiembre:

| Modelo | Media del campo original | Media de seis horas de la API | Diferencia relativa entre canales |
|---|---:|---:|---:|
| IFS | 495,36 W/m² | 496,50 W/m² | +0,23 % |
| AIFS | 484,53 W/m² | 487,83 W/m² | +0,68 % |

Estas diferencias corresponden a una sola comprobación de transformación de datos. No son errores frente a la realidad ni resultados de precisión. Su causa exacta no se ha atribuido; habrá que repetir el contraste en varios intervalos y cuantificar el procesamiento antes de extraer conclusiones pequeñas. La [documentación de la API](https://open-meteo.com/en/docs/single-runs-api) define la radiación horaria como media de la hora anterior.

## Trabajo restante y decisión

| Etapa | Trabajo | Condición para pasar |
|---|---|---|
| Preparación, días 1–2 | Confirmar coordenadas actuales, verificar integral diaria frente al dato diario publicado y revisar horas, huecos y unidades en el mes completo. | Comparaciones con los mismos intervalos físicos y calidad suficiente. |
| Comparación, días 3–5 | Descargar los cuatro pronósticos por fecha y calcular las diferencias emparejadas. Separar precisión a igual ciclo de beneficio por ciclo nuevo. | Resultados reproducibles, todas las exclusiones visibles y ninguna selección del periodo favorable. |
| Decisión, días 6–7 | Contrastar la magnitud y estabilidad del efecto; revisar si la ventaja depende solo de usar un canal lento. | Seguir, replicar una sola vez si es inconcluso, o descartar esta tesis. |

Las etapas son un límite de esfuerzo propuesto, no una tarea programada ni una promesa de trabajo en segundo plano. Los datos de evaluación de treinta días todavía no se han descargado ni puntuado en esta entrega.

**Seguimos hacia una réplica** si hay una mejora estable, los datos pasan los controles y queda una diferencia operativa que no se explica simplemente accediendo al mismo pronóstico por un canal más rápido. La réplica deberá usar estaciones elegidas antes de ver sus errores.

**Descartamos esta tesis o detenemos su evaluación** si persisten problemas de reloj/unidades, si el nuevo ciclo no aporta una mejora útil en la muestra o si la supuesta ventaja se debe íntegramente al canal elegido. Un resultado mixto se informa como inconcluso; no se cambia repetidamente la pregunta hasta obtener un ganador.

Solo tras esa réplica tendría sentido diseñar la valoración económica: una decisión y producción representativas, el calendario de entrega español exacto, costes y precios adecuados. Las observaciones de una estación no son los desvíos de una planta y el error meteorológico no equivale automáticamente a ahorro.

Gasto contratado acumulado: **0 €**. No se ha instalado ni iniciado un observador recurrente. El paquete de evidencia de hoy se entrega separado del histórico conservado ayer.
