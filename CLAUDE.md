# CLAUDE.md — Transferibilidad de umbrales de severidad de incendios (Biobío, Chile)

Este archivo define las reglas de trabajo para Claude dentro de este proyecto. Léelo completo antes de responder o modificar archivos.

## 1. Contexto del proyecto

- **Tipo:** proyecto de título de Ingeniería Civil en Informática (UCT), guiado por el Prof. Levano.
- **Tema:** evaluar si los umbrales de severidad de incendio calibrados internacionalmente (Key & Benson, 2006) son transferibles al contexto chileno, o si umbrales calibrados regionalmente rinden mejor.
- **Zona y datos:** región del Biobío, imágenes Sentinel-2 L2A (nivel 2A: reflectancia de superficie ya corregida atmosféricamente).
- **Evento de validación:** incendio Lirquén-Penco-Concepción (enero 2026), con el producto EMSR859 de Copernicus EMS (Servicio de Gestión de Emergencias de Copernicus) como referencia independiente.
- **Calibración:** inventario de incendios del Biobío 2020–2025 (sin referencia de terreno disponible).

## 2. Regla de fuentes (prioridad máxima)

1. Toda información técnica o científica debe basarse en **fuentes verídicas y académicas**: literatura primaria revisada por pares (peer-reviewed: evaluada por expertos antes de publicarse), documentos oficiales o informes técnicos de instituciones reconocidas.
2. **No citar** wikis, blogs, foros, páginas comerciales ni documentación de plataformas como respaldo científico. Si aparecen, indicar que no son aptas para citar.
3. Si una afirmación **no tiene** una fuente académica que la respalde, decirlo explícitamente. No reemplazarla con otra fuente más débil ni inventar la referencia.
4. Nunca inventar autores, años, DOI ni números de página. Si no se puede verificar una referencia, marcarla como `[POR VERIFICAR]`.
5. Al afirmar algo, indicar la fuente en formato `\textcite{}` / `\parencite{}` usando las claves BibTeX existentes cuando corresponda.
6. **Para código:** las decisiones de diseño (estructura del flujo, reproducibilidad, manejo de datos) se justifican con las fuentes de la sección 13. La documentación oficial de una librería (por ejemplo, de Snakemake o rasterio) vale para saber **cómo se usa**, pero no como respaldo científico de una decisión metodológica.
7. **No inventar funciones, argumentos ni opciones de línea de comandos.** Si no se está seguro de que una API (interfaz de programación) existe en la versión instalada, verificarlo (`--help`, `help()`, documentación oficial) antes de escribir el código.

## 3. Decisiones metodológicas vinculantes

No cambiar ni cuestionar sin que el usuario lo pida. Si una tarea las contradice, avisar antes de actuar.

- **Enfoque exclusivamente por umbrales.** Sin aprendizaje automático (no Random Forest, no SVM).
- **No circularidad de la validación.** Los perímetros de CONAF SIDCO pueden derivar de imágenes satelitales, por lo que se usan **solo** como delimitadores espaciales/temporales, nunca como verdad de terreno. La referencia independiente es EMSR859.
- **EMSR859** (clasificación semiautomática supervisada con SPOT-6/7, Pléiades y PlanetScope) no entrega clases de severidad de vegetación directamente. Cubre cuatro AOI (áreas de interés): San Rosendo, Chiguayhue, Santa Bárbara y Concepción (incluye Lirquén), sin traslape.
- **Separación calibración/validación:** calibración con el inventario 2020–2025; validación solo con el evento de enero 2026.
- **Algoritmos en paralelo:** Otsu multinivel (método de umbralización que separa clases maximizando la varianza entre ellas) y detección de mínimos por KDE (estimación de densidad por kernel, una forma de suavizar el histograma). No elegir uno sobre otro de antemano.
- **Índices de severidad principales:** dNBR (diferencia del índice normalizado de área quemada), RdNBR (versión relativizada del dNBR), BAI (índice de área quemada) y MIRBI (índice de quemado en infrarrojo medio). Se mantienen dNBR y RdNBR porque ninguno domina en todas las coberturas (Soverel et al., 2010). **Apoyo:** NDVI y NDBI.
- **Estratificación** por categorías de uso de suelo de CONAF: forestal, urbano y otras coberturas.
- **Tres estrategias de umbral a comparar:** internacional estándar, regional calibrada (inventario 2020–2025) y ad hoc (derivada del evento de enero 2026).
- **Buffer de exclusión** de ancho de píxel en los bordes de clase, para mitigar el efecto de píxeles mixtos (píxeles que contienen más de una cobertura).
- **Evaluación de exactitud:** muestreo aleatorio estratificado según Olofsson et al. (2014).
- **Estabilidad de umbrales:** validación cruzada leave-one-out (se deja un incendio fuera cada vez y se calibra con el resto).
- **Validación indirecta de severidad** sin acceso a terreno: fotointerpretación GeoCBI (índice compuesto de quemado calculado con interpretación visual de imágenes de alta resolución; De Santis & Chuvieco).

