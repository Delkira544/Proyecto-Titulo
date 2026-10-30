# ADR-0021: Adoptar EPSG:32719 (UTM 19S) como CRS único del proyecto

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-29 |
| **Origen** | Preparación de la referencia del evento de validación (ADR-0020) |
| **Relacionado con** | RNF de reproducibilidad, ADR-0003, ADR-0017, ADR-0020 |

## Contexto

Los insumos llegan en CRS distintos: perímetros CONAF en EPSG:32719 (UTM 19S),
catastro SIT de CONAF en EPSG:32718 (UTM 18S), EMSR859 en EPSG:4326 y los
límites regionales en EPSG:3857. Las áreas y distancias deben calcularse en un
CRS proyectado (CLAUDE.md §7.3). Hasta ahora, `crs_trabajo` y `crs_export`
estaban fijados en EPSG:32719 como valor provisorio.

El Biobío se extiende de 70,98° a 73,96° W y cruza el límite entre los husos
UTM 18 y 19 (72° W). El mapa de EMSR859 para Concepción usa UTM 18S. Los
índices de los incendios de calibración ya están exportados desde Google Earth
Engine en la grilla EPSG:32719 (unos 200 productos en `results/processed`).

Factores de escala de área calculados con `pyproj.Proj.get_factors`:

| Punto | EPSG:32719 | EPSG:32718 |
|---|---|---|
| Costa (73,7° W; 37,5° S) | 1,00346 | 0,99953 |
| Concepción (73,0° W; 36,8° S) | 1,00234 | 0,99998 |
| San Rosendo (72,6° W; 37,3° S) | 1,00171 | 1,00031 |
| Cordillera (71,0° W; 37,5° S) | 0,99997 | 1,00228 |

## Opciones consideradas

1. **EPSG:32719 (UTM 19S).** *Ventaja:* CRS nativo de los perímetros de
   calibración y de todos los productos ya exportados. *Limitación:* la costa
   queda fuera de su huso; distorsión de área de hasta 0,35 %.
2. **EPSG:32718 (UTM 18S).** *Ventaja:* ajusta mejor la costa y Concepción.
   *Limitación:* distorsión de hasta 0,23 % en la cordillera, y obliga a
   re-exportar todos los índices desde Earth Engine, una fuente remota y no
   determinista (la colección puede actualizarse), con lo que se pierde la
   comparabilidad con lo ya calculado.
3. **Proyección equivalente (por ejemplo, Albers).** *Ventaja:* áreas
   exactas. *Limitación:* exige una definición propia (WKT) en la exportación
   de GEE y también obliga a re-exportar todo.

## Decisión

Se adopta la opción 1: **EPSG:32719 es el CRS único del proyecto** para el
cálculo de áreas, la grilla de los rásteres y la exportación desde GEE.

La distorsión máxima (0,35 % de área) es del mismo orden que la de la
alternativa (0,23 %). Es pequeña frente a la resolución de 20 m y afecta por
igual a las tres estrategias de umbral, porque todas se evalúan sobre la misma
grilla. Cambiar de CRS no mejoraría la comparación y sí costaría rehacer las
exportaciones.

## Consecuencias

**Positivas**
- No hay que re-exportar ni recalcular los productos de calibración.
- Una sola grilla para calibración y validación, sin remuestreos.

**Negativas**
- Las superficies se sobrestiman hasta un 0,35 % en el extremo occidental.
  Se reportan en EPSG:32719 indicando esta distorsión.

**Pendientes**
- Los vectores en otros CRS (SIT en 32718, EMSR859 en 4326, límites en 3857) se
  reproyectan de forma explícita antes de cualquier operación espacial, como ya
  hacen `04_label_pixel_strata.py` y `08_build_validation_perimeters.py`.
- Respaldo cartográfico de los factores de escala de la proyección transversa
  de Mercator: Snyder (1987) [POR VERIFICAR clave y páginas].

## Referencias

- Snyder, J. P. (1987). *Map Projections: A Working Manual*. U.S. Geological
  Survey Professional Paper 1395. [POR VERIFICAR]
