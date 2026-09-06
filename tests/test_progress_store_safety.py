import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pathlib import Path

from data_science_arcade.app.game import App
from data_science_arcade.progress import store as progress_store
from data_science_arcade.progress.store import ProgressStore

REPO_SRC = Path(__file__).resolve().parent.parent / "src"


def test_default_save_path_is_not_the_real_user_save_path():
    assert progress_store.DEFAULT_SAVE_PATH != progress_store.real_user_save_path()


def test_default_save_path_is_not_under_the_real_users_home_directory():
    # The real incident class this whole module exists to close off:
    # DEFAULT_SAVE_PATH silently resolving under the developer's actual
    # home directory, the way it used to.
    assert Path.home() not in progress_store.DEFAULT_SAVE_PATH.parents


def test_bare_app_construction_never_targets_the_real_save_path(tmp_path, monkeypatch):
    # Deliberately does NOT rely on tests/conftest.py's own isolation
    # fixture staying correctly wired - constructs App() the same way an
    # ad-hoc debugging/screenshot script would, with its own explicit
    # (but still non-real) redirect, to prove the *architecture* makes
    # this safe rather than the fixture's own convention.
    monkeypatch.setattr(progress_store, "DEFAULT_SAVE_PATH", tmp_path / "save.json")
    app = App()
    assert app.progress_store.path != progress_store.real_user_save_path()
    assert Path.home() not in app.progress_store.path.parents


def test_progress_store_requires_an_explicit_path():
    import inspect

    signature = inspect.signature(ProgressStore.__init__)
    path_parameter = signature.parameters["path"]
    assert path_parameter.default is inspect.Parameter.empty


def test_real_user_save_path_has_exactly_one_caller_in_the_whole_codebase():
    # Static guard for the actual acceptance test the user asked for: the
    # real save location must only ever be reachable through one
    # deliberate opt-in (the real application entry point), never through
    # App's own default, a test, or a debug/screenshot script. A second
    # call site anywhere in src/ would silently reopen the exact class of
    # bug this module exists to close off, so this fails loudly instead.
    callers = []
    for path in REPO_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "real_user_save_path()" in text and "def real_user_save_path" not in text:
            callers.append(path.relative_to(REPO_SRC))

    assert callers == [Path("data_science_arcade/__init__.py")]
