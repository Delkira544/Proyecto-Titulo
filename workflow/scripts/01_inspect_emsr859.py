"""Spike HU-04.1: inspecciona EMSR859 por AOI y decide el supuesto S2 (ADR-0020).

Escribe los campos y valores de cada capa, los conteos de la capa de grado de
daño, un resumen por capa y las filas de uso de suelo de la tabla resumen de EMS,
más un informe en Markdown con el veredicto. No modifica los datos crudos.
"""

from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd

from burnsev.emsr import (
    count_by,
    find_layer,
    graded_values,
    is_grading_populated,
    land_use_table,
    read_xlsx_sheets,
    share_below_mmu,
    summarize_fields,
)
from burnsev.runlog import setup_logging

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
out = snakemake.output


def md_table(table: pd.DataFrame) -> str:
    """Tabla en Markdown (sin depender de ``tabulate``)."""
    cells = table.map(lambda v: "" if pd.isna(v) else str(v).replace("|", "\\|"))
    lines = [
        "| " + " | ".join(map(str, table.columns)) + " |",
        "|" + "---|" * len(table.columns),
    ]
    lines += ["| " + " | ".join(row) + " |" for row in cells.itertuples(index=False)]
    return "\n".join(lines)


fields, counts, layers, summaries, sources, verdicts = [], [], [], [], [], []
for folder in sorted(Path(params.root).glob("AOI*")):
    aoi = folder.name.removeprefix("AOI")
    for layer in params.layers:
        path = find_layer(folder, layer)
        if path is None:
            layers.append({"aoi": aoi, "capa": layer, "archivo": "(no existe)"})
            continue
        gdf = gpd.read_file(path)
        is_polygon = gdf.geom_type.isin(["Polygon", "MultiPolygon"]).all()
        areas_m2 = gdf.to_crs(params.crs).area if is_polygon else pd.Series(dtype=float)
        layers.append(
            {
                "aoi": aoi,
                "capa": layer,
                "archivo": path.name,
                "n": len(gdf),
                "geometria": ",".join(sorted(set(gdf.geom_type))),
                "crs": gdf.crs.to_string() if gdf.crs else None,
                "invalidas": int((~gdf.geometry.is_valid).sum()),
                "area_ha": round(float(areas_m2.sum()) / 10_000, 2),
                "pct_bajo_umm": round(
                    100 * share_below_mmu(areas_m2, params.mmu_m2), 1
                ),
            }
        )
        summary = summarize_fields(gdf, params.max_values)
        fields.append(summary.assign(aoi=aoi, capa=layer, archivo=path.name))
        if layer == params.grade_layer:
            counts.append(count_by(gdf, params.group_by, params.crs).assign(aoi=aoi))
        logger.info("AOI%s %s: %d entidades", aoi, path.name, len(gdf))

    grade_path = find_layer(folder, params.grade_layer)
    if grade_path is None:
        verdicts.append(
            {"aoi": aoi, "capa_grado": "(no existe)", "grados": "", "poblado": False}
        )
    else:
        values = gpd.read_file(grade_path, columns=[params.grade_attr])[
            params.grade_attr
        ]
        verdicts.append(
            {
                "aoi": aoi,
                "capa_grado": grade_path.name,
                "valores": "; ".join(
                    f"{k}={v}" for k, v in values.value_counts().items()
                ),
                "grados": ", ".join(sorted(graded_values(values, params.ungraded))),
                "poblado": is_grading_populated(values, params.ungraded),
            }
        )

    xlsx = find_layer(folder, "summaryTable", ".xlsx")
    if xlsx is not None:
        table = land_use_table(read_xlsx_sheets(xlsx))
        summaries.append(table.assign(aoi=aoi, archivo=xlsx.name))
    source = find_layer(folder, "source", ".dbf")
    if source is not None:
        table = gpd.read_file(source, ignore_geometry=True)
        sources.append(table[table["eventphase"] == "Post-event"].assign(aoi=aoi))

fields_table = pd.concat(fields, ignore_index=True)
counts_table = pd.concat(counts, ignore_index=True) if counts else pd.DataFrame()
layers_table = pd.DataFrame(layers).astype({"n": "Int64", "invalidas": "Int64"})
summary_table = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
verdict_table = pd.DataFrame(verdicts)
for path in out:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
fields_table.to_csv(out.fields, sep="\t", index=False)
counts_table.to_csv(out.counts, sep="\t", index=False)
layers_table.to_csv(out.layers, sep="\t", index=False)
summary_table.to_csv(out.summary, sep="\t", index=False)

s2_holds = bool(verdict_table["poblado"].any())
scenario = (
    "A (validar contra EMSR859 en el nivel de severidad)"
    if s2_holds
    else "B reducido: EMSR859 solo como referencia quemado / no quemado (ADR-0020)"
)
post = pd.concat(sources, ignore_index=True) if sources else pd.DataFrame()
post_md = md_table(post) if not post.empty else "(sin tabla)"
s2_text = "se cumple" if s2_holds else "no se cumple"
grade_fields = cast(
    pd.DataFrame,
    fields_table[fields_table["capa"] == params.grade_layer][
        ["aoi", "campo", "n_unicos", "valores"]
    ],
)
report = f"""# Spike HU-04.1: grado de daño en EMSR859

Generado por la regla `inspect_emsr859` (no editar a mano).

## Veredicto

- Supuesto S2 (grado de daño en vegetación poblado): **{s2_text}**.
- Criterio: al menos dos grados distintos en `{params.grade_attr}` de
  `{params.grade_layer}`, sin contar {", ".join(params.ungraded)} ni nulos.
- Escenario: **{scenario}**.

{md_table(verdict_table)}

## Capas por AOI

UMM = {params.mmu_m2} m² (metadatos XML de EMSR859). Áreas en {params.crs}.

{md_table(layers_table)}

## Campos de la capa de grado de daño

{md_table(grade_fields)}

## Conteos de la capa de grado de daño

{md_table(counts_table.round(2)) if not counts_table.empty else "(sin capa)"}

## Uso de suelo según la tabla resumen de EMS

Cifras tal como las publica EMS; pueden contradecir la capa vectorial.

{md_table(summary_table.round(2)) if not summary_table.empty else "(sin tabla)"}

## Imágenes post-evento (source.dbf)

{post_md}
"""
Path(out.report).write_text(report, encoding="utf-8")
logger.info("S2 %s; escenario %s", s2_holds, scenario)
