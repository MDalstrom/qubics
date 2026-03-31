import os
import pytest
from pathlib import Path

from epk.registry import LocalRegistry
from epk.lock import LockedPackage
from epk.reference import TagReference
from epk import use_cases


PLATFORM = "darwin-arm64"


@pytest.fixture
def registry_path(tmp_path):
    path = tmp_path / "registry"
    path.mkdir()
    return path


@pytest.fixture
def env(registry_path):
    return LocalRegistry(registry_path, PLATFORM)


@pytest.fixture
def build_dir(tmp_path):
    return tmp_path / "build"


def make_registry_package(registry_path, name, version, deps=None, *, with_artifact=True):
    pkg = registry_path / name / version
    pkg.mkdir(parents=True, exist_ok=True)
    deps_toml = ", ".join(f'"{d}"' for d in (deps or []))
    (pkg / "manifest.toml").write_text(
        f'name = "{name}"\nversion = "{version}"\ndeps = [{deps_toml}]\n'
    )
    if with_artifact:
        art = pkg / PLATFORM
        art.mkdir()
        (art / f"{name}.dylib").write_bytes(b"fake artifact")
    return pkg


def make_manifest(path, name, version, deps=None):
    deps_toml = ", ".join(f'"{d}"' for d in (deps or []))
    path.write_text(f'name = "{name}"\nversion = "{version}"\ndeps = [{deps_toml}]\n')


# ── lock ──────────────────────────────────────────────────────────────────────

class TestLock:
    def test_no_deps(self, tmp_path, env):
        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0")

        locks = use_cases.lock(manifest, tmp_path / "lock.toml", env=env)

        assert locks == []

    def test_single_dep(self, tmp_path, env, registry_path):
        make_registry_package(registry_path, "pkgA", "1.0.0")
        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0", deps=["pkgA"])

        locks = use_cases.lock(manifest, tmp_path / "lock.toml", env=env)

        assert len(locks) == 1
        assert locks[0].name == "pkgA"
        assert locks[0].version == "1.0.0"

    def test_transitive_deps_ordered(self, tmp_path, env, registry_path):
        # A → B → C; dependencies must appear before dependents
        make_registry_package(registry_path, "pkgC", "1.0.0")
        make_registry_package(registry_path, "pkgB", "1.0.0", deps=["pkgC"])
        make_registry_package(registry_path, "pkgA", "1.0.0", deps=["pkgB"])
        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0", deps=["pkgA"])

        locks = use_cases.lock(manifest, tmp_path / "lock.toml", env=env)

        assert [l.name for l in locks] == ["pkgC", "pkgB", "pkgA"]

    def test_diamond_dep_deduplicated(self, tmp_path, env, registry_path):
        # A → B → D, A → C → D; D should appear exactly once
        make_registry_package(registry_path, "pkgD", "1.0.0")
        make_registry_package(registry_path, "pkgB", "1.0.0", deps=["pkgD"])
        make_registry_package(registry_path, "pkgC", "1.0.0", deps=["pkgD"])
        make_registry_package(registry_path, "pkgA", "1.0.0", deps=["pkgB", "pkgC"])
        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0", deps=["pkgA"])

        locks = use_cases.lock(manifest, tmp_path / "lock.toml", env=env)

        names = [l.name for l in locks]
        assert names.count("pkgD") == 1
        assert set(names) == {"pkgA", "pkgB", "pkgC", "pkgD"}

    def test_missing_dep_raises(self, tmp_path, env):
        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0", deps=["doesnotexist"])

        with pytest.raises(Exception, match="could not resolve manifest"):
            use_cases.lock(manifest, tmp_path / "lock.toml", env=env)

    def test_resolves_latest_version(self, tmp_path, env, registry_path):
        make_registry_package(registry_path, "pkgA", "1.0.0")
        make_registry_package(registry_path, "pkgA", "2.0.0")
        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0", deps=["pkgA"])

        locks = use_cases.lock(manifest, tmp_path / "lock.toml", env=env)

        assert locks[0].version == "2.0.0"


# ── add ───────────────────────────────────────────────────────────────────────

class TestAdd:
    def test_registers_package_in_registry(self, tmp_path, env, registry_path):
        src = tmp_path / "mypkg"
        src.mkdir()
        (src / "manifest.toml").write_text('name = "mypkg"\nversion = "1.0.0"\ndeps = []\n')

        use_cases.add(src, env=env)

        assert (registry_path / "mypkg" / "1.0.0" / "manifest.toml").exists()
        assert (registry_path / "mypkg" / "1.0.0" / "src").is_symlink()

    def test_src_symlink_points_to_source(self, tmp_path, env, registry_path):
        src = tmp_path / "mypkg"
        src.mkdir()
        (src / "manifest.toml").write_text('name = "mypkg"\nversion = "1.0.0"\ndeps = []\n')

        use_cases.add(src, env=env)

        link = registry_path / "mypkg" / "1.0.0" / "src"
        assert Path(os.readlink(link)).resolve() == src.resolve()


