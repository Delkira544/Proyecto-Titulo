# ADR-0020: Validar en el nivel de superficie quemada con EMSR859 y comparar la severidad sin referencia externa

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-29 |
| **Origen** | Spike HU-04.1 (revisión de la capa de grado de daño de EMSR859) |
| **Relacionado con** | RF-12 a RF-16, OE4, OE5 (propuesto), supuestos S2 y S4, ADR-0007, ADR-0008, ADR-0013, ADR-0014, ADR-0016, ADR-0021 |

## Contexto

El ADR-0007 adopta EMSR859 como referencia de validación y el ADR-0008 deja
definida la contingencia si el atributo de grado de daño no está poblado
(supuesto S2). El spike HU-04.1 revisó todos los productos disponibles de la
activación: los *Grading* (GRA) de las cuatro AOI del repositorio y, como
contraste, la delimitación inicial (DEL) y sus monitoreos (DEL MONIT01–03),
74 capas en total. La evidencia reproducible la genera la regla
`inspect_emsr859` en `results/emsr859_spike_hu041.md` y
`results/tables/emsr859_*.tsv`.

Capa *Grading – Areas – Affected land use-cover* (`naturalLandUseA`):

| AOI | Polígonos | `damage_gra` | `det_method` | `notation` / `cd_value` |
|---|---|---|---|---|
| 01 San Rosendo (v3) | 788 | Affected = 100 % | Automatic extraction | Not Applicable |
| 02 Chiguaihue (v2) | 802 | Affected = 100 % | Semi-automatic extraction | Not Applicable |
| 03 Santa Bárbara (v1) | sin capa | — | — | — |
| 04 Concepción (v2) | 7181 | Affected = 100 % | Automatic extraction | Not Applicable |

- La capa es el área quemada intersectada con *Copernicus Global Land Cover
  2019* (100 m; `or_src_id` = 982). El estilo (SLD) declara un único valor de
  `damage_gra`.
- Las tablas resumen (`summaryTable.xlsx`) solo gradúan edificios e
  infraestructura (*Destroyed / Damaged / Possibly damaged*). Para el uso de
  suelo entregan solo «Total affected» y «Total in AOI», con inconsistencias
  internas: la hoja «Grading» informa 0 ha de bosque afectado en AOI02 y AOI04
  mientras su hoja de detalle informa 1123 y 12 205 ha, y en AOI01 y AOI03 la
  vegetación dentro del área quemada figura como «Not Affected».
- En Copernicus EMS, los productos de *Grading* evalúan la severidad del
  **daño a bienes expuestos**, y los de *Delineation* la extensión del evento
  \parencite{CopernicusEMS2025}. No es la severidad de quemado de la vegetación.
- Ningún producto DEL ni DEL MONIT trae un atributo de grado para la vegetación.

Por lo tanto, **no se cumple el supuesto S2** y se cumple el criterio de
activación del ADR-0008. Su contingencia (GeoCBI fotointerpretado) depende de
imágenes de muy alta resolución de febrero–marzo de 2026 a las que no se tiene
acceso. Además, el GeoCBI es un protocolo de terreno
\parencite{DeSantisChuvieco2009} [POR VERIFICAR clave]: desde imágenes solo se
observa el dosel, y no se encontró literatura revisada por pares que valide su
puntuación por fotointerpretación.

La capa `observedEventA` (área quemada) sí está en las cuatro AOI, derivada con
sensores independientes de Sentinel-2 en la imagen post (PlanetScope 3 m,
SPOT-6/7 1,5 m, Pléiades 0,5 m).

Por último, la revisión de las AOI contra el límite regional
(`limites_chile/Regiones`, código 8) mostró que AOI02 queda fuera del Biobío
(0 %) y AOI03 solo en parte (29 % del AOI; 2908 de 7908 ha quemadas).

## Opciones consideradas

1. **GeoCBI fotointerpretado (ADR-0008).** *Ventaja:* valida la severidad.
   *Limitación:* depende de imágenes no disponibles; la referencia es propia y
   su método no está validado en la literatura.
2. **Validación binaria contra EMSR859 y comparación de la severidad sin
   referencia externa.** *Ventaja:* factible con los datos disponibles y con
   una referencia externa e independiente. *Limitación:* no mide la exactitud
   de los niveles de severidad.
3. **Fotointerpretación sobre Sentinel-2.** *Limitación:* circular, porque es
   el mismo sensor del que derivan los índices.

## Decisión

Se adopta la opción 2, en dos niveles:

1. **Superficie quemada (OE4).** Para cada estrategia (internacional,
   regional y ad hoc), el umbral entre «no quemado» y «baja» se evalúa contra
   EMSR859. Se mantienen el muestreo (ADR-0013), las métricas (ADR-0015) y los
   criterios de decisión (ADR-0016).
