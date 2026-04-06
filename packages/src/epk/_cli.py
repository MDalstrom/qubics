import logging
import platform
from argparse import ArgumentParser
from pathlib import Path

from epk.registry import LocalRegistry
from epk import use_cases

REGISTRY_PATH = Path.home() / ".local" / "share" / "epk"


def _detect_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    return f"{system}-{machine}"


def main():
    parser = ArgumentParser(prog="epk")
    parser.add_argument("--registry", "-r", default=REGISTRY_PATH, type=Path)
    parser.add_argument("--platform", "-p", default=_detect_platform(), type=str)
    parser.add_argument("--log-level", "-l", default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    commands = parser.add_subparsers(dest="command", required=True)

    cmd_install = commands.add_parser("install")
    cmd_install.add_argument("--manifest", default=Path("manifest.toml"), type=Path)
    cmd_install.add_argument("--lock-file", default=Path("build/lock.toml"), type=Path)
    cmd_install.add_argument("--build-dir", "-o", default=Path("build"), type=Path)
    cmd_install.add_argument("--rebuild", action="store_true")

    cmd_add = commands.add_parser("add")
    cmd_add.add_argument("source", default=Path("."), type=Path)

    cmd_publish = commands.add_parser("publish")
    cmd_publish.add_argument("artifact", type=Path)
    cmd_publish.add_argument("--manifest", default=Path("manifest.toml"), type=Path)

    cmd_watch = commands.add_parser("watch")
    cmd_watch.add_argument("--lock-file", default=Path("build/lock.toml"), type=Path)
    cmd_watch.add_argument("--build-dir", "-o", default=Path("build"), type=Path)
    cmd_watch.add_argument("--interval", default=0.5, type=float)

    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level,
        format="%(name)s %(levelname)s %(message)s",
    )
    env = LocalRegistry(args.registry, args.platform)

    match args.command:
        case "install":
            from epk import lock
            if args.lock_file.exists():
                locks = lock.parse(args.lock_file)
            else:
                locks = use_cases.lock(args.manifest, args.lock_file, env=env)
                lock.serialize(args.lock_file, locks)
            use_cases.install(locks, args.build_dir, env=env, rebuild=args.rebuild)
        case "add":
            use_cases.add(args.source.resolve(), env=env)
        case "publish":
            use_cases.publish(args.artifact.resolve(), args.manifest.resolve(), env=env)
        case "watch":
            from epk import lock
            if not args.lock_file.exists():
                parser.error(f"lock file not found: {args.lock_file}")
            locks = lock.parse(args.lock_file)
            use_cases.watch(locks, args.build_dir, env=env, interval=args.interval)

