import os
from epk.lock import LockedPackage
from epk.registry import LocalRegistry
from epk import registry, fetch, build
from epk.reference import FileReference, GitReference, ArtifactReference
from typing import NamedTuple, TypeAlias
from pathlib import Path


class AlreadyBuilt(NamedTuple):
    name: str
    artifact: Path


class NeedsBuild(NamedTuple):
    name: str
    src: Path
    artifact: Path


class NeedsFetchSource(NamedTuple):
    name: str
    reference: FileReference | GitReference
    src: Path
    artifact: Path


class NeedsFetchArtifact(NamedTuple):
    name: str
    reference: ArtifactReference
    artifact: Path


type InstallPlan = AlreadyBuilt | NeedsBuild | NeedsFetchSource | NeedsFetchArtifact


class InstallSuccess(NamedTuple):
    link: Path


InstallFailure: TypeAlias = str


def plan(lock: LockedPackage, *, env: LocalRegistry, rebuild: bool = False) -> InstallPlan:
    match lock.reference:
        case ArtifactReference(_, platform):
            native = platform or env.native_platform
        case _:
            native = None

    art = registry.artifact_path(env, lock.name, lock.version, native)
    src = registry.src_path(env, lock.name, lock.version)

    if art.exists():
        if rebuild and src.exists() and build.needs_rebuild(src, art):
            return NeedsBuild(lock.name, src, art)
        return AlreadyBuilt(lock.name, art)

    if src.exists():
        return NeedsBuild(lock.name, src, art)

    registry.package_path(env, lock.name, lock.version).mkdir(
        parents=True, exist_ok=True
    )
    match lock.reference:
        case FileReference() | GitReference() as ref:
            return NeedsFetchSource(lock.name, ref, src, art)
        case ArtifactReference() as ref:
            return NeedsFetchArtifact(lock.name, ref, art)

    raise NotImplementedError(lock.name)


def _symlink(name: str, artifact: Path, target: Path) -> InstallFailure | InstallSuccess:
    if not artifact.exists():
        return "Artifact not found"

    link = target / name
    if link.is_symlink():
        if link.readlink() == artifact:
            return InstallSuccess(link)
        os.unlink(link)
    os.symlink(artifact, link)
    return InstallSuccess(link)


def rollback(result: InstallSuccess) -> None:
    if result.link.is_symlink():
        os.unlink(result.link)


def execute(p: InstallPlan, target: Path) -> InstallFailure | InstallSuccess:
    match p:
        case AlreadyBuilt(name, artifact):
            return _symlink(name, artifact, target)

        case NeedsBuild(name, src, artifact):
            return (build.build(src, artifact) or
                _symlink(name, artifact, target))

        case NeedsFetchSource(name, ref, src, artifact):
            return (fetch.fetch(ref, src) or 
                build.build(src, artifact) or
                _symlink(name, artifact, target))

        case NeedsFetchArtifact(name, ref, artifact):
            return (fetch.artifact(ref, artifact) or
                _symlink(name, artifact, target))

        case _:
            raise NotImplementedError()
