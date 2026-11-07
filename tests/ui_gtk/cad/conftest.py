"""Initialize real GTK without replacing global widget classes."""

import pytest
from gi.repository import Adw, Gdk


@pytest.fixture(autouse=True)
def gtk_display():
    Adw.init()
    if Gdk.Display.get_default() is None:
        pytest.skip("CAD widget tests require a display (use xvfb-run).")
