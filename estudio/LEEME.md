# Medición a escala: paquete portable revisado el 19-09-2026 — corrección v1.0.2

34 estaciones SiAR; 14 de mayo–31 de agosto de 2026. Las cifras científicas y la especificación congelada se conservan. Se corrigen interpretaciones y rutas. Leer `outputs/informe.md` y `revision/informe_revision.md`.

**v1.0.2 corrige un fallo de reproducibilidad en Linux y macOS.** Hasta v1.0.1, el manifiesto de datos heredados guardaba las rutas con el separador de Windows. En un sistema POSIX la barra invertida no separa directorios, así que la sección 6.5 del informe, el enlace 06-18 UTC, no se podía reconstruir y quedaba como un error dentro de `outputs/resultados.json` mientras el programa terminaba con éxito. Ahora el manifiesto usa `/`, el lector acepta los dos formatos y `analizar.py` **aborta** si esa sección falla, en vez de publicar un resultado incompleto en silencio. Ninguna cifra cambia: en Windows el resultado era y sigue siendo el mismo.

## Reproducir

Extraiga este ZIP en cualquier carpeta NUEVA. Requiere Python 3.12 o posterior y NumPy. La comprobación de esta entrega utilizó Python 3.12.14 y NumPy 2.3.5. Matplotlib solo se necesita para regenerar figuras (entregadas también como PNG).

Desde la carpeta extraída:

```powershell
python reproducir_offline.py
# Opcional, si matplotlib está instalado:
python reproducir_offline.py --figuras
```

El lanzador comprueba todos los hashes de `manifest_portable_sha256.json`, crea una copia en `reproduccion/<fecha UTC>/`, bloquea conexiones de red y procesos externos mediante un audit hook de Python y comprueba las escrituras de archivos. Ejecuta pruebas, reconstrucción de observaciones, análisis principal (10.000 réplicas, 1.000 sorteos), diagnóstico posterior, verificación decimal y 708 recibos, e informe. Compara siete archivos JSON, incluidos intervalos, sorteos y huecos, con los entregados; excluye solamente cuatro marcas `generado_utc`. Los resultados de la reproducción se guardan en esa copia. No es una medida de aislamiento del sistema operativo.

El lanzador no descarga datos y no necesita claves ni conexión. Python, NumPy y, si procede, matplotlib deben estar instalados antes de desconectar. La tolerancia de comparación es absoluta 1e-10 y relativa 1e-11; en el entorno verificado la diferencia fue exactamente cero. En otra versión de NumPy o plataforma puede haber redondeos diferentes; los cambios grandes o resultados diferentes se marcan como FAIL.

`code/verificar.py` necesita los cuerpos originales de `raw/`, que viajan en este paquete pero **no** en el árbol de Git. Ejecutado desde un clon del repositorio termina con un mensaje explicándolo; para reproducir el estudio use siempre `reproducir_offline.py` desde la raíz de este paquete.

`code/comun.py` resuelve las salidas en la carpeta local `outputs/`. Ejecutar scripts individuales directamente puede sobrescribir las salidas de ESTA copia: use el lanzador. Los descargadores se conservan por procedencia y no forman parte de la reproducción sin red.

## Trazabilidad

El ZIP previo permanece intacto, SHA-256 `8237b05305d233a6dd29d5e424e6ae3c5fe98bdeacd36bf758c50185ff318c06`.
Especificación congelada: SHA-256 `4f84de4a19ad94283261ac370313cca153177f9b46c77288c0745f18633892e3`.
Los motores `metodo.py`, `analizar.py`, `preparar_observaciones.py` y `diagnostico_posterior.py` son copias exactas de los originales. Cambian las rutas de `comun.py` y la presentación de `informe.py` y `figuras.py`. Las diferencias de código están en `revision/*.diff`. Los comentarios y etiquetas históricos del diagnóstico se conservan como procedencia; su interpretación válida es la del informe revisado.

`revision/original_manifest_sha256.json` corresponde al ZIP ANTERIOR, no a esta versión. El manifiesto válido de esta entrega es `manifest_portable_sha256.json`. `verificar.py` marca NO_APLICA para el ZIP al reproducir dentro de una carpeta extraída; el lanzador comprueba el manifiesto antes de ejecutar, y la integridad del nuevo ZIP se entrega fuera de él para evitar una referencia circular.

Fuentes: MAPA/SiAR y ECMWF vía Open-Meteo, con sus recibos, URL y fechas de recuperación conservados. Una comprobación bibliográfica de Urraca et al. (2019) se guarda en `revision/fuentes/`, con URL, fecha y hash. No se descargaron nuevas observaciones, satélites ni pronósticos.

## Alcance de la corrección y límites técnicos

Leer `revision/correccion_v1.0.1.md`. El escenario de escala de la secundaria es una extensión posterior; no se reescriben el método ni resultados.json. El audit hook intercepta aperturas para escritura, conexiones y procesos externos, pero no todo borrado o renombrado; no es aislamiento del sistema operativo. Algunos scripts auxiliares conservan rutas heredadas o absolutas y están fuera de la cadena reproducida. En Windows use una ruta corta de extracción; no se garantiza cualquier longitud de ruta.

Base de v1.0.1: paquete portable v1.0.0, SHA-256 `7c08d8ce4748beda42412b82719a2cfa7132f08b17c50cc331c56393fb15f930`. La versión anterior permanece íntegra.
