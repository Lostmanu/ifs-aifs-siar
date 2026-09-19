# Auditoría de la referencia: estaciones vecinas y otra red

14 de septiembre de 2026 · 565 días solicitados · Siete estaciones SiAR y dos de MeteoGalicia · Coste de datos: 0 €

**La diferencia con el satélite no es exclusiva de La Mojonera ni de A Capela. En Galicia, además, cambia de forma apreciable entre las estaciones SiAR y dos estaciones cercanas de MeteoGalicia.** Esto aporta una razón concreta para comprobar el sesgo de AIFS con otra referencia antes de desarrollar una corrección. No certifica que SiAR mida mal ni que el satélite mida bien.

El contraste está ejecutado con observaciones nuevas, no solo con disponibilidad del archivo de pronósticos. No se ha entrenado ningún corrector ni atribuido una causa física a los errores.

## Muestra y comparación

Se solicitaron datos del **25 de febrero de 2025 al 12 de septiembre de 2026**, 565 días de calendario. Para cada estación original se seleccionaron, por distancia y antes de calcular diferencias, hasta tres estaciones SiAR activas dentro de 75 km. El catálogo no garantiza que una estación marcada como activa tenga datos recientes: Cajamar–PITA lo demuestra.

Para A Capela se añadieron las dos estaciones más próximas de MeteoGalicia que ofrecían irradiación diaria en una consulta de disponibilidad: Aldea Nova y CIS Ferrol. O Val, la tercera más próxima, no ofreció esa variable en dicha consulta. Es una muestra dirigida, no representativa de toda España ni suficiente para estimar un «efecto de red» general.

| Estación | Red | Distancia al punto original | Altitud | Días con radiación diaria utilizable / 565 |
|---|---|---:|---:|---:|
| La Mojonera | SiAR | 0 km | 137 m | 561 |
| Adra | SiAR | 26,1 km | 2 m | 565 |
| Almería | SiAR | 27,5 km | 5 m | 564 |
| Cajamar–PITA | SiAR | 34,3 km | 111 m | 373 |
| A Capela | SiAR | 0 km | 374 m | 564 |
| Boimorto | SiAR | 46,5 km | 412 m | 563 |
| Castro de Rei | SiAR | 56,4 km | 400 m | 565 |
| Aldea Nova | MeteoGalicia | 14,2 km | 278 m | 564 |
| CIS Ferrol | MeteoGalicia | 16,7 km | 37 m | 564 |

