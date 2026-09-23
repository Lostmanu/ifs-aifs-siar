# Una comparación que también examina su referencia

[Portada](../README.md) · [Reproducción](REPRODUCIR.md) · [Informe completo](../estudio/outputs/informe.md)

Una estación terrestre permite comprobar un pronóstico, pero su medición también tiene incertidumbre. Este estudio pregunta cuánto mejora la radiación diaria prevista al actualizar el ciclo de IFS o al usar AIFS, y cuánto depende esa respuesta de la escala relativa entre pronósticos y observaciones.

## Las dos decisiones

**H1: esperar a la actualización.** IFS de las 00 UTC frente a IFS de las 06 UTC del día anterior al objetivo. Cambian ciclo y antelación; no es una comparación a igual plazo.

**H2: cambiar de modelo.** IFS y AIFS de las 00 UTC del día anterior. El ciclo coincide; se evalúa el producto horario de Open-Meteo. No se han contrastado directamente los GRIB nativos de ECMWF.

Se suma la energía de las 24 horas del día objetivo. IFS 00 usa las marcas +25…+48 h e IFS 06, +19…+42 h. Identificar un ciclo histórico no certifica que estuviera disponible antes de una decisión comercial concreta.

## Cómo se evitó elegir los casos favorables

Selección, ventanas, métrica y procedimiento estadístico se guardaron con un hash antes de la descarga principal. Las estaciones se eligieron por rejilla geográfica, sin sustituirlas por su error: 33 en celdas peninsulares y Baleares, más una en Canarias. Las 34 superaron el mínimo de cobertura primaria.

La primaria son 110 días (14-may–31-ago-2026), con versiones nuevas de los modelos. La secundaria son 40 días (3-abr–12-may), con las anteriores. El 13 de mayo mezcla versiones y se excluye. La muestra no representa un año completo ni evalúa invierno.

La congelación es local. Un piloto ya era conocido y había exposición previa a 92 estación-días de dos estaciones. El informe declara ese límite y las desviaciones de implementación; no se presenta como prerregistro externo ni como ausencia total de conocimiento previo.

## Leer los porcentajes

El MAE mide la distancia absoluta entre pronóstico y observación, aquí normalizada por la radiación media de cada estación. La mejora compara dos pronósticos sobre los mismos pares válidos:

```text
mejora (%) = 100 × (MAE del primero − MAE del segundo) / MAE del primero
```

**7,57 % de mejora** significa reducción relativa de ese error. No significa un 7,57 % más de radiación, producción fotovoltaica o ingresos. Las estaciones pesan según sus pares válidos; no todas tienen idéntico peso agregado. Los huecos permanecen como huecos.

Los intervalos remuestrean días completos, con todas sus estaciones, mediante bloques circulares. Se muestran los tres largos fijados. Holm corrige H1 y H2 dentro de cada largo; los diagnósticos posteriores no heredan esa condición confirmatoria. [Fórmulas y punteros exactos](TRAZABILIDAD.md).

## El resultado y la prueba de escala

| Comparación | SiAR publicada | Puntuar con O/0,95 |
|---|---|---|
| H1: IFS 00 → IFS 06 | +1,47 %; IC95 [0,69; 2,26] | +0,44 %; IC95 [−0,58; 1,39] |
| H2: IFS 00 → AIFS 00 | +7,57 %; IC95 [4,60; 10,48] | −5,64 %; IC95 [−10,08; −1,33] |

IC95 con bloques de 7 días. El informe contiene bloques de 1 y 14 días y todos los escenarios k = 0,95; 1; 1,05.

Dividir O por 0,95 la aumenta un 5,26 %. No demuestra que el sensor mida un 5 % de menos. En esta métrica, dividir O por k y recalcular su media equivale a multiplicar los pronósticos por k: **el eje no separa error del sensor y del pronóstico**.

H1 mantiene signo positivo pero pierde un intervalo enteramente positivo. H2 invierte su signo. Las dos incumplen la regla congelada entre escenarios; eso no prueba ausencia de capacidad predictiva.

## El contexto que impide simplificar demasiado

**La secundaria difiere.** Con k = 0,95: H1 +2,36 % (IC95 [−0,87; 4,89]) y H2 +5,33 % ([0,73; 9,06]). La ventana estaba fijada, pero esta extensión es posterior y sus intervalos son exploratorios, sin Holm. Periodo, duración y versiones cambian a la vez; no se identifica una causa estacional.

**La historia no calibra esta muestra.** Urraca et al. describen una desviación cercana al −1 % para la mayoría de los fotodiodos históricos desde 2010. Da contexto para no tratar k = 0,95 como central, pero no estima la escala de estas 34 estaciones en 2026. Fuente y texto archivado constan en el informe.

**Las redes no coinciden por completo.** En una auditoría previa, SARAH-3 menos medida en 546 fechas comunes de Galicia dio +6,95 %, +8,62 % y +15,75 % en tres SiAR, frente a +1,38 % y −1,96 % en dos MeteoGalicia. Ubicación, altitud, nubosidad y representatividad impiden atribuirlo solo al instrumento. Es otro periodo y otra muestra, no una validación de estos pronósticos.

**Centrar no valida una corrección operativa.** Al retirar desplazamientos medios por estación dentro de la muestra, las diferencias de MAE son pequeñas y sus intervalos incluyen cero. Se usa información de la propia muestra: no es postproceso entrenado y evaluado fuera de muestra, ni identifica un componente causal ni demuestra equivalencia.

## Qué aporta y qué queda fuera

Una comparación cuantificada y reproducible, junto con la demostración de cuánto puede depender de la referencia. Sirve como caso de evaluación: emparejar, declarar exposición previa, conservar huecos, examinar escenarios y separar estadística de explicación física.

No demuestra una regla operativa con aerosoles, un fallo de sensores, una mejora anual generalizable ni una decisión rentable. La evaluación de pronósticos contra MeteoGalicia quedó incompleta en un encargo separado. [Auditorías y alcance](AUDITORIA.md) · [Correcciones](../CHANGELOG.md) · [Archivo](ARCHIVO.md).
