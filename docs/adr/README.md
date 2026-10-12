# Registro de decisiones de arquitectura (ADR)

Esta carpeta documenta las decisiones de diseño del proyecto de título
*Evaluación de la transferibilidad de umbrales de severidad de quemado al
paisaje de la región del Biobío*. Cada archivo registra una decisión, su
contexto, las alternativas consideradas, sus consecuencias y su respaldo
bibliográfico. La convención se define en el
[ADR-0001](0001-registrar-decisiones-con-adr.md).

## Índice

| N.º | Decisión | Estado | Fecha |
|---|---|---|---|
| [0001](0001-registrar-decisiones-con-adr.md) | Registrar las decisiones de diseño mediante ADR | Aceptado | 2026-09-29 |
| [0002](0002-umbralizacion-no-supervisada.md) | Clasificar la severidad mediante umbralización no supervisada | Aceptado | 2026-09-29 |
| [0003](0003-procesamiento-hibrido-gee-local.md) | Procesamiento híbrido entre Google Earth Engine y Python local | Aceptado | 2026-09-29 |
| [0004](0004-coleccion-armonizada-sentinel2.md) | Usar la colección armonizada de Sentinel-2 y fijar los identificadores de escena | Aceptado | 2026-09-29 |
| [0005](0005-evaluar-dnbr-y-rdnbr.md) | Evaluar dNBR y RdNBR sin preferir uno de antemano | Aceptado | 2026-09-29 |
| [0006](0006-otsu-y-kde-en-paralelo.md) | Aplicar umbralización multinivel de Otsu y KDE en paralelo | Aceptado | 2026-09-29 |
| [0007](0007-referencia-validacion-emsr859.md) | Usar el producto EMSR859 como referencia de validación | Aceptado | 2026-09-29 |
| [0008](0008-escenario-b-geocbi.md) | Escenario B: referencia mediante GeoCBI fotointerpretado | Propuesto (contingencia) | 2026-09-29 |
| [0009](0009-prueba-multimodalidad-silverman.md) | Usar la prueba de Silverman como prueba principal de multimodalidad | Aceptado | 2026-09-29 |
| [0010](0010-contingencia-umbrales-percentiles.md) | Umbrales por percentiles como contingencia ante falta de multimodalidad | Propuesto (contingencia) | 2026-09-29 |
| [0011](0011-estratificacion-catastro-conaf.md) | Estratificar con el catastro de CONAF y usar sus polígonos solo como delimitadores | Aceptado | 2026-09-29 |
| [0012](0012-particion-temporal-datos.md) | Partición temporal de los datos con validación cruzada complementaria | Aceptado | 2026-09-29 |
| [0013](0013-muestreo-estratificado-comun.md) | Muestreo aleatorio estratificado común a las tres estrategias | Aceptado | 2026-09-29 |
| [0014](0014-unidad-analisis-correspondencia-clases.md) | Unidad de análisis y correspondencia de clases entre EMSR859 y severidad | Propuesto | 2026-09-29 |
| [0015](0015-metricas-de-exactitud.md) | Exactitudes global, de usuario y de productor como métricas principales | Aceptado | 2026-09-29 |
| [0016](0016-criterios-de-decision-estadistica.md) | Criterios de decisión mediante McNemar, superioridad y equivalencia | Propuesto | 2026-09-29 |
| [0017](0017-configuracion-fuente-unica.md) | Archivo de configuración como fuente única de parámetros y de la partición de datos | Aceptado | 2026-09-29 |
| [0018](0018-snakemake-gestor-flujo-trabajo.md) | Snakemake como gestor del flujo de trabajo, con entornos conda por regla | Aceptado | 2026-09-29 |

## Estados

- **Propuesto:** decisión definida pero pendiente de una verificación o de un
  parámetro. Los registros de contingencia permanecen en este estado hasta
  que se cumple su criterio de activación.
- **Aceptado:** decisión vigente. Su contenido no se modifica.
- **Obsoleto:** decisión que dejó de aplicarse sin ser reemplazada.
- **Reemplazado por ADR-XXXX:** decisión sustituida por un registro
  posterior.

## Cómo agregar un registro

1. Copiar [`0000-plantilla.md`](0000-plantilla.md) con el siguiente número
   disponible: `NNNN-titulo-en-minusculas.md`.
2. Completar todas las secciones. El contexto se redacta sin adelantar la
   decisión.
3. Si reemplaza una decisión anterior, cambiar solo el estado del registro
   antiguo a *Reemplazado por ADR-NNNN*.
4. Agregar la fila correspondiente a este índice.
5. Hacer commit con el prefijo `docs(adr):`, por ejemplo:
   `docs(adr): registrar ADR-0019 cambio de referencia de validación`.

## Nota sobre las fechas

Los registros 0001 a 0018 se redactaron en la misma fecha. Los que indican
"registrado retroactivamente" documentan decisiones tomadas durante la
Fase 1; su fecha corresponde a la redacción del registro y no a la de la
decisión original.