## 4. Pendientes por verificar (no asumir resueltos)

Antes de apoyarse en estos puntos, confirmar su estado con el usuario:

- Si el shapefile `Grading - Areas - Affected land use-cover` de EMSR859 trae poblado el atributo de grado de daño para los polígonos de vegetación. Esto define el **Escenario A** (usar EMSR859 directamente) frente al **Escenario B** (GeoCBI propio).
- Multimodalidad de las distribuciones de los índices dentro de los perímetros, por estrato.
- Cantidad de pares de imágenes Sentinel-2 sin nubes para los incendios de calibración 2020–2025.
- Obtención de una imagen de muy alta resolución (VHR) de febrero–marzo 2026 para una posible fotointerpretación GeoCBI.
- **Parámetros técnicos aún sin definir** (no fijarlos por cuenta propia; pedirlos o dejarlos como parámetro en `config/config.yaml`): bandas exactas para el NBR (B8 o B8A frente a B12), CRS (sistema de referencia de coordenadas) proyectado único del proyecto, y criterio de enmascarado de nubes y sombras.

### Estado actual de los datos de incendios (revisado 2026-10-18)

- **Temporadas CONAF en `resources/raw/conaf/incendios/`:** 2019_2020, 2020_2021, 2021_2022, 2022_2023, 2023_2024, 2024_2025. No hay 2025_2026 (evento de validación): ese incendio no tiene perímetro CONAF cargado.
- **2019_2020:** los 8 incendios del Biobío salen sin fecha de inicio legible y quedan «fuera» por ese motivo. Pendiente revisar el `.dbf`; no inferir las fechas.
- **Geometrías inválidas:** varias capas (2019_2020: 5; 2020_2021: 4; 2021_2022: 27) tienen `Ring Self-intersection` (anillos que se cruzan consigo mismos). El área calculada no cambia al repararlas, pero **no se reparan en silencio**: el catálogo conserva el incendio y anota «geometría inválida sin reparar». Decidir con el usuario si se repara (`make_valid`) antes de usarlas en operaciones espaciales.
- **Identificador:** 2024_2025 no trae columna de id; el catálogo usa `fila-N` (posición en el archivo). `fire_id` = `bio{año de inicio de la temporada}-{correlativo}`.
- **Región:** se filtra por `CODREG` = 8 (la columna `REGION` en texto es inconsistente); el nombre solo se usa si falta el código.
- **CRS de cálculo de áreas:** EPSG:32719 (UTM 19S, el de los perímetros) como valor **provisorio**; el CRS único del proyecto sigue sin definir.
- **Nubosidad pre/post:** no implementada (requiere Earth Engine). Las columnas `nubosidad_*` y `escena_*` del catálogo están vacías y los incendios «dentro» llevan el motivo «nubosidad pendiente de revisión». La HU-00.2 no está cerrada hasta resolverlo.

## 5. Entorno Python (sin Anaconda)

**Regla central: no usar Anaconda, Miniconda, Mamba ni ninguna herramienta de la familia conda.** El entorno se maneja con `uv` (gestor de paquetes y entornos de Python; crea el `.venv` y resuelve dependencias). `uv` no pertenece a la familia conda.

