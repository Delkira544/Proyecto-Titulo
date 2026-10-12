# ADR-0008: Escenario B, referencia mediante GeoCBI fotointerpretado

| Campo | Valor |
|---|---|
| **Estado** | Propuesto (contingencia) |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-12 a RF-16, OE4, supuesto S2, ADR-0007 |

## Contexto

El ADR-0007 adopta EMSR859 como referencia de validación. La validación del
nivel de severidad depende de que el atributo de grado de daño esté poblado en
la capa del producto (supuesto S2), lo que se verifica en el spike HU-04.1. Si
el atributo no está disponible, EMSR859 solo permitiría validar la distinción
entre superficie quemada y no quemada.

Este registro deja definida la contingencia antes de conocer el resultado de
la verificación.

## Opciones consideradas

1. **Restringir la validación al nivel de superficie quemada.**
   *Ventaja:* no requiere trabajo adicional. *Limitación:* deja sin
   responder la pregunta de investigación, que es sobre severidad.
2. **Construir una referencia propia mediante GeoCBI fotointerpretado**
   sobre imágenes de alta resolución, en los puntos de la muestra.
   *Ventaja:* mantiene la validación en el nivel de severidad.
   *Limitación:* la referencia pasa a ser de elaboración propia.
3. **Usar datos CBI de terreno levantados por CONAF.**
   *Ventaja:* mediciones de campo. *Limitación:* su obtención depende de una
   solicitud formal con plazos inciertos; clasificado como *Won't* para este
   proyecto.

## Decisión

Si el supuesto S2 no se cumple, se adopta la opción 2: la referencia de
severidad se construye mediante GeoCBI fotointerpretado en los puntos de la
muestra estratificada (ADR-0013).

**Criterio de activación:** el spike HU-04.1 concluye que el atributo de grado
de daño no está poblado, o que no admite una correspondencia defendible con
clases de severidad (ADR-0014). Al activarse, este registro pasa a estado
*Aceptado* y el ADR-0007 se actualiza para indicar que su validación de
severidad fue reemplazada.

## Consecuencias

**Positivas**
- La pregunta de investigación puede responderse aunque falle el supuesto S2.

**Negativas**
- La referencia deja de ser externa en el nivel de severidad, lo que
  introduce el riesgo de subjetividad del intérprete.

**Pendientes**
- Si se activa: documentar el protocolo de fotointerpretación e interpretar
  los puntos sin ver los mapas clasificados, para evitar sesgos.

## Referencias

- De Santis, A. y Chuvieco, E. (2009). GeoCBI: A modified version of the
  Composite Burn Index for the initial assessment of the short-term burn
  severity from remotely sensed data. *Remote Sensing of Environment*,
  113(3), 554–562. https://doi.org/10.1016/j.rse.2008.10.011
  *(verificar volumen, páginas y DOI antes de citar)*
