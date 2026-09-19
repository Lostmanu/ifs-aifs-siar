# Registro de cambios

Las cifras del estudio no han cambiado en ninguna versión. La especificación congelada
(`estudio/metodo_fijado.json`, SHA-256 `4f84de4a19ad94283261ac370313cca153177f9b46c77288c0745f18633892e3`)
es la misma desde el 14 de septiembre de 2026 y ninguna corrección la toca.

## v1.0.2 — 19 de septiembre de 2026

Corrige la reproducibilidad fuera de Windows. **Ningún resultado cambia.**

**Reproducibilidad multiplataforma.** `datos/heredado_manifiesto.json` guardaba sus 1.461 rutas con el
separador de Windows. En un sistema POSIX la barra invertida no separa directorios, de modo que
`Path('raw\\heredado\\…')` era un único nombre de fichero: la sección 6.5 del informe, el enlace
06-18 UTC, no se podía reconstruir en Linux ni en macOS. Ahora el manifiesto usa `/` y
`comun.ruta()` acepta los dos formatos, así que la resolución es idéntica en los dos sistemas.
Comprobado: de las 1.461 rutas guardadas, 1.461 se resolvían de forma distinta en Windows y en POSIX
antes del cambio, y 0 después.

**Los fallos dejan de ser silenciosos.** `analizar.py` guardaba el error del enlace 06-18 UTC dentro de
`resultados.json` y terminaba con éxito, así que un informe incompleto podía publicarse sin que nadie lo
notara. Ahora aborta con un mensaje; para obtener un resultado sin esa sección hay que pedirlo
explícitamente con `--enlace-opcional`, y entonces queda marcado como degradado.

**Pruebas.** El método pasa de 16 a 20 pruebas. Las cuatro nuevas cubren la resolución de rutas: que el
lector acepta los dos separadores, que el manifiesto publicado no contiene ninguno de Windows, que las
1.461 entradas reales resuelven a más de un componente, y una que reproduce el fallo de POSIX sin
depender del sistema donde corre.

**`verificar.py` desde un clon de Git.** Terminaba con `StopIteration` porque el árbol publicado no
incluye los cuerpos `raw/`. Ahora explica que hay que descargar el paquete de la versión y usar
`reproducir_offline.py`.

**Enlaces.** Los informes archivados enlazaban figuras y datos por ruta absoluta de la máquina donde se
hizo el trabajo. Esos artefactos se publican ahora junto a cada informe y los enlaces son relativos. Se
añade `herramientas/comprobar_enlaces.py`, que revisa los 228 enlaces de los 30 documentos y falla si
encuentra uno roto o una ruta absoluta; encontró ocho enlaces rotos más que nadie había visto.

**Integración continua.** `.github/workflows/ci.yml` compila, ejecuta las pruebas, re-deriva la selección
de estaciones y comprueba los enlaces en Ubuntu y en Windows en cada envío. La reproducción completa del
paquete se lanza a mano o al publicar una versión, y descarga el asset en las dos plataformas.

**Paquete.** Incluye ahora `code/verificar_seleccion.py` y el catálogo SiAR, y `reproducir_offline.py`
re-deriva las 34 estaciones como un paso más. 3.058 ficheros,
SHA-256 `3a09f5b39f8e14595bf21c0f4e1fd6c60ddceadacd2d6e5393e4e00427996a91`.
La v1.0.1 se conserva publicada y sin modificar.

## v1.0.1 — 19 de septiembre de 2026

Restituye el contexto histórico de Urraca et al. 2019, el contraste con MeteoGalicia y la descomposición
descriptiva del error cuadrático. Añade la sensibilidad de escala en la ventana secundaria. Declara el
cambio de vocabulario respecto al método congelado. Sin cambios en resultados, muestra ni método.

También, fuera del paquete: licencia MIT para el código, `DERECHOS.md` con el desglose por fuente de
datos, y `estudio/code/verificar_seleccion.py`, que re-deriva las 34 estaciones desde el catálogo
publicado sin necesitar el árbol de trabajo original.

## v1.0.0 — 19 de septiembre de 2026

Cierre del estudio. 34 estaciones SiAR, 110 días objetivo del 14 de mayo al 31 de agosto de 2026,
dos hipótesis primarias con corrección de Holm y análisis de sensibilidad al error de escala.
