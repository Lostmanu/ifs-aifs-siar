# Trazabilidad y guía de comprobación del cierre

Documentación añadida al publicar, sin cambiar datos ni método. La tabla JSON conserva valores sin redondear y punteros RFC 6901.

**Versiones de las comprobaciones.** Los 60.602 valores y las 16 pruebas de la tabla histórica corresponden al cierre original. La cadena actual incorpora 61.383 valores y 20 pruebas; el [registro del 23-09-2026](revision_20260923/informe.md) distingue la reproducción actual de los controles conservados.

## Diseño, pares y agregación

La [especificación congelada](../estudio/metodo_fijado.json) y su [recibo](../estudio/state/metodo_fijado_recibo.json) fijan la selección por rejilla 1,5°, las 34 estaciones, los criterios de validez y las ventanas. El [listado de estaciones](../estudio/outputs/estaciones.json) incluye coordenadas, cobertura y exclusiones. La primaria son 110 días objetivo, 14-may–31-ago-2026; la secundaria son 40 días, 3-abr–12-may, y no se mezclan versiones. El 13 de mayo se excluye por ser mixto.

Las pasadas son D−1 00 o 06 UTC. `shortwave_radiation` es una media de la hora precedente. Se suman las 24 marcas D 01 UTC … D+1 00 UTC: horizontes +25…+48 h para 00 UTC y +19…+42 h para 06 UTC. Las observaciones SiAR MJ/m² se convierten a Wh/m² con 1000/3,6. Ver `total_diario` en [metodo.py](../estudio/code/metodo.py) y la sección 3 del [informe](../estudio/outputs/informe.md) para las cinco pasadas ausentes. El [estado de descargas](../estudio/state/descarga_pronosticos.json) identifica las peticiones individuales.

Para cada estación s se obtiene μ_s = media de todas las observaciones válidas de la ventana. Para cada contraste h se crea M_h = {(s,d): O, F_A y F_B son válidos}. El denominador μ_s no se restringe a M_h. Los dos modelos de un contraste se puntúan sobre exactamente los mismos pares.

```
MAE_rel(A,h) = suma[(s,d) en M_h] |F_A(s,d) − O(s,d)| / μ_s / |M_h|
mejora(h) = 100 × (MAE_rel(A,h) − MAE_rel(B,h)) / MAE_rel(A,h)
```

Cada par válido pesa igual después de normalizar por estación. Por tanto, el peso agregado de una estación es proporcional a sus pares válidos: **no es una media con idéntico peso de estación**. Las medias de normalización quedan fijas en el bootstrap de cada escenario. Los huecos se conservan como `null` en el [panel](../estudio/outputs/panel_analisis.json). La implementación usa cero solo en sumas enmascaradas y excluye esos pares del denominador; no imputa radiación cero.

## Bootstrap e inferencia

Se remuestrean **días completos con todas sus estaciones y ambos pronósticos emparejados**. La dependencia contemporánea entre estaciones se conserva. Para L = 1, 7, 14 se sortean comienzos uniformes de bloques circulares, se concatenan ceil(110/L) bloques y se truncan a 110 días. Se generan 10.000 réplicas, semilla 20260914, y se calcula el cociente de MAE en cada réplica. Intervalos percentiles 2,5 y 97,5. Ver `pesos_bootstrap`, `comparar` y `p_bilateral` en [metodo.py](../estudio/code/metodo.py).

El contraste bilateral implementado usa p = min(1, 2 × min(fracción de réplicas ≤ 0, fracción ≥ 0)), con igualdad de MAE como nula. La hipótesis de mejora se apoya si el efecto es positivo y se rechaza la nula tras Holm. Es el procedimiento bootstrap congelado; no un test exacto libre de supuestos. Un p guardado como 0 significa que ninguna réplica cayó en la cola contraria: no implica probabilidad poblacional cero; con 10.000 réplicas se comunica p < 0,0002.

**Familia Holm:** H1 y H2, por separado dentro de cada L, α = 0,05; no se aplica una única corrección a seis pruebas. Se muestran los tres esquemas sin seleccionar uno. S1, S2, estratos, ventana secundaria y anexo posterior son exploratorios. La validez de Holm no elimina las limitaciones de los bloques ni la sensibilidad de escala.

| L (días) | Hipótesis | p bilateral guardado | p ajustado Holm guardado | Rechaza a 0,05 |
|---:|---|---:|---:|---|
| 1 | H1 | 0.0042 | 0.0042 | sí |
| 1 | H2 | 0.0000 | 0.0000 | sí |
| 7 | H1 | 0.0006 | 0.0006 | sí |
| 7 | H2 | 0.0000 | 0.0000 | sí |
| 14 | H1 | 0.0000 | 0.0000 | sí |
| 14 | H2 | 0.0000 | 0.0000 | sí |

