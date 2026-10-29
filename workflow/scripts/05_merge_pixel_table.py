"""Une los Parquet por incendio en la tabla de valores de píxel."""

from pathlib import Path

import pandas as pd

from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

fires = pd.read_csv(snakemake.input.fires, sep="\t")
tables = [pd.read_parquet(f) for f in snakemake.input.pixels]
pixels = pd.concat(tables, ignore_index=True)

ids = set(pixels["fire_id"])
roles = fires.set_index("fire_id")["role"]
missing = ids - set(roles.index)
if missing:
    raise ValueError(f"Incendios fuera de fires.tsv: {sorted(missing)}")
wrong = sorted(i for i in ids if roles[i] != params.role)
if wrong:
    raise ValueError(f"Incendios que no son de '{params.role}': {wrong}")
for col in ("fire_id", "estrato", "zona"):
    pixels[col] = pixels[col].astype("category")

Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
pixels.to_parquet(snakemake.output[0], index=False)
logger.info("%d incendios, %d píxeles", len(ids), len(pixels))
