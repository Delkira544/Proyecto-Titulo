"""Consulta a GEE la nubosidad (SCL) dentro del perímetro de un incendio."""

import logging
from datetime import date
from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd

from burnsev.clouds import Thresholds, exploration_slices, explore_side
from burnsev.gee_scenes import init_ee, perimeter_geometry, scene_stats
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
fire_id = snakemake.wildcards.fire_id
logger.info("Consulta GEE el %s, colección %s", date.today(), params.collection)

fires = pd.read_csv(snakemake.input.fires, sep="\t").set_index("fire_id")
if fire_id not in fires.index:
    raise ValueError(f"{fire_id} no está en fires.tsv")
anchors = {
    "pre": pd.to_datetime(fires.loc[fire_id, "fecha_inicio"]),
    "post": pd.to_datetime(fires.loc[fire_id, "fecha_termino"]),
}
for side, anchor in anchors.items():
    if pd.isna(anchor):
        raise ValueError(f"{fire_id}: falta la fecha de ancla de la ventana {side}")

perimeters = gpd.read_file(snakemake.input.perimeters)
perimeter = cast(gpd.GeoDataFrame, perimeters[perimeters["fire_id"] == fire_id])
if perimeter.empty:
    raise ValueError(f"{fire_id}: sin perímetro")

init_ee(params.project_env)
geometry = perimeter_geometry(perimeter, params.crs, params.simplify_m)
thresholds = Thresholds(params.max_bad_pct, params.min_coverage_pct)


def make_fetch():
    def fetch(start, end):
        return scene_stats(
            params.collection,
            geometry,
            start,
            end,
            params.bad_classes,
            params.scale_m,
            params.tile_scale,
        )

    return fetch


parts = []
for side, anchor in anchors.items():
    slices = exploration_slices(params.steps, params.max_days[side])
    logger.info("%s: ancla %s, rebanadas %s", side, anchor.date(), slices)
    found = explore_side(make_fetch(), anchor.date(), side, slices, thresholds)
    found.insert(0, "lado", side)
    parts.append(found)

Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
pd.concat(parts, ignore_index=True).to_csv(snakemake.output[0], index=False)
logging.getLogger("burnsev").info("Escenas exploradas: %d", sum(map(len, parts)))
