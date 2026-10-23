# Utilidades compartidas por todas las reglas.
from pathlib import Path
import pandas as pd
from snakemake.exceptions import WorkflowError

RAW_INC = config["rutas"]["raw_incendios"]
RAW_CONAF = config["rutas"]["raw_conaf"]
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


def archivos_crudos_conaf(wildcards=None):
    """Todos los archivos bajo rutas.raw_conaf (para el manifiesto sha256)."""
    return sorted(str(p) for p in Path(RAW_CONAF).rglob("*") if p.is_file())


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
