"""Suficiencia de cada estrato según el mínimo configurado (RNF-03, supuesto S6)."""

from pathlib import Path

import pandas as pd

from burnsev.runlog import setup_logging
from burnsev.strata import stratum_sufficiency

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

counts = pd.concat([pd.read_csv(f) for f in snakemake.input], ignore_index=True)
by_stratum = pd.DataFrame(
    {
        "fire_id": counts["fire_id"],
        "estrato": counts["estrato"],
        "pixeles": counts["pixeles_analizables"],
    }
)
by_stratum = by_stratum.loc[by_stratum["estrato"] != "sin_catastro"]
table = stratum_sufficiency(
    by_stratum,
    params.min_pixels,
    params.min_fires,
    params.min_pixels_per_fire,
)
table["estado"] = [
    "suficiente" if ok else "datos insuficientes" for ok in table["suficiente"]
]
Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
table.to_csv(snakemake.output[0], index=False)
logger.info("Suficiencia por estrato:\n%s", table.to_string())
