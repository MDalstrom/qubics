from pathlib import Path
import os
from ctypes import CDLL
from generated.ecs.ecs import Lib


_root_path = Path(os.getenv("QUBICS_PATH") or os.getcwd())
_cdll = CDLL(_root_path / "ecs" / "ecs.dylib")
lib = Lib(_cdll)
