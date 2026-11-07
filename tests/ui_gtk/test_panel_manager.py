"""Tests for PanelManager and CAD Studio layout presets."""

import importlib.util
import os
from unittest.mock import MagicMock

# Isolated load so tests run on platforms without GTK4/gi installed
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))

_panel_mgr_path = os.path.join(
    _REPO_ROOT, "rayforge", "ui_gtk", "panel_manager.py"
)
_spec = importlib.util.spec_from_file_location(
    "panel_manager_module", _panel_mgr_path
)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
PanelManager = _mod.PanelManager


def test_panel_manager_presets():
    presets = PanelManager.valid_presets()
    assert "default" in presets
    assert "compact" in presets
    assert "expanded" in presets
    assert "cad_studio" in presets


def test_panel_manager_resolve():
    cad_preset = PanelManager.resolve("cad_studio")
    assert cad_preset["right"] is True
    assert cad_preset["bottom"] is True
    assert cad_preset["cad_palette"] is True
    assert cad_preset["cad_ribbon"] is True

    fallback = PanelManager.resolve("unknown_preset")
    assert fallback == PanelManager.resolve("default")


def test_panel_manager_apply_layout():
    right = MagicMock()
    bottom = MagicMock()
    cad_palette = MagicMock()
    cad_ribbon = MagicMock()

    mgr = PanelManager(
        right_panel=right,
        bottom_panel=bottom,
        cad_palette=cad_palette,
        cad_ribbon=cad_ribbon,
    )

    mgr.apply_layout("cad_studio")
    right.set_visible.assert_called_with(True)
    bottom.set_visible.assert_called_with(True)
    cad_palette.set_visible.assert_called_with(True)
    cad_ribbon.set_visible.assert_called_with(True)

    mgr.apply_layout("expanded")
    right.set_visible.assert_called_with(False)
    bottom.set_visible.assert_called_with(True)
    cad_palette.set_visible.assert_called_with(False)
    cad_ribbon.set_visible.assert_called_with(False)


def test_panel_manager_individual_controls():
    palette = MagicMock()
    palette.get_visible.return_value = True
    ribbon = MagicMock()
    ribbon.get_visible.return_value = False

    mgr = PanelManager(cad_palette=palette, cad_ribbon=ribbon)

    assert mgr.is_cad_palette_visible() is True
    assert mgr.is_cad_ribbon_visible() is False

    mgr.set_cad_palette_visible(False)
    palette.set_visible.assert_called_with(False)

    mgr.set_cad_ribbon_visible(True)
    ribbon.set_visible.assert_called_with(True)