Los ceros de esta tabla son la representación exacta del archivo, con la limitación de resolución indicada arriba. Los intervalos no se interpretan como robustez frente a cualquier dependencia o no estacionariedad.

## Sensibilidad y diagnóstico posterior

El determinista usa k común en {0,95; 1; 1,05}; reemplaza O por O/k y recalcula también μ_s. El criterio congelado exige signo e interpretación del intervalo invariantes a los tres k para cada longitud. El Monte Carlo independiente usa 1.000 vectores de 34 factores uniformes U(0,95; 1,05), uno por estación, semilla 20260915. Se declaran por separado supervivencia de signo y de signo más intervalo. Son supuestos, no distribuciones estimadas del error de red.

Los cruces de k son posteriores: rejilla 0,855…1,10 con paso 0,0025, búsqueda de cambios de signo e interpolación lineal entre nodos. La precisión reportada no es un intervalo de incertidumbre del k real. El cambio relativo de observación es 100 × (1/k − 1). Código: [diagnostico_posterior.py](../estudio/code/diagnostico_posterior.py); campos `cruce_k_comun`, `curva`, `k_cruce` y `discrepancia_equivalente_pct` del diagnóstico. No se usaron para elegir estaciones, fechas ni método.

## Cifras científicas y verificaciones históricas del cierre

Los valores se muestran sin reinterpretarlos; los porcentajes de supervivencia almacenados son fracciones. [Versión estructurada con todas las filas](cifras_fuentes.json).

| Cifra | Valor almacenado | Archivo | JSON Pointer |
|---|---|---|---|
| Estaciones seleccionadas | `34` | [estudio/outputs/estaciones.json](../estudio/outputs/estaciones.json) | `/n_seleccionadas` |
| Días calendario primarios | `110` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/n_dias_calendario` |
| H1: pares | `3664` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H1/n_estacion_dias` |
| H1: efecto, L7 | `1.4710096441072182` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H1/por_bloque/7/efecto` |
| H1: ic95, L7 | `[0.6897371163822766,2.2619991392315275]` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H1/por_bloque/7/ic95` |
| H1: mae_a, L7 | `0.08133922801563157` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H1/por_bloque/7/mae_a` |
| H1: mae_b, L7 | `0.08014272012707926` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H1/por_bloque/7/mae_b` |
| H1: efecto, k=0,95, L7 | `0.44444461628801063` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/sensibilidad_determinista/por_k/0.95/comparaciones/H1/7/efecto` |
| H1: ic95, k=0,95, L7 | `[-0.5833013437325135,1.3925883896050673]` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/sensibilidad_determinista/por_k/0.95/comparaciones/H1/7/ic95` |
| H1: signo en Monte Carlo | `1.0` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/sensibilidad_montecarlo/comparaciones/H1/supervivencia_nivel1_signo` |
| H1: cruce de k (posterior) | `0.9316659952065517` | [estudio/datos/diagnostico_posterior.json](../estudio/datos/diagnostico_posterior.json) | `/cruce_k_comun/H1/k_cruce` |
| H1: cambio equivalente de observación (posterior) | `7.334603296141395` | [estudio/datos/diagnostico_posterior.json](../estudio/datos/diagnostico_posterior.json) | `/cruce_k_comun/H1/discrepancia_equivalente_pct` |
| H2: pares | `3697` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H2/n_estacion_dias` |
| H2: efecto, L7 | `7.570369778548527` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H2/por_bloque/7/efecto` |
| H2: ic95, L7 | `[4.599204348009697,10.484376539259713]` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H2/por_bloque/7/ic95` |
| H2: mae_a, L7 | `0.08152012562567407` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H2/por_bloque/7/mae_a` |
| H2: mae_b, L7 | `0.07534875067187324` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/comparaciones/H2/por_bloque/7/mae_b` |
| H2: efecto, k=0,95, L7 | `-5.643853232009067` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/sensibilidad_determinista/por_k/0.95/comparaciones/H2/7/efecto` |
| H2: ic95, k=0,95, L7 | `[-10.084729375477416,-1.3311552889146272]` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/sensibilidad_determinista/por_k/0.95/comparaciones/H2/7/ic95` |
| H2: signo en Monte Carlo | `1.0` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/sensibilidad_montecarlo/comparaciones/H2/supervivencia_nivel1_signo` |
| H2: cruce de k (posterior) | `0.9747619834991298` | [estudio/datos/diagnostico_posterior.json](../estudio/datos/diagnostico_posterior.json) | `/cruce_k_comun/H2/k_cruce` |
| H2: cambio equivalente de observación (posterior) | `2.589146574045964` | [estudio/datos/diagnostico_posterior.json](../estudio/datos/diagnostico_posterior.json) | `/cruce_k_comun/H2/discrepancia_equivalente_pct` |
| Réplicas | `10000` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/replicas` |
| Sorteos | `1000` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/sorteos` |
| Números reproducidos | `60602` | [estudio/outputs/verificacion_entrega.json](../estudio/outputs/verificacion_entrega.json) | `/reproduccion_independiente/valores_comparados` |
| Diferencia máxima | `0.0` | [estudio/outputs/verificacion_entrega.json](../estudio/outputs/verificacion_entrega.json) | `/reproduccion_independiente/diferencia_maxima` |
| Recibos comprobados | `708` | [docs/verificacion_metodo_original.json](../docs/verificacion_metodo_original.json) | `/recibos/comprobados` |
| Pruebas del método | `16` | [docs/verificacion_metodo_original.json](../docs/verificacion_metodo_original.json) | `/pruebas/ejecutadas` |
| Archivos anteriores intactos | `4832` | [estudio/outputs/verificacion_entrega.json](../estudio/outputs/verificacion_entrega.json) | `/originales/archivos_comprobados` |
| H1: Holm L=1 | `{"p":0.0042,"p_ajustado":0.0042,"rechaza":true,"efecto":1.4710096441072182,"apoyada":true}` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/holm/1/H1` |
| H2: Holm L=1 | `{"p":0.0,"p_ajustado":0.0,"rechaza":true,"efecto":7.570369778548527,"apoyada":true}` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/holm/1/H2` |
| H1: Holm L=7 | `{"p":0.0006,"p_ajustado":0.0006,"rechaza":true,"efecto":1.4710096441072182,"apoyada":true}` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/holm/7/H1` |
| H2: Holm L=7 | `{"p":0.0,"p_ajustado":0.0,"rechaza":true,"efecto":7.570369778548527,"apoyada":true}` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/holm/7/H2` |
| H1: Holm L=14 | `{"p":0.0,"p_ajustado":0.0,"rechaza":true,"efecto":1.4710096441072182,"apoyada":true}` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/holm/14/H1` |
| H2: Holm L=14 | `{"p":0.0,"p_ajustado":0.0,"rechaza":true,"efecto":7.570369778548527,"apoyada":true}` | [estudio/outputs/resultados.json](../estudio/outputs/resultados.json) | `/primaria/holm/14/H2` |

