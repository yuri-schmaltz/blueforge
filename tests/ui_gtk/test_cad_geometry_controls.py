"""Exercise CAD widget signals against real editor commands and undo."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from gi.repository import Adw

from rayforge.core.workpiece import WorkPiece
from rayforge.ui_gtk.cad.cad_inspector import CadInspectorTab
from rayforge.ui_gtk.cad.cad_ribbon import CadRibbon

pytestmark = pytest.mark.ui


@pytest.fixture
def cad(doc_editor):
    Adw.init()
    item = WorkPiece(name="Rectangle")
    item.set_size(10, 20)
    doc_editor.doc.active_layer.add_workpiece(item)
    ribbon = CadRibbon(
        SimpleNamespace(  # type: ignore[arg-type]
            doc_editor=doc_editor
        )
    )
    inspector = CadInspectorTab(doc_editor)
    ribbon.on_selection_changed([item])
    inspector.on_selection_changed([item])
    yield doc_editor, item, ribbon, inspector
    ribbon.on_selection_changed([])
    inspector.on_selection_changed([])


def test_ribbon_resize_updates_inspector_and_undo(cad):
    editor, item, ribbon, inspector = cad
    ribbon._width_spin.set_value(30)
    assert editor.transform.get_size_group([item]) == pytest.approx((30, 60))
    assert inspector.width_row.get_value() == pytest.approx(30)
    assert inspector.height_row.get_value() == pytest.approx(60)
    editor.history_manager.undo()
    assert editor.transform.get_size_group([item]) == pytest.approx((10, 20))
    assert ribbon._width_spin.get_value() == pytest.approx(10)
    assert inspector.height_row.get_value() == pytest.approx(20)


def test_inspector_position_uses_machine_coordinates(cad):
    editor, item, ribbon, inspector = cad
    with patch("rayforge.doceditor.transform_cmd.get_context") as context:
        context.return_value.machine = None
        inspector.pos_x_row.set_value(25)
        inspector.pos_y_row.set_value(35)
        assert editor.transform.get_position_group([item]) == pytest.approx(
            (25, 35)
        )


def test_rotation_is_absolute_and_undoable(cad):
    editor, item, ribbon, inspector = cad
    ribbon._angle_spin.set_value(30)
    ribbon._angle_spin.set_value(45)
    assert item.angle == pytest.approx(45)
    assert inspector.rot_row.get_value() == pytest.approx(45)
    editor.history_manager.undo()
    assert item.angle == pytest.approx(0)
    assert ribbon._angle_spin.get_value() == pytest.approx(0)


def test_unlocked_resize_and_disabled_unwired_controls(cad):
    editor, item, ribbon, inspector = cad
    ribbon._aspect_btn.set_active(False)
    ribbon._height_spin.set_value(35)
    assert editor.transform.get_size_group([item]) == pytest.approx((10, 35))
    assert not inspector.fillet_row.is_sensitive()
    assert not inspector.tab_width_row.is_sensitive()
    assert not inspector.lead_len_row.is_sensitive()


def test_contour_settings_notify_and_undo(cad):
    from laser_essentials.steps.contour_step import ContourStep

    editor, item, ribbon, inspector = cad
    step = ContourStep()
    editor.doc.active_layer.workflow.add_step(step)
    inspector.on_selection_changed([item])
    assert inspector.cut_side_row.get_selected() == 2
    initial_kerf = step.kerf_mm
    inspector.kerf_spin.set_value(0.12)
    assert step.kerf_mm == pytest.approx(0.12)
    editor.history_manager.undo()
    assert inspector.kerf_spin.get_value() == pytest.approx(initial_kerf)
    inspector.cut_side_row.set_selected(0)
    assert step.cut_side == "OUTSIDE"
    editor.history_manager.undo()
    assert step.cut_side == "CENTERLINE"
    assert inspector.cut_side_row.get_selected() == 2
    inspector.overcut_row.set_value(0.4)
    assert step.overcut == pytest.approx(0.4)
    editor.history_manager.undo()
    assert inspector.overcut_row.get_value() == pytest.approx(0)


def test_timeline_updates_on_model_edits_and_document_switch(cad):
    from laser_essentials.steps.contour_step import ContourStep
    from rayforge.core.doc import Doc
    from rayforge.ui_gtk.cad.operations_timeline import (
        OperationCard,
        OperationsTimelineWidget,
    )

    editor, item, ribbon, inspector = cad
    timeline = OperationsTimelineWidget(editor)
    step = ContourStep()
    editor.doc.active_layer.workflow.add_step(step)
    card = timeline.cards_container.get_first_child()
    assert isinstance(card, OperationCard)
    assert card.step is step
    editor.set_doc(Doc())
    assert ribbon._selected_items == []
    assert inspector._selected_items == []
    assert not isinstance(
        timeline.cards_container.get_first_child(), OperationCard
    )
    new_step = ContourStep()
    editor.doc.active_layer.workflow.add_step(new_step)
    new_card = timeline.cards_container.get_first_child()
    assert isinstance(new_card, OperationCard)
    assert new_card.step is new_step
