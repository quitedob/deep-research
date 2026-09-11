"""Run checks with a relocated environment's existing packages when necessary."""

from pathlib import Path
import importlib.util
import os
import site
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if importlib.util.find_spec("pytest") is None:
    packages = ROOT / ".venv" / "Lib" / "site-packages"
    if packages.is_dir():
        site.addsitedir(str(packages))

if __name__ == "__main__":
    # Unrelated installed plugins can import paid tracing clients during collection.
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    import pytest

    raise SystemExit(pytest.main(["-p", "pytest_asyncio.plugin", *(sys.argv[1:] or ["tests", "-q"])]))
