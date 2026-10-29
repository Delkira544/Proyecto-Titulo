"""Cajas por índice y estrato, y panorama de los incendios usables."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from burnsev.pixel_stats import display_range  # noqa: E402
from burnsev.runlog import setup_logging  # noqa: E402

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
indices, strata = list(params.indices), list(params.strata_order)
COLORS = {"dentro": "#D55E00", "fuera": "#0072B2"}
STRATA_COLORS = {"forestal": "#009E73", "otras": "#E69F00", "urbano": "#CC79A7"}
suff = pd.read_csv(snakemake.input.sufficiency).set_index("estrato")["estado"]

pixels = pd.read_parquet(snakemake.input.pixels)
for col in ("estrato", "zona"):
    pixels[col] = pixels[col].astype(str)

# --- Cajas dentro/fuera por estrato ---
fig, axes = plt.subplots(
    1, len(indices), figsize=(4 * len(indices), 4.2), squeeze=False
)
for ax, index in zip(axes[0], indices, strict=True):
    low, high = display_range(pixels[index], params.percentiles)
    for k, stratum in enumerate(strata):
        for off, zone in ((-0.18, "dentro"), (0.18, "fuera")):
            v = pixels.loc[
                (pixels["estrato"] == stratum) & (pixels["zona"] == zone), index
            ].to_numpy()
            if v.size == 0:
                continue
            bp = ax.boxplot(
                v,
                positions=[k + off],
                widths=0.3,
                showfliers=False,
                patch_artist=True,
                medianprops={"color": "black"},
            )
            bp["boxes"][0].set_facecolor(COLORS[zone])
            bp["boxes"][0].set_alpha(0.6)
    ax.set_ylim(low, high)
    labels = [s + ("*" if suff.get(s) != "suficiente" else "") for s in strata]
    ax.set_xticks(range(len(strata)), labels)
    ax.set_title(index.upper())
    ax.spines[["top", "right"]].set_visible(False)
handles = [Rectangle((0, 0), 1, 1, color=c, alpha=0.6) for c in COLORS.values()]
fig.legend(handles, ["Dentro del perímetro", "Buffer (fuera)"], loc="lower center",
           ncol=2, frameon=False)  # fmt: skip
fig.suptitle(
    "Índices por estrato (sin valores atípicos; * = datos insuficientes)", fontsize=12
)
fig.tight_layout(rect=(0, 0.06, 1, 0.95))
Path(snakemake.output.boxes).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(snakemake.output.boxes, dpi=params.dpi)
plt.close(fig)

# --- Panorama de incendios ---
ov = pd.read_csv(snakemake.input.overview)
x = np.arange(len(ov))
fig, (top, bottom) = plt.subplots(
    2, 1, figsize=(max(10, 0.45 * len(ov)), 7), sharex=True,
    gridspec_kw={"height_ratios": [3, 2]},
)  # fmt: skip
width = 0.8 / len(strata)
for k, stratum in enumerate(strata):
    vals = ov[f"px_dentro_{stratum}"].to_numpy(dtype=float)
    vals[vals == 0] = np.nan  # barras en escala log: el 0 no se dibuja
    top.bar(x + (k - (len(strata) - 1) / 2) * width, vals, width=width,
            color=STRATA_COLORS[stratum], label=stratum)  # fmt: skip
top.set_yscale("log")
top.set_ylabel("píxeles analizables dentro\ndel perímetro (escala log)")
top.legend(frameon=False, title="estrato")
bottom.plot(
    x, ov["mediana_dentro_dnbr"], "o", color="#D55E00", label="todos los estratos"
)
bottom.plot(x, ov["mediana_forestal_dnbr"], "s", mfc="none", color="#009E73",
            label="solo forestal")  # fmt: skip
bottom.set_ylabel("mediana dNBR\n(dentro)")
bottom.legend(frameon=False)
bottom.set_xticks(x, ov["fire_id"], rotation=90, fontsize=8)
for ax in (top, bottom):
    ax.spines[["top", "right"]].set_visible(False)
top.set_title("Incendios usables de calibración, ordenados por fecha de inicio")
fig.tight_layout()
fig.savefig(snakemake.output.panorama, dpi=params.dpi, bbox_inches="tight")
logger.info("Figuras escritas")
