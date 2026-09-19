"""Fase 0: escribe metodo_fijado.json (especificación congelada), su SHA-256 y la marca temporal.

Se ejecuta UNA vez, antes de cualquier descarga. No lee datos meteorológicos.
"""
from comun import *
import sys

sel = load(STATE / 'seleccion_rejilla_out.json')
cells = [c for c in sel['cells'] if c['selected']]
by_code = {s['code']: s for s in sel['stations_active']}
canarias = sel['canarias_alphabetical'][0]
ordered = []
for c in cells:
    s = by_code[c['selected']]
    ordered.append({
        'orden': len(ordered), 'codigo': s['code'], 'nombre': s['name'], 'id_formulario': s.get('id'), 'region_formulario': s.get('region'),
        'centro_zonal': s['zone_center'], 'provincia': s['province'], 'propiedad': s['owner'], 'fecha_instalacion': s['installed'],
        'utm': {'huso': s['utm_zone'], 'x': s['utmx'], 'y': s['utmy'], 'crs': f'ETRS89 / UTM huso {s["utm_zone"]} (EPSG:258{s["utm_zone"]:02d})'},
        'latitud': round(s['latitude'], 9), 'longitud': round(s['longitude'], 9),
        'celda': {'centro_lat': c['center'][0], 'centro_lon': c['center'][1], 'estaciones_en_celda': c['n_stations'],
                  'distancia_km': c['distance_km'], 'segunda_mas_proxima': c['runner_up'], 'distancia_segunda_km': c['runner_up_distance_km']},
    })
s = by_code[canarias['code']]
ordered.append({
    'orden': len(ordered), 'codigo': s['code'], 'nombre': s['name'], 'id_formulario': s.get('id'), 'region_formulario': s.get('region'),
    'centro_zonal': s['zone_center'], 'provincia': s['province'], 'propiedad': s['owner'], 'fecha_instalacion': s['installed'],
    'utm': {'huso': s['utm_zone'], 'x': s['utmx'], 'y': s['utmy'], 'crs': f'ETRS89 / UTM huso {s["utm_zone"]} (EPSG:258{s["utm_zone"]:02d})'},
    'latitud': round(s['latitude'], 9), 'longitud': round(s['longitude'], 9),
    'celda': None, 'motivo': 'Canarias: primera estación activa del catálogo por orden alfabético de nombre (casefold), regla 6.1.3 del encargo',
})

