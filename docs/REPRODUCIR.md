# Reproducir y comprobar

[Portada](../README.md) · [Guía de lectura](LECTURA.md) · [Trazabilidad](TRAZABILIDAD.md)

El clon permite inspeccionar código, catálogo, panel y resultados. El paquete descargable añade las respuestas originales `raw/` para reconstruir toda la cadena.

## Comprobar el clon

Desde la raíz del repositorio, con Python 3.12:

```bash
python -m pip install -r requirements.txt
python estudio/code/test_metodo.py
python estudio/code/verificar_seleccion.py
python herramientas/comprobar_enlaces.py
python herramientas/generar_figura_portada.py --check
```

La instalación requiere conexión o un paquete NumPy local. Después, estas comprobaciones funcionan sin red. Hay **20 pruebas** del método y de las rutas; la selección se rehace desde el catálogo publicado. La figura de portada se coteja con los JSON originales.

## Obtener y verificar el paquete

Descargue **`datos_y_analisis_portable_v1.0.2.zip`** de la [versión v1.0.2-cierre](https://github.com/Lostmanu/ifs-aifs-siar/releases/tag/v1.0.2-cierre) y guárdelo en `descarga/`. El ZIP automático «Source code» de GitHub no contiene `raw/` y no lo sustituye.

Con GitHub CLI, opcionalmente:

```bash
gh release download v1.0.2-cierre --repo Lostmanu/ifs-aifs-siar --pattern datos_y_analisis_portable_v1.0.2.zip --dir descarga
```

Compruebe el SHA-256 antes de extraer:

```bash
python herramientas/verificar_paquete.py descarga/datos_y_analisis_portable_v1.0.2.zip
```

Debe coincidir con [integridad_git.json](integridad_git.json). El comando devuelve error si no coincide. SHA-256 esperado:

```text
3a09f5b39f8e14595bf21c0f4e1fd6c60ddceadacd2d6e5393e4e00427996a91
```

## Ejecutar sin conexión

Con Python y NumPy instalados, desconecte la red si desea comprobar el funcionamiento offline. Estos comandos sirven en PowerShell, Linux y macOS; use `python3` si su sistema lo requiere. Elija una carpeta nueva y de ruta corta:

```bash
python -m zipfile -e descarga/datos_y_analisis_portable_v1.0.2.zip reproduccion_cierre
python herramientas/reproducir_paquete.py reproduccion_cierre
```

La entrada de compatibilidad inicializa `numpy.testing` antes de ejecutar el lanzador original. En el Windows restringido de la revisión del 23-09-2026, su carga diferida consultaba el sistema después de activarse el audit hook y fallaba al abrir `nul`. **Se conserva el mismo bloqueo durante el análisis**; no se modifica el paquete ni se desactiva su verificación. [Incidencia y comprobación](revision_20260923/informe.md).

El lanzador valida **3.057 archivos más el manifiesto** y crea una copia dentro de `reproduccion/`. Ejecuta ocho pasos: pruebas, selección, observaciones, análisis, diagnóstico, sensibilidad secundaria posterior, verificación e informe. No descarga datos ni necesita claves.

**Salida esperada:** `PASS` y una ruta a `comprobacion_offline.json`. Se comparan siete JSON, con intervalos y huecos; se excluyen cuatro marcas de generación. Son **61.383 valores**, con diferencia máxima cero en la [ejecución compatible documentada](revision_20260923/reproduccion.json). Las tolerancias son absoluta 1e−10 y relativa 1e−11; fuera de ellas se informa `FAIL`.

Entorno local de referencia: Python 3.12.14 y NumPy 2.3.5. La [verificación remota del 23 de septiembre](https://github.com/Lostmanu/ifs-aifs-siar/actions/runs/35894661786) también reprodujo los 61.383 valores con diferencia máxima cero en Ubuntu (Python 3.12.14) y Windows (Python 3.12.10), ambos con NumPy 2.3.5. [Registros conservados y alcance](revision_20260923/validacion_github.json). macOS no se ejecutó en esta revisión.

## Figuras

Los PNG científicos ya están incluidos. `--figuras` requiere matplotlib, fuera de las dependencias mínimas fijadas, y su aspecto puede variar con versión y fuentes. La figura SVG de portada se genera con Python estándar:

```bash
python herramientas/generar_figura_portada.py
```

Es una vista adicional de cuatro resultados existentes. No sustituye las figuras archivadas.

## Si algo falla

| Situación | Qué comprobar |
|---|---|
| SHA-256 distinto | Paquete completo de v1.0.2, no ZIP de fuentes u otra versión |
| Archivo ausente o hash distinto | Extraer en una carpeta vacía; no mezclar entregas |
| Faltan cuerpos originales | Usar el paquete completo, no `verificar.py` desde el clon |
| `FAIL` numérico | Conservar el registro y comprobar Python/NumPy; no ampliar tolerancias para forzar PASS |
| Rutas demasiado largas en Windows | Extraer en una carpeta más corta |

El audit hook bloquea conexiones y procesos externos e inspecciona aperturas para escritura. No aísla el sistema operativo ni certifica calibración. Ejecutar scripts individuales puede sobrescribir las salidas de esa copia; use el lanzador.

## Aclaración de documentación heredada

El LEEME conservado contiene la frase de v1.0.1 «los cuatro motores […] son copias exactas». **No describe v1.0.2**: `analizar.py` cambió para resolver rutas y abortar si falla el enlace 06–18 UTC. Se conservan cifras y especificación, no los bytes de todos los motores. [Cambios de v1.0.2](../CHANGELOG.md).

La guía aclara esa frase sin reemplazar archivos ni alterar retroactivamente el hash de la entrega publicada. En la primera fase de la revisión se reconstruyó el árbol desde copias locales y se validó contra su manifiesto. Después se descargó el ZIP remoto y se confirmó su SHA-256: [registro de revisión](revision_20260923/informe.md).
