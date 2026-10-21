import logging
import unicodedata
from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd
from pandas._libs.tslibs.nattype import NaTType

logger = logging.getLogger(__name__)

_DATE_COLUMN_MAP = {
    "FH_INICIO": "FECHA_INI",
    "FH_EXTINC": "FECHA_TER",
}

_MONTHS_ES = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}


def load_fire_poligons(file_path: str | Path) -> gpd.GeoDataFrame | None:
    """Lee una capa de incendios; devuelve ``None`` si la lectura falla."""
    try:
        fire_polygons = gpd.read_file(file_path, encoding="utf-8")
        return fire_polygons
    except Exception as e:
        print(f"Error loading fire polygons: {e}")
        return None


def parse_es_date(date_str: str) -> pd.Timestamp | NaTType:
    """Parse a Spanish-format date string like '25-ene-2024 15:10' -> 2024-01-25."""
    try:
        parts = date_str.strip().split("-")
        day = int(parts[0])
        month = _MONTHS_ES.get(parts[1][:3].lower(), None)
        year = int(parts[2].split()[0])
        return pd.Timestamp(year=year, month=month, day=day)
    except ValueError, IndexError, TypeError:
        return pd.NaT


def _normalize_table(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Normalize the fire polygons table across seasons

    - Uppercases all column names (handles 2021_2022 which uses lowercase)
    - Maps FH_INICIO/FH_EXTINC to FECHA_INI/FECHA_TER (2023_2024)
    - Parses Spanish date strings and keeps only day-month-year
    """
    gdf = gdf.copy()
    gdf.columns = [c.upper() for c in gdf.columns]

    for old_col, new_col in _DATE_COLUMN_MAP.items():
        if old_col in gdf.columns and new_col not in gdf.columns:
            gdf[new_col] = gdf[old_col]

    for col in ["FECHA_INI", "FECHA_TER"]:
        if col in gdf.columns:
            # Si es datetime nativo, solo normalizar (quitar hora)
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].dt.normalize()
            # Si es object (string), parsear con parse_es_date y normalizar
            else:
                gdf[col] = (
                    gdf[col]
                    .apply(lambda x: parse_es_date(str(x)) if pd.notna(x) else pd.NaT)
                    .dt.normalize()
                )

    return gdf


def normalize_region(region: str) -> str:
    """Normalize a region name: remove 'R.' prefix, fix mojibake, strip accents."""
    cleaned = region.strip()
    if cleaned.startswith("R."):
        cleaned = cleaned[2:]

    try:
        cleaned.encode("latin-1")
        cleaned = cleaned.encode("latin-1").decode("utf-8")
    except UnicodeDecodeError, UnicodeEncodeError:
        pass

    normalized = unicodedata.normalize("NFD", cleaned)
    cleaned = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    return cleaned.strip().title()


def filter_by_region(
    gdf: gpd.GeoDataFrame,
    region: str = "Biobío",
) -> gpd.GeoDataFrame:
    """Normalize a table and keep only fires in the specified region."""
    gdf = _normalize_table(gdf)

    if "REGION" not in gdf.columns:
        logger.warning("No REGION column found in the data.")
        return gdf

    target = normalize_region(region)
    mask = gdf["REGION"].apply(lambda r: normalize_region(str(r)) == target)
    return cast(gpd.GeoDataFrame, gdf[mask].copy())


def load_fire_poligons_in_interval(
    start_year: int,
    end_year: int,
    base_path: str,
    region: str | None = None,
) -> dict[int, gpd.GeoDataFrame] | None:
    """
    Load fire polygons for a range of seasons, optionally normalized by region.

    Each loaded table is normalized (column names, dates, regions) before
    filtering by region if provided.
    """
    root = Path(base_path)
    all_polygons: dict[int, gpd.GeoDataFrame] = {}

    for year in range(start_year, end_year + 1):
        file_path = root / f"{year}_{year + 1}" / f"if_magnitud_{year}_{year + 1}.shp"

        fire_polygons = load_fire_poligons(file_path)
        if fire_polygons is None:
            logger.warning("Failed to load fire polygons for year %s.", year)
            continue

        if region is not None:
            fire_polygons = filter_by_region(fire_polygons, region)
        else:
            fire_polygons = _normalize_table(fire_polygons)

        if not fire_polygons.empty:
            all_polygons[year] = fire_polygons
        else:
            logger.warning("No fires after filtering for year %s.", year)

    if not all_polygons:
        logger.warning("No fire polygons found for the specified interval.")
        return None

    return all_polygons
