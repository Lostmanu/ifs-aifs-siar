# ¿Puede convertirse la mejora meteorológica en un proyecto valioso?

13 de septiembre de 2026 · segunda puerta de decisión · gasto contratado: 0 €

**Resultado: hay una decisión económica concreta que investigar, pero aún falta el acceso que permitiría demostrar valor.** El candidato es evaluar si una actualización disponible antes de una subasta permite a un representante de plantas solares ajustar su energía vendida y mejorar su resultado neto frente a su práctica actual. No hemos calculado beneficios históricos ni validado un negocio.

La réplica anterior mostró una reducción del error de radiación de IFS del 8,56 % en La Mojonera y del 8,27 % en A Capela. Ese porcentaje no se puede aplicar a una factura de desvíos. Es un resultado meteorológico, con incertidumbre, de dos estaciones y un mes.

## La decisión y quién podría beneficiarse

Un representante ya vende la producción de sus plantas y gestiona sus desvíos. La decisión propuesta es cuánto ajustar la posición del siguiente día antes de IDA1, con el pronóstico que realmente haya recibido y procesado. El horario, los periodos negociables y el margen operativo se fijarán para la fecha concreta antes de evaluar. La fase inicial sería una simulación junto a la operación existente, sin enviar órdenes.

Axpo describe expresamente la venta de programas en OMIE y la liquidación de desvíos ante REE. Nexus ofrece representación, telemedida y participación en mercados de ajuste. Son ejemplos verificables de la función que necesitamos entender; no son clientes nuestros ni hay constancia de que quieran colaborar. [Axpo](https://www.axpo.com/es/es/energia/productores-energia/representacion-mercado.html), [Nexus](https://www.nexusenergia.com/productores/mercado-de-ajuste/).

**La alternativa real es el sistema que ya utiliza ese gestor.** AleaSoft, por ejemplo, comercializa previsiones solares por planta o cartera. Por tanto, no podemos vender como novedad que existan previsiones solares o actualizaciones intradiarias. La pregunta es si nuestra información llega de forma útil antes que la suya y mejora una decisión a un coste razonable. [Oferta de previsiones de AleaSoft](https://aleasoft.com/services/renewable-energy-forecasts/short-term/).

También debemos identificar quién soporta los costes bajo el contrato. Un propietario puede tener los desvíos cubiertos o repartidos por su representante. Un ahorro del conjunto de la cartera no equivale automáticamente al ahorro del propietario ni a ingresos para nosotros. Esa asignación contractual está pendiente de obtener.

## Por qué menos error no garantiza más dinero

He construido y probado un núcleo contable para comparar dos decisiones. **Los siguientes números son inventados exclusivamente para explicar el mecanismo**, no proceden de los precios descargados ni de una planta real.

La planta produce 10 MWh. Se habían vendido 12 MWh. Una actualización lleva a recomprar 1 MWh a 50 €/MWh, con 1 € de coste. El déficit disminuye de 2 a 1 MWh en todos los casos:

| Supuesto ilustrativo | Efecto económico de la actualización |
|---|---:|
| Liquidar el déficit cuesta 100 €/MWh | **+49 €**: se evitan 100 €, se pagan 50 € y 1 € de coste |
| Liquidar el déficit cuesta 20 €/MWh | **−31 €**: se evitan 20 €, se pagan 50 € y 1 € de coste |
| El resto de la cartera tiene +5 MWh y el excedente se valora a 20 €/MWh | **−31 €**: cambia el saldo de la cartera, aunque mejore el error de la planta |

La documentación de liquidación contempla importes con signo y precios de desvío que pueden ser únicos o distintos según el sentido. El modelo admite ambos casos y precios negativos. **No reproduce todos los componentes de la liquidación española:** los cargos adicionales, el contrato, las versiones normativas y las correcciones de medida deben incorporarse y reconciliarse antes de valorar un caso real. [P.O. 14.4 en el BOE de 2025](https://www.boe.es/buscar/doc.php?id=BOE-A-2025-13076).

Para una producción fija y una operación que no cambia los precios, el cálculo incremental es:

`resultado = cambio de energía vendida × precio de ejecución + cambio de liquidación del saldo − costes de operar − otros costes incrementales`

Se liquida el saldo positivo con su precio correspondiente y el negativo con el suyo. El saldo incluye el resto de la cartera cuando esa es la unidad de liquidación. No se sustituye esta cuenta por «reducción del error absoluto × precio medio». Los ingresos comunes de las dos decisiones se cancelan; si una acción altera la producción o las actuaciones posteriores, esa simplificación deja de ser suficiente.

El núcleo pasó 12 pruebas: signos, precios negativos, cruce entre déficit y excedente, compensación de cartera, costes, datos ausentes y uso de información antes del cierre. Eso verifica la aritmética y los controles básicos; no demuestra rentabilidad.

## Qué datos he comprobado que podemos obtener

| Dato | Comprobación realizada | Qué permite y qué no |
|---|---|---|
| Precios de subasta intradiaria OMIE | Descargado sin cuenta un fichero del 12/09/2026, 96 registros numerados, respuesta 200 | Acredita acceso a un resultado de subasta; no que nuestra oferta hubiera sido aceptada |
| Máximos, mínimos y medias del continuo | Descargado sin cuenta el fichero del mismo día, 96 registros | Describe operaciones agregadas; no un precio ejecutable a una hora dada |
| Indicador eSIOS consultado anónimamente | Respuesta 403 a una consulta de metadatos del indicador 763 | Esa ruta no funcionó sin autenticación; no demuestra que todas las descargas públicas estén bloqueadas |
| Producción y programa de una planta/cartera | No disponibles en este proyecto | Imprescindibles para comparar decisiones reales |
| Pronósticos y decisiones que usa el gestor | No disponibles | Sin ellos no podemos afirmar que lo superamos |
| Costes, liquidación y reparto contractual | No disponibles | Determinan ahorro neto y beneficiario |

Los enlaces de los dos ficheros se localizaron en el [catálogo público de OMIE](https://www.omie.es/es/file-access-list). El resumen del continuo indica emisión el 13/09/2026 a las 01:02 para el día anterior: usar su media como precio al que habríamos operado antes sería una suposición injustificada. Además, conserva una cabecera que habla de horas pese a sus 96 registros; el formato y el calendario se deben validar antes de emparejarlo con producción. No se han unido esos precios con las observaciones de seis horas.

La [documentación de la API eSIOS](https://api.esios.ree.es/) indica cómo solicitar un token personal. No se han utilizado claves encontradas en ejemplos de documentación ni enviado solicitudes en nombre del usuario. REE distingue la información pública de los ficheros privados de liquidación del responsable del balance; obtener una clave de API no sustituye disponer de los datos del cliente. [Acceso a la liquidación, REE](https://www.ree.es/es/clientes/consumidor/acceso-a-tu-liquidacion).

La resolución de julio de 2026 vincula la aplicación de las nuevas rondas al anuncio de los operadores y contiene excepciones sobre disposiciones anteriores. El diseño exige registrar qué reglas se aplican a cada muestra; no se aplica retroactivamente la reforma por ser el texto más reciente. Esta fase no certifica una implementación normativa completa. [Resolución de 2026](https://www.boe.es/buscar/doc.php?id=BOE-A-2026-17285).

## La investigación que sí propondría

**Medir el valor incremental de disponer de un dato antes de una decisión, manteniendo constantes su contenido y la regla de decisión.** La prueba principal compararía el mismo pronóstico disponible inmediatamente con una copia retrasada 15 minutos. Se conservarían 5 y 30 minutos como sensibilidades secundarias. Si ambos llegan a tiempo y permiten la misma decisión, no se atribuye un beneficio a esa diferencia temporal.

Compararíamos también con la práctica actual del gestor, con no hacer una actualización adicional y con el canal accesible más rápido del mismo modelo. Esta última referencia es esencial: la auditoría anterior ya encontró que elegir un canal lento podía crear una aparente ventaja de IA.

Preferiría 30 días consecutivos de evaluación futura, después de calibrar por separado la conversión de pronóstico a producción y congelar la regla. La unidad económica sería el periodo de entrega de quince minutos, conservando días de 92, 96 o 100 periodos. La incertidumbre se calcularía por días completos y conjuntamente para la cartera. Un mes serviría para decidir si merece ampliar; no para anunciar rentabilidad anual.

**No afirmo que esta pregunta sea nueva.** Kuppelwieser y Wozabal ya estudian negociación intradiaria, actualizaciones meteorológicas y liquidez. La literatura también considera la relación entre revisiones de renovables y precios. Una contribución defendible necesitaría identificar algo que esas investigaciones no resuelvan —por ejemplo, una evaluación verificable del coste de retrasos alrededor de cierres concretos— y demostrarlo con datos adecuados. Cambiar de país o añadir un modelo de IA no basta. [OR Spectrum](https://link.springer.com/article/10.1007/s00291-022-00698-5), [estudio de previsión intradiaria](https://arxiv.org/abs/2211.13002).

## Próxima acción concreta y límite de esfuerzo

He preparado una propuesta breve para un posible colaborador y un diccionario de los datos mínimos. El primer intercambio debería ser una muestra de un día anonimizada y una explicación de su práctica actual; con eso se puede comprobar si es posible reconstruir una liquidación y una decisión. No hace falta pedir acceso de negociación ni credenciales.

Propondría dedicar como máximo diez días de trabajo a conseguir una colaboración con esos datos. Es un límite de esfuerzo propuesto, no una tarea programada. No se ha contactado con ninguna empresa. Si nadie puede aportar producción, versiones de pronósticos y costes, **no seguiría ampliando esta vía comercial ni gastaría en más modelos**. Se conservaría la auditoría realizada y se reconsideraría una pregunta investigable con datos realmente accesibles.

Si se consigue acceso, el orden sería: reconciliar un día de liquidación; fijar el protocolo completo y el umbral económico relevante para el colaborador; evaluar fuera de muestra; y solo entonces decidir si invertir varios meses. Ese umbral no se puede deducir del 8 % meteorológico.

La situación actual es precisa: infraestructura meteorológica probada, una señal de mejora, acceso público parcial a precios y aritmética económica preparada. Faltan los datos de la decisión real y del sistema que debemos superar. **Aún no hemos descubierto una ventaja extraordinaria monetizable. Sí hemos delimitado la prueba que podría distinguirla de un resultado bonito.**

## Control de disponibilidad pendiente

Al plantear una comprobación adicional de descarga antes de IDA1, la lectura del reloj fue 13/09/2026 16:39:36 UTC, 18:39:36 en Madrid, posterior al cierre de las 15:00 utilizado en el protocolo. No se ejecutó ni se contabilizó como una observación previa al cierre. Una captura posterior no permite reconstruir retrospectivamente la usabilidad. Se conserva la limitación de las capturas anteriores: HEAD acreditaba una respuesta, no la descarga y decodificación completa antes del cierre. No hay una nueva captura programada ni un observador en ejecución.
