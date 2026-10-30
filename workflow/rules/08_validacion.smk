# Etapa 08: evento de validación (enero 2026) con EMSR859 como referencia binaria (ADR-0020).
# Reutiliza los scripts de las etapas 03 y 04 con entradas y salidas propias del rol
# 'validacion': ninguna regla de calibración lee estos archivos (tests/test_no_leakage.py).
_VAL = config["validacion_emsr859"]
_VAL_IDS = [entry["fire_id"] for entry in _VAL["aois"]]


rule build_validation_perimeters:
    """Zona de trabajo (AOI ∩ Biobío − sin analizar) y área quemada de referencia."""
    input:
        emsr=archivos_emsr859,
        regions=config["rutas"]["regiones"],
        companions=archivos_regiones,
    output:
        perimeters=f"{INT}/validacion/perimetros_validacion.gpkg",
        reference=f"{INT}/validacion/referencia_emsr859.gpkg",
        catalog=f"{RES}/catalogo/catalogo_validacion.csv",
        fires=f"{RES}/catalogo/fires_validacion.tsv",
    params:
        root=RAW_EMSR,
        aois=_VAL["aois"],
        start_date=_VAL["fecha_inicio"],
        season=_VAL["temporada"],
        region_column=_VAL["region_columna"],
        region_code=config["seleccion"]["region_codigo"],
        burnt_layer=_VAL["capa_quemado"],
        excluded_layers=_VAL["capas_excluidas"],
        no_data_footprint=_VAL["huella_sin_dato"],
        mmu_m2=_VAL["umm_m2"],
        crs=config["ingesta"]["crs_trabajo"],
    log:
        f"{LOGS}/build_validation_perimeters.log",
    benchmark:
        "benchmarks/build_validation_perimeters.tsv"
    script:
        "../scripts/08_build_validation_perimeters.py"


use rule query_scene_cloud as query_validation_scene_cloud with:
    input:
        perimeters=f"{INT}/validacion/perimetros_validacion.gpkg",
        fires=f"{RES}/catalogo/fires_validacion.tsv",
    output:
        f"{INT}/validacion/escenas/{{fire_id}}_stats.csv",
    log:
        f"{LOGS}/query_validation_scene_cloud_{{fire_id}}.log",
    benchmark:
        "benchmarks/query_validation_scene_cloud_{fire_id}.tsv"


use rule review_fire_cloudiness as review_validation_cloudiness with:
    input:
        stats=[f"{INT}/validacion/escenas/{fire_id}_stats.csv" for fire_id in _VAL_IDS],
        catalog=f"{RES}/catalogo/catalogo_validacion.csv",
    output:
        catalog=f"{RES}/catalogo/catalogo_validacion_revisado.csv",
        usability=f"{EXT_META}/fires_validacion_usability.csv",
        summary=f"{EXT_META}/fires_validacion_usability_summary.csv",
    log:
        f"{LOGS}/review_validation_cloudiness.log",
    benchmark:
        "benchmarks/review_validation_cloudiness.tsv"


use rule export_fire_indices as export_validation_indices with:
    input:
        perimeters=f"{INT}/validacion/perimetros_validacion.gpkg",
        usability=f"{EXT_META}/fires_validacion_usability.csv",
    output:
        raster=f"{PROC}/validacion/indices/{_PROD}_{{fire_id}}_indices_{{fecha}}.tif",
        scenes=f"{PROC}/validacion/indices/{_PROD}_{{fire_id}}_escenas_{{fecha}}.csv",
    log:
        f"{LOGS}/export_validation_indices_{{fire_id}}_{{fecha}}.log",
    benchmark:
        "benchmarks/export_validation_indices_{fire_id}_{fecha}.tsv"


localrules:
    build_validation_perimeters,
    query_validation_scene_cloud,
    review_validation_cloudiness,
    export_validation_indices,
