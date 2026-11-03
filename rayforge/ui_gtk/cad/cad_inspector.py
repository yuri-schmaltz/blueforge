"""
Parametric CAD & Kerf Inspector Tab.

Provides direct access to geometric constraints, laser beam kerf compensation,
holding tabs placement, and lead-in/lead-out parameters.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, List

from gi.repository import Adw, Gtk

from ...core.item import DocItem
from ...shared.util.a11y import set_a11y_label
from ...shared.util.localized import _

if TYPE_CHECKING:
    from ...doceditor.editor import DocEditor

logger = logging.getLogger(__name__)


class CadInspectorTab(Gtk.Box):
    """
    Inspector panel tab integrating CAD dimensions, beam kerf offsets,
    holding tabs, and cutting lead-in/out configurations.
    """

    def __init__(self, editor: "DocEditor", **kwargs) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=12, **kwargs
        )
        self.editor = editor
        self.add_css_class("cad-inspector")
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(8)
        self.set_margin_bottom(8)

        self._selected_items: List[DocItem] = []
        self._updating: bool = False
        self._aspect_locked: bool = True

        set_a11y_label(
            self,
            _("CAD & Kerf Inspector"),
            role=Gtk.AccessibleRole.GROUP,
            description=_("Parametric geometry, kerf compensation, and tabs"),
        )

        self._build_ui()

    def _build_ui(self) -> None:
        # ============================================================
        # 1. Geometry & Parametric Dimensions
        # ============================================================
        geom_group = Adw.PreferencesGroup()
        geom_group.set_title(_("Parametric Geometry"))
        geom_group.set_description(
            _("Real-world dimensions, position, and corner fillets")
        )

        # X, Y Position
        x_adj = Gtk.Adjustment(
            lower=-10000.0, upper=10000.0, step_increment=1.0, page_increment=10.0
        )
        self.pos_x_row = Adw.SpinRow(
            title=_("X Position (mm)"), adjustment=x_adj, digits=2
        )
        self.pos_x_row.connect("changed", self._on_pos_x_changed)
        geom_group.add(self.pos_x_row)

        y_adj = Gtk.Adjustment(
            lower=-10000.0, upper=10000.0, step_increment=1.0, page_increment=10.0
        )
        self.pos_y_row = Adw.SpinRow(
            title=_("Y Position (mm)"), adjustment=y_adj, digits=2
        )
        self.pos_y_row.connect("changed", self._on_pos_y_changed)
        geom_group.add(self.pos_y_row)

        # Width, Height
        w_adj = Gtk.Adjustment(
            lower=0.01, upper=10000.0, step_increment=1.0, page_increment=10.0
        )
        self.width_row = Adw.SpinRow(
            title=_("Width (mm)"), adjustment=w_adj, digits=2
        )
        self.width_row.connect("changed", self._on_width_changed)
        geom_group.add(self.width_row)

        h_adj = Gtk.Adjustment(
            lower=0.01, upper=10000.0, step_increment=1.0, page_increment=10.0
        )
        self.height_row = Adw.SpinRow(
            title=_("Height (mm)"), adjustment=h_adj, digits=2
        )
        self.height_row.connect("changed", self._on_height_changed)
        geom_group.add(self.height_row)

        # Rotation Angle
        rot_adj = Gtk.Adjustment(
            lower=-180.0, upper=180.0, step_increment=5.0, page_increment=15.0
        )
        self.rot_row = Adw.SpinRow(
            title=_("Rotation (deg)"), adjustment=rot_adj, digits=1
        )
        self.rot_row.connect("changed", self._on_rotation_changed)
        geom_group.add(self.rot_row)

        # Fillet / Corner Radius
        fillet_adj = Gtk.Adjustment(
            lower=0.0, upper=100.0, step_increment=0.5, page_increment=2.0
        )
        self.fillet_row = Adw.SpinRow(
            title=_("Corner Radius (Fillet)"),
            subtitle=_("Round sharp corners for smooth laser cutting"),
            adjustment=fillet_adj,
            digits=2,
        )
        geom_group.add(self.fillet_row)

        self.append(geom_group)

        # ============================================================
        # 2. Laser Kerf & Cut Offset
        # ============================================================
        kerf_group = Adw.PreferencesGroup()
        kerf_group.set_title(_("Laser Kerf & Offset Compensation"))
        kerf_group.set_description(
            _("Compensate for beam spot width so parts fit with exact clearance")
        )

        # Quick Kerf Presets
        presets_row = Adw.ActionRow(
            title=_("Laser Type Preset"),
            subtitle=_("Quick beam spot diameter presets"),
        )
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.set_valign(Gtk.Align.CENTER)

        btn_fiber = Gtk.Button(label=_("Fiber (0.05mm)"))
        btn_fiber.add_css_class("flat")
        btn_fiber.connect("clicked", lambda *_: self._set_kerf_value(0.05))
        btn_box.append(btn_fiber)

        btn_diode = Gtk.Button(label=_("Diode (0.12mm)"))
        btn_diode.add_css_class("flat")
        btn_diode.connect("clicked", lambda *_: self._set_kerf_value(0.12))
        btn_box.append(btn_diode)

        btn_co2 = Gtk.Button(label=_("CO2 (0.20mm)"))
        btn_co2.add_css_class("flat")
        btn_co2.connect("clicked", lambda *_: self._set_kerf_value(0.20))
        btn_box.append(btn_co2)

        presets_row.add_suffix(btn_box)
        kerf_group.add(presets_row)

        # Spot size / Kerf value
        kerf_adj = Gtk.Adjustment(
            lower=0.0, upper=5.0, step_increment=0.01, page_increment=0.05
        )
        self.kerf_spin = Adw.SpinRow(
            title=_("Kerf Diameter (mm)"),
            subtitle=_("Effective width of material vaporized by the laser beam"),
            adjustment=kerf_adj,
            digits=3,
        )
        kerf_adj.set_value(0.15)
        self.kerf_spin.connect("changed", self._on_kerf_changed)
        kerf_group.add(self.kerf_spin)

        # Cut Side
        cut_side_choices = [
            _("Outside (Male / Part Boundary)"),
            _("Inside (Female / Hole / Pocket)"),
            _("On Path (Centerline / Score)"),
        ]
        self.cut_side_row = Adw.ComboRow(
            title=_("Cut Side Compensation"),
            model=Gtk.StringList.new(cut_side_choices),
        )
        self.cut_side_row.set_selected(0)
        self.cut_side_row.connect("notify::selected", self._on_cut_side_changed)
        kerf_group.add(self.cut_side_row)

        # Overcut (clean dropout)
        overcut_adj = Gtk.Adjustment(
            lower=0.0, upper=10.0, step_increment=0.1, page_increment=0.5
        )
        self.overcut_row = Adw.SpinRow(
            title=_("Overcut (mm)"),
            subtitle=_("Extend contour cut past end to ensure clean part fallout"),
            adjustment=overcut_adj,
            digits=2,
        )
        self.overcut_row.connect("changed", self._on_overcut_changed)
        kerf_group.add(self.overcut_row)

        self.append(kerf_group)

        # ============================================================
        # 3. Holding Tabs (Bridges)
        # ============================================================
        tabs_group = Adw.PreferencesGroup()
        tabs_group.set_title(_("Holding Tabs (Bridges)"))
        tabs_group.set_description(
            _("Keep lightweight cut pieces connected to stock sheet")
        )

        tab_width_adj = Gtk.Adjustment(
            lower=0.2, upper=20.0, step_increment=0.2, page_increment=1.0
        )
        self.tab_width_row = Adw.SpinRow(
            title=_("Tab Width (mm)"),
            adjustment=tab_width_adj,
            digits=2,
        )
        tab_width_adj.set_value(1.5)
        tabs_group.add(self.tab_width_row)

        tab_actions_row = Adw.ActionRow(
            title=_("Generate Tabs"),
            subtitle=_("Place equidistant holding tabs on contour"),
        )
        btn_add_tabs = Gtk.Button(label=_("Add 4 Cardinal Tabs"))
        btn_add_tabs.set_action_name("win.add-tabs-cardinal")
        btn_add_tabs.set_valign(Gtk.Align.CENTER)
        tab_actions_row.add_suffix(btn_add_tabs)
        tabs_group.add(tab_actions_row)

        self.append(tabs_group)

        # ============================================================
        # 4. Lead-in / Lead-out
        # ============================================================
        lead_group = Adw.PreferencesGroup()
        lead_group.set_title(_("Lead-In / Lead-Out"))
        lead_group.set_description(
            _("Start piercing off-contour to eliminate burn pierce marks")
        )

        lead_type_choices = [_("None (Direct)"), _("Linear"), _("Arc (Smooth)")]
        self.lead_type_row = Adw.ComboRow(
            title=_("Lead-In Type"),
            model=Gtk.StringList.new(lead_type_choices),
        )
        self.lead_type_row.set_selected(0)
        lead_group.add(self.lead_type_row)

        lead_len_adj = Gtk.Adjustment(
            lower=0.0, upper=20.0, step_increment=0.5, page_increment=1.0
        )
        self.lead_len_row = Adw.SpinRow(
            title=_("Lead-In Length (mm)"),
            adjustment=lead_len_adj,
            digits=2,
        )
        lead_len_adj.set_value(2.0)
        lead_group.add(self.lead_len_row)

        self.append(lead_group)

    def _set_kerf_value(self, value: float) -> None:
        self.kerf_spin.set_value(value)
        self._apply_kerf_to_active_step(value)

    def on_selection_changed(self, selected_items: List[DocItem]) -> None:
        """Called when selection changes on the canvas."""
        self._selected_items = list(selected_items)
        if not self._selected_items:
            self.set_sensitive(False)
            return

        self.set_sensitive(True)
        self._update_geometry_fields()

    def _update_geometry_fields(self) -> None:
        if not self._selected_items or self._updating:
            return

        try:
            bbox = self.editor.transform.group_bbox_world(self._selected_items)
            min_x, min_y, max_x, max_y = bbox
            w = max(0.01, max_x - min_x)
            h = max(0.01, max_y - min_y)

            self._updating = True
            try:
                self.pos_x_row.set_value(min_x)
                self.pos_y_row.set_value(min_y)
                self.width_row.set_value(w)
                self.height_row.set_value(h)
            finally:
                self._updating = False
        except Exception as e:
            logger.debug(f"Failed to update CAD inspector fields: {e}")

    def _on_pos_x_changed(self, row: Adw.SpinRow) -> None:
        if self._updating or not self._selected_items:
            return
        new_x = row.get_value()
        try:
            bbox = self.editor.transform.group_bbox_world(self._selected_items)
            dx = new_x - bbox[0]
            if abs(dx) > 0.001:
                self.editor.transform.translate_items(
                    self._selected_items, delta_x=dx, delta_y=0.0
                )
        except Exception as e:
            logger.debug(f"Position X update: {e}")

    def _on_pos_y_changed(self, row: Adw.SpinRow) -> None:
        if self._updating or not self._selected_items:
            return
        new_y = row.get_value()
        try:
            bbox = self.editor.transform.group_bbox_world(self._selected_items)
            dy = new_y - bbox[1]
            if abs(dy) > 0.001:
                self.editor.transform.translate_items(
                    self._selected_items, delta_x=0.0, delta_y=dy
                )
        except Exception as e:
            logger.debug(f"Position Y update: {e}")

    def _on_width_changed(self, row: Adw.SpinRow) -> None:
        if self._updating or not self._selected_items:
            return
        new_w = row.get_value()
        try:
            bbox = self.editor.transform.group_bbox_world(self._selected_items)
            old_w = max(0.001, bbox[2] - bbox[0])
            scale_x = new_w / old_w
            scale_y = scale_x if self._aspect_locked else 1.0

            if self._aspect_locked:
                old_h = max(0.001, bbox[3] - bbox[1])
                self._updating = True
                try:
                    self.height_row.set_value(old_h * scale_y)
                finally:
                    self._updating = False

            center = self.editor.transform.group_center_world(self._selected_items)
            self.editor.transform.scale_items(
                self._selected_items, scale_x=scale_x, scale_y=scale_y, center=center
            )
        except Exception as e:
            logger.debug(f"Width update: {e}")

    def _on_height_changed(self, row: Adw.SpinRow) -> None:
        if self._updating or not self._selected_items:
            return
        new_h = row.get_value()
        try:
            bbox = self.editor.transform.group_bbox_world(self._selected_items)
            old_h = max(0.001, bbox[3] - bbox[1])
            scale_y = new_h / old_h
            scale_x = scale_y if self._aspect_locked else 1.0

            if self._aspect_locked:
                old_w = max(0.001, bbox[2] - bbox[0])
                self._updating = True
                try:
                    self.width_row.set_value(old_w * scale_x)
                finally:
                    self._updating = False

            center = self.editor.transform.group_center_world(self._selected_items)
            self.editor.transform.scale_items(
                self._selected_items, scale_x=scale_x, scale_y=scale_y, center=center
            )
        except Exception as e:
            logger.debug(f"Height update: {e}")

    def _on_rotation_changed(self, row: Adw.SpinRow) -> None:
        if self._updating or not self._selected_items:
            return
        angle_deg = row.get_value()
        try:
            center = self.editor.transform.group_center_world(self._selected_items)
            self.editor.transform.rotate_items(
                self._selected_items,
                angle_rad=math.radians(angle_deg),
                center=center,
            )
        except Exception as e:
            logger.debug(f"Rotation update: {e}")

    def _on_kerf_changed(self, row: Adw.SpinRow) -> None:
        self._apply_kerf_to_active_step(row.get_value())

    def _on_cut_side_changed(self, row: Adw.ComboRow, pspec) -> None:
        idx = row.get_selected()
        mapping = {0: "OUTSIDE", 1: "INSIDE", 2: "ON_PATH"}
        side_name = mapping.get(idx, "OUTSIDE")
        active_step = self._get_active_contour_step()
        if active_step and hasattr(active_step, "cut_side"):
            active_step.cut_side = side_name
            self.editor.pipeline.request_recomputation()

    def _on_overcut_changed(self, row: Adw.SpinRow) -> None:
        val = row.get_value()
        active_step = self._get_active_contour_step()
        if active_step and hasattr(active_step, "overcut"):
            active_step.overcut = val
            self.editor.pipeline.request_recomputation()

    def _get_active_contour_step(self):
        """Find contour step in current active layer."""
        try:
            layer = self.editor.doc.active_layer
            if not layer or not layer.workflow:
                return None
            for step in layer.workflow.steps:
                if "contour" in step.__class__.__name__.lower():
                    return step
        except Exception:
            pass
        return None

    def _apply_kerf_to_active_step(self, kerf_val: float) -> None:
        step = self._get_active_contour_step()
        if step:
            if hasattr(step, "kerf_mm"):
                step.kerf_mm = kerf_val
            elif hasattr(step, "path_offset_mm"):
                step.path_offset_mm = kerf_val / 2.0
            self.editor.pipeline.request_recomputation()
            logger.debug(f"Applied kerf {kerf_val}mm to {step}")
