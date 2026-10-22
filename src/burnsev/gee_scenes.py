"""Capa fina de Earth Engine para medir nubosidad (SCL) dentro de un perímetro.

Aquí vive todo lo que toca la red. El cálculo de decisión está en
:mod:`burnsev.clouds`. Una consulta = una llamada ``getInfo`` por rebanada de
fechas y por incendio; no se exporta ningún ráster.
"""

import logging
import os
import urllib.request
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import cast

import ee
import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

logger = logging.getLogger(__name__)


def init_ee(project_env: str) -> None:
    """Inicializa Earth Engine con credenciales ya guardadas fuera del repo.

    Raises:
        RuntimeError: si falta la variable de entorno o la autenticación.
    """
    project = os.environ.get(project_env)
    if not project:
        raise RuntimeError(
            f"Falta la variable de entorno {project_env} (proyecto de Earth Engine)."
        )
    try:
        ee.Initialize(project=project)
    except ee.EEException as exc:
        raise RuntimeError(
            "No se pudo inicializar Earth Engine; ejecuta `earthengine authenticate` "
            f"fuera del repositorio. Detalle: {exc}"
        ) from exc


def perimeter_lonlat(
    perimeter: gpd.GeoDataFrame, work_crs: str, simplify_m: float
) -> BaseGeometry:
    """Perímetro unido, simplificado en CRS proyectado y en 2D, en lon/lat (4326).

    La simplificación reduce el tamaño de la petición; la tolerancia es del orden
    del píxel SCL (20 m). Se descarta la coordenada Z porque GEE rechaza el
    GeoJSON 3D (algunos perímetros CONAF la traen).
    """
    projected = perimeter.to_crs(work_crs)
    merged = projected.geometry.union_all()
    if simplify_m > 0:
        merged = merged.simplify(simplify_m, preserve_topology=True)
    lonlat = gpd.GeoSeries([merged], crs=work_crs).to_crs("EPSG:4326").iloc[0]
    return shapely.force_2d(lonlat)


def perimeter_geometry(
    perimeter: gpd.GeoDataFrame, work_crs: str, simplify_m: float
) -> ee.Geometry:
    """Geometría de GEE (bordes planos, ``geodesic=False``) del perímetro."""
    lonlat = perimeter_lonlat(perimeter, work_crs, simplify_m)
    return ee.Geometry(mapping(lonlat), proj="EPSG:4326", geodesic=False)


def _collection(
    collection_id: str, geometry: ee.Geometry, start: date, end: date
) -> ee.ImageCollection:
    """Colección filtrada por fechas (fin excluido) y por el perímetro."""
    return (
        ee.ImageCollection(collection_id)
        .filterDate(start.isoformat(), end.isoformat())
        .filterBounds(geometry)
    )


TILE_SEP = ";"  # separador de teselas en ``scene_id`` (pasada del mismo día)


def _day_mosaic(day: ee.ImageCollection, band: str) -> ee.Image:
    """Mosaico de las teselas de un día; orden fijo por ``system:index``.

    Donde dos teselas se solapan prevalece la última del orden. Es determinista,
    pero no elige el mejor píxel. El sin dato de una tesela lo rellena la otra.
    """
    return day.sort("system:index").select(band).mosaic()


def scene_stats(
    collection_id: str,
    geometry: ee.Geometry,
    start: date,
    end: date,
    bad_classes: Sequence[int],
    scale_m: float,
    tile_scale: float,
) -> pd.DataFrame:
    """Nubosidad y cobertura por fecha de adquisición en ``[start, end)``.

    Las teselas (granules) del mismo día se combinan en un mosaico SCL antes de
    medir, porque un perímetro puede quedar repartido entre dos teselas. Ambos
    porcentajes se normalizan por los píxeles del perímetro (ver
    :func:`burnsev.clouds.scl_fractions`). ``unmask(0)`` hace que el sin dato
    cuente como no malo y como no cubierto.

    Returns:
        DataFrame con ``scene_id`` (teselas del día unidas por ``;``), ``fecha``,
        ``nubosidad_pct`` y ``cobertura_pct`` (vacío, con esas columnas, si no hay
        escenas).
    """
    logger.info(
        "GEE %s %s..%s clases_malas=%s escala=%s m (mosaico por fecha)",
        collection_id,
        start,
        end,
        list(bad_classes),
        scale_m,
    )
    images = _collection(collection_id, geometry, start, end).map(
        lambda img: img.set("dia", img.date().format("YYYY-MM-dd"))
    )

    def per_day(day_str: ee.String) -> ee.Feature:
        day = images.filter(ee.Filter.eq("dia", day_str))
        scl = _day_mosaic(day, "SCL")
        bad = ee.Image.constant(0)
        for cls in bad_classes:
            bad = bad.Or(scl.eq(cls))
        bands = (
            bad.unmask(0).rename("bad").addBands(scl.mask().unmask(0).rename("valid"))
        )
        mean = bands.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            crs=ee.Image(day.first()).select("SCL").projection(),
            scale=scale_m,
            maxPixels=10**9,
            tileScale=tile_scale,
        )
        ids = ee.List(day.sort("system:index").aggregate_array("system:index"))
        return ee.Feature(
            None,
            {
                "scene_id": ids.join(TILE_SEP),
                "fecha": day_str,
                "bad": mean.get("bad"),
                "valid": mean.get("valid"),
            },
        )

    days = ee.List(images.aggregate_array("dia")).distinct()
    info = ee.FeatureCollection(days.map(per_day)).getInfo() or {}
    rows = info.get("features", [])
    columns = ["scene_id", "fecha", "nubosidad_pct", "cobertura_pct"]
    if not rows:
        return pd.DataFrame(columns=columns)
    frame = pd.DataFrame([r["properties"] for r in rows])
    frame["nubosidad_pct"] = 100 * frame["bad"].astype(float)
    frame["cobertura_pct"] = 100 * frame["valid"].astype(float)
    return cast(pd.DataFrame, frame[columns])


def download_quicklook(
    collection_id: str,
    scene_id: str,
    geometry: ee.Geometry,
    dimensions_px: int,
    out_path: Path,
) -> None:
    """Miniatura RGB (B4, B3, B2) con el perímetro en rojo, guardada como PNG.

    ``scene_id`` puede traer varias teselas del mismo día separadas por ``;``;
    se muestran en mosaico. Es solo una ayuda visual (estirado fijo 0-3000); no se
    usa en ningún cálculo.
    """
    ids = scene_id.split(TILE_SEP)
    tiles = ee.ImageCollection(collection_id).filter(
        ee.Filter.inList("system:index", ids)
    )
    rgb = (
        tiles.sort("system:index")
        .select(["B4", "B3", "B2"])
        .mosaic()
        .visualize(bands=["B4", "B3", "B2"], min=0, max=3000)
    )
    outline = (
        ee.Image()
        .byte()
        .paint(ee.FeatureCollection([ee.Feature(geometry)]), 0, 2)
        .visualize(palette=["FF0000"])
    )
    url = (
        ee.ImageCollection([rgb, outline])
        .mosaic()
        .getThumbURL(
            {
                "region": geometry.bounds(),
                "dimensions": dimensions_px,
                "format": "png",
            }
        )
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out_path)  # noqa: S310 (URL emitida por GEE)
