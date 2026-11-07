"""
CAD Tool Palette for Parametric CAD & Design Studio.

Vertical tool strip housing selection, parametric shapes, vector paths,
spline curves, text, kerf offset, tabs, and measurement tools.
"""

from __future__ import annotations

import logging
from typing import Dict

from blinker import Signal
from gi.repository import Gtk

from ...shared.util.a11y import set_a11y_label
from ...shared.util.localized import _
from ..icons import get_icon

logger = logging.getLogger(__name__)


class CadToolPalette(Gtk.Box):
    """
    Vertical CAD tool palette placed on the left side of the workspace.
    Provides rapid 1-click access to 2D vector creation and CAD operations.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=4, **kwargs
        )
        self.add_css_class("cad-tool-palette")
        self.set_margin_start(8)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.START)

        # Signals
        self.tool_changed = Signal()  # (sender, tool_name: str)
        self.action_requested = Signal()  # (sender, action_name: str)

        self._active_tool: str = "select"
        self._tool_buttons: Dict[str, Gtk.ToggleButton] = {}
        self._action_buttons: Dict[str, Gtk.Button] = {}
        self._updating_toggle: bool = False

        set_a11y_label(
            self,
            _("CAD Tool Palette"),
            role=Gtk.AccessibleRole.TOOLBAR,
            description=_(
                "Tools for selecting, drawing, and modifying 2D shapes"
            ),
        )

        self._build_palette()

    def _build_palette(self) -> None:
        # ---- Group 1: Selection & Nodes ----
        self._add_tool_button(
            "select",
            "sketch-select-symbolic",
            _("Select / Transform (S)"),
            _("Select and transform shapes on the canvas"),
        )
        self._add_tool_button(
            "nodes",
            "sketch-edit-symbolic",
            _("Edit Nodes / Vertices (N)"),
            _("Edit vertices, control points, and sketch geometry"),
        )

        self.append(self._create_separator())

        # ---- Group 2: Parametric Primitives ----
        self._add_tool_button(
            "rectangle",
            "sketch-rect-symbolic",
            _("Rectangle (R)"),
            _("Create a parametric rectangle"),
        )
        self._add_tool_button(
            "rounded_rect",
            "sketch-rounded-rect-symbolic",
            _("Rounded Rectangle"),
            _("Create a rectangle with rounded corners"),
        )
        self._add_tool_button(
            "circle",
            "sketch-circle-symbolic",
            _("Circle / Ellipse (C)"),
            _("Create a circle or ellipse"),
        )
        self._add_tool_button(
            "arc",
            "sketch-arc-symbolic",
            _("Arc (A)"),
            _("Create a 3-point circular arc"),
        )
        self._add_tool_button(
            "line",
            "sketch-line-symbolic",
            _("Polyline / Path (P)"),
            _("Create a multi-segment line or polygon"),
        )
        self._add_tool_button(
            "bezier",
            "sketch-bezier-symbolic",
            _("Bezier Curve (B)"),
            _("Create smooth spline curves"),
        )
        self._add_tool_button(
            "text",
            "sketch-text-symbolic",
            _("Text / Laser Typography (T)"),
            _("Add vector text ready for engraving or cutting"),
        )

        self.append(self._create_separator())

        # ---- Group 3: CAM & Fabrication Tools ----
        self._add_tool_button(
            "offset",
            "sketch-distance-symbolic",
            _("Kerf Offset / Contour Expansion"),
            _("Expand or inset contour to compensate for beam kerf"),
        )
        self._add_tool_button(
            "tabs",
            "tabs-equidistant-symbolic",
            _("Holding Tabs (Bridge Placer)"),
            _("Add tabs to prevent cut parts from tilting or falling"),
        )
        self._add_tool_button(
            "measure",
            "sketch-diameter-symbolic",
            _("Measure & Inspect"),
            _("Measure distances, dimensions, and clearances"),
        )

        self._tool_buttons["measure"].set_sensitive(False)
        self._tool_buttons["measure"].set_tooltip_text(
            _("Measurement is not yet available from this palette")
        )

        # Set default active
        if "select" in self._tool_buttons:
            self._tool_buttons["select"].set_active(True)

    def _create_separator(self) -> Gtk.Separator:
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(2)
        sep.set_margin_bottom(2)
        return sep

    def _add_tool_button(
        self,
        tool_name: str,
        icon_name: str,
        label: str,
        description: str,
    ) -> Gtk.ToggleButton:
        btn = Gtk.ToggleButton()
        btn.set_child(get_icon(icon_name))
        btn.add_css_class("flat")
        btn.add_css_class("cad-tool-btn")
        btn.set_tooltip_text(f"{label}\n{description}")
        set_a11y_label(
            btn,
            label,
            role=Gtk.AccessibleRole.TOGGLE_BUTTON,
            description=description,
        )

        btn.connect("toggled", self._on_button_toggled, tool_name)
        self._tool_buttons[tool_name] = btn
        self.append(btn)
        return btn

    def _on_button_toggled(
        self, button: Gtk.ToggleButton, tool_name: str
    ) -> None:
        if self._updating_toggle:
            return

        if button.get_active():
            self._updating_toggle = True
            try:
                # Deactivate all other tool buttons
                for name, other_btn in self._tool_buttons.items():
                    if name != tool_name and other_btn.get_active():
                        other_btn.set_active(False)
            finally:
                self._updating_toggle = False

            self._active_tool = tool_name
            logger.debug(f"CAD Tool selected: {tool_name}")
            self.tool_changed.send(self, tool_name=tool_name)
        else:
            # If user unclicks the active tool, revert to 'select'
            if self._active_tool == tool_name:
                self.set_active_tool("select")

    def set_active_tool(self, tool_name: str) -> None:
        """Selects a tool programmatically."""
        if tool_name not in self._tool_buttons:
            tool_name = "select"

        self._active_tool = tool_name
        self._updating_toggle = True
        try:
            for name, btn in self._tool_buttons.items():
                btn.set_active(name == tool_name)
        finally:
            self._updating_toggle = False

        self.tool_changed.send(self, tool_name=tool_name)

    @property
    def active_tool(self) -> str:
        """Return the current active tool identifier."""
        return self._active_tool
