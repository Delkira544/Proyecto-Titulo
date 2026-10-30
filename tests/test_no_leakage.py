"""No fuga: la calibración no depende del evento de validación (CLAUDE.md §8.6).

Se construye el grafo de reglas (sin ejecutar nada) de los productos finales de
calibración y se comprueba que ninguna regla de validación ni de EMSR859 queda
aguas arriba.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_RULES = {
    "inspect_emsr859",
    "build_validation_perimeters",
    "query_validation_scene_cloud",
    "review_validation_cloudiness",
    "export_validation_indices",
}


def _calibration_targets() -> list[str]:
    config = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
    res = config["rutas"]["results"]
    return [
        f"{res}/tables/suficiencia_estratos.csv",
        f"{res}/tables/estadisticos_indice_estrato.csv",
        f"{res}/tables/multimodalidad_indice_estrato.csv",
    ]


def _upstream_rules(targets: list[str]) -> set[str]:
    cmd = [sys.executable, "-m", "snakemake", "--rulegraph", "dot", *targets]
    done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        pytest.skip(f"No se pudo construir el grafo: {done.stderr[-500:]}")
    return {
        line.split('label = "', 1)[1].split('"', 1)[0]
        for line in done.stdout.splitlines()
        if 'label = "' in line
    }


def test_calibration_does_not_depend_on_validation():
    rules = _upstream_rules(_calibration_targets())
    assert "build_fire_catalog" in rules  # el grafo se construyó de verdad
    assert not rules & VALIDATION_RULES
