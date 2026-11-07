"""
Operations & Passes Timeline Widget for Blueforge.

Displays a horizontal / vertical sequence of laser passes (Engraving, Scoring,
Inner Cuts, Outer Contours) with visual ordering, power/speed badges,
and an intelligent auto-optimization button to guarantee safe cutting sequence.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Optional

from gi.repository import Gtk, Pango

from ...core.undo.list_cmd import ReorderListCommand
from ...core.workflow import Workflow
from ...shared.util.a11y import set_a11y_label
from ...shared.util.localized import _
from ..icons import get_icon

if TYPE_CHECKING:
    from ...core.step import Step
    from ...doceditor.editor import DocEditor

logger = logging.getLogger(__name__)


class OperationCard(Gtk.Box):
    """Visual card representing a single operation / pass in the timeline."""

    def __init__(
        self,
        step: "Step",
        pass_index: int,
        total_passes: int,
        on_move_up: Optional[Callable[[int], None]] = None,
        on_move_down: Optional[Callable[[int], None]] = None,
        **kwargs,
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=4, **kwargs
        )
        self.step = step
        self.pass_index = pass_index
        self.total_passes = total_passes
        self.add_css_class("card")
        self.add_css_class("operation-timeline-card")
        self.set_margin_start(4)
        self.set_margin_end(4)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        self.set_size_request(200, -1)

        self._build_ui(on_move_up, on_move_down)

    def _build_ui(self, on_move_up, on_move_down):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Pass number badge
        badge = Gtk.Label(
            label=_("Operation {number}").format(number=self.pass_index + 1)
        )
        badge.add_css_class("forge-statusbar-mode-badge")
        header_box.append(badge)

        # Operation icon & title
        icon_name = "cut-symbolic"
        step_type = self.step.__class__.__name__.lower()
        if "raster" in step_type or "engrave" in step_type:
            icon_name = "sketch-fill-symbolic"
        elif "score" in step_type:
            icon_name = "laser-path-symbolic"
        elif "frame" in step_type:
            icon_name = "frame-symbolic"

        icon = get_icon(icon_name)
        header_box.append(icon)

        step_name = getattr(self.step, "name", _("Operation"))
        name_label = Gtk.Label(label=step_name)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_hexpand(True)
        name_label.set_halign(Gtk.Align.START)
        header_box.append(name_label)

        # Reorder buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        if on_move_up:
            up_btn = Gtk.Button(child=get_icon("arrow-west-symbolic"))
            up_btn.add_css_class("flat")
            up_btn.set_tooltip_text(_("Move Earlier in Sequence"))
            up_btn.set_sensitive(self.pass_index > 0)
            up_btn.connect("clicked", lambda *_: on_move_up(self.pass_index))
            btn_box.append(up_btn)

        if on_move_down:
            down_btn = Gtk.Button(child=get_icon("arrow-east-symbolic"))
            down_btn.add_css_class("flat")
            down_btn.set_tooltip_text(_("Move Later in Sequence"))
            down_btn.set_sensitive(self.pass_index < self.total_passes - 1)
            down_btn.connect(
                "clicked", lambda *_: on_move_down(self.pass_index)
            )
            btn_box.append(down_btn)

        header_box.append(btn_box)
        self.append(header_box)

        # Telemetry / Parameters preview row
        param_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        param_box.set_margin_top(4)

        power_val = getattr(self.step, "power", None)
        speed_val = getattr(self.step, "cut_speed", None)

        info_text = []
        if power_val is not None:
            info_text.append(f"P: {power_val * 100:g}%")
        if speed_val is not None:
            info_text.append(f"F: {speed_val}mm/min")

        desc = " | ".join(info_text) if info_text else _("Standard Defaults")
        param_label = Gtk.Label(label=desc)
        param_label.add_css_class("forge-coord-mono")
        param_label.set_halign(Gtk.Align.START)
        param_box.append(param_label)

        self.append(param_box)


class OperationsTimelineWidget(Gtk.Box):
    """
    Timeline dock item visualizing all passes/operations in execution sequence.
    """

    def __init__(self, editor: "DocEditor", **kwargs) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=6, **kwargs
        )
        self.editor = editor
        self.add_css_class("operations-timeline")
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(6)
        self.set_margin_bottom(6)

        set_a11y_label(
            self,
            _("Operations Timeline"),
            role=Gtk.AccessibleRole.GROUP,
            description=_(
                "Execution timeline of laser passes "
                "from engraving to final contour"
            ),
        )

        self._build_header()
        self._build_scroll_area()
        self._document = None
        self._connect_signals()
        self.editor.document_changed.connect(self._on_document_changed)
        self.refresh()

    def _build_header(self) -> None:
        header_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.title_label = Gtk.Label(label=_("Execution Order Timeline"))
        self.title_label.add_css_class("heading")
        header_bar.append(self.title_label)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_bar.append(spacer)

        # Auto-Optimize Order Button
        btn_optimize = Gtk.Button(
            label=_("Sort Operations by Type"),
            child=None,
        )
        btn_optimize.set_tooltip_text(
            _(
                "Group engraving, scoring, and contour operations "
                "in this layer. "
                "Review toolpaths before sending to the machine."
            )
        )
        btn_optimize.connect("clicked", self._on_auto_optimize_clicked)
        header_bar.append(btn_optimize)

        self.append(header_bar)

    def _build_scroll_area(self) -> None:
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER
        )
        self.scrolled_window.set_vexpand(True)

        self.cards_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=8
        )
        self.cards_container.set_valign(Gtk.Align.CENTER)
        self.scrolled_window.set_child(self.cards_container)
        self.append(self.scrolled_window)

    @staticmethod
    def _document_signals(doc):
        return (
            doc.updated,
            doc.active_layer_changed,
            doc.descendant_added,
            doc.descendant_removed,
            doc.descendant_updated,
        )

    def _connect_signals(self) -> None:
        if self._document is not None:
            for signal in self._document_signals(self._document):
                signal.disconnect(self._on_model_changed)
        self._document = self.editor.doc
        for signal in self._document_signals(self._document):
            signal.connect(self._on_model_changed)

    def _on_model_changed(self, sender, **kwargs) -> None:
        self.refresh()

    def _on_document_changed(self, sender, **kwargs) -> None:
        self._connect_signals()
        self.refresh()

    def refresh(self) -> None:
        """Rebuilds the timeline cards from the active workflow."""
        # Clear existing cards
        while child := self.cards_container.get_first_child():
            self.cards_container.remove(child)

        workflow = self._get_active_workflow()
        if not workflow or not workflow.steps:
            self.title_label.set_label(_("Execution Order Timeline"))
            empty_lbl = Gtk.Label(
                label=_("No operations defined for this layer.")
            )
            empty_lbl.add_css_class("dim-label")
            empty_lbl.set_margin_start(16)
            self.cards_container.append(empty_lbl)
            return

        total_passes = len(workflow.steps)
        self.title_label.set_label(
            _("Execution Order ({total} operations)").format(
                total=total_passes
            )
        )

        for i, step in enumerate(workflow.steps):
            card = OperationCard(
                step=step,
                pass_index=i,
                total_passes=total_passes,
                on_move_up=self._on_move_step_up,
                on_move_down=self._on_move_step_down,
            )
            self.cards_container.append(card)

            # Add flow arrow between cards
            if i < total_passes - 1:
                arrow = get_icon("arrow-east-symbolic")
                arrow.add_css_class("dim-label")
                arrow.set_valign(Gtk.Align.CENTER)
                self.cards_container.append(arrow)

    def _get_active_workflow(self) -> Optional[Workflow]:
        layer = self.editor.doc.active_layer
        return layer.workflow if layer else None

    def _on_move_step_up(self, index: int) -> None:
        if index <= 0:
            return
        self._swap_steps(index, index - 1)

    def _on_move_step_down(self, index: int) -> None:
        workflow = self._get_active_workflow()
        if not workflow or index >= len(workflow.steps) - 1:
            return
        self._swap_steps(index, index + 1)

    def _swap_steps(self, i: int, j: int) -> None:
        workflow = self._get_active_workflow()
        if not workflow:
            return

        new_steps = list(workflow.steps)
        new_steps[i], new_steps[j] = new_steps[j], new_steps[i]

        setter_name = "set_steps" if hasattr(workflow, "set_steps") else None
        cmd = ReorderListCommand(
            target_obj=workflow,
            list_property_name="steps",
            new_list=new_steps,
            setter_method_name=setter_name,
            name=_("Reorder Operations"),
        )
        self.editor.history_manager.execute(cmd)
        self.refresh()

    def _on_auto_optimize_clicked(self, *args) -> None:
        """
        Sort steps by priority:
        1. Engraving / Raster (priority 10)
        2. Score / Marking (priority 20)
        3. Contour operations (priority 30)
        4. Other operations (priority 40)
        """
        workflow = self._get_active_workflow()
        if not workflow or len(workflow.steps) <= 1:
            return

        def _step_priority(step) -> int:
            name = step.__class__.__name__.lower()
            if "raster" in name or "engrave" in name:
                return 10
            elif "score" in name:
                return 20
            elif "contour" in name:
                return 30
            return 40

        sorted_steps = sorted(workflow.steps, key=_step_priority)
        if sorted_steps == workflow.steps:
            return
        setter_name = "set_steps" if hasattr(workflow, "set_steps") else None
        cmd = ReorderListCommand(
            target_obj=workflow,
            list_property_name="steps",
            new_list=sorted_steps,
            setter_method_name=setter_name,
            name=_("Sort Operations by Type"),
        )
        self.editor.history_manager.execute(cmd)
        self.refresh()
        logger.info(
            "Auto-optimized workflow steps sequence for laser cutting."
        )
