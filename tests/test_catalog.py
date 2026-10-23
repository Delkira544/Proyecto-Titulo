"""Pruebas de burnsev.catalog con datos sintéticos pequeños."""

from typing import Any

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from burnsev.catalog import (
    MOTIVO_PENDIENTE,
    assign_fire_ids,
    build_catalog,
    build_fires_table,
    build_perimeters,
    classify_fires,
    compute_area_ha,
    fill_missing_ids,
    harmonize_columns,
    in_region,
    parse_dates,
)

COLUMNS = {
    "id_conaf": ["ID", "NUMERO_REG"],
    "fecha_inicio": ["FECHA_INI", "FH_INICIO"],
    "fecha_termino": ["FECHA_TER", "FH_EXTINC"],
    "superficie_ha_conaf": ["SUPERFICIE"],
    "codreg": ["CODREG"],
    "region": ["REGION"],
    "comuna": ["COMUNA"],
    "nombre": ["NOM_INCEN"],
}
REQUIRED = ["id_conaf", "fecha_inicio"]
CRS = "EPSG:32719"


def square(side_m: float, x0: float = 0.0):
    """Cuadrado de ``side_m`` metros: área = side_m**2 / 10 000 ha."""
    return box(x0, 0, x0 + side_m, side_m)


def test_harmonize_ignores_case_and_accents_and_fills_missing():
    gdf = gpd.GeoDataFrame(
        {"id": [1], "fh_inicio": ["25-ene-2024"], "CODREG": ["08"]},
        geometry=[square(100)],
        crs=CRS,
    )
    out = harmonize_columns(gdf, COLUMNS, REQUIRED)
    assert out["id_conaf"].iloc[0] == 1
    assert out["fecha_inicio"].iloc[0] == "25-ene-2024"
    assert pd.isna(out["comuna"].iloc[0])


def test_harmonize_fails_without_required_column():
    gdf = gpd.GeoDataFrame({"ID": [1]}, geometry=[square(100)], crs=CRS)
    with pytest.raises(ValueError, match="fecha_inicio"):
        harmonize_columns(gdf, COLUMNS, REQUIRED)


def test_parse_dates_spanish_strings_and_native():
    text = pd.Series(["25-ene-2024 15:10", None, "basura"])
    parsed = parse_dates(text)
    assert parsed.iloc[0] == pd.Timestamp("2024-01-25")
    assert parsed.iloc[1:].isna().all()
    native = pd.Series(pd.to_datetime(["2021-01-15 10:30"]))
    assert parse_dates(native).iloc[0] == pd.Timestamp("2021-01-15")


def test_in_region_by_code_and_by_name_fallback():
    codreg = pd.Series(["08", "8", "5", None, None])
    region = pd.Series(["x", "x", "Biobío", "R.Biobio", "Maule"])
    mask = in_region(codreg, region, 8, ["biobio"])
    assert mask.tolist() == [True, True, False, True, False]


def test_compute_area_ha_known_value():
    gdf = gpd.GeoDataFrame(geometry=[square(1000)], crs=CRS)  # 1 km² = 100 ha
    assert compute_area_ha(gdf, CRS).iloc[0] == pytest.approx(100.0)


def test_compute_area_requires_projected_crs():
    gdf = gpd.GeoDataFrame(geometry=[square(1)], crs=CRS)
    with pytest.raises(ValueError, match="proyectado"):
        compute_area_ha(gdf, "EPSG:4326")


def test_classify_fires_accumulates_reasons():
    df = pd.DataFrame(
        {
            "fecha_inicio": pd.to_datetime(
                ["2022-01-10", "2019-12-31", None, "2022-01-10"]
            ),
            "superficie_ha_calc": [50.0, 50.0, 50.0, 2.0],
            "geometria_valida": [True, True, True, False],
            "geometria_vacia": [False, False, False, True],
        }
    )
    out = classify_fires(df, ("2020-01-01", "2025-12-31"), 5)
    assert out["estado"].tolist() == ["dentro", "fuera", "fuera", "fuera"]
    assert out["motivo"].iloc[0] == MOTIVO_PENDIENTE
    assert "fuera de la ventana" in out["motivo"].iloc[1]
    assert "fecha de inicio faltante" in out["motivo"].iloc[2]
    assert out["motivo"].iloc[3].count(";") == 1  # vacía y < 5 ha


def test_classify_fires_invalid_geometry_is_flagged_not_excluded():
    df = pd.DataFrame(
        {
            "fecha_inicio": pd.to_datetime(["2022-01-10"]),
            "superficie_ha_calc": [50.0],
            "geometria_valida": [False],
            "geometria_vacia": [False],
        }
    )
    out = classify_fires(df, ("2020-01-01", "2025-12-31"), 5)
    assert out["estado"].iloc[0] == "dentro"
    assert "geometría inválida sin reparar" in out["motivo"].iloc[0]


def test_assign_fire_ids_stable_per_season():
    df = pd.DataFrame(
        {
            "temporada": ["2021_2022", "2020_2021", "2020_2021"],
            "id_conaf": [1, 2, 1],
            "fecha_inicio": pd.to_datetime(["2022-01-01", "2021-02-01", "2021-01-01"]),
        }
    )
    assert assign_fire_ids(df, "bio").tolist() == [
        "bio2021-001",
        "bio2020-002",
        "bio2020-001",
    ]


