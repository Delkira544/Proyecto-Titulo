"""Verifica que el entorno instalado coincide con ``uv.lock``."""

import argparse
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

# Bibliotecas que deben importarse sin error (paquetes previstos en CLAUDE.md §5).
KEY_IMPORTS = (
    "numpy",
    "scipy",
    "pandas",
    "geopandas",
    "shapely",
    "pyproj",
    "rasterio",
    "skimage",
    "sklearn",
    "matplotlib",
    "ee",
    "snakemake",
    "yaml",
    "pytest",
)


def find_sync_problems() -> list[str]:
    """Comprueba con ``uv sync --locked --check`` que el entorno coincide con uv.lock.

    uv evalúa los marcadores de plataforma del lock (paquetes solo de Windows,
    por ejemplo), cosa que una lectura directa del TOML no haría.
    """
    result = subprocess.run(
        ["uv", "sync", "--locked", "--check"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return []
    return [f"uv sync --check: {result.stderr.strip() or result.stdout.strip()}"]


def find_import_errors(modules: tuple[str, ...] = KEY_IMPORTS) -> list[str]:
    """Módulos clave que no se pueden importar."""
    errors = []
    for module in modules:
        try:
            __import__(module)
        except Exception as exc:  # se informa; no se silencia
            errors.append(f"{module}: {type(exc).__name__}: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    problems = find_sync_problems() + find_import_errors()
    logger.info("Python %s", sys.version.split()[0])
    for problem in problems:
        logger.error(problem)
    if problems:
        return 1
    logger.info("Entorno consistente con uv.lock")
    return 0


if __name__ == "__main__":
    sys.exit(main())
