"""Verify the first-run tour uses the available Adwaita dialog API."""

import time

import pytest
from gi.repository import Adw, GLib, Gtk

from rayforge.ui_gtk.walkthrough import WalkthroughDialog

pytestmark = pytest.mark.ui


def wait_until(predicate):
    context = GLib.MainContext.default()
    deadline = time.monotonic() + 2
    while not predicate() and time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        time.sleep(0.01)
    assert predicate()


def test_walkthrough_navigation_and_skip():
    Adw.init()
    settings = Gtk.Settings.get_default()
    assert settings is not None
    animations = settings.get_property("gtk-enable-animations")
    settings.set_property("gtk-enable-animations", False)
    parent = Gtk.Window()
    tour = WalkthroughDialog()
    try:
        parent.present()
        tour.present(parent)
        wait_until(lambda: tour._carousel.get_width() > 0)
        tour._on_next()
        wait_until(lambda: tour._carousel.get_position() == pytest.approx(1))
        tour._on_back()
        wait_until(lambda: tour._carousel.get_position() == pytest.approx(0))
        tour.set_can_close(False)
        tour.skip()
        wait_until(lambda: tour.get_parent() is None)
    finally:
        tour.force_close()
        parent.destroy()
        settings.set_property("gtk-enable-animations", animations)