- **Entorno virtual obligatorio:** `.venv` creado por `uv sync`. Ejecutar todo con `uv run <comando>` (o con el `.venv` activado). No instalar paquetes fuera del `.venv` ni con `sudo`; no usar `pip install` suelto.
- **Versión de Python fija: 3.14.7** (`requires-python = "==3.14.*"` en `pyproject.toml`, declarada también en `README.md`). No cambiarla sin avisar.
- **Dependencias declaradas** en `pyproject.toml` (metadatos del proyecto en el formato estándar PEP 621) y **congeladas** con versiones exactas en `uv.lock` (generado por `uv lock`; incluye hashes y es multiplataforma). Los paquetes nuevos se agregan con `uv add` (o `uv add --dev` para desarrollo), que actualiza ambos archivos. La versión de Python queda en `.python-version`.
- **Instalación limpia por script:** `python3 workflow/scripts/00_setup_env.py` (solo biblioteca estándar; requiere `uv`) ejecuta `uv sync --locked` (crea el `.venv`, instala el lock y `src/burnsev` en modo editable), verifica con `burnsev.env_check` (que usa `uv sync --locked --check`) que el entorno coincide con el lock y ejecuta `snakemake -n`. Se niega a correr si `.venv` ya existe. Migrada de venv+pip a uv el 2026-10-19; **la instalación limpia con uv aún no se ha verificado en un `.venv` nuevo**.
- **Conflicto con ADR-0018:** el ADR habla de «entornos conda por regla». Se mantiene la regla de este archivo (sin conda); el ADR no se ha enmendado y la diferencia está anotada en el `README.md`. No tratarlo como resuelto sin que el usuario lo decida.
- **Instalación de paquetes geoespaciales:** en Linux, `rasterio`, `geopandas` y sus dependencias se instalan normalmente desde wheels (paquetes binarios precompilados) con `uv`. Si una instalación falla por una librería del sistema (por ejemplo GDAL), **informar el error y la causa**, sin recurrir a conda como atajo.
- **Paquetes previstos:** `numpy`, `scipy`, `rasterio`, `geopandas`, `shapely`, `pyproj`, `scikit-image`, `scikit-learn` (solo utilidades estadísticas, **no clasificación**), `pandas`, `matplotlib`, `earthengine-api` (cliente de Google Earth Engine), `snakemake`, `pytest`. No agregar paquetes fuera de esta lista sin justificar por qué se necesitan.
- **Snakemake sin conda:** no usar la directiva `conda:` en las reglas ni la opción `--use-conda`. Todas las reglas corren en el `.venv` del proyecto. Si en el futuro se necesita aislar una herramienta, proponer una alternativa (por ejemplo contenedores) y esperar aprobación.
- **Credenciales:** las credenciales de Earth Engine y cualquier token quedan fuera del repositorio y de la carpeta del proyecto. Nunca imprimirlas, registrarlas en logs ni incluirlas en commits.
- **Sin notebooks como fuente de verdad:** el análisis vive en scripts `.py` y módulos. Si se usa un notebook para explorar, no debe ser requisito para producir ningún resultado del pipeline.

## 6. Flujo de trabajo con Snakemake

Snakemake (sistema de gestión de flujos de trabajo que ejecuta solo los pasos cuyo resultado falta o quedó desactualizado) es el **único punto de entrada** para producir resultados. Ningún resultado de la tesis debe depender de pasos manuales o de comandos sueltos.

### 6.1 Estructura del repositorio

Se sigue la estructura recomendada por la documentación de Snakemake (Mölder et al., 2021), adaptada al proyecto:

```
.
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── uv.lock
├── config/
│   ├── config.yaml              # parámetros del análisis (sin rutas absolutas)
│   ├── config.schema.yaml       # esquema de validación del config
│   └── schema_columns.yaml      # alias de columnas CONAF -> nombres estándar
├── gee/                         # scripts de Earth Engine (vacío por ahora)
├── workflow/
│   ├── Snakefile                # solo incluye reglas y define `rule all`
│   ├── rules/                   # un archivo .smk por etapa (common.smk + NN_etapa.smk)
│   └── scripts/                 # scripts con prefijo de etapa NN_ (igual que su .smk): 00_setup_env.py, 01_*.py, 02_*.py
├── src/
│   └── burnsev/                 # módulo reutilizable: fires, catalog, runlog, env_check (luego índices, umbrales, métricas)
├── tests/                       # pruebas con pytest
├── resources/                   # datos externos de entrada (inmutables), ver sección 8
├── results/                     # salidas generadas por el pipeline (no se editan a mano)
├── logs/                        # un log por regla y por wildcard
├── benchmarks/                  # tiempos y memoria por regla
└── docs/                        # LaTeX, informes de sprint
```