Coordenadas y altitudes proceden del catálogo y las fichas oficiales de SiAR y del listado de MeteoGalicia. Se conserva la selección, incluidas estaciones con datos insuficientes. [Consulta SiAR](https://servicio.mapa.gob.es/siarweb/consultaDatos/inicio), [listado de MeteoGalicia](https://servizos.meteogalicia.gal/mgrss/observacion/listaEstacionsMeteo.action), [metadatos extraídos](C:/Users/manue/Documents/Codex/2026-09-11/qu/outputs/latencia_pronosticos/auditoria_referencia/station_metadata.json).

La comparación histórica usa **energía diaria de 00 a 24 UTC**, en kWh/m²/día. Para SiAR se convierten los totales publicados en MJ/m² dividiendo por 3,6. Para MeteoGalicia se usa `IRD_SUM_1.5m`, expresado en unidades de 10 kJ/m²/día, dividiendo por 360. Solo se aceptan sus registros con código 1, dato válido original; cada estación tenía un registro con código 9, no registrado. [Definiciones del servicio de MeteoGalicia](https://www.meteogalicia.gal/datosred/infoweb/meteo/docs/rss/JSON_EstacionsDiarios_es.pdf).

El satélite procede de los productos LSA SAF MSG y SARAH-3 servidos por Open-Meteo. Sus medias horarias representan la hora precedente: se suman las marcas 01 UTC a 00 UTC del día siguiente y se divide por 1.000. Por eso la descarga llega hasta el 13 de septiembre. Se requieren las 24 horas completas, sin completar huecos ni interpolar. [Definición del servicio de radiación](https://open-meteo.com/en/docs/satellite-radiation-api).

**Los porcentajes siguientes son `100 × suma(satélite − medida) / suma(medida)` en fechas comunes. No son MAE, precisión de sensor ni los errores de los bloques de seis horas del ensayo anterior.**

## La Mojonera: hay un componente compartido en la zona

SARAH-3 permite comparar La Mojonera, Adra y Almería en 545 fechas comunes:

| Estación | Diferencia diaria media | Diferencia respecto a la energía medida |
|---|---:|---:|
| La Mojonera | +0,270 kWh/m²/día | +4,85 % |
| Adra | +0,148 kWh/m²/día | +2,63 % |
| Almería | +0,164 kWh/m²/día | +2,87 % |

La Mojonera presenta una diferencia algo mayor, pero las tres tienen el mismo signo promedio. Comparando cada pareja en sus mismas fechas, el exceso de discrepancia de La Mojonera es +0,122 kWh/m²/día frente a Adra y +0,106 frente a Almería. Los intervalos exploratorios del 95 %, con remuestreo en bloques de 30 días, son [0,053; 0,186] y [0,031; 0,184], respectivamente. No convierten esa diferencia local en una estimación de error instrumental.

El cambio entre años tampoco es exclusivo de La Mojonera. En el tramo **16 de junio–31 de julio**, usando 42 fechas comunes dentro de cada año:

| SARAH-3 menos medida | 2025 | 2026 |
|---|---:|---:|
| La Mojonera | +3,29 % | +7,50 % |
| Adra | +3,20 % | +6,57 % |
| Almería | +2,07 % | +5,36 % |

Las tres diferencias aumentan. Esto debilita una explicación basada únicamente en un problema aislado del sensor de La Mojonera. Es compatible con condiciones regionales, con errores del producto satelital y con errores de medida compartidos. No distingue aerosoles de nubes ni certifica una deriva instrumental. Cada año tiene sus propias fechas disponibles; no es un experimento causal entre años.

LSA SAF añade un matiz importante: frente a Almería, en 521 fechas comunes, La Mojonera tiene una discrepancia **0,059 kWh/m²/día menor**, con intervalo [−0,147; +0,029]. La magnitud y hasta el signo de la diferencia local dependen del producto. No sería defendible asignar un factor de recalibración al sensor usando solo SARAH-3.

## Galicia: el contraste con otra red cambia la lectura

Las cinco estaciones de comparación tienen **546 fechas comunes** con SARAH-3:

| Estación | Red | SARAH-3 menos medida, kWh/m²/día | Diferencia relativa |
|---|---|---:|---:|
| A Capela | SiAR | +0,279 | +6,95 % |
| Boimorto | SiAR | +0,354 | +8,62 % |
| Castro de Rei | SiAR | +0,609 | +15,75 % |
| Aldea Nova | MeteoGalicia | +0,059 | +1,38 % |
| CIS Ferrol | MeteoGalicia | −0,088 | −1,96 % |

Las tres estaciones SiAR quedan por debajo de SARAH-3 en promedio. Las dos estaciones de MeteoGalicia coinciden más en el promedio de esta ventana. A Capela no es la estación con mayor discrepancia: Castro de Rei merece una revisión específica.

El patrón relativo también aparece con LSA SAF. En sus **495 fechas comunes**, las diferencias son +11,21 %, +13,70 % y +20,52 % para las tres estaciones SiAR; +7,22 % y +4,78 % para Aldea Nova y CIS Ferrol. Es decir, la separación entre los grupos se mantiene, aunque LSA SAF eleva el nivel general de las discrepancias. Los dos productos comparten observaciones satelitales; no son dos instrumentos independientes.

En parejas con fechas comunes y descontando la diferencia satelital de cada emplazamiento, A Capela tiene un residuo SARAH-3–medida superior al de Aldea Nova en **0,219 kWh/m²/día**, intervalo [0,127; 0,320], y al de CIS Ferrol en **0,365**, intervalo [0,236; 0,498]. Hay 548 pares por comparación. Los intervalos se obtienen con 5.000 remuestreos en bloques de 30 días sobre el calendario completo, conservando huecos; describen esta ventana, no una calibración.

**Esto es una señal para investigar la referencia, no una demostración de sesgo de SiAR.** A Capela está a 374 m, Aldea Nova a 278 m y CIS Ferrol a 37 m. La distancia, el relieve y la exposición a nubes pueden producir diferencias reales que el píxel satelital no resuelva. Tampoco se han obtenido certificados ni modelos de sensor de las estaciones MeteoGalicia. Su código de dato válido no sustituye esa trazabilidad.

![Comparación entre estaciones y redes](C:/Users/manue/Documents/Codex/2026-09-11/qu/outputs/latencia_pronosticos/auditoria_referencia/comparacion_redes.png)

## La estacionalidad impide convertir una buena media en «verdad»

La serie mensual muestra que SARAH-3 también supera apreciablemente a las dos estaciones de MeteoGalicia durante parte del invierno. En enero y febrero de 2026 las diferencias mensuales se sitúan aproximadamente entre +8 % y +14 %. Por tanto, sus promedios próximos a cero durante toda la ventana incluyen compensaciones entre épocas del año.

La diferencia de A Capela tampoco es constante: en el tramo 16 de junio–31 de julio pasa de +11,74 % en 2025 a +7,38 % en 2026 frente a SARAH-3. No se justifica deducir una deriva uniforme a partir de los dos veranos o de la última fecha publicada de calibración.

![Evolución mensual](C:/Users/manue/Documents/Codex/2026-09-11/qu/outputs/latencia_pronosticos/auditoria_referencia/evolucion_mensual.png)

Las curvas mensuales emplean fechas disponibles por estación y solo muestran meses con al menos 15 días completos. Las tablas principales, en cambio, exigen las mismas fechas dentro de cada comparación. Los archivos entregados permiten ver ambos criterios.

## Lo que sí dicen las fichas de los sensores

Las fichas públicas consultadas identifican un **SKYE Instruments SP1110** en las seis estaciones SiAR con instrumentación informada:

| Estación | Última calibración publicada |
|---|---|
| La Mojonera | 21/10/2025 |
| Adra | 10/09/2025 |
| Almería | 05/09/2025 |
| A Capela | 01/10/2024 |
| Boimorto | 02/10/2024 |
| Castro de Rei | 02/10/2024 |

Cajamar–PITA no informa esos campos. Las fichas se recuperaron mediante el formulario público; se conservan peticiones, respuestas y recibos. La fecha es un campo de la estación: **no es el certificado individual del piranómetro**, ni demuestra qué número de serie estuvo instalado durante toda la ventana. Una ficha sin actualizar puede omitir trabajos posteriores.

La documentación SiAR de julio de 2025 describe el SP1110 como fotocélula de silicio con sensibilidad de 350–1.100 nm e indica una precisión de ±5 %. Ese dato es una especificación publicada, no un intervalo de confianza de nuestras mediciones ni una justificación para restar un 5 %. [Ficha técnica de sensores](https://servicio.mapa.gob.es/siarweb/documentos/masInfo/Piran%C3%B3metro-sensor-radiacion-global.pdf).

El procedimiento SiAR de mantenimiento de 2025 contempla limpieza, nivelación, comparación con patrones y sustitución de sensores por otros calibrados. La frecuencia de calibración remite al fabricante. La comprobación del piranómetro usa referencias de termopila y condiciones de luz natural. El documento diferencia estos procesos internos de una certificación por entidad acreditadora, aunque los patrones sí se calibran periódicamente por entidades acreditadas. No se ha comprobado la ejecución de esas tareas en cada estación. [Procedimiento de mantenimiento](https://servicio.mapa.gob.es/siarweb/documentos/masInfo/Mantenimiento-de-las-estaciones.pdf).

Compartir modelo de sensor y procedimientos importa: **un error de medida puede ser coherente entre estaciones**. Por ello, «estructura geográfica = error del modelo» y «ruido entre vecinas = error del sensor» no constituyen una separación válida por sí solos. También sigue siendo posible un error regional del satélite. Estas hipótesis necesitan controles adicionales.

## Cobertura, controles y límites

- Se descargaron siete series diarias SiAR de 565 filas y las dos series diarias de MeteoGalicia. En total hay 5.085 filas de calendario, incluidas las ausencias. No se encontraron totales diarios aceptados iguales a cero.
- Cajamar–PITA tiene datos utilizables del 14/04/2025 al 21/04/2026; no permite el cruce de junio–julio de 2026. Su etiqueta «activa» no se usó para inventar continuidad ni sustituir sus huecos.
- LSA SAF, en la celda más próxima solicitada para Adra, no ofrece ningún día con 24 horas completas. Tampoco permite ventanas completas 06–18 en el periodo focal. Se publica esa ausencia; no se trasladó el punto ni se rellenaron horas para obtener un resultado.
- Las seis estaciones SiAR con datos de media hora permiten reconstruir los 46 días focales. Las 276 integrales diarias cumplen la tolerancia heredada de 0,05 MJ/m² frente al total publicado y no presentan las anomalías nocturnas definidas. Esto comprueba coherencia interna, no exactitud metrológica. El histórico completo de 565 días no se ha reconstruido entero desde medias horas.
- Para enlazar con el ensayo anterior se repite el cruce 06–18 UTC y se mantiene su exclusión del 23 de junio en las comparaciones focales. Las observaciones y series satelitales de los dos puntos originales coinciden con el cruce anterior dentro del redondeo numérico.
- La verificación separada reconstruye conversiones y sumas con aritmética decimal, comprueba los campos de las fichas contra el HTML visible y valida los hashes de las respuestas. El detalle está en `independent_verification.json`. El número de comprobaciones no mide la fuerza de una hipótesis física.
- La selección espacial, la referencia de satélite y los periodos están documentados. Los intervalos y la interpretación siguen siendo exploratorios. No se ha demostrado un efecto causal de aerosoles, un fallo instrumental, una corrección disponible el día anterior ni una oportunidad comercial.

## Decisión de investigación

La ampliación justifica mantener abierta la investigación, pero cambia el experimento prioritario. **El siguiente contraste debe comprobar si el sesgo de AIFS y el beneficio de corregirlo sobreviven al cambio de referencia**, usando las estaciones de MeteoGalicia con datos de calidad original, además de SiAR. Hay observaciones suficientes para hacerlo; ya no depende de conseguir una cuenta para descargar estos datos.

Ese ensayo debería usar pronósticos con emisión y antelación identificadas, separar ajuste y evaluación temporal, y comparar el modelo sin corregir con una referencia estadística sencilla. Antes de atribuir una mejora a AOD, debe existir una mejora verificable con datos disponibles en el momento de emitir el pronóstico. No conviene esperar a cerrar toda la física para probar esa utilidad, ni presentar una mejora contra una sola referencia como corrección física del modelo.

En paralelo quedan dos comprobaciones acotadas: obtener trazabilidad de números de serie, cambios y calibración para las estaciones señaladas; y revisar Castro de Rei, cuya discrepancia destaca frente a ambos productos. No se ha enviado ninguna consulta a terceros.

Los datos, las dos figuras y los programas están incluidos en el paquete reproducible. Los informes y archivos anteriores permanecen intactos.
