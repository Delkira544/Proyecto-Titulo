"""Extrae los píxeles analizables de un incendio a una tabla Parquet."""

from pathlib import Path

import rasterio

from burnsev.exports import check_alignment
from burnsev.pixel_stats import extract_pixels
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
fire_id = snakemake.wildcards.fire_id

with (
    rasterio.open(snakemake.input.indices) as idx,
    rasterio.open(snakemake.input.labels) as lab,
):
    for src in (idx, lab):
        if src.crs is None:
            raise ValueError(f"{fire_id}: ráster sin CRS ({src.name})")
    check_alignment(
        {
            "crs": str(idx.crs),
            "transform": tuple(idx.transform)[:6],
            "shape": idx.shape,
        },
        {
            "crs": str(lab.crs),
            "transform": tuple(lab.transform)[:6],
            "shape": lab.shape,
        },
    )
    if idx.nodata != params.nodata:
        raise ValueError(
            f"{fire_id}: nodata {idx.nodata} != configurado {params.nodata}"
        )
    indices, index_names = idx.read(), list(idx.descriptions)
    labels, label_names = lab.read(), list(lab.descriptions)

names = {code: name for name, code in params.strata_codes.items()}
table = extract_pixels(
    indices, labels, index_names, label_names, names, params.nodata, fire_id
)
Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
table.to_parquet(snakemake.output[0], index=False)
logger.info("%s: %d píxeles analizables", fire_id, len(table))
logger.info("Por estrato y zona:\n%s", table.groupby(["estrato", "zona"]).size())