def _frame(codreg, dates, side_m, region="Biobío"):
    n = len(dates)
    return gpd.GeoDataFrame(
        {
            "ID": range(1, n + 1),
            "FECHA_INI": pd.to_datetime(dates),
            "CODREG": codreg,
            "REGION": [region] * n,
        },
        geometry=[square(s) for s in side_m],
        crs=CRS,
    )


def test_build_catalog_end_to_end_and_fires_table():
    frames = {
        "2020_2021": _frame(["08", "05", "08"], ["2021-01-10"] * 3, [1000, 1000, 100]),
        "2021_2022": _frame(["8"], ["2022-02-01"], [2000]),
    }
    catalog = build_catalog(
        frames,
        columns=COLUMNS,
        required=REQUIRED,
        region_code=8,
        region_names=["biobio"],
        crs=CRS,
        window=("2020-01-01", "2025-12-31"),
        min_area_ha=5,
        id_prefix="bio",
    )
    assert len(catalog) == 3  # la fila de CODREG 05 se descarta
    assert catalog["estado"].value_counts().to_dict() == {"dentro": 2, "fuera": 1}
    small = catalog[catalog["superficie_ha_calc"] < 5].iloc[0]
    assert small["estado"] == "fuera" and "superficie" in small["motivo"]
    fires = build_fires_table(catalog)
    assert sorted(fires["fire_id"]) == ["bio2020-001", "bio2021-001"]
    assert (fires["role"] == "calibracion").all()


def test_build_catalog_is_deterministic():
    frames = {
        "2020_2021": _frame(["8", "8"], ["2021-01-10", "2021-01-05"], [1000, 1000])
    }
    kwargs: dict[str, Any] = dict(
        columns=COLUMNS,
        required=REQUIRED,
        region_code=8,
        region_names=["biobio"],
        crs=CRS,
        window=("2020-01-01", "2025-12-31"),
        min_area_ha=5,
        id_prefix="bio",
    )
    pd.testing.assert_frame_equal(
        build_catalog(frames, **kwargs), build_catalog(frames, **kwargs)
    )


def test_fill_missing_ids_uses_file_position():
    ids = pd.Series([pd.NA, 7.0, pd.NA], dtype="object")
    assert fill_missing_ids(ids).tolist() == ["fila-1", "7", "fila-3"]


def test_build_perimeters_ignora_id_repetido_en_otra_region():
    # El mismo ID aparece en el Biobío y en otra región (pasa en CONAF 2022_2023).
    raw = gpd.GeoDataFrame(
        {
            "ID": [801, 801],
            "FECHA_INI": ["2-feb-2023", "17-feb-2023"],
            "CODREG": ["08", "09"],
            "REGION": ["Biobío", "Araucanía"],
        },
        geometry=[square(1000), square(1000, x0=5000)],
        crs=CRS,
    )
    kwargs: dict[str, Any] = dict(
        columns=COLUMNS, required=REQUIRED, region_code=8, region_names=["biobio"]
    )
    catalog = build_catalog(
        {"2022_2023": raw},
        crs=CRS,
        window=("2020-01-01", "2025-12-31"),
        min_area_ha=5,
        id_prefix="bio",
        **kwargs,
    )
    perimeters = build_perimeters({"2022_2023": raw}, catalog, crs=CRS, **kwargs)
    assert perimeters["fire_id"].tolist() == ["bio2022-001"]
    assert perimeters.geometry.iloc[0].bounds[0] == 0  # la geometría del Biobío


def test_fill_dates_from_points():
    from burnsev.catalog import fill_dates_from_points

    cat = pd.DataFrame(
        {
            "fire_id": ["a", "b", "c"],
            "nombre": ["342 - RAQUI RESERVA", "10 - OTRO", "7 - SIN PUNTO"],
            "superficie_ha_conaf": [351.2, 100.0, 50.0],
            "fecha_inicio": [pd.NaT, pd.NaT, pd.Timestamp("2021-01-01")],
            "fecha_termino": [pd.NaT, pd.NaT, pd.NaT],
        }
    )
    pts = pd.DataFrame(
        {
            "NUMERO_REG": [342.0, 10.0],
            "NOM_INCEN": ["Raqui Reserva", "OTRO"],
            "SUPERFICIE": [350.0, 300.0],  # el segundo difiere más de 5 %
            "INICIO_IN": ["30-dic-2019 01:47", "1-ene-2020 10:00"],
            "EXTINCION": ["8-ene-2020 21:46", "2-ene-2020 10:00"],
        }
    )
    out = fill_dates_from_points(cat, pts, 5.0).set_index("fire_id")
    assert out.loc["a", "fecha_inicio"] == pd.Timestamp("2019-12-30")
    assert out.loc["a", "fecha_termino"] == pd.Timestamp("2020-01-08")
    assert out.loc["a", "fecha_origen"] == "puntos_conaf"
    assert pd.isna(out.loc["b", "fecha_inicio"])  # superficie no coincide
    assert out.loc["c", "fecha_origen"] == "perimetro"  # ya tenía fecha
