from pathlib import Path
from typing import NamedTuple


class GitReference(str):
    pass


class FileReference(Path):
    pass


class ArtifactReference(NamedTuple):
    base: str
    platform: str | None = None


class TagReference(NamedTuple):
    name: str
    version: str | None = None
    artifact: str | None = None


type Reference = GitReference | FileReference | ArtifactReference | TagReference


def parse(source: str) -> Reference:
    if source.startswith("git:"):
        return GitReference()

    elif source.startswith("file:"):
        path = Path(source).resolve()
        if path.is_dir():
            path = path / "manifest.toml"
        return FileReference(path)

    elif "://" in source:
        if source.endswith(".tar.gz"):
            base, filename = source.rsplit("/", 1)
            platform = filename.removesuffix(".tar.gz")
            return ArtifactReference(base, platform)
        return ArtifactReference(source.rstrip("/"))

    else:
        parts = source.split("/")
        return TagReference(*parts)

def serialize(reference: Reference) -> str:
    match reference:
        case GitReference():
            return reference
        case ArtifactReference(base, platform) if platform:
            return f"{base}/{platform}.tar.gz"
        case ArtifactReference(base, _):
            return base
        case FileReference():
            return f"file://{reference}"
        case TagReference(name, version, platform):
            return f"{name}/{version or ""}/{platform or ""}"
