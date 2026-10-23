"""Índices espectrales de severidad (funciones puras sobre arreglos NumPy).

Convención de escala: reflectancia en [0, 1] y NBR en [-1, 1] (sin multiplicar
por 1000), por lo que dNBR y RdNBR quedan en esa misma escala (Key & Benson,
2006; Miller & Thode, 2007). Los píxeles sin dato se propagan como NaN.
"""

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float32]


def _f32(x: NDArray) -> Array:
    return np.asarray(x, dtype=np.float32)


def nbr(nir: NDArray, swir2: NDArray) -> Array:
    """NBR = (NIR - SWIR2) / (NIR + SWIR2), en [-1, 1] (Key & Benson, 2006).

    Args:
        nir: reflectancia del infrarrojo cercano, [0, 1].
        swir2: reflectancia del infrarrojo de onda corta 2, [0, 1].

    Returns:
        NBR float32; NaN donde la suma es 0 o algún insumo es NaN.
    """
    nir, swir2 = _f32(nir), _f32(swir2)
    total = nir + swir2
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(total == 0, np.nan, (nir - swir2) / total)
    return _f32(out)


def dnbr(nbr_pre: NDArray, nbr_post: NDArray) -> Array:
    """dNBR = NBR_pre - NBR_post, en la escala del NBR (Key & Benson, 2006)."""
    return _f32(_f32(nbr_pre) - _f32(nbr_post))


def rdnbr(dnbr_: NDArray, nbr_pre: NDArray, eps: float) -> Array:
    """RdNBR = dNBR / sqrt(|NBR_pre|) con NBR en [-1, 1] (Miller & Thode, 2007).

    Args:
        dnbr_: dNBR en [-1, 1] aprox.
        nbr_pre: NBR previo al incendio.
        eps: si |NBR_pre| < eps el resultado es NaN (denominador casi cero).

    Returns:
        RdNBR float32 con NaN donde no es calculable.
    """
    if eps <= 0:
        raise ValueError("eps debe ser > 0")
    d, pre = _f32(dnbr_), _f32(nbr_pre)
    denom = np.sqrt(np.abs(pre))
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(np.abs(pre) < eps, np.nan, d / denom)
    return _f32(out)


def bai(red: NDArray, nir: NDArray, red_ref: float, nir_ref: float) -> Array:
    """BAI = 1 / ((red_ref - rojo)^2 + (nir_ref - nir)^2) (Chuvieco et al., 2002).

    Referencias típicas 0,1 y 0,06 (reflectancia del carbón); vienen del config.
    La fuente aún está [POR VERIFICAR] contra el artículo original.
    """
    red, nir = _f32(red), _f32(nir)
    dist = (red_ref - red) ** 2 + (nir_ref - nir) ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(dist == 0, np.nan, 1.0 / dist)
    return _f32(out)


def mirbi(swir1: NDArray, swir2: NDArray, a: float, b: float, c: float) -> Array:
    """MIRBI = a*SWIR2 - b*SWIR1 + c (Trigg & Flasse, 2001).

    Coeficientes 10; 9,8; 2 desde el config. Fuente [POR VERIFICAR] contra el
    artículo original.
    """
    return _f32(a * _f32(swir2) - b * _f32(swir1) + c)
