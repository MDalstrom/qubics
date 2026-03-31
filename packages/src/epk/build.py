import subprocess
from pathlib import Path


def build(src: Path, artifact: Path) -> str | None:
    artifact.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["make", f"O={artifact.resolve()}"],
        cwd=src,
        capture_output=True,
    )
    if result.returncode != 0:
        return result.stderr.decode()
    return None

def needs_rebuild(src: Path, artifact: Path) -> bool:
    result = subprocess.run(
        ["make", "-q", f"O={artifact.resolve()}"],
        cwd=src,
        capture_output=True,
    )
    return result.returncode != 0

