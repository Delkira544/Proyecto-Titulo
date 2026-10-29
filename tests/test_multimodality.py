"""Pruebas de multimodalidad (Silverman calibrado, dip, BIC) con datos sintéticos."""

from typing import Any

import numpy as np
import pandas as pd
import pytest

from burnsev.multimodality import (
    HALL_YORK_COEF,
    analyze_combination,
    build_tasks,
    clip_to_percentiles,
    contingency_active,
    critical_bandwidth,
    decide,
    dip_test,
    fit_gmm_bic,
    hall_york_lambda,
    seed_for,
    silverman_test,
    subsample,
)


def _unimodal(n=3000, seed=1):
    return np.random.default_rng(seed).normal(size=n)


def _bimodal(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    return np.r_[rng.normal(-3, 1, n // 2), rng.normal(3, 1, n // 2)]


def _trimodal(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    return np.r_[
        rng.normal(-6, 1, n // 3), rng.normal(0, 1, n // 3), rng.normal(6, 1, n // 3)
    ]


def test_hall_york_lambda_hand_computed():
    # Ec. (4.1) con la Tabla 2 a mano para alpha = 0,05:
    # num = 0,0001175 - 0,0039979 + 0,0088475 + 0,48971 = 0,4946771
    # den = 0,000125 - 0,0044448 + 0,018081 + 0,42423 = 0,4379912
    assert len(HALL_YORK_COEF) == 7
    assert hall_york_lambda(0.05) == pytest.approx(0.4946771 / 0.4379912, abs=1e-4)
    assert hall_york_lambda(0.01) > hall_york_lambda(0.05) > 1.0


def test_hall_york_lambda_rejects_bad_alpha():
    with pytest.raises(ValueError, match="alpha"):
        hall_york_lambda(1.5)


def test_critical_bandwidth_grows_with_separation():
    near = np.r_[
        np.random.default_rng(2).normal(-1.5, 1, 1500),
        np.random.default_rng(3).normal(1.5, 1, 1500),
    ]
    assert critical_bandwidth(_bimodal()) > critical_bandwidth(near)


def test_silverman_unimodal_not_rejected_bimodal_rejected():
    assert not silverman_test(_unimodal(), 0.05, 200, 1)["reject"]
    assert silverman_test(_bimodal(), 0.05, 200, 1)["reject"]


def test_silverman_constant_series_fails():
    with pytest.raises(ValueError, match="constante"):
        silverman_test(np.ones(100), 0.05, 50, 1)


def test_dip_constant_series_is_zero():
    # Serie con todos los valores iguales: dip 0 (allow_zero del paquete)
    assert dip_test(np.ones(10))[0] == 0.0


def test_dip_rejects_tiny_sample():
    with pytest.raises(ValueError, match="más de 3"):
        dip_test([1.0, 2.0, 5.0])


def test_dip_unimodal_vs_bimodal():
    assert dip_test(_unimodal())[1] > 0.05
    assert dip_test(_bimodal())[1] < 0.05


@pytest.mark.parametrize(
    ("maker", "k"), [(_unimodal, 1), (_bimodal, 2), (_trimodal, 3)]
)
def test_gmm_bic_recovers_components(maker, k):
    out = fit_gmm_bic(maker(), k_max=5, n_init=3, seed=1)
    assert out["k_opt"] == k
    assert len(out["bic"]) == 5
    assert out["delta_bic"] > 0


def test_decide_cases():
    assert decide(True, True) == {
        "veredicto": "multimodal",
        "decision_final": "multimodal",
        "metodo": "otsu_kde",
    }
    unimodal = decide(False, False)
    assert unimodal["veredicto"] == "unimodal"
    assert unimodal["metodo"] == "percentiles"
    # Silverman y dip se contradicen: discordante, decide Silverman (ADR-0019)
    only_dip = decide(False, True)
    assert only_dip["veredicto"] == "discordante"
    assert only_dip["decision_final"] == "unimodal"
    only_sil = decide(True, False)
    assert only_sil["veredicto"] == "discordante"
    assert only_sil["decision_final"] == "multimodal"


def test_contingency_threshold_edge():
    decisions = ["multimodal", "unimodal"] * 2  # proporción 0,5
    assert not contingency_active(decisions, 0.5)  # igual al mínimo: no se activa
    assert contingency_active(decisions, 0.51)
    with pytest.raises(ValueError, match="combinaciones"):
        contingency_active([], 0.5)


def test_clip_and_subsample():
    x = np.arange(1000.0)
    clipped = clip_to_percentiles(x, [10, 90])
    assert clipped.min() >= 99.9 and clipped.max() <= 899.1
    rng = np.random.default_rng(0)
    assert subsample(x, 50, rng).size == 50
    assert subsample(x, 5000, rng).size == 1000


def test_seed_for_is_stable_and_distinct():
    assert seed_for(1, "a", 2) == seed_for(1, "a", 2)
    assert seed_for(1, "a", 2) != seed_for(1, "a", 3)


_KW: dict[str, Any] = {
    "alpha": 0.05,
    "n_sample": 1000,
    "n_rep": 3,
    "n_boot": 50,
    "k_max": 3,
    "n_init": 2,
    "covariance_type": "full",
    "clip_pct": [0.5, 99.5],
    "seed": 7,
}


def test_analyze_combination_reproducible_and_correct():
    a = analyze_combination(_bimodal(4000), **_KW)
    b = analyze_combination(_bimodal(4000), **_KW)
    assert a == b  # misma semilla, mismo resultado
    assert a["decision_final"] == "multimodal"
    assert a["k_bic"] == 2
    assert a["replicas"] == 3
    uni = analyze_combination(_unimodal(4000), **_KW)
    assert uni["metodo"] == "percentiles"


def test_analyze_combination_small_group_single_replicate():
    out = analyze_combination(_bimodal(600), **_KW)
    assert out["replicas"] == 1
    assert out["n_muestra"] == out["n_total"]


def test_build_tasks_levels_and_min_pixels():
    rng = np.random.default_rng(0)
    rows = []
    for fire, n in (("f1", 50), ("f2", 5)):
        rows.append(
            pd.DataFrame(
                {
                    "fire_id": fire,
                    "estrato": "forestal",
                    "zona": "dentro",
                    "dnbr": rng.normal(size=n),
                    "bai": rng.normal(size=n),
                }
            )
        )
    rows.append(
        pd.DataFrame(
            {
                "fire_id": "f1",
                "estrato": "forestal",
                "zona": "fuera",
                "dnbr": [0.0],
                "bai": [0.0],
            }
        )
    )
    px = pd.concat(rows, ignore_index=True)
    common = {
        "indices": ["dnbr", "bai"],
        "strata": ["forestal"],
        "zone": "dentro",
        "base_seed": 1,
        "kwargs": {},
    }
    pool = build_tasks(px, by_fire=False, min_pixels=0, **common)
    assert [t["key"] for t in pool] == [
        {"estrato": "forestal", "indice": "dnbr"},
        {"estrato": "forestal", "indice": "bai"},
    ]
    assert pool[0]["values"].size == 55  # solo zona 'dentro'
    fires = build_tasks(px, by_fire=True, min_pixels=10, **common)
    assert {t["key"]["fire_id"] for t in fires} == {"f1"}  # f2 queda bajo el mínimo
    assert pool[0]["kwargs"]["seed"] != pool[1]["kwargs"]["seed"]