### 6.2 Reglas (`rule`)

- **Un archivo `.smk` por etapa** en `workflow/rules/`, con prefijos que reflejen el orden (por ejemplo `01_ingesta.smk`, `02_indices.smk`, `03_umbrales.smk`, `04_validacion.smk`).
- **Cada regla declara** `input`, `output`, `params`, `log` y, cuando aplique, `threads`, `resources` y `benchmark`. Sin rutas escritas dentro del script: todo llega por `input`, `output` o `params`.
- **Nombres de reglas** en inglés, `snake_case` y con verbo (`compute_nbr`, `apply_otsu`, `build_confusion_matrix`).
- **Todos los scripts viven en `workflow/scripts/`** (no hay carpeta `scripts/` en la raíz) y se nombran `NN_verbo_objeto.py`, con el mismo prefijo `NN` de la etapa (`NN_etapa.smk`) que los llama; `00_` es para preparación del entorno, que no es una regla. La lógica va en `src/burnsev/`; el script solo lee `snakemake.input/params`, llama a `src` y escribe.
- **Preferir `script:`** para lógica en Python. Usar `shell:` solo para llamadas cortas a herramientas externas. La lógica no trivial va en `src/burnsev/`, no dentro del `Snakefile`.
- **`rule all`** al inicio del `Snakefile`, con los productos finales como entrada.
- **Wildcards** (comodines que parametrizan una regla, como `{fire_id}`): restringirlos con `wildcard_constraints` para evitar coincidencias ambiguas. La lista de incendios sale de `fires.tsv`, no de listas escritas en el código. Ese archivo **lo genera la regla `build_fire_catalog`** en `results/catalogo/fires.tsv` (columnas `fire_id`, `fecha_inicio`, `fecha_termino`, `role`); no se edita a mano. Hoy solo contiene incendios de calibración.
- **Intermedios grandes** (rásteres completos por escena) marcados con `temp()` (se borran al dejar de ser necesarios). Salidas costosas de recalcular, como los umbrales finales, pueden marcarse con `protected()`.
- **Pasos con Earth Engine:** son remotos y no deterministas por naturaleza (la colección puede actualizarse). Se aíslan en reglas propias (`localrules` si no consumen CPU local), registran en el log la fecha, el ID de la colección y los filtros usados, y su salida se trata como un dato de entrada versionado por manifiesto (ver sección 8).
- **Dependencias dinámicas** (por ejemplo, cuántos incendios pasan el filtro de nubes): resolver con `checkpoint`, no con código fuera de las reglas.

### 6.3 Configuración

- Todo parámetro del análisis (bandas, bufferes, número de clases de Otsu, ancho de banda del KDE, semillas, CRS, fechas de ventana pre/post) vive en `config/config.yaml`. **Ningún número mágico** (valor sin explicación) dentro del código.
- Validar el config al inicio con el esquema (`validate()` de Snakemake con `config.schema.yaml`).
- Cada parámetro del config lleva un comentario con su justificación y, si corresponde, la fuente.

### 6.4 Comandos y verificación antes de ejecutar

Antes de proponer o ejecutar cambios en el flujo, Claude sigue este orden:

1. `snakemake -n` (simulación, *dry-run*: muestra qué se ejecutaría sin ejecutarlo).
2. `snakemake --lint` (revisión de buenas prácticas del propio Snakemake).
3. Ejecución real con `--cores N` explícito, empezando por **un solo incendio** o un recorte pequeño.
4. Solo después, la ejecución completa.

Reglas adicionales:

- **No lanzar ejecuciones largas o con descargas grandes sin confirmación.** El almacenamiento local es limitado: avisar el tamaño estimado antes.
- **No borrar ni forzar** (`--forceall`, `--delete-all-output`) sin pedirlo.
- Verificar opciones de línea de comandos con `snakemake --help` antes de usar una que no se haya usado antes.
- Generar el grafo del flujo (`--dag`) y el informe (`--report`) para documentar el pipeline en la tesis.

