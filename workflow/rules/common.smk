# Utilidades compartidas por todas las reglas.
from pathlib import Path
import pandas as pd
from snakemake.exceptions import WorkflowError

RAW_INC = config["rutas"]["raw_incendios"]
RAW_CONAF = config["rutas"]["raw_conaf"]
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
