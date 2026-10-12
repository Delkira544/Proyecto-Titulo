# ADR-0007: Usar el producto EMSR859 como referencia de validación

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-12, OE4, supuesto S2, ADR-0008, ADR-0011, ADR-0014 |

## Contexto

Los antecedentes nacionales más cercanos validaron sus resultados contra los
polígonos de área quemada de CONAF (Sánchez et al., 2023; Miranda et al.,
2022). En el programa de evaluación de severidad de CONAF, el área quemada se
delimita mediante teledetección (CONAF, 2021). Usar esos productos como
referencia de un método también basado en teledetección introduce un riesgo
de circularidad: se evalúa un producto satelital contra otro de origen
comparable.

Se necesita una referencia de otra institución y de una fuente de datos
independiente de Sentinel-2.

## Opciones consideradas

1. **Polígonos de área quemada de CONAF.**
   *Ventaja:* disponibles para varios eventos. *Limitación:* riesgo de
   circularidad; además, no contienen niveles de severidad.
2. **Producto EMSR859 del Servicio de Gestión de Emergencias de Copernicus.**
   *Ventaja:* institución distinta, sensores de mayor resolución y fuente
   independiente. *Limitación:* es una estimación aproximada, no verdad de
   terreno.
3. **Levantamiento propio en terreno con CBI.**
   *Ventaja:* la referencia metodológicamente más sólida.
   *Limitación:* fuera del alcance, por la restricción de no realizar trabajo
   de campo.

## Decisión

Se adopta EMSR859 como referencia de validación, porque satisface tres
condiciones que los polígonos de CONAF no cumplen simultáneamente:

1. Proviene de una institución distinta.
2. Se genera con sensores de resolución sustancialmente mayor (Pléiades,
   SPOT-6/7 y PlanetScope, entre 0,5 y 3 m, frente a los 20 m de Sentinel-2).
3. Su fuente de datos es independiente de la empleada en este trabajo.

Los polígonos de CONAF se usan solo para delimitar los incendios de
calibración (ADR-0011).

## Consecuencias

**Positivas**
- Se elimina el riesgo de circularidad con la institución que produce los
  polígonos de referencia nacionales.

**Negativas**
- El propio servicio advierte que su información de daño es una estimación
  aproximada y no verdad de terreno (Copernicus EMS, 2025). Los resultados se
  reportan como concordancia con esa referencia y no como exactitud absoluta.
- La validación queda restringida a un solo evento (enero de 2026).

**Pendientes**
- Verificar en los metadatos oficiales del producto los sensores y
  resoluciones indicados.
- Verificar que el atributo de grado de daño esté poblado (supuesto S2). Si
  no lo está, se activa el ADR-0008.

## Referencias

- CONAF (2021). *Chile Forestal*, 399. Corporación Nacional Forestal.
- Copernicus Emergency Management Service (2025). *Detection methods and
  Damage Assessment. Rapid Mapping Manual*.
  https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/detection-methods-damage-assessment/
- Lee, K., Kim, B. y Park, S. (2023). *GIScience & Remote Sensing*, 60(1),
  2192157. https://doi.org/10.1080/15481603.2023.2192157
- Miranda, A. et al. (2022). *Earth System Science Data*, 14(8), 3599–3613.
  https://doi.org/10.5194/essd-14-3599-2022
- Sánchez, R. et al. (2023). *Revista de Teledetección*, 61, 43–58.
  https://doi.org/10.4995/raet.2023.18155
