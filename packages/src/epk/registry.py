from pathlib import Path
from typing import NamedTuple


class LocalRegistry(NamedTuple):
    path: Path
    native_platform: str


def package_path(env: LocalRegistry, name: str, version: str) -> Path:
    return env.path / name / version


def src_path(env: LocalRegistry, name: str, version: str) -> Path:
    return package_path(env, name, version) / "src"


def artifact_path(env: LocalRegistry, name: str, version: str, platform: str | None = None) -> Path:
    return package_path(env, name, version) / (platform or env.native_platform)


def manifest_path(env: LocalRegistry, name: str, version: str) -> Path:
    return package_path(env, name, version) / "manifest.toml"
