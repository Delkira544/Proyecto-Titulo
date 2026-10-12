# ADR-0009: Usar la prueba de Silverman como prueba principal de multimodalidad

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Revisión posterior a la Fase 1 |
| **Relacionado con** | RF-07, OE1, supuesto S1, ADR-0006, ADR-0010 |

## Contexto

La umbralización no supervisada presupone que las distribuciones de los
índices admiten separación en clases (supuesto S1). RF-07 exige verificarlo
con una prueba estadística para cada combinación de índice y estrato, pero la
versión anterior no especificaba cuál. Como la umbralización es multinivel,
interesa saber no solo si la distribución es multimodal, sino cuántas modas
presenta.

## Opciones consideradas

1. **Prueba dip de Hartigan y Hartigan (1985).**
   *Ventaja:* ampliamente usada y de cálculo simple. *Limitación:* solo
   permite rechazar la unimodalidad; no indica el número de modas.
2. **Prueba de Silverman (1981), basada en estimación de densidad kernel.**
   *Ventaja:* contrasta hipótesis sobre el número de modas y es coherente con
   el uso de KDE en la umbralización. *Limitación:* mayor costo
   computacional.

## Decisión

Se adopta la prueba de Silverman como prueba principal, porque contrasta el
número de modas que requiere la umbralización multinivel. La prueba dip de
Hartigan se conserva como verificación complementaria de no unimodalidad.

## Consecuencias

**Positivas**
- La verificación del supuesto S1 corresponde directamente a lo que exige el
  método (número de clases), y no solo a la ausencia de unimodalidad.

**Negativas**
- Mayor tiempo de cómputo en la etapa de verificación.

**Pendientes**
- Fijar en la configuración el nivel de significancia y el criterio de
  "proporción relevante" de combinaciones que activa el ADR-0010.

## Referencias

- Hartigan, J. A. y Hartigan, P. M. (1985). The dip test of unimodality.
  *The Annals of Statistics*, 13(1), 70–84.
  https://doi.org/10.1214/aos/1176346577
- Silverman, B. W. (1981). Using kernel density estimates to investigate
  multimodality. *Journal of the Royal Statistical Society: Series B*, 43(1),
  97–99. https://doi.org/10.1111/j.2517-6161.1981.tb01155.x
