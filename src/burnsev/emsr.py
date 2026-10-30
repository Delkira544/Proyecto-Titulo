"""Producto EMSR859 de Copernicus EMS: inspección y referencia de validación.

Funciones puras (reciben y devuelven tablas o geometrías); la lectura y escritura
de archivos vive en ``workflow/scripts/``. EMSR859 se usa como referencia
**binaria** quemado / no quemado (ADR-0020): su atributo de grado de daño no
gradúa la vegetación, y en Copernicus EMS el *grading* se refiere a bienes
expuestos, no a la severidad de quemado (Copernicus EMS, 2025).
"""

import re
import zipfile
from collections.abc import Collection, Iterable, Mapping, Sequence
from pathlib import Path
from typing import cast
from xml.etree import ElementTree

import geopandas as gpd
import pandas as pd
from shapely.geometry.base import BaseGeometry

from burnsev.catalog import M2_PER_HA

_VERSION_RE = re.compile(r"_v(\d+)$")
_XLSX_NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def find_layer(folder: str | Path, layer: str, suffix: str = ".shp") -> Path | None:
    """Archivo de la capa ``layer`` con la versión más alta dentro de ``folder``.

    Los productos de Copernicus EMS se nombran
    ``EMSR859_AOI01_GRA_PRODUCT_{capa}_v{N}{sufijo}`` y una misma carpeta puede
    mezclar versiones (p. ej. AOI02 trae capas v2 y v3).

    Args:
        folder: carpeta del AOI.
        layer: nombre de la capa (p. ej. ``naturalLandUseA``).
        suffix: extensión, con el punto.

    Returns:
        Ruta del archivo de mayor versión, o ``None`` si la capa no existe.

    Raises:
        ValueError: si dos archivos comparten la versión más alta.
    """
    found: dict[int, list[Path]] = {}
    for path in Path(folder).glob(f"*_{layer}_v*{suffix}"):
        match = _VERSION_RE.search(path.name.removesuffix(suffix))
        if match:
            found.setdefault(int(match.group(1)), []).append(path)
    if not found:
        return None
    top = found[max(found)]
    if len(top) > 1:
        raise ValueError(f"Capa '{layer}' ambigua en {folder}: {sorted(top)}")
    return top[0]


def summarize_fields(table: pd.DataFrame, max_values: int) -> pd.DataFrame:
    """Una fila por campo: tipo, nulos, valores únicos y sus conteos.

    Args:
        table: atributos de la capa (sin geometría o con ella; se ignora).
        max_values: se listan los valores con su conteo solo si hay como mucho
            esta cantidad de valores distintos.

    Returns:
        Columnas ``campo``, ``tipo``, ``n``, ``nulos``, ``n_unicos`` y ``valores``
        (``"valor=conteo; ..."`` o vacío si hay demasiados).
    """
    rows = []
    for column in table.columns:
        if isinstance(table, gpd.GeoDataFrame) and column == table.geometry.name:
            continue
        series = cast(pd.Series, table[column])
        counts = series.value_counts(dropna=False)
        listed = (
            "; ".join(f"{value}={count}" for value, count in counts.items())
            if len(counts) <= max_values
            else ""
        )
        rows.append(
            {
                "campo": column,
                "tipo": str(series.dtype),
                "n": len(series),
                "nulos": int(series.isna().sum()),
                "n_unicos": len(counts),
                "valores": listed,
            }
        )
    return pd.DataFrame(rows)


def count_by(gdf: gpd.GeoDataFrame, columns: Sequence[str], crs: str) -> pd.DataFrame:
    """Número de polígonos y superficie (ha, en ``crs`` proyectado) por grupo."""
    areas = gdf.to_crs(crs).area / M2_PER_HA
    table = pd.DataFrame(gdf[list(columns)]).assign(area_ha=areas.to_numpy())
    grouped = table.groupby(list(columns), dropna=False)
    return grouped.agg(
        n_poligonos=("area_ha", "size"), area_ha=("area_ha", "sum")
    ).reset_index()


def graded_values(values: Iterable[object], ungraded: Collection[str]) -> set[str]:
    """Valores de grado de daño que sí distinguen niveles (sin nulos ni comodines)."""
    return {
        str(value)
        for value in values
        if not pd.isna(value) and str(value) not in ungraded  # type: ignore[arg-type]
    }


def is_grading_populated(values: Iterable[object], ungraded: Collection[str]) -> bool:
    """Criterio del supuesto S2: el atributo gradúa el daño en la vegetación.

    Se exige al menos dos grados distintos, sin contar nulos ni los valores de
    ``ungraded`` (``Affected``, ``Not Applicable``): con un solo grado no se puede
    establecer una correspondencia con varias clases de severidad (ADR-0014).
    """
    return len(graded_values(values, ungraded)) >= 2


