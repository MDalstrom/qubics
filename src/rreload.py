import importlib
from pathlib import Path
import sys

BLACKLIST = {
    'infrastructure.rendering',
}

def deep_reload(source: str):
    PROJECT_ROOT = Path(source).parent.resolve()
    for module_name, m in list(sys.modules.items()):
        if m and hasattr(m, "__file__") and m.__file__:
            if m.__file__ is source:
                continue

            if any(blacklisted in module_name for blacklisted in BLACKLIST):
                continue

            m_path = Path(m.__file__).resolve()
            if PROJECT_ROOT in m_path.parents or m_path == PROJECT_ROOT:
                importlib.reload(m)

sys.modules[__name__] = deep_reload
