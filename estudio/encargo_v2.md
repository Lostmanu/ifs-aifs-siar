# Encargo: medición a escala del valor de la actualización y de IA frente a física

Versión 2 (14-sep-2026). Sustituye a la anterior, que fijaba una ventana de 18 meses que **no existe** en el archivo de la Single Runs API para los modelos a 0,25°. Pega este documento completo como primer mensaje a Codex. Contiene todo el contexto necesario; no asumas que recuerda nada de sesiones anteriores.

---

## 1. Rol

Actúas como ingeniero de datos y analista experimental. Tu trabajo es **ejecutar una medición preespecificada y reportar su resultado, sea cual sea**, incluido "no hay efecto" o "no se puede medir". No eres un optimizador de resultados: si el resultado sale nulo, el encargo se ha cumplido igual de bien.

## 2. Contexto: de dónde viene esto

Trabajo previo, en `C:\Users\manue\Documents\Codex\2026-09-11\qu\outputs\latencia_pronosticos\`:

1. **Piloto de latencia** (Madrid) y **réplica** (La Mojonera AL01, A Capela C01, 10-ago a 8-sep-2026): actualizar el pronóstico del ciclo 00 UTC al 06 UTC reduce el MAE de radiación un 8,56 % y 8,27 %. Intervalos por estación incluyendo cero.
2. **Validación de calibración** (13-sep): una constante de sesgo entrenada con 14 días de junio y evaluada en julio mejora el MAE un 12,11 % en A Capela y lo **empeora** un 14,23 % en La Mojonera. El criterio general de continuación falló.
3. **Auditoría de la referencia** (14-sep): 7 estaciones SiAR + 2 de MeteoGalicia contra satélite (SARAH-3, LSA SAF), 565 días. SiAR queda sistemáticamente por debajo del satélite; MeteoGalicia mucho menos.

**Hallazgo externo decisivo**: Urraca et al. 2019 (*Sensors* 19:2483) contrastaron 732 estaciones de 9 redes españolas y midieron que los fotodiodos de silicio de SiAR (SKYE SP1110) tienen una incertidumbre real de **±15 % en irradiación diaria y ±5 % anual** frente a patrones AEMET, muy por encima del ±5 % nominal; el 35 % de las estaciones SiAR presentaban defectos. Consecuencia: **cualquier magnitud absoluta medida contra SiAR —un sesgo del modelo, una corrección constante— no es distinguible del error del instrumento.**

## 3. Decisiones de marco — NO se revisan en este encargo

Estas decisiones ya están tomadas. No las discutas, no las reabras, no propongas experimentos para comprobarlas.

**D1. El error del sensor se acepta como dato, no se investiga.** Se asume ±5 % de incertidumbre multiplicativa por estación y se **implementa dentro del análisis** (sección 7.4). No se valida ningún piranómetro, no se piden certificados, no se descarga satélite, no se comparan redes.

**D2. Solo se miden comparaciones RELATIVAS entre pronósticos.** Dos pronósticos distintos contra la misma observación. Un error multiplicativo del sensor afecta a ambos a la vez, así que la comparación sobrevive donde una magnitud absoluta no. Queda prohibido en este encargo medir el sesgo absoluto del modelo o entrenar correcciones.

**D3. El objetivo es investigación y portfolio, no negocio.** No se estiman euros, no se busca comprador, no se contacta a nadie. Un resultado publicable es el entregable.

**D4. Techo a la regresión metodológica.** Si durante el trabajo aparece un problema de referencia, instrumento, producto satelital, modelo de cielo despejado o similar: **se documenta en la sección de limitaciones y ahí se queda**. No se convierte en la siguiente fase. Este encargo no genera un encargo siguiente.

## 4. Tarea

Medir, con más potencia que el piloto de dos estaciones y un mes, dos cosas:

- **H1 — Valor de la actualización.** Para el modelo **IFS**, ¿el ciclo de las 06 UTC predice mejor el día siguiente que el de las 00 UTC?
- **H2 — IA frente a física.** A igualdad de ciclo (00 UTC), ¿predice mejor **AIFS** o **IFS**?

Escala objetivo: del orden de **25-30 estaciones repartidas por España** y **una ventana de ~16 semanas con una sola versión de cada modelo**. Es 15× más estaciones y 4× más días que el piloto; no cubre el invierno, y eso se dirá en el titular.

## 5. Fase 0 — Congelar la especificación antes de descargar nada

Escribe `metodo_fijado.json` con **todo** lo de las secciones 6 y 7, calcula su SHA-256, y **solo después** empieza a descargar. Registra la marca temporal de ambas cosas.

Si algo de lo que sigue es ambiguo, resuélvelo tú, escribe tu decisión en la especificación congelada, y sigue. No me preguntes antes de congelar: lo que importa es que la regla esté fijada antes de ver datos, no cuál regla sea.

## 6. Datos

### 6.1 Selección de estaciones — regla objetiva, aplicada antes de ver datos

1. Rejilla de **1,5° × 1,5°** sobre la península. Los valores siguientes son **centros de celda**; cada celda cubre ±0,75° alrededor de su centro:
   - latitudes: 36,0 · 37,5 · 39,0 · 40,5 · 42,0 · 43,5
   - longitudes: −9,0 · −7,5 · −6,0 · −4,5 · −3,0 · −1,5 · 0,0 · 1,5 · 3,0
2. Del catálogo público de estaciones SiAR con radiación global, para **cada celda que contenga al menos una estación**, selecciona la **más próxima al centro de la celda**. Una estación por celda. Baleares entra por esta rejilla si tiene estación en su celda; no se añade a mano.
3. Añade **una estación de Canarias** (la primera del catálogo por orden alfabético de nombre), porque queda fuera de la rejilla y es un régimen distinto.
4. **No se sustituye ninguna estación después de ver sus datos.** Si una tiene menos del 80 % de días válidos en la ventana primaria, se excluye por regla y se documenta; no se reemplaza.

Guarda el catálogo descargado, coordenadas, altitud y distancia al centro de celda de cada seleccionada.

### 6.2 Ventana temporal — condicionada por el archivo disponible

**Hecho verificado**: la Single Runs API de Open-Meteo solo archiva `ecmwf_ifs025` y `ecmwf_aifs025_single` **desde el 2 de abril de 2026**. Antes no hay runs individuales de estos modelos, y sin runs individuales no se puede separar el ciclo 00 del 06. **El 12 de mayo de 2026 (06 UTC)** IFS pasó al ciclo 50r1 y AIFS a la versión 2.

Por tanto:
- **Ventana primaria: 2026-05-12 a 2026-08-31** (~112 días objetivo). Una sola versión de cada modelo.
- **Ventana secundaria: 2026-04-02 a 2026-05-11** (~40 días). Versión anterior. Se reporta por separado, sin mezclar.
- Comprueba tú mismo la primera fecha con runs disponibles para ambos modelos y ciclos en una estación antes de congelar, y ajusta el inicio de la secundaria si difiere; documéntalo.

### 6.3 Observación

Totales diarios de radiación global de SiAR en MJ/m², convertidos a Wh/m² **multiplicando por 277,78** (1 MJ = 277,78 Wh). Día natural 00-24 UTC, según la convención horaria documentada de SiAR que ya usas.

Controles heredados: fechas únicas, ningún total nulo aceptado como válido, rango físico plausible. Excluye días completos que fallen; no imputes.

### 6.4 Pronóstico

Cuatro series, del **run del día anterior** al día objetivo, agregadas a día completo:

| Serie | Modelo Open-Meteo | Run | Horas del run que caen en el día objetivo |
|---|---|---|---|
| IFS_00 | `ecmwf_ifs025` | D−1 00 UTC | +24 … +47 |
| IFS_06 | `ecmwf_ifs025` | D−1 06 UTC | +18 … +41 |
| AIFS_00 | `ecmwf_aifs025_single` | D−1 00 UTC | +24 … +47 |
| AIFS_06 | `ecmwf_aifs025_single` | D−1 06 UTC | +18 … +41 |

Endpoint: `https://single-runs-api.open-meteo.com/v1/forecast`, parámetro `run` con la inicialización exacta, `forecast_days=3`, `timezone=UTC`, `cell_selection=nearest`. Variables: `shortwave_radiation` (obligatoria) y `cloud_cover` (existe en esta API; si para algún modelo viene vacía, regístralo y sigue). Las medias horarias representan la hora precedente: el total del día D es la suma de las marcas 01 UTC de D a 00 UTC de D+1, como en los trabajos anteriores.

