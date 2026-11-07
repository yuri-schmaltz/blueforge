"""Centralized panel show/hide and layout presets.

The MainWindow has three main user-toggleable surfaces:

  - Toolbar (handled by MainToolbar, controlled via the
    'toolbar_mode' config: essential / all)
  - Right pane (workflow + properties tabs, on the canvas
    overlay; toggle button in the header)
  - Bottom panel (logs, gcode viewer, etc., in the VPaned
    below the canvas; toggle button in the header)

This module centralizes the show/hide state for the right and
bottom panels and applies one of three layout presets:

  - "default"  : all panels visible (right + bottom)
  - "compact"  : bottom hidden, right visible (focus mode
                 for the canvas)
  - "expanded" : right hidden, bottom visible (logs focus
                 mode for debugging)

The current layout is persisted to config.panel_layout so it
survives restarts. Per-panel overrides (e.g. "user toggled
the right panel off in default layout") are layered on top of
the preset, so a user who likes 'default' but wants no right
panel doesn't have to reconfigure each restart.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# Layout preset → (right_panel_visible, bottom_panel_visible,
# cad_palette, cad_ribbon).
# 'toolbar' isn't included here because the toolbar already has
# its own mode toggle in the MainToolbar; mixing it in here
# would conflate two concerns.
_PRESETS = {
    "default": {
        "right": True,
        "bottom": True,
        "cad_palette": True,
        "cad_ribbon": True,
    },
    "compact": {
        "right": True,
        "bottom": False,
        "cad_palette": True,
        "cad_ribbon": False,
    },
    "expanded": {
        "right": False,
        "bottom": True,
        "cad_palette": False,
        "cad_ribbon": False,
    },
    "cad_studio": {
        "right": True,
        "bottom": True,
        "cad_palette": True,
        "cad_ribbon": True,
    },
}


class PanelManager:
    """Coordinates show/hide of the right + bottom panels and CAD
    studio surfaces.

    Holds weak references to the widgets it controls. The
    MainWindow calls apply_layout() whenever config changes
    (initial load, settings change, menu action).
    """

    def __init__(
        self,
        right_panel=None,
        bottom_panel=None,
        cad_palette=None,
        cad_ribbon=None,
    ) -> None:
        self._right = right_panel
        self._bottom = bottom_panel
        self._cad_palette = cad_palette
        self._cad_ribbon = cad_ribbon

    def set_panels(
        self,
        right_panel=None,
        bottom_panel=None,
        cad_palette=None,
        cad_ribbon=None,
    ) -> None:
        """Late-bind the actual panel widgets. Called from
        MainWindow.__init__ after the widgets are constructed."""
        if right_panel is not None:
            self._right = right_panel
        if bottom_panel is not None:
            self._bottom = bottom_panel
        if cad_palette is not None:
            self._cad_palette = cad_palette
        if cad_ribbon is not None:
            self._cad_ribbon = cad_ribbon

    @staticmethod
    def valid_presets() -> list[str]:
        return list(_PRESETS.keys())

    @staticmethod
    def resolve(layout: str) -> dict:
        """Return the visibility dict for a layout name.

        Unknown values fall back to 'default' (the canonical
        'everything visible' state) so a stale config value
        doesn't break the UI.
        """
        return _PRESETS.get(layout, _PRESETS["default"])

    def apply_layout(self, layout: str) -> None:
        """Apply a layout preset to the bound panels.

        The 'toolbar' column of the preset is intentionally
        ignored here — the toolbar is controlled by the
        MainToolbar itself.
        """
        preset = self.resolve(layout)
        if self._right is not None:
            self._right.set_visible(preset.get("right", True))
        if self._bottom is not None:
            self._bottom.set_visible(preset.get("bottom", True))
        if self._cad_palette is not None:
            self._cad_palette.set_visible(preset.get("cad_palette", True))
        if self._cad_ribbon is not None:
            self._cad_ribbon.set_visible(preset.get("cad_ribbon", True))
        logger.debug("Applied panel layout '%s': %s", layout, preset)

    def set_right_visible(self, visible: bool) -> None:
        if self._right is not None:
            self._right.set_visible(visible)

    def set_bottom_visible(self, visible: bool) -> None:
        if self._bottom is not None:
            self._bottom.set_visible(visible)

    def set_cad_palette_visible(self, visible: bool) -> None:
        if self._cad_palette is not None:
            self._cad_palette.set_visible(visible)

    def set_cad_ribbon_visible(self, visible: bool) -> None:
        if self._cad_ribbon is not None:
            self._cad_ribbon.set_visible(visible)

    def is_right_visible(self) -> bool:
        return bool(self._right and self._right.get_visible())

    def is_bottom_visible(self) -> bool:
        return bool(self._bottom and self._bottom.get_visible())

    def is_cad_palette_visible(self) -> bool:
        return bool(self._cad_palette and self._cad_palette.get_visible())

    def is_cad_ribbon_visible(self) -> bool:
        return bool(self._cad_ribbon and self._cad_ribbon.get_visible())
