# ADR-0005: Evaluar dNBR y RdNBR sin preferir uno de antemano

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-03a, RF-03b, OE1, OE2, OE3 |

## Contexto

El dNBR es el índice empleado en el protocolo FIREMON (Key y Benson, 2006). El
RdNBR relativiza la diferencia respecto del valor previo al incendio, para
reducir la dependencia de la densidad de vegetación existente (Miller y Thode,
2007). En teoría, el RdNBR es más apropiado para paisajes heterogéneos como
el del Biobío, donde coexisten bosque nativo, matorral y plantaciones.

Sin embargo, la ventaja del RdNBR no es uniforme: su desempeño relativo
depende del tipo de cobertura y del dosel previo (Soverel et al., 2010), y hay
casos en que ambos índices rinden de forma similar (Sánchez et al., 2023).

## Opciones consideradas

1. **Solo dNBR.** *Ventaja:* comparabilidad directa con FIREMON.
   *Limitación:* no evalúa la corrección por vegetación previa.
2. **Solo RdNBR.** *Ventaja:* teóricamente mejor para paisajes heterogéneos.
   *Limitación:* asume de antemano lo que la investigación debe comprobar.
3. **Ambos índices.** *Ventaja:* permite determinar cuál transfiere mejor.
   *Limitación:* duplica las combinaciones a evaluar.
4. **Ambos más índices adicionales.** *Ventaja:* mayor cobertura.
   *Limitación:* multiplica el procesamiento y las comparaciones.

## Decisión

Se adoptan dNBR y RdNBR como índices obligatorios (RF-03a, *Must*). Los índices
adicionales se incorporan solo si el plazo lo permite (RF-03b, *Could*).

## Consecuencias

**Positivas**
- Determinar qué índice transfiere mejor entre estratos pasa a ser un
  resultado de la investigación y no un supuesto previo.

**Negativas**
- Se duplica el número de combinaciones de índice y estrato, lo que aumenta
  el número de comparaciones estadísticas (ver ADR-0016).

## Referencias

- Key, C. H. y Benson, N. C. (2006). Landscape Assessment (LA). En *FIREMON*,
  RMRS-GTR-164-CD. USDA Forest Service.
- Miller, J. D. y Thode, A. E. (2007). *Remote Sensing of Environment*, 109(1),
  66–80. https://doi.org/10.1016/j.rse.2006.12.006
- Sánchez, R. et al. (2023). *Revista de Teledetección*, 61, 43–58.
  https://doi.org/10.4995/raet.2023.18155
- Soverel, N. O., Perrakis, D. D. B. y Coops, N. C. (2010). *Remote Sensing of
  Environment*, 114(9), 1896–1909. https://doi.org/10.1016/j.rse.2010.03.013