# ── remove ────────────────────────────────────────────────────────────────────

class TestRemove:
    def test_deletes_package_from_registry(self, env, registry_path):
        make_registry_package(registry_path, "pkgA", "1.0.0")

        use_cases.remove("pkgA", "1.0.0", env=env)

        assert not (registry_path / "pkgA" / "1.0.0").exists()

    def test_missing_package_raises(self, env):
        with pytest.raises(FileNotFoundError):
            use_cases.remove("nonexistent", "1.0.0", env=env)


# ── install ───────────────────────────────────────────────────────────────────

class TestInstall:
    def test_empty_lock_list(self, env, build_dir):
        use_cases.install([], build_dir, env=env)

        assert build_dir.exists()

    def test_creates_symlink_in_build_dir(self, env, registry_path, build_dir):
        make_registry_package(registry_path, "pkgA", "1.0.0")
        locks = [LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0"))]

        use_cases.install(locks, build_dir, env=env)

        link = build_dir / "pkgA"
        assert link.is_symlink()
        assert link.resolve() == (registry_path / "pkgA" / "1.0.0" / PLATFORM).resolve()

    def test_multiple_packages(self, env, registry_path, build_dir):
        make_registry_package(registry_path, "pkgA", "1.0.0")
        make_registry_package(registry_path, "pkgB", "1.0.0")
        locks = [
            LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0")),
            LockedPackage("pkgB", "1.0.0", TagReference("pkgB", "1.0.0")),
        ]

        use_cases.install(locks, build_dir, env=env)

        assert (build_dir / "pkgA").is_symlink()
        assert (build_dir / "pkgB").is_symlink()

    def test_failure_raises(self, env, registry_path, build_dir, monkeypatch):
        make_registry_package(registry_path, "pkgA", "1.0.0")
        make_registry_package(registry_path, "pkgB", "1.0.0")
        locks = [
            LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0")),
            LockedPackage("pkgB", "1.0.0", TagReference("pkgB", "1.0.0")),
        ]

        call_count = 0
        from epk import install as install_mod
        original = install_mod.execute

        def fail_on_second(plan, target):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return "build failed"
            return original(plan, target)

        monkeypatch.setattr("epk.install.execute", fail_on_second)

        with pytest.raises(Exception, match="build failed"):
            use_cases.install(locks, build_dir, env=env)

    def test_partial_failure_rolls_back_first(self, env, registry_path, build_dir, monkeypatch):
        make_registry_package(registry_path, "pkgA", "1.0.0")
        make_registry_package(registry_path, "pkgB", "1.0.0")
        locks = [
            LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0")),
            LockedPackage("pkgB", "1.0.0", TagReference("pkgB", "1.0.0")),
        ]

        call_count = 0
        from epk import install as install_mod
        original = install_mod.execute

        def fail_on_second(plan, target):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return "build failed"
            return original(plan, target)

        monkeypatch.setattr("epk.install.execute", fail_on_second)

        with pytest.raises(Exception):
            use_cases.install(locks, build_dir, env=env)

        assert not (build_dir / "pkgA").is_symlink()


# ── watch ─────────────────────────────────────────────────────────────────────

class TestWatch:
    def _run_one_pass(self, monkeypatch, locks, stamp_file, env):
        def stop(_): raise StopIteration
        monkeypatch.setattr("time.sleep", stop)
        with pytest.raises(StopIteration):
            use_cases.watch(locks, stamp_file, env=env, interval=0)

    def test_empty_locks_no_stamp(self, tmp_path, env, monkeypatch):
        stamp = tmp_path / "stamp"
        self._run_one_pass(monkeypatch, [], stamp, env)
        assert not stamp.exists()

    def test_no_src_target_skipped(self, tmp_path, env, registry_path, monkeypatch):
        # Package in registry but no src dir — target should be filtered out
        make_registry_package(registry_path, "pkgA", "1.0.0")
        locks = [LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0"))]
        stamp = tmp_path / "stamp"

        called = []
        monkeypatch.setattr("epk.build.needs_rebuild", lambda s, a: called.append(1) or True)

        self._run_one_pass(monkeypatch, locks, stamp, env)

        assert not called
        assert not stamp.exists()

    def test_no_rebuild_needed_no_stamp(self, tmp_path, env, registry_path, monkeypatch):
        pkg = make_registry_package(registry_path, "pkgA", "1.0.0")
        (pkg / "src").mkdir()
        locks = [LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0"))]
        stamp = tmp_path / "stamp"

        monkeypatch.setattr("epk.build.needs_rebuild", lambda s, a: False)

        self._run_one_pass(monkeypatch, locks, stamp, env)

        assert not stamp.exists()

    def test_rebuild_success_touches_stamp(self, tmp_path, env, registry_path, monkeypatch):
        pkg = make_registry_package(registry_path, "pkgA", "1.0.0")
        (pkg / "src").mkdir()
        locks = [LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0"))]
        stamp = tmp_path / "stamp"

        monkeypatch.setattr("epk.build.needs_rebuild", lambda s, a: True)
        monkeypatch.setattr("epk.build.build", lambda s, a: None)

        self._run_one_pass(monkeypatch, locks, stamp, env)

        assert stamp.exists()

    def test_build_failure_no_stamp(self, tmp_path, env, registry_path, monkeypatch):
        pkg = make_registry_package(registry_path, "pkgA", "1.0.0")
        (pkg / "src").mkdir()
        locks = [LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0"))]
        stamp = tmp_path / "stamp"

        monkeypatch.setattr("epk.build.needs_rebuild", lambda s, a: True)
        monkeypatch.setattr("epk.build.build", lambda s, a: "make: error: build failed")

        self._run_one_pass(monkeypatch, locks, stamp, env)

        assert not stamp.exists()

    def test_symlink_src_resolved(self, tmp_path, env, registry_path, monkeypatch):
        pkg = make_registry_package(registry_path, "pkgA", "1.0.0")
        real_src = tmp_path / "real_src"
        real_src.mkdir()
        (pkg / "src").symlink_to(real_src)
        locks = [LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0"))]
        stamp = tmp_path / "stamp"

        seen_src = []
        monkeypatch.setattr("epk.build.needs_rebuild", lambda s, a: seen_src.append(s) or False)

        self._run_one_pass(monkeypatch, locks, stamp, env)

        assert seen_src[0] == real_src

    def test_any_rebuild_touches_stamp(self, tmp_path, env, registry_path, monkeypatch):
        pkgA = make_registry_package(registry_path, "pkgA", "1.0.0")
        (pkgA / "src").mkdir()
        pkgB = make_registry_package(registry_path, "pkgB", "1.0.0")
        (pkgB / "src").mkdir()
        locks = [
            LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0")),
            LockedPackage("pkgB", "1.0.0", TagReference("pkgB", "1.0.0")),
        ]
        stamp = tmp_path / "stamp"

        monkeypatch.setattr("epk.build.needs_rebuild", lambda s, a: "pkgA" in str(s))
        monkeypatch.setattr("epk.build.build", lambda s, a: None)

        self._run_one_pass(monkeypatch, locks, stamp, env)

        assert stamp.exists()

    def test_stamp_updated_on_second_pass(self, tmp_path, env, registry_path, monkeypatch):
        pkg = make_registry_package(registry_path, "pkgA", "1.0.0")
        (pkg / "src").mkdir()
        locks = [LockedPackage("pkgA", "1.0.0", TagReference("pkgA", "1.0.0"))]
        stamp = tmp_path / "stamp"

        sleep_calls = []

        def stop_after_two(_):
            sleep_calls.append(1)
            if len(sleep_calls) >= 2:
                raise StopIteration

        monkeypatch.setattr("time.sleep", stop_after_two)
        monkeypatch.setattr("epk.build.needs_rebuild", lambda s, a: True)
        monkeypatch.setattr("epk.build.build", lambda s, a: None)

        with pytest.raises(StopIteration):
            use_cases.watch(locks, stamp, env=env, interval=0)

        assert len(sleep_calls) == 2
        assert stamp.exists()


# ── end-to-end ────────────────────────────────────────────────────────────────

class TestEndToEnd:
    def test_add_lock_install(self, tmp_path, env, registry_path, build_dir):
        src = tmp_path / "mypkg"
        src.mkdir()
        (src / "manifest.toml").write_text('name = "mypkg"\nversion = "1.0.0"\ndeps = []\n')

        use_cases.add(src, env=env)

        # Skip actual build — place artifact directly
        art = registry_path / "mypkg" / "1.0.0" / PLATFORM
        art.mkdir(parents=True)
        (art / "mypkg.dylib").write_bytes(b"fake")

        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0", deps=["mypkg"])
        locks = use_cases.lock(manifest, tmp_path / "lock.toml", env=env)
        assert len(locks) == 1

        use_cases.install(locks, build_dir, env=env)

        assert (build_dir / "mypkg").is_symlink()

    def test_remove_breaks_lock(self, tmp_path, env, registry_path):
        make_registry_package(registry_path, "pkgA", "1.0.0")
        manifest = tmp_path / "manifest.toml"
        make_manifest(manifest, "root", "0.1.0", deps=["pkgA"])

        use_cases.remove("pkgA", "1.0.0", env=env)

        with pytest.raises(Exception, match="could not resolve manifest"):
            use_cases.lock(manifest, tmp_path / "lock.toml", env=env)
