"""Unit tests for CadToolPalette."""

import pytest

from rayforge.ui_gtk.cad.cad_palette import CadToolPalette


pytestmark = pytest.mark.ui


def test_cad_palette_initialization():
    palette = CadToolPalette()
    assert palette.active_tool == "select"
    assert "select" in palette._tool_buttons
    assert "rectangle" in palette._tool_buttons
    assert "circle" in palette._tool_buttons
    assert "line" in palette._tool_buttons
    assert "bezier" in palette._tool_buttons
    assert "text" in palette._tool_buttons
    assert "offset" in palette._tool_buttons
    assert "tabs" in palette._tool_buttons
    assert "measure" in palette._tool_buttons
    assert not palette._tool_buttons["measure"].get_sensitive()


def test_cad_palette_set_active_tool():
    palette = CadToolPalette()
    events = []

    def on_tool_changed(sender, tool_name):
        events.append(tool_name)

    palette.tool_changed.connect(on_tool_changed)

    palette.set_active_tool("rectangle")
    assert palette.active_tool == "rectangle"
    assert "rectangle" in events

    palette.set_active_tool("circle")
    assert palette.active_tool == "circle"
    assert "circle" in events

    # Invalid tool name falls back to select
    palette.set_active_tool("nonexistent")
    assert palette.active_tool == "select"


def test_cad_palette_button_toggled():
    palette = CadToolPalette()
    events = []

    def on_tool(sender, tool_name):
        events.append(tool_name)

    palette.tool_changed.connect(on_tool)

    btn_rect = palette._tool_buttons["rectangle"]
    btn_rect.set_active(True)

    palette._on_button_toggled(btn_rect, "rectangle")
    assert palette.active_tool == "rectangle"
    assert "rectangle" in events
