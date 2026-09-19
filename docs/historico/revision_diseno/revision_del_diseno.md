# Revisión del diseño y de la crítica

**La crítica justifica ampliar y rediseñar el estudio. Mi recomendación de decidir sobre esta vía con otra prueba pequeña y un plazo de dos semanas fue prematura: faltaba dimensionar la muestra para un efecto útil.** La validación ya terminada sigue siendo una prueba de una corrección concreta. Sus resultados no descartan MOS, EMOS ni la calibración local en general.

He releído el informe completo, revisado fuentes oficiales, calculado una sensibilidad del tamaño muestral y comprobado otra vía de acceso al histórico. No se han calculado correlaciones con aerosoles ni nuevos resultados de calibración.

## Corrección exacta que se probó

Para cada estación y cada una de las cuatro series —IFS/AIFS, ciclos 00/06 del día anterior— se calculó una sola constante: la media de `pronóstico − observación` sobre 28 bloques diurnos de seis horas, procedentes de 14 días completos de junio. Se restó la misma constante a los bloques 06–12 y 12–18 UTC de todo julio, con mínimo cero. Los otros bloques no cambiaron. No hubo pendiente, ajuste por hora, aerosoles, nubosidad, estación del año ni actualización móvil.

En la comparación principal AIFS 00, las constantes equivalían a 40,13 W/m² en La Mojonera y 30,66 W/m² en A Capela. Se evaluó la MAE de las medias de bloques de seis horas. La mediana se incluyó como sensibilidad y produjo pequeñas mejoras de AIFS en La Mojonera; no se eligió después como ganadora.

Esto es una referencia sencilla de transferencia temporal. Su fracaso en una estación no era inevitable ni demuestra que allí no se pueda corregir. Tampoco confirma una explicación física particular. En A Capela hubo una señal positiva detectable; por tanto, tampoco es exacto decir que una prueba así «solo puede salir nula». La limitación es el alcance de la inferencia y la baja precisión para efectos más pequeños, además de la incertidumbre de los parámetros.

## Lo que faltaba: magnitud de la incertidumbre

Con los errores firmados diarios del entrenamiento, la desviación típica fue 32,15 W/m² en La Mojonera y 91,26 W/m² en A Capela. Dividir entre √14 da errores estándar de 8,59 y 24,39 W/m², respectivamente, **si los días fueran independientes e idénticamente distribuidos**. La dependencia temporal y la deriva invalidan esa simplificación. Los 28 bloques tampoco equivalen a 28 días independientes.

Los intervalos publicados de julio condicionaban a las constantes ya entrenadas: no incluían esta incertidumbre del entrenamiento. Para estudiar un procedimiento que vuelve a entrenarse hay que repetir ese ajuste dentro de una evaluación cronológica y de la estimación de incertidumbre.

Como orientación de escala, tomé la dispersión de las diferencias diarias de MAE de julio y calculé el tamaño aproximado para efectos futuros prefijados, con potencia del 80% y contraste bilateral al 5%:

| Mejora que se quiere detectar | La Mojonera | A Capela |
|---|---:|---:|
| 5 W/m² | 240 días independientes | 135 días independientes |
| 10 W/m² | 60 días independientes | 34 días independientes |

Son escenarios ilustrativos, no la potencia observada del ensayo ni una garantía de muestra suficiente para un nuevo MOS. Usan aproximación normal, variabilidad de un solo mes y parámetros fijos; no incluyen reajuste, estacionalidad, multiplicidad ni dependencia espacial. Con una autocorrelación AR(1) supuesta de 0,3, las cifras del escenario de 5 W/m² subirían aproximadamente a 446 y 249 días. Los 5 W/m² no son un umbral económico demostrado. La [formulación del NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc222.htm) explica los supuestos del cálculo.

Para una correlación de magnitud 0,3, una aproximación mediante la transformación de Fisher pide unos 85 pares independientes al 80% de potencia y 5% bilateral; para 0,2, unos 194; para 0,5, unos 30. La muestra de junio–julio podría revelar una asociación grande, pero un resultado no significativo no permitiría declarar que «la calima muere». Estos cálculos de correlación también presuponen independencia y aproximación normal, no control de nubes ni ajuste de un modelo predictivo.

