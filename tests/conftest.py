import pytest

from data_science_arcade.progress import store as progress_store


@pytest.fixture(autouse=True)
def _isolate_save_file(tmp_path, monkeypatch):
    """Every ProgressStore() built during tests must never touch the real
    developer's ~/.data_science_arcade/save.json."""
    monkeypatch.setattr(progress_store, "DEFAULT_SAVE_PATH", tmp_path / "save.json")
