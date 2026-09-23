# Referencias de presentación

Consulta: 23-09-2026. Se han revisado repositorios reconocidos y ejemplos próximos al tema, no un ranking universal de calidad. Las estrellas son una señal de difusión, no una evaluación científica ni una garantía de buen diseño.

| Referencia | Difusión visible al consultar | Qué se ha tomado como criterio |
|---|---:|---|
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | ~67,4 mil estrellas | Entrada con propósito e instalación, enlaces a documentación y forma de citar |
| [Ruff](https://github.com/astral-sh/ruff) | ~49,7 mil | Una figura que permite entender pronto la afirmación principal, seguida de instrucciones concretas |
| [WeatherNext, antes GraphCast](https://github.com/google-deepmind/weathernext) | ~7,7 mil | Acceso al código, datos y uso inicial; distinción entre modelos y materiales |
| [pvlib-python](https://github.com/pvlib/pvlib-python) | ~1,7 mil | Cercanía al ámbito solar, propósito claro, documentación, contribución y cita |
| [WeatherBench 2](https://github.com/google-research/weatherbench2) | 638 | Separación entre explicación del benchmark, datos y evaluación; se observa además su aviso de sucesión por WeatherBench-X |

Las cifras son aproximadas y pueden cambiar. Son observaciones de las páginas enlazadas. La selección combina popularidad y pertinencia; no pretende que un estudio cerrado deba parecer una biblioteca con miles de usuarios.

## Decisiones para este estudio

La nueva portada presenta la pregunta y un gráfico de resultados con intervalos. Mantiene los colores verde y terracota de las figuras existentes. La imagen es SVG, se genera desde los datos y dispone de una composición móvil. La tabla y el texto alternativo conservan la información si la imagen no se ve.

La navegación distingue tres tareas: comprender, reproducir y auditar. El detalle de las correcciones se conserva en el registro de cambios, con guías accesibles desde la entrada. Dos insignias enlazan CI y la versión del paquete; no se añaden insignias que certifiquen calidad científica, prestigio o rentabilidad.

Se añade una cita CFF y una guía breve para comunicar errores. Se mantiene Markdown nativo de GitHub: no se añade una web, un framework ni una dependencia de diseño al cálculo científico. Ningún texto, logo o recurso gráfico de los proyectos de referencia se copia.

## Guías de GitHub consultadas

- [Acerca de los README](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes): propósito, utilidad, inicio y orientación para el visitante.
- [Acerca de los archivos CITATION](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files): metadatos de cita reconocidos por GitHub.

## Lo que aún necesita la cuenta de GitHub

Descripción sugerida: «Radiación solar: IFS y AIFS frente a 34 estaciones SiAR. Resultados, sensibilidad de escala y reproducción sin red.» Temas sugeridos: `solar-radiation`, `forecast-verification`, `ecmwf`, `aifs`, `reproducible-research`, `python`.

Son propuestas, no cambios remotos realizados. Antes de dar la presentación por publicada hay que revisar el README en GitHub y confirmar la ejecución de CI con el nuevo commit. No se afirma que estas mejoras garanticen estrellas o audiencia.