**Cuota**: Open-Meteo acepta **múltiples coordenadas en una petición** (`latitude=a,b,c&longitude=x,y,z`, hasta 1000; devuelve un array). Pide **todas las estaciones en la misma petición por run**: ~150 días × 2 ciclos × 2 modelos ≈ **600 peticiones**. Cada petición se contabiliza aproximadamente como una llamada **por ubicación**, así que espera del orden de **600 × 28 ≈ 17.000 llamadas contadas**. Límites gratuitos: 600/min, 5.000/hora, **10.000/día**. Es decir, **dos días de descarga**. Mide el consumo real en las primeras 20 peticiones y reparte. No reduzcas estaciones por cuota; reparte en días.

Guarda cada respuesta íntegra con su SHA-256 y la URL. Registra los runs no disponibles como tales, sin sustituirlos por otro ciclo.

### 6.5 Enlace con el trabajo anterior (secundario, sin descarga nueva)

Con los datos semihorarios que **ya tienes** de las estaciones de trabajos previos, repite el análisis principal restringido a 06-18 UTC en la parte de la ventana que se solape, para comprobar que el veredicto no depende de agregar a día completo. No descargues datos semihorarios nuevos.

## 7. Análisis

### 7.1 Métrica

Para cada estación *i*, día *d* y serie *s*: `e = pronóstico − observación` en Wh/m².

