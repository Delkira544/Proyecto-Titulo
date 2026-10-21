"""Registro de ejecución para los scripts de Snakemake."""

import logging
import platform
import sys
from importlib import metadata
from pathlib import Path

KEY_PACKAGES = ("geopandas", "pandas", "numpy", "pyproj", "pyogrio", "shapely")


def setup_logging(log_file: str | Path, params: dict | None = None) -> logging.Logger:
    """Configura ``logging`` hacia ``log_file`` y registra versiones y parámetros.

    Args:
        log_file: archivo definido en ``log:`` de la regla.
        params: parámetros recibidos por el script (se escriben al inicio).
    """
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    logger = logging.getLogger("burnsev")

    def log_uncaught(exc_type, exc, tb):
        logger.critical("Error no controlado", exc_info=(exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = log_uncaught  # el traceback queda en el log de la regla
    logger.info("Python %s", platform.python_version())
    for package in KEY_PACKAGES:
        logger.info("%s %s", package, metadata.version(package))
    logger.info("Parámetros: %s", params)
    return logger
