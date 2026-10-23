"""Pruebas de índices, nombres, alineación y mapeo de estratos."""

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Polygon, box

from burnsev.exports import check_alignment, export_name, map_id_uso, tile_bounds
from burnsev.indices import bai, dnbr, mirbi, nbr, rdnbr
from burnsev.strata import (
    analysis_zone,
    class_border,
    repair_invalid_geometries,
    stratum_sufficiency,
)


def test_nbr_dnbr_rdnbr_a_mano():
    # pre: nir 0.4, swir2 0.1 -> 0.6 ; post: nir 0.2, swir2 0.2 -> 0.0
    pre = nbr(np.array([0.4]), np.array([0.1]))
    post = nbr(np.array([0.2]), np.array([0.2]))
    assert pre[0] == pytest.approx(0.6)
    assert post[0] == pytest.approx(0.0)
    d = dnbr(pre, post)
    assert d[0] == pytest.approx(0.6)
    assert rdnbr(d, pre, 0.001)[0] == pytest.approx(0.6 / np.sqrt(0.6))
    assert pre.dtype == np.float32


def test_nodata_y_division_por_cero():
    assert np.isnan(nbr(np.array([0.0]), np.array([0.0]))[0])
    assert np.isnan(nbr(np.array([np.nan]), np.array([0.1]))[0])
    d, pre = np.array([0.5]), np.array([0.0005])
    assert np.isnan(rdnbr(d, pre, 0.001)[0])
    with pytest.raises(ValueError):
        rdnbr(d, pre, 0)


def test_bai_y_mirbi_a_mano():
    # distancia al carbón: (0.1-0.2)^2 + (0.06-0.16)^2 = 0.02 -> BAI 50
    assert bai(np.array([0.2]), np.array([0.16]), 0.1, 0.06)[0] == pytest.approx(50.0)
    assert np.isnan(bai(np.array([0.1]), np.array([0.06]), 0.1, 0.06)[0])
    # 10*0.2 - 9.8*0.1 + 2 = 3.02
    assert mirbi(np.array([0.1]), np.array([0.2]), 10.0, 9.8, 2.0)[0] == pytest.approx(
        3.02
    )


def test_export_name():
    n = export_name("s2l2a", "bio2020-001", "indices", "20210202", "tif")
    assert n == "s2l2a_bio2020-001_indices_20210202.tif"
    with pytest.raises(ValueError):
        export_name("S2", "bio2020-001", "indices", "20210202", "tif")


def test_check_alignment():
    a = {"crs": "EPSG:32719", "transform": (20, 0, 0, 0, -20, 0), "shape": (3, 3)}
    check_alignment(a, dict(a))
    with pytest.raises(ValueError, match="shape"):
        check_alignment(a, {**a, "shape": (3, 4)})
    with pytest.raises(ValueError, match="crs"):
        check_alignment(a, {**a, "crs": "EPSG:32718"})


def test_map_id_uso():
    codes = {"forestal": 1, "urbano": 2, "otras": 3}
    by_id = {"01": "urbano", "04": "forestal", "03": "otras"}
    out = map_id_uso(np.array(["04", "01", "03"]), by_id, codes)
    assert out.tolist() == [1, 2, 3]
    with pytest.raises(KeyError):
        map_id_uso(np.array(["99"]), by_id, codes)


def test_tile_bounds_cubre_sin_traslape_y_alineado():
    # recuadro 95 x 45 m con escala 20 -> 5 x 3 píxeles (alineado hacia afuera)
    tiles = tile_bounds((10.0, 5.0, 105.0, 50.0), 20.0, 4)  # lado 2 px
    assert all(t[0] % 20 == 0 and t[1] % 20 == 0 for t in tiles)
    area = sum((t[2] - t[0]) * (t[3] - t[1]) for t in tiles)
    assert area == (120 - 0) * (60 - 0)  # x: 0..120 (6 px), y: 0..60 (3 px)
    assert all((t[2] - t[0]) / 20 * (t[3] - t[1]) / 20 <= 4 for t in tiles)
    assert len(tiles) == 3 * 2
    one = tile_bounds((0.0, 0.0, 40.0, 40.0), 20.0, 100)
    assert one == [(0.0, 0.0, 40.0, 40.0)]
    with pytest.raises(ValueError):
        tile_bounds((0, 0, 1, 1), 0, 4)


def test_repair_invalid_geometries():
    bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])  # se cruza: inválido
    gdf = gpd.GeoDataFrame(
        {"ID": [7, 8], "ID_USO": ["04", "01"]},
        geometry=[bowtie, box(10, 10, 12, 12)],
        crs=32719,
    )
    fixed, report = repair_invalid_geometries(gdf, "ID", "ID_USO")
    assert fixed.geometry.is_valid.all()
    assert len(report) == 1 and report.loc[0, "id_poligono"] == 7
    assert report.loc[0, "area_despues"] == pytest.approx(2.0)  # dos triángulos de 1
    assert fixed.geometry.iloc[1].equals(gdf.geometry.iloc[1])  # la válida no cambia
    _, none = repair_invalid_geometries(fixed, "ID", "ID_USO")
    assert none.empty


def test_class_border_ancho_un_pixel():
    st = np.array([[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 3, 3], [1, 1, 3, 3]])
    b = class_border(st, 1)
    assert b[0, 0] == False  # noqa: E712 (lejos del cambio de clase)
    assert b[1, 1] and b[2, 1] and b[1, 2] and b[2, 2] and b[3, 2]
    assert not b[0, 3]
    assert not class_border(st, 0).any()
    assert not class_border(np.ones((3, 3), dtype=int), 1).any()


def test_analysis_zone():
    from rasterio.transform import from_origin

    t = from_origin(0, 100, 20, 20)  # 5x5 píxeles de 20 m
    z = analysis_zone(box(40, 40, 60, 60), 20, t, (5, 5))
    assert z[2, 2] == 1  # el píxel central cae dentro del perímetro
    assert z[1, 2] == 2 and z[2, 1] == 2  # vecinos dentro del buffer de 20 m
    assert z[0, 0] == 0


def test_stratum_sufficiency():
    import pandas as pd

    c = pd.DataFrame(
        {
            "fire_id": ["a", "b", "c", "a", "b"],
            "estrato": ["forestal", "forestal", "forestal", "urbano", "urbano"],
            "pixeles": [4000, 2000, 1500, 5000, 10],
        }
    )
    r = stratum_sufficiency(c, 3000, 3, 1000).set_index("estrato")
    assert r.loc["forestal", "pixeles"] == 7500
    assert r.loc["forestal", "incendios_aportantes"] == 3
    assert bool(r.loc["forestal", "suficiente"])
    assert r.loc["urbano", "incendios_aportantes"] == 1
    assert not bool(r.loc["urbano", "suficiente"])