Métrica primaria: **MAE relativo**, `MAE_s / media(observación)`, en %. Hace comparables estaciones con niveles de radiación muy distintos.

Comparación entre dos series: **reducción relativa de MAE**, `(MAE_A − MAE_B) / MAE_A × 100`. Positivo = B mejor que A.

### 7.2 Hipótesis

**Primarias** (dos, con corrección de multiplicidad), sobre la ventana primaria:
- **H1**: reducción de MAE de IFS_00 → IFS_06 mayor que cero.
- **H2**: reducción de MAE de IFS_00 → AIFS_00 mayor que cero.

**Secundarias preespecificadas** (se reportan todas, marcadas como exploratorias):
- AIFS_00 → AIFS_06; IFS_06 → AIFS_06.
- Las cuatro comparaciones en la ventana secundaria (versión anterior de los modelos).
- Las cuatro restringidas a 06-18 UTC donde haya semihorario (6.5).

**p-valor**: bootstrap bilateral, `p = 2 · min(fracción de réplicas con efecto ≤ 0, fracción con efecto ≥ 0)`, acotado en [0, 1].

**Multiplicidad**: Holm-Bonferroni sobre los dos p-valores primarios, α = 0,05. Si prefieres consistencia con el pre-registro del laboratorio anterior, Benjamini-Yekutieli con familia de tamaño 2; declara cuál en la especificación congelada.

### 7.3 Incertidumbre estadística

Bootstrap **por días completos**: cada réplica remuestrea días del calendario y toma **todas las estaciones de ese día a la vez**. Obligatorio: las estaciones comparten el estado sinóptico diario, y tratar estación-días como independientes infla la confianza.

Bloques circulares de longitud **1, 7 y 14 días** (no 30: con ~112 días no hay bloques suficientes); **10.000 réplicas**; semilla fija (20260914). Percentiles del 95 %. Reporta los tres; no elijas el más favorable.

### 7.4 Análisis de sensibilidad al error del sensor — el núcleo de este encargo

La observación de cada estación lleva un factor de escala desconocido por calibración, suciedad y deriva: `obs_medida = k_i · obs_real`, con `k_i` del orden de ±5 %.

**(a) Determinista.** Repite el análisis completo con `k` global en {0,95; 1,00; 1,05} (observación dividida por `k`). Un resultado se declara **robusto al instrumento** únicamente si el signo del efecto y la conclusión del intervalo se mantienen en los tres casos.

**(b) Monte Carlo por estación.** Sortea `k_i ~ Uniforme(0,95; 1,05)` **independiente para cada estación**, divide la observación de esa estación por `k_i`, recalcula el efecto puntual. Repite **1.000 veces** con semilla fija. Reporta la distribución del efecto y **la fracción de sorteos en que el veredicto se mantiene**. Este es el resultado principal de robustez: un efecto que sobrevive en el 99 % de los sorteos es sólido; uno que sobrevive en el 60 % no lo es.

### 7.5 Estratificación preespecificada (exploratoria)

Reporta el efecto principal desglosado por: estación individual; mes (mayo, junio, julio, agosto); tercil de `cloud_cover` medio diurno pronosticado; y latitud (norte/centro/sur en terciles de latitud de las estaciones). Sección marcada como exploratoria, sin corrección. **No la uses para reformular las hipótesis primarias.**

