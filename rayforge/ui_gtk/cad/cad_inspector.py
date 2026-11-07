"""
Parametric CAD & Kerf Inspector Tab.

Provides direct access to geometric constraints, laser beam kerf compensation,
holding tabs placement, and lead-in/lead-out parameters.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from gi.repository import Adw, Gtk

from ...core.item import DocItem
from ...core.undo import ChangePropertyCommand
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
        self.set_sensitive(False)
        self._document = None
        self._bind_document()
        self.editor.document_changed.connect(self._on_document_changed)

    def _bind_document(self) -> None:
        if self._document is not None:
            for signal in self._step_signals(self._document):
                signal.disconnect(self._on_step_changed)
        self._document = self.editor.doc
        for signal in self._step_signals(self._document):
            signal.connect(self._on_step_changed)

    @staticmethod
    def _step_signals(doc):
        return (
            doc.active_layer_changed,
            doc.descendant_updated,
            doc.descendant_added,
            doc.descendant_removed,
        )

    def _on_document_changed(self, sender, **kwargs) -> None:
        self.on_selection_changed([])
        self._bind_document()

    def _on_step_changed(self, sender, **kwargs) -> None:
        self._update_step_fields()

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
            lower=-10000.0,
            upper=10000.0,
            step_increment=1.0,
            page_increment=10.0,
        )
        self.pos_x_row = Adw.SpinRow(
            title=_("X Position (mm)"), adjustment=x_adj, digits=2
        )
        self.pos_x_row.connect("notify::value", self._on_pos_x_changed)
        geom_group.add(self.pos_x_row)

        y_adj = Gtk.Adjustment(
            lower=-10000.0,
            upper=10000.0,
            step_increment=1.0,
            page_increment=10.0,
        )
        self.pos_y_row = Adw.SpinRow(
            title=_("Y Position (mm)"), adjustment=y_adj, digits=2
        )
        self.pos_y_row.connect("notify::value", self._on_pos_y_changed)
        geom_group.add(self.pos_y_row)

        # Width, Height
        w_adj = Gtk.Adjustment(
            lower=0.01, upper=10000.0, step_increment=1.0, page_increment=10.0
        )
        self.width_row = Adw.SpinRow(
            title=_("Width (mm)"), adjustment=w_adj, digits=2
        )
        self.width_row.connect("notify::value", self._on_width_changed)
        geom_group.add(self.width_row)

        h_adj = Gtk.Adjustment(
            lower=0.01, upper=10000.0, step_increment=1.0, page_increment=10.0
        )
        self.height_row = Adw.SpinRow(
            title=_("Height (mm)"), adjustment=h_adj, digits=2
        )
        self.height_row.connect("notify::value", self._on_height_changed)
        geom_group.add(self.height_row)

        # Rotation Angle
        rot_adj = Gtk.Adjustment(
            lower=-180.0, upper=180.0, step_increment=5.0, page_increment=15.0
        )
        self.rot_row = Adw.SpinRow(
            title=_("Rotation (deg)"), adjustment=rot_adj, digits=1
        )
        self.rot_row.connect("notify::value", self._on_rotation_changed)
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
        self.fillet_row.set_sensitive(False)
        self.fillet_row.set_subtitle(
            _("Edit corner geometry in the sketch editor")
        )
        geom_group.add(self.fillet_row)

        self.append(geom_group)

        # ============================================================
        # 2. Laser Kerf & Cut Offset
        # ============================================================
        kerf_group = Adw.PreferencesGroup()
        self._kerf_group = kerf_group
        kerf_group.set_title(_("Laser Kerf and Offset Compensation"))
        kerf_group.set_description(
            _(
                "Settings for the first contour operation in the active layer"
            )
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
            subtitle=_(
                "Effective width of material vaporized by the laser beam"
            ),
            adjustment=kerf_adj,
            digits=3,
        )
        kerf_adj.set_value(0.15)
        self.kerf_spin.connect("notify::value", self._on_kerf_changed)
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
        self.cut_side_row.connect(
            "notify::selected", self._on_cut_side_changed
        )
        kerf_group.add(self.cut_side_row)

        # Overcut (clean dropout)
        overcut_adj = Gtk.Adjustment(
            lower=0.0, upper=10.0, step_increment=0.1, page_increment=0.5
        )
        self.overcut_row = Adw.SpinRow(
            title=_("Overcut (mm)"),
            subtitle=_(
                "Extend contour cut past end to ensure clean part fallout"
            ),
            adjustment=overcut_adj,
            digits=2,
        )
        self.overcut_row.connect("notify::value", self._on_overcut_changed)
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
        self.tab_width_row.set_sensitive(False)
        self.tab_width_row.set_subtitle(
            _("Configure tab dimensions in item properties")
        )
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

        lead_type_choices = [
            _("None (Direct)"),
            _("Linear"),
            _("Arc (Smooth)"),
        ]
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

        lead_group.set_sensitive(False)
        lead_group.set_description(
            _("Not yet connected to the toolpath pipeline")
        )
        self.append(lead_group)

    def _set_kerf_value(self, value: float) -> None:
        self.kerf_spin.set_value(value)

    def on_selection_changed(self, selected_items: List[DocItem]) -> None:
        """Called when selection changes on the canvas."""
        for item in self._selected_items:
            item.transform_changed.disconnect(self._on_transform_changed)
        self._selected_items = list(selected_items)
        for item in self._selected_items:
            item.transform_changed.connect(self._on_transform_changed)
        if not self._selected_items:
            self.set_sensitive(False)
            return

        self.set_sensitive(True)
        self._update_geometry_fields()
        self._update_step_fields()

    def _on_transform_changed(self, sender, **kwargs) -> None:
        self._update_geometry_fields()

    def _update_step_fields(self) -> None:
        step = self._get_active_contour_step()
        self._kerf_group.set_sensitive(step is not None)
        for widget in (self.kerf_spin, self.cut_side_row, self.overcut_row):
            widget.set_sensitive(step is not None)
        if step is None:
            return
        self._updating = True
        try:
            self.kerf_spin.set_value(step.kerf_mm)
            sides = {"OUTSIDE": 0, "INSIDE": 1, "CENTERLINE": 2}
            self.cut_side_row.set_selected(
                sides.get(getattr(step, "cut_side", "CENTERLINE"), 2)
            )
            self.overcut_row.set_value(getattr(step, "overcut", 0.0))
        finally:
            self._updating = False

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
                position = self.editor.transform.get_position_group(
                    self._selected_items
                )
                if position is None:
                    return
                x, y = position
                self.pos_x_row.set_value(x)
                self.pos_y_row.set_value(y)
                self.rot_row.set_value(
                    self.editor.transform.get_angle_group(self._selected_items)
                    or 0.0
                )
                self.width_row.set_value(w)
                self.height_row.set_value(h)
            finally:
                self._updating = False
        except Exception as e:
            logger.debug(f"Failed to update CAD inspector fields: {e}")

    def _on_pos_x_changed(self, row: Adw.SpinRow, pspec=None) -> None:
        if self._updating or not self._selected_items:
            return
        position = self.editor.transform.get_position_group(
            self._selected_items
        )
        if position is None:
            return
        _, y = position
        self.editor.transform.set_position_group(
            self._selected_items, row.get_value(), y
        )
        self._update_geometry_fields()

    def _on_pos_y_changed(self, row: Adw.SpinRow, pspec=None) -> None:
        if self._updating or not self._selected_items:
            return
        position = self.editor.transform.get_position_group(
            self._selected_items
        )
        if position is None:
            return
        x, _ = position
        self.editor.transform.set_position_group(
            self._selected_items, x, row.get_value()
        )
        self._update_geometry_fields()

    def _on_width_changed(self, row: Adw.SpinRow, pspec=None) -> None:
        if self._updating or not self._selected_items:
            return
        self.editor.transform.set_size_group(
            self._selected_items,
            width=row.get_value(),
            fixed_ratio=self._aspect_locked,
        )
        self._update_geometry_fields()

    def _on_height_changed(self, row: Adw.SpinRow, pspec=None) -> None:
        if self._updating or not self._selected_items:
            return
        self.editor.transform.set_size_group(
            self._selected_items,
            height=row.get_value(),
            fixed_ratio=self._aspect_locked,
        )
        self._update_geometry_fields()

    def _on_rotation_changed(self, row: Adw.SpinRow, pspec=None) -> None:
        if self._updating or not self._selected_items:
            return
        self.editor.transform.set_angle_group(
            self._selected_items, row.get_value()
        )
        self._update_geometry_fields()

    def _on_kerf_changed(self, row: Adw.SpinRow, pspec=None) -> None:
        self._apply_kerf_to_active_step(row.get_value())

    def _on_cut_side_changed(self, row: Adw.ComboRow, pspec) -> None:
        mapping = {0: "OUTSIDE", 1: "INSIDE", 2: "CENTERLINE"}
        self._set_contour_property(
            "cut_side", mapping[row.get_selected()], _("Change cut side")
        )

    def _on_overcut_changed(self, row: Adw.SpinRow, pspec=None) -> None:
        self._set_contour_property(
            "overcut", row.get_value(), _("Change overcut")
        )

    def _set_contour_property(self, key, value, name) -> None:
        if self._updating:
            return
        step = self._get_active_contour_step()
        if step is None or getattr(step, key) == value:
            return

        def notify_step() -> None:
            step.updated.send(step)

        setter = f"set_{key}"
        self.editor.history_manager.execute(
            ChangePropertyCommand(
                target=step,
                property_name=key,
                new_value=value,
                setter_method_name=setter if hasattr(step, setter) else None,
                on_change_callback=(
                    None if hasattr(step, setter) else notify_step
                ),
                name=name,
            )
        )

    def _get_active_contour_step(self):
        """Find contour step in current active layer."""
        layer = self.editor.doc.active_layer
        if layer is None or layer.workflow is None:
            return None
        return next(
            (
                step
                for step in layer.workflow.steps
                if step.ASSEMBLER_NAME == "contour"
            ),
            None,
        )

    def _apply_kerf_to_active_step(self, kerf_val: float) -> None:
        self._set_contour_property(
            "kerf_mm", kerf_val, _("Change kerf diameter")
        )
