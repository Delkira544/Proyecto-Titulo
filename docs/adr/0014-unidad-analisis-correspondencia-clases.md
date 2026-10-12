# ADR-0014: Unidad de análisis y correspondencia de clases entre EMSR859 y severidad

| Campo | Valor |
|---|---|
| **Estado** | Propuesto (hasta verificar el supuesto S4) |
| **Fecha** | 2026-09-29 |
| **Origen** | Revisión posterior a la Fase 1 |
| **Relacionado con** | RF-12, OE4, supuestos S2 y S4, ADR-0006, ADR-0007, ADR-0013 |

## Contexto

Olofsson et al. (2014) distinguen tres componentes en la evaluación de
exactitud: el diseño de muestreo, el diseño de respuesta y el análisis. El
diseño de respuesta define cómo se asigna la etiqueta de referencia a cada
unidad de la muestra. Para este proyecto implica dos definiciones:

1. Qué es una unidad de análisis y cómo se le asigna una clase, dado que los
   polígonos de EMSR859 no coinciden con la grilla de Sentinel-2.
2. Qué clase de severidad corresponde a cada clase de daño de EMSR859.

La segunda definición también fija el número de clases que usa la
umbralización multinivel (ADR-0006).

## Opciones consideradas

**Unidad de análisis**
1. **Píxel de la grilla de trabajo, con la clase que cubre la mayor parte de
   su superficie.** *Ventaja:* regla simple y reproducible.
   *Limitación:* los píxeles de borde quedan con etiquetas ambiguas.
2. **Píxel, con exclusión de los píxeles mixtos.** *Ventaja:* etiquetas más
   confiables. *Limitación:* sesga la muestra hacia zonas homogéneas.

**Correspondencia de clases**
1. **Correspondencia uno a uno** entre las clases de daño y las de severidad.
2. **Agregación de clases** hasta un nivel en que la correspondencia sea
   defendible.

## Decisión (propuesta)

- **Unidad de análisis:** el píxel de la grilla de trabajo, etiquetado con la
  clase de EMSR859 que cubre más del 50 % de su superficie. El efecto de los
  píxeles de borde se evalúa mediante la exclusión configurable de RF-16.
- **Correspondencia de clases:** se definirá tras revisar las definiciones
  oficiales de las clases de daño en el manual de Copernicus EMS. Si la
  correspondencia uno a uno no es defendible, se agregan clases.

Este registro pasa a *Aceptado* cuando se complete la tabla de
correspondencia.

## Consecuencias

**Positivas**
- La etiqueta de referencia de cada punto queda definida por una regla
  explícita y reproducible.

**Negativas**
- Una agregación de clases reduciría el nivel de detalle de la severidad
  evaluada.

**Pendientes**
- Completar la tabla de correspondencia (supuesto S4).
- Si el atributo de grado de daño no está poblado (supuesto S2), esta
  decisión se reemplaza en el contexto del ADR-0008.

## Referencias

- Copernicus Emergency Management Service (2025). *Detection methods and
  Damage Assessment. Rapid Mapping Manual*.
  https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/detection-methods-damage-assessment/
- Olofsson, P. et al. (2014). *Remote Sensing of Environment*, 148, 42–57.
  https://doi.org/10.1016/j.rse.2014.02.015
