# ADR-0016: Criterios de decisión mediante McNemar, superioridad y equivalencia

| Campo | Valor |
|---|---|
| **Estado** | Propuesto (hasta fijar el margen de equivalencia) |
| **Fecha** | 2026-09-29 |
| **Origen** | Revisión posterior a la Fase 1 |
| **Relacionado con** | RF-15, RNF-05, OE4, ADR-0013, ADR-0015 |

## Contexto

El objetivo general plantea dos preguntas distintas:

1. Si el umbral regional **supera** al internacional.
2. Si el umbral regional **se acerca** al desempeño del ad hoc.

La primera es una pregunta de diferencia. La segunda es una pregunta de
equivalencia, que no se responde con una prueba de diferencia convencional:
no encontrar una diferencia significativa no demuestra que dos métodos sean
equivalentes. Foody (2009) plantea el uso de intervalos de confianza para
evaluar diferencia, equivalencia y no inferioridad entre exactitudes.

Además, el número de comparaciones (índices × estratos × áreas de interés ×
pares de estrategias) exige controlar el error por comparaciones múltiples.

## Opciones consideradas

1. **Comparar las exactitudes sin prueba estadística.**
   *Limitación:* no distingue diferencias reales del error de muestreo.
2. **Solo pruebas de diferencia.**
   *Limitación:* no permite concluir equivalencia.
3. **Prueba de McNemar para las diferencias y un criterio de equivalencia
   basado en intervalos de confianza, con corrección por comparaciones
   múltiples.**

## Decisión (propuesta)

Se adopta la opción 3, con los siguientes criterios, fijados antes del
análisis y registrados en la configuración (RNF-05):

- **Prueba:** McNemar entre pares de estrategias sobre la muestra común
  (ADR-0013).
- **Nivel de significancia:** α = 0,05, con corrección de Holm por
  comparaciones múltiples.
- **Superioridad:** el umbral regional supera al internacional en una
  combinación si el intervalo de confianza del 95 % de la diferencia de
  exactitud global excluye el cero a favor del regional, y la prueba de
  McNemar es significativa tras la corrección.
- **Equivalencia:** el umbral regional es equivalente al ad hoc si el
  intervalo de confianza de la diferencia queda completamente dentro de
  (−Δ, +Δ).
- **Margen de equivalencia Δ:** *pendiente de fijar y justificar.*

Este registro pasa a *Aceptado* cuando se fije Δ. **Debe quedar aceptado
antes de ejecutar la evaluación de exactitud**; la fecha del commit lo
acredita.

## Consecuencias

**Positivas**
- Las dos preguntas del objetivo general quedan respondidas con criterios
  explícitos y definidos antes de conocer los resultados.

**Negativas**
- La corrección por comparaciones múltiples reduce la potencia estadística
  en cada comparación individual.

**Pendientes**
- Fijar y justificar Δ, por ejemplo según la diferencia de exactitud que
  tendría consecuencias prácticas para la clasificación de severidad.

## Referencias

- Foody, G. M. (2004). *Photogrammetric Engineering & Remote Sensing*, 70(5),
  627–633. https://doi.org/10.14358/PERS.70.5.627
- Foody, G. M. (2009). Classification accuracy comparison: Hypothesis tests
  and the use of confidence intervals in evaluations of difference,
  equivalence and non-inferiority. *Remote Sensing of Environment*, 113(8),
  1658–1663. https://doi.org/10.1016/j.rse.2009.03.014
- Holm, S. (1979). A simple sequentially rejective multiple test procedure.
  *Scandinavian Journal of Statistics*, 6(2), 65–70.
  *(verificar antes de citar)*