spec = {
    'version': '1.0',
    'titulo': 'Medición a escala del valor de la actualización (IFS 00→06 UTC) y de IA frente a física (AIFS vs IFS) sobre radiación global diaria, estaciones SiAR, 2026',
    'encargo': {
        'fichero': 'encargo_v2.md (copia de PROMPT_CODEX_medicion_escala.md, versión 2, 14-sep-2026)',
        'sha256': sha256_file(BASE / 'encargo_v2.md'),
    },
    'interpretacion_en_tres_frases': (
        'Se ejecuta una medición preespecificada y relativa: dos pronósticos distintos contra la misma observación diaria de SiAR, '
        'en 33 estaciones peninsulares/baleares elegidas por rejilla más una canaria, en una ventana de una sola versión de modelo (pasadas desde 2026-05-12 06 UTC) '
        'y una ventana secundaria anterior, con incertidumbre por bloques de días y sensibilidad explícita al error multiplicativo del sensor. '
        'El resultado se reporta sea cual sea, sin fase siguiente.'
    ),
    'correcciones_y_decisiones_previas_a_los_datos': [
        {'id': 'C1', 'tema': 'Frontera de las ventanas', 'encargo': 'Ventana primaria 2026-05-12 a 2026-08-31; secundaria 2026-04-02 a 2026-05-11.',
         'problema': 'El cambio de versión (IFS 50r1 y AIFS Single v2) ocurre en la PASADA de 2026-05-12 06 UTC. El día objetivo D usa las pasadas de D−1 a las 00 y 06 UTC. '
                     'Con D=2026-05-12 ambas pasadas (11-may) son de la versión anterior; con D=2026-05-13 la pasada 00 es antigua y la 06 es nueva (día mixto). '
                     'Definir las ventanas por día objetivo mezclaría versiones, cosa que el encargo prohíbe.',
         'decision': 'Las ventanas se definen por la hora de inicialización de las pasadas: primaria = días objetivo cuyas dos pasadas de D−1 son ≥ 2026-05-12T06Z → D ∈ [2026-05-14, 2026-08-31] (110 días); '
                     'secundaria = días objetivo cuyas dos pasadas de D−1 son < 2026-05-12T06Z y están archivadas → D ∈ [2026-04-03, 2026-05-12] (40 días si existe la pasada de 2026-04-02 06 UTC; si no, empieza el 2026-04-04). '
                     'El día 2026-05-13 se excluye de ambas ventanas por mixto. Se descargan las pasadas 00 y 06 UTC del 2026-04-02 al 2026-08-30 (151 días de pasada).',
         'fuentes': ['https://confluence.ecmwf.int/display/FCST/Implementation+of+IFS+Cycle+50r1 («IFS Cycle 50r1 was successfully implemented on 12 May 2026 from the 06 UTC run»)',
                     'https://confluence.ecmwf.int/spaces/UDOC/pages/599165907/AIFS+Version+History (AIFS Single v2: 12 May 2026; v1.1: 27 Aug 2025)',
                     'https://open-meteo.com/en/docs/single-runs-api («From May 12, 2026 06 UTC, runs use the updated IFS Cycle 50R1»; «Archival runs are available from 2nd of April 2026 for most models»)']},
        {'id': 'C2', 'tema': 'Plazos +24…+47 / +18…+41', 'problema': 'Los plazos de la tabla 6.4 están en convención de hora inicial, pero el encargo define el total diario por marcas de hora final (01 UTC de D a 00 UTC de D+1), que corresponden a +25…+48 (pasada 00) y +19…+42 (pasada 06).',
         'decision': 'Manda la definición por marcas de tiempo: total del día D = suma de las 24 medias horarias precedentes con marcas D 01:00 … D+1 00:00 UTC. Los plazos se documentan como +25…+48 h y +19…+42 h.'},
        {'id': 'C3', 'tema': 'Factor MJ/m² → Wh/m²', 'decision': 'Se usa el valor exacto 1000/3,6 = 277,777… Wh/m² por MJ/m² (el 277,78 del encargo difiere en 8·10⁻⁶ relativo; es irrelevante para el resultado, pero el cálculo decimal independiente exige una constante exacta).'},
        {'id': 'C4', 'tema': 'Tamaño de la muestra', 'observacion': 'La regla de rejilla produce 33 celdas con estación (no 25-30) + 1 canaria = 34 estaciones. No hay estaciones SiAR en Asturias, Cantabria, País Vasco, La Rioja ni Cataluña (redes propias), y solo 4 activas en Galicia; el mapa queda sesgado al sur, centro y este. Se acepta tal cual: la regla es la del encargo.'},
        {'id': 'C5', 'tema': 'Elegibilidad por instalación cubierta', 'decision': 'Se excluyen de la elegibilidad las estaciones cuyo nombre en el catálogo contiene «Invernadero» o «(malla)» (medición bajo cubierta, no radiación global de cielo abierto). Aplicado ANTES de ver datos; no cambia ninguna selección (ninguna de las 34 lo es; la primera canaria por alfabeto, TF153 «Adeje - Hoya Grande Aire Libre», es de aire libre).'},
        {'id': 'C6', 'tema': 'Estado de la API al congelar', 'observacion': 'El 2026-09-14 entre 13:45 y 14:36 UTC la Single Runs API devolvió timeouts (40-150 s), HTTP 500 «Something went wrong», HTTP 429 «Too many concurrent requests» y HTTP 502 nginx, tanto desde esta máquina como desde una red externa; la Previous Runs API también agotaba el tiempo; la Forecast API normal respondía en 0,4 s. '
                        'Es una caída de los servicios de archivo del proveedor. La descarga se diseña reanudable, estrictamente secuencial (una petición en vuelo), con espera exponencial y sin plazo: si el archivo no vuelve, el encargo termina como «no se puede medir» con lo descargado.'},
        {'id': 'C7', 'tema': 'Primera pasada archivada', 'observacion': 'Documentación del proveedor y sonda de Codex (2026-09-14 08:17 UTC, HTTP 200 para ambos modelos con run=2026-04-02T00:00; HTTP 400 «model run is not available» para 2026-04-01T00:00 en la sonda propia de las 14:17 UTC). '
                        'La existencia de la pasada de 2026-04-02 06 UTC no se ha podido verificar antes de congelar por la caída de la API: la regla de la ventana secundaria la absorbe (empieza en el primer día objetivo con las cuatro pasadas archivadas).'},
    ],
    'hipotesis': {
        'primarias': {
            'H1': 'Valor de la actualización: reducción relativa de MAE de IFS_00 → IFS_06 mayor que cero, ventana primaria.',
            'H2': 'IA frente a física: reducción relativa de MAE de IFS_00 → AIFS_00 mayor que cero, ventana primaria.',
        },
        'secundarias_exploratorias': [
            'AIFS_00 → AIFS_06 (ventana primaria)', 'IFS_06 → AIFS_06 (ventana primaria)',
            'Las cuatro comparaciones (IFS_00→IFS_06, IFS_00→AIFS_00, AIFS_00→AIFS_06, IFS_06→AIFS_06) en la ventana secundaria',
            'Las cuatro comparaciones restringidas a 06-18 UTC en las estaciones con semihorario existente (sección enlace_06_18)',
        ],
        'p_valor': 'Bootstrap bilateral por percentiles: p = 2·min(fracción de réplicas con efecto ≤ 0, fracción con efecto ≥ 0), acotado a [0, 1].',
        'multiplicidad': 'Holm-Bonferroni sobre los dos p-valores primarios (α = 0,05): el menor se compara con 0,025 y, si supera, el mayor con 0,05. Se declara Holm y NO Benjamini-Yekutieli.',
        'veredicto': 'Una hipótesis primaria se declara APOYADA si su p ajustado por Holm es < 0,05 Y el efecto puntual es > 0. En cualquier otro caso, NO APOYADA (incluido efecto negativo significativo, que se reporta como tal).',
        'p_valor_por_bloque': 'Se calculan p e intervalos para los tres largos de bloque. Holm se aplica a cada largo por separado y se reportan los tres; el titular exige el mismo veredicto en los tres largos para decir «apoyada»; si difieren, el titular dice «depende del largo de bloque» y no se elige ninguno.',
    },
    'ventanas': {
        'cambio_de_version': {'instante': '2026-05-12T06:00Z', 'ifs': '49r1 → 50r1', 'aifs': 'Single v1.1 → Single v2'},
        'primaria': {'dias_objetivo': ['2026-05-14', '2026-08-31'], 'n_dias': 110, 'pasadas': 'D−1 00 y 06 UTC, todas de la versión nueva', 'meses_para_estratos': ['2026-05 (14-31)', '2026-06', '2026-07', '2026-08']},
        'secundaria': {'dias_objetivo': ['2026-04-03', '2026-05-12'], 'n_dias_max': 40, 'pasadas': 'D−1 00 y 06 UTC, todas de la versión anterior', 'inicio_ajustable': 'primer día objetivo con las cuatro pasadas archivadas para ambos modelos'},
        'excluido': {'2026-05-13': 'día mixto: pasada 00 UTC antigua y 06 UTC nueva'},
        'pasadas_a_descargar': {'primera': '2026-04-02T00:00Z', 'ultima': '2026-08-30T06:00Z', 'ciclos': ['00', '06'], 'modelos': ['ecmwf_ifs025', 'ecmwf_aifs025_single'], 'n_peticiones': 151 * 2 * 2},
        'prohibido': 'Mezclar ventanas en un mismo resultado.',
    },
    'estaciones': {
        'catalogo': {'url': 'https://servicio.mapa.gob.es/siarweb/fichaEstacion/masInfo/coordenadasEstacion', 'descargado_utc': '2026-09-14T07:41:46Z (por Codex; copia raw/catalogo_siar_20260914T0741Z.csv)',
                     'sha256': sha256_file(RAW / 'catalogo_siar_20260914T0741Z.csv'), 'filas': 635, 'activas': 520, 'codificacion': 'cp1252, separador ;'},
        'elegibilidad': ['Estado = Activa en el catálogo', 'Nombre sin «Invernadero» ni «(malla)» (C5)', 'Todas las estaciones SiAR llevan piranómetro (radiación global); se registra el modelo desde la ficha oficial, sin validarlo (D1)'],
        'coordenadas': 'UTM ETRS89 del catálogo (huso 30 península/Baleares, 28 Canarias) → geográficas por inversa de Mercator transversa (series de Karney hasta n⁶, GRS80). Verificado frente a pyproj (EPSG:25830→4326) en 7 estaciones del trabajo previo: diferencia máxima 2,5·10⁻⁶ mm.',
        'rejilla': {'celdas_lat': [36.0, 37.5, 39.0, 40.5, 42.0, 43.5], 'celdas_lon': [-9.0, -7.5, -6.0, -4.5, -3.0, -1.5, 0.0, 1.5, 3.0], 'semiancho_grados': 0.75,
                    'pertenencia': '|lat − centro_lat| ≤ 0,75 y |lon − centro_lon| ≤ 0,75 (huso 30 solamente)', 'distancia': 'haversine, R = 6371,0088 km, al centro de celda; empate por código (no ocurre)',
                    'celdas_con_estacion': len(cells), 'celdas_sin_estacion': 54 - len(cells)},
        'canarias': 'Una estación: la primera activa de Centro Zonal = Canarias por orden alfabético de nombre (casefold). Fuera de rejilla; se reporta como una estación más y en el estrato de latitud que le corresponda.',
        'regla_de_exclusion_posterior': 'Se excluye (sin sustituir) toda estación con menos del 80 % de días con observación válida en la ventana primaria (< 88 de 110). Los pronósticos ausentes NO cuentan contra la estación; se contabilizan aparte.',
        'orden_fijo_para_peticiones': 'El campo «orden» fija la posición en las listas latitude/longitude de cada petición; el análisis verifica la correspondencia por location_id de la respuesta.',
        'seleccion': ordered,
    },
    'observacion': {
        'fuente': 'SiAR, consulta pública web (https://servicio.mapa.gob.es/siarweb/consultaDatos), datos DIARIOS (tipoCalculo=2), variable «Radiación (MJ/m2)», una consulta por estación del 2026-04-01 al 2026-09-01.',
        'convencion_horaria': 'Día natural 00-24 UTC según la documentación de SiAR (manual sep-2025 pp. 21 y 24: horas mostradas en UTC desde abril de 2014), como en los trabajos previos. El total diario publicado se acepta tal cual; no se reconstruye desde semihorarios salvo en la sección enlace_06_18.',
        'conversion': 'Wh/m² = MJ/m² × 1000/3,6 (exacto).',
        'validez_dia': [
            'Fecha única por estación (duplicados ⇒ el día se excluye)',
            'Valor numérico finito publicado; un valor vacío/nulo/no numérico NO es válido',
            'Rango físico: 0,03 ≤ H/H0 ≤ 1,00, con H0 = irradiación extraterrestre diaria sobre superficie horizontal (FAO-56, ec. 21; Gsc = 0,0820 MJ m⁻² min⁻¹) para la latitud de la estación y el día del año',
            'El indicador tieneDatos del proveedor se registra pero NO se usa como filtro (sin definición documentada; decisión heredada de la réplica)',
        ],
        'imputacion': 'Ninguna. Un día no válido se excluye en esa estación.',
    },
    'pronostico': {
        'endpoint': 'https://single-runs-api.open-meteo.com/v1/forecast',
        'parametros': {'latitude/longitude': 'las 34 estaciones en el orden fijo, en la misma petición', 'models': 'uno por petición (ecmwf_ifs025 o ecmwf_aifs025_single)', 'hourly': 'shortwave_radiation,cloud_cover',
                       'run': 'YYYY-MM-DDT00:00 o T06:00 (UTC)', 'forecast_days': 3, 'timezone': 'UTC', 'cell_selection': 'nearest'},
        'series': {'IFS_00': ['ecmwf_ifs025', 'D−1 00 UTC', 'marcas D 01:00…D+1 00:00 = plazos +25…+48 h'], 'IFS_06': ['ecmwf_ifs025', 'D−1 06 UTC', 'plazos +19…+42 h'],
                   'AIFS_00': ['ecmwf_aifs025_single', 'D−1 00 UTC', '+25…+48 h'], 'AIFS_06': ['ecmwf_aifs025_single', 'D−1 06 UTC', '+19…+42 h']},
        'agregacion': 'Las medias horarias representan la hora precedente (documentación Single Runs). Total del día D (Wh/m²) = suma de los 24 valores (W/m²) con marcas D 01:00 … D+1 00:00 UTC.',
        'validez': 'Los 24 valores presentes, finitos y en [0, 1500] W/m²; si falta uno, el día-serie-estación es ausente (sin imputar).',
        'nubosidad': 'cloud_cover medio diurno = media simple de las 13 marcas D 06:00 … 18:00 UTC de la serie IFS_00 (si IFS no la trae, AIFS_00; si ninguna, el estrato no se calcula). Requiere las 13 presentes y en [0, 100].',
        'pasadas_no_disponibles': 'HTTP 400 con «model run is not available» ⇒ pasada ausente; se registra, no se sustituye por otro ciclo. Al final de la descarga se reintenta una sola vez cada pasada ausente.',
        'errores_transitorios': 'HTTP 429/500/502/503/504, timeouts y errores de red ⇒ reintento de la MISMA petición con espera exponencial (30 s × 2^k, tope 30 min, con azar), sin límite de intentos; una sola petición en vuelo; timeout de 180 s por petición.',
        'alternativa_por_estacion': 'Si una petición con las 34 coordenadas falla ≥ 12 veces seguidas mientras una de una sola coordenada responde, esa pasada se descarga por estación (mismo coste contado). Se anota en el recibo.',
        'recibos': 'Cada respuesta íntegra con URL, marcas de tiempo, estado, SHA-256, bytes y llamadas contadas.',
        'identificacion_de_celda': 'Se registran latitude/longitude/elevation de la celda devuelta por estación y se comprueba que son idénticos entre modelos, ciclos y días.',
    },
    'cuota': {
        'conteo_supuesto': 'Una llamada contada por ubicación y petición (≤ 10 variables, ≤ 2 semanas): 34 por petición; 604 peticiones ≈ 20.536 llamadas.',
        'limites_gratuitos': {'minuto': 600, 'hora': 5000, 'dia': 10000},
        'politica': 'Ventanas deslizantes propias: ≤ 550/min, ≤ 4.800/h, ≤ 9.500/día UTC; ⇒ ≈ 141 peticiones/h, 279/día, ≈ 2,2 días de descarga con la API sana. No se reduce el número de estaciones por cuota.',
        'medicion_inicial': 'Se registran los tiempos de respuesta y códigos de las primeras 20 peticiones y se reparte el resto en días.',
    },
    'analisis': {
        'error': 'e = pronóstico − observación (Wh/m²) por estación i, día d, serie s.',
        'error_relativo': 'r = e / Ō_i, con Ō_i = media de la observación válida de la estación en la ventana (todos sus días válidos, con independencia de la disponibilidad de pronósticos). Ō_i se recalcula bajo cada escala k del análisis de sensibilidad.',
        'mae_relativo': 'MAE_rel(s) = media de |r| sobre el conjunto de análisis; es MAE_s/media(obs) cuando se calcula por estación (métrica primaria del encargo, en %).',
        'efecto': 'Reducción relativa de MAE A→B = (MAE_A − MAE_B)/MAE_A × 100 sobre el MISMO conjunto de estación-días. Positivo = B mejor.',
        'conjunto_de_analisis': 'Por comparación (pares completos): estación-días con observación válida y las dos series comparadas válidas. Se reporta N por comparación. Efecto principal = agregado con peso igual por estación-día (equivale a media de efectos por estación ponderada por su MAE_A·N_i).',
        'por_estacion': 'Mismo efecto restringido a la estación; intervalo con el mismo bootstrap de días restringido a esa estación.',
        'bootstrap': {'unidad': 'día natural del calendario de la ventana; cada réplica toma TODAS las estaciones de los días remuestreados',
                      'esquema': 'bloques circulares móviles de longitud L ∈ {1, 7, 14}; número de bloques = ceil(N/L); inicio uniforme en 0…N−1; concatenar y truncar a N días',
                      'replicas': 10000, 'semilla': 20260914, 'generador': 'numpy.random.default_rng(20260914), una matriz de índices por (ventana, L), compartida por todas las comparaciones (números aleatorios comunes)',
                      'estadistico_por_replica': 'MAE_A y MAE_B como cocientes de sumas sobre los estación-días de los días remuestreados; efecto por réplica con la fórmula del efecto', 'intervalo': 'percentiles 2,5 y 97,5', 'reporte': 'los tres largos, siempre'},
        'sensibilidad_instrumento': {
            'a_determinista': 'k ∈ {0,95; 1,00; 1,05}: observación de todas las estaciones dividida por k; se repite TODO (efectos, intervalos, p, Holm). Robusto al instrumento ⇔ signo del efecto y conclusión de los tres intervalos idénticos en los tres casos.',
            'b_monte_carlo': {'sorteos': 1000, 'k_i': 'Uniforme(0,95; 1,05) independiente por estación', 'semilla': 20260915, 'generador': 'numpy.random.default_rng(20260915)',
                              'por_sorteo': 'observación de cada estación dividida por su k_i; efecto puntual de H1, H2 y secundarias; intervalos bootstrap con la MISMA matriz de índices del análisis principal (L = 1, 7, 14)',
                              'reporte': ['distribución del efecto (media, desviación, percentiles 2,5/50/97,5)',
                                          'supervivencia nivel 1 = fracción de sorteos con el mismo signo del efecto puntual que el análisis principal',
                                          'supervivencia nivel 2 = fracción con el mismo signo Y la misma conclusión del intervalo (excluye cero por el mismo lado / incluye cero) en cada uno de los tres largos, reportada por largo']},
        },
        'estratos_exploratorios': {'sin_correccion': True, 'por': ['estación', 'mes (mayo 14-31, junio, julio, agosto)', 'tercil de cloud_cover medio diurno de IFS_00 (cortes en percentiles 33,3/66,7 de los estación-días del conjunto de H1)', 'latitud: terciles de la latitud de las 34 estaciones (norte/centro/sur)'],
                                  'calculo': 'efecto sobre los estación-días del estrato; intervalo con el mismo bootstrap de calendario completo (los días fuera del estrato aportan cero)',
                                  'reporte': 'resultados.json con los tres largos; informe.md con el efecto puntual y el intervalo L = 7 para no multiplicar tablas',
                                  'prohibido': 'reformular las hipótesis primarias a partir de los estratos'},
        'enlace_06_18': {'proposito': 'comprobar que el veredicto no depende de agregar a día completo',
                         'datos': 'semihorarios SiAR YA descargados en trabajos previos (sin descarga nueva): AL01 y C01 (16-jun→31-jul y 10-ago→8-sep), M01 (10-ago→8-sep), AL10 y LU01 (16-jun→31-jul); AL02 y C02 tienen semihorario pero no pronóstico y se omiten',
                         'pronosticos': 'los ya descargados por el piloto/réplica/validación para AL01, C01, M01 (cuatro series), y los de la descarga nueva para AL10 y LU01 (están entre las 34)',
                         'ventana': 'intersección con la ventana primaria: 16-jun→31-jul y 10-ago→31-ago de 2026',
                         'calculo': 'observación 06-18 UTC = suma de las 24 medias semihorarias (fin de intervalo 06:30 … 18:00) × 0,5 h; pronóstico 06-18 = suma de las 12 medias horarias con marcas 07:00 … 18:00; mismas métricas, mismo bootstrap; marcado como exploratorio'},
        'verificacion': ['recálculo independiente con aritmética decimal de MAE y efectos puntuales desde los ficheros crudos',
                         'pruebas automatizadas de: agregación diaria, H0 (FAO-56), bootstrap por bloques circulares, p bilateral, Holm, escalado k',
                         'verificación del paquete sin conexión (hashes de datos_y_analisis.zip y reproducción de resultados.json)'],
    },
    'salida': {'directorio': 'outputs/latencia_pronosticos/medicion_escala/',
               'ficheros': ['metodo_fijado.json', 'metodo_fijado_recibo.json', 'estaciones.json', 'resultados.json', 'informe.md', 'figura_principal.png', 'figura_sensibilidad.png', 'datos_y_analisis.zip', 'verificacion.json'],
               'figura_principal': 'efecto por estación (H1 y H2) con intervalo L = 7 y el efecto agregado, ventana primaria', 'figura_sensibilidad': 'histograma del efecto de H1 y H2 en los 1.000 sorteos, con el efecto principal y el cero'},
    'terminacion': 'El encargo termina con el informe (veredicto H1/H2, intervalos, sensibilidad, secundarias, limitaciones). Termina igual si no hay efecto, si no sobrevive al instrumento, o si el archivo no puede descargarse (se reporta «no se puede medir» con lo que haya). No se propone fase siguiente.',
    'no_se_hace': ['validar sensores, pedir certificados, descargar satélite', 'entrenar correcciones de sesgo', 'magnitudes absolutas del error como resultado', 'euros, compradores', 'cambiar rejilla/estaciones/ventanas/hipótesis tras ver datos', 'mezclar ventanas', 'añadir métodos para rescatar un nulo', 'proponer el siguiente experimento'],
    'entorno': {'python': sys.version.split()[0], 'numpy': __import__('numpy').__version__, 'pandas': __import__('pandas').__version__, 'matplotlib': 'entorno virtual aparte, solo para figuras'},
}

target = OUT / 'metodo_fijado.json'
if target.exists() and '--force' not in sys.argv:
    raise SystemExit('metodo_fijado.json ya existe; no se sobrescribe sin --force')
dump(target, spec)
digest = sha256_file(target)
receipt = {'fichero': 'metodo_fijado.json', 'sha256': digest, 'bytes': target.stat().st_size, 'congelado_en_utc': now(), 'descargas_iniciadas_en_utc': None,
           'nota': 'Marca temporal local y hash; no es un prerregistro externo. descargas_iniciadas_en_utc se rellena al lanzar la primera descarga.'}
dump(OUT / 'metodo_fijado_recibo.json', receipt)
dump(STATE / 'metodo_fijado_recibo.json', receipt)
(BASE / 'metodo_fijado.json').write_bytes(target.read_bytes())
print(json.dumps(receipt, ensure_ascii=False, indent=2))
print('estaciones:', len(ordered))
