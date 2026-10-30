"""Pruebas de burnsev.emsr con datos sintéticos pequeños."""

import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from burnsev.catalog import CATALOG_COLUMNS
from burnsev.emsr import (
    burnt_reference,
    count_by,
    find_layer,
    graded_values,
    is_grading_populated,
    land_use_table,
    read_xlsx_sheets,
    select_region,
    share_below_mmu,
    summarize_fields,
    validation_catalog,
    validation_regions,
)

CRS = "EPSG:32719"
UNGRADED = ["Affected", "Not Applicable"]


def test_find_layer_picks_highest_version(tmp_path: Path):
    for name in ("X_naturalLandUseA_v2.shp", "X_naturalLandUseA_v3.shp"):
        (tmp_path / name).touch()
    assert (
        find_layer(tmp_path, "naturalLandUseA") == tmp_path / "X_naturalLandUseA_v3.shp"
    )


def test_find_layer_missing_returns_none(tmp_path: Path):
    assert find_layer(tmp_path, "naturalLandUseA") is None  # caso AOI03


def test_find_layer_ambiguous_fails(tmp_path: Path):
    for name in ("A_observedEventA_v2.shp", "B_observedEventA_v2.shp"):
        (tmp_path / name).touch()
    with pytest.raises(ValueError, match="ambigua"):
        find_layer(tmp_path, "observedEventA")


def test_grading_single_value_is_not_populated():
    assert not is_grading_populated(["Affected"] * 5, UNGRADED)


def test_grading_ignores_nulls_and_wildcards():
    values = ["Destroyed", None, "Not Applicable", "Damaged", "Affected"]
    assert graded_values(values, UNGRADED) == {"Destroyed", "Damaged"}
    assert is_grading_populated(values, UNGRADED)


def test_grading_one_real_grade_is_not_enough():
    assert not is_grading_populated(["Destroyed", "Destroyed"], UNGRADED)


def test_summarize_fields_lists_only_few_values():
    table = pd.DataFrame({"g": ["a", "a", "b"], "x": [1, 2, 3]})
    out = summarize_fields(table, max_values=2).set_index("campo")
    assert out.loc["g", "valores"] == "a=2; b=1"
    assert out.loc["x", "valores"] == ""  # 3 valores > máximo
    assert out.loc["x", "n_unicos"] == 3


def test_count_by_area_in_hectares():
    gdf = gpd.GeoDataFrame(
        {"k": ["a", "a", "b"]},
        geometry=[box(0, 0, 100, 100), box(200, 0, 300, 100), box(0, 0, 50, 50)],
        crs=CRS,
    )
    out = count_by(gdf, ["k"], CRS).set_index("k")
    assert out.loc["a", "n_poligonos"] == 2
    assert out.loc["a", "area_ha"] == pytest.approx(2.0)  # 2 × 10 000 m²
    assert out.loc["b", "area_ha"] == pytest.approx(0.25)


def test_share_below_mmu():
    assert share_below_mmu(pd.Series([100.0, 300.0, 50.0, 225.0]), 225) == 0.5
    assert share_below_mmu(pd.Series([], dtype=float), 225) == 0.0


def test_select_region_requires_exactly_one():
    regions = gpd.GeoDataFrame({"cod": [8, 16]}, geometry=[box(0, 0, 1, 1)] * 2)
    assert len(select_region(regions, "cod", 8)) == 1
    with pytest.raises(ValueError):
        select_region(regions, "cod", 5)


def _aois(*geoms):
    return gpd.GeoDataFrame(
        {
            "fire_id": [f"emsr2026-00{i}" for i in range(1, len(geoms) + 1)],
            "aoi": [f"0{i}" for i in range(1, len(geoms) + 1)],
        },
        geometry=list(geoms),
        crs=CRS,
    )


def test_validation_regions_keeps_only_inside_part():
    region = box(0, 0, 1000, 1000)
    aois = _aois(box(500, 0, 1500, 1000))  # cruza el límite: queda la mitad
    out = validation_regions(aois, region, None, CRS)
    assert out.loc[0, "area_ha"] == pytest.approx(50.0)  # 500 × 1000 m²


