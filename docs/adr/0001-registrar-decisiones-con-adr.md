# ADR-0001: Registrar las decisiones de diseño mediante ADR

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Inicio de la Etapa 2 (Diseño e implementación inicial) |
| **Relacionado con** | RNF-06, RNF-08, RNF-10, OE5 |

## Contexto

El proyecto acumula decisiones de diseño con alternativas técnicamente
viables: método de clasificación, índices, referencia de validación, diseño de
muestreo, plataforma de procesamiento y gestión del flujo de trabajo, entre
otras. Hoy estas decisiones están dispersas en el documento de tesis, que no
registra cuándo se tomaron ni cómo cambiaron.

La rúbrica de la Etapa 2 exige documentar las decisiones técnicas, los cambios
implementados y la justificación de cualquier desviación del plan original.
Se necesita un registro versionado, ubicado junto al código, que permita
reconstruir por qué el diseño es como es.

## Opciones consideradas

1. **Registrar las decisiones solo en el documento de tesis.**
   *Ventaja:* no agrega artefactos. *Limitación:* el documento muestra el
   estado final y no conserva el historial de cambios ni su fecha.
2. **Usar la wiki o los issues de GitHub.**
   *Ventaja:* integrados en la plataforma. *Limitación:* quedan fuera del
   control de versiones del código y dependen del servicio.
3. **Registros de decisiones de arquitectura (ADR) en Markdown dentro del
   repositorio.**
   *Ventaja:* versionados con el código, legibles sin herramientas y con
   historial auditable mediante Git. *Limitación:* requieren disciplina para
   mantenerse al día.

## Decisión

Se adopta la opción 3, con las siguientes reglas:

- Los registros se ubican en `docs/adr/`, uno por decisión, con nombre
  `NNNN-titulo-en-minusculas.md` y numeración secuencial que no se reutiliza.
- La estructura sigue el formato de Nygard (título, estado, contexto,
  decisión y consecuencias), ampliado con una sección de opciones
  consideradas, una de referencias y una tabla de trazabilidad con los
  requisitos y objetivos de la tesis.
- Los estados posibles son *Propuesto*, *Aceptado*, *Obsoleto* y
  *Reemplazado por ADR-XXXX*.
- Un ADR aceptado no se modifica en su contenido. Si la decisión cambia, se
  redacta un ADR nuevo que reemplaza al anterior, y en este último solo se
  actualiza el estado.
- El índice `docs/adr/README.md` se actualiza con cada registro nuevo.
- Los commits que agregan o modifican registros usan el prefijo `docs(adr):`.

## Consecuencias

**Positivas**
- Cada decisión queda trazable a su contexto, sus alternativas y su
  respaldo bibliográfico.
- Las desviaciones del plan original quedan documentadas mediante registros
  que reemplazan a otros, sin reescribir la historia.
- El documento de tesis puede remitir a los ADR en lugar de repetir su
  contenido.

**Negativas**
- Agrega una tarea de documentación a cada decisión relevante.

**Pendientes**
- Las decisiones tomadas durante la Fase 1 se registran de forma
  retroactiva; la fecha de cada registro corresponde a su redacción, no a la
  de la decisión original.

## Referencias

- Nygard, M. (2011). *Documenting Architecture Decisions*.
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Architectural Decision Records. https://adr.github.io/
