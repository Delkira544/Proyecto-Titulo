# Clasificación de severidad de daño post-incendio en Biobío

Transferibilidad de umbrales de severidad de incendios (Key & Benson, 2006) al Biobío, Chile, con Sentinel-2 L2A.

- [Backlog Github](https://github.com/users/Delkira544/projects/2)
- Decisiones de diseño: [`docs/adr/`](./docs/adr/README.md)

## Requisitos

- **Python 3.14.7** (fijado en `pyproject.toml`: `requires-python = "==3.14.*"`).
- Entorno y dependencias con [`uv`](https://docs.astral.sh/uv/) (crea y mantiene el `.venv`). **No se usa conda**: todas las reglas de Snakemake corren en el `.venv`.
- Linter y formateador: `ruff` (configurado en `pyproject.toml`).
  El [ADR-0018](./docs/adr/0018-snakemake-gestor-flujo-trabajo.md) menciona «entornos conda por regla»; el proyecto aplica la regla de `CLAUDE.md` (sin conda) y el ADR queda sin enmendar por ahora.

## Instalación

Instalación limpia (`uv sync --locked`: crea el `.venv` con las versiones de `uv.lock` e instala `src/burnsev`; luego verifica con `burnsev.env_check` y hace `snakemake -n`):

```bash
python3 workflow/scripts/00_setup_env.py   # equivale a: uv sync --locked
```

Las dependencias se declaran en `pyproject.toml` y se fijan en `uv.lock` (`uv add <paquete>` actualiza ambos; `uv lock` regenera el lock).

## Datos de entrada

Los datos crudos van en `resources/raw/` (fuera de Git, inmutables). Esperado hoy:

```
resources/raw/conaf/incendios/{2019_2020,...,2024_2025}/if_magnitud_*.shp
resources/raw/conaf/sit/sit_2024_biobio.shp
```

Falta la temporada 2025_2026 (evento de validación, enero 2026): no hay perímetros CONAF. El catálogo solo cubre lo que existe.

## Ejecución

Desde la raíz del repo:

```bash
uv run snakemake -n --cores 1          # simulacro
uv run snakemake --cores 1             # esqueleto actual (lee shapefiles locales, sin descargas)
uv run pytest                          # pruebas de src/burnsev
uv run ruff check                      # linter
uv run ruff format --check             # formato (sin modificar)
```

Productos actuales:

| Archivo | Contenido |
|---|---|
| `results/catalogo/catalogo_incendios.csv` | Incendios del Biobío con `estado` (dentro/fuera) y `motivo` |
| `results/catalogo/fires.tsv` | Incendios «dentro» con `role=calibracion` |
| `results/catalogo/inventario_shapefiles.csv` | CRS, columnas, geometrías inválidas por temporada |
| `resources/external_meta/manifest.tsv` | Procedencia y `sha256` de los datos crudos |

Los parámetros viven en `config/config.yaml` (los marcados `PROVISORIO` no están definidos).

## Estado del catálogo

La revisión de nubosidad pre/post (Sentinel-2 vía Earth Engine) aún no está implementada: el catálogo deja `nubosidad_*` y `escena_*` vacíos, y el motivo de los incendios «dentro» indica «nubosidad pendiente de revisión».
