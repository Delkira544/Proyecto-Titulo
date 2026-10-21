"""Inventario de los shapefiles de incendios: completitud, CRS, columnas, geometrías."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from burnsev.runlog import setup_logging

COMPANIONS = (".shx", ".dbf", ".prj", ".cpg")

logger = setup_logging(snakemake.log[0], dict(snakemake.params))

rows = []
for shp in map(Path, snakemake.input.shp):
    gdf = gpd.read_file(shp)
    missing = [ext for ext in COMPANIONS if not shp.with_suffix(ext).exists()]
    rows.append(
        {
            "temporada": shp.parent.name,
            "archivo": shp.name,
            "n_poligonos": len(gdf),
            "crs": gdf.crs.to_string() if gdf.crs else None,
            "n_geometrias_invalidas": int((~gdf.geometry.is_valid).sum()),
            "n_geometrias_vacias": int(gdf.geometry.is_empty.sum()),
            "faltan_archivos": ",".join(missing),
            "columnas": ",".join(c for c in gdf.columns if c != gdf.geometry.name),
        }
    )
    logger.info("%s: %d polígonos, CRS %s", shp.name, len(gdf), rows[-1]["crs"])

Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(snakemake.output[0], index=False)
