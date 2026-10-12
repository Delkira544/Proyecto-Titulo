# ADR-0017: Archivo de configuración como fuente única de parámetros y de la partición de datos

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1 (RNF-05); ampliado en la revisión (RNF-04, RNF-12) |
| **Relacionado con** | RNF-04, RNF-05, RNF-12, RF-18, OE5, ADR-0004, ADR-0012, ADR-0018 |

## Contexto

El método depende de parámetros discrecionales: ancho de banda de KDE,
número de clases, ancho de la banda de entorno, ancho de exclusión de bordes,
tamaño de muestra, nivel de significancia y margen de equivalencia. Si estos
valores quedan dispersos en el código, no es posible saber con qué
configuración se produjo cada resultado.

Además, la validez del estudio depende de que los incendios de calibración y
el evento de validación nunca se mezclen (RNF-04).

## Opciones consideradas

1. **Parámetros definidos dentro del código.**
   *Limitación:* cambios difíciles de rastrear y fáciles de olvidar.
2. **Parámetros en argumentos de línea de comandos.**
   *Limitación:* la configuración de cada ejecución no queda registrada en el
   repositorio.
3. **Un único archivo `config/config.yaml` versionado**, que contiene los
   parámetros, los identificadores de escena y las listas de incendios de
   calibración y de validación.

## Decisión

Se adopta la opción 3. Todo parámetro discrecional, los identificadores de
escena (ADR-0004) y las listas de incendios se definen en `config/config.yaml`.
Los conjuntos de calibración y de validación se declaran en listas separadas,
de las que el flujo de trabajo (ADR-0018) deriva rutas de datos
independientes.

## Consecuencias

**Positivas**
- Cada resultado queda asociado a una versión concreta de la configuración
  mediante el historial de Git.
- La separación entre calibración y validación queda garantizada por
  construcción, y no depende de la disciplina manual.
- Reejecutar el estudio en otra región o temporada solo requiere un archivo
  de configuración nuevo.

**Negativas**
- Todo parámetro nuevo debe agregarse a la configuración, lo que exige
  disciplina.

## Referencias

- Sandve, G. K. et al. (2013). Ten simple rules for reproducible
  computational research. *PLoS Computational Biology*, 9(10), e1003285.
  https://doi.org/10.1371/journal.pcbi.1003285
- Wilson, G. et al. (2017). Good enough practices in scientific computing.
  *PLoS Computational Biology*, 13(6), e1005510.
  https://doi.org/10.1371/journal.pcbi.1005510
