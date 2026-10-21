# Etapa 02: catálogo de incendios de calibración con estado dentro/fuera y motivo.

rule build_fire_catalog:
    """Armoniza las temporadas, filtra Biobío/fechas/superficie y asigna fire_id."""
    input:
        shp=shapefiles_crudos,
        schema_columns=config["rutas"]["esquema_columnas"],
    output:
        catalog=f"{RES}/catalogo/catalogo_incendios.csv",
        fires=f"{RES}/catalogo/fires.tsv",
    params:
        encoding=config["ingesta"]["encoding_si_falta_cpg"],
        region_code=config["seleccion"]["region_codigo"],
        region_names=config["seleccion"]["region_valores_aceptados"],
        crs=config["ingesta"]["crs_trabajo"],
        window=config["seleccion"]["periodos"]["calibracion"],
        min_area_ha=config["seleccion"]["superficie_min_ha"],
        id_prefix=config["proyecto"]["prefijo_id"],
    log:
        f"{LOGS}/build_fire_catalog.log",
    benchmark:
        "benchmarks/build_fire_catalog.tsv"
    script:
        "../scripts/02_build_fire_catalog.py"
