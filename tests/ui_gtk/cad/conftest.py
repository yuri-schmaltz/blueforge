"""Mock GTK 4 and Libadwaita base classes for headless testing."""

import sys
from unittest.mock import MagicMock

# Base mock widgets
class MockWidget:
    def __init__(self, *args, **kwargs):
        self._children = []
        self._visible = True
        self._sensitive = True
        self._callbacks = {}
        self._active = False

    def append(self, child):
        self._children.append(child)

    def remove(self, child):
        if child in self._children:
            self._children.remove(child)

    def get_first_child(self):
        return self._children[0] if self._children else None

    def add_css_class(self, cls):
        pass

    def set_margin_start(self, v):
        pass

    def set_margin_end(self, v):
        pass

    def set_margin_top(self, v):
        pass

    def set_margin_bottom(self, v):
        pass

    def set_valign(self, v):
        pass

    def set_halign(self, v):
        pass

    def set_size_request(self, w, h):
        pass

    def set_sensitive(self, s):
        self._sensitive = s

    def set_visible(self, v):
        self._visible = v

    def get_visible(self):
        return self._visible

    def set_child(self, c):
        pass

    def set_tooltip_text(self, t):
        pass

    def set_action_name(self, n):
        pass

    def set_active(self, a):
        self._active = a

    def get_active(self):
        return self._active

    def connect(self, sig, cb, *args):
        self._callbacks.setdefault(sig, []).append((cb, args))

    def connect_unit_changed(self, cb):
        pass

    def set_label(self, label):
        pass

    def set_ellipsize(self, e):
        pass

    def set_hexpand(self, h):
        pass

    def set_vexpand(self, v):
        pass

    def set_policy(self, h, v):
        pass

    @classmethod
    def new(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def new_with_range(cls, min_val, max_val, step):
        w = cls()
        w._min_val = min_val
        w._max_val = max_val
        w._step = step
        return w

    def set_digits(self, d):
        pass

    def set_width_chars(self, c):
        pass

    def set_value(self, v):
        self._value = v

    def get_value(self):
        return getattr(self, "_value", 0.0)

    def set_selected(self, s):
        self._selected = s

    def get_selected(self):
        return getattr(self, "_selected", 0)

    def set_title(self, t):
        pass

    def set_description(self, d):
        pass

    def add(self, row):
        self._children.append(row)

    def add_suffix(self, s):
        pass


class MockOrientation:
    HORIZONTAL = 0
    VERTICAL = 1


class MockAlign:
    START = 0
    CENTER = 1
    END = 2
    FILL = 3


class MockPolicy:
    NEVER = 0
    AUTOMATIC = 1


class MockAccessibleRole:
    TOOLBAR = "toolbar"
    BUTTON = "button"
    TOGGLE_BUTTON = "toggle_button"
    GROUP = "group"
    LABEL = "label"
    TEXT_BOX = "text_box"
    CHECKBOX = "checkbox"
    PROGRESS_BAR = "progress_bar"
    SEPARATOR = "separator"
    TAB = "tab"
    TAB_PANEL = "tab_panel"
    STATUS = "status"
    DIALOG = "dialog"
    IMG = "img"
    REGION = "region"


if "gi" in sys.modules:
    gi_repo = sys.modules.get("gi.repository")
    if gi_repo and hasattr(gi_repo, "Gtk"):
        gtk = gi_repo.Gtk
        gtk.Box = MockWidget
        gtk.Button = MockWidget
        gtk.ToggleButton = MockWidget
        gtk.Label = MockWidget
        gtk.Separator = MockWidget
        gtk.ScrolledWindow = MockWidget
        gtk.SpinButton = MockWidget
        gtk.Adjustment = MockWidget
        gtk.StringList = MockWidget
        gtk.Orientation = MockOrientation
        gtk.Align = MockAlign
        gtk.PolicyType = MockPolicy
        gtk.AccessibleRole = MockAccessibleRole

        gio = getattr(gi_repo, "Gio", MagicMock())
        gio.Icon = type("MockIcon", (), {})
        gio.File = type("MockFile", (), {})
        gi_repo.Gio = gio

        adw = getattr(gi_repo, "Adw", MagicMock())
        adw.PreferencesGroup = MockWidget
        adw.ActionRow = MockWidget
        adw.SpinRow = MockWidget
        adw.ComboRow = MockWidget
        gi_repo.Adw = adw
