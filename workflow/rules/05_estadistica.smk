# Etapa 05: valores de píxel y estadística descriptiva por índice y estrato (insumo de multimodalidad).
_PROD5 = config["indices_export"]["producto"]
_EST = config["estadistica"]


rule extract_pixel_values:
    """Tabla de píxeles analizables de un incendio (estrato, dentro/fuera, índices)."""
    input:
        indices=f"{PROC}/indices/{_PROD5}_{{fire_id}}_indices_{{fecha}}.tif",
        labels=f"{PROC}/indices/{_PROD5}_{{fire_id}}_estrato_{{fecha}}.tif",
    output:
        temp(f"{INT}/pixeles/{{fire_id}}_{{fecha}}.parquet"),
    params:
        strata_codes=config["indices_export"]["estratos"]["codigos"],
        nodata=config["indices_export"]["nodata"],
    log:
        f"{LOGS}/extract_pixel_values_{{fire_id}}_{{fecha}}.log",
    script:
        "../scripts/05_extract_pixel_values.py"


rule merge_pixel_table:
    """Une los incendios usables en una sola tabla; exige que sean de calibración."""
    input:
        pixels=pixeles_por_incendio,
        fires=f"{RES}/catalogo/fires.tsv",
    output:
        f"{PROC}/tablas/valores_pixel.parquet",
    params:
        role="calibracion",
    log:
        f"{LOGS}/merge_pixel_table.log",
    script:
        "../scripts/05_merge_pixel_table.py"


rule summarize_pixel_stats:
    """Estadísticos, datos de histogramas y resumen por incendio."""
    input:
        pixels=f"{PROC}/tablas/valores_pixel.parquet",
        catalog=f"{RES}/catalogo/catalogo_incendios_revisado.csv",
        usability=f"{EXT_META}/fires_usability.csv",
    output:
        by_stratum=f"{RES}/tables/estadisticos_indice_estrato.csv",
        by_fire=f"{RES}/tables/estadisticos_por_incendio.csv",
        histograms=f"{RES}/tables/histogramas_indice_estrato.csv",
        overview=f"{RES}/tables/resumen_incendios.csv",
    params:
        indices=_EST["indices"],
        strata_order=_EST["estratos_orden"],
        bins=_EST["bins"],
        percentiles=_EST["rango_percentil"],
    log:
        f"{LOGS}/summarize_pixel_stats.log",
    script:
        "../scripts/05_summarize_pixel_stats.py"


rule plot_histograms:
    """Grilla índice × estrato con la densidad dentro y fuera del perímetro."""
    input:
        histograms=f"{RES}/tables/histogramas_indice_estrato.csv",
        stats=f"{RES}/tables/estadisticos_indice_estrato.csv",
        sufficiency=f"{RES}/tables/suficiencia_estratos.csv",
    output:
        f"{RES}/figures/histogramas_indice_estrato.png",
    params:
        indices=_EST["indices"],
        strata_order=_EST["estratos_orden"],
        dpi=_EST["figuras_dpi"],
    log:
        f"{LOGS}/plot_histograms.log",
    script:
        "../scripts/05_plot_histograms.py"


rule plot_overview:
    """Cajas por índice y estrato, y panorama de los incendios usables."""
    input:
        pixels=f"{PROC}/tablas/valores_pixel.parquet",
        overview=f"{RES}/tables/resumen_incendios.csv",
        sufficiency=f"{RES}/tables/suficiencia_estratos.csv",
    output:
        boxes=f"{RES}/figures/cajas_indice_estrato.png",
        panorama=f"{RES}/figures/panorama_incendios.png",
    params:
        indices=_EST["indices"],
        strata_order=_EST["estratos_orden"],
        percentiles=_EST["rango_percentil"],
        dpi=_EST["figuras_dpi"],
    log:
        f"{LOGS}/plot_overview.log",
    script:
        "../scripts/05_plot_overview.py"


localrules:
    extract_pixel_values,
    merge_pixel_table,
    summarize_pixel_stats,
    plot_histograms,
    plot_overview,