## Entorno, integridad y límites de la comprobación

El registro de reproducción especifica Python 3.12.14, NumPy 2.3.5 y Windows 11; la comparación permite tolerancias absolutas 1e−10 y relativas 1e−11, pero la ejecución registrada obtuvo diferencia exactamente cero. La identidad por hash de los cuatro motores describe v1.0.0 y v1.0.1: **v1.0.2 modifica `analizar.py`** para corregir rutas y abortar ante el fallo del enlace 06–18 UTC. Las cifras y la especificación se conservan. Los parches de cierre están en `estudio/revision/*.diff` y las correcciones posteriores en [CHANGELOG.md](../CHANGELOG.md). El ZIP guarda los hashes de cada entrada en `manifest_portable_sha256.json`; su propio SHA-256 y los históricos están en [paquetes_release.json](paquetes_release.json).

Para un control rápido: leer esta página y la tabla de estaciones; inspeccionar `sumas` y `analizar_ventana` en `analizar.py`; inspeccionar las cuatro funciones citadas de `metodo.py`; extraer el ZIP de cierre y ejecutar su lanzador. El recálculo numérico no constituye una auditoría física de los datos ni valida una interpretación causal. La auditoría textual recibida no inspeccionó estos archivos; se conserva su alcance en [AUDITORIA.md](AUDITORIA.md).

## Extensión posterior incorporada en v1.0.1

La nueva [sensibilidad secundaria](../estudio/datos/sensibilidad_secundaria_posterior.json) se calcula desde el panel existente con `sensibilidad_secundaria_posterior.py`. Cada ventana conserva sus propios pares y medias. La rejilla ampliada 0,80–1,10, paso 0,0025, permite comprobar los cruces aportados por la objeción; se define después del resultado y no sustituye la rejilla ni el criterio originales. Los intervalos nuevos conservan todas las estaciones de cada día y usan el mismo método de bloques y semilla, sin corrección de Holm para esta extensión exploratoria.

Los datos de Galicia y sus dos contrastes se extraen sin recalcularlos de la auditoría previa; [contexto_referencia_cierre.json](../estudio/datos/contexto_referencia_cierre.json) conserva hashes, índices y punteros. La descomposición restituida del MSE es **global**: media del residuo al cuadrado más varianza, no una descomposición por estación ni del MAE. Las cifras originales del cierre siguen en la tabla anterior; los nuevos punteros se incorporan a `cifras_fuentes.json`.
