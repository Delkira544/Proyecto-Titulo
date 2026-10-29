"""Tabla final por índice y estrato y combinaciones que pasan a percentiles."""

import pandas as pd

from burnsev.multimodality import contingency_active
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

pool = pd.read_csv(snakemake.input.pool)
fires = pd.read_csv(snakemake.input.fires)
suff = pd.read_csv(snakemake.input.sufficiency)[["estrato", "suficiente", "estado"]]

# Sensibilidad: fracción de incendios cuya decisión final es multimodal
sens = (
    fires.assign(multi=fires["decision_final"] == "multimodal")
    .groupby(["indice", "estrato"])
    .agg(
        n_incendios=("fire_id", "nunique"), frac_incendios_multimodal=("multi", "mean")
    )
    .reset_index()
)
table = pool.merge(sens, on=["indice", "estrato"], how="left").merge(
    suff, on="estrato", how="left"
)
table["reserva"] = table["estado"].where(~table["suficiente"], "")
order = {s: i for i, s in enumerate(params.strata)}
table = table.sort_values(
    ["estrato", "indice"], key=lambda c: c.map(order) if c.name == "estrato" else c
)

# ADR-0010: las combinaciones con datos insuficientes no entran en la proporción
valid = table[table["suficiente"]]
active = contingency_active(list(valid["decision_final"]), params.min_proportion)
share = (valid["decision_final"] == "multimodal").mean()
table["contingencia_activada"] = active
logger.info(
    "Multimodales (suficientes): %.3f de %d; mínimo %.2f; contingencia activada: %s",
    share,
    len(valid),
    params.min_proportion,
    active,
)
table.to_csv(snakemake.output.summary, index=False)

pct = table.loc[
    table["metodo"] == "percentiles",
    ["indice", "estrato", "veredicto", "p_silverman", "p_dip", "k_bic", "reserva"],
].copy()
pct["decision"] = "usar percentiles (ADR-0010)"
pct["percentiles"] = " ".join(str(p) for p in params.percentiles)
pct["contingencia_activada"] = active
pct.to_csv(snakemake.output.percentiles, index=False)
logger.info("Combinaciones a percentiles:\n%s", pct.to_string())
