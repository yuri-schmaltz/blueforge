# Screenshots

This directory is where the
[Blueforge](https://github.com/yuri-schmaltz/blueforge) UI
screenshots used in the README and release notes are stored.

Blueforge is distributed without a website (the upstream
Rayforge website at <https://rayforge.org> is the documentation
for the original project, not the fork). Release notes on
GitHub are the primary channel for visual assets.

## Capturing screenshots

Blueforge uses GTK4 + Adwaita. To capture screenshots:

### Linux (Cinnamon, GNOME, KDE)

```bash
# Install a screenshot tool
sudo apt install gnome-screenshot

# Launch Blueforge
blueforge &

# Wait for the window to appear
sleep 3

# Capture
gnome-screenshot -w -f blueforge-main.png
```

### macOS

Press `⌘ + Shift + 4` and select the window. The screenshot is
saved to `~/Desktop`.

### Windows

Press `Win + Shift + S` to open the Snipping Tool. Select the
window. The screenshot is copied to the clipboard.

## Uploading to a release

Screenshots are usually attached to a GitHub release as part of
the release notes. The Blueforge maintainer curates these for
each tagged release.

To add a screenshot to the next release:

1. Capture the screenshot in the appropriate directory.
2. Commit it via PR (preferred for tracking) or include it in
   the release notes draft.
3. The maintainer will upload it to the GitHub release page.
