"""Pruebas de la revisión de nubosidad con datos sintéticos."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from burnsev.catalog import apply_cloud_review, summarize_usability
from burnsev.clouds import (
    Thresholds,
    decide_usable,
    exploration_slices,
    explore_side,
    pick_scene,
    scl_fractions,
    side_diagnosis,
    slice_dates,
)

BAD = [1, 3, 8, 9, 10]
TH = Thresholds(max_bad_pct=10, min_coverage_pct=95)


def test_scl_fractions_valores_a_mano():
    # 10 píxeles dentro: 1 saturado, 1 sombra, 1 clase 7, 1 sin dato, 6 vegetación.
    scl = np.array([1, 3, 7, 0, 4, 4, 5, 5, 4, 4, 9, 9])
    inside = np.array([True] * 10 + [False] * 2)  # los 2 últimos (clase 9) afuera
    bad, cover = scl_fractions(scl, inside, BAD)
    assert bad == pytest.approx(20.0)  # clase 7 y sin dato no cuentan
    assert cover == pytest.approx(90.0)  # solo el píxel clase 0 sin cobertura


def test_scl_fractions_falla_con_formas_distintas_o_perimetro_vacio():
    with pytest.raises(ValueError, match="Formas distintas"):
        scl_fractions(np.zeros(3), np.ones(4, bool), BAD)
    with pytest.raises(ValueError, match="no contiene"):
        scl_fractions(np.zeros(3), np.zeros(3, bool), BAD)


def test_exploration_slices_sin_traslape_y_recorte():
    assert exploration_slices([10, 20, 30], 30) == [(0, 10), (10, 20), (20, 30)]
    assert exploration_slices([10, 20, 30], 15) == [(0, 10), (10, 15)]
    with pytest.raises(ValueError):
        exploration_slices([20, 10], 30)


def test_slice_dates_pre_y_post():
    anchor = date(2023, 2, 10)
    assert slice_dates(anchor, "pre", (0, 10)) == (date(2023, 1, 31), anchor)
    assert slice_dates(anchor, "pre", (10, 20)) == (
        date(2023, 1, 21),
        date(2023, 1, 31),
    )
    assert slice_dates(anchor, "post", (0, 10)) == (anchor, date(2023, 2, 20))


def _stats(rows):
    return pd.DataFrame(
        rows,
        columns=["scene_id", "fecha", "nubosidad_pct", "cobertura_pct"],
    )


def test_pick_scene_umbral_inclusivo_y_desempate():
    stats = _stats([("a", "2023-01-01", 10.0, 100.0), ("b", "2023-01-02", 10.0, 100.0)])
    stats["offset_dias"] = [5, 2]
    best = pick_scene(stats, TH)
    assert best is not None and best["scene_id"] == "b"  # empate 10 %: la más cercana
    stats.loc[:, "nubosidad_pct"] = 10.01
    assert pick_scene(stats, TH) is None


def test_explore_side_no_repite_y_se_detiene():
    calls = []
    anchor = date(2023, 2, 10)

    def fetch(start, end):
        calls.append((start, end))
        if start <= date(2023, 1, 25) < end:  # escena limpia solo en la 2.ª rebanada
            return _stats([("ok", "2023-01-25", 2.0, 100.0)])
        return (
            _stats([("nube", "2023-02-05", 80.0, 100.0)])
            if len(calls) == 1
            else _stats([])
        )

    slices = exploration_slices([10, 20, 30], 30)
    out = explore_side(fetch, anchor, "pre", slices, TH)
    assert len(calls) == 2  # no consulta la 3.ª rebanada
    assert len({c for c in calls}) == len(calls)  # sin repetir
    assert calls[0][0] == calls[1][1]  # rebanadas contiguas
    assert set(out["scene_id"]) == {"nube", "ok"}
    best = pick_scene(out, TH)
    assert best is not None and best["scene_id"] == "ok"


def test_diagnosticos_y_decision():
    assert side_diagnosis(_stats([]), TH) == "sin_escena"
    assert side_diagnosis(_stats([("a", "x", 50, 100)]), TH) == "nublado"
    assert side_diagnosis(_stats([("a", "x", 0, 50)]), TH) == "cobertura_insuficiente"
    assert side_diagnosis(_stats([("a", "x", 0, 100)]), TH) == "ok"
    assert decide_usable("ok", "ok") == ("usable", "escena_pre_y_post_validas")
    assert decide_usable("nublado", "sin_escena") == (
        "excluido",
        "pre_nublado+sin_escena_post",
    )
    assert decide_usable("ok", "nublado")[0] == "excluido"
    assert decide_usable("ok", "nublado", require_both=False)[0] == "usable"


def test_apply_cloud_review_y_resumen():
    catalog = pd.DataFrame(
        {
            "fire_id": ["f-1", "f-2", "f-3"],
            "temporada": "2022_2023",
            "id_conaf": ["1", "2", "3"],
            "nombre": "x",
            "comuna": "y",
            "codreg": 8,
            "fecha_inicio": "2023-02-01",
            "fecha_termino": "2023-02-10",
            "superficie_ha_conaf": 10.0,
            "superficie_ha_calc": 10.0,
            "geometria_valida": [True, False, True],
            "estado": ["dentro", "dentro", "fuera"],
            "motivo": ["pendiente", "pendiente", "fecha de inicio faltante"],
            "nubosidad_revisada": False,
            "nubosidad_pre_pct": pd.NA,
            "nubosidad_post_pct": pd.NA,
            "escena_pre": pd.NA,
            "escena_post": pd.NA,
        }
    )
    review = pd.DataFrame(
        {
            "fire_id": ["f-1", "f-2"],
            "estado_uso": ["usable", "excluido"],
            "motivo_codigo": [
                "escena_pre_y_post_validas",
                "pre_nublado+sin_escena_post",
            ],
            "escena_pre": ["s1", None],
            "escena_post": ["s2", None],
            "nubosidad_pre_pct": [1.0, None],
            "nubosidad_post_pct": [2.0, None],
        }
    )
    out = apply_cloud_review(catalog, review)
    assert out["estado"].tolist() == ["usable", "excluido", "excluido"]
    assert out.loc[1, "motivo"].endswith("geometría inválida sin reparar")
    assert out.loc[2, "motivo_codigo"] == "fecha de inicio faltante"
    summary = summarize_usability(out)
    assert summary["n"].sum() == 3
    assert summary.iloc[0]["estado"] == "usable"
    with pytest.raises(ValueError, match="Sin revisión"):
        apply_cloud_review(catalog, review.iloc[:1])


def test_perimeter_lonlat_descarta_z_y_pasa_a_4326():
    import geopandas as gpd
    from shapely.geometry import MultiPolygon, Polygon

    from burnsev.gee_scenes import perimeter_lonlat

    ring = [(250000, 5800000, 10), (250500, 5800000, 10), (250500, 5800500, 10)]
    gdf = gpd.GeoDataFrame(geometry=[MultiPolygon([Polygon(ring)])], crs="EPSG:32719")
    assert gdf.geometry.has_z.all()
    geom = perimeter_lonlat(gdf, "EPSG:32719", 0)
    assert not geom.has_z
    lon, lat = geom.representative_point().coords[0]
    assert -75 < lon < -70 and -40 < lat < -35  # Biobío aprox.
