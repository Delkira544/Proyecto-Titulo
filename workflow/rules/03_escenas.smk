# Etapa 03: nubosidad pre/post dentro del perímetro (Earth Engine) y marcado de usables.
rule extract_fire_perimeters:
    """Perímetros de los incendios 'dentro' con su fire_id (solo para delimitar)."""
    input:
        shp=shapefiles_crudos,
        schema_columns=config["rutas"]["esquema_columnas"],
        catalog=f"{RES}/catalogo/catalogo_incendios.csv",
    output:
        f"{INT}/escenas/perimetros_dentro.gpkg",
    params:
        crs=config["ingesta"]["crs_trabajo"],
        encoding=config["ingesta"]["encoding_si_falta_cpg"],
        region_code=config["seleccion"]["region_codigo"],
        region_names=config["seleccion"]["region_valores_aceptados"],
    log:
        f"{LOGS}/extract_fire_perimeters.log",
    benchmark:
        "benchmarks/extract_fire_perimeters.tsv"
    script:
        "../scripts/03_extract_perimeters.py"


rule query_scene_cloud:
    """Consulta a GEE: nubosidad SCL dentro del perímetro, por rebanadas de días."""
    input:
        perimeters=f"{INT}/escenas/perimetros_dentro.gpkg",
        fires=f"{RES}/catalogo/fires.tsv",
    output:
        f"{INT}/escenas/{{fire_id}}_stats.csv",
    params:
        collection=config["sensor"]["coleccion_gee"],
        scale_m=config["sensor"]["resolucion_m"],
        bad_classes=config["calidad"]["scl_clases_malas"],
        max_bad_pct=config["calidad"]["nubosidad_max_pct"],
        min_coverage_pct=config["calidad"]["cobertura_min_pct"],
        steps=config["escenas"]["exploracion_pasos_dias"],
        max_days={
            "pre": config["escenas"]["ventana_pre_dias"],
            "post": config["escenas"]["ventana_post_dias"],
        },
        crs=config["ingesta"]["crs_trabajo"],
        simplify_m=config["gee"]["simplificar_m"],
        tile_scale=config["gee"]["tile_scale"],
        project_env=config["gee"]["proyecto_env"],
    log:
        f"{LOGS}/query_scene_cloud_{{fire_id}}.log",
    benchmark:
        "benchmarks/query_scene_cloud_{fire_id}.tsv"
    script:
        "../scripts/03_query_scene_cloud.py"


rule review_fire_cloudiness:
    """Decide usable/excluido por incendio y escribe el CSV versionado y su resumen."""
    input:
        stats=stats_de_incendios,
        catalog=f"{RES}/catalogo/catalogo_incendios.csv",
    output:
        catalog=f"{RES}/catalogo/catalogo_incendios_revisado.csv",
        usability=f"{EXT_META}/fires_usability.csv",
        summary=f"{EXT_META}/fires_usability_summary.csv",
    params:
        max_bad_pct=config["calidad"]["nubosidad_max_pct"],
        min_coverage_pct=config["calidad"]["cobertura_min_pct"],
        require_both=config["calidad"]["requiere_pre_y_post"],
    log:
        f"{LOGS}/review_fire_cloudiness.log",
    benchmark:
        "benchmarks/review_fire_cloudiness.tsv"
    script:
        "../scripts/03_review_fire_cloudiness.py"


rule make_quicklooks:
    """Miniaturas RGB de las escenas elegidas de los incendios usables (descarga)."""
    input:
        perimeters=f"{INT}/escenas/perimetros_dentro.gpkg",
        usability=f"{EXT_META}/fires_usability.csv",
    output:
        touch(f"{RES}/figures/quicklooks/.hecho"),
    params:
        collection=config["sensor"]["coleccion_gee"],
        crs=config["ingesta"]["crs_trabajo"],
        simplify_m=config["gee"]["simplificar_m"],
        thumb_px=config["gee"]["miniatura_px"],
        project_env=config["gee"]["proyecto_env"],
    log:
        f"{LOGS}/make_quicklooks.log",
    script:
        "../scripts/03_make_quicklooks.py"


localrules:
    extract_fire_perimeters,
    query_scene_cloud,
    review_fire_cloudiness,
    make_quicklooks,
