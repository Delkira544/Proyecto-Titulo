"""Instala el entorno del proyecto desde cero con uv.

Ejecuta ``uv sync --locked`` (crea ``.venv`` con las versiones de ``uv.lock``
e instala ``src/burnsev`` en modo editable), verifica el resultado con
``burnsev.env_check`` y hace ``snakemake -n``.

Requiere ``uv`` instalado. Uso (desde cualquier carpeta):
    python3 workflow/scripts/00_setup_env.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> None:
    """Ejecuta un comando desde la raíz del repo; falla si el código de salida != 0."""
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    if shutil.which("uv") is None:
        sys.exit("No se encontró 'uv' en el PATH; instálalo primero.")
    if (ROOT / ".venv").exists():
        sys.exit(".venv ya existe; bórralo tú mismo si quieres una instalación limpia.")

    run(["uv", "sync", "--locked"])
    run(["uv", "run", "python", "-m", "burnsev.env_check"])
    run(["uv", "run", "snakemake", "-n", "--cores", "1"])
    print("Instalación limpia verificada.")


if __name__ == "__main__":
    main()
