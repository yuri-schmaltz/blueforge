"""Constants for Blueforge application."""

APP_NAME = "Blueforge"
APP_NAME_SHORT = "blueforge"
MIME_TYPE_PROJECT = "application/x-blueforge-project"
MIME_TYPE_SKETCH = "application/x-blueforge-sketch"

# Blueforge is a rebrand / fork of the upstream Rayforge project. The
# upstream repository is kept as the source of bug reports and release
# metadata (since Blueforge is built from upstream and most user-facing
# bugs originate there), but the user-visible identity is "Blueforge".
#
# Update checks point to the FORK (yuri-schmaltz/blueforge), not
# upstream (barebaric/rayforge), because Blueforge is a separate
# distribution with its own release cadence. The version check is
# also off by default (see core/config.py) — users must opt in via
# Settings → Preferences.
GITHUB_RELEASES_API = (
    "https://api.github.com/repos/yuri-schmaltz/blueforge/releases/latest"
)
GITHUB_URL = "https://github.com/yuri-schmaltz/blueforge"
ISSUES_URL = "https://github.com/yuri-schmaltz/blueforge/issues"
DOWNLOAD_URL = (
    "https://github.com/yuri-schmaltz/blueforge/releases"
)
