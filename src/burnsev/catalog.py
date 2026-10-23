"""Catálogo de incendios de calibración: armonización, filtros y estado dentro/fuera.

Todo el cálculo es puro (recibe y devuelve DataFrames); la lectura y escritura de
archivos vive en ``workflow/scripts/``. Los perímetros CONAF se usan solo para
delimitar espacial y temporalmente, nunca como referencia de exactitud.
"""

import logging
import unicodedata
from collections.abc import Mapping, Sequence
from typing import cast

import geopandas as gpd
import pandas as pd

from burnsev.fires import normalize_region, parse_es_date

logger = logging.getLogger(__name__)

M2_PER_HA = 10_000  # 1 ha = 10 000 m²

CATALOG_COLUMNS = [
    "fire_id",
    "temporada",
    "id_conaf",
    "nombre",
    "comuna",
    "codreg",
    "fecha_inicio",
    "fecha_termino",
    "superficie_ha_conaf",
    "superficie_ha_calc",
    "geometria_valida",
    "estado",
    "motivo",
    "nubosidad_revisada",
    "nubosidad_pre_pct",
    "nubosidad_post_pct",
    "escena_pre",
    "escena_post",
    "fecha_origen",
]

MOTIVO_PENDIENTE = "cumple filtros espaciotemporales; nubosidad pendiente de revisión"


def _fold(text: str) -> str:
    """Minúsculas sin tildes, para comparar nombres de columna."""
    decomposed = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


def harmonize_columns(
    gdf: gpd.GeoDataFrame,
    columns: Mapping[str, Sequence[str]],
    required: Sequence[str],
) -> gpd.GeoDataFrame:
    """Renombra las columnas originales de CONAF a nombres estándar.

    Para cada nombre estándar se usa el primer alias presente en ``gdf`` (sin
    distinguir mayúsculas ni tildes). Los estándar ausentes quedan como ``NA``.

    Args:
        gdf: tabla original de una temporada.
        columns: nombre estándar -> lista ordenada de alias posibles.
        required: nombres estándar que deben existir; si falta alguno, falla.

    Returns:
        GeoDataFrame con las columnas estándar y la geometría.

    Raises:
        ValueError: si falta una columna obligatoria.
    """
    available = {_fold(c): c for c in gdf.columns if c != gdf.geometry.name}
    out = {}
    for standard, aliases in columns.items():
        source = next(
            (available[_fold(a)] for a in aliases if _fold(a) in available), None
        )
        if source is None:
            if standard in required:
                raise ValueError(
                    f"Falta la columna obligatoria '{standard}' "
                    f"(alias probados: {list(aliases)}; columnas: {list(gdf.columns)})"
                )
            out[standard] = pd.Series(pd.NA, index=gdf.index, dtype="object")
        else:
            out[standard] = gdf[source]
    result = gpd.GeoDataFrame(out, geometry=gdf.geometry, crs=gdf.crs)
    return result


def fill_missing_ids(ids: pd.Series) -> pd.Series:
    """Rellena ids ausentes con ``fila-N`` (posición 1-based en el archivo original).

    Algunas temporadas (p. ej. 2024_2025) no traen identificador. El orden de
    lectura de un shapefile es fijo, así que la posición es reproducible.
    Debe llamarse antes de filtrar filas.
    """
    position = pd.Series(range(1, len(ids) + 1), index=ids.index).astype(str)
    as_text = ids.map(
        lambda v: (
            str(int(v)) if isinstance(v, (int, float)) and float(v).is_integer() else v
        )
    )
    return as_text.where(ids.notna(), "fila-" + position).astype(str)