### 7.6 Verificación

Como en los trabajos anteriores: recálculo independiente con aritmética decimal, pruebas automatizadas del método, verificación del paquete sin conexión.

## 8. Criterio de terminación — explícito

Este encargo **termina** cuando se entregue el informe con: veredicto de H1 y H2, intervalos, análisis de sensibilidad al instrumento, secundarias y limitaciones.

Termina **igual de bien** si no hay efecto, si el efecto no sobrevive al error del instrumento, o si concluyes que el diseño no puede responder la pregunta.

**No propongas una fase siguiente.** Si crees que hay una continuación obvia, escríbela en una línea al final bajo "posible continuación, no ejecutada" y nada más.

## 9. Estructura de salida

Entrega en `outputs/latencia_pronosticos/medicion_escala/`:

```
metodo_fijado.json          especificación congelada + SHA-256
estaciones.json             catálogo, selección, coordenadas, distancias a centro de celda
resultados.json             métricas, intervalos, sensibilidad, estratos, ambas ventanas
informe.md                  el informe (estructura abajo)
figura_principal.png        efecto por estación con intervalo, ventana primaria
figura_sensibilidad.png     distribución Monte Carlo del efecto
datos_y_analisis.zip        paquete reproducible con recibos y código congelado
verificacion.json           recálculo independiente y pruebas
```

Informe en español, con esta estructura:

1. **Resultado en una frase**, en negrita, primero. Incluye la ventana y su limitación ("mayo–agosto 2026, sin invierno"). Si es nulo, dilo en esa frase.
2. **Qué se decidió antes de medir**: fechas, hashes, regla de selección, hipótesis, y el motivo de la ventana (archivo disponible, cambio de versión).
3. **Muestra**: tabla de estaciones con días válidos por ventana, exclusiones y motivo.
4. **Resultado primario**: H1 y H2, efecto puntual, los tres intervalos, p bootstrap, veredicto tras Holm.
5. **Robustez al instrumento**: tabla del determinista y fracción de supervivencia del Monte Carlo. **Si un primario no sobrevive, va en el titular.**
6. **Secundarias y estratos**, marcados como exploratorios, todos, incluidos los desfavorables, y la ventana secundaria.
7. **Limitaciones**: ventana corta y sin invierno; cambio de versión; y cualquier cosa que por D4 no se investiga.
8. **Reproducción**: hashes y cómo verificar.

Ejemplo del tono del titular:

> **En 27 estaciones y 108 días de mayo a agosto de 2026, actualizar del ciclo 00 al 06 UTC reduce el MAE de IFS un X,X % (IC95 [a, b]), y el efecto sobrevive en el 9X % de los sorteos de error instrumental. No hay datos de invierno.**

o bien

> **Ninguna de las dos hipótesis primarias supera la corrección de multiplicidad en la ventana de mayo a agosto de 2026. El efecto de la actualización es de X,X % con intervalo que incluye cero.**

## 10. Lo que NO debes hacer

- No validar sensores, pedir certificados ni descargar satélite.
- No entrenar ninguna corrección de sesgo ni evaluar su beneficio.
- No medir magnitudes absolutas del error del modelo como resultado principal.
- No estimar euros, buscar comprador ni evaluar viabilidad comercial.
- No cambiar rejilla, estaciones, ventanas ni hipótesis después de ver datos.
- No mezclar las dos ventanas (dos versiones de modelo) en un solo resultado.
- No añadir métodos ni subconjuntos para rescatar un resultado nulo.
- No proponer el siguiente experimento.

## 11. Incertidumbre y permiso para parar

Tienes permiso explícito para:

- **Decir "no lo sé"** y marcar un dato como no verificado en vez de rellenarlo.
- **Parar y reportar** si descubres que el diseño no puede responder la pregunta con estos datos. Explica por qué, entrega lo que tengas, y no improvises un diseño alternativo.
- **Contradecir este encargo** si encuentras un error en él — la versión anterior ya tenía uno (la ventana). Si algo está mal planteado, dilo antes de ejecutarlo, con el motivo.
- **Reportar un resultado nulo como resultado**, sin adornarlo.

Antes de empezar a descargar, escribe en dos o tres frases cómo has interpretado el encargo y qué vas a hacer, para que pueda corregirte si te has desviado.
