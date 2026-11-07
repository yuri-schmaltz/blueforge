# Developer guide

Blueforge is a desktop application and a fork of Rayforge. The installed
command and package are named `blueforge`. Addons and Python imports use
the `rayforge` namespace.
The license is MIT; see [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Development environment

Use Pixi to install the native GTK, Libadwaita, image-processing and Python
dependencies together. Installing only `pip install -e .` is insufficient:
the Python package metadata does not declare the full runtime environment.

```bash
git clone https://github.com/yuri-schmaltz/blueforge.git
cd blueforge
pixi install --locked
pixi run --frozen blueforge
```

The supported Pixi platforms are Linux x86_64 and macOS ARM64. Windows
uses the separate MSYS2 scripts in `scripts/win/`. Python metadata allows
3.10+, while the Pixi environment requires 3.11+; the lockfile selects the
concrete interpreter. See [docs/BUILDING.md](docs/BUILDING.md).

## Code layout

| Path | Responsibility |
| --- | --- |
| `rayforge/app.py` | Application entry point and startup |
| `rayforge/context.py` | Shared context and addon initialization |
| `rayforge/core/` | Documents, items, layers, steps, workflows, undo |
| `rayforge/doceditor/` | Editing commands, import/export, transformations |
| `rayforge/pipeline/` | Toolpath computation, artifacts and encoding |
| `rayforge/machine/` | Machine models, drivers, transports and checks |
| `rayforge/simulator/` | Playback and compiled 3D scenes |
| `rayforge/image/` | Importers, rendering and image processing |
| `rayforge/ui_gtk/` | GTK widgets, window, dialogs and canvas |
| `rayforge/ui_gtk/cad/` | CAD palette, ribbon, inspector and timeline |
| `rayforge/shared/tasker/` | Background threads and worker processes |
| `rayforge/addon_mgr/` | Addon discovery and lifecycle |
| `rayforge/builtin_addons/` | Laser operations, sketcher and materials |
| `rayforge/locale/` | Translation catalogs |
| `tests/` | Backend, UI, integration and stress tests |

## Editing and model notifications

`DocEditor` owns document editing commands and the pipeline. Use its
commands rather than changing matrices directly from widgets:

- `editor.transform.set_position_group(items, x, y)` uses machine coordinates.
- `editor.transform.set_size_group(items, width=..., fixed_ratio=True)` resizes
  the selection around its center.
- `editor.transform.set_angle_group(items, angle)` sets an absolute angle in
  degrees using the first selected item as the anchor.

These commands preserve undo/redo. Widget refreshes must guard against
feedback from programmatic updates. Use `notify::value` for `Adw.SpinRow`.
Step edits must use undo commands and the model's setters/signals so the
pipeline invalidates cached computations.

The GTK event loop runs on the main thread. Background tasks use threads
and worker processes; this is not a single-process architecture. Worker
entry points support headless operation. Avoid importing GTK into core
editing and computation modules.

## Tests and checks

```bash
pixi run --frozen test
pixi run --frozen pytest tests/doceditor/test_transform_cmd.py tests/test_headless.py
pixi run --frozen uitest
pixi run --frozen pytest -m ui tests/ui_gtk/test_cad_geometry_controls.py
pixi run --frozen coverage
pixi run --frozen lint
pixi run --frozen format
```

UI tests require a display; on CI use `xvfb-run -a pixi run --frozen uitest`.
The default pytest selection excludes UI and stress tests. The backend
Pixi task also excludes `tests/ui_gtk`; run that directory explicitly with
`-m ui` when checking CAD widgets. Built-in addon tests are included via
pytest's `testpaths` configuration.

The coverage gate is defined in `pyproject.toml` (currently 35%). It is a
baseline, not a claim that all critical UI paths are covered. Do not
silently lower it when adding code.

```bash
pixi run --frozen python -m rayforge.util.i18n_audit --format text
pixi run --frozen python -m rayforge.util.contrast_check
pixi run --frozen python -m rayforge.util.benchmarks
PYTHONPATH=. pixi run --frozen python tests/property/__init__.py
```

`make lint` runs the Pixi lint task (flake8, pyflakes and pyright). Bandit
runs separately in CI. Use `make help` for the available wrappers.

## Translations and accessibility

Wrap user-facing strings in `_()`. Run `pixi run update-translations` to
update catalogs and `pixi run compile-translations` to compile them.
Add accessible names to icon-only buttons and verify keyboard navigation.
See [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md).

## Documentation and releases

[docs/INDEX.md](docs/INDEX.md) indexes the manuals and operational guides.
[docs/RELEASE.md](docs/RELEASE.md) describes versioning and the actual
release workflows. The repository includes automated Linux and Windows
builds; macOS packaging is a local script, not an automated universal build.
