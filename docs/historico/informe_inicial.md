# Primera prueba: disponibilidad de pronósticos y cierres eléctricos

Fecha: 12 de septiembre de 2026. Fase 0: conservación, trazabilidad y viabilidad temporal.

**La primera prueba está completada: se ha conservado el histórico, calculado su relación con los cierres y observado un ciclo en directo. El resultado impide atribuir todavía una ventaja a la IA.** El histórico de Open-Meteo produce diferencias grandes en IDA1, pero el acceso directo a ECMWF cambia la comparación. Tenemos evidencia de diferencias entre canales, todavía ninguna estimación de precisión o rentabilidad.

## Qué se ha conservado

- **744 archivos de metadatos:** 372 de AIFS y 372 de IFS, todos los encontrados por el listado paginado durante esta captura.
- **79.610 entradas de objetos**, con nombre, LastModified, tamaño y ETag. Esta captura no descargó los cuerpos de los campos meteorológicos globales. Una prueba posterior recuperó dos series puntuales de 72 horas, separadas del análisis histórico.
- Descarga de conservación: **32.627.217 bytes**, aproximadamente 31,1 MiB. Cero errores de descarga.
- Captura iniciada a las 09:31:57 UTC y finalizada a las 09:34:34 UTC del 12 de septiembre.
- Cobertura de referencia: AIFS, 10 de junio 00 UTC–12 de septiembre 00 UTC; IFS, 9 de junio 18 UTC–12 de septiembre 00 UTC.
- Faltan cinco ciclos intermedios en AIFS y seis en IFS. Están enumerados en `analysis/results.json`. Su ausencia del archivo **no prueba una caída del proveedor**.

La captura conserva respuestas originales, cabeceras, hora de recuperación y SHA-256. Se han comprobado los 744 hashes. El listado se obtuvo en varias peticiones y no representa una instantánea atómica del servidor.

## Qué significan las fechas

