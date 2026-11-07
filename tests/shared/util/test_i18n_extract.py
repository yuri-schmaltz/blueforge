"""Catalog checks must be reproducible and leave tracked files untouched."""

import shutil
import sys

import pytest

from rayforge.util.i18n_extract import extract_pot, main


@pytest.mark.skipif(
    shutil.which("xgettext") is None or shutil.which("msgmerge") is None,
    reason="gettext tools are required",
)
def test_check_catalog_is_non_mutating_and_detects_new_strings(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "rayforge" / "widget.py"
    source.parent.mkdir()
    source.write_text('label = _("A translated label")\n')
    catalog = source.parent / "locale" / "rayforge.pot"
    catalog.parent.mkdir()
    extract_pot(tmp_path, catalog)
    original = catalog.read_bytes()
    monkeypatch.setattr(sys, "argv", ["i18n_extract", "--check"])
    assert main() == 0
    assert catalog.read_bytes() == original
    source.write_text('label = _("A new translated label")\n')
    assert main() == 2
    assert catalog.read_bytes() == original
