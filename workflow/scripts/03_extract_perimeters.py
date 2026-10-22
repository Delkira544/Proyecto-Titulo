"""Escribe los perímetros de los incendios 'dentro' con su fire_id (GeoPackage)."""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import yaml

from burnsev.catalog import build_perimeters
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

with open(snakemake.input.schema_columns, encoding="utf-8") as fh:
    schema = yaml.safe_load(fh)

frames = {
    Path(shp).parent.name: gpd.read_file(shp, encoding=params.encoding)
    for shp in snakemake.input.shp
}
catalog = pd.read_csv(snakemake.input.catalog)
perimeters = build_perimeters(
    frames,
    catalog,
    columns=schema["columnas"],
    required=schema["obligatorias"],
    region_code=params.region_code,
    region_names=params.region_names,
    crs=params.crs,
)
logger.info(
    "%d perímetros; inválidos sin reparar: %d",
    len(perimeters),
    int((~perimeters.geometry.is_valid).sum()),
)
Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
perimeters.to_file(snakemake.output[0], driver="GPKG")
