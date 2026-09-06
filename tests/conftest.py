import pytest

from data_science_arcade.progress import store as progress_store


@pytest.fixture(autouse=True)
def _isolate_save_file(tmp_path, monkeypatch):
    """DEFAULT_SAVE_PATH is no longer the real developer save location at
    all (see progress/store.py) - a bare App() structurally can't reach
    ~/.data_science_arcade/save.json without opting in via
    real_user_save_path(), which nothing in this test suite calls. This
    fixture's real job now is giving each test its own tmp_path-scoped
    file instead of sharing the module-level default (still a temp dir,
    just not this test's own) across parallel/repeated test runs, and
    letting a test construct multiple bare App() instances that share
    one file on purpose (see e.g. test_lesson01_scenario.py's resume
    tests)."""
    monkeypatch.setattr(progress_store, "DEFAULT_SAVE_PATH", tmp_path / "save.json")
