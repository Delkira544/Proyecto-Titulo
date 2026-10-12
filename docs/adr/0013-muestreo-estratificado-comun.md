# ADR-0013: Muestreo aleatorio estratificado común a las tres estrategias

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1; estratificación ajustada en la revisión |
| **Relacionado con** | RF-13, RF-14a, RF-15, OE4, ADR-0014, ADR-0016 |

## Contexto

Las tres estrategias de umbral deben evaluarse contra la misma referencia y
compararse entre sí con rigor estadístico. La comparación de clasificaciones
evaluadas sobre los mismos puntos requiere pruebas para muestras
relacionadas, como la de McNemar (Foody, 2004). Si cada estrategia se
evaluara con una muestra distinta, esa comparación pareada no sería posible.

## Opciones consideradas

1. **Comparación exhaustiva de todos los píxeles.**
   *Ventaja:* simple de implementar. *Limitación:* los píxeles vecinos no son
   observaciones independientes, lo que sobrestima el tamaño muestral
   efectivo y la significancia; además, es inviable si la referencia debe
   fotointerpretarse (ADR-0008).
2. **Muestreo estratificado por las clases de cada mapa.**
   *Ventaja:* diseño estándar de Olofsson et al. (2014). *Limitación:* cada
   estrategia produce un mapa distinto y, por tanto, una muestra distinta.
3. **Muestreo estratificado por área de interés y uso de suelo, común a las
   tres estrategias.**
   *Ventaja:* una sola muestra permite comparaciones pareadas.
   *Limitación:* los estratos no coinciden con las clases del mapa, lo que
   exige estimadores específicos.

## Decisión

Se adopta la opción 3. Los estratos se definen por área de interés y categoría
de uso de suelo, independientes de cualquier clasificación. La exactitud y la
superficie se estiman con los estimadores para estratos distintos de las
clases del mapa (Stehman, 2014), siguiendo las buenas prácticas de Olofsson
et al. (2014).

## Consecuencias

**Positivas**
- La misma muestra sirve a las tres estrategias y habilita la prueba de
  McNemar.
- Los estimadores son insesgados y se reportan con intervalos de confianza.

**Negativas**
- Los resultados incluyen error de muestreo, que se reporta mediante
  intervalos de confianza.

**Pendientes**
- Fijar el tamaño muestral y la asignación por estrato en la configuración.
- Buscar una fuente que respalde el argumento de autocorrelación espacial de
  la opción 1.

## Referencias

- Foody, G. M. (2004). Thematic map comparison: evaluating the statistical
  significance of differences in classification accuracy. *Photogrammetric
  Engineering & Remote Sensing*, 70(5), 627–633.
  https://doi.org/10.14358/PERS.70.5.627
- Olofsson, P. et al. (2014). Good practices for estimating area and
  assessing accuracy of land change. *Remote Sensing of Environment*, 148,
  42–57. https://doi.org/10.1016/j.rse.2014.02.015
- Stehman, S. V. (2014). Estimating area and map accuracy for stratified
  random sampling when the strata are different from the map classes.
  *International Journal of Remote Sensing*, 35(13), 4923–4939.
  https://doi.org/10.1080/01431161.2014.930207
