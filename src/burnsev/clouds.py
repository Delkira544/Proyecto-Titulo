"""Revisión de nubosidad pre/post por incendio, medida dentro del perímetro.

Todo el cálculo es puro. La consulta a Earth Engine se inyecta como una función
(``fetch``), de modo que la lógica de exploración y de decisión se prueba sin red.

La nubosidad se mide con la banda SCL de Sentinel-2 L2A sobre los píxeles del
perímetro, no con ``CLOUDY_PIXEL_PERCENTAGE`` (que describe toda la escena).
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import cast

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SIDES = ("pre", "post")

STATS_COLUMNS = [
    "scene_id",
    "fecha",
    "offset_dias",
    "nubosidad_pct",
    "cobertura_pct",
    "rebanada",
]

# Diagnóstico por lado (valores de ``side_diagnosis``).
OK = "ok"
NO_SCENE = "sin_escena"
CLOUDY = "nublado"
LOW_COVERAGE = "cobertura_insuficiente"


@dataclass(frozen=True)
class Thresholds:
    """Criterios de usabilidad de una escena (vienen de ``config.yaml``)."""

    max_bad_pct: float  # % máximo de píxeles malos en el perímetro, [0, 100]
    min_coverage_pct: float  # % mínimo del perímetro con dato, [0, 100]


def exploration_slices(steps: Sequence[int], max_days: int) -> list[tuple[int, int]]:
    """Rebanadas de días consecutivas y sin traslape: ``[10, 20, 30]`` -> 3 tramos.

    Args:
        steps: límites superiores acumulados, estrictamente crecientes (días).
        max_days: tope de la ventana; los pasos mayores se descartan y el último
            tramo se recorta a ``max_days``.

    Returns:
        Lista de ``(desde, hasta)`` en días, p. ej. ``[(0, 10), (10, 20)]``.

    Raises:
        ValueError: si ``steps`` no es estrictamente creciente o queda vacío.
    """
    if any(b <= a for a, b in zip(steps, steps[1:], strict=False)) or any(
        s <= 0 for s in steps
    ):
        raise ValueError(f"Los pasos deben ser positivos y crecientes: {list(steps)}")
    limits = [s for s in steps if s < max_days] + [max_days]
    limits = sorted(set(limits))
    return list(zip([0, *limits[:-1]], limits, strict=True))


def slice_dates(anchor: date, side: str, days: tuple[int, int]) -> tuple[date, date]:
    """Rango de fechas ``[inicio, fin)`` (fin excluido) de una rebanada.

    Pre: fechas anteriores a ``anchor`` (``fecha_inicio``); el día del inicio no
    entra. Post: desde ``anchor`` (``fecha_termino``) inclusive hacia adelante.
    """
    lo, hi = days
    if side == "pre":
        return anchor - timedelta(days=hi), anchor - timedelta(days=lo)
    if side == "post":
        return anchor + timedelta(days=lo), anchor + timedelta(days=hi)
    raise ValueError(f"side debe ser 'pre' o 'post', no '{side}'")


def scl_fractions(
    scl: np.ndarray,
    inside: np.ndarray,
    bad_classes: Sequence[int],
    nodata_class: int = 0,
) -> tuple[float, float]:
    """Porcentaje de píxeles malos y de cobertura dentro del perímetro.

    Es la definición que Earth Engine replica en el servidor: ambos porcentajes
    se normalizan por **todos** los píxeles del perímetro (``inside``).

    Args:
        scl: clases SCL por píxel (enteros 0-11).
        inside: máscara booleana del perímetro, misma forma que ``scl``.
        bad_classes: clases que cuentan como malas (p. ej. 1, 3, 8, 9, 10).
        nodata_class: clase sin dato; no es mala, solo reduce la cobertura.

    Returns:
        ``(nubosidad_pct, cobertura_pct)``, ambos en [0, 100].

    Raises:
        ValueError: si las formas difieren o el perímetro no tiene píxeles.
    """
    if scl.shape != inside.shape:
        raise ValueError(f"Formas distintas: scl {scl.shape}, inside {inside.shape}")
    total = int(inside.sum())
    if total == 0:
        raise ValueError("El perímetro no contiene píxeles.")
    bad = np.isin(scl, list(bad_classes)) & inside
    valid = (scl != nodata_class) & inside
    return 100 * bad.sum() / total, 100 * valid.sum() / total


def usable_mask(stats: pd.DataFrame, th: Thresholds) -> pd.Series:
    """Escenas que cumplen ambos umbrales (borde inclusivo)."""
    return (stats["nubosidad_pct"] <= th.max_bad_pct) & (
        stats["cobertura_pct"] >= th.min_coverage_pct
    )


def pick_scene(stats: pd.DataFrame, th: Thresholds) -> pd.Series | None:
    """Mejor escena usable: menos nubosidad; empate -> más cercana al incendio.

    Returns:
        Fila elegida, o ``None`` si ninguna cumple.
    """
    ok = cast(pd.DataFrame, stats[usable_mask(stats, th)] if len(stats) else stats)
    if ok.empty:
        return None
    ordered = ok.sort_values(by=["nubosidad_pct", "offset_dias", "scene_id"])
    return ordered.iloc[0]


def side_diagnosis(stats: pd.DataFrame, th: Thresholds) -> str:
    """Por qué un lado (pre o post) quedó como quedó.

    ``ok`` si hay escena usable; ``sin_escena`` si no se encontró ninguna;
    ``nublado`` si alguna tiene cobertura suficiente pero exceso de píxeles malos;
    ``cobertura_insuficiente`` en el resto.
    """
    if stats.empty:
        return NO_SCENE
    if usable_mask(stats, th).any():
        return OK
    if (stats["cobertura_pct"] >= th.min_coverage_pct).any():
        return CLOUDY
    return LOW_COVERAGE


def explore_side(
    fetch: Callable[[date, date], pd.DataFrame],
    anchor: date,
    side: str,
    slices: Sequence[tuple[int, int]],
    th: Thresholds,
) -> pd.DataFrame:
    """Explora rebanadas de la más cercana a la más lejana hasta hallar una usable.

    Cada rebanada se consulta una sola vez y solo por sus días nuevos. Se detiene
    en la primera rebanada con al menos una escena usable.

    Args:
        fetch: ``(inicio, fin_excluido) -> DataFrame`` con ``scene_id``, ``fecha``,
            ``nubosidad_pct`` y ``cobertura_pct`` (una fila por imagen).
        anchor: ``fecha_inicio`` (pre) o ``fecha_termino`` (post).
        side: ``'pre'`` o ``'post'``.
        slices: salida de :func:`exploration_slices`.
        th: umbrales de usabilidad.

    Returns:
        Todas las escenas exploradas (``STATS_COLUMNS``), con la rebanada y los
        días de distancia al ancla.
    """
    parts = []
    for days in slices:
        start, end = slice_dates(anchor, side, days)
        found = fetch(start, end).copy()
        found["rebanada"] = f"{days[0]}-{days[1]}"
        found["offset_dias"] = (
            pd.to_datetime(found["fecha"]).dt.date.map(lambda d: abs((d - anchor).days))
            if len(found)
            else pd.Series(dtype="int64")
        )
        parts.append(found)
        logger.info(
            "%s %s-%s d: %d escenas, %d usables",
            side,
            days[0],
            days[1],
            len(found),
            int(usable_mask(found, th).sum()) if len(found) else 0,
        )
        if len(found) and usable_mask(found, th).any():
            break
    nonempty = [p for p in parts if len(p)]
    if not nonempty:
        return pd.DataFrame(columns=STATS_COLUMNS)
    return cast(pd.DataFrame, pd.concat(nonempty, ignore_index=True)[STATS_COLUMNS])


def decide_usable(pre: str, post: str, require_both: bool = True) -> tuple[str, str]:
    """Estado final (``usable``/``excluido``) y código de motivo.

    Args:
        pre, post: diagnósticos de :func:`side_diagnosis`.
        require_both: si es ``True``, se exigen escena pre y post válidas.

    Returns:
        ``(estado, motivo_codigo)``; los motivos de ambos lados se unen con ``+``
        (p. ej. ``pre_nublado+sin_escena_post``).
    """
    sides = {"pre": pre, "post": post}
    good = [s for s, d in sides.items() if d == OK]
    if (require_both and len(good) == 2) or (not require_both and good):
        return "usable", "escena_pre_y_post_validas" if len(good) == 2 else (
            f"solo_{good[0]}_valida"
        )
    labels = {
        NO_SCENE: lambda s: f"sin_escena_{s}",
        CLOUDY: lambda s: f"{s}_nublado",
        LOW_COVERAGE: lambda s: f"{s}_cobertura_insuficiente",
    }
    reasons = [labels[d](s) for s, d in sides.items() if d != OK]
    return "excluido", "+".join(reasons)
