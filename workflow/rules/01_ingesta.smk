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
    """Manifiesto de procedencia con sha256 de cada archivo crudo de CONAF."""
    input:
        archivos_crudos_conaf,
    output:
        f"{EXT_META}/manifest.tsv",
    params:
        root=RAW_CONAF,
        sources=config["fuentes_raw"],
    log:
        f"{LOGS}/compute_raw_manifest.log",
    benchmark:
        "benchmarks/compute_raw_manifest.tsv"
    script:
        "../scripts/01_compute_raw_checksums.py"
