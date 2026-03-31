from tempfile import TemporaryDirectory
import functools
from epk.install import InstallSuccess
import logging
import shutil
import time
from pathlib import Path
from typing import NamedTuple

from epk.registry import LocalRegistry
from epk.reference import Reference, FileReference
from epk.lock import LockedPackage

from epk import (
    reference as references_mod,
    manifest as manifest_mod,
    resolve as resolve_mod,
    install as install_mod,
    registry as registry_mod,
    fetch as fetch_mod,
    build as build_mod,
)

log = logging.getLogger(__name__)


def lock(manifest_path: Path, lock_path: Path, *, env: LocalRegistry) -> list[LockedPackage]:
    class _ResolvedManifest(NamedTuple):
        name: str
        version: str
        deps: list[str]
        reference: Reference

    def transform(name: str) -> _ResolvedManifest:
        log.debug("resolving manifest for: %s", name)
        reference = references_mod.parse(name)
        m = manifest_mod.parse(reference, env=env)
        if not m:
            raise Exception(f"could not resolve manifest for: {name}")
        log.debug("resolved %s -> %s@%s (deps: %s)", name, m.name, m.version, m.deps)
        return _ResolvedManifest(*m, reference=reference)

    log.info("locking %s", manifest_path)
    root = manifest_mod.parse_from_file(manifest_path)
    log.debug("root manifest: %s@%s, deps: %s", root.name, root.version, root.deps)
    manifests = resolve_mod.traverse(transform, root.deps)
    locked = [LockedPackage(m.name, m.version, m.reference) for m in manifests]
    log.info("locked %d package(s): %s", len(locked), [f"{p.name}@{p.version}" for p in locked])
    return locked


def install(locks: list[LockedPackage], build_path: Path, *, env: LocalRegistry):
    log.info("installing %d package(s) to %s", len(locks), build_path)
    build_path.mkdir(parents=True, exist_ok=True)

    plans = [install_mod.plan(lock, env=env) for lock in locks]
    installs = []
    for plan in plans:
        log.debug("executing plan: %s", plan)
        result = install_mod.execute(plan, build_path)
        if isinstance(result, InstallSuccess):
            log.debug("installed: %s", result)
            installs.append(result)
        else:
            log.error("install failed: %s", result)
            break
    else:
        log.info("all packages installed successfully")
        return

    log.warning("rolling back %d successful install(s)", len(installs))
    for install in installs:
        install_mod.rollback(install)
    raise Exception(result)


def add(target_path: Path, *, env: LocalRegistry) -> None:
    log.info("adding package from %s", target_path)
    manifest = manifest_mod.parse_from_file(target_path / "manifest.toml")
    log.debug("parsed manifest: %s@%s", manifest.name, manifest.version)

    package_path = registry_mod.package_path(env, manifest.name, manifest.version)
    package_path.mkdir(parents=True, exist_ok=True)

    reference = FileReference(target_path)
    src_path = registry_mod.src_path(env, manifest.name, manifest.version)
    log.debug("fetching %s -> %s", reference, src_path)
    fetch_mod.file(reference, src_path)
    log.info("added %s@%s to registry", manifest.name, manifest.version)


def watch(locks: list[LockedPackage], stamp_file: Path, *, env: LocalRegistry, interval: float) -> None:
    log.info("preparing watch for %d locked package(s)", len(locks))

    class _Target():
        def __init__(self, lock: LockedPackage):
            self.name = lock.name
            self.src = registry_mod.src_path(env, lock.name, lock.version)
            if self.src.is_symlink():
                self.src = self.src.readlink()
            self.artifact = registry_mod.artifact_path(env, lock.name, lock.version)

    targets = [target for target in map(_Target, locks) if target.src.exists()]
    skipped = len(locks) - len(targets)
    if skipped:
        log.debug("skipping %d package(s) with no src", skipped)
    log.debug("watching %d target(s)", len(targets))

    def _pass(target: _Target) -> bool:
        if not build_mod.needs_rebuild(target.src, target.artifact):
            return False

        log.info("rebuilding %s", target.name)
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            error = build_mod.build(target.src, tmp_path)
            if error:
                log.error("build failed for %s: %s", target.name, error)
                return False

            shutil.copytree(tmp_path, target.artifact, dirs_exist_ok=True)
        log.info("rebuilt %s -> %s", target.name, target.artifact)
        return True

    while True:
        if functools.reduce(lambda state, target: state | _pass(target), targets, False):
            log.debug("touching stamp file %s", stamp_file)
            stamp_file.touch()
        log.debug("sleeping")
        time.sleep(interval)

def publish(artifact_path: Path, manifest_path: Path, *, env: LocalRegistry) -> None:
    log.info("publishing from %s", artifact_path)
    manifest = manifest_mod.parse_from_file(manifest_path)
    dest = registry_mod.artifact_path(env, manifest.name, manifest.version)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(artifact_path, dest, dirs_exist_ok=True)
    shutil.copy2(manifest_path, registry_mod.manifest_path(env, manifest.name, manifest.version))
    log.info("published %s@%s -> %s", manifest.name, manifest.version, dest)


def remove(name: str, version: str, *, env: LocalRegistry) -> None:
    log.info("removing %s@%s from registry", name, version)
    path = registry_mod.package_path(env, name, version)
    shutil.rmtree(path)
    log.debug("removed %s", path)
