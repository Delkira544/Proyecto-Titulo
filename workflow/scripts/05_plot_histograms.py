"""Grilla de histogramas (densidad) índice × estrato, dentro vs fuera del perímetro."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from burnsev.runlog import setup_logging  # noqa: E402

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))

hist = pd.read_csv(snakemake.input.histograms)
stats = pd.read_csv(snakemake.input.stats).set_index(["indice", "estrato", "zona"])
suff = pd.read_csv(snakemake.input.sufficiency).set_index("estrato")["estado"]

# Paleta Okabe-Ito (apta para daltonismo)
COLORS = {"dentro": "#D55E00", "fuera": "#0072B2"}
LABELS = {"dentro": "Dentro del perímetro", "fuera": "Buffer (fuera)"}
indices, strata = list(params.indices), list(params.strata_order)

fig, axes = plt.subplots(
    len(indices),
    len(strata),
    figsize=(4.2 * len(strata), 2.8 * len(indices)),
    sharex="row",
    squeeze=False,
)
for i, index in enumerate(indices):
    for j, stratum in enumerate(strata):
        ax = axes[i][j]
        for zone in ("dentro", "fuera"):
            h = hist[
                (hist["indice"] == index)
                & (hist["estrato"] == stratum)
                & (hist["zona"] == zone)
            ]
            if h.empty or h["conteo"].sum() == 0:
                continue
            mid = (h["borde_inf"] + h["borde_sup"]) / 2
            ax.fill_between(
                mid, h["densidad"], step="mid", alpha=0.35, color=COLORS[zone]
            )
            ax.step(mid, h["densidad"], where="mid", lw=1, color=COLORS[zone],
                    label=LABELS[zone])  # fmt: skip
            med = stats.loc[(index, stratum, zone), "mediana"]
            ax.axvline(med, color=COLORS[zone], ls="--", lw=1)
        n_in = int(stats.loc[(index, stratum, "dentro"), "n"])
        title = f"{stratum} (n dentro = {n_in:,})".replace(",", ".")
        if suff.get(stratum) != "suficiente":
            title += "\ndatos insuficientes"
        if i == 0:
            ax.set_title(title, fontsize=10)
        elif suff.get(stratum) != "suficiente":
            ax.set_title("datos insuficientes", fontsize=8, color="0.4")
        if j == 0:
            ax.set_ylabel(f"{index.upper()}\ndensidad")
        ax.spines[["top", "right"]].set_visible(False)
        if i == len(indices) - 1:
            ax.set_xlabel("valor del índice")
handles, labels = axes[0][0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
fig.suptitle(
    "Distribución de los índices de severidad por estrato (línea punteada = mediana)",
    fontsize=12,
)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(snakemake.output[0], dpi=params.dpi)
logger.info("Figura escrita en %s", snakemake.output[0])
