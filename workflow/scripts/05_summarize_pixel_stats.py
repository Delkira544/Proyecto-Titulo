"""Estadísticos, datos de histogramas y resumen por incendio."""

import pandas as pd

from burnsev.pixel_stats import (
    display_range,
    histogram_table,
    summary_table,
)
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

pixels = pd.read_parquet(snakemake.input.pixels)
for col in ("fire_id", "estrato", "zona"):
    pixels[col] = pixels[col].astype(str)
indices = list(params.indices)
order = list(params.strata_order)
if set(pixels["estrato"]) - set(order):
    raise ValueError(f"Estratos fuera de estratos_orden: {set(pixels['estrato'])}")

# 'ambas' = perímetro + buffer
both = pixels.assign(zona="ambas")
all_zones = pd.concat([pixels, both], ignore_index=True)

by_stratum = summary_table(all_zones, indices, ["estrato", "zona"])
by_fire = summary_table(all_zones, indices, ["fire_id", "estrato", "zona"])
by_stratum.to_csv(snakemake.output.by_stratum, index=False)
by_fire.to_csv(snakemake.output.by_fire, index=False)

# Bins fijos por índice (mismo rango para todos los estratos y zonas)
parts = []
for index in indices:
    low, high = display_range(pixels[index], params.percentiles)
    logger.info("%s: rango de bins [%.4f, %.4f]", index, low, high)
    for keys, group in all_zones.groupby(["estrato", "zona"]):
        estrato, zona = str(keys[0]), str(keys[1])  # type: ignore[index]
        hist = histogram_table(group[index], params.bins, (low, high))
        parts.append(hist.assign(indice=index, estrato=estrato, zona=zona))
hist_all = pd.concat(parts, ignore_index=True)
hist_all = hist_all[
    ["indice", "estrato", "zona", "borde_inf", "borde_sup", "conteo", "densidad"]
]
hist_all.to_csv(snakemake.output.histograms, index=False)

# Resumen por incendio (para presentar)
catalog = pd.read_csv(snakemake.input.catalog).set_index("fire_id")
usab = pd.read_csv(snakemake.input.usability).set_index("fire_id")
inside = pixels[pixels["zona"] == "dentro"]
counts = pd.DataFrame(
    inside.groupby(["fire_id", "estrato"]).size().unstack(fill_value=0)
)
counts = pd.DataFrame(counts.reindex(columns=order, fill_value=0))
counts = counts.add_prefix("px_dentro_")
med = (
    inside.groupby("fire_id")[["dnbr", "rdnbr"]].median().add_prefix("mediana_dentro_")
)
med_forest = (
    inside.query("estrato == 'forestal'")
    .groupby("fire_id")[["dnbr", "rdnbr"]]
    .median()
    .add_prefix("mediana_forestal_")
)
fire_ids = sorted(pixels["fire_id"].unique())
overview = pd.DataFrame(index=pd.Index(fire_ids, name="fire_id"))
overview["nombre"] = catalog.loc[fire_ids, "nombre"]
overview["comuna"] = catalog.loc[fire_ids, "comuna"]
overview["fecha_inicio"] = catalog.loc[fire_ids, "fecha_inicio"]
overview["fecha_pre"] = usab.loc[fire_ids, "fecha_pre"]
overview["fecha_post"] = usab.loc[fire_ids, "fecha_post"]
overview["superficie_ha"] = catalog.loc[fire_ids, "superficie_ha_calc"].round(1)
overview["nubosidad_pre_pct"] = usab.loc[fire_ids, "nubosidad_pre_pct"]
overview["nubosidad_post_pct"] = usab.loc[fire_ids, "nubosidad_post_pct"]
overview = overview.join(counts).join(med).join(med_forest)
overview["px_buffer_fuera"] = (
    pixels[pixels["zona"] == "fuera"].groupby("fire_id").size().reindex(fire_ids)
)
overview = overview.sort_values("fecha_inicio").round(4).reset_index()
overview.to_csv(snakemake.output.overview, index=False)
logger.info("Resumen de %d incendios:\n%s", len(overview), overview.to_string())
