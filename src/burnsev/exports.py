"""Nombres de archivos exportados y comprobación de alineación de rásteres."""

import re
from collections.abc import Mapping

import numpy as np
from numpy.typing import NDArray

NAME_PATTERN = re.compile(r"^[a-z0-9]+_[a-z]+\d{4}-\d{3}_[a-z0-9]+_\d{8}\.[a-z]+$")


def export_name(
    product: str, fire_id: str, variable: str, date_yyyymmdd: str, ext: str
) -> str:
    """``{producto}_{fire_id}_{variable}_{YYYYMMDD}.{ext}`` (CLAUDE.md §8.4).

    Raises:
        ValueError: si el nombre resultante no cumple el patrón.
    """
    name = f"{product}_{fire_id}_{variable}_{date_yyyymmdd}.{ext}"
    if not NAME_PATTERN.match(name):
        raise ValueError(f"Nombre fuera de convención: {name}")
    return name


def check_alignment(a: Mapping, b: Mapping) -> None:
    """Falla si dos rásteres no comparten CRS, transformación y forma.

    Args:
        a, b: mapeos con ``crs`` (str), ``transform`` (tupla de 6) y ``shape``.

    Raises:
        ValueError: ante cualquier diferencia; nunca remuestrea.
    """
    for key in ("crs", "transform", "shape"):
        same = a[key] == b[key] if key == "crs" else tuple(a[key]) == tuple(b[key])
        if not same:
            raise ValueError(f"Rásteres desalineados en '{key}': {a[key]} != {b[key]}")


def map_id_uso(
    id_uso: NDArray, by_id: Mapping[str, str], codes: Mapping[str, int]
) -> NDArray:
    """Convierte códigos ``ID_USO`` del SIT en códigos enteros de estrato.

    Raises:
        KeyError: si hay un ``ID_USO`` ausente en la tabla (no se asigna en silencio).
    """
    out = np.zeros(len(id_uso), dtype=np.uint8)
    for i, value in enumerate(id_uso):
        key = str(value)
        if key not in by_id:
            raise KeyError(f"ID_USO sin estrato asignado: {key!r}")
        out[i] = codes[by_id[key]]
    return out


def tile_bounds(
    bounds: tuple[float, float, float, float],
    scale: float,
    max_pixels: int,
) -> list[tuple[float, float, float, float]]:
    """Divide un recuadro en teselas alineadas a la grilla de ``scale`` metros.

    El recuadro se expande hasta múltiplos de ``scale`` (origen en 0 del CRS) y se
    cubre con teselas cuadradas de a lo más ``max_pixels`` píxeles. Teselas
    contiguas, sin traslape, para unirlas sin remuestrear.

    Args:
        bounds: (minx, miny, maxx, maxy) en el CRS proyectado.
        scale: tamaño de píxel en metros (> 0).
        max_pixels: píxeles máximos por tesela (>= 1).
    """
    if scale <= 0 or max_pixels < 1:
        raise ValueError("scale debe ser > 0 y max_pixels >= 1")
    minx, miny, maxx, maxy = bounds
    x0 = np.floor(minx / scale) * scale
    y0 = np.floor(miny / scale) * scale
    ncols = int(np.ceil((maxx - x0) / scale))
    nrows = int(np.ceil((maxy - y0) / scale))
    side = max(int(np.sqrt(max_pixels)), 1)
    tiles = []
    for r in range(0, nrows, side):
        for c in range(0, ncols, side):
            h, w = min(side, nrows - r), min(side, ncols - c)
            tiles.append(
                (
                    float(x0 + c * scale),
                    float(y0 + r * scale),
                    float(x0 + (c + w) * scale),
                    float(y0 + (r + h) * scale),
                )
            )
    return tiles