def share_below_mmu(areas_m2: pd.Series, mmu_m2: float) -> float:
    """Fracción (0–1) de polígonos más chicos que la unidad mínima de mapeo."""
    if areas_m2.empty:
        return 0.0
    return float((areas_m2 < mmu_m2).mean())


def _cell_text(cell: ElementTree.Element, shared: Sequence[str]) -> str | None:
    value = cell.find("m:v", _XLSX_NS)
    if cell.get("t") == "s" and value is not None and value.text is not None:
        return shared[int(value.text)].strip()
    if cell.get("t") == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(f"{{{_XLSX_NS['m']}}}t"))
    return None if value is None else value.text


def read_xlsx_sheets(path: str | Path) -> dict[str, list[list[str]]]:
    """Lee todas las hojas de un ``.xlsx`` como filas de texto (sin openpyxl).

    Un ``.xlsx`` es un ZIP con XML (ECMA-376); se lee con la biblioteca estándar
    para no agregar una dependencia solo para la tabla resumen de EMS. Las celdas
    vacías se omiten, por lo que las filas no conservan la posición de columna.
    """
    with zipfile.ZipFile(path) as book:
        names = book.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ElementTree.fromstring(book.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", _XLSX_NS):
                shared.append(
                    "".join(t.text or "" for t in item.iter(f"{{{_XLSX_NS['m']}}}t"))
                )
        rels = ElementTree.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        targets = {
            rel.get("Id"): rel.get("Target", "")
            for rel in rels.findall("rel:Relationship", _XLSX_NS)
        }
        workbook = ElementTree.fromstring(book.read("xl/workbook.xml"))
        sheets: dict[str, list[list[str]]] = {}
        for sheet in workbook.iter(f"{{{_XLSX_NS['m']}}}sheet"):
            target = targets[sheet.get(f"{{{_XLSX_NS['r']}}}id")]
            member = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
            root = ElementTree.fromstring(book.read(member))
            rows = []
            for row in root.iter(f"{{{_XLSX_NS['m']}}}row"):
                cells = [_cell_text(c, shared) for c in row.findall("m:c", _XLSX_NS)]
                values = [c for c in cells if c not in (None, "")]
                if values:
                    rows.append(cast(list[str], values))
            sheets[str(sheet.get("name"))] = rows
    return sheets


def land_use_table(sheets: Mapping[str, list[list[str]]]) -> pd.DataFrame:
    """Filas de uso de suelo de la tabla resumen de EMS (hojas ``_naturalLandUseA*``).

    Returns:
        Columnas ``hoja``, ``clase``, ``damage_gra``, ``frecuencia`` y
        ``area_ha`` (tal como las publica EMS; pueden contradecir la capa
        vectorial). Vacía si el libro no tiene esas hojas.
    """
    rows = []
    for name, sheet in sheets.items():
        if "naturalLandUseA" not in name:
            continue
        header = next((r for r in sheet if "class_desc" in r), None)
        if header is None:
            continue
        for row in sheet[sheet.index(header) + 1 :]:
            if len(row) != len(header):
                continue  # filas con celdas vacías (p. ej. sin área) quedan fuera
            record = dict(zip(header, row, strict=True))
            rows.append(
                {
                    "hoja": name,
                    "clase": record["class_desc"],
                    "damage_gra": record["damage_gra"],
                    "frecuencia": float(record["Frequency"]),
                    "area_ha": float(record["Area"]),
                }
            )
    return pd.DataFrame(
        rows, columns=["hoja", "clase", "damage_gra", "frecuencia", "area_ha"]
    )


def select_region(
    regions: gpd.GeoDataFrame, column: str, code: int
) -> gpd.GeoDataFrame:
    """La región cuyo ``column`` vale ``code``; falla si no hay exactamente una."""
    chosen = regions[regions[column].astype(int) == code]
    if len(chosen) != 1:
        raise ValueError(
            f"Se esperaba 1 región con {column}={code} y hay {len(chosen)}"
        )
    return cast(gpd.GeoDataFrame, chosen)


def validation_regions(
    aois: gpd.GeoDataFrame,
    region: BaseGeometry,
    not_analysed: gpd.GeoDataFrame | None,
    crs: str,
) -> gpd.GeoDataFrame:
    """Zona de trabajo de cada incendio de validación: AOI ∩ región − sin analizar.

    Args:
        aois: columnas ``fire_id``, ``aoi`` y la geometría del AOI de EMSR859.
        region: polígono de la región de estudio, en ``crs``.
        not_analysed: zonas que EMS declaró sin analizar (``notAnalysedA`` y
            huellas «Not Analysed - No data»), o ``None``.
        crs: CRS proyectado de trabajo.

    Returns:
        GeoDataFrame con ``fire_id``, ``aoi``, ``area_ha`` y la geometría.

    Raises:
        ValueError: si un AOI queda sin superficie dentro de la región.
    """
    projected = aois.to_crs(crs)
    clipped = projected.geometry.intersection(region)
    if not_analysed is not None and not not_analysed.empty:
        holes = not_analysed.to_crs(crs).geometry.union_all()
        clipped = clipped.difference(holes)
    empty = projected.loc[clipped.is_empty | (clipped.area == 0), "aoi"].tolist()
    if empty:
        raise ValueError(f"AOI sin superficie dentro de la región de estudio: {empty}")
    result = gpd.GeoDataFrame(
        projected[["fire_id", "aoi"]].copy(), geometry=clipped.to_numpy(), crs=crs
    )
    result["area_ha"] = result.area / M2_PER_HA
    return cast(gpd.GeoDataFrame, result.sort_values("fire_id", ignore_index=True))


def burnt_reference(
    burnt: gpd.GeoDataFrame, regions: gpd.GeoDataFrame, mmu_m2: float
) -> gpd.GeoDataFrame:
    """Área quemada de referencia (EMSR859) disuelta y recortada por incendio.

    Une los polígonos de ``observedEventA`` de cada AOI (resuelve los fragmentos
    contiguos más chicos que la unidad mínima de mapeo) y los recorta a la zona
    de trabajo. No elimina fragmentos aislados: eso se decide al pasar a la
    grilla de Sentinel-2 (ADR-0014).

    Args:
        burnt: columnas ``aoi`` y geometría de ``observedEventA`` (cualquier CRS).
        regions: salida de :func:`validation_regions`.
        mmu_m2: unidad mínima de mapeo declarada por EMS, en m².

    Returns:
        Una fila por ``fire_id`` con ``area_ha``, ``n_partes`` y
        ``n_partes_bajo_umm`` (partes que siguen bajo la UMM tras disolver).
    """
    crs = str(regions.crs)
    projected = burnt.to_crs(crs)
    rows = []
    for zone in regions.to_dict("records"):
        own = projected[projected["aoi"] == zone["aoi"]]
        merged = own.geometry.union_all().intersection(zone["geometry"])
        parts = gpd.GeoSeries([merged], crs=crs).explode(index_parts=False)
        parts = cast(gpd.GeoSeries, parts[~parts.is_empty])
        rows.append(
            {
                "fire_id": zone["fire_id"],
                "aoi": zone["aoi"],
                "area_ha": merged.area / M2_PER_HA,
                "n_partes": len(parts),
                "n_partes_bajo_umm": int((parts.area < mmu_m2).sum()),
                "geometry": merged,
            }
        )
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)


