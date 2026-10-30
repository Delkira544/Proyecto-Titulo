"""Zonas de trabajo y referencia quemado / no quemado del evento de validación.

Zona de trabajo = AOI de EMSR859 ∩ región de estudio − zonas que EMS no analizó.
Escribe además un catálogo y una tabla de incendios propios del rol
``validacion`` (sin tocar ``fires.tsv`` de calibración), para reutilizar la
revisión de nubosidad y la exportación de índices (ADR-0020).
"""

from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd

from burnsev.catalog import CATALOG_COLUMNS
from burnsev.emsr import (
    burnt_reference,
    find_layer,
    select_region,
    validation_catalog,
    validation_regions,
)
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
out = snakemake.output
root = Path(params.root)

regions = gpd.read_file(snakemake.input.regions)
region = select_region(regions, params.region_column, params.region_code)
region_geom = region.to_crs(params.crs).geometry.make_valid().union_all()

aoi_rows, burnt_parts, excluded = [], [], []
for entry in params.aois:
    folder = root / f"AOI{entry['aoi']}"
    aoi_path = find_layer(folder, "areaOfInterestA")
    burnt_path = find_layer(folder, params.burnt_layer)
    if aoi_path is None or burnt_path is None:
        raise FileNotFoundError(
            f"AOI{entry['aoi']}: falta el AOI o {params.burnt_layer}"
        )
    aoi = gpd.read_file(aoi_path).to_crs(params.crs)
    aoi_rows.append(
        {"fire_id": entry["fire_id"], "aoi": entry["aoi"], "geometry": aoi.union_all()}
    )
    burnt = gpd.read_file(burnt_path)
    burnt_parts.append(burnt[[burnt.geometry.name]].assign(aoi=entry["aoi"]))
    for layer in params.excluded_layers:
        path = find_layer(folder, layer)
        if path is not None:
            excluded.append(gpd.read_file(path)[["geometry"]].to_crs(params.crs))
    footprint = find_layer(folder, "imageFootprintA")
    if footprint is not None:
        prints = gpd.read_file(footprint)
        no_data = cast(
            gpd.GeoDataFrame, prints[prints["obj_type"] == params.no_data_footprint]
        )
        excluded.append(no_data[["geometry"]].to_crs(params.crs))
    logger.info("AOI%s -> %s", entry["aoi"], entry["fire_id"])

aois = gpd.GeoDataFrame(aoi_rows, geometry="geometry", crs=params.crs)
holes = (
    gpd.GeoDataFrame(pd.concat(excluded, ignore_index=True), crs=params.crs)
    if excluded
    else None
)
zones = validation_regions(aois, region_geom, holes, params.crs)
burnt_all = gpd.GeoDataFrame(pd.concat(burnt_parts, ignore_index=True))
reference = burnt_reference(burnt_all, zones, params.mmu_m2)
summary = zones[["fire_id", "area_ha"]].merge(
    reference[["fire_id", "area_ha", "n_partes", "n_partes_bajo_umm"]],
    on="fire_id",
    suffixes=("_zona", "_quemado"),
)
logger.info("Zonas y área quemada de referencia:\n%s", summary.round(1).to_string())

dates = {e["fire_id"]: (params.start_date, e["fecha_termino"]) for e in params.aois}
catalog = validation_catalog(
    zones, dates, CATALOG_COLUMNS, params.region_code, params.season
)
fires = catalog[["fire_id", "fecha_inicio", "fecha_termino"]].assign(role="validacion")

for path in out:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
zones.to_file(out.perimeters, driver="GPKG")
reference.to_file(out.reference, driver="GPKG")
catalog.to_csv(out.catalog, index=False)
fires.to_csv(out.fires, sep="\t", index=False)
