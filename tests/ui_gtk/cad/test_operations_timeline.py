"""Unit tests for OperationsTimelineWidget."""

from unittest.mock import MagicMock
from rayforge.ui_gtk.cad.operations_timeline import (
    OperationCard,
    OperationsTimelineWidget,
)


class MockRasterStep:
    name = "Engrave Text"
    power = 30
    speed = 250
    passes = 1


class MockContourStep:
    name = "Outer Cut"
    power = 100
    speed = 15
    passes = 2


class MockScoreStep:
    name = "Score Fold Lines"
    power = 20
    speed = 100
    passes = 1


def test_operation_card_initialization():
    step = MockContourStep()
    card = OperationCard(step, pass_index=0, total_passes=2)
    assert card.pass_index == 0
    assert card.total_passes == 2
    assert card.step == step


def test_operations_timeline_refresh():
    editor = MagicMock()
    workflow = MagicMock()
    workflow.steps = [MockRasterStep(), MockContourStep()]
    editor.doc.active_layer.workflow = workflow

    timeline = OperationsTimelineWidget(editor)
    assert len(timeline.cards_container._children) > 0


def test_operations_timeline_reordering():
    editor = MagicMock()
    workflow = MagicMock()
    step1 = MockRasterStep()
    step2 = MockContourStep()
    workflow.steps = [step1, step2]
    editor.doc.active_layer.workflow = workflow

    timeline = OperationsTimelineWidget(editor)

    # Move step 1 down
    timeline._on_move_step_down(0)
    assert editor.history_manager.execute.called
    reorder_cmd = editor.history_manager.execute.call_args[0][0]
    assert reorder_cmd.new_list == [step2, step1]


def test_operations_timeline_auto_optimize():
    editor = MagicMock()
    workflow = MagicMock()
    # Initial suboptimal order: Outer cut before raster and score
    outer_cut = MockContourStep()
    raster = MockRasterStep()
    score = MockScoreStep()
    workflow.steps = [outer_cut, raster, score]
    editor.doc.active_layer.workflow = workflow

    timeline = OperationsTimelineWidget(editor)
    timeline._on_auto_optimize_clicked()

    assert editor.history_manager.execute.called
    reorder_cmd = editor.history_manager.execute.call_args[0][0]
    # Optimal sequence: raster (10) -> score (20) -> contour (30/40)
    assert reorder_cmd.new_list == [raster, score, outer_cut]
