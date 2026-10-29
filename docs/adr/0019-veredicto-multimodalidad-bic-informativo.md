# ADR-0019: Veredicto de multimodalidad por Silverman y dip, con el BIC solo como información

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-29 |
| **Origen** | Primera ejecución de la etapa 06 (HU-01.1) |
| **Relacionado con** | RF-07, OE1, supuesto S1, ADR-0009, ADR-0010 |

## Contexto

ADR-0009 fija la prueba de Silverman como principal y el dip de Hartigan como
verificación complementaria. La historia HU-01.1 pide además ajustar mezclas
gaussianas y elegir el número de componentes por BIC. Ninguno de los dos
registros dice cómo se combinan las tres evidencias en un veredicto.

La primera versión de la etapa 06 trató «el BIC elige k ≥ 2» como evidencia de
multimodalidad al mismo nivel que las pruebas de hipótesis. Con la tabla de
valores de píxel (unos 2,6 millones de píxeles forestales; submuestras de
20 000) las 12 combinaciones índice-estrato resultaron «discordantes»: el BIC
eligió k ≥ 2 en todas y llegó al máximo permitido (k = 5) en 7 de ellas, aunque
el dip no rechazó la unimodalidad en ninguna. Una mezcla de gaussianas puede
necesitar varias componentes para describir una sola distribución asimétrica,
de modo que el número de componentes no equivale al número de modas.

Este cambio se decide después de ver los resultados de esa primera ejecución.
No modifica ningún parámetro de decisión del config (α, proporción mínima,
percentiles); corrige una regla lógica que contaba como evidencia algo que no
mide modas. Los resultados anteriores se conservan en el historial de Git.

## Opciones consideradas

1. **Mantener la regla original.**
   *Ventaja:* ningún cambio posterior a los resultados.
   *Limitación:* el veredicto «discordante» deja de distinguir casos y no
   informa sobre la estructura de los datos.
2. **Veredicto por Silverman y dip; el BIC solo se reporta.**
   *Ventaja:* cada prueba contrasta la hipótesis para la que se diseñó.
   *Limitación:* el BIC queda como información descriptiva, sin peso en la
   decisión.
3. **Además, repetir el BIC con un máximo de componentes mayor.**
   *Ventaja:* comprueba si k se estabiliza.
   *Limitación:* no resuelve la diferencia entre componentes y modas.

## Decisión

Se adopta la opción 2.

- La decisión final de cada combinación la fija Silverman (ADR-0009): si
  rechaza la unimodalidad con el nivel α del config, la combinación es
  multimodal y conserva Otsu y KDE; si no, es unimodal y pasa a percentiles
  (ADR-0010).
- El veredicto es `multimodal` o `unimodal` cuando Silverman y el dip
  coinciden, y `discordante` cuando se contradicen. En los casos discordantes
  la decisión final sigue siendo la de Silverman.
- El número de componentes según BIC y la diferencia de BIC con el segundo
  mejor modelo se reportan en la tabla de resultados, sin intervenir en el
  veredicto.
- La prueba de Silverman se implementa con la calibración de Hall y York
  (2001, Método 1), porque la versión sin calibrar es conservadora y tiene poca
  potencia.

## Consecuencias

**Positivas**
- El veredicto depende solo de pruebas que contrastan modalidad.
- El «discordante» queda reservado a la contradicción real entre las dos
  pruebas de hipótesis.

**Negativas**
- La regla se fijó después de conocer los resultados de la primera ejecución,
  lo que va contra el criterio de ADR-0010 de definir las reglas antes. Se
  mitiga porque la decisión final (Silverman) no cambió en ninguna combinación;
  solo cambió el rótulo del veredicto.
- El BIC no aporta al veredicto. El número de clases de Otsu no debe tomarse
  del BIC sin una justificación adicional.

**Pendientes**
- Los p-valores son orientativos: los píxeles vecinos están autocorrelacionados
  y el submuestreo no elimina esa dependencia.
- Reportar la sensibilidad por incendio (ya generada) al discutir los
  resultados, porque la fracción de incendios multimodales varía entre
  combinaciones.
- No se halló una fuente verificada que respalde el valor del umbral de
  proporción (0,5), α = 0,05 de forma específica para este uso, ni los
  percentiles de contingencia; se declaran como convención de diseño.

## Referencias

- Silverman, B. W. (1981). Using kernel density estimates to investigate
  multimodality. *Journal of the Royal Statistical Society: Series B*, 43(1),
  97–99. https://doi.org/10.1111/j.2517-6161.1981.tb01155.x
- Hall, P. y York, M. (2001). On the calibration of Silverman's test for
  multimodality. *Statistica Sinica*, 11, 515–536.
- Hartigan, J. A. y Hartigan, P. M. (1985). The dip test of unimodality. *The
  Annals of Statistics*, 13(1), 70–84. https://doi.org/10.1214/aos/1176346577
- Fraley, C. y Raftery, A. E. (2002). Model-based clustering, discriminant
  analysis, and density estimation. *Journal of the American Statistical
  Association*, 97(458), 611–631. (Selección del número de componentes por BIC.)
- Sobre la diferencia entre componentes de una mezcla y modas: Ray, S. y
  Lindsay, B. G. (2005), *The topography of multivariate normal mixtures*,
  *The Annals of Statistics*, 33(5), 2042–2065. `[POR VERIFICAR]`
