# ADR-0011: Estratificar con el catastro de CONAF y usar sus polígonos solo como delimitadores

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-05, RF-06, RNF-03, OE1, OE2, supuestos S5 y S6, ADR-0007 |

## Contexto

La respuesta del dNBR varía según la cobertura de suelo, incluso dentro de una
misma región. En el Biobío, los umbrales que mejor delimitaron la superficie
quemada en 2017 fueron de 0,10 en plantaciones y bosque nativo, de 0,25 en
praderas y matorrales, y de 0,45 en terrenos agrícolas (Sánchez et al., 2023,
Tabla 2). Por eso los umbrales deben derivarse por estrato de uso de suelo.

A la vez, cada estrato necesita suficientes píxeles válidos para derivar
umbrales estables (supuesto S6), y los polígonos de CONAF no deben usarse como
referencia de exactitud (ADR-0007).

## Opciones consideradas

1. **Sin estratificación.** *Ventaja:* máximo número de píxeles.
   *Limitación:* ignora la dependencia de la señal respecto de la cobertura.
2. **Estratificación fina** (siete categorías, como Sánchez et al., 2023).
   *Ventaja:* mayor detalle. *Limitación:* varias categorías tienen poca
   superficie quemada, lo que compromete el mínimo de píxeles por estrato.
3. **Tres categorías agregadas: forestal, urbana y otras coberturas.**
   *Ventaja:* equilibra la heterogeneidad del paisaje con el tamaño muestral
   por estrato. *Limitación:* agrupa coberturas con respuestas distintas
   dentro de "otras".

## Decisión

Se adopta la estratificación en tres categorías a partir del catastro de uso
de suelo de CONAF. Los polígonos de incendio de CONAF se usan exclusivamente
para ubicar y delimitar los incendios de calibración, y nunca como referencia
de exactitud.

## Consecuencias

**Positivas**
- Los umbrales reflejan la dependencia de la señal respecto de la cobertura.
- Se mantiene la separación entre los datos de CONAF y la referencia de
  validación.

**Negativas**
- La categoría "otras coberturas" agrupa respuestas espectrales distintas.
  Sánchez et al. (2023) reportan un bajo desempeño en terrenos agrícolas,
  asociado a patrones espurios de la actividad agroindustrial.

**Pendientes**
- Supuesto S5: comparar la fecha de actualización del catastro con la de
  cada incendio. Si el catastro es posterior, usar la versión anterior al
  evento o declarar el supuesto, como hicieron Sánchez et al. (2023, p. 49).
- Supuesto S6: combinaciones con menos píxeles que el mínimo configurado se
  excluyen (RNF-03).

## Referencias

- Sánchez, R. et al. (2023). *Revista de Teledetección*, 61, 43–58.
  https://doi.org/10.4995/raet.2023.18155
