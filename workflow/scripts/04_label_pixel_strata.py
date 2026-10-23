"""Etiqueta cada píxel: estrato, ID_USO, zona, borde de clase y si es analizable."""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.transform
from shapely.geometry import box

from burnsev.runlog import setup_logging
from burnsev.strata import (
    analysis_zone,
    class_border,
    rasterize_id_uso,
    rasterize_strata,
    repair_invalid_geometries,
)

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
fire_id = snakemake.wildcards.fire_id

with rasterio.open(snakemake.input.raster) as src:
    transform, shape, crs, nodata = src.transform, src.shape, src.crs, src.nodata
    first = src.read(1)
    profile = src.profile
if str(crs) != params.crs:
    raise ValueError(f"CRS del ráster {crs} distinto del configurado {params.crs}")

# Lectura acotada al recuadro de la grilla (el SIT tiene ~200 mil polígonos)
catastro_crs = gpd.read_file(snakemake.input.catastro, rows=1).crs
grid_box = gpd.GeoSeries(
    [box(*rasterio.transform.array_bounds(shape[0], shape[1], transform))], crs=crs
)
bbox = tuple(float(v) for v in grid_box.to_crs(catastro_crs or crs).total_bounds)
catastro = gpd.read_file(snakemake.input.catastro, bbox=bbox)
# Reparación documentada (decisión del usuario, 2026-10-22): make_valid solo
# a las geometrías inválidas.
catastro, repairs = repair_invalid_geometries(
    catastro, params.poly_id_column, params.id_column
)
repairs.to_csv(snakemake.output.repairs, index=False)
logger.warning("Geometrías del catastro reparadas con make_valid: %d", len(repairs))

strata = rasterize_strata(
    catastro, params.id_column, params.by_id, params.codes, transform, shape, params.crs
)
id_uso = rasterize_id_uso(
    catastro, params.id_column, params.id_uso_codes, transform, shape, params.crs
)

perimeters = gpd.read_file(snakemake.input.perimeters)
mine = perimeters[perimeters["fire_id"] == fire_id]
if mine.empty:
    raise ValueError(f"{fire_id}: sin perímetro")
perimeter = mine.to_crs(params.crs).geometry.union_all()
zone = analysis_zone(perimeter, params.buffer_m, transform, shape)
border = class_border(strata, params.border_px)

valid_index = first != nodata
# Analizable = con índice, dentro del catastro del Biobío (estrato != 0), dentro del
# perímetro o su buffer, y fuera de bordes de clase.
analyzable = valid_index & (strata != 0) & (zone != 0) & ~border

bands = {
    "estrato": strata,
    "id_uso": id_uso,
    "zona": zone,
    "borde": border.astype("uint8"),
    "analizable": analyzable.astype("uint8"),
}
profile.update(
    count=len(bands),
    dtype="uint8",
    nodata=None,
    compress="deflate",
    tiled=True,
    blockxsize=256,
    blockysize=256,
)
Path(snakemake.output.raster).parent.mkdir(parents=True, exist_ok=True)
with rasterio.open(snakemake.output.raster, "w", **profile) as dst:
    for i, (name, data) in enumerate(bands.items(), start=1):
        dst.write(data, i)
        dst.set_band_description(i, name)

inv = {v: k for k, v in params.codes.items()}
rows = []
for code, name in inv.items():
    in_stratum = strata == code
    rows.append(
        {
            "fire_id": fire_id,
            "estrato": name,
            "pixeles_perimetro": int((in_stratum & valid_index & (zone == 1)).sum()),
            "pixeles_borde_perimetro": int(
                (in_stratum & valid_index & (zone == 1) & border).sum()
            ),
            "pixeles_analizables": int((in_stratum & analyzable & (zone == 1)).sum()),
            "pixeles_analizables_buffer": int(
                (in_stratum & analyzable & (zone == 2)).sum()
            ),
        }
    )
rows.append(
    {
        "fire_id": fire_id,
        "estrato": "sin_catastro",
        "pixeles_perimetro": int(((strata == 0) & valid_index & (zone == 1)).sum()),
        "pixeles_borde_perimetro": 0,
        "pixeles_analizables": 0,
        "pixeles_analizables_buffer": 0,
    }
)
table = pd.DataFrame(rows)
table.to_csv(snakemake.output.counts, index=False)
logger.info("Conteo por estrato:\n%s", table.to_string())
