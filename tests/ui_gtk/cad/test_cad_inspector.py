"""Unit tests for CadInspectorTab."""

import pytest

from unittest.mock import MagicMock
from rayforge.ui_gtk.cad.cad_inspector import CadInspectorTab


pytestmark = pytest.mark.ui


def test_cad_inspector_initialization():
    editor = MagicMock()
    tab = CadInspectorTab(editor)
    assert tab.pos_x_row is not None
    assert tab.pos_y_row is not None
    assert tab.width_row is not None
    assert tab.height_row is not None
    assert tab.kerf_spin is not None
    assert tab.cut_side_row is not None


def test_cad_inspector_kerf_presets():
    editor = MagicMock()
    tab = CadInspectorTab(editor)

    # Fiber preset
    tab._set_kerf_value(0.05)
    assert tab.kerf_spin.get_value() == 0.05

    # Diode preset
    tab._set_kerf_value(0.12)
    assert tab.kerf_spin.get_value() == 0.12

    # CO2 preset
    tab._set_kerf_value(0.20)
    assert tab.kerf_spin.get_value() == 0.20


def test_cad_inspector_selection_sensitivity():
    editor = MagicMock()
    tab = CadInspectorTab(editor)

    # No items selected -> inspector becomes insensitive
    tab.on_selection_changed([])
    assert tab.get_sensitive() is False

    # Items selected -> inspector becomes sensitive
    item1 = MagicMock()
    editor.transform.group_bbox_world.return_value = (10.0, 20.0, 110.0, 120.0)
    editor.transform.get_position_group.return_value = (10.0, 20.0)
    editor.transform.get_angle_group.return_value = 0.0
    tab.on_selection_changed([item1])
    assert tab.get_sensitive() is True
    assert tab.pos_x_row.get_value() == 10.0
    assert tab.pos_y_row.get_value() == 20.0
    assert tab.width_row.get_value() == 100.0
    assert tab.height_row.get_value() == 100.0
