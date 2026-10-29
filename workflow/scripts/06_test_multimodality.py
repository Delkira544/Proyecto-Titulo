"""Silverman, dip y BIC por combinación (pool o por incendio)."""

from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from burnsev.multimodality import build_tasks, run_task
from burnsev.runlog import setup_logging

# Con Python 3.14 el método de arranque por defecto es 'forkserver': cada proceso hijo
# vuelve a importar este archivo, donde no existe `snakemake`. El cuerpo va protegido.
if __name__ == "__main__":
    params = snakemake.params
    logger = setup_logging(snakemake.log[0], dict(params))
    mm = params.mm

    pixels = pd.read_parquet(snakemake.input.pixels)
    fires = pd.read_csv(snakemake.input.fires, sep="\t")
    bad = set(pixels["fire_id"].astype(str)) - set(
        fires.loc[fires["role"] == params.role, "fire_id"]
    )
    if bad:
        raise ValueError(f"Incendios que no son de rol {params.role}: {sorted(bad)}")

    by_fire = params.level == "incendio"
    kwargs = {
        "alpha": mm["alfa"],
        "n_sample": mm["n_muestra"],
        "n_rep": mm["replicas_incendio"] if by_fire else mm["replicas"],
        "n_boot": mm["bootstrap_silverman"],
        "k_max": mm["k_max"],
        "n_init": mm["n_init"],
        "covariance_type": mm["covarianza"],
        "clip_pct": mm["recorte_percentil"],
    }
    tasks = build_tasks(
        pixels,
        indices=params.indices,
        strata=params.strata,
        zone=mm["zona"],
        by_fire=by_fire,
        min_pixels=params.min_pixels,
        base_seed=params.seed,
        kwargs=kwargs,
    )
    logger.info(
        "Nivel %s: %d combinaciones, %d procesos",
        params.level,
        len(tasks),
        snakemake.threads,
    )
    with ProcessPoolExecutor(max_workers=snakemake.threads) as pool:
        rows = list(pool.map(run_task, tasks))
    result = pd.DataFrame(rows)
    logger.info("Resultado:\n%s", result.drop(columns=["metodo"]).to_string())
    result.to_csv(snakemake.output[0], index=False)
