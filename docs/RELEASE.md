# Release process

The repository is [yuri-schmaltz/blueforge](https://github.com/yuri-schmaltz/blueforge).
The product and installed package retain the name Blueforge. Releases use
MIT licensing and preserve the Rayforge attribution in LICENSE and NOTICE.

## Prepare a release

1. Run `pixi install --locked`, `pixi run --frozen test`,
   `pixi run --frozen uitest`, `pixi run --frozen lint` and
   `pixi run --frozen coverage`. Inspect all failures before publishing.
2. Run `pixi run --frozen -e docs docs-build`.
3. Update `SOURCE_VERSION` in `rayforge/version.py` and the entry in
   `CHANGELOG.md`. Python package metadata reads this value through
   `[tool.setuptools.dynamic]`; do not add a second static version to
   `pyproject.toml` or `const.py`. Regenerate the catalog with
   `pixi run --frozen python -m rayforge.util.i18n_extract --no-merge`
   after changing the version, and review the resulting template.
4. Update `debian/changelog` for the release. Debian packaging replaces
   the dynamic Python metadata and writes `rayforge/version.txt` in its
   temporary source tree using the Debian package version.
5. Review and commit the release changes. Create an annotated tag
   `vX.Y.Z` on the intended commit and push it when ready to publish.
   Never move an already published release tag; issue a new patch version.

## Automated builds

- `build-deb.yml` builds Ubuntu 24.04 packages on main, tags and PRs.
- `build-exe.yml` builds the Windows installer; consult its triggers and
  optional inputs for the exact release run.
- `release.yml` coordinates Linux and Windows build artifacts and creates
  the GitHub release. Inspect its logs for missing artifacts and attach
  only installers built from the release commit.
- macOS is built locally with `bash scripts/mac/mac_build.sh`; there is
  no `build-macos-universal.yml` workflow. The Pixi macOS target is ARM64;
  do not label a build universal without testing both architectures.
- Documentation is built by `website.yml` and uploaded as a preview
  artifact. It does not deploy to the former Blueforge website.

## Local packaging

```bash
pixi run --frozen build-deb
bash scripts/mac/mac_build.sh
# In an initialized MSYS2 environment:
bash scripts/win/win_build.sh vX.Y.Z
```

See [BUILDING.md](BUILDING.md) for prerequisites. Installer filenames are
chosen by the build scripts and workflows; use the generated artifact
names rather than assuming a fixed three-platform filename scheme.
`rayforge/version.txt` is a generated bundle override and is not committed.

## Verify the published release

Check the release under this repository's Releases page. Confirm that the
tag points at the reviewed commit, download and install each attached
artifact on its target platform, and test startup, import, save/reopen,
simulation and machine connection. Confirm the displayed version, desktop
entry and translations. Record which platforms and hardware were tested;
build success alone is not evidence of hardware validation.

If a release is broken, publish a new patch release with a new tag and
explain the affected version in the changelog.