`reference_time` identifica el ciclo de inicialización. El código de Open-Meteo asigna `created_at` al generar el metadato del archivo completo; no es la fecha de publicación original de ECMWF. La versión de código inspeccionada fue `9701689dd81ebef2d478800366c586c8a02c0c19`; no se ha demostrado que esa misma versión estuviera desplegada durante todo el histórico. [Código de generación](https://github.com/open-meteo/open-meteo/blob/9701689dd81ebef2d478800366c586c8a02c0c19/Sources/App/Helper/File/FullRunMetaJson.swift).

Open-Meteo documenta una distribución espacial progresiva y una distribución por ejecuciones posterior, con tres meses de retención pública. Sus canales pueden tener tiempos diferentes. [Documentación del archivo](https://github.com/open-meteo/open-data/blob/main/README.md).

`Last-Modified` es una marca del objeto almacenado; puede cambiar con una sustitución, y una carga multipart tiene particularidades temporales. No acredita por sí sola la primera lectura satisfactoria del contenido. [Metadatos de S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html).

El cálculo principal usa el máximo entre las fechas de modificación de `meta.json` y del objeto `shortwave_radiation.om`. Se compara también con `created_at` y con la fecha de `meta.json` sola. En 216 ejecuciones AIFS y 215 IFS, algún objeto solar tiene una marca posterior a la de su metadato; el máximo evita ignorarlo. **Las tres medidas siguen siendo aproximaciones del proceso de archivo.**

## Cálculo del calendario

Se analizaron **93 días**, del 11 de junio al 11 de septiembre, todos en horario de verano. Los horarios se convirtieron con `Europe/Madrid`, base de zonas horarias 2026.3. Se probaron por separado los días de 23 y 25 horas.

Se seleccionó el ciclo de referencia más reciente cuya marca temporal, más el margen de procesamiento, era **estrictamente anterior** al cierre. El metadato debía declarar las variables requeridas y un rango que cubriera el horizonte de entrega. No se han decodificado los campos ni comprobado la cobertura efectiva de cada variable o punto geográfico.

Para DA, IDA1 e IDA2 el horizonte es el día siguiente; para IDA3, desde las 12:00 hasta el final del día en curso. Se usa el calendario normal de las [reglas de 2025](https://www.boe.es/buscar/doc.php?id=BOE-A-2025-4908), sin reconstruir modificaciones excepcionales de cada sesión. El protocolo local se escribió antes de los cálculos agregados; **no es un prerregistro externo**.

### Retraso del archivo respecto al ciclo de referencia

Estas cifras corresponden a Open-Meteo `data_run`, no a disponibilidad universal del modelo. Las horas se redondean al minuto. P05–P95 son percentiles descriptivos de retraso, no intervalos de confianza.

| Modelo | Ciclo | Ejecuciones | Retraso mediano | Hora UTC mediana del archivo | Retraso P05–P95 |
|---|---|---:|---:|---:|---:|
| AIFS | 00 UTC | 94 | 05:41 | 05:41 UTC | 05:39–05:52 |
| AIFS | 06 UTC | 92 | 05:42 | 11:42 UTC | 05:39–05:45 |
| AIFS | 12 UTC | 93 | 05:42 | 17:42 UTC | 05:39–06:18 |
| AIFS | 18 UTC | 93 | 05:41 | 23:41 UTC | 05:39–05:47 |
| IFS | 00 UTC | 94 | 07:46 | 07:46 UTC | 07:42–07:58 |
| IFS | 06 UTC | 92 | 07:08 | 13:08 UTC | 07:05–07:14 |
| IFS | 12 UTC | 92 | 07:46 | 19:46 UTC | 07:42–08:06 |
| IFS | 18 UTC | 94 | 07:08 | 01:08 UTC (día siguiente) | 07:06–07:17 |

### Ciclo seleccionable en las subastas, sin margen adicional

| Mercado | Cierre Madrid / UTC en verano | Días comparados | Mismo ciclo | AIFS más reciente | IFS más reciente |
|---|---|---:|---:|---:|---:|
| DA | 12:00 / 10:00 | 93 | 92 | 1 | 0 |
| IDA1 | 15:00 / 13:00 | 93 | 2 | 91 | 0 |
| IDA2 | 22:00 / 20:00 | 93 | 86 | 7 | 0 |
| IDA3 | 10:00 / 08:00 | 93 | 90 | 3 | 0 |

**91 de 93 comparaciones de IDA1 eligen un ciclo AIFS más reciente usando el archivo de Open-Meteo. Esto no significa que IFS no existiera antes del cierre por otro canal.** El resultado es igual para los tres indicadores de fecha y para la sensibilidad con viento a 100 m.

Como comprobación posterior adicional, se excluyeron los días sin los ocho ciclos de referencia de los días UTC anterior y actual para ambos modelos. Quedaron **87 días**; en **87** de ellos AIFS fue más reciente en IDA1. El criterio y los días excluidos están guardados; no reemplazan el cálculo principal.

### La discrepancia decisiva: 11 de septiembre, ciclo 06 UTC

| Evidencia | IFS | AIFS |
|---|---|---|
| `created_at` de Open-Meteo | 2026-09-11T13:07:18Z | 2026-09-11T11:37:56Z |
| Last-Modified de `meta.json` | 2026-09-11T13:09:31+00:00 | 2026-09-11T11:38:39+00:00 |
| Cabecera ECMWF, paso +42 h | 12:27:00 UTC | 11:58:00 UTC |
| Cierre IDA1 de ese día | 13:00:00 UTC | 13:00:00 UTC |

Se consultaron las cabeceras de todos los pasos IFS +15 a +42 h cada 3 h y AIFS +12 a +42 h cada 6 h. En IFS, los diez archivos devolvieron Last-Modified 12:27 UTC. Los índices del paso +42 h incluyen radiación solar y las dos componentes de viento a 100 m. Las respuestas originales están en `channel_probes/20260912T094130Z/`.

Según la marca de ECMWF, IFS precede al cierre en 33 minutos; según el metadato archivado en Open-Meteo, lo supera en 9 minutos y 31 segundos. **No hemos presenciado la publicación de ayer:** son dos marcas históricas distintas, no una medida certificada del retraso de transporte. AIFS incluso presenta una marca de archivo anterior a algunas marcas del canal ECMWF inspeccionado; tampoco puede tratarse a esos servidores como una cadena temporal única.

Esta discrepancia obliga a separar: modelo, canal, subconjunto de campos y momento observado de acceso. La diferencia de ciclo en IDA1 no acredita todavía una ventaja intrínseca de AIFS ni una oportunidad comercial.

### Sensibilidad al tiempo necesario para procesar y actuar

Días, de 93, con un ciclo AIFS más reciente según la aproximación principal:

| Margen adicional supuesto | DA | IDA1 | IDA2 | IDA3 |
|---|---:|---:|---:|---:|
| 0 min | 1 | 91 | 7 | 3 |
| 5 min | 1 | 91 | 11 | 8 |
| 15 min | 1 | 91 | 63 | 62 |
| 30 min | 2 | 91 | 91 | 92 |

Los márgenes son escenarios declarados, no tiempos de una instalación real medidos. La sensibilidad de IDA2 e IDA3 confirma que no conviene escoger un margen después de ver el resultado.

## Cambio de 24 a 96 rondas: simulación de calendario

La reforma está prevista para el 22 de septiembre, con entrega el 23; **aún no ha ocurrido en esta muestra**. Se aplicaron ambos calendarios a las mismas fechas históricas: cierre por grupo horario y cierre individual a T−60 minutos. Se estudiaron 8.928 periodos de quince minutos por modelo. [Instrucción OMIE](https://www.omie.es/sites/default/files/2026-08/instruccion-4-2026-puesta-en-funcionamiento-de-la-negociacion-del-mercado-intradiario-continuo-en-96-rondas.pdf), [reglas de 2026](https://www.boe.es/buscar/doc.php?id=BOE-A-2026-17570).

| Modelo | Margen supuesto | Periodos con un ciclo adicional bajo 96 rondas | Porcentaje |
|---|---|---:|---:|
| AIFS | 0 min | 366 / 8928 | 4.10% |
| AIFS | 5 min | 155 / 8928 | 1.74% |
| AIFS | 15 min | 83 / 8928 | 0.93% |
| AIFS | 30 min | 1048 / 8928 | 11.74% |
| IFS | 0 min | 618 / 8928 | 6.92% |
| IFS | 5 min | 549 / 8928 | 6.15% |
| IFS | 15 min | 715 / 8928 | 8.01% |
| IFS | 30 min | 592 / 8928 | 6.63% |

El primer cuarto de cada hora no cambia en esta comparación; los otros tres ganan 15, 30 y 45 minutos. Estos porcentajes describen acceso adicional bajo una simulación del calendario. **No miden una mejora de precisión, ingresos o impacto causal de la reforma.** El tiempo ganado puede ser nocturno o carecer de utilidad económica; no se ha valorado.

## Validación realizada y límites

- Siete pruebas temporales superadas: invierno/verano, días de 92/100 periodos, exclusión de información futura, cierre estricto, margen de procesamiento, horizonte insuficiente y variable ausente; también se comprueba la preferencia por ciclo de referencia frente a orden de descarga.
- 744 comprobaciones de integridad del contenido descargado y control de claves repetidas en las listas.
- Seis combinaciones de variable/fecha y cuatro márgenes para subastas; ocho escenarios de calendario continuo.
- Sin estimación de euros, datos de una planta, señales de compra o venta ni valoración de rentabilidad. No se ha utilizado ningún precio futuro para decidir.
- Ausencias, revisiones de archivos, cobertura parcial y excepciones de calendario siguen limitando la reconstrucción histórica. La muestra no incluye invierno.

El artículo de Kuppelwieser y Wozabal estudia estrategias intradiarias con pronósticos de renovables, libro de órdenes, costes de liquidez y productos horarios y cuarto-horarios. Es un antecedente cercano; cambiar de país o añadir quince minutos no demuestra novedad. Nuestro resultado actual es una auditoría de disponibilidad, todavía sin validar una contribución económica nueva. [OR Spectrum](https://link.springer.com/article/10.1007/s00291-022-00698-5).

## Captura prospectiva completada: 12 de septiembre, ciclo 06 UTC

El observador funcionó de **09:45:12 a 13:10:54 UTC**, consultando aproximadamente cada 60 segundos. Detectó sus **22 objetivos y terminó automáticamente**. Registró 3.117 peticiones: 2.788 respuestas 404 esperadas y 329 respuestas 200; de estas últimas, 307 todavía correspondían a un ciclo anterior y 22 cumplieron el criterio. No hubo otros errores. Todos los objetivos tuvieron una ausencia anterior registrada.

| Canal y objetos observados | Inicio más temprano de la última consulta negativa, UTC | Fin más tardío de la primera respuesta positiva, UTC |
|---|---|---|
| ECMWF AIFS, 6 pasos | 11:33:25 | 11:34:29 |
| Open-Meteo AIFS, 3 objetivos | 11:38:37 | 11:39:40 |
| ECMWF IFS, 10 pasos | 12:26:16 | 12:27:19 |
| Open-Meteo IFS, 3 objetivos | 13:09:52 | 13:10:54 |

Para ECMWF se observaron cabeceras HEAD de los pasos IFS +15 a +42 y AIFS +12 a +42. Para Open-Meteo se comprobaron el metadato de la ejecución, la cabecera del archivo solar y el metadato de actualización. Las filas agregan varios objetos; los intervalos de cada objeto están guardados. Son intervalos de respuesta observada desde este equipo, no certificados de primera publicación mundial.

Las cabeceras IFS de ECMWF respondieron antes de IDA1 (13:00 UTC); los objetivos de Open-Meteo IFS, después. **La diferencia entre canales vuelve a aparecer en una observación prospectiva**, aunque una cabecera satisfactoria no demuestra que el campo completo ya pudiera leerse y decodificarse.

Hay otra limitación concreta: las seis cabeceras AIFS respondieron aproximadamente a las 11:34:29, pero declararon Last-Modified entre las 11:49 y las 11:58. Es una inconsistencia entre la hora observada y la marca declarada, cuya causa no está resuelta. El reloj usado es el UTC del equipo; una cabecera Date de S3 concordó aproximadamente al segundo, pero no se hizo una calibración NTP independiente. **No se ha corregido artificialmente ninguna fecha ni inferido disponibilidad del contenido a partir de esa inconsistencia.**

El registro terminado está en la carpeta `captura_ciclo_20260912_06`, junto a este informe, y también en `live_capture/` dentro del ZIP. Se conserva separado de los 93 días históricos. No queda ningún observador de esta prueba ejecutándose ni hay una tarea recurrente instalada.

## Acceso a valores meteorológicos: viable, evaluación pendiente

Se recuperó una serie de radiación de **72 horas para cada modelo**, del ciclo 06 UTC del 11 de septiembre, solicitando un punto de Madrid. Ambos devuelven la celda 40,5° N, 3,75° O y radiación en W/m². IFS tiene dos valores iniciales ausentes y AIFS cuatro: se conservan como tales, sin rellenarlos con cero ni desplazar las fechas. La aparente desalineación detectada en una lectura preliminar provenía de omitir esos nulos al resumir; no se detectó un fallo del proveedor en esta comprobación. Los máximos del primer día ocurren a las 13:00 UTC en ambas muestras. La API documenta esta variable como media de la hora anterior. [Single Runs API](https://open-meteo.com/en/docs/single-runs-api).

También se obtuvieron **48 observaciones de media hora**, del 10 de septiembre, de la estación pública SiAR M01, Center: Finca experimental. Es la primera estación madrileña listada, elegida solo para verificar acceso sin cuenta. La muestra no está emparejada con los pronósticos anteriores: tiene otra fecha y ubicación. [Consulta pública SiAR](https://servicio.mapa.gob.es/siarweb/consultaDatos/inicio).

Antes de puntuar existe un problema real que resolver: la documentación oficial dice que los datos horarios se muestran en UTC desde abril de 2014, mientras el JSON del gráfico añade `+02:00` a la hora mostrada. Se han conservado ambas representaciones. No se elegirá la que produzca mejores errores ni se convertirá automáticamente la etiqueta a UTC. Hay que contrastar el reloj, el final del intervalo y las coordenadas con otra exportación documentada o una fuente independiente. [Definición de los datos SiAR](https://www.mapa.gob.es/es/desarrollo-rural/temas/gestion-sostenible-regadios/Datos%20Publicados_tcm30-82981.pdf).

Estos ejemplos acreditan acceso al contenido en el momento de consulta; no su disponibilidad pasada. Las respuestas y recibos están en `value_access/`, con los campos de sesión de la web omitidos.

## Decisión sobre el proyecto

**Seguir con un piloto pequeño; todavía no comprometer cinco meses ni gastar el presupuesto.** La afirmación fuerte —AIFS llega a IDA1 e IFS no— no se sostiene de forma general cuando se cambia de canal. Esto reduce el atractivo de esa supuesta ventaja, aunque deja abierta la pregunta sobre el valor de un dato realmente utilizable antes del cierre.

El siguiente experimento deberá cumplir, en este orden:

1. Confirmar una lectura y decodificación de radiación por canal, ciclo y horizonte. Registrar fin de descarga y fin de decodificación, no solo HEAD o Last-Modified.
2. Resolver el reloj de las observaciones y emparejar pronósticos y estaciones con idénticos intervalos físicos. Congelar selección de estaciones, fechas y tratamiento de huecos antes de ver errores.
3. Separar precisión a igual ciclo de la selección del último ciclo disponible en cada cierre. Simular retrasos manteniendo constantes modelo y contenido para aislar el efecto del tiempo.
4. Solo después traducir las diferencias a una decisión energética definida, con producción representativa, costes y precios que correspondan a esa decisión. Una estación meteorológica no proporciona por sí sola los desvíos de una planta.

Si la ventaja desaparece al usar un canal accesible más rápido, se descartará esa tesis de ventaja de IA para IDA1. Si no se puede verificar el reloj o la lectura efectiva, se detendrá la puntuación económica. Un resultado negativo puede ser informativo, pero su publicación o monetización no está garantizada.

Gasto contratado en datos o servicios durante esta fase: **0 €**. No se han comprado datos ni usado claves de pago.
