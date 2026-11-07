# Project status — 2026-11-07

This review applies to the local changes based on commit `8303ecb5` in
[yuri-schmaltz/blueforge](https://github.com/yuri-schmaltz/blueforge).
The application is Blueforge, with executable `blueforge` and Python
namespace `rayforge`. The project license is MIT.

## Product scope

Blueforge is a laser-engraving-only application. The following features
were removed because they are not part of the engraving workflow:

| Removed | What went with it |
| --- | --- |
| Anonymous usage telemetry | Umami client, consent dialog, all `track_page_view` call sites, the Privacy preferences group |
| Print & Cut addon | The whole `rayforge-addon-print-and-cut` builtin addon (1,273 LOC) |
| Camera integration | Camera manager, V4L2 controller, ChArUco calibration, ten UI dialogs, the canvas element, the settings page and the `<Ctrl><Alt>c` action |
| Rotary axis support | Rotary module model and settings page, `ROTARY` axis type, kinematic mapping/math helpers, chuck and cylinder machinery, cylinder renderer, rotary layer attachment |

The 3D simulator now compiles every layer into a single flat vertex layer.
The machine and device profiles no longer carry `rotary_modules` or
`rotary_enabled_default` keys.

## Priorities addressed

- CAD position, dimension and rotation controls now use the existing editor
  commands, with machine coordinates, absolute rotation and undo/redo.
  Ribbon and inspector values follow model transforms and document changes.
- Contour kerf, cut side and overcut edits use undo commands and model
  notifications. Settings apply to the first contour in the active layer.
- The timeline reconnects after document replacement and updates on model
  edits. It displays operations, normalized power as a percentage and
  speed in mm/min. Sorting groups operation types; toolpath review is
  still required to determine an appropriate machining sequence.
- Unsupported inspector controls and palette measurement are disabled.
  The user manual explains the current behavior of the sketch entry points.
- GTK shortcuts and the first-run tour use supported APIs. The tour opens,
  navigates and closes, and the main-window project-import test passes.
- OpenCV is included in the Pixi environment. Python package metadata and
  source fallback report 1.3.3 without requiring Git tags.
- Documentation builds in a dedicated locked environment. The documentation
  workflow uploads a preview. Development, release and installation guides
  describe the available environments and platform scripts.
- The backend coverage job uses the 35% threshold in `pyproject.toml`;
  the duplicate 70% job was removed. Translation checks parse JSON results
  correctly and compare catalogs without rewriting them.
- Test runs use separate configuration directories. CAD tests use real GTK
  widgets, and the serial simulator keeps polling paced under coverage.

## Verification

Local results:

| Check | Result |
| --- | --- |
| Backend suite with coverage | 4,928 passed; 35% coverage gate |
| Complete UI suite | 298 passed |
| Stress suite | 22 passed |
| Property-based tests | 8 properties, 100 iterations each; all passed |
| Documentation build | Strict build passed |
| Translation workflow | Update, check and compile passed in an isolated copy |
| Translation audit | Zero candidates |
| Lint gate | flake8, pyflakes and pyright all report zero findings |
| Python distribution | Wheel and source archive built as 1.3.3 |

Reproduce the checks from the repository root:

```bash
pixi install --locked
pixi run --frozen test
pixi run --frozen uitest
pixi run --frozen coverage
pixi run --frozen lint
pixi run --frozen -e docs docs-build
pixi run --frozen python -m rayforge.util.i18n_audit --format json
pixi run --frozen python -m rayforge.util.i18n_extract --check
pixi run --frozen wheel
```

UI tests require a display. Use `xvfb-run -a` on Linux CI. The generated
wheel is `dist/blueforge-1.3.3-py3-none-any.whl`; it retains the
`blueforge` entry point and MIT package metadata.

## Remaining limitations

- Fillet, tab width and lead-in/out editing in the CAD inspector remain
  unavailable. Use the existing sketch editor and item properties where
  applicable. Palette shape buttons open the sketch editor; they do not
  automatically select the corresponding sketch tool.
- Native Linux, Windows and macOS installers were not built or installed
  in this review. The macOS script is local and the Pixi target is ARM64;
  there is no automated universal macOS build.
- Connected hardware, signing credentials, publication and remote GitHub
  Actions runs were not exercised. The checks above were run locally.
- New catalog entries use the English source text until translated. The
  contrast checker retains its two documented WCAG AA exceptions.
- The `insights_panel` sections are built as `Gtk.ListBox` rows rather
  than `Adw.PreferencesRow` entries. The visual grouping matches the rest
  of the app, but the rows are not keyboard-navigable the way native
  Adwaita preference rows are.
