"""Build the root manuals and docs/ without copying source or build caches."""

from pathlib import Path
import shutil
import subprocess
import tempfile

import yaml


def main():
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "mkdocs.yml").read_text())
    with tempfile.TemporaryDirectory(prefix="blueforge-docs-") as temporary:
        staging = Path(temporary)
        content = staging / "content"
        content.mkdir()
        shutil.copytree(root / "docs", content / "docs")
        for source in root.glob("*.md"):
            shutil.copy2(source, content / source.name)
        shutil.copy2(root / "LICENSE", content / "LICENSE.md")
        shutil.copy2(root / "NOTICE", content / "NOTICE")
        shutil.copy2(root / "pyproject.toml", content / "pyproject.toml")
        for document in content.rglob("*.md"):
            text = document.read_text()
            text = text.replace("](LICENSE)", "](LICENSE.md)")
            text = text.replace("](../LICENSE)", "](../LICENSE.md)")
            text = text.replace(
                "](../.github/SECURITY.md)",
                "](https://github.com/yuri-schmaltz/blueforge/"
                "blob/main/.github/SECURITY.md)",
            )
            document.write_text(text)
        config["docs_dir"] = str(content)
        config["site_dir"] = str(root / "site")
        generated_config = staging / "mkdocs.yml"
        generated_config.write_text(yaml.safe_dump(config, sort_keys=False))
        subprocess.run(
            [
                "mkdocs",
                "build",
                "--strict",
                "--config-file",
                str(generated_config),
            ],
            cwd=root,
            check=True,
        )


if __name__ == "__main__":
    main()
