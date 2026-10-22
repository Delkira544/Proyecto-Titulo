"""Decide usable/excluido por incendio y escribe el CSV versionado y el resumen."""

from pathlib import Path
from typing import cast

import pandas as pd

from burnsev.catalog import apply_cloud_review, summarize_usability
from burnsev.clouds import SIDES, Thresholds, decide_usable, pick_scene, side_diagnosis
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
thresholds = Thresholds(params.max_bad_pct, params.min_coverage_pct)

catalog = pd.read_csv(snakemake.input.catalog)
rows = []
for path in snakemake.input.stats:
    fire_id = Path(path).name.removesuffix("_stats.csv")
    stats = pd.read_csv(path)
    row: dict = {"fire_id": fire_id}
    diagnoses = {}
    for side in SIDES:
        side_stats = cast(pd.DataFrame, stats[stats["lado"] == side])
        diagnoses[side] = side_diagnosis(side_stats, thresholds)
        best = pick_scene(side_stats, thresholds)
        row[f"escena_{side}"] = None if best is None else best["scene_id"]
        row[f"fecha_{side}"] = None if best is None else best["fecha"]
        row[f"nubosidad_{side}_pct"] = None if best is None else best["nubosidad_pct"]
        row[f"cobertura_{side}_pct"] = None if best is None else best["cobertura_pct"]
        row[f"ventana_{side}_usada"] = None if best is None else best["rebanada"]
        row[f"escenas_exploradas_{side}"] = len(side_stats)
    row["estado_uso"], row["motivo_codigo"] = decide_usable(
        diagnoses["pre"], diagnoses["post"], params.require_both
    )
    rows.append(row)
review = pd.DataFrame(rows).sort_values("fire_id", ignore_index=True)

result = apply_cloud_review(catalog, review)
usability = result[
    ["fire_id", "fecha_inicio", "fecha_termino", "estado", "motivo_codigo", "motivo"]
].merge(
    review.drop(
        columns=[
            "estado_uso",
            "motivo_codigo",
            "nubosidad_pre_pct",
            "nubosidad_post_pct",
        ]
    ),
    on="fire_id",
    how="left",
)
nubosidad = review.set_index("fire_id")[["nubosidad_pre_pct", "nubosidad_post_pct"]]
usability = usability.join(nubosidad, on="fire_id")
usability = usability.round({c: 2 for c in usability.columns if c.endswith("_pct")})
summary = summarize_usability(result)

for out in (
    snakemake.output.catalog,
    snakemake.output.usability,
    snakemake.output.summary,
):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
result.to_csv(snakemake.output.catalog, index=False)
usability.to_csv(snakemake.output.usability, index=False)
summary.to_csv(snakemake.output.summary, index=False)
logger.info("Resumen:\n%s", summary.to_string(index=False))
