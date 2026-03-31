from pathlib import Path
import subprocess
import tempfile

from _epk.manifest import dump_from_pyproject


def publish(src: str):
    src_path = Path(src)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        dump_from_pyproject(src_path, tmp_path)

        subprocess.run(
            ["pip", "install", src, "--target", tmp],
            check=True,
            capture_output=True
        )
        subprocess.run(["epk", "publish", tmp], check=True)
