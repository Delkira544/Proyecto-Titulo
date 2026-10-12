# ADR-0010: Umbrales por percentiles como contingencia ante falta de multimodalidad

| Campo | Valor |
|---|---|
| **Estado** | Propuesto (contingencia) |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-08 a RF-10, OE2, supuesto S1, ADR-0006, ADR-0009 |

## Contexto

Otsu y KDE (ADR-0006) requieren que las distribuciones presenten modas
separables. Si la prueba de multimodalidad (ADR-0009) resulta negativa para
una proporción relevante de las combinaciones de índice y estrato, esos
métodos producirían cortes sin sustento en la estructura de los datos.

Este registro define la alternativa antes de conocer el resultado.

## Opciones consideradas

1. **Excluir las combinaciones sin multimodalidad.**
   *Ventaja:* conserva la coherencia del método. *Limitación:* si son
   muchas, la comparación pierde cobertura.
2. **Derivar umbrales por percentiles de la distribución del índice.**
   *Ventaja:* aplicable a cualquier distribución. *Limitación:* los cortes
   dejan de reflejar una separación natural entre poblaciones.

## Decisión

Si el supuesto S1 no se cumple en una proporción relevante de combinaciones,
se adopta la opción 2 para esas combinaciones: los cortes se definen por
percentiles de la distribución del índice dentro del perímetro, con los
percentiles fijados en la configuración. Las combinaciones multimodales
mantienen Otsu y KDE.

**Criterio de activación:** la proporción de combinaciones multimodales es
inferior al umbral definido en la configuración. *(Pendiente: fijar este
umbral antes de ejecutar el spike HU-01.1.)*

## Consecuencias

**Positivas**
- OE2 puede cumplirse aunque falle el supuesto S1; cambia el método, no el
  objetivo.

**Negativas**
- Los umbrales por percentiles no son comparables en su fundamento con los
  obtenidos por Otsu y KDE, lo que debe declararse al interpretar los
  resultados.

**Pendientes**
- Fijar el umbral de activación y los percentiles antes de conocer los
  resultados, para que la contingencia no se ajuste a posteriori.
