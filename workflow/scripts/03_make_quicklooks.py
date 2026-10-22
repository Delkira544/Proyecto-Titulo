"""Descarga miniaturas RGB de las escenas elegidas de los incendios usables."""

from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd

from burnsev.gee_scenes import download_quicklook, init_ee, perimeter_geometry
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

usable = pd.read_csv(snakemake.input.usability).query("estado == 'usable'")
perimeters = gpd.read_file(snakemake.input.perimeters)
out_dir = Path(snakemake.output[0]).parent
init_ee(params.project_env)

for _, row in usable.iterrows():
    perimeter = cast(
        gpd.GeoDataFrame, perimeters[perimeters["fire_id"] == row["fire_id"]]
    )
    geometry = perimeter_geometry(perimeter, params.crs, params.simplify_m)
    for side in ("pre", "post"):
        scene = row[f"escena_{side}"]
        if not isinstance(scene, str):
            continue
        target = out_dir / f"{row['fire_id']}_{side}.png"
        download_quicklook(params.collection, scene, geometry, params.thumb_px, target)
        logger.info("%s", target)