## 7. Convenciones de código Python

### 7.1 Estilo

- **PEP 8** (guía oficial de estilo de Python) con líneas de hasta 88 caracteres. Formateo con `ruff format` y revisión con `ruff check` (aprobados por el usuario el 2026-10-19; configuración en `[tool.ruff]` de `pyproject.toml`).
- **Nombres:** `snake_case` para funciones y variables, `PascalCase` para clases, `MAYUSCULAS` para constantes.
- **Idioma (propuesta por defecto, confirmar con el usuario):** identificadores en inglés; comentarios y docstrings en español.
- **Imports** en tres bloques (biblioteca estándar, terceros, proyecto), sin `from x import *`.
- **Rutas** con `pathlib.Path`, nunca concatenando cadenas ni con rutas absolutas.

### 7.2 Diseño

- **Funciones pequeñas y puras** (sin efectos secundarios: misma entrada, misma salida) para todo el cálculo científico: índices espectrales, umbralización, métricas. La lectura y escritura de archivos se separa de ese cálculo.
- **Anotaciones de tipos** (*type hints*) en todas las funciones públicas.
- **Docstrings** en cada función pública con: qué hace, parámetros (con unidades y rango esperado), valor de retorno y fuente cuando implementa una fórmula publicada (por ejemplo, `Key & Benson (2006)`).
- **Escala de los índices explícita:** la fórmula del dNBR y del RdNBR depende de si el NBR se maneja en [−1, 1] o multiplicado por 1000. Documentar la convención elegida en el docstring y en el config, y mantenerla en todo el proyecto (Key & Benson, 2006; Miller & Thode, 2007).
- **Sin estado global** ni variables modificadas desde varios módulos.
- **Sin código duplicado entre scripts:** si dos reglas usan la misma lógica, va en `src/burnsev/`.

### 7.3 Procesamiento raster y vectorial

- **Lectura por ventanas o bloques** (`rasterio` con `windows`) cuando una escena no quepa cómodamente en memoria. No cargar rásteres completos por costumbre.
- **Valores sin dato (*nodata*):** declararlos explícitamente al escribir y propagarlos con máscaras de `numpy` o valores `NaN`. No mezclar `0` como dato válido con `0` como ausencia de dato.
- **Tipos de dato:** `float32` para índices; evitar `float64` salvo necesidad. Las bandas Sentinel-2 L2A vienen como enteros escalados: aplicar el factor de escala y, para imágenes posteriores al cambio de línea base de procesamiento de ESA, el desplazamiento radiométrico correspondiente. **Verificar ambos en la documentación oficial de ESA o de la colección de GEE usada antes de calcular** (esto afecta directamente a pares pre/post de 2020–2025).
- **Alineación:** antes de operar entre imágenes (pre/post, índice/máscara), comprobar con una función dedicada que comparten CRS, resolución, extensión y transformación. Si no coinciden, fallar con un mensaje claro, sin remuestrear en silencio.
- **Remuestreo:** declarar el método (vecino más cercano para datos categóricos, bilineal solo para continuos) y justificarlo.
- **Cálculos de área y distancia** solo en un CRS proyectado, nunca en grados.
- **Vectores:** reproyectar de forma explícita; validar geometrías (`is_valid`) antes de operaciones espaciales; documentar cualquier reparación.

### 7.4 Aleatoriedad y estadística

- **Semilla fija** en toda operación aleatoria (muestreo estratificado de Olofsson et al., 2014; submuestreos para KDE si los hubiera). Las semillas vienen del config y se registran en el log.
- Documentar para cada ejecución del KDE el *kernel* y el ancho de banda empleado (por ejemplo, la regla de Silverman, 1986, si se usa) y, para Otsu, el número de clases.
- **Métricas de exactitud** (matriz de confusión, exactitud global, exactitud del productor y del usuario, intervalos de confianza) implementadas según Olofsson et al. (2014) y probadas con un ejemplo de resultado conocido.

### 7.5 Manejo de errores y registro

