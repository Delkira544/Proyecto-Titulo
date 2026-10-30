# Utilidades compartidas por todas las reglas.
from pathlib import Path
import pandas as pd
from snakemake.exceptions import WorkflowError

RAW_INC = config["rutas"]["raw_incendios"]
RAW = config["rutas"]["raw"]
RAW_CONAF = config["rutas"]["raw_conaf"]
RAW_EMSR = config["rutas"]["raw_emsr859"]
RAW_PUNTOS = config["rutas"]["raw_incendios_puntos"]
EXT_META = config["rutas"]["external_meta"]
INT = config["rutas"]["interim"]
PROC = config["rutas"]["processed"]
RES = config["rutas"]["results"]
LOGS = config["rutas"]["logs"]
TEMPORADAS = config["temporadas"]

# Los comodines (wildcards) se restringen para que un nombre mal escrito falle rápido.
wildcard_constraints:
    temporada=r"\d{4}_\d{4}",        # ej. 2020_2021
    fire_id=r"[a-z]+\d{4}-\d{3}",    # ej. bio2022-007
    fase=r"pre|post",
    indice=r"[a-z0-9]+",
    fecha=r"\d{8}",       # YYYYMMDD de la escena post


def shapefile_de_temporada(temporada):
    """Ruta del único .shp de la temporada; falla con mensaje claro si no hay uno solo."""
    carpeta = Path(RAW_INC) / temporada
    shps = sorted(carpeta.glob("*.shp"))
    if len(shps) != 1:
        raise WorkflowError(f"Se esperaba 1 .shp en '{carpeta}' y hay {len(shps)}.")
    return str(shps[0])


def shapefiles_crudos(wildcards=None):
    """Un .shp por temporada declarada en config['temporadas']."""
    return [shapefile_de_temporada(t) for t in TEMPORADAS]


def archivos_crudos(wildcards=None):
    """Todos los archivos bajo rutas.raw (para el manifiesto sha256)."""
    return sorted(str(p) for p in Path(RAW).rglob("*") if p.is_file())


def archivos_emsr859(wildcards=None):
    """Capas (.shp/.dbf) y tablas resumen del GRA de EMSR859, de todas las AOI."""
    keep = (".shp", ".dbf", ".shx", ".prj", ".xlsx")
    return sorted(
        str(p) for p in Path(RAW_EMSR).glob("AOI*/*") if p.suffix in keep
    )


def archivos_regiones(wildcards=None):
    """Shapefile de regiones con sus archivos compañeros."""
    shp = Path(config["rutas"]["regiones"])
    return sorted(str(p) for p in shp.parent.glob(f"{shp.stem}.*"))


def stats_de_incendios(wildcards):
    """Un archivo de estadísticas por incendio 'dentro' (lista leída de fires.tsv)."""
    fires = checkpoints.build_fire_catalog.get().output.fires
    ids = pd.read_csv(fires, sep="\t")["fire_id"]
    return [f"{INT}/escenas/{fire_id}_stats.csv" for fire_id in ids]


def incendios_usables(wildcards=None):
    """Filas (fire_id, fecha_post YYYYMMDD) de los incendios usables, tras la revisión."""
    path = checkpoints.review_fire_cloudiness.get().output.usability
    usable = pd.read_csv(path).query("estado == 'usable'")
    fechas = pd.to_datetime(usable["fecha_post"]).dt.strftime("%Y%m%d")
    return list(zip(usable["fire_id"], fechas, strict=True))


def productos_indices(wildcards=None):
    """Nombres finales de índices y estratos por incendio usable (convención §8.4)."""
    cfg = config["indices_export"]
    base = f"{PROC}/indices"
    out = []
    for fire_id, fecha in incendios_usables():
        for variable in ("indices", "estrato"):
            out.append(f"{base}/{cfg['producto']}_{fire_id}_{variable}_{fecha}.tif")
    return out


def conteos_estrato(wildcards=None):
    """CSV de conteo por estrato de cada incendio usable."""
    prod = config["indices_export"]["producto"]
    return [
        f"{PROC}/indices/{prod}_{fire_id}_conteo_estrato_{fecha}.csv"
        for fire_id, fecha in incendios_usables()
    ]


def shapefiles_puntos(wildcards=None):
    """Shapefiles de puntos de inicio de incendios (solo aportan fechas faltantes)."""
    return sorted(str(p) for p in Path(RAW_PUNTOS).glob("*/*.shp"))


def productos_estadistica(wildcards=None):
    """Tablas y figuras finales de la etapa 05."""
    return [
        f"{PROC}/tablas/valores_pixel.parquet",
        f"{RES}/tables/estadisticos_indice_estrato.csv",
        f"{RES}/tables/estadisticos_por_incendio.csv",
        f"{RES}/tables/histogramas_indice_estrato.csv",
        f"{RES}/tables/resumen_incendios.csv",
        f"{RES}/figures/histogramas_indice_estrato.png",
        f"{RES}/figures/cajas_indice_estrato.png",
        f"{RES}/figures/panorama_incendios.png",
    ]


def productos_validacion(wildcards=None):
    """Índices exportados de los incendios de validación usables (tras su revisión)."""
    path = checkpoints.review_validation_cloudiness.get().output.usability
    usable = pd.read_csv(path).query("estado == 'usable'")
    fechas = pd.to_datetime(usable["fecha_post"]).dt.strftime("%Y%m%d")
    prod = config["indices_export"]["producto"]
    return [
        f"{PROC}/validacion/indices/{prod}_{fire_id}_indices_{fecha}.tif"
        for fire_id, fecha in zip(usable["fire_id"], fechas, strict=True)
    ]


def productos_multimodalidad(wildcards=None):
    """Tablas finales de la etapa 06."""
    return [
        f"{RES}/tables/multimodalidad_indice_estrato.csv",
        f"{RES}/tables/combinaciones_percentiles.csv",
        f"{RES}/figures/multimodalidad_discordantes.png",
    ]


def pixeles_por_incendio(wildcards=None):
    """Parquet intermedio de píxeles de cada incendio usable."""
    return [
        f"{INT}/pixeles/{fire_id}_{fecha}.parquet"
        for fire_id, fecha in incendios_usables()
    ]
