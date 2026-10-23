"""Composición S2 L2A y exportación de índices de severidad desde Earth Engine.

La colección es ``S2_SR_HARMONIZED`` (ADR-0004): ya compensa el desplazamiento
radiométrico de las escenas con baseline >= 04.00, por lo que aquí NO se vuelve a
restar; solo se aplica la escala de reflectancia y se registra el baseline.
"""

import logging
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path

import ee
import pandas as pd

from burnsev.gee_scenes import TILE_SEP

logger = logging.getLogger(__name__)


def scene_composite(
    collection_id: str,
    scene_id: str,
    bands: Mapping[str, str],
    bad_classes: Sequence[int],
    scale: float,
) -> ee.Image:
    """Mosaico de las teselas de una escena, enmascarado por SCL y en [0, 1].

    Args:
        scene_id: ``system:index`` de las teselas del día unidos por ``;``.
        bands: nombres de banda por rol (rojo, nir, swir1, swir2).
        bad_classes: clases SCL a enmascarar.
        scale: factor de escala (DN -> reflectancia).
    """
    ids = scene_id.split(TILE_SEP)
    tiles = (
        ee.ImageCollection(collection_id)
        .filter(ee.Filter.inList("system:index", ids))
        .sort("system:index")
    )
    mosaic = tiles.select([*bands.values(), "SCL"]).mosaic()
    bad = ee.Image.constant(0)
    for cls in bad_classes:
        bad = bad.Or(mosaic.select("SCL").eq(cls))
    refl = mosaic.select(list(bands.values())).multiply(scale)
    renamed = refl.rename(list(bands.keys()))
    return renamed.updateMask(bad.Not())


def scene_baselines(collection_id: str, scene_id: str) -> pd.DataFrame:
    """Baseline de procesamiento y fecha de cada tesela (evidencia de la corrección)."""
    ids = scene_id.split(TILE_SEP)
    coll = ee.ImageCollection(collection_id).filter(
        ee.Filter.inList("system:index", ids)
    )
    info = ee.FeatureCollection(
        coll.map(
            lambda img: ee.Feature(
                None,
                {
                    "tesela": img.get("system:index"),
                    "baseline": img.get("PROCESSING_BASELINE"),
                    "fecha": img.date().format("YYYY-MM-dd"),
                },
            )
        )
    ).getInfo()
    rows = [f["properties"] for f in (info or {}).get("features", [])]
    return pd.DataFrame(rows, columns=["tesela", "baseline", "fecha"])


def severity_indices(
    pre: ee.Image,
    post: ee.Image,
    bai_ref: Mapping[str, float],
    mirbi_coef: Mapping[str, float],
    rdnbr_eps: float,
) -> ee.Image:
    """Bandas dnbr, rdnbr, bai, mirbi (mismas fórmulas que :mod:`burnsev.indices`).

    BAI y MIRBI se calculan sobre la escena post (``bai_mirbi_escena: post``).
    """
    nbr_pre = pre.normalizedDifference(["nir", "swir2"])
    nbr_post = post.normalizedDifference(["nir", "swir2"])
    dnbr = nbr_pre.subtract(nbr_post)
    rdnbr = dnbr.divide(nbr_pre.abs().sqrt()).updateMask(nbr_pre.abs().gte(rdnbr_eps))
    bai = post.expression(
        "1 / ((r0 - red) ** 2 + (n0 - nir) ** 2)",
        {
            "r0": bai_ref["rojo_ref"],
            "n0": bai_ref["nir_ref"],
            "red": post.select("rojo"),
            "nir": post.select("nir"),
        },
    )
    mirbi = post.expression(
        "a * s2 - b * s1 + c",
        {
            "a": mirbi_coef["a"],
            "b": mirbi_coef["b"],
            "c": mirbi_coef["c"],
            "s1": post.select("swir1"),
            "s2": post.select("swir2"),
        },
    )
    return ee.Image.cat(
        [
            dnbr.rename("dnbr"),
            rdnbr.rename("rdnbr"),
            bai.rename("bai"),
            mirbi.rename("mirbi"),
        ]
    ).toFloat()


def download_geotiff_tile(
    image: ee.Image,
    tile: tuple[float, float, float, float],
    crs: str,
    scale: float,
    out_path: Path,
) -> None:
    """Descarga una tesela alineada a la grilla (``crs_transform`` explícito).

    Falla si GEE rechaza la petición (por ejemplo, por superar 32 MB).
    """
    minx, miny, maxx, maxy = tile
    region = ee.Geometry.Rectangle(
        [minx, miny, maxx, maxy], proj=crs, geodesic=False, evenOdd=True
    )
    url = image.getDownloadURL(
        {
            "region": region,
            "crs": crs,
            "crs_transform": [scale, 0, minx, 0, -scale, maxy],
            "format": "GEO_TIFF",
            "filePerBand": False,
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out_path)  # noqa: S310 (URL emitida por GEE)