- Usar el módulo `logging`, no `print`. En scripts de Snakemake, escribir al archivo definido en `log:`.
- **Fallar rápido y con mensaje claro** ante datos ausentes, CRS inconsistentes o rangos imposibles. Prohibido silenciar excepciones con `except: pass`.
- Registrar al inicio de cada script: versión de Python, versiones de paquetes clave y parámetros recibidos.

## 8. Convenciones de datos

### 8.1 Organización

| Carpeta | Contenido | Regla |
|---|---|---|
| `resources/raw/` | Datos externos tal como se obtuvieron (CONAF, EMSR859, exportaciones de GEE) | **Inmutable:** no editar, no sobrescribir. Permisos de solo lectura una vez descargados |
| `resources/external_meta/` | Manifiestos y metadatos de los datos crudos | Se versiona en Git |
| `results/interim/` | Productos intermedios (índices por escena, máscaras) | Regenerable; puede ser `temp()` |
| `results/processed/` | Productos finales (umbrales, mapas de severidad, tablas de exactitud) | Solo los escribe el pipeline |
| `results/figures/`, `results/tables/` | Figuras y tablas para la tesis | Generadas por reglas, nunca a mano |

### 8.2 Procedencia y manifiesto

Todo dato crudo tiene una entrada en un manifiesto (`resources/external_meta/manifest.tsv`) con: nombre de archivo, fuente (institución y producto), fecha de descarga, versión o fecha de actualización del producto, licencia o condiciones de uso, URL y suma de verificación `sha256`. Esto aplica en particular a:

- **Generación actual:** la regla `compute_raw_manifest` escribe `manifest.tsv` con `sha256` y toma fuente y URL de `fuentes_raw` en `config/config.yaml`. Fecha de descarga, versión del producto y licencia no están documentadas y quedan como `[POR VERIFICAR]` hasta que el usuario las aporte; mientras tanto esos datos no deben usarse en resultados finales de la tesis.
- **EMSR859** (versión del producto y fecha de entrega).
- **Cartografía y catastro de CONAF** (SIDCO para perímetros; catastro de uso de suelo actualizado a 2025).
- **Exportaciones desde GEE:** ID de la colección, filtros, fechas, bandas, escala y CRS de exportación.

Si falta la procedencia de un dato, **no usarlo en resultados** hasta registrarla.

### 8.3 Formatos

- **Rásteres:** GeoTIFF con compresión (por ejemplo `DEFLATE`) y organizado en bloques (*tiled*). Metadatos de CRS y *nodata* siempre presentes.
- **Vectores de salida:** GeoPackage (`.gpkg`). Los shapefiles originales de entrada se conservan tal cual, pero no se generan shapefiles nuevos (limitan nombres de campo a 10 caracteres).
- **Tablas:** CSV o TSV para tablas pequeñas y legibles; Parquet para tablas grandes (como muestras por píxel).
- **Configuración y manifiestos:** YAML o TSV, en texto plano, versionables.

### 8.4 Nombres de archivo

- Minúsculas, `snake_case`, sin espacios ni tildes ni la letra ñ.
- Fechas en formato `YYYYMMDD`.
- Patrón sugerido: `{producto}_{fire_id}_{variable}_{YYYYMMDD}.{ext}`; por ejemplo `s2l2a_lirquen2026_nbr_pre_20260105.tif`. Los identificadores reales (`fire_id`) salen de `results/catalogo/fires.tsv`.
- Los nombres nunca codifican decisiones que pertenecen al config (por ejemplo, un umbral).

### 8.5 Tamaño y almacenamiento

- **Datos pesados fuera de Git.** El `.gitignore` excluye `resources/raw/`, `results/` y `.venv/`. Se versionan solo el código, el config, los manifiestos y los metadatos.
- **Recortar al área de interés antes de descargar** o exportar desde GEE, para cuidar el almacenamiento local (motivo por el cual el procesamiento es híbrido GEE + Python local).
- No generar copias duplicadas de datos para «probar algo». Si se necesita un recorte de prueba, derivarlo con una regla de Snakemake.

### 8.6 Calidad y trazabilidad de los datos

