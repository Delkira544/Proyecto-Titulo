"""Pruebas de extracción de píxeles y estadística descriptiva."""

import numpy as np
import pandas as pd
import pytest

from burnsev.pixel_stats import (
    describe,
    display_range,
    extract_pixels,
    histogram_table,
    summary_table,
)

STRATA = {1: "forestal", 2: "urbano", 3: "otras"}
NODATA = -9999.0


def _rasters():
    # 2x3 píxeles, dos índices
    dnbr = np.array([[0.1, 0.2, NODATA], [0.4, 0.5, 0.6]], dtype="float32")
    rdnbr = dnbr * 2
    rdnbr[0, 2] = NODATA
    indices = np.stack([dnbr, rdnbr])
    estrato = np.array([[1, 1, 1], [3, 0, 2]], dtype="uint8")
    zona = np.array([[1, 2, 1], [1, 1, 2]], dtype="uint8")
    analizable = np.array([[1, 1, 1], [1, 1, 1]], dtype="uint8")
    analizable[1, 1] = 0  # sin catastro
    labels = np.stack([estrato, zona, analizable])
    return indices, labels


def test_describe_a_mano():
    # desviaciones -3,-2,-1,0,6: m2 = 10, m3 = 36 -> g1 = 36 / 10**1.5
    d = describe(np.array([1.0, 2.0, 3.0, 4.0, 10.0]))
    assert d["n"] == 5
    assert d["media"] == pytest.approx(4.0)
    assert d["mediana"] == pytest.approx(3.0)
    assert (d["q1"], d["q3"], d["iqr"]) == pytest.approx((2.0, 4.0, 2.0))
    assert d["asimetria"] == pytest.approx(36 / 10**1.5)
    assert d["desv_est"] == pytest.approx(np.sqrt(10))


def test_describe_ignora_nan_y_vacio():
    assert describe(np.array([1.0, np.nan, 3.0]))["media"] == pytest.approx(2.0)
    vacio = describe(np.array([np.nan]))
    assert vacio["n"] == 0
    assert np.isnan(vacio["media"])


def test_extract_pixels_filtra_y_etiqueta():
    indices, labels = _rasters()
    df = extract_pixels(
        indices, labels, ["dnbr", "rdnbr"], ["estrato", "zona", "analizable"],
        STRATA, NODATA, "bio2020-001",
    )  # fmt: skip
    # quedan (0,0), (0,1), (1,0), (1,2); (0,2) es nodata y (1,1) no analizable
    assert len(df) == 4
    assert df["dnbr"].dtype == np.float32
    assert df["fire_id"].unique().tolist() == ["bio2020-001"]
    fila = df[df["dnbr"].round(1) == 0.2].iloc[0]
    assert (fila["estrato"], fila["zona"]) == ("forestal", "fuera")
    assert df.loc[df["dnbr"].round(1) == 0.6, "estrato"].iloc[0] == "urbano"


def test_extract_pixels_falla_ante_inconsistencias():
    indices, labels = _rasters()
    names = ["estrato", "zona", "analizable"]
    with pytest.raises(ValueError, match="desalineados"):
        extract_pixels(indices[:, :1], labels, ["a", "b"], names, STRATA, NODATA, "x")
    with pytest.raises(ValueError, match="falta la banda"):
        extract_pixels(indices, labels, ["a", "b"], ["estrato", "zona", "otra"],
                       STRATA, NODATA, "x")  # fmt: skip
    with pytest.raises(ValueError, match="sin nombre"):
        extract_pixels(indices, labels, ["a", "b"], names, {1: "forestal"}, NODATA, "x")


def test_summary_table_por_grupo():
    df = pd.DataFrame(
        {
            "estrato": ["forestal"] * 3 + ["otras"] * 2,
            "dnbr": [1.0, 2.0, 3.0, 10.0, 20.0],
        }
    )
    t = summary_table(df, ["dnbr"], ["estrato"])
    assert t.set_index("estrato").loc["forestal", "mediana"] == pytest.approx(2.0)
    assert t.set_index("estrato").loc["otras", "media"] == pytest.approx(15.0)


def test_histograma_y_rango():
    v = np.array([0.0, 0.1, 0.9, 1.0, 5.0])
    h = histogram_table(v, 2, (0.0, 1.0))
    assert h["conteo"].tolist() == [2, 2]  # 5.0 queda fuera; 1.0 entra en el último bin
    assert (h["densidad"] * (h["borde_sup"] - h["borde_inf"])).sum() == pytest.approx(1)
    assert display_range(np.arange(101.0), [10, 90]) == pytest.approx((10.0, 90.0))
    with pytest.raises(ValueError):
        display_range(v, [90, 10])
    with pytest.raises(ValueError):
        histogram_table(v, 0, (0, 1))


def test_reproducible():
    v = np.random.default_rng(1).normal(size=100)
    assert describe(v) == describe(v.copy())
