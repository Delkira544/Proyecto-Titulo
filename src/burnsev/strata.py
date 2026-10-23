"""Etiquetado de estratos CONAF sobre la grilla de un ráster exportado."""

from collections.abc import Mapping
from typing import cast

import geopandas as gpd
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from rasterio.features import rasterize
from rasterio.transform import Affine
from scipy.ndimage import maximum_filter, minimum_filter
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.validation import explain_validity, make_valid

from burnsev.exports import map_id_uso


def repair_invalid_geometries(
    catastro: gpd.GeoDataFrame, id_column: str, uso_column: str
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """Repara con ``make_valid`` solo las geometrías inválidas y lo documenta.

    ``make_valid`` puede devolver una colección; se conservan solo las partes
    poligonales. No toca las geometrías ya válidas.

    Args:
        catastro: capa del SIT.
        id_column: columna con el identificador del polígono (``ID``).
        uso_column: columna con el código de uso (``ID_USO``).

    Returns:
        (catastro con las geometrías reparadas, tabla con una fila por reparación:
        id del polígono en el SIT, ``ID_USO``, motivo, área antes/después en las
        unidades del CRS).

    Raises:
        ValueError: si una reparación deja una geometría vacía o no poligonal.
    """
    invalid = ~catastro.geometry.is_valid
    columns = ["id_poligono", "id_uso", "motivo", "area_antes", "area_despues"]
    if not invalid.any():
        return catastro, pd.DataFrame(columns=columns)
    fixed = catastro.copy()
    rows = []
    for pos in np.flatnonzero(invalid.to_numpy()):
        geom = catastro.geometry.iloc[pos]
        repaired = make_valid(geom)
        parts = [
            g
            for g in getattr(repaired, "geoms", [repaired])
            if g.geom_type in ("Polygon", "MultiPolygon")
        ]
        if not parts:
            raise ValueError(f"Reparación sin polígonos en la fila {pos}")
        result = unary_union(parts)
        fixed.iloc[pos, fixed.columns.get_loc("geometry")] = result  # type: ignore[arg-type]
        rows.append(
            {
                "id_poligono": catastro[id_column].iloc[pos],
                "id_uso": catastro[uso_column].iloc[pos],
                "motivo": explain_validity(geom),
                "area_antes": geom.area,
                "area_despues": result.area,
            }
        )
    return fixed, pd.DataFrame(rows, columns=columns)


def _local_catastro(
    catastro: gpd.GeoDataFrame, transform: Affine, shape: tuple[int, int], crs: str
) -> gpd.GeoDataFrame:
    """Catastro reproyectado y recortado a la grilla; exige geometrías válidas."""
    if catastro.crs is None:
        raise ValueError("El catastro no declara CRS")
    height, width = shape
    bounds = box(*(transform * (0, height)), *(transform * (width, 0)))
    projected = catastro.to_crs(crs)
    local = cast(gpd.GeoDataFrame, projected.loc[projected.intersects(bounds)])
    if not local.geometry.is_valid.all():
        raise ValueError("Hay geometrías inválidas; repáralas antes de rasterizar")
    return local


def rasterize_id_uso(
    catastro: gpd.GeoDataFrame,
    id_column: str,
    codes: Mapping[str, int],
    transform: Affine,
    shape: tuple[int, int],
    crs: str,
) -> NDArray[np.uint8]:
    """Ráster del código de ``ID_USO`` (0 = sin catastro) sobre la grilla dada.

    Raises:
        KeyError: si un ``ID_USO`` no está en ``codes``.
    """
    local = _local_catastro(catastro, transform, shape, crs)
    if local.empty:
        return np.zeros(shape, dtype=np.uint8)
    values = []
    for value in local[id_column].to_numpy():
        key = str(value)
        if key not in codes:
            raise KeyError(f"ID_USO sin código: {key!r}")
        values.append(codes[key])
    return rasterize(
        zip(local.geometry, values, strict=True),
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype="uint8",
    )


def analysis_zone(
    perimeter: BaseGeometry,
    buffer_m: float,
    transform: Affine,
    shape: tuple[int, int],
) -> NDArray[np.uint8]:
    """Zona por píxel: 1 = dentro del perímetro, 2 = en el buffer, 0 = fuera.

    El perímetro y la geometría con buffer deben estar en el CRS de la grilla.
    Se usa el centro del píxel (``all_touched=False``).
    """
    if buffer_m < 0:
        raise ValueError("buffer_m debe ser >= 0")
    outer = rasterize(
        [(perimeter.buffer(buffer_m), 2)],
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype="uint8",
    )
    inner = rasterize(
        [(perimeter, 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8"
    )
    return np.where(inner == 1, 1, outer).astype(np.uint8)


def class_border(strata: NDArray, width_px: int) -> NDArray[np.bool_]:
    """Píxeles a menos de ``width_px`` píxeles de otra clase (buffer de exclusión).

    Un píxel es de borde si en su ventana de (2*width_px + 1) de lado hay más de
    un valor de clase distinto. Mitiga el efecto de píxeles mixtos. Con
    ``width_px = 0`` ningún píxel se marca.
    """
    if width_px < 0:
        raise ValueError("width_px debe ser >= 0")
    if width_px == 0:
        return np.zeros(strata.shape, dtype=bool)
    size = 2 * width_px + 1
    return maximum_filter(strata, size=size, mode="nearest") != minimum_filter(
        strata, size=size, mode="nearest"
    )


def stratum_sufficiency(
    counts: pd.DataFrame, min_pixels: int, min_fires: int, min_pixels_per_fire: int
) -> pd.DataFrame:
    """Suficiencia por estrato a partir de píxeles analizables por incendio.

    Args:
        counts: columnas ``fire_id``, ``estrato``, ``pixeles`` (analizables, en el
            perímetro y fuera de bordes).
        min_pixels: píxeles agrupados mínimos del estrato.
        min_fires: incendios aportantes mínimos.
        min_pixels_per_fire: píxeles que debe tener un incendio para contar.

    Returns:
        Una fila por estrato: píxeles, incendios aportantes, mayor aporte (%) y
        ``suficiente`` (``True`` solo si cumple píxeles e incendios).
    """
    rows = []
    for name, group in counts.groupby("estrato"):
        total = int(group["pixeles"].to_numpy().sum())
        contributors = int((group["pixeles"] >= min_pixels_per_fire).sum())
        top = 100 * float(group["pixeles"].to_numpy().max()) / total if total else 0.0
        rows.append(
            {
                "estrato": name,
                "pixeles": total,
                "incendios_aportantes": contributors,
                "mayor_aporte_pct": round(float(top), 1),
                "suficiente": total >= min_pixels and contributors >= min_fires,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "estrato",
            "pixeles",
            "incendios_aportantes",
            "mayor_aporte_pct",
            "suficiente",
        ],
    )


def rasterize_strata(
    catastro: gpd.GeoDataFrame,
    id_column: str,
    by_id: Mapping[str, str],
    codes: Mapping[str, int],
    transform: Affine,
    shape: tuple[int, int],
    crs: str,
) -> NDArray[np.uint8]:
    """Ráster de estratos (0 = sin catastro) sobre la grilla dada.

    El catastro se reproyecta de forma explícita al CRS de la grilla y se recorta a
    su extensión. Exige geometrías válidas (ver ``repair_invalid_geometries``).

    Raises:
        KeyError: si un ``ID_USO`` del recorte no tiene estrato asignado.
        ValueError: si el catastro no declara CRS.
    """
    local = _local_catastro(catastro, transform, shape, crs)
    if local.empty:
        return np.zeros(shape, dtype=np.uint8)
    values = map_id_uso(local[id_column].to_numpy(), by_id, codes)
    shapes = zip(local.geometry, values.tolist(), strict=True)
    return rasterize(
        shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype="uint8",
        all_touched=False,
    )
