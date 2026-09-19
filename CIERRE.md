# Cierre del proyecto

**Decisión del usuario: cerrar y conservar; no ampliar el experimento. Fecha: 19-09-2026.**

El entregable definitivo es el estudio de 34 estaciones SiAR y 110 días de mayo a agosto de 2026, revisado para separar comparación empírica, inferencia condicionada y sensibilidad de escala. El código, los datos archivados y los resultados permiten reproducir el cálculo.

Con SiAR publicada hay mejoras relativas del MAE del 1,47 % (IFS 00→06) y 7,57 % (IFS 00→AIFS 00). Las dos superan Holm en cada uno de los tres largos de bloque. La prueba determinista de escala fijada no respalda una conclusión robusta bajo todos sus escenarios: H1 pierde un intervalo enteramente positivo y H2 invierte su signo con O/0,95.

Quedan fuera de las conclusiones una causa física, un fallo de sensores, una ventaja operacional demostrada y una utilidad económica. Restar el residuo medio dentro de la muestra no es una corrección operativa validada. La simulación con factores independientes tampoco estima la probabilidad real de calibración de la red.

La evaluación AIFS/IFS frente a MeteoGalicia pertenecía al encargo separado `evaluacion_meteogalicia`, no al estudio de 34 estaciones. Aquel encargo quedó incompleto. No se presenta su ausencia como una pregunta incumplida de este estudio ni se abre una continuación automática.

La auditoría aportada por el usuario respalda el cierre con reservas y pidió hacer visible la trazabilidad. Esa documentación se completa en [TRAZABILIDAD.md](docs/TRAZABILIDAD.md), sin modificar la selección, el método congelado ni los resultados. Se conserva [la auditoría tal como fue recibida](docs/auditoria_cierre_recibida.txt), identificando que su autor no inspeccionó ni recalculó el paquete completo.

La publicación en Git añade documentación, código legible y versiones descargables de los paquetes. Los entregables locales originales se conservan intactos; el cierre no elimina datos ni informes históricos.

## Corrección v1.0.1

Se restituyen el contexto histórico de Urraca, el contraste con MeteoGalicia y la descomposición descriptiva del MSE. El escenario k=0,95 conserva puntos positivos en la ventana secundaria: H1 +2,36 % y H2 +5,33 %; el intervalo de H1 incluye cero. Esta extensión de escala es posterior al resultado y no cambia el veredicto primario. El cambio de vocabulario respecto al método congelado queda declarado. [Detalle y límites de la corrección](docs/CORRECCION_v1.0.1.md).
