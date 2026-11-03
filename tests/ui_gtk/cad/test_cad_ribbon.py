"""Unit tests for CadRibbon."""

from unittest.mock import MagicMock
from rayforge.ui_gtk.cad.cad_ribbon import CadRibbon


def test_cad_ribbon_initialization():
    win = MagicMock()
    ribbon = CadRibbon(win)
    assert ribbon._btn_align_left is not None
    assert ribbon._btn_group is not None
    assert ribbon._aspect_locked is True


def test_cad_ribbon_sensitivity_per_selection_count():
    win = MagicMock()
    ribbon = CadRibbon(win)

    # 0 items selected
    ribbon.on_selection_changed([])
    assert ribbon._btn_align_left.get_visible() is True
    assert ribbon._width_spin._sensitive is False
    assert ribbon._btn_group._sensitive is False
    assert ribbon._btn_spread_h._sensitive is False

    # 1 item selected
    item1 = MagicMock()
    ribbon.on_selection_changed([item1])
    assert ribbon._width_spin._sensitive is True
    assert ribbon._btn_align_left._sensitive is True
    assert ribbon._btn_group._sensitive is False
    assert ribbon._btn_spread_h._sensitive is False

    # 2 items selected
    item2 = MagicMock()
    ribbon.on_selection_changed([item1, item2])
    assert ribbon._btn_group._sensitive is True
    assert ribbon._btn_spread_h._sensitive is False

    # 3 items selected
    item3 = MagicMock()
    ribbon.on_selection_changed([item1, item2, item3])
    assert ribbon._btn_spread_h._sensitive is True


def test_cad_ribbon_aspect_ratio_toggle():
    win = MagicMock()
    ribbon = CadRibbon(win)
    assert ribbon._aspect_locked is True

    btn = ribbon._aspect_btn
    btn.get_active = MagicMock(return_value=False)
    ribbon._on_aspect_toggled(btn)
    assert ribbon._aspect_locked is False

    btn.get_active = MagicMock(return_value=True)
    ribbon._on_aspect_toggled(btn)
    assert ribbon._aspect_locked is True
