from gi.repository import Adw


class BasePreferencesPage(Adw.PreferencesPage):
    """Base class for the app's Adw.PreferencesPage subclasses.

    It exists so the settings pages share a single import target
    and a common place to hang future shared behaviour.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