2. **Niveles de severidad (OE5, propuesto).** Las estrategias se comparan por
   la diferencia entre sus umbrales, el desacuerdo entre mapas en cantidad y
   asignación \parencite{PontiusMillones2011} [POR VERIFICAR clave] y la
   estabilidad de los umbrales regionales (validación cruzada dejando un
   incendio fuera). Se reportan como discrepancia, no como exactitud.

Reglas de la referencia:

- **Producto:** `observedEventA` del GRA de cada AOI. No se usan DEL ni
  DEL MONIT, por tres razones: (i) los DEL MONIT01 de las AOI 02, 03 y 04 se
  derivaron de Sentinel-2, lo que introduciría circularidad; (ii) el GRA es el
  producto homogéneo y más tardío de cada AOI (imágenes post del 20 al 25 de
  enero de 2026); (iii) es coherente con la capa revisada para S2.
- **AOI:** se usan AOI01 (`emsr2026-001`), AOI03 recortado a la parte en el
  Biobío (`emsr2026-003`) y AOI04 (`emsr2026-004`). Se excluye AOI02, porque
  queda fuera de la región de estudio.
- **Zona de trabajo:** AOI ∩ Biobío − zonas que EMS declaró sin analizar
  (`notAnalysedA` y huellas «Not Analysed – No data»). Dentro de ella,
  «quemado» = `observedEventA` y «no quemado» = el resto.
- **Fechas:** inicio del evento el 16/01/2026 según Copernicus EMS (ancla de la
  escena pre). El ancla de la escena post es la fecha de la imagen post del GRA
  de cada AOI (21, 24 y 25 de enero).
- **Correspondencia de clases** (completa el ADR-0014): «Burnt area» ↔
  {baja, moderada, alta}; fuera de `observedEventA` ↔ no quemado.

## Consecuencias

**Positivas**
- La validación se mantiene externa e independiente del sensor evaluado.
- Se conservan el objeto de estudio (el umbral), las tres estrategias y la
  partición temporal (ADR-0012).
- La cadena del evento de validación reutiliza las reglas de nubosidad y
  exportación con archivos propios del rol `validacion`. Una prueba automática
  (`tests/test_no_leakage.py`) verifica que la calibración no depende de ella.

**Negativas**
- La exactitud de los niveles de severidad queda fuera del alcance y se
  declara como limitación.
- La pregunta de investigación y el OE4 se reformulan, y se agrega el OE5.
- EMSR859 es una estimación y no verdad de terreno: los resultados se
  reportan como concordancia (ADR-0007).
- El área quemada del GRA es menor que la de monitoreos previos en AOI04
  (12 781 frente a 13 672 ha) y AOI03 (7894 frente a 8503 ha), aunque los
  mapas indiquen que acumula las extensiones anteriores. Se reporta y no se
  corrige.
- Tras disolver, en AOI04 quedan 2485 de 3930 partes más chicas que la unidad
  mínima de mapeo declarada (225 m²). Su efecto se controla al pasar a la grilla
  de Sentinel-2 (regla > 50 % y buffer de exclusión, ADR-0014).
- La escena post de Sentinel-2 es posterior a la imagen de referencia. Si el
  incendio siguió activo, parte del área quemada en la escena no figura en la
  referencia y aparece como comisión.

**Pendientes**
- Validar con el profesor guía la reformulación de la pregunta y del OE4, y el
  OE5 nuevo.
- Fecha de descarga y licencia de EMSR859 en el manifiesto; fuente, versión y
  licencia de `limites_chile`.
- Fijar el margen de equivalencia Δ (ADR-0016) antes de evaluar.
- Si se obtienen imágenes de muy alta resolución, el GeoCBI puede retomarse
  como análisis complementario sin modificar este registro.

## Referencias

- Copernicus Emergency Management Service (2025). *Rapid Mapping Manual*.
  https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/ (clave
  `CopernicusEMS2025`).
- Copernicus EMS (2026). *Wildfires in the Biobío and Ñuble regions, Chile
  (EMSR859)*. Noticia de la activación, 21/01/2026.
  https://mapping.emergency.copernicus.eu/news/wildfires-in-the-biobio-and-nuble-regions-chile-emsr859/
- De Santis, A. y Chuvieco, E. (2009). *Remote Sensing of Environment*,
  113(3), 554–562. [POR VERIFICAR]
- Olofsson, P. et al. (2014). *Remote Sensing of Environment*, 148, 42–57.
- Pontius, R. G. y Millones, M. (2011). *International Journal of Remote
  Sensing*, 32(15), 4407–4429. [POR VERIFICAR]
