# IFS y AIFS frente a SiAR — estudio cerrado

**Estado: cerrado el 19 de septiembre de 2026. Evidencia comparativa condicionada y reproducible.**

En 34 estaciones SiAR y 110 días entre el 14 de mayo y el 31 de agosto de 2026, el producto horario de Open-Meteo mostró menor MAE relativo al actualizar IFS de 00 a 06 UTC y al sustituir IFS 00 por AIFS 00, usando las observaciones SiAR publicadas y pares completos dentro de cada contraste. Los resultados superan el ajuste de Holm bajo los tres largos de bloque fijados. Las mejoras no superan todos los escenarios comunes de escala preespecificados.

| Contraste | Pares estación-día | Reducción relativa del MAE normalizado | IC95, bloques de 7 días | Escenario O/0,95 |
|---|---:|---:|---:|---|
| IFS 00 → IFS 06 UTC | 3.664 | 1,47 % | [0,69; 2,26] | 0,44 %; IC95 [−0,58; 1,39] |
| IFS 00 → AIFS 00 UTC | 3.697 | 7,57 % | [4,60; 10,48] | −5,64 %; IC95 [−10,08; −1,33] |

Los ciclos corresponden al día anterior al día objetivo. La referencia, la muestra estacional, el producto servido y la sensibilidad de escala condicionan la conclusión. No se identifican errores de sensores, habilidad libre de error observacional, disponibilidad operacional, ahorro o rentabilidad. La evaluación de pronósticos frente a MeteoGalicia pertenece a otro encargo (`evaluacion_meteogalicia`), que quedó incompleto; nunca estuvo incluida en este estudio de 34 estaciones.

## Leer y comprobar

- [Cierre y alcance](CIERRE.md).
- [Informe completo revisado](estudio/outputs/informe.md) y [revisión de interpretación](estudio/revision/informe_revision.md).
- [Trazabilidad: cifras, fórmulas, pares, bootstrap y Holm](docs/TRAZABILIDAD.md).
- [Especificación congelada](estudio/metodo_fijado.json), [estaciones](estudio/outputs/estaciones.json) y [resultados completos](estudio/outputs/resultados.json).
- [Verificación de entrega](estudio/outputs/verificacion_entrega.json): 60.602 valores reproducidos exactamente, 708 recibos comprobados y 16 pruebas del método superadas. La auditoría textual aportada por el usuario no hizo ese recálculo; [su alcance se conserva aquí](docs/AUDITORIA.md).
- [Re-derivar la selección de estaciones](estudio/code/verificar_seleccion.py): `python estudio/code/verificar_seleccion.py` rehace las 34 estaciones desde el catálogo publicado (`estudio/datos/catalogo_siar_20260914T0741Z.csv`, SHA-256 comprobado contra la especificación congelada) y las compara con `estaciones.json`. No necesita el ZIP ni el árbol original.
- [Archivo histórico y hashes](docs/ARCHIVO.md). Los informes anteriores son antecedentes y no sustituyen el cierre revisado.

![Sensibilidad de escala](estudio/outputs/figura_sensibilidad.png)

## Reproducir sin red

Python 3.12.14 y NumPy 2.3.5 fueron el entorno verificado. Instale NumPy antes de desconectar. Las figuras PNG ya están incluidas; matplotlib es opcional si quiere regenerarlas.

Descargue `datos_y_analisis_portable_v1.0.1.zip` de la [versión de cierre](https://github.com/Lostmanu/ifs-aifs-siar/releases/tag/v1.0.1-cierre). El ZIP contiene las respuestas originales, recibos, código y manifiesto completo. El árbol de Git permite inspeccionar código y resultados; los cuerpos `raw/` se conservan en el ZIP.

Con GitHub CLI, o descargando el asset desde la página de la versión:

```powershell
gh release download v1.0.1-cierre --repo Lostmanu/ifs-aifs-siar --pattern datos_y_analisis_portable_v1.0.1.zip --dir descarga
Get-FileHash descarga/datos_y_analisis_portable_v1.0.1.zip -Algorithm SHA256
Expand-Archive descarga/datos_y_analisis_portable_v1.0.1.zip -DestinationPath reproduccion_cierre
python -m pip install -r requirements.txt
python reproduccion_cierre/reproducir_offline.py
```

SHA-256 esperado del ZIP: `421d2af84c439009abee798f897e0c9a3f8dfe8bbe200be603c49948dde38795`.

El lanzador verifica el manifiesto y crea una copia de trabajo dentro de la carpeta extraída. Bloquea conexiones del proceso, reconstruye las salidas y compara números, estructura y huecos; excluye cuatro marcas de generación al comparar los siete archivos de v1.0.1. El registro verificado empleó aproximadamente un minuto de cálculo, aunque el tiempo depende del equipo. Consulte el [LEEME del paquete](estudio/LEEME.md).

## Fuentes y conservación

Datos MAPA/SiAR y pronósticos ECMWF servidos por Open-Meteo. Se conservan las URL, fechas de recuperación y hashes originales. El repositorio conserva un trabajo de investigación, sin servicio desplegado ni nueva fase experimental.

**Licencias.** El código está bajo [MIT](LICENSE); el texto de los informes, la documentación y las figuras, bajo CC BY 4.0. Los datos de terceros conservan las condiciones de sus proveedores y esta publicación no les asigna una licencia nueva ni concede derechos adicionales sobre ellos. El desglose por fuente, con lo que está verificado y lo que no, está en [DERECHOS.md](DERECHOS.md).

## Corrección v1.0.1

Se restituyen el contexto histórico de Urraca, el contraste con MeteoGalicia y la descomposición descriptiva del MSE. El escenario k=0,95 conserva puntos positivos en la ventana secundaria: H1 +2,36 % y H2 +5,33 %; el intervalo de H1 incluye cero. Esta extensión de escala es posterior al resultado y no cambia el veredicto primario. El cambio de vocabulario respecto al método congelado queda declarado. [Detalle y límites de la corrección](docs/CORRECCION_v1.0.1.md).

Verificación v1.0.1: **61.383 valores numéricos**. diferencia máxima 0.0. [Registro](estudio/outputs/verificacion_v1.0.1.json). Los 60.602 valores de la entrega anterior se conservan; la diferencia de recuento es el archivo de diagnóstico añadido.
