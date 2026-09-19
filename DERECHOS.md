# Licencias y derechos de datos

Este repositorio mezcla código propio, texto propio y datos de terceros. Cada parte tiene condiciones
distintas y conviene no tratarlas como un bloque.

El fichero [LICENSE](LICENSE) es la MIT y **cubre solo el código**. El texto, las figuras y los datos tienen las condiciones que se detallan aquí abajo.

## Lo que es propio

| Parte | Ficheros | Licencia |
|---|---|---|
| Código | `estudio/code/*.py`, `estudio/reproducir_offline.py` | MIT, ver [LICENSE](LICENSE) |
| Informes, documentación y figuras | `README.md`, `CIERRE.md`, `docs/**`, `estudio/outputs/informe.md`, `estudio/revision/*.md`, los dos PNG | CC BY 4.0 |
| Resultados derivados | `estudio/outputs/resultados.json`, `panel_analisis.json`, `estaciones.json`, `estudio/datos/*.json` | CC BY 4.0, con la reserva sobre datos de origen que se explica abajo |

## Datos de terceros

Ninguno de estos proveedores ha cedido derechos a este repositorio. Se incluyen o se citan para poder
verificar el trabajo, con atribución, y **sus condiciones siguen siendo las suyas**. Quien reutilice
estos materiales debe comprobarlas en la fuente, no aquí.

**Observaciones de radiación — SiAR, Ministerio de Agricultura, Pesca y Alimentación (España).**
Totales diarios de radiación global descargados de la consulta pública del Sistema de Información
Agroclimática para el Regadío, y el catálogo de estaciones. En el repositorio están las respuestas ya
procesadas (`estudio/datos/observaciones_diarias*.json`) y el catálogo original
(`estudio/datos/catalogo_siar_20260914T0741Z.csv`, SHA-256 `c1af4cc4…`, descargado el 2026-09-14 a las
07:41 UTC de `https://servicio.mapa.gob.es/siarweb/fichaEstacion/masInfo/coordenadasEstacion`).
Los cuerpos originales de las consultas viajan solo en el paquete de la versión de cierre.
Condiciones del proveedor: no verificadas en este trabajo; consúltense en el servicio de SiAR.

**Pronósticos — ECMWF, servidos por Open-Meteo.**
Series horarias de `shortwave_radiation` y `cloud_cover` de los modelos `ecmwf_ifs025` y
`ecmwf_aifs025_single`, obtenidas de la Single Runs API. La documentación de precios de Open-Meteo
describe su nivel gratuito como de uso **no comercial**; el uso aquí fue de investigación y el gasto
contratado fue de 0 €. Las condiciones de ECMWF sobre la salida de sus modelos son las suyas y no se
han verificado en este trabajo. Las respuestas íntegras y sus recibos viajan en el paquete de la
versión de cierre, no en el árbol de Git.

**Urraca, R. et al. (2019), *Sensors* 19(11):2483.**
El texto completo en XML se conserva en `estudio/revision/fuentes/urraca_2019.xml`, descargado de
Europe PMC (`PMC6603785`). El propio artículo declara: *«This article is an open access article
distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license»*,
© 2019 by the authors, licenciataria MDPI. Se redistribuye con atribución bajo esa licencia.
DOI: [10.3390/s19112483](https://doi.org/10.3390/s19112483).

**Productos satelitales SARAH-3 y LSA SAF.**
No se redistribuye ningún dato satelital. Solo se citan cifras agregadas de una auditoría anterior de
este mismo proyecto, que sí los descargó; esa auditoría se conserva como antecedente en
`estudio/revision/antecedentes_referencia/`.

## Datos personales

El repositorio no contiene datos personales. Varios ficheros de archivo histórico y el programa
`estudio/code/seleccion_rejilla.py` contienen rutas absolutas de la máquina donde se ejecutó el
trabajo, que incluyen un nombre de usuario de Windows. Se conservan sin editar porque están cubiertos
por manifiestos de integridad y modificarlos rompería la cadena de hashes; no afectan a ninguna
comprobación, y la selección de estaciones se puede rehacer sin ellos con
`estudio/code/verificar_seleccion.py`.

## Cómo citar

> *IFS y AIFS frente a SiAR: medición preespecificada del valor de la actualización y de IA frente a
> física en radiación global diaria* (2026). Repositorio `Lostmanu/ifs-aifs-siar`, versión de cierre
> v1.0.1. Especificación congelada SHA-256 `4f84de4a19ad94283261ac370313cca153177f9b46c77288c0745f18633892e3`.
