# Building Blueforge from Source

Blueforge uses [pixi](https://pixi.sh) for reproducible development
environments and produces native installers for Linux (`.deb`),
macOS (`.dmg`), and Windows (`.exe`).

## Python version

The project targets **Python 3.12** (the system Python in
Ubuntu 24.04, which is the build target for the `.deb`). The
declared lower bound in `pyproject.toml` is `>=3.10` to keep
development on 3.11/3.13 viable, but the CI and the `.deb` are
built and tested against 3.12.

## Prerequisites

- [pixi](https://pixi.sh) (recommended; handles all dependencies)
- On Linux: `dpkg-buildpackage`, `devscripts`, `fakeroot`
- On macOS: Xcode command line tools, `create-dmg`
- On Windows: MSYS2 with `mingw-w64`, NSIS

## Quick start

```bash
# Clone the repository
git clone https://github.com/yuri-schmaltz/blueforge.git
cd blueforge

# Install the pixi environment
pixi install --locked

# Run the app
pixi run blueforge
```

The Pixi manifest supports Linux x86_64 and macOS ARM64. The macOS
script builds for the host architecture; universal Intel + ARM64 output
is not provided by the current CI. Windows builds use MSYS2.

## Running tests

```bash
pixi run --frozen test
```

## Building packages

### Linux (.deb for Ubuntu 24.04)

```bash
./scripts/build-deb.sh
```

The output is written to `dist/`. The script vendors Python wheel
dependencies for ABI compatibility with the target distribution.

### macOS (.dmg, local build)

```bash
./scripts/mac/mac_build.sh
```

### Windows (.exe NSIS installer)

```bash
# From an initialized MSYS2 shell
bash scripts/win/win_build.sh
```

## Cross-platform notes

- The Python module path is `rayforge/` (intentionally kept
  identical to the upstream Rayforge project for addon compatibility).
- The user-facing binary name is `blueforge` (set via
  `[project.gui-scripts]` in `pyproject.toml`).
- The build scripts use the tag name to set the version. To produce
  a release, create and push a tag like `v1.0.0`. See
  [`RELEASE.md`](RELEASE.md) for the full release process.

## Adding a new device

Blueforge uses a plugin system for device drivers. See the addon
documentation at
[`rayforge/builtin_addons/rayforge-addon-laser/`](https://github.com/yuri-schmaltz/blueforge/tree/main/rayforge/builtin_addons/rayforge-addon-laser)
for examples.

## CI/CD

The repository includes GitHub Actions workflows under
[`.github/workflows/`](https://github.com/yuri-schmaltz/blueforge/tree/main/.github/workflows) for:

- Building `.deb` and `.exe` packages on tag push (macOS is built locally)
- Lint, test, and security gates on every push
- Generating release notes

For the end-to-end release process (changelog, version bump,
tag push, post-release verification), see
[`RELEASE.md`](RELEASE.md).

## Troubleshooting

- If `pixi install` fails with a lockfile mismatch, run
  `pixi lock` to refresh it, review the diff, then `pixi install --locked`.
- If the `.deb` build fails with `dpkg-source: error: source
  package has two conflicting values`, the `debian/changelog`
  header does not match `Source:` in `debian/control`.
- For NSIS packaging issues on Windows, see
  [`CODE_SIGNING.md`](CODE_SIGNING.md).