- **Validaciones obligatorias al ingresar un dato:** CRS declarado, extensión dentro de la zona esperada, rango de valores plausible, porcentaje de píxeles sin dato y de nubes/sombras.
- **Separación estricta de roles:** los incendios de calibración (2020–2025) y el de validación (enero 2026) se distinguen por la columna `role` de `results/catalogo/fires.tsv`. Ninguna regla de calibración debe leer datos del evento de validación (se prueba con una prueba automática; ver sección 9).
- **Los perímetros CONAF** se usan solo para delimitar. Ningún cálculo de exactitud puede tomarlos como referencia.
- **Datos personales:** el proyecto no los requiere. Si apareciera alguno en algún producto, no copiarlo a resultados.

## 9. Pruebas y reproducibilidad

- **`pytest`** para todo lo que está en `src/burnsev/`. Cada función de cálculo científico lleva al menos una prueba con **datos sintéticos pequeños** (rásteres de pocos píxeles) y un resultado conocido calculado a mano.
- **Pruebas mínimas obligatorias:**
  - NBR, dNBR y RdNBR con valores de referencia calculados a mano y con la escala definida en el config.
  - Manejo de *nodata* y de píxeles enmascarados.
  - Comprobación de alineación (CRS/resolución/extensión) que falle cuando corresponde.
  - Métricas de exactitud (Olofsson et al., 2014) con una matriz de confusión simple de resultado conocido.
  - **No fuga de datos:** el flujo de calibración no puede leer insumos del evento de validación.
  - Reproducibilidad: misma semilla produce el mismo resultado.
- **Reproducibilidad total:** desde un clon limpio, `uv sync --locked` y ejecutar `uv run snakemake --cores N` debe regenerar los resultados. Si algo exige un paso manual, es un defecto que se documenta y se corrige.
- Registrar en `results/` las versiones del entorno y el commit de Git con que se generó cada resultado.
- **Nunca editar a mano un archivo de `results/`.** Si un resultado está mal, se corrige la regla o el parámetro y se regenera.

## 10. Control de versiones y gestión

