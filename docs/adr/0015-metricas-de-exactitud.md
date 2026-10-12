# ADR-0015: Exactitudes global, de usuario y de productor como métricas principales

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Revisión posterior a la Fase 1 |
| **Relacionado con** | RF-14a, RF-14b, OE4, ADR-0013 |

## Contexto

La versión anterior del proyecto incluía el coeficiente Kappa entre las
métricas principales de exactitud. Foody (2020) sostiene que el Kappa no es
un índice de exactitud sino de acuerdo más allá del azar, y que el acuerdo por
azar no es relevante en una evaluación de exactitud. Olofsson et al. (2014)
recomiendan reportar las exactitudes global, de usuario y de productor con sus
intervalos de confianza.

## Opciones consideradas

1. **Kappa como métrica principal.** *Ventaja:* comparabilidad con estudios
   antiguos. *Limitación:* no mide exactitud.
2. **Exactitudes global, de usuario y de productor, sin Kappa.**
   *Ventaja:* métricas interpretables alineadas con las buenas prácticas.
   *Limitación:* se pierde comparabilidad con estudios que solo reportan
   Kappa.
3. **Exactitudes como métricas principales y Kappa como secundaria.**
   *Ventaja:* combina rigor y comparabilidad.

## Decisión

Se adopta la opción 3. Las métricas principales son la exactitud global y las
exactitudes de usuario y de productor por clase, con intervalos de confianza
del 95 % (RF-14a, *Must*). El Kappa se reporta solo como métrica secundaria
para comparar con estudios previos (RF-14b, *Could*) y no interviene en los
criterios de decisión (ADR-0016).

## Consecuencias

**Positivas**
- Las conclusiones se basan en métricas que miden exactitud.
- Las exactitudes de usuario y de productor muestran qué clases concentran
  los errores de comisión y de omisión.

**Negativas**
- La comparación con estudios que solo reportan Kappa queda limitada.

## Referencias

- Foody, G. M. (2020). Explaining the unsuitability of the kappa coefficient
  in the assessment and comparison of the accuracy of thematic maps obtained
  by image classification. *Remote Sensing of Environment*, 239, 111630.
  https://doi.org/10.1016/j.rse.2019.111630
- Olofsson, P. et al. (2014). *Remote Sensing of Environment*, 148, 42–57.
  https://doi.org/10.1016/j.rse.2014.02.015
