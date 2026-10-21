"""Construye el catálogo de incendios y la tabla fires.tsv (ver burnsev.catalog)."""

from pathlib import Path

import geopandas as gpd
import yaml

from burnsev.catalog import build_catalog, build_fires_table
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

with open(snakemake.input.schema_columns, encoding="utf-8") as fh:
    schema = yaml.safe_load(fh)

frames = {
    Path(shp).parent.name: gpd.read_file(shp, encoding=params.encoding)
    for shp in snakemake.input.shp
}

catalog = build_catalog(
    frames,
    columns=schema["columnas"],
    required=schema["obligatorias"],
    region_code=params.region_code,
    region_names=params.region_names,
    crs=params.crs,
    window=tuple(params.window),
    min_area_ha=params.min_area_ha,
    id_prefix=params.id_prefix,
)

logger.info(
    "Catálogo: %d incendios, %s",
    len(catalog),
    catalog["estado"].value_counts().to_dict(),
)
Path(snakemake.output.catalog).parent.mkdir(parents=True, exist_ok=True)
catalog.to_csv(snakemake.output.catalog, index=False)
build_fires_table(catalog).to_csv(snakemake.output.fires, sep="\t", index=False)
