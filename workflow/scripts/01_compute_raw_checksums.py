"""Manifiesto de datos crudos (CLAUDE.md §8.2): archivo, fuente, sha256.

Los campos que no se pueden derivar de los archivos se marcan [POR VERIFICAR]
en lugar de adivinarse.
"""

import hashlib
from pathlib import Path

import pandas as pd

from burnsev.runlog import setup_logging

CHUNK_BYTES = 1024 * 1024  # lectura por bloques de 1 MiB (el SIT pesa >1 GB)
PENDING = "[POR VERIFICAR]"

params = snakemake.params
logger = setup_logging(snakemake.log[0], dict(params))
sources = params.sources  # subcarpeta de raw_conaf -> {fuente, url}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


rows = []
for name in snakemake.input:
    path = Path(name)
    source = sources.get(path.relative_to(params.root).parts[0], {})
    rows.append(
        {
            "archivo": path.as_posix(),
            "fuente": source.get("fuente", PENDING),
            "url": source.get("url", PENDING),
            "fecha_descarga": source.get("fecha_descarga", PENDING),
            "version_producto": source.get("version_producto", PENDING),
            "licencia": source.get("licencia", PENDING),
            "sha256": sha256_of(path),
        }
    )
    logger.info("%s", path)

Path(snakemake.output[0]).parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(snakemake.output[0], sep="\t", index=False)
