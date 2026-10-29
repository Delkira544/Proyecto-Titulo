# Etapa 06: multimodalidad por índice y estrato (Silverman, dip, BIC) y decisión Otsu/KDE vs percentiles.
_MM = config["multimodalidad"]
# Parámetros de las pruebas (sin los de visualización: cambiarlos no debe repetir el cálculo)
_MM_TEST = {k: v for k, v in _MM.items() if k != "figura_puntos_kde"}


rule test_multimodality_pool:
    """Silverman, dip y BIC por índice y estrato con los incendios agrupados."""
    input:
        pixels=f"{PROC}/tablas/valores_pixel.parquet",
        fires=f"{RES}/catalogo/fires.tsv",
    output:
        f"{RES}/tables/multimodalidad_pool.csv",
    params:
        level="pool",
        indices=config["estadistica"]["indices"],
        strata=config["estadistica"]["estratos_orden"],
        seed=config["semilla_aleatoria"],
        mm=_MM_TEST,
        min_pixels=0,
        role="calibracion",
    threads: 4
    log:
        f"{LOGS}/test_multimodality_pool.log",
    benchmark:
        f"benchmarks/test_multimodality_pool.tsv"
    script:
        "../scripts/06_test_multimodality.py"


rule test_multimodality_fire:
    """Lo mismo por incendio, como sensibilidad a la mezcla de incendios."""
    input:
        pixels=f"{PROC}/tablas/valores_pixel.parquet",
        fires=f"{RES}/catalogo/fires.tsv",
    output:
        f"{RES}/tables/multimodalidad_por_incendio.csv",
    params:
        level="incendio",
        indices=config["estadistica"]["indices"],
        strata=config["estadistica"]["estratos_orden"],
        seed=config["semilla_aleatoria"],
        mm=_MM_TEST,
        min_pixels=config["calidad"]["minimo_estrato"]["pixeles_por_incendio"],
        role="calibracion",
    threads: 4
    log:
        f"{LOGS}/test_multimodality_fire.log",
    benchmark:
        f"benchmarks/test_multimodality_fire.tsv"
    script:
        "../scripts/06_test_multimodality.py"


rule summarize_multimodality:
    """Tabla final por combinación y registro de las que pasan a percentiles (ADR-0010)."""
    input:
        pool=f"{RES}/tables/multimodalidad_pool.csv",
        fires=f"{RES}/tables/multimodalidad_por_incendio.csv",
        sufficiency=f"{RES}/tables/suficiencia_estratos.csv",
    output:
        summary=f"{RES}/tables/multimodalidad_indice_estrato.csv",
        percentiles=f"{RES}/tables/combinaciones_percentiles.csv",
    params:
        min_proportion=_MM["proporcion_minima_multimodal"],
        percentiles=_MM["percentiles_contingencia"],
        indices=config["estadistica"]["indices"],
        strata=config["estadistica"]["estratos_orden"],
    log:
        f"{LOGS}/summarize_multimodality.log",
    script:
        "../scripts/06_summarize_multimodality.py"


rule plot_discordant_combinations:
    """Histograma y KDE de las combinaciones con Silverman y dip en desacuerdo."""
    input:
        pixels=f"{PROC}/tablas/valores_pixel.parquet",
        summary=f"{RES}/tables/multimodalidad_indice_estrato.csv",
    output:
        f"{RES}/figures/multimodalidad_discordantes.png",
    params:
        seed=config["semilla_aleatoria"],
        mm=_MM,
        bins=config["estadistica"]["bins"],
        dpi=config["estadistica"]["figuras_dpi"],
    log:
        f"{LOGS}/plot_discordant_combinations.log",
    script:
        "../scripts/06_plot_discordant.py"


localrules:
    summarize_multimodality,
    plot_discordant_combinations,
