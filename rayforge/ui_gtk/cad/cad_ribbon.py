"""
Contextual CAD Alignment & Properties Ribbon.

Placed directly below the coordinate bar, providing 1-click access to
alignment, distribution, flipping, grouping, and geometric aspect-ratio constraints.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, List, Optional

from gi.repository import Gtk

from ...shared.util.a11y import set_a11y_label
from ...shared.util.localized import _
from ..icons import get_icon

if TYPE_CHECKING:
    from ...core.item import DocItem
    from ..mainwindow import MainWindow

logger = logging.getLogger(__name__)


class CadRibbon(Gtk.Box):
    """
    Contextual ribbon bar for alignment, mirroring, and parametric constraints.
    Automatically enables/disables based on canvas selection count.
    """

    def __init__(self, main_window: "MainWindow", **kwargs) -> None:
        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6, **kwargs
        )
        self.main_window = main_window
        self.add_css_class("cad-ribbon")
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(2)
        self.set_margin_bottom(2)

        self._aspect_locked: bool = True
        self._updating_inputs: bool = False
        self._selected_items: List["DocItem"] = []

        set_a11y_label(
            self,
            _("CAD Contextual Ribbon"),
            role=Gtk.AccessibleRole.TOOLBAR,
            description=_("Quick alignment, distribution, and geometry constraints"),
        )

        self._build_ribbon()
        self._update_action_sensitivity(0)

    def _build_ribbon(self) -> None:
        # ---- 1. Alignment Tools ----
        align_label = Gtk.Label(label=_("Align:"))
        align_label.add_css_class("forge-coord-mono")
        self.append(align_label)

        self._btn_align_left = self._create_action_btn(
            "align-left-symbolic",
            "win.align-left",
            _("Align Left"),
            min_items=1,
        )
        self._btn_align_hcenter = self._create_action_btn(
            "align-horizontal-center-symbolic",
            "win.align-h-center",
            _("Align Center Horizontally"),
            min_items=1,
        )
        self._btn_align_right = self._create_action_btn(
            "align-right-symbolic",
            "win.align-right",
            _("Align Right"),
            min_items=1,
        )
        self._btn_align_top = self._create_action_btn(
            "align-top-symbolic",
            "win.align-top",
            _("Align Top"),
            min_items=1,
        )
        self._btn_align_vcenter = self._create_action_btn(
            "align-vertical-center-symbolic",
            "win.align-v-center",
            _("Align Center Vertically"),
            min_items=1,
        )
        self._btn_align_bottom = self._create_action_btn(
            "align-bottom-symbolic",
            "win.align-bottom",
            _("Align Bottom"),
            min_items=1,
        )

        self.append(self._create_separator())

        # ---- 2. Distribution Tools ----
        self._btn_spread_h = self._create_action_btn(
            "distribute-horizontal-symbolic",
            "win.spread-h",
            _("Distribute Horizontally"),
            min_items=3,
        )
        self._btn_spread_v = self._create_action_btn(
            "distribute-vertical-symbolic",
            "win.spread-v",
            _("Distribute Vertically"),
            min_items=3,
        )

        self.append(self._create_separator())

        # ---- 3. Flip / Mirror ----
        self._btn_flip_h = self._create_action_btn(
            "horizontal-constraint-symbolic",
            "win.flip-horizontal",
            _("Flip Horizontal"),
            fallback_icon="sketch-constrain-horizontal-symbolic",
            min_items=1,
        )
        self._btn_flip_v = self._create_action_btn(
            "vertical-constraint-symbolic",
            "win.flip-vertical",
            _("Flip Vertical"),
            fallback_icon="sketch-constrain-vertical-symbolic",
            min_items=1,
        )

        self.append(self._create_separator())

        # ---- 4. Grouping & Split ----
        self._btn_group = self._create_action_btn(
            "sketch-add-symbolic",
            "win.group",
            _("Group Selection"),
            min_items=2,
        )
        self._btn_ungroup = self._create_action_btn(
            "cut-symbolic",
            "win.ungroup",
            _("Ungroup"),
            min_items=1,
        )
        self._btn_split = self._create_action_btn(
            "laser-path-symbolic",
            "win.split",
            _("Split / Break Apart"),
            min_items=1,
        )

        self.append(self._create_separator())

        # ---- 5. Aspect Ratio Lock & Quick Transform Inputs ----
        self._aspect_btn = Gtk.ToggleButton()
        self._aspect_btn.set_child(get_icon("sketch-constrain-aspect-symbolic"))
        self._aspect_btn.set_active(True)
        self._aspect_btn.add_css_class("flat")
        self._aspect_btn.set_tooltip_text(_("Lock / Unlock Aspect Ratio"))
        set_a11y_label(
            self._aspect_btn,
            _("Lock Aspect Ratio"),
            role=Gtk.AccessibleRole.TOGGLE_BUTTON,
        )
        self._aspect_btn.connect("toggled", self._on_aspect_toggled)
        self.append(self._aspect_btn)

        # Width Spin
        w_lbl = Gtk.Label(label=_("W:"))
        w_lbl.add_css_class("forge-coord-mono")
        self.append(w_lbl)
        self._width_spin = Gtk.SpinButton.new_with_range(0.01, 10000.0, 1.0)
        self._width_spin.set_digits(2)
        self._width_spin.set_width_chars(6)
        self._width_spin.connect("value-changed", self._on_width_changed)
        self.append(self._width_spin)

        # Height Spin
        h_lbl = Gtk.Label(label=_("H:"))
        h_lbl.add_css_class("forge-coord-mono")
        self.append(h_lbl)
        self._height_spin = Gtk.SpinButton.new_with_range(0.01, 10000.0, 1.0)
        self._height_spin.set_digits(2)
        self._height_spin.set_width_chars(6)
        self._height_spin.connect("value-changed", self._on_height_changed)
        self.append(self._height_spin)

        # Angle Spin
        angle_lbl = Gtk.Label(label=_("∠:"))
        angle_lbl.add_css_class("forge-coord-mono")
        self.append(angle_lbl)
        self._angle_spin = Gtk.SpinButton.new_with_range(-180.0, 180.0, 5.0)
        self._angle_spin.set_digits(1)
        self._angle_spin.set_width_chars(5)
        self._angle_spin.connect("value-changed", self._on_angle_changed)
        self.append(self._angle_spin)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.append(spacer)

    def _create_separator(self) -> Gtk.Separator:
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(4)
        sep.set_margin_end(4)
        return sep

    def _create_action_btn(
        self,
        icon_name: str,
        action_name: str,
        tooltip: str,
        fallback_icon: Optional[str] = None,
        min_items: int = 1,
    ) -> Gtk.Button:
        btn = Gtk.Button()
        try:
            btn.set_child(get_icon(icon_name))
        except Exception:
            if fallback_icon:
                btn.set_child(get_icon(fallback_icon))
            else:
                btn.set_child(get_icon("sketch-select-symbolic"))

        btn.add_css_class("flat")
        btn.add_css_class("cad-ribbon-btn")
        btn.set_tooltip_text(tooltip)
        btn.set_action_name(action_name)
        set_a11y_label(btn, tooltip, role=Gtk.AccessibleRole.BUTTON)
        btn._min_items = min_items  # type: ignore
        self.append(btn)
        return btn

    def _on_aspect_toggled(self, button: Gtk.ToggleButton) -> None:
        self._aspect_locked = button.get_active()
        logger.debug(f"Aspect ratio lock toggled: {self._aspect_locked}")

    def on_selection_changed(self, selected_items: List["DocItem"]) -> None:
        """Called by MainWindow when selection changes on the canvas."""
        self._selected_items = list(selected_items)
        count = len(self._selected_items)
        self._update_action_sensitivity(count)

        if count > 0:
            self._update_dimension_inputs()

    def _update_action_sensitivity(self, count: int) -> None:
        """Enable or disable ribbon controls based on item count."""
        has_items = count > 0
        self._width_spin.set_sensitive(has_items)
        self._height_spin.set_sensitive(has_items)
        self._angle_spin.set_sensitive(has_items)
        self._aspect_btn.set_sensitive(has_items)

        for btn in [
            self._btn_align_left,
            self._btn_align_hcenter,
            self._btn_align_right,
            self._btn_align_top,
            self._btn_align_vcenter,
            self._btn_align_bottom,
            self._btn_spread_h,
            self._btn_spread_v,
            self._btn_flip_h,
            self._btn_flip_v,
            self._btn_group,
            self._btn_ungroup,
            self._btn_split,
        ]:
            min_req = getattr(btn, "_min_items", 1)
            btn.set_sensitive(count >= min_req)

    def _update_dimension_inputs(self) -> None:
        """Read selected items' bounding box and set spin inputs."""
        if not self._selected_items or self._updating_inputs:
            return

        try:
            editor = self.main_window.doc_editor
            bbox = editor.transform.group_bbox_world(self._selected_items)
            w = max(0.01, bbox[2] - bbox[0])
            h = max(0.01, bbox[3] - bbox[1])

            self._updating_inputs = True
            try:
                self._width_spin.set_value(w)
                self._height_spin.set_value(h)
            finally:
                self._updating_inputs = False
        except Exception as e:
            logger.debug(f"Failed to update CAD ribbon dimensions: {e}")

    def _on_width_changed(self, spin: Gtk.SpinButton) -> None:
        if self._updating_inputs or not self._selected_items:
            return
        new_w = spin.get_value()
        self._apply_size_change(new_w=new_w)

    def _on_height_changed(self, spin: Gtk.SpinButton) -> None:
        if self._updating_inputs or not self._selected_items:
            return
        new_h = spin.get_value()
        self._apply_size_change(new_h=new_h)

    def _apply_size_change(
        self,
        new_w: Optional[float] = None,
        new_h: Optional[float] = None,
    ) -> None:
        """Resize the selected items via editor transform command."""
        try:
            editor = self.main_window.doc_editor
            bbox = editor.transform.group_bbox_world(self._selected_items)
            old_w = max(0.001, bbox[2] - bbox[0])
            old_h = max(0.001, bbox[3] - bbox[1])

            if new_w is not None and new_h is None:
                scale_x = new_w / old_w
                scale_y = scale_x if self._aspect_locked else 1.0
                if self._aspect_locked:
                    self._updating_inputs = True
                    try:
                        self._height_spin.set_value(old_h * scale_y)
                    finally:
                        self._updating_inputs = False
            elif new_h is not None and new_w is None:
                scale_y = new_h / old_h
                scale_x = scale_y if self._aspect_locked else 1.0
                if self._aspect_locked:
                    self._updating_inputs = True
                    try:
                        self._width_spin.set_value(old_w * scale_x)
                    finally:
                        self._updating_inputs = False
            else:
                return

            center = editor.transform.group_center_world(self._selected_items)
            editor.transform.scale_items(
                self._selected_items,
                scale_x=scale_x,
                scale_y=scale_y,
                center=center,
            )
        except Exception as e:
            logger.debug(f"Scale change through ribbon: {e}")

    def _on_angle_changed(self, spin: Gtk.SpinButton) -> None:
        if self._updating_inputs or not self._selected_items:
            return
        angle_deg = spin.get_value()
        try:
            editor = self.main_window.doc_editor
            center = editor.transform.group_center_world(self._selected_items)
            editor.transform.rotate_items(
                self._selected_items,
                angle_rad=math.radians(angle_deg),
                center=center,
            )
        except Exception as e:
            logger.debug(f"Rotate change through ribbon: {e}")