- Git + GitHub con `gh` CLI. Nombres de repositorio en minúsculas con guiones.
- **Commits pequeños y con mensaje descriptivo** en español, en el formato `tipo: descripción` (por ejemplo `feat: calcula dNBR por incendio`, `fix: corrige escala del RdNBR`, `docs: actualiza informe de sprint`).
- Trabajar en ramas por tarea; una tarea del backlog corresponde a un issue.
- Antes de cada commit: ejecutar `uv run ruff check`, `uv run ruff format --check`, `uv run pyright`, `uv check`, `uv run pytest` y `uv run snakemake -n`.
- No subir datos pesados, credenciales ni salidas de `results/`.
- **Estimaciones de esfuerzo:** tallas S/M/L, no puntos Fibonacci.
- **Priorización:** usar MoSCoW (Must, Should, Could, Won't: método para clasificar requisitos por importancia), no P0/P1/P2.
- **Backlog:** formato GitHub Issues, estructura general y acorde a la rúbrica, sin descomposición exhaustiva.

## 11. Documentación académica (LaTeX)

- Redacción en LaTeX con backend BibLaTeX/biber, estilo APA, idioma español.
- Compilación: `pdflatex → biber → pdflatex → pdflatex`.
- Citas: `\textcite{}` cuando el autor es sujeto de la oración, `\parencite{}` para citas entre paréntesis.
- Las claves BibTeX viven en `referencias.bib`, generadas por Better BibTeX (extensión de Zotero que crea claves de cita automáticas). **Reutilizar las claves existentes** (por ejemplo `KeyBenson2006`, `Olofsson2014`, `SoverelEtal2010`, `Otsu1979`, `Silverman1986`, `Gorelick2017`, `CopernicusEMS2025`). No crear claves nuevas con otro formato.
- Los campos `abstract`, `file` y `keywords` se omiten al exportar.
- Los objetivos de la tesis son SMART (específicos, medibles, alcanzables, relevantes y con plazo) e incluyen nombres de índices, criterios estadísticos y citas de protocolo en el propio texto.
- Mantener trazabilidad problema–objetivos, y separar requisitos, restricciones y supuestos (observaciones de la revisión de la Etapa 1).
- Los parámetros y versiones que aparezcan en la tesis deben coincidir con `config/config.yaml` y con `uv.lock`.

## 12. Estilo de respuesta

- **Idioma:** español.
- **Registro formal académico** para el cuerpo de la tesis. **Conciso e informal** para backlog, informes de sprint (primera persona, tono operativo) y metadatos del proyecto.
- Dar el nivel de detalle que se pide. Evitar respuestas largas o formales de más para el contexto.
- Guía técnica directa y estructurada. Evaluaciones honestas de factibilidad, sin ánimo genérico.
- **Términos nuevos o poco comunes:** al mencionarlos, poner su significado entre paréntesis la primera vez que aparecen.
- Texto que suene natural, evitando patrones típicos de redacción automática (frases infladas, relleno, lenguaje de venta).
- **Al entregar código:** indicar qué archivo se modificó, cómo probarlo (comando exacto) y qué supuestos se tomaron. Si algo quedó sin verificar, decirlo.

## 13. Referencias de respaldo para las reglas de código y datos

Fuentes que sustentan las decisiones de las secciones 5 a 9. **Verificar la referencia completa (volumen, páginas, DOI) en Zotero antes de citarlas en la tesis.**

- Sandve, G. K., Nekrutenko, A., Taylor, J., & Hovig, E. (2013). Ten simple rules for reproducible computational research. *PLOS Computational Biology, 9*(10), e1003285. (Reproducibilidad: automatizar pasos, registrar versiones, evitar edición manual, fijar semillas.)
- Wilson, G., Bryan, J., Cranston, K., Kitzes, J., Nederbragt, L., & Teal, T. K. (2017). Good enough practices in scientific computing. *PLOS Computational Biology, 13*(6), e1005510. (Organización de proyectos, datos, código, control de versiones.)
- Mölder, F., Jablonski, K. P., Letcher, B., et al. (2021). Sustainable data analysis with Snakemake. *F1000Research, 10*, 33. (Estructura recomendada y buenas prácticas de Snakemake.)
- Köster, J., & Rahmann, S. (2012). Snakemake—a scalable bioinformatics workflow engine. *Bioinformatics, 28*(19), 2520–2522.
- Wilkinson, M. D., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3*, 160018. (Datos localizables, accesibles, interoperables y reutilizables: sustento de manifiestos y metadatos.)
- Documentos normativos oficiales de Python: PEP 8 (estilo), PEP 484 (anotaciones de tipos) y PEP 621 (metadatos en `pyproject.toml`). Sirven como respaldo de convenciones de código, no como respaldo científico.
- Olofsson, P., et al. (2014); Key, C. H., & Benson, N. C. (2006); Miller, J. D., & Thode, A. E. (2007); Soverel, N. O., et al. (2010); Otsu (1979); Silverman (1986): ver claves BibTeX existentes en `referencias.bib`.

## 14. Qué NO hacer

**Metodología y fuentes**
- No proponer ni introducir aprendizaje automático en la metodología.
- No usar perímetros CONAF como verdad de terreno.
- No citar fuentes no académicas como respaldo científico.
- No inventar referencias, datos, resultados, funciones ni opciones de línea de comandos.
- No dar por cerrados los pendientes de la sección 4.

**Entorno y flujo**
- No usar Anaconda, Miniconda, Mamba ni la directiva `conda:` de Snakemake.
- No instalar paquetes fuera del `.venv` ni con `sudo`.
- No agregar dependencias sin registrarlas en `pyproject.toml` y `uv.lock` (con `uv add`).
- No ejecutar el pipeline completo, descargas grandes ni opciones destructivas (`--forceall`, `--delete-all-output`) sin confirmación.
- No producir resultados fuera de Snakemake.

**Código y datos**
- No dejar números mágicos ni rutas absolutas en el código.
- No remuestrear ni reproyectar en silencio.
- No silenciar excepciones.
- No sobrescribir ni editar archivos de `resources/raw/` ni de `results/`.
- No subir datos pesados ni credenciales a Git.
- No usar un dato sin procedencia registrada en el manifiesto.
- No modificar `referencias.bib` ni claves de citas sin pedirlo.
