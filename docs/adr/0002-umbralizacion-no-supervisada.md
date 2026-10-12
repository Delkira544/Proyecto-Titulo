# ADR-0002: Clasificar la severidad mediante umbralización no supervisada

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-07, RF-08, RF-11, OE2, OE3 |

## Contexto

La pregunta de investigación es si los umbrales de severidad calibrados en
otro ecosistema, como los de Key y Benson (2006), son transferibles al paisaje
del Biobío, y si un umbral calibrado regionalmente se acerca al desempeño de
uno calculado sobre el propio evento. El objeto de estudio es, por lo tanto,
el **umbral** como valor de corte interpretable, y no la exactitud máxima
alcanzable por cualquier método.

Los clasificadores de aprendizaje automático supervisado han mostrado buenos
resultados en la cartografía de severidad, incluso usando productos de
Copernicus EMS como referencia (Lee et al., 2023).

## Opciones consideradas

1. **Umbralización no supervisada (Otsu, KDE).**
   *Ventaja:* produce valores de corte interpretables y comparables con los
   de la literatura, sin requerir datos etiquetados. *Limitación:* no alcanza
   necesariamente la mayor exactitud posible.
2. **Clasificación supervisada (bosques aleatorios, máquinas de soporte
   vectorial).**
   *Ventaja:* suele alcanzar mayor exactitud. *Limitación:* no produce un
   umbral interpretable, por lo que no permite responder si un valor de corte
   específico es transferible.
3. **Umbrales optimizados de forma supervisada contra una referencia**, como
   el enfoque de Sánchez et al. (2023), que selecciona el umbral que maximiza
   la similitud con los polígonos de CONAF.
   *Ventaja:* produce umbrales interpretables. *Limitación:* requiere una
   referencia en la etapa de calibración, que en el Biobío solo existe para el
   evento de validación; usarla para calibrar comprometería la independencia
   de la evaluación.

## Decisión

Se adopta la umbralización no supervisada, porque es la única opción que
produce umbrales interpretables sin requerir datos de referencia en la etapa
de calibración, y permite así comparar directamente los umbrales regionales
con los de Key y Benson.

## Consecuencias

**Positivas**
- La calibración no usa la referencia de validación, lo que preserva su
  independencia.
- Los umbrales resultantes son comparables con los valores publicados.

**Negativas**
- El estudio no informa cuál es la exactitud máxima alcanzable con los datos
  disponibles.
- La exclusión del aprendizaje supervisado queda como restricción de alcance
  del proyecto de título y se declara como trabajo futuro.

**Pendientes**
- La aplicabilidad del método depende del supuesto S1 (multimodalidad),
  verificado según el ADR-0009, con contingencia en el ADR-0010.

## Referencias

- Key, C. H. y Benson, N. C. (2006). Landscape Assessment (LA). En *FIREMON*,
  RMRS-GTR-164-CD. USDA Forest Service.
- Lee, K., Kim, B. y Park, S. (2023). *GIScience & Remote Sensing*, 60(1),
  2192157. https://doi.org/10.1080/15481603.2023.2192157
- Otsu, N. (1979). *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1),
  62–66. https://doi.org/10.1109/TSMC.1979.4310076
- Sánchez, R. et al. (2023). *Revista de Teledetección*, 61, 43–58.
  https://doi.org/10.4995/raet.2023.18155
