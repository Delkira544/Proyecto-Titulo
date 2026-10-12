# ADR-0012: Partición temporal de los datos con validación cruzada complementaria

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente; ajustado en la revisión |
| **Relacionado con** | RF-10, RNF-04, OE2, OE3, ADR-0017 |

## Contexto

La pregunta de transferibilidad exige evaluar los umbrales sobre datos no
usados para calibrarlos. Los píxeles de un mismo incendio son espacialmente
dependientes. Cuando los datos tienen estructura espacial o temporal, la
validación cruzada aleatoria subestima el error, y la validación por bloques
es más apropiada para predecir sobre datos nuevos (Roberts et al., 2017).

## Opciones consideradas

1. **Partición aleatoria de píxeles.** *Limitación:* píxeles vecinos del
   mismo incendio caerían en calibración y validación, lo que filtra
   información y sobrestima el desempeño.
2. **Partición aleatoria de incendios.** *Ventaja:* respeta la dependencia
   dentro de cada incendio. *Limitación:* no representa la aplicación real,
   que es usar umbrales históricos sobre un evento futuro.
3. **Partición temporal:** incendios 2020–2025 para calibración y evento de
   enero de 2026 para validación, con validación cruzada dejando un incendio
   fuera dentro del conjunto de calibración.
   *Ventaja:* reproduce la aplicación real y respeta la dependencia espacial.

## Decisión

Se adopta la partición temporal. La validación cruzada dejando un incendio
fuera se ejecuta como análisis complementario de la estabilidad de los
umbrales (RF-10, prioridad *Should*), y no forma parte del criterio de
cumplimiento de OE2.

## Consecuencias

**Positivas**
- La evaluación reproduce el uso operacional: umbrales calibrados con
  eventos pasados aplicados a un evento nuevo.
- Cada incendio actúa como un bloque, en línea con Roberts et al. (2017).

**Negativas**
- La validación externa depende de un único evento, lo que limita la
  generalización y debe declararse.

## Referencias

- Miller, J. D. et al. (2009). *Remote Sensing of Environment*, 113(3),
  645–656. https://doi.org/10.1016/j.rse.2008.11.009
- Roberts, D. R. et al. (2017). Cross-validation strategies for data with
  temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*,
  40(8), 913–929. https://doi.org/10.1111/ecog.02881
