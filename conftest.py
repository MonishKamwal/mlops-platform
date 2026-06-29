import sys
from pathlib import Path

_MODELS_DIR = Path(__file__).parent / "models"


def _activate_model(test_file: Path) -> None:
    """Put the owning model's root at the front of sys.path and evict stale src cache."""
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
    """Swap in the right model root before pytest imports the test file."""
    if file_path.suffix == ".py" and file_path.name.startswith("test_"):
        _activate_model(file_path)
    return None


def pytest_runtest_setup(item):
    """Re-activate before each test in case a prior test dirtied sys.modules."""
    _activate_model(Path(str(item.fspath)))
