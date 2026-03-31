import toml
from typing import Any
from pathlib import Path


def dump_from_pyproject(source: Path, dest: Path) -> None:
    pyproject: dict[str, Any]

    pyproject = toml.load(source / "pyproject.toml")

    manifest = {
        "name": pyproject["project"]["name"],
        "version": pyproject["project"]["version"],
        "deps": ((pyproject.get("tool") or {}).get("epk") or {}).get("dependencies") or [],
    }
    manifest["deps"].append("qubics-py")

    with open(dest / "manifest.toml", "w") as fp:
        toml.dump(manifest, fp)
