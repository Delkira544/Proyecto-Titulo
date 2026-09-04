# Backlog — Clasificación de severidad de daño post-incendio en Biobío

**Autor:** Christian Verdugo Troncoso · **Profesor guía:** Prof. Levano
**Prioridad:** P0 (bloqueante) · P1 (necesario) · P2 (cierre)

---

## Épicas y su relación con los objetivos

| Épica | Objetivo | Prioridad |
|---|---|---|
| E0 — Infraestructura de datos | Base para el resto del trabajo | P0 |
| E1 — Caracterización y multimodalidad | OE1 | P0 |
| E2 — Umbrales regionales | OE2 | P0 |
| E3 — Clasificación del evento de validación | OE3 | P0 |
| E4 — Evaluación de exactitud contra EMSR859 | OE4 | P0 |
| E5 — Documentación y cierre | OE5 | P1/P2 |

Orden de trabajo: E0 → E1 → E2 → E3 → E4 → E5. Cada épica necesita las salidas de la anterior, así que no tiene sentido adelantar una sin cerrar la que la precede.

---

## E0 — Infraestructura de datos

### HU-00.1 — Pipeline en GEE para calcular los índices espectrales
**Historia:** Como tesista, quiero exportar desde Google Earth Engine los índices espectrales (dNBR, RdNBR, BAI, MIRBI) ya recortados por perímetro y por estrato CONAF, para no tener que procesar cada incendio a mano.
**Tareas técnicas:**
- Filtrar y componer la colección Sentinel-2 L2A (pre/post incendio, libre de nubes).
- Calcular los cuatro índices y recortarlos al perímetro + buffer.
- Cruzar el recorte con el catastro de uso de suelo CONAF para etiquetar cada píxel por estrato.
**Criterios de aceptación:**
- Dado un incendio con polígono y fechas, el script entrega los 4 índices ya recortados y estratificados.
- El export queda en un formato reutilizable (GeoTIFF o tabla) con nombres consistentes.
**Estimación:** L · **Prioridad:** P0

### HU-00.2 — Repositorio y catálogo de incendios usables
**Historia:** Como tesista, quiero dejar el repositorio versionado y armar un catálogo con el porcentaje de nubosidad de los incendios 2020-2025, para saber de entrada con qué eventos puedo trabajar y dejar todo reproducible desde el inicio.
**Tareas técnicas:**
- Definir la estructura del repo (`/gee`, `/src`, `/docs`) y fijar versiones de las librerías.
- Revisar nubosidad de las escenas pre/post por incendio y marcar cuáles son usables.
**Criterios de aceptación:**
- El repo compila el entorno sin ajustes manuales.
- El catálogo indica, para cada incendio, si queda dentro o fuera del análisis y por qué.
**Estimación:** M · **Prioridad:** P0

---

## E1 (OE1) — Caracterización estadística y multimodalidad

### HU-01.1 (Spike) — Verificar si los índices se separan en clases por estrato
**Historia:** Como tesista, quiero correr el test de dip de Hartigan y comparar modelos de mezcla gaussiana (seleccionados por BIC) sobre cada índice y estrato, para saber en qué combinaciones se puede aplicar Otsu/KDE y en cuáles hay que usar otro método (percentiles).
**Tareas técnicas:**
- Implementar el dip test sobre los valores extraídos en HU-01.2.
- Ajustar modelos de mezcla gaussiana y elegir el número de componentes con BIC.
- Armar una tabla resumen con el resultado por combinación índice-estrato.
**Criterios de aceptación:**
- Cada combinación índice-estrato tiene su p-valor del dip test y su número de componentes según BIC.
- Si alguna combinación resulta unimodal, queda registrada la decisión de pasar a percentiles para ese caso.
**Estimación:** M · **Prioridad:** P0 — bloquea E2

### HU-01.2 — Extracción y estadística descriptiva de los índices
**Historia:** Como tesista, quiero sacar los valores de píxel de cada índice dentro del perímetro y su entorno inmediato, y describirlos estadísticamente por estrato, para tener el insumo del spike anterior y del capítulo de resultados.
**Tareas técnicas:**
- Extraer valores de píxel por incendio, estrato e índice, con la banda "dentro del perímetro" marcada.
- Generar histogramas y estadísticos resumen (media, mediana, IQR, asimetría) por combinación.
**Criterios de aceptación:**
- Existe una tabla con valor de píxel, incendio, estrato e índice para todos los incendios usables.
- Los histogramas y la tabla resumen quedan listos para incorporar al documento.
**Estimación:** M · **Prioridad:** P0

---

## E2 (OE2) — Derivación y consolidación de umbrales regionales

### HU-02.1 — Umbrales Otsu y KDE del conjunto de calibración
**Historia:** Como tesista, quiero calcular el umbral Otsu y el umbral KDE por incendio, índice y estrato en el conjunto 2020-2025, para tener la distribución de la que después se saca el umbral regional.
**Tareas técnicas:**
- Aplicar Otsu multinivel (`skimage.filters.threshold_multiotsu`) a cada combinación multimodal.
- Aplicar KDE (`scipy.stats.gaussian_kde`) ajustando el ancho de banda hasta encontrar los mínimos esperados.
- Guardar ambos resultados en tablas comparables.
**Criterios de aceptación:**
- Cada combinación índice-estrato-incendio marcada como multimodal tiene un umbral Otsu y un umbral KDE calculados.
**Estimación:** L · **Prioridad:** P0

