"""Pruebas de multimodalidad por índice y estrato (HU-01.1, ADR-0009 y ADR-0010).

- Silverman (1981) con la calibración de Hall y York (2001, Método 1): prueba principal.
- Dip de Hartigan y Hartigan (1985): verificación complementaria.
- Mezcla gaussiana elegida por BIC (Fraley y Raftery, 2002): número de componentes.
  La mezcla se usa solo como modelo de densidad, no para clasificar píxeles.

Toda la aleatoriedad llega por una semilla explícita. Los valores de los índices se
manejan en su escala original (dNBR y RdNBR con NBR en [-1, 1]).
"""

import zlib
from collections.abc import Sequence
from typing import Any, cast

import diptest as _diptest
import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.mixture import GaussianMixture

# Coeficientes a1..a7 de la Tabla 2 de Hall y York (2001), ecuación (4.1).
HALL_YORK_COEF = (0.94029, -1.59914, 0.17695, 0.48971, -1.77793, 0.36162, 0.42423)

# Constantes numéricas de la implementación (no son parámetros del análisis).
GRID_SIZE = 2**13  # puntos de la grilla donde se evalúa la densidad kernel
MODE_FLOOR = 1e-10  # densidad relativa bajo la cual se ignora el ruido de la FFT
BISECT_ITER = 30  # iteraciones de la bisección del ancho de banda crítico

FloatArray = NDArray[np.float64]


