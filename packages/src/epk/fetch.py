import os
import subprocess
import tempfile
import tarfile
import urllib.request
from epk.reference import Reference, FileReference, GitReference, ArtifactReference
from pathlib import Path


def file(ref: FileReference, dest: Path) -> None:
    os.symlink(ref, dest)
    src_manifest = dest / "manifest.toml"
    if src_manifest.exists():
        os.link(src_manifest, dest.parent / "manifest.toml")


def git(ref: GitReference, dest: Path) -> None:
    subprocess.run(["git", "clone", str(ref), str(dest)], check=True)
    src_manifest = dest / "manifest.toml"
    if src_manifest.exists():
        os.link(src_manifest, dest.parent / "manifest.toml")


def artifact(ref: ArtifactReference, dest: Path) -> None:
    platform = ref.platform or dest.name
    url = f"{ref.base}/{platform}.tar.gz"
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "package.tar.gz"
        urllib.request.urlretrieve(url, str(archive))
        with tarfile.open(archive) as tf:
            tf.extractall(dest)

    manifest_url = f"{ref.base}/manifest.toml"
    urllib.request.urlretrieve(manifest_url, str(dest.parent / "manifest.toml"))


def fetch(ref: Reference, dest: Path) -> None:
    match ref:
        case FileReference():
            file(ref, dest)
        case GitReference():
            git(ref, dest)
        case ArtifactReference():
            artifact(ref, dest)
        case _:
            raise NotImplementedError()
