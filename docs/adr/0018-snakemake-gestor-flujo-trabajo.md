# ADR-0018: Snakemake como gestor del flujo de trabajo, con entornos conda por regla

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Revisión posterior a la Fase 1 |
| **Relacionado con** | RF-18, RNF-07, RNF-08, RNF-10, OE5, ADR-0003, ADR-0017 |

## Contexto

OE5 exige entregar un procedimiento reejecutable que regenere todos los
resultados. Si el análisis se ejecuta manualmente, mediante scripts o
cuadernos lanzados uno a uno, no hay garantía de que los resultados
reportados correspondan a la versión vigente del código y de los parámetros.
Sandve et al. (2013) recomiendan especificar el análisis completo en una
forma directamente ejecutable y mencionan los sistemas de flujos de trabajo
como una forma de lograrlo.

## Opciones consideradas

1. **Ejecución manual de scripts o cuadernos.**
   *Ventaja:* sin herramientas adicionales. *Limitación:* no garantiza la
   correspondencia entre resultados y código.
2. **Makefile.** *Ventaja:* ampliamente disponible. *Limitación:* sintaxis
   ajena a Python y manejo limitado de entornos de software.
3. **Nextflow.** *Ventaja:* robusto y escalable. *Limitación:* lenguaje
   distinto del resto del proyecto.
4. **Snakemake.** *Ventaja:* escrito en Python, con reglas de entrada y
   salida, entornos por regla y reporte de ejecución.
   *Limitación:* curva de aprendizaje inicial.

## Decisión

Se adopta Snakemake, porque está escrito en Python, el mismo lenguaje del
resto del proyecto, y porque su diseño apunta a análisis reproducibles,
adaptables y transparentes (Mölder et al., 2021).

- Cada etapa se define como una regla con entradas, salidas y entorno de
  software declarados.
- Cada regla declara su entorno conda con versiones fijadas (RNF-07).
- El flujo completo se ejecuta con un único comando a partir de
  `config/config.yaml` (ADR-0017).
- El reporte de ejecución vincula cada resultado con su código y sus
  parámetros (RNF-10).
- El diagrama de dependencias se genera con `snakemake --rulegraph` y se
  incluye en la documentación (RNF-08).

## Consecuencias

**Positivas**
- Todas las tablas y figuras de la tesis pueden regenerarse con un comando.
- Al cambiar un parámetro, solo se reejecutan los pasos afectados.
- El diagrama de dependencias se deriva del código y no puede quedar
  desactualizado.

**Negativas**
- Curva de aprendizaje inicial.
- Snakemake trabaja con archivos, por lo que la interacción asíncrona con
  Earth Engine debe resolverse descargando las escenas como archivos locales
  en la primera regla (ADR-0003).

**Pendientes**
- Construir el esqueleto del flujo al inicio de la implementación, para que
  cada etapa nueva nazca como una regla y no deba adaptarse al final.

## Referencias

- Köster, J. y Rahmann, S. (2012). Snakemake—a scalable bioinformatics
  workflow engine. *Bioinformatics*, 28(19), 2520–2522.
  https://doi.org/10.1093/bioinformatics/bts480
- Mölder, F. et al. (2021). Sustainable data analysis with Snakemake.
  *F1000Research*, 10, 33. https://doi.org/10.12688/f1000research.29032.2
- Sandve, G. K. et al. (2013). *PLoS Computational Biology*, 9(10), e1003285.
  https://doi.org/10.1371/journal.pcbi.1003285