def test_validation_regions_removes_not_analysed():
    region = box(0, 0, 1000, 1000)
    holes = gpd.GeoDataFrame(geometry=[box(0, 0, 100, 1000)], crs=CRS)
    out = validation_regions(_aois(box(0, 0, 1000, 1000)), region, holes, CRS)
    assert out.loc[0, "area_ha"] == pytest.approx(90.0)


def test_validation_regions_outside_fails():
    with pytest.raises(ValueError, match="sin superficie"):
        validation_regions(
            _aois(box(2000, 0, 3000, 1000)), box(0, 0, 1000, 1000), None, CRS
        )


def test_burnt_reference_dissolves_contiguous_fragments():
    zones = validation_regions(
        _aois(box(0, 0, 1000, 1000)), box(0, 0, 1000, 1000), None, CRS
    )
    burnt = gpd.GeoDataFrame(
        {"aoi": ["01"] * 3},
        geometry=[
            box(0, 0, 10, 10),  # 100 m²: bajo la UMM, pero contiguo al siguiente
            box(10, 0, 20, 10),
            box(500, 500, 505, 505),  # 25 m² aislado: sigue bajo la UMM
        ],
        crs=CRS,
    )
    out = burnt_reference(burnt, zones, mmu_m2=150)
    assert out.loc[0, "n_partes"] == 2
    assert out.loc[0, "n_partes_bajo_umm"] == 1
    assert out.loc[0, "area_ha"] == pytest.approx(0.0225)  # (200 + 25) m²


def test_validation_catalog_schema_and_dates():
    zones = validation_regions(
        _aois(box(0, 0, 100, 100)), box(0, 0, 1000, 1000), None, CRS
    )
    out = validation_catalog(
        zones,
        {"emsr2026-001": ("2026-01-16", "2026-01-21")},
        CATALOG_COLUMNS,
        8,
        "2025_2026",
    )
    assert list(out.columns) == CATALOG_COLUMNS
    assert out.loc[0, "estado"] == "dentro"
    assert out.loc[0, "codreg"] == "08"
    assert out.loc[0, "fecha_termino"] == "2026-01-21"


def _write_xlsx(path: Path) -> None:
    """Libro mínimo con una hoja de uso de suelo (cadenas en línea)."""

    def cell(ref, text):
        return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'

    def num(ref, value):
        return f'<c r="{ref}"><v>{value}</v></c>'

    header = ["class_desc", "damage_gra", "Frequency", "Area"]
    cols = "ABCD"
    rows = (
        '<row r="1">'
        + "".join(cell(f"{c}1", h) for c, h in zip(cols, header, strict=True))
        + "</row>"
    )
    rows += (
        f'<row r="2">{cell("A2", "Forests")}{cell("B2", "Affected")}'
        f"{num('C2', 3)}{num('D2', 12.5)}</row>"
    )
    rows += (
        f'<row r="3">{cell("A3", "Shrub")}{cell("B3", "Affected")}{num("C3", 1)}</row>'
    )
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(path, "w") as book:
        book.writestr(
            "xl/workbook.xml",
            f'<workbook xmlns="{ns}" xmlns:r="{rns}"><sheets>'
            '<sheet name="_naturalLandUseA_v2_aff" sheetId="1" r:id="rId1"/>'
            "</sheets></workbook>",
        )
        book.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
        )
        book.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet xmlns="{ns}"><sheetData>{rows}</sheetData></worksheet>',
        )


def test_read_xlsx_and_land_use_table(tmp_path: Path):
    path = tmp_path / "t.xlsx"
    _write_xlsx(path)
    sheets = read_xlsx_sheets(path)
    assert sheets["_naturalLandUseA_v2_aff"][1] == ["Forests", "Affected", "3", "12.5"]
    table = land_use_table(sheets)
    assert len(table) == 1  # la fila sin área queda fuera
    assert table.loc[0, "area_ha"] == pytest.approx(12.5)