def validation_catalog(
    regions: gpd.GeoDataFrame,
    dates: Mapping[str, tuple[str, str]],
    columns: Sequence[str],
    region_code: int,
    season: str,
) -> pd.DataFrame:
    """Catálogo de los incendios de validación con el esquema del de calibración.

    Permite reutilizar la revisión de nubosidad (``apply_cloud_review``) sin
    mezclar roles: el catálogo de validación vive en su propio archivo.

    Args:
        regions: salida de :func:`validation_regions`.
        dates: ``fire_id -> (fecha_inicio, fecha_termino)`` en ISO.
        columns: columnas del catálogo (``catalog.CATALOG_COLUMNS``).
        region_code: código de la región de estudio.
        season: temporada del evento (``AAAA_AAAA``).
    """
    base = {column: None for column in columns}
    rows = []
    for zone in regions.to_dict("records"):
        start, end = dates[zone["fire_id"]]
        rows.append(
            base
            | {
                "fire_id": zone["fire_id"],
                "temporada": season,
                "nombre": f"EMSR859 AOI{zone['aoi']}",
                "codreg": f"{region_code:02d}",
                "fecha_inicio": start,
                "fecha_termino": end,
                "superficie_ha_calc": zone["area_ha"],
                "geometria_valida": bool(zone["geometry"].is_valid),
                "estado": "dentro",
                "motivo": "evento de validación (EMSR859); nubosidad pendiente",
                "nubosidad_revisada": False,
                "fecha_origen": "emsr859",
            }
        )
    return pd.DataFrame(rows, columns=list(columns))
