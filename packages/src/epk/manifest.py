import urllib.request
import tempfile
from epk.registry import LocalRegistry
from epk import registry
from epk.reference import Reference, TagReference, FileReference, ArtifactReference
from typing import NamedTuple
from pathlib import Path
import tomllib


class Manifest(NamedTuple):
    name: str
    version: str
    deps: list[str]


def parse_from_file(path: Path) -> Manifest:
    with open(path, "rb") as f:
        return Manifest(**tomllib.load(f))


def _latest_version(package_path: Path) -> Path | None:
    versions = sorted(
        (d for d in package_path.iterdir() if d.is_dir() and (d / "manifest.toml").exists()),
        key=lambda d: d.name,
    )
    return versions[-1] if versions else None


def parse_tag(tag: TagReference, *, env: LocalRegistry) -> Manifest | None:
    package_path = env.path / tag.name
    if not package_path.exists():
        return None

    if tag.version:
        mpath = registry.manifest_path(env, tag.name, tag.version)
        if not mpath.exists():
            return None
        return parse_from_file(mpath)

    version_path = _latest_version(package_path)
    if not version_path:
        return None
    return parse_from_file(version_path / "manifest.toml")


def parse_file(ref: FileReference) -> Manifest:
    return parse_from_file(ref)


def parse_artifact(ref: ArtifactReference) -> Manifest:
    url = ref.base + "/manifest.toml"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "manifest.toml"
        urllib.request.urlretrieve(url, str(path))
        return parse_from_file(path)


def parse(ref: Reference, **deps) -> Manifest | None:
    match ref:
        case TagReference():
            return parse_tag(ref, **deps)
        case FileReference():
            return parse_file(ref)
        case ArtifactReference():
            return parse_artifact(ref)
        case _:
            raise NotImplementedError()
