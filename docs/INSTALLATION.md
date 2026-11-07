# Installing Blueforge

Blueforge is distributed as a `.deb` (Ubuntu), `.dmg` (macOS), and
`.exe` (Windows) from the
[Releases page](https://github.com/yuri-schmaltz/blueforge/releases).

## Linux (`.deb` for Ubuntu 24.04 / Linux Mint 22.x)

The `.deb` is built for Ubuntu 24.04 (Noble) and compatible
distributions. Linux Mint 22.x (which is Ubuntu 24.04-based) is
the primary supported target.

### Install

```bash
sudo apt install /path/to/blueforge-linux.deb
blueforge
```

This installs:

- `/usr/bin/blueforge` — the binary
- `/usr/share/applications/org.blueforge.blueforge.desktop` —
  menu entry (in category **Graphics**)
- `/usr/share/metainfo/org.blueforge.blueforge.metainfo.xml` —
  AppStream metadata
- `/usr/share/icons/hicolor/scalable/apps/org.blueforge.blueforge.svg` —
  app icon
- `/usr/share/mime/packages/org.blueforge.blueforge.xml` —
  MIME type registration (`.ryp`, `.rfs`)
- Python modules under `/usr/lib/python3/dist-packages/rayforge/`

### Upgrade from an older release

The Debian package was renamed from `rayforge` to `blueforge`
during the rebrand. To upgrade:

```bash
sudo apt remove rayforge  # or blueforge, whichever is installed
sudo apt install /path/to/blueforge-linux.deb
```

Your config and addon data in `~/.config/rayforge/` is preserved
(the config directory keeps the `rayforge` name for compatibility
with the Python module path).

### Refresh menu and icon caches

After installing or upgrading, run:

```bash
sudo update-desktop-database
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor
```

Then log out and back in. The app should appear in
**Menu → Graphics → Blueforge**.

## macOS (`.dmg`)

macOS packages are built locally. Check the release asset architecture;
the current Pixi configuration targets Apple Silicon (ARM64).

1. Open `blueforge-macos.dmg`.
2. Drag **Blueforge.app** to **/Applications**.
3. Open **Blueforge** from Launchpad or `/Applications`.

The first launch may require you to allow the app in
**System Settings → Privacy & Security** because the binary is not
notarized with an Apple Developer ID.

To uninstall, drag `Blueforge.app` from `/Applications` to the
Trash.

## Windows (`.exe`)

The `.exe` is an NSIS installer.

1. Run `blueforge-v1.0.0-installer.exe` (or whichever version you
   downloaded).
2. Accept the license and choose the install location.
3. The Start Menu entry is under **Blueforge**.

The installer puts files in `C:\Program Files\Blueforge\` by
default. To uninstall, use **Control Panel → Programs → Uninstall**.

## After installation

Once installed, see [BUILDING.md](BUILDING.md) if you want to
build from source, or [SUPPORT.md](../SUPPORT.md) for
troubleshooting.

## Source tarball

If you want to install from source, see [BUILDING.md](BUILDING.md)
for build instructions. The project uses [pixi](https://pixi.sh)
for reproducible development environments and is tested on Linux,
macOS, and Windows.
