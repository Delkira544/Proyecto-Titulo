"""Histograma y KDE de las combinaciones discordantes (Silverman vs dip)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from burnsev.multimodality import (
    clip_to_percentiles,
    kde_curve,
    rule_of_thumb_bandwidth,
    seed_for,
    subsample,
)
from burnsev.runlog import setup_logging

INK = "#1f2933"  # texto principal
MUTED = "#5f6b76"  # texto secundario y ejes
BAR = "#c9d1d9"  # histograma (neutro)
LINE = "#1f5fae"  # KDE con la regla práctica
LINE_CRIT = "#c2570c"  # KDE con el ancho de banda crítico

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
mm = params.mm

summary = pd.read_csv(snakemake.input.summary)
cases = summary[summary["veredicto"] == "discordante"].reset_index(drop=True)
logger.info("Combinaciones discordantes: %d", len(cases))

pixels = pd.read_parquet(snakemake.input.pixels)
inside = pixels[pixels["zona"] == mm["zona"]]

n_cases = max(len(cases), 1)
fig, axes = plt.subplots(1, n_cases, figsize=(5.2 * n_cases, 4.2), squeeze=False)
if cases.empty:
    axes[0, 0].text(0.5, 0.5, "Sin combinaciones discordantes", ha="center", color=INK)
    axes[0, 0].set_axis_off()

records = cases.to_dict(orient="records")  # type: ignore[call-overload]
for ax, row in zip(axes[0], records, strict=False):
    column = inside.loc[inside["estrato"] == row["estrato"], row["indice"]]
    clipped = clip_to_percentiles(column.to_numpy(), mm["recorte_percentil"])
    # misma submuestra que la primera réplica de la prueba (misma derivación de semilla)
    seed = seed_for(params.seed, row["estrato"], row["indice"])
    sample = subsample(clipped, mm["n_muestra"], np.random.default_rng(seed))

    h_rot = rule_of_thumb_bandwidth(sample)
    h_crit = float(row["h_crit_mediano"])
    grid, dens_rot, modes_rot = kde_curve(sample, h_rot, mm["figura_puntos_kde"])
    _, dens_crit, _ = kde_curve(sample, h_crit, mm["figura_puntos_kde"])

    ax.hist(sample, bins=params.bins, density=True, color=BAR, linewidth=0)
    ax.plot(
        grid,
        dens_rot,
        color=LINE,
        linewidth=1.6,
        label=f"KDE, regla práctica (h = {h_rot:.3g})",
    )
    ax.plot(
        grid,
        dens_crit,
        color=LINE_CRIT,
        linewidth=1.6,
        label=f"KDE, ancho crítico (h = {h_crit:.3g})",
    )
    ax.plot(
        modes_rot,
        np.interp(modes_rot, grid, dens_rot),
        "v",
        color=LINE,
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=1.0,
    )
    ax.set_title(
        f"{row['estrato']} · {row['indice']}\n"
        f"Silverman p = {row['p_silverman']:.3g} · dip p = {row['p_dip']:.2f} · "
        f"modas con regla práctica: {len(modes_rot)}",
        fontsize=9,
        color=INK,
    )
    ax.set_xlabel(row["indice"], color=MUTED)
    ax.set_ylabel("densidad", color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.grid(axis="y", color=BAR, linewidth=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=7.5, labelcolor=INK, loc="upper right")
    logger.info(
        "%s %s: n=%d, h_rot=%.4g, h_crit=%.4g, h_crit/h_rot=%.2f, modas(h_rot)=%d",
        row["estrato"],
        row["indice"],
        sample.size,
        h_rot,
        h_crit,
        h_crit / h_rot,
        len(modes_rot),
    )

fig.suptitle(
    "Combinaciones con Silverman y dip en desacuerdo (pool, dentro del perímetro, "
    "rango recortado)",
    fontsize=10,
    color=INK,
)
fig.tight_layout()
fig.savefig(snakemake.output[0], dpi=params.dpi)
