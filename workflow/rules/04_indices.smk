# Etapa 04: índices de severidad desde GEE, recortados a perímetro + buffer y etiquetados por estrato.
_PROD = config["indices_export"]["producto"]


rule export_fire_indices:
    """Compone pre/post, calcula dnbr/rdnbr/bai/mirbi y descarga el GeoTIFF (GEE)."""
    input:
        perimeters=f"{INT}/escenas/perimetros_dentro.gpkg",
        usability=f"{EXT_META}/fires_usability.csv",
    output:
        raster=f"{PROC}/indices/{_PROD}_{{fire_id}}_indices_{{fecha}}.tif",
        scenes=f"{PROC}/indices/{_PROD}_{{fire_id}}_escenas_{{fecha}}.csv",
    params:
        collection=config["sensor"]["coleccion_gee"],
        bands=config["indices_export"]["bandas"],
        bad_classes=config["calidad"]["scl_clases_malas"],
        scale_refl=config["indices_export"]["escala_reflectancia"],
        scale_m=config["sensor"]["resolucion_m"],
        crs=config["indices_export"]["crs_export"],
        buffer_m=config["indices_export"]["buffer_m"],
        simplify_m=config["gee"]["simplificar_m"],
        nodata=config["indices_export"]["nodata"],
        max_mb=config["indices_export"]["descarga_max_mb"],
        bai=config["indices_export"]["bai"],
        mirbi=config["indices_export"]["mirbi"],
        rdnbr_eps=config["indices_export"]["rdnbr_eps_nbr_pre"],
        project_env=config["gee"]["proyecto_env"],
    log:
        f"{LOGS}/export_fire_indices_{{fire_id}}_{{fecha}}.log",
    benchmark:
        "benchmarks/export_fire_indices_{fire_id}_{fecha}.tsv"
    script:
        "../scripts/04_export_fire_indices.py"


rule label_pixel_strata:
    """Rasteriza el estrato CONAF sobre la grilla de los índices (local)."""
    input:
        raster=f"{PROC}/indices/{_PROD}_{{fire_id}}_indices_{{fecha}}.tif",
        catastro=config["rutas"]["catastro_sit"],
        perimeters=f"{INT}/escenas/perimetros_dentro.gpkg",
    output:
        raster=f"{PROC}/indices/{_PROD}_{{fire_id}}_estrato_{{fecha}}.tif",
        counts=f"{PROC}/indices/{_PROD}_{{fire_id}}_conteo_estrato_{{fecha}}.csv",
        repairs=f"{PROC}/indices/{_PROD}_{{fire_id}}_reparaciones_sit_{{fecha}}.csv",
    params:
        crs=config["indices_export"]["crs_export"],
        id_column=config["indices_export"]["estratos"]["columna_sit"],
        poly_id_column=config["indices_export"]["estratos"]["columna_id_poligono"],
        by_id=config["indices_export"]["estratos"]["por_id_uso"],
        codes=config["indices_export"]["estratos"]["codigos"],
        id_uso_codes=config["indices_export"]["estratos"]["codigos_id_uso"],
        buffer_m=config["indices_export"]["buffer_m"],
        border_px=config["indices_export"]["exclusion_borde_px"],
    log:
        f"{LOGS}/label_pixel_strata_{{fire_id}}_{{fecha}}.log",
    script:
        "../scripts/04_label_pixel_strata.py"


rule assess_strata_sufficiency:
    """Cuenta píxeles analizables por estrato y marca los de datos insuficientes."""
    input:
        conteos_estrato,
    output:
        f"{RES}/tables/suficiencia_estratos.csv",
    params:
        min_pixels=config["calidad"]["minimo_estrato"]["pixeles"],
        min_fires=config["calidad"]["minimo_estrato"]["incendios"],
        min_pixels_per_fire=config["calidad"]["minimo_estrato"]["pixeles_por_incendio"],
    log:
        f"{LOGS}/assess_strata_sufficiency.log",
    script:
        "../scripts/04_assess_strata_sufficiency.py"


localrules:
    assess_strata_sufficiency,
    export_fire_indices,
