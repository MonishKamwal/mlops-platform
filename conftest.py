import sys
from pathlib import Path

_MODELS_DIR = Path(__file__).parent / "models"
_SERVING_DIR = Path(__file__).parent / "serving"


def _activate_context(test_file: Path) -> None:
    """Put the owning module root at the front of sys.path and evict stale src cache."""
    if _SERVING_DIR in test_file.parents:
        if str(_SERVING_DIR) not in sys.path:
            sys.path.insert(0, str(_SERVING_DIR))
        return
    for model_dir in _MODELS_DIR.iterdir():
        if model_dir.is_dir() and model_dir in test_file.parents:
            for key in list(sys.modules.keys()):
                if key == "src" or key.startswith("src."):
                    del sys.modules[key]
            if str(model_dir) in sys.path:
                sys.path.remove(str(model_dir))
            sys.path.insert(0, str(model_dir))
            return


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".py" and file_path.name.startswith("test_"):
        _activate_context(file_path)
    return None


def pytest_runtest_setup(item):
    _activate_context(Path(str(item.fspath)))
