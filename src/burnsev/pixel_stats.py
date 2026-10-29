"""Valores de píxel por incendio, estrato e índice y su estadística descriptiva."""

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from scipy.stats import skew

ZONA_NOMBRES = {1: "dentro", 2: "fuera"}


def extract_pixels(
    indices: NDArray,
    labels: NDArray,
    index_names: Sequence[str],
    label_names: Sequence[str],
    strata_names: Mapping[int, str],
    nodata: float,
    fire_id: str,
) -> pd.DataFrame:
    """Tabla de píxeles analizables de un incendio (una fila por píxel).

    Un píxel entra solo si ``analizable == 1`` (con índice, dentro del catastro,
    en el perímetro o su buffer y fuera de bordes de clase) y ninguno de sus
    índices es ``nodata`` ni NaN.

    Args:
        indices: arreglo (bandas, filas, columnas) con los índices.
        labels: arreglo (bandas, filas, columnas) con ``estrato``, ``zona``,
            ``analizable``.
        index_names: nombre de cada banda de ``indices``.
        label_names: nombre de cada banda de ``labels``.
        strata_names: código de estrato -> nombre.
        nodata: valor sin dato de ``indices``.
        fire_id: identificador del incendio.

    Returns:
        DataFrame con ``fire_id``, ``estrato``, ``zona`` (``dentro``/``fuera``,
        según perímetro o buffer) y una columna float32 por índice.

    Raises:
        ValueError: si las grillas difieren o falta una banda.
    """
    if indices.shape[1:] != labels.shape[1:]:
        raise ValueError(
            f"{fire_id}: rásteres desalineados "
            f"{indices.shape[1:]} != {labels.shape[1:]}"
        )
    if len(index_names) != indices.shape[0] or len(label_names) != labels.shape[0]:
        raise ValueError(f"{fire_id}: nombres de banda no coinciden con los datos")
    lab = dict(zip(label_names, labels, strict=True))
    for needed in ("estrato", "zona", "analizable"):
        if needed not in lab:
            raise ValueError(f"{fire_id}: falta la banda '{needed}'")
    values = dict(zip(index_names, indices, strict=True))
    ok = lab["analizable"] == 1
    for arr in values.values():
        ok &= (arr != nodata) & np.isfinite(arr)
    unknown = set(np.unique(lab["estrato"][ok]).tolist()) - set(strata_names)
    if unknown:
        raise ValueError(f"{fire_id}: códigos de estrato sin nombre: {unknown}")
    unknown_zone = set(np.unique(lab["zona"][ok]).tolist()) - set(ZONA_NOMBRES)
    if unknown_zone:
        raise ValueError(f"{fire_id}: píxeles analizables con zona {unknown_zone}")
    data: dict[str, object] = {
        "fire_id": fire_id,
        "estrato": pd.Series(lab["estrato"][ok]).map(strata_names).to_numpy(),
        "zona": pd.Series(lab["zona"][ok]).map(ZONA_NOMBRES).to_numpy(),
    }
    for name, arr in values.items():
        data[name] = arr[ok].astype("float32")
    return pd.DataFrame(data)


def describe(values: ArrayLike) -> dict[str, float]:
    """Estadísticos descriptivos de un conjunto de valores (ignora NaN).

    La asimetría es el coeficiente de Fisher-Pearson poblacional
    ``g1 = m3 / m2^1.5`` (``scipy.stats.skew`` con ``bias=True``). Los cuantiles
    usan interpolación lineal (valor por defecto de numpy).

    Args:
        values: valores del índice, en su escala original.

    Returns:
        ``n``, ``media``, ``mediana``, ``q1``, ``q3``, ``iqr``, ``asimetria``,
        ``desv_est`` (poblacional), ``min``, ``max``. Todo NaN salvo ``n`` = 0
        si no hay datos.
    """
    v = np.asarray(values, dtype="float64")
    v = v[np.isfinite(v)]
    keys = [
        "media",
        "mediana",
        "q1",
        "q3",
        "iqr",
        "asimetria",
        "desv_est",
        "min",
        "max",
    ]
    if v.size == 0:
        return {"n": 0, **dict.fromkeys(keys, float("nan"))}
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    return {
        "n": int(v.size),
        "media": float(v.mean()),
        "mediana": float(med),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "asimetria": float(skew(v, bias=True)) if v.size > 2 else float("nan"),
        "desv_est": float(v.std()),
        "min": float(v.min()),
        "max": float(v.max()),
    }


def summary_table(
    pixels: pd.DataFrame,
    index_names: Sequence[str],
    group_columns: Sequence[str],
) -> pd.DataFrame:
    """Estadísticos por índice y por cada combinación de ``group_columns``."""
    rows = []
    for keys, group in pixels.groupby(list(group_columns), sort=True, observed=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        for index in index_names:
            rows.append(
                {**dict(zip(group_columns, keys, strict=True)), "indice": index}
                | describe(group[index])
            )
    return pd.DataFrame(rows)


def display_range(
    values: ArrayLike, percentiles: Sequence[float]
) -> tuple[float, float]:
    """Rango [p_bajo, p_alto] de los datos, para fijar los bins del histograma.

    Solo afecta el histograma/figura, no los estadísticos.

    Raises:
        ValueError: si ``percentiles`` no son dos valores crecientes en [0, 100] o
            no hay datos.
    """
    low, high = percentiles
    if not 0 <= low < high <= 100:
        raise ValueError(f"Percentiles inválidos: {percentiles}")
    v = np.asarray(values, dtype="float64")
    v = v[np.isfinite(v)]
    if v.size == 0:
        raise ValueError("Sin datos para calcular el rango")
    lo, hi = np.percentile(v, [low, high])
    return float(lo), float(hi)


def histogram_table(
    values: ArrayLike, bins: int, value_range: tuple[float, float]
) -> pd.DataFrame:
    """Histograma con bins fijos: bordes, conteo y densidad por clase.

    Los valores fuera de ``value_range`` no se cuentan; ``densidad`` se normaliza
    sobre los valores dentro del rango (área = 1).

    Raises:
        ValueError: si ``bins`` < 1 o el rango es vacío.
    """
    if bins < 1:
        raise ValueError("bins debe ser >= 1")
    if not value_range[0] < value_range[1]:
        raise ValueError(f"Rango vacío: {value_range}")
    v = np.asarray(values, dtype="float64")
    v = v[np.isfinite(v)]
    counts, edges = np.histogram(v, bins=bins, range=value_range)
    total = counts.sum()
    width = np.diff(edges)
    density = counts / (total * width) if total else np.zeros(bins)
    return pd.DataFrame(
        {
            "borde_inf": edges[:-1],
            "borde_sup": edges[1:],
            "conteo": counts,
            "densidad": density,
        }
    )