def hall_york_lambda(alpha: float) -> float:
    """Factor de calibración λα de Hall y York (2001, Método 1, ec. 4.1).

    Parámetros: alpha en (0, 1). Devuelve λα > 1 (≈1,13 para alpha = 0,05).
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha fuera de (0, 1): {alpha}")
    a1, a2, a3, a4, a5, a6, a7 = HALL_YORK_COEF
    num = a1 * alpha**3 + a2 * alpha**2 + a3 * alpha + a4
    den = alpha**3 + a5 * alpha**2 + a6 * alpha + a7
    return float(num / den)


def seed_for(base_seed: int, *key: str | int) -> int:
    """Semilla estable derivada de la semilla base y una clave (sin usar hash())."""
    text = "|".join(str(k) for k in key)
    seq = np.random.SeedSequence([base_seed, zlib.crc32(text.encode())])
    return int(seq.generate_state(1)[0])


def clip_to_percentiles(values: ArrayLike, percentiles: Sequence[float]) -> FloatArray:
    """Conserva los valores entre los percentiles p_bajo y p_alto (en %) de la serie."""
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    low, high = np.percentile(x, list(percentiles))
    return x[(x >= low) & (x <= high)]


def subsample(values: FloatArray, n: int, rng: np.random.Generator) -> FloatArray:
    """Submuestra sin reemplazo de tamaño n; si hay menos datos, devuelve todos."""
    if values.size <= n:
        return values
    return values[rng.choice(values.size, size=n, replace=False)]


class _Grid:
    """Grilla común para estimar la densidad kernel gaussiana por FFT (con relleno)."""

    def __init__(self, x: FloatArray) -> None:
        span = float(x.max() - x.min())
        if span <= 0.0:
            raise ValueError("Serie constante: no hay densidad que estimar")
        self.lo = float(x.min()) - span
        self.hi = float(x.max()) + span
        self.dx = (self.hi - self.lo) / GRID_SIZE
        self.omega2 = (2.0 * np.pi * np.fft.rfftfreq(GRID_SIZE, d=self.dx)) ** 2

    def spectrum(self, x: FloatArray) -> NDArray[np.complex128]:
        idx = np.clip(((x - self.lo) / self.dx).astype(np.int64), 0, GRID_SIZE - 1)
        counts = np.bincount(idx, minlength=GRID_SIZE).astype(np.float64)
        return np.fft.rfft(counts)

    def n_modes(self, spectrum: NDArray[np.complex128], h: float) -> int:
        dens = np.fft.irfft(spectrum * np.exp(-0.5 * self.omega2 * h * h), GRID_SIZE)
        core = dens[1:-1]
        peak = (core > dens[:-2]) & (core > dens[2:]) & (core > MODE_FLOOR * dens.max())
        return int(peak.sum())


def critical_bandwidth(x: FloatArray, grid: _Grid | None = None) -> float:
    """Ancho de banda crítico para una sola moda (Silverman, 1981) por bisección.

    h_crit = ínfimo de h tal que la densidad kernel gaussiana tiene una sola moda.
    """
    g = grid or _Grid(x)
    spec = g.spectrum(x)
    lo, hi = g.dx, g.hi - g.lo
    for _ in range(BISECT_ITER):
        mid = float(np.sqrt(lo * hi))
        if g.n_modes(spec, mid) > 1:
            lo = mid
        else:
            hi = mid
    return hi


def silverman_test(
    values: ArrayLike, alpha: float, n_boot: int, seed: int
) -> dict[str, float | bool]:
    """Prueba de Silverman (1981) calibrada según Hall y York (2001, Método 1).

    H0: la densidad tiene una sola moda. Se remuestrea de la densidad kernel con h_crit,
    reescalada para conservar media y varianza, y se rechaza H0 si la proporción de
    remuestras con más de una moda a ancho λα·h_crit es ≤ alpha. Equivale a la regla
    P(h*_crit / h_crit ≤ λα | X) ≥ 1 − alpha del artículo.

    Parámetros: values (índice, escala original); alpha en (0, 1); n_boot >= 1;
    seed entero. Devuelve h_crit, lambda, p_cal (válido solo para este alpha) y reject.
    """
    x = np.asarray(values, dtype=np.float64)
    grid = _Grid(x)
    h_crit = critical_bandwidth(x, grid)
    lam = hall_york_lambda(alpha)
    rng = np.random.default_rng(seed)
    mean, var = float(x.mean()), float(x.var())
    shrink = 1.0 / np.sqrt(1.0 + h_crit**2 / var)
    multimodal = 0
    for _ in range(n_boot):
        draw = rng.choice(x, size=x.size) + h_crit * rng.standard_normal(x.size)
        y = mean + (draw - mean) * shrink
        if grid.n_modes(grid.spectrum(y), lam * h_crit) > 1:
            multimodal += 1
    p_cal = multimodal / n_boot
    return {"h_crit": h_crit, "lambda": lam, "p_cal": p_cal, "reject": p_cal <= alpha}


def dip_test(values: ArrayLike) -> tuple[float, float]:
    """Dip de Hartigan y Hartigan (1985): (estadístico, p-valor tabulado).

    Implementación del paquete `diptest` (basada en el cálculo de P. M. Hartigan, 1985).
    """
    x = np.asarray(values, dtype=np.float64)
    if x.size <= 3:
        raise ValueError("El dip requiere más de 3 observaciones")
    dip, pval = cast(tuple[float, float], _diptest.diptest(x))
    return float(dip), float(pval)


def fit_gmm_bic(
    values: ArrayLike, k_max: int, n_init: int, seed: int, covariance_type: str = "full"
) -> dict[str, Any]:
    """Elige el número de componentes de una mezcla gaussiana 1D por mínimo BIC.

    Se ajusta sobre la serie estandarizada (el BIC de todos los k cambia en la misma
    constante). Devuelve k_opt, bic (lista, k = 1..k_max) y delta_bic (BIC del segundo
    mejor menos el del mejor).
    """
    x = np.asarray(values, dtype=np.float64)
    z = ((x - x.mean()) / x.std()).reshape(-1, 1)
    bics = []
    for k in range(1, k_max + 1):
        gmm = GaussianMixture(
            n_components=k,
            covariance_type=covariance_type,
            n_init=n_init,
            random_state=seed,
        )
        bics.append(float(gmm.fit(z).bic(z)))
    order = np.argsort(bics)
    return {
        "k_opt": int(order[0]) + 1,
        "bic": bics,
        "delta_bic": float(bics[order[1]] - bics[order[0]])
        if k_max > 1
        else float("nan"),
    }


def decide(silverman_reject: bool, dip_reject: bool) -> dict[str, str]:
    """Veredicto de una combinación (ADR-0009 y ADR-0019).

    Silverman (principal) fija la decisión final; el dip es la verificación
    complementaria. El BIC no interviene: sus componentes no equivalen a modas
    (ADR-0019) y se reporta aparte.

    - 'multimodal' / 'unimodal' si Silverman y el dip coinciden.
    - 'discordante' si se contradicen; la decisión final la mantiene Silverman.
    metodo: 'otsu_kde' si la decisión final es multimodal; si no, 'percentiles'
    (ADR-0010).
    """
    final = "multimodal" if silverman_reject else "unimodal"
    verdict = final if silverman_reject == dip_reject else "discordante"
    return {
        "veredicto": verdict,
        "decision_final": final,
        "metodo": "otsu_kde" if final == "multimodal" else "percentiles",
    }


def contingency_active(final_decisions: Sequence[str], min_proportion: float) -> bool:
    """Criterio de activación de ADR-0010.

    Verdadero si la proporción de combinaciones multimodales es inferior al mínimo.
    """
    if not final_decisions:
        raise ValueError("No hay combinaciones para evaluar")
    share = sum(d == "multimodal" for d in final_decisions) / len(final_decisions)
    return share < min_proportion


def analyze_combination(
    values: ArrayLike,
    *,
    alpha: float,
    n_sample: int,
    n_rep: int,
    n_boot: int,
    k_max: int,
    n_init: int,
    covariance_type: str,
    clip_pct: Sequence[float],
    seed: int,
) -> dict[str, Any]:
    """Aplica Silverman, dip y BIC a una serie y agrega las réplicas de submuestreo.

    Silverman: p mediano y fracción de réplicas que rechazan. Dip: dip y p medianos.
    BIC: k más frecuente entre réplicas (empate: el menor). El rechazo agregado de
    cada prueba usa la mediana del p-valor (≤ alpha).
    """
    x = clip_to_percentiles(values, clip_pct)
    rng = np.random.default_rng(seed)
    reps = 1 if x.size <= n_sample else n_rep
    rows = []
    for r in range(reps):
        sub = subsample(x, n_sample, rng)
        sil = silverman_test(sub, alpha, n_boot, seed_for(seed, "sil", r))
        dip, p_dip = dip_test(sub)
        gmm = fit_gmm_bic(sub, k_max, n_init, seed_for(seed, "gmm", r), covariance_type)
        rows.append(
            (sil["p_cal"], dip, p_dip, gmm["k_opt"], gmm["delta_bic"], sil["h_crit"])
        )
    arr = np.array(rows, dtype=np.float64)
    ks, counts = np.unique(arr[:, 3].astype(int), return_counts=True)
    p_sil, p_dip_med = float(np.median(arr[:, 0])), float(np.median(arr[:, 2]))
    k_bic = int(ks[np.argmax(counts)])
    return {
        "n_total": int(x.size),
        "n_muestra": int(min(x.size, n_sample)),
        "replicas": reps,
        "p_silverman": p_sil,
        "frac_rechazo_silverman": float((arr[:, 0] <= alpha).mean()),
        "h_crit_mediano": float(np.median(arr[:, 5])),
        "dip_mediano": float(np.median(arr[:, 1])),
        "p_dip": p_dip_med,
        "frac_rechazo_dip": float((arr[:, 2] <= alpha).mean()),
        "k_bic": k_bic,
        "frac_k_bic": float(counts.max() / reps),
        "delta_bic_mediano": float(np.nanmedian(arr[:, 4])),
        **decide(p_sil <= alpha, p_dip_med <= alpha),
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    """Ejecuta una combinación (función de nivel de módulo para usar con procesos).

    task: 'key' (columnas identificadoras), 'values' (serie) y 'kwargs'
    (argumentos de analyze_combination).
    """
    return {**task["key"], **analyze_combination(task["values"], **task["kwargs"])}


def build_tasks(
    pixels: Any,
    *,
    indices: Sequence[str],
    strata: Sequence[str],
    zone: str,
    by_fire: bool,
    min_pixels: int,
    base_seed: int,
    kwargs: dict[str, Any],
) -> list[dict[str, Any]]:
    """Arma una tarea por combinación índice-estrato (pool) o incendio-índice-estrato.

    pixels: DataFrame con fire_id, estrato, zona y los índices. En el nivel por incendio
    se omiten las combinaciones con menos de min_pixels píxeles. kwargs se pasa tal cual
    a analyze_combination, añadiendo la semilla derivada de cada clave.
    """
    inside = pixels[pixels["zona"] == zone]
    groups: list[tuple[dict[str, Any], Any]] = []
    for stratum in strata:
        sub = inside[inside["estrato"] == stratum]
        if by_fire:
            for fire_id, part in sub.groupby("fire_id", observed=True):
                groups.append(({"fire_id": str(fire_id), "estrato": stratum}, part))
        else:
            groups.append(({"estrato": stratum}, sub))
    tasks = []
    for key, part in groups:
        if len(part) < min_pixels:
            continue
        for index in indices:
            full = {**key, "indice": index}
            seed = seed_for(base_seed, *full.values())
            tasks.append(
                {
                    "key": full,
                    "values": part[index].to_numpy(dtype=np.float64),
                    "kwargs": {**kwargs, "seed": seed},
                }
            )
    return tasks


def rule_of_thumb_bandwidth(values: ArrayLike) -> float:
    """Ancho de banda gaussiano de la regla práctica de Silverman (1986, ec. 3.31).

    h = 0,9 · min(desviación estándar, IQR / 1,34) · n^(-1/5). Los coeficientes son
    los de la fórmula publicada. Unidades: las del índice.
    """
    x = np.asarray(values, dtype=np.float64)
    q1, q3 = np.percentile(x, [25, 75])
    spread = min(float(x.std(ddof=1)), float(q3 - q1) / 1.34)
    return 0.9 * spread * x.size ** (-1 / 5)


def kde_curve(
    values: ArrayLike, bandwidth: float, n_points: int
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Densidad kernel gaussiana con ancho de banda absoluto y sus modas.

    Devuelve (rejilla, densidad, posiciones de las modas) sobre el rango de los datos.
    """
    from scipy.stats import gaussian_kde

    x = np.asarray(values, dtype=np.float64)
    kde = gaussian_kde(x, bw_method=bandwidth / float(x.std(ddof=1)))
    grid = np.linspace(x.min(), x.max(), n_points)
    dens = kde(grid)
    inner = dens[1:-1]
    peaks = (inner > dens[:-2]) & (inner > dens[2:])
    return grid, dens, grid[1:-1][peaks]
