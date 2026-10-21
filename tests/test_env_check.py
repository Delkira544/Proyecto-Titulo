"""Pruebas de burnsev.env_check."""

from burnsev import env_check


def test_find_import_errors_informa_modulo_inexistente():
    errors = env_check.find_import_errors(("numpy", "modulo_inexistente_xyz"))
    assert len(errors) == 1
    assert errors[0].startswith("modulo_inexistente_xyz")


def test_find_sync_problems_informa_fallo_de_uv(monkeypatch):
    class Falla:
        returncode = 1
        stdout = ""
        stderr = "lock desactualizado"

    monkeypatch.setattr(env_check.subprocess, "run", lambda *a, **k: Falla())
    assert env_check.find_sync_problems() == ["uv sync --check: lock desactualizado"]