def parse_dates(series: pd.Series) -> pd.Series:
    """Convierte fechas nativas o en texto ('25-ene-2024 15:10') a ``datetime64``.

    El resultado queda sin hora. Los valores que no se pueden interpretar quedan
    como ``NaT``.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.normalize()
    parsed = series.map(lambda x: parse_es_date(str(x)) if pd.notna(x) else pd.NaT)
    return pd.to_datetime(parsed).dt.normalize()


def _name_key(text: object) -> str:
    """Nombre de incendio comparable: sin tildes, mayúsculas y espacios simples."""
    return " ".join(_fold(str(text)).split())


def split_fire_name(name: object) -> tuple[int | None, str]:
    """Separa ``'342 - RAQUI RESERVA'`` en (342, 'raqui reserva')."""
    head, sep, tail = str(name).partition("-")
    if sep and head.strip().isdigit():
        return int(head.strip()), _name_key(tail)
    return None, _name_key(name)


def fill_dates_from_points(
    catalog: pd.DataFrame, points: pd.DataFrame, area_tol_pct: float
) -> pd.DataFrame:
    """Rellena fechas faltantes con el archivo de puntos de inicio de CONAF.

    Solo toca incendios sin ``fecha_inicio``. El emparejamiento exige: número de
    registro (prefijo del nombre del perímetro) igual a ``NUMERO_REG`` del punto,
    mismo nombre (sin tildes ni mayúsculas), un único punto candidato y superficie
    dentro de ``area_tol_pct`` % de la del perímetro. Si algo falla, el incendio
    queda sin fecha (no se infiere). Los puntos solo aportan fechas.

    Args:
        catalog: tabla con ``nombre``, ``superficie_ha_conaf``, ``fecha_inicio`` y
            ``fecha_termino``.
        points: tabla con ``NUMERO_REG``, ``NOM_INCEN``, ``SUPERFICIE``,
            ``INICIO_IN`` y ``EXTINCION``.
        area_tol_pct: diferencia relativa máxima de superficie, en %.

    Returns:
        Catálogo con ``fecha_origen`` = ``perimetro`` o ``puntos_conaf``.
    """
    out = catalog.copy()
    out["fecha_origen"] = "perimetro"
    keys = points.assign(
        _num=pd.to_numeric(points["NUMERO_REG"], errors="coerce"),
        _name=points["NOM_INCEN"].map(_name_key),
    )
    for idx in out.index[out["fecha_inicio"].isna()]:
        number, name = split_fire_name(out.at[idx, "nombre"])
        if number is None:
            continue
        hits = keys[(keys["_num"] == number) & (keys["_name"] == name)]
        if len(hits) != 1:
            logger.warning(
                "%s: %d puntos candidatos; sin fecha", out.at[idx, "fire_id"], len(hits)
            )
            continue
        hit = hits.iloc[0]
        area = float(out.at[idx, "superficie_ha_conaf"])
        diff = 100 * abs(float(hit["SUPERFICIE"]) - area) / area if area else 100.0
        if diff > area_tol_pct:
            logger.warning(
                "%s: superficie del punto difiere %.1f %%; sin fecha",
                out.at[idx, "nombre"],
                diff,
            )
            continue
        out.at[idx, "fecha_inicio"] = parse_dates(pd.Series([hit["INICIO_IN"]])).iloc[0]
        if pd.isna(out.at[idx, "fecha_termino"]):
            out.at[idx, "fecha_termino"] = parse_dates(
                pd.Series([hit["EXTINCION"]])
            ).iloc[0]
        out.at[idx, "fecha_origen"] = "puntos_conaf"
    return out


def in_region(
    codreg: pd.Series,
    region: pd.Series,
    code: int,
    accepted_names: Sequence[str],
) -> pd.Series:
    """Marca los incendios de la región objetivo.

    Criterio principal: código de región (``CODREG``) numérico igual a ``code``.
    Si el código falta, se recurre al nombre de la región normalizado (sin
    prefijo 'R.', tildes ni mojibake) contra ``accepted_names``.
    """
    numeric = cast(pd.Series, pd.to_numeric(codreg, errors="coerce"))
    by_code = numeric == code
    accepted = {normalize_region(n) for n in accepted_names}
    by_name = region.map(
        lambda r: pd.notna(r) and normalize_region(str(r)) in accepted
    ).astype(bool)
    return by_code | (numeric.isna() & by_name)


def compute_area_ha(gdf: gpd.GeoDataFrame, crs: str) -> pd.Series:
    """Superficie en hectáreas, calculada en un CRS proyectado.

    Raises:
        ValueError: si el CRS de trabajo no es proyectado o el de entrada falta.
    """
    if gdf.crs is None:
        raise ValueError("La capa no declara CRS; no se puede calcular el área.")
    projected = gdf.to_crs(crs)
    if projected.crs is None or not projected.crs.is_projected:
        raise ValueError(f"El CRS de trabajo '{crs}' no es proyectado.")
    return projected.geometry.area / M2_PER_HA


def classify_fires(
    df: pd.DataFrame,
    window: tuple[str, str],
    min_area_ha: float,
) -> pd.DataFrame:
    """Asigna ``estado`` (dentro/fuera) y ``motivo`` según los filtros de calibración.

    Motivos de exclusión (se acumulan, separados por '; '): geometría vacía,
    fecha de inicio faltante, fuera de la ventana de calibración y superficie
    menor al mínimo. Un incendio que los cumple todos queda 'dentro' con motivo
    de nubosidad pendiente. Una geometría inválida (p. ej. autointersección) no
    excluye ni se repara: se anota en el motivo para decidir después.

    Args:
        df: tabla con ``fecha_inicio``, ``superficie_ha_calc``, ``geometria_valida``
            y ``geometria_vacia``.
        window: (inicio, fin) inclusivos en formato ISO, ventana de calibración.
        min_area_ha: superficie mínima en hectáreas.
    """
    start, end = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    date = df["fecha_inicio"]
    reasons = pd.DataFrame(
        {
            "geometría vacía": df["geometria_vacia"].astype(bool),
            "fecha de inicio faltante": date.isna(),
            "fuera de la ventana de calibración": date.notna()
            & ((date < start) | (date > end)),
            f"superficie < {min_area_ha:g} ha": df["superficie_ha_calc"] < min_area_ha,
        }
    )
    motivo = reasons.apply(lambda row: "; ".join(row.index[row.to_numpy()]), axis=1)
    out = df.copy()
    excluded = motivo != ""
    out["estado"] = excluded.map(lambda is_out: "fuera" if is_out else "dentro")
    inside_note = (
        df["geometria_valida"]
        .astype(bool)
        .map(
            lambda is_valid: (
                MOTIVO_PENDIENTE
                if is_valid
                else MOTIVO_PENDIENTE + "; geometría inválida sin reparar"
            )
        )
    )
    out["motivo"] = motivo.where(excluded, inside_note)
    return out


def assign_fire_ids(df: pd.DataFrame, prefix: str) -> pd.Series:
    """Identificador estable ``{prefijo}{año_inicio_temporada}-{correlativo:03d}``.

    El correlativo se asigna dentro de cada temporada ordenando por fecha de
    inicio e ``id_conaf``; así agregar otra temporada no cambia los ids existentes.
    """
    ordered = df.assign(_key=df["id_conaf"].astype(str)).sort_values(
        ["temporada", "fecha_inicio", "_key"], na_position="last", kind="stable"
    )
    counter = ordered.groupby("temporada").cumcount() + 1
    year = ordered["temporada"].str[:4]
    ids = prefix + year + "-" + counter.astype(str).str.zfill(3)
    return ids.reindex(df.index)


def _column(df: pd.DataFrame, name: str) -> pd.Series:
    """Columna como ``Series`` (para el verificador de tipos de pandas)."""
    return cast(pd.Series, df[name])


def build_catalog(
    frames: Mapping[str, gpd.GeoDataFrame],
    *,
    columns: Mapping[str, Sequence[str]],
    required: Sequence[str],
    region_code: int,
    region_names: Sequence[str],
    crs: str,
    window: tuple[str, str],
    min_area_ha: float,
    id_prefix: str,
    points: pd.DataFrame | None = None,
    points_area_tol_pct: float = 5.0,
) -> pd.DataFrame:
    """Construye el catálogo de incendios del Biobío con estado dentro/fuera y motivo.

    Args:
        frames: temporada (``2020_2021``) -> capa original leída de CONAF.
        columns, required: diccionario de armonización (``schema_columns.yaml``).
        region_code, region_names: criterio de región (ver :func:`in_region`).
        crs: CRS proyectado para calcular superficies (viene del config).
        window: ventana de calibración (inicio, fin) ISO.
        min_area_ha: superficie mínima en hectáreas.
        id_prefix: prefijo de ``fire_id``.
        points: puntos de inicio de CONAF para completar fechas faltantes
            (ver :func:`fill_dates_from_points`); opcional.
        points_area_tol_pct: tolerancia de superficie para emparejar puntos.

    Returns:
        DataFrame con las columnas de ``CATALOG_COLUMNS`` (sin geometría).
    """
    parts = []
    for season, raw in frames.items():
        table = harmonize_columns(raw, columns, required)
        table["id_conaf"] = fill_missing_ids(_column(table, "id_conaf"))
        keep = in_region(
            _column(table, "codreg"),
            _column(table, "region"),
            region_code,
            region_names,
        )
        logger.info(
            "%s: %d incendios, %d en la región objetivo", season, len(table), keep.sum()
        )
        table = cast(gpd.GeoDataFrame, table[keep].copy())
        if table.empty:
            continue
        table["temporada"] = season
        table["fecha_inicio"] = parse_dates(_column(table, "fecha_inicio"))
        table["fecha_termino"] = parse_dates(_column(table, "fecha_termino"))
        table["geometria_vacia"] = table.geometry.is_empty | table.geometry.isna()
        table["geometria_valida"] = table.geometry.is_valid
        table["superficie_ha_calc"] = compute_area_ha(
            cast(gpd.GeoDataFrame, table), crs
        )
        parts.append(pd.DataFrame(table.drop(columns=table.geometry.name)))

    if not parts:
        raise ValueError("Ninguna temporada aportó incendios de la región objetivo.")

    catalog = pd.concat(parts, ignore_index=True)
    duplicated = catalog.duplicated(["temporada", "id_conaf"], keep=False)
    if duplicated.any():
        logger.warning(
            "%d filas con (temporada, id_conaf) repetido; revisar el inventario",
            duplicated.sum(),
        )
    if points is not None:
        catalog = fill_dates_from_points(catalog, points, points_area_tol_pct)
    else:
        catalog["fecha_origen"] = "perimetro"
    catalog = classify_fires(catalog, window, min_area_ha)
    catalog["fire_id"] = assign_fire_ids(catalog, id_prefix)
    catalog["nubosidad_revisada"] = False
    for col in ("nubosidad_pre_pct", "nubosidad_post_pct", "escena_pre", "escena_post"):
        catalog[col] = pd.NA
    ordered = cast(pd.DataFrame, catalog[CATALOG_COLUMNS])
    return ordered.sort_values("fire_id", ignore_index=True)


def build_fires_table(catalog: pd.DataFrame) -> pd.DataFrame:
    """Tabla de incendios de calibración que quedan dentro (``config/fires.tsv``)."""
    inside = cast(pd.DataFrame, catalog[catalog["estado"] == "dentro"])
    table = cast(
        pd.DataFrame, inside[["fire_id", "fecha_inicio", "fecha_termino"]]
    ).copy()
    table["role"] = "calibracion"
    return table.reset_index(drop=True)


def build_perimeters(
    frames: Mapping[str, gpd.GeoDataFrame],
    catalog: pd.DataFrame,
    *,
    columns: Mapping[str, Sequence[str]],
    required: Sequence[str],
    region_code: int,
    region_names: Sequence[str],
    crs: str,
) -> gpd.GeoDataFrame:
    """Perímetros de los incendios 'dentro' con su ``fire_id`` (sin reparar).

    Repite la armonización y el filtro de región de :func:`build_catalog` (los
    ``id_conaf`` se repiten entre regiones) y une por
    (``temporada``, ``id_conaf``). Los perímetros solo delimitan; no son verdad
    de terreno. Las geometrías inválidas se conservan tal cual.

    Raises:
        ValueError: si algún incendio 'dentro' no encuentra su geometría.
    """
    inside = cast(pd.DataFrame, catalog[catalog["estado"] == "dentro"])
    parts = []
    for season, raw in frames.items():
        table = harmonize_columns(raw, columns, required)
        table["id_conaf"] = fill_missing_ids(_column(table, "id_conaf"))
        table["temporada"] = season
        keep = in_region(
            _column(table, "codreg"),
            _column(table, "region"),
            region_code,
            region_names,
        )
        table = cast(gpd.GeoDataFrame, table[keep])  # mismo filtro que el catálogo
        parts.append(table[["temporada", "id_conaf", table.geometry.name]])
    geoms = cast(pd.DataFrame, pd.concat(parts, ignore_index=True))
    keys = cast(pd.DataFrame, inside[["fire_id", "temporada", "id_conaf"]])
    merged = keys.merge(geoms, on=["temporada", "id_conaf"], how="left")
    missing = merged[merged.geometry.isna()]
    if len(missing) or len(merged) != len(inside):
        raise ValueError(
            f"Perímetros no resueltos o duplicados para: {missing['fire_id'].tolist()}"
        )
    result = gpd.GeoDataFrame(merged[["fire_id"]], geometry=merged.geometry, crs=crs)
    return cast(gpd.GeoDataFrame, result.sort_values("fire_id", ignore_index=True))


def apply_cloud_review(catalog: pd.DataFrame, review: pd.DataFrame) -> pd.DataFrame:
    """Marca cada incendio como ``usable`` o ``excluido`` con su motivo.

    Args:
        catalog: salida de :func:`build_catalog` (``estado`` dentro/fuera).
        review: una fila por incendio 'dentro' con ``fire_id``, ``estado_uso``,
            ``motivo_codigo``, ``escena_pre``, ``escena_post``,
            ``nubosidad_pre_pct`` y ``nubosidad_post_pct``.

    Returns:
        Catálogo con ``estado`` en {usable, excluido}, ``motivo`` legible,
        ``motivo_codigo`` y las columnas de nubosidad rellenas. Los 'fuera'
        pasan a ``excluido`` conservando su motivo. No repara geometrías.

    Raises:
        ValueError: si falta la revisión de algún incendio 'dentro'.
    """
    inside_ids = set(catalog.loc[catalog["estado"] == "dentro", "fire_id"])
    missing = inside_ids - set(review["fire_id"])
    if missing:
        raise ValueError(f"Sin revisión de nubosidad: {sorted(missing)}")
    renamed = cast(
        pd.DataFrame,
        review[
            [
                "fire_id",
                "estado_uso",
                "motivo_codigo",
                "escena_pre",
                "escena_post",
                "nubosidad_pre_pct",
                "nubosidad_post_pct",
            ]
        ],
    ).rename(
        columns={
            "escena_pre": "_escena_pre",
            "escena_post": "_escena_post",
            "nubosidad_pre_pct": "_pre",
            "nubosidad_post_pct": "_post",
        }
    )
    out = catalog.merge(renamed, on="fire_id", how="left")
    reviewed = out["estado_uso"].notna()
    note = (~out["geometria_valida"].astype(bool)).map(
        lambda bad: "; geometría inválida sin reparar" if bad else ""
    )
    out["motivo_codigo"] = out["motivo_codigo"].where(reviewed, out["motivo"])
    out["motivo"] = out["motivo_codigo"].where(~reviewed, out["motivo_codigo"] + note)
    out["estado"] = out["estado_uso"].where(reviewed, "excluido")
    out["nubosidad_revisada"] = reviewed
    for col, src in (
        ("escena_pre", "_escena_pre"),
        ("escena_post", "_escena_post"),
        ("nubosidad_pre_pct", "_pre"),
        ("nubosidad_post_pct", "_post"),
    ):
        out[col] = out[src]
    columns = [*CATALOG_COLUMNS[:13], "motivo_codigo", *CATALOG_COLUMNS[13:]]
    return cast(pd.DataFrame, out[columns])


def summarize_usability(catalog: pd.DataFrame) -> pd.DataFrame:
    """Número de incendios por ``estado`` y ``motivo_codigo`` (usables primero)."""
    sizes = catalog.groupby(["estado", "motivo_codigo"]).size()
    counts = pd.DataFrame({"n": sizes}).reset_index()
    counts["orden"] = (counts["estado"] != "usable").astype(int)
    counts = counts.sort_values(["orden", "n"], ascending=[True, False])
    return counts.drop(columns="orden").reset_index(drop=True)
