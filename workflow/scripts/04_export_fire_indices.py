"""Compone las escenas pre/post de un incendio y exporta dnbr, rdnbr, bai, mirbi."""

from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.merge import merge

from burnsev.exports import tile_bounds
from burnsev.gee_indices import (
    download_geotiff_tile,
    scene_baselines,
    scene_composite,
    severity_indices,
)
from burnsev.gee_scenes import init_ee, perimeter_geometry
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
fire_id = snakemake.wildcards.fire_id

usable = pd.read_csv(snakemake.input.usability).set_index("fire_id")
if fire_id not in usable.index or usable.loc[fire_id, "estado"] != "usable":
    raise ValueError(f"{fire_id} no es un incendio usable")
row = usable.loc[fire_id]
logger.info(
    "Escenas %s | pre=%s post=%s", fire_id, row["escena_pre"], row["escena_post"]
)

perimeters = gpd.read_file(snakemake.input.perimeters)
perimeter = cast(gpd.GeoDataFrame, perimeters[perimeters["fire_id"] == fire_id])
if perimeter.empty:
    raise ValueError(f"{fire_id}: sin perímetro")
projected = perimeter.to_crs(params.crs)
perimeter = projected.set_geometry(projected.buffer(params.buffer_m))

init_ee(params.project_env)
region = perimeter_geometry(perimeter, params.crs, params.simplify_m)

bands = dict(params.bands)
pre = scene_composite(
    params.collection, row["escena_pre"], bands, params.bad_classes, params.scale_refl
)
post = scene_composite(
    params.collection, row["escena_post"], bands, params.bad_classes, params.scale_refl
)
image = severity_indices(pre, post, params.bai, params.mirbi, params.rdnbr_eps)

baselines = []
for side in ("pre", "post"):
    frame = scene_baselines(params.collection, row[f"escena_{side}"])
    frame.insert(0, "lado", side)
    baselines.append(frame)
baseline_table = pd.concat(baselines, ignore_index=True)
baseline_table.insert(0, "fire_id", fire_id)
baseline_table.insert(len(baseline_table.columns), "coleccion", params.collection)
Path(snakemake.output.scenes).parent.mkdir(parents=True, exist_ok=True)
baseline_table.to_csv(snakemake.output.scenes, index=False)
logger.info("Baselines:\n%s", baseline_table.to_string())

# Se recorta al perímetro + buffer (fuera queda nodata) y se descarga por teselas
# alineadas a la grilla de 20 m; cada tesela respeta el límite de tamaño de GEE.
bands_per_image = 4
bytes_per_pixel = bands_per_image * 4  # float32
max_pixels = int(params.max_mb * 1e6 // bytes_per_pixel)
buffered = perimeter.geometry.union_all()
tiles = tile_bounds(
    (buffered.bounds[0], buffered.bounds[1], buffered.bounds[2], buffered.bounds[3]),
    params.scale_m,
    max_pixels,
)
logger.info("Descarga en %d tesela(s) de <= %d píxeles", len(tiles), max_pixels)
# sameFootprint=False: sin esto, lo recortado por clip queda enmascarado y GEE lo
# exporta como 0 (que se confundiría con dato válido) en vez de nodata.
clipped = image.clip(region).unmask(params.nodata, False)

raw_dir = Path(snakemake.output.raster).parent / f".{fire_id}_teselas"
tile_paths = []
for k, tile in enumerate(tiles):
    path = raw_dir / f"tesela_{k:03d}.tif"
    download_geotiff_tile(clipped, tile, params.crs, params.scale_m, path)
    tile_paths.append(path)
    logger.info("Tesela %d/%d descargada", k + 1, len(tiles))

sources = [rasterio.open(p) for p in tile_paths]
try:
    data, transform = merge(sources, nodata=params.nodata)
    profile = sources[0].profile
finally:
    for src in sources:
        src.close()
profile.update(
    dtype="float32",
    nodata=params.nodata,
    compress="deflate",
    tiled=True,
    blockxsize=256,
    blockysize=256,
    height=data.shape[1],
    width=data.shape[2],
    transform=transform,
)
with rasterio.open(snakemake.output.raster, "w", **profile) as dst:
    dst.write(data.astype("float32"))
    for i, name in enumerate(["dnbr", "rdnbr", "bai", "mirbi"], start=1):
        dst.set_band_description(i, name)
for path in tile_paths:
    path.unlink()
raw_dir.rmdir()
logger.info("Escrito %s", snakemake.output.raster)