## Sí existe una vía práctica hacia casi 19 meses

El archivo Single Runs utilizado antes identifica cada ejecución por su inicialización y anuncia AIFS desde el 2 de abril de 2026. El histórico continuo anuncia AIFS desde febrero de 2025, pero concatena previsiones. La API Previous Runs ofrece series por anticipación fija, aptas para estudiar postprocesado con una definición distinta del objetivo. [Single Runs](https://open-meteo.com/en/docs/single-runs-api), [histórico continuo](https://open-meteo.com/en/docs/historical-forecast-api), [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api).

He descargado realmente `shortwave_radiation_previous_day1` de AIFS en ambas estaciones, del **25 de febrero de 2025 al 12 de septiembre de 2026: 565 días, 13.560 valores horarios no nulos por estación**. Esto confirma cobertura de respuesta, no exactitud meteorológica ni correspondencia con observaciones. No se han calculado nuevos errores. El producto no es la misma ejecución 00 UTC para todas las horas del día y no debe presentarse como una réplica ampliada de aquella comparación. Habrá que verificar su semántica en el tramo compartido con Single Runs y definir expresamente el horizonte del nuevo estudio.

El catálogo SiAR que conservamos contiene **635 identificadores: 520 activos y 115 dados de baja**. Eso concuerda con la descripción oficial de una red de [más de 500 estaciones](https://servicio.mapa.gob.es/siarweb/). No acredita todavía 520 series completas de radiación. Se necesita inventario de fechas, instrumentos/ubicaciones y calidad; varias estaciones pueden compartir celda de pronóstico o episodios meteorológicos, por lo que no son 520 réplicas independientes.

Además, AIFS cambió de versión durante ese historial: v1.1 se implantó el 27 de agosto de 2025 y v2 el 12 de mayo de 2026. El cambio de sesgo puede proceder del modelo y no de la estación. El análisis debe separar o modelar esas versiones. [Historial oficial de AIFS](https://confluence.ecmwf.int/spaces/UDOC/pages/599165907/AIFS%2BVersion%2BHistory).

## Aerosoles: hipótesis razonable, atribución pendiente

IFS meteorológico emplea climatologías de aerosoles en la mayoría de sus configuraciones; CAMS utiliza aerosoles pronosticados. Hay antecedentes documentados de episodios de polvo que afectan a radiación y temperatura y que la climatología no representa. Eso respalda investigar la hipótesis. No demuestra que los errores de La Mojonera de junio y julio procedan principalmente del polvo. [Documentación de radiación de ECMWF](https://confluence.ecmwf.int/display/ECRAD/Aerosol-radiation+interactions+in+the+IFS), [estudio de episodios de 2021](https://www.ecmwf.int/en/newsletter/168/news/saharan-dust-events-spring-2021).

Tampoco hemos probado que el sesgo de A Capela sea niebla marina estructural. Nubes, rejilla, relieve, sensor y otras condiciones pueden contribuir. Que un modelo aprendido no resuelva explícitamente química no significa que carezca de toda información indirecta sobre los efectos de aerosoles.

Con el signo `pronóstico − observación`, la hipótesis de polvo no representado apunta, a igualdad de nubosidad y geometría, a más sobrepredicción cuando aumenta la carga de polvo respecto al fondo representado. Por tanto no se deduce la regla «corregir cuando el AOD es bajo». El tamaño y signo de la corrección deben estimarse; el AOD total tampoco equivale exclusivamente a polvo sahariano.

Una correlación puede ser un diagnóstico útil. Para demostrar utilidad predictiva hace falta comprobar si el AOD **pronosticado con anterioridad** añade mejora frente a referencias que ya usan nubes y época del año, en datos posteriores. Usar análisis o reanálisis del propio día sería adecuado para otras preguntas, pero no demostraría anticipación. Una correlación nula tampoco descarta mecanismos no lineales, errores del predictor o falta de variación/potencia.

La idea de combinar pronóstico de nubes y aerosoles para corregir radiación ya existe: un [artículo de 2017](https://journals.ametsoc.org/view/journals/apme/56/6/jamc-d-16-0297.1.xml) estudió radiación directa normal en ocho ubicaciones españolas, y [Bakker et al. (2019)](https://arxiv.org/abs/1904.07192) compararon postprocesado de radiación global con información de CAMS. Son antecedentes; no prueban ni refutan la novedad de una evaluación específica AIFS–SiAR. No hay base para afirmar aún que «nadie publica ese mapa».

MOS es una familia de relaciones estadísticas entre pronóstico y observación. EMOS es una familia de postprocesado probabilístico. Una constante ya puede entenderse como una referencia estadística con intercepto; el cambio útil sería introducir predictores, regularización y un entrenamiento adecuado, no solamente cambiar el nombre del método.

## CAMS: solicitud preparada, análisis sin ejecutar

El [catálogo oficial](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts?tab=overview) ofrece AOD total y de polvo a 550 nm, ejecuciones 00/12 UTC y archivo desde 2015. He comprobado los nombres de variables, formato y plazos contra el formulario público actual. `solicitud_cams.json` pide un pequeño recorte alrededor de La Mojonera: ejecuciones 00 UTC del 15 de junio al 30 de julio de 2026, pasos +30 a +42, correspondientes a 06–18 UTC del día siguiente.

No se ha enviado una extracción ni descargado AOD. El [acceso oficial por API](https://ads.atmosphere.copernicus.eu/how-to-api) requiere cuenta/token y aceptación manual de las condiciones. No hay archivos de configuración estándar `.cdsapirc` o `.adsapirc` en este equipo. No se han leído ni buscado secretos. El formulario advierte además que las fechas de más de 30 días están en acceso lento; no puede prometerse que la extracción de junio–julio finalice en una tarde.

El muestreo de AOD es instantáneo; la propuesta promedia 06–18 con pesos trapezoidales. No se integra como la energía solar. La comprobación del formulario no equivale a validar todas las restricciones del servidor; ese paso y la descarga están pendientes del acceso. No existe todavía resultado de correlación.

## Cómo cambia la siguiente fase

1. **Ampliar el inventario de datos.** Utilizar la vía de anticipación fija comprobada, contrastarla con ejecuciones identificadas en el solapamiento, y comprobar cobertura/calidad de SiAR en el periodo largo. Elegir estaciones por cobertura y geografía antes de estudiar sus mejoras. Separar versiones de AIFS.
2. **Estudiar estabilidad usando sólo el pasado disponible en cada fecha.** Ventanas móviles, estaciones del año y datos de estaciones ajenas al ajuste. La autocorrelación aislada no clasifica «corregibilidad»: un error de media constante más ruido independiente tiene autocorrelación cero y aun así puede beneficiarse de corregir esa media; una serie con tendencia puede tener autocorrelación alta y una constante poco transferible.
3. **Contrastar predictores físicos.** Empezar por AOD de polvo, AOD total como sensibilidad y nubosidad pronosticada, con una referencia sin aerosoles. La consulta de junio–julio sirve como diagnóstico exploratorio, no como test final de una regla elegida después de observar esos errores.
4. **Dimensionar y evaluar el procedimiento completo.** Fijar el efecto que justifica continuar, simular con dependencia temporal/espacial y volver a entrenar en cada partición. Reservar periodos y estaciones para la evaluación final. Incorporar referencias de corrección constante y móvil antes de métodos más complejos.

La estabilidad sería un predictor candidato de utilidad, no una etiqueta validada por sí sola. Un resultado fuera de muestra deberá mostrar si realmente anticipa mejoras de la corrección. Con los datos largos ya accesibles, retiro el planteamiento de otra pequeña prueba como criterio suficiente para abandonar o comprometer cinco meses. El criterio siguiente debe depender de la pregunta, precisión y cobertura, no de un plazo arbitrario.

## Entregables y comprobaciones

`sensibilidad_tamano_muestral.json` contiene fórmulas, supuestos y números. `cobertura_565_dias.json` resume las respuestas descargadas. `solicitud_cams.json` y `estado_cams.json` distinguen lo preparado de lo ejecutado. El paquete de comprobaciones contiene las respuestas originales de cobertura y del formulario de CAMS, sin credenciales, con código y huellas. No sustituye al paquete reproducible del ensayo anterior, que permanece intacto.

Revisión del 13 de septiembre de 2026. Gasto contratado en datos: 0 €.
