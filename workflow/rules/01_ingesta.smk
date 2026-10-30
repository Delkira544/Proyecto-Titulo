# Etapa 01: inventario y procedencia de los datos crudos.

rule inspect_raw_shapes:
    """Qué hay, si está completo, CRS, columnas y geometrías inválidas por temporada."""
    input:
        shp=shapefiles_crudos,
    output:
        f"{RES}/catalogo/inventario_shapefiles.csv",
    log:
        f"{LOGS}/inspect_raw_shapes.log",
    benchmark:
        "benchmarks/inspect_raw_shapes.tsv"
    script:
        "../scripts/01_inspect_shapes.py"


rule compute_raw_manifest:
    """Manifiesto de procedencia con sha256 de cada archivo crudo (CONAF, EMSR859, límites)."""
    input:
        archivos_crudos,
    output:
        f"{EXT_META}/manifest.tsv",
    params:
        root=RAW,
        sources=config["fuentes_raw"],
    log:
        f"{LOGS}/compute_raw_manifest.log",
    benchmark:
        "benchmarks/compute_raw_manifest.tsv"
    script:
        "../scripts/01_compute_raw_checksums.py"


rule inspect_emsr859:
    """Spike HU-04.1: campos, valores y conteos de EMSR859 por AOI; veredicto del supuesto S2."""
    input:
        archivos_emsr859,
    output:
        fields=f"{RES}/tables/emsr859_campos.tsv",
        counts=f"{RES}/tables/emsr859_conteos_aoi.tsv",
        layers=f"{RES}/tables/emsr859_capas_aoi.tsv",
        summary=f"{RES}/tables/emsr859_resumen_xlsx.tsv",
        report=f"{RES}/emsr859_spike_hu041.md",
    params:
        root=RAW_EMSR,
        crs=config["ingesta"]["crs_trabajo"],
        mmu_m2=config["validacion_emsr859"]["umm_m2"],
        layers=config["validacion_emsr859"]["inspeccion"]["capas"],
        grade_layer=config["validacion_emsr859"]["inspeccion"]["capa_grado"],
        grade_attr=config["validacion_emsr859"]["inspeccion"]["atributo_grado"],
        ungraded=config["validacion_emsr859"]["inspeccion"]["sin_grado"],
        max_values=config["validacion_emsr859"]["inspeccion"]["max_valores_listados"],
        group_by=config["validacion_emsr859"]["inspeccion"]["agrupar_por"],
    log:
        f"{LOGS}/inspect_emsr859.log",
    benchmark:
        "benchmarks/inspect_emsr859.tsv"
    script:
        "../scripts/01_inspect_emsr859.py"