### HU-02.2 — Umbral regional consolidado y su estabilidad
**Historia:** Como tesista, quiero consolidar los umbrales por mediana y medir su estabilidad con validación cruzada dejando un incendio fuera, para llegar al umbral calibrado regional con una idea de cuánto varía.
**Tareas técnicas:**
- Calcular la mediana, el IQR y el coeficiente de variación por combinación índice-estrato.
- Correr la validación leave-one-out y comparar el umbral resultante en cada iteración.
**Criterios de aceptación:**
- Existe un umbral regional final por índice y estrato, con su mediana, IQR y CV documentados.
- Cada combinación queda marcada como estable o inestable según el criterio CV ≤ 0.20.
**Estimación:** M · **Prioridad:** P1

---

## E3 (OE3) — Clasificación del evento de validación (Lirquén-Penco-Concepción)

### HU-03.1 — Preprocesar el evento de enero de 2026
**Historia:** Como tesista, quiero calcular los índices espectrales del incendio sobre las cuatro AOI de EMSR859, para tener la base común que después clasifico con las tres estrategias de umbral.
**Tareas técnicas:**
- Componer las escenas pre/post del evento para cada AOI (San Rosendo, Chiguayhue, Santa Bárbara, Concepción/Lirquén).
- Calcular los cuatro índices sobre cada AOI.
**Criterios de aceptación:**
- Los cuatro índices están calculados y recortados para las cuatro AOI.
**Estimación:** M · **Prioridad:** P0

### HU-03.2 — Clasificar con las tres estrategias de umbral
**Historia:** Como tesista, quiero clasificar el evento con el umbral internacional (Key & Benson), el umbral regional y un umbral ad hoc calculado directamente sobre Lirquén, para tener las tres clasificaciones que se van a comparar contra EMSR859.
**Tareas técnicas:**
- Aplicar los cortes FIREMON directamente sobre los índices del evento.
- Aplicar el umbral regional de HU-02.2.
- Calcular Otsu/KDE sobre los índices del propio evento y clasificar con ese resultado.
**Criterios de aceptación:**
- Existe un mapa de severidad por AOI e índice para cada una de las tres estrategias, en el mismo formato.
**Estimación:** M · **Prioridad:** P0

---

## E4 (OE4) — Evaluación de exactitud contra EMSR859

### HU-04.1 (Spike) — Definir si la validación sigue el Escenario A o el B
**Historia:** Como tesista, quiero revisar la tabla de atributos de la capa de grading de EMSR859 para confirmar si el grado de daño en vegetación está poblado, y así decidir si valido directamente contra EMSR859 o si necesito armar un GeoCBI fotointerpretado propio.
**Tareas técnicas:**
- Abrir el shapefile de grading y revisar los campos y valores de la capa de cobertura vegetal.
- Documentar el hallazgo y registrar la decisión (Escenario A o B).
**Criterios de aceptación:**
- Queda escrita la decisión (A o B) junto con la evidencia que la sustenta.
**Estimación:** S · **Prioridad:** P0 — bloquea el resto de E4

### HU-04.2 — Muestreo y matrices de confusión
**Historia:** Como tesista, quiero diseñar el muestreo aleatorio estratificado siguiendo a Olofsson et al. (2014) y calcular matrices de confusión, exactitud global y Kappa para las tres estrategias, para comparar su desempeño contra el mismo ground truth.
**Tareas técnicas:**
- Definir el tamaño de muestra por clase y aplicar el buffer de exclusión en bordes.
- Calcular matriz de confusión, exactitud global, Kappa e intervalos de confianza por estrategia, índice y AOI.
**Criterios de aceptación:**
- El muestreo tiene al menos 50 puntos por clase.
- Cada estrategia tiene su matriz de confusión, exactitud global y Kappa calculados y desagregados por AOI.
**Estimación:** L · **Prioridad:** P0

### HU-04.3 — Comparar el desempeño de las tres estrategias
**Historia:** Como tesista, quiero probar si las diferencias de exactitud entre las tres estrategias son estadísticamente significativas, para poder afirmar con sustento cuál transfiere mejor.
**Tareas técnicas:**
- Aplicar la prueba correspondiente (McNemar o bootstrap) a cada par de estrategias.
**Criterios de aceptación:**
- Quedan reportados los resultados de las tres comparaciones posibles (internacional-regional, regional-ad hoc, internacional-ad hoc).
**Estimación:** M · **Prioridad:** P1

---

## E5 (OE5) — Documentación y cierre

### HU-05.1 — Limitaciones y repositorio reproducible
**Historia:** Como tesista, quiero escribir las condiciones de aplicabilidad y las limitaciones del trabajo, y dejar el repositorio publicado con instrucciones claras, para cerrar OE5.
**Tareas técnicas:**
- Redactar la sección de limitaciones con base en los resultados de E4.
- Escribir el README con los pasos para reproducir el pipeline completo.
**Criterios de aceptación:**
- La sección de limitaciones está redactada y se apoya en cifras concretas de E4.
- El repositorio queda publicado con un README que permite reproducir el procedimiento paso a paso.
**Estimación:** M · **Prioridad:** P1

### HU-05.2 — Redactar metodología y resultados
**Historia:** Como tesista, quiero escribir los capítulos de metodología y resultados con las salidas de E1 a E4, para dejar el documento cerrado.
**Tareas técnicas:**
- Integrar figuras y tablas generadas en E1-E4 al documento LaTeX.
- Revisar que las citas queden alineadas con `referencias.bib`.
**Criterios de aceptación:**
- Los capítulos compilan sin errores y todas las cifras citadas provienen de los scripts de E1-E4.
**Estimación:** L · **Prioridad:** P2 — depende de que E1-E4 estén cerradas

---

## Orden de priorización

1. HU-00.2
2. HU-00.1
3. HU-01.2
4. **HU-01.1** (spike)
5. HU-02.1
6. HU-02.2
7. HU-03.1
8. HU-03.2
9. **HU-04.1** (spike)
10. HU-04.2
11. HU-04.3
12. HU-05.1
13. HU-05.2
