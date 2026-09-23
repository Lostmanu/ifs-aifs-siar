# Revisión de contenido, reproducción y presentación

23 de septiembre de 2026 · Base local: `96efbc68432c9ab8519eadc868577d3e45abd6d6`.

**El repositorio tiene una base sólida y comprobable, pero no estaba libre de problemas.** La revisión detectó un fallo del lanzador en este entorno, referencias documentales desactualizadas y una portada que exigía demasiado contexto previo. Se corrigen conservando el estudio y sus archivos históricos.

[Portada](../../README.md) · [Referencias de diseño](referencias.md) · [Comprobaciones estructuradas](comprobaciones.json) · [Registro de reproducción](reproduccion.json)

La [validación de presentación](validacion_presentacion.json) registra los enlaces, la correspondencia de las figuras con sus datos, el contraste de texto y las vistas previas. Incluye controles negativos: rechazar otro ZIP como v1.0.2 y detectar una imagen HTML rota.

## Hallazgos y resolución

| Hallazgo | Consecuencia | Resolución |
|---|---|---|
| El lanzador activa el audit hook antes de cargar `numpy.testing` | En este Windows, tres pruebas fallan al consultar el sistema y abrir `nul` | Entrada de compatibilidad que inicializa esa dependencia antes de ejecutar el lanzador original; los controles siguen activos durante el análisis |
| LEEME y trazabilidad decían que los cuatro motores son idénticos a los originales | Confunde conservación de resultados con conservación de bytes; `analizar.py` cambió en v1.0.2 | Aclaración en la guía vigente y en trazabilidad; no se modifica el paquete publicado |
| La portada destacaba 16 pruebas y 60.602 valores sin marcar su versión | Mezcla la verificación original con la cadena actual de 20 pruebas y 61.383 valores | Versiones diferenciadas y acceso al registro actual |
| Archivo recomendaba v1.0.1 y el índice omitía v1.0.2 | El visitante podía empezar por una entrega anterior | Enlaces e índice actualizados, conservando todas las entradas históricas |
| CI descargaba la última versión sin ligarla al evento | Una ejecución podía validar un paquete distinto del que pretendía comprobar | Versión explícita y SHA-256 verificado antes de extraer |
| Correcciones, instrucciones y conclusión competían en el README | La pregunta y el resultado eran difíciles de encontrar | Portada ordenada, figura resumida, guías separadas y entrada a la auditoría |

El [fallo de la invocación directa](fallo_lanzador_original.txt) se conserva. No se reemplaza por un PASS retrospectivo: el PASS corresponde a la ejecución mediante `herramientas/reproducir_paquete.py`.

## Lo que se comprobó

- Los **3.057 archivos** del árbol completo coinciden con el manifiesto v1.0.2. Se reconstruyeron desde 78 archivos de la copia Git y 2.979 de los paquetes locales anteriores, sin una nueva descarga.
- Los **ocho pasos** de la cadena compatible terminaron. Se compararon **61.383 valores numéricos**, con **diferencia máxima 0** y cuatro marcas de generación excluidas.
- Pasaron las **20 pruebas** del método y las rutas; se rehicieron las **34 estaciones** desde el catálogo y se ejecutó la verificación decimal y de **708 recibos**.
- Se comprobaron **43 entradas** de cifras contra sus punteros JSON. Las imágenes nuevas se generan desde los resultados archivados y su hash de origen.
- Los **109 archivos versionados** de `estudio/` y `docs/historico/` conservan sus bytes respecto al estado inicial de esta revisión. Incluyen método, paneles, observaciones, informes y figuras originales.

El registro conserva Python 3.12.14, NumPy 2.3.5, duración por paso y comparaciones por archivo. Es evidencia de reproducción y de controles concretos; no una auditoría científica independiente de todos los supuestos.

## Alcance científico

No se cambia la pregunta, la selección ni los resultados. Se mantiene la mejora medida frente a SiAR y el incumplimiento del criterio de escala en la ventana primaria. La secundaria, la evidencia histórica y las discrepancias entre redes se explican como contexto con sus límites.

La evaluación no identifica la fuente de la discrepancia entre observación y pronóstico. No acredita disponibilidad operacional, utilidad anual ni rentabilidad. La exposición previa a datos, el carácter local de la congelación y los análisis posteriores siguen explícitos. El cierre científico permanece vigente.

## Presentación y referencias

Se revisaron scikit-learn, Ruff, pvlib-python, WeatherNext y WeatherBench 2. Se adoptan patrones útiles: propósito inmediato, evidencia visual, reproducción fácil de localizar, cita y forma de comunicar errores. La [comparación de referencias](referencias.md) enlaza las fuentes y distingue popularidad de calidad.

La figura se presenta en escritorio/móvil y claro/oscuro, con ejes comunes, intervalos, formas diferentes para los escenarios y valores repetidos en texto. No incorpora datos simulados. Se conserva Markdown de GitHub y Python estándar para generar la figura; no se añade un sitio web ni una dependencia al motor científico.

## Primera fase local y límites

La primera prueba se ejecutó en Windows con el árbol reconstruido desde archivos locales, sin una nueva descarga del ZIP ni ejecución en Linux/macOS. La coincidencia del árbol por SHA-256 no verificaba la envoltura binaria del ZIP remoto. La inicialización de NumPy ocurre antes del audit hook y puede consultar el sistema; el análisis original sigue ejecutándose bajo sus controles. Estos controles no constituyen aislamiento del sistema operativo.

En esa primera fase no se pudo publicar por las restricciones de escritura y red de la sesión. Los registros de comprobación local conservan ese estado histórico; no describen el estado actual de GitHub.

## Verificación del paquete publicado

Al recuperar el acceso el 23 de septiembre, se descargó el ZIP v1.0.2 de GitHub: **115.443.833 bytes**, SHA-256 `3a09f5b39f8e14595bf21c0f4e1fd6c60ddceadacd2d6e5393e4e00427996a91`, coincidente con el registro conservado y el digest del asset remoto. No se sustituyó la versión publicada.

La [ejecución remota 35894661786](https://github.com/Lostmanu/ifs-aifs-siar/actions/runs/35894661786), sobre el commit `ed18b9162f1ff0b31163a06286474267ee5703cf`, terminó con **los cuatro trabajos correctos**: pruebas y reproducción completa en Ubuntu y Windows. Ambos descargaron el paquete publicado, verificaron su SHA-256 y completaron ocho pasos, con **61.383 valores comparados y diferencia máxima cero por sistema**.

| Entorno remoto | Python | NumPy | Registro conservado |
|---|---|---|---|
| Ubuntu | 3.12.14 | 2.3.5 | [Reproducción Ubuntu](reproduccion_ubuntu.json) |
| Windows | 3.12.10 | 2.3.5 | [Reproducción Windows](reproduccion_windows.json) |

Se conservan los registros sin la ruta temporal absoluta del runner y con el hash de sus originales. La [validación de GitHub](validacion_github.json) reúne ejecución, entornos, paquete, metadatos y conservación de los 109 archivos originales. macOS no se ejecutó en esta revisión.

También se comprobó la página publicada con un navegador: las cuatro variantes de la figura cargan correctamente a 390 y 1.280 píxeles, en modo claro y oscuro, sin desbordamiento horizontal de la página. GitHub reconoce la opción de cita en la vista de escritorio. La descripción remota y el tema `solar-radiation` quedaron actualizados. Estos controles verifican presentación y reproducción; no amplían las conclusiones científicas.
