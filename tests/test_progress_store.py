import json

from data_science_arcade.progress.model import LessonState, Progress
from data_science_arcade.progress.store import ProgressStore


def test_loading_a_missing_file_returns_a_fresh_progress(tmp_path):
    store = ProgressStore(tmp_path / "does_not_exist.json")

    assert store.load() == Progress()


def test_save_then_load_round_trips(tmp_path):
    store = ProgressStore(tmp_path / "save.json")
    original = Progress(language="pl", fullscreen=True)
    original.complete(1)
    original.complete(2)

    store.save(original)
    loaded = store.load()

    assert loaded == original


def test_save_creates_parent_directories(tmp_path):
    store = ProgressStore(tmp_path / "nested" / "dir" / "save.json")

    store.save(Progress())

    assert store.path.exists()


def test_corrupt_json_falls_back_to_a_fresh_progress(tmp_path):
    path = tmp_path / "save.json"
    path.write_text("{not valid json", encoding="utf-8")
    store = ProgressStore(path)

    assert store.load() == Progress()


def test_unrecognized_save_version_falls_back_to_a_fresh_progress(tmp_path):
    path = tmp_path / "save.json"
    path.write_text(json.dumps({"version": 999, "language": "pl"}), encoding="utf-8")
    store = ProgressStore(path)

    loaded = store.load()

    assert loaded == Progress()
    assert loaded.language == "en"


def test_lesson_states_round_trip_through_json_string_keys(tmp_path):
    store = ProgressStore(tmp_path / "save.json")
    original = Progress()
    original.lesson_states = {1: LessonState.COMPLETED, 2: LessonState.UNLOCKED, 7: LessonState.LOCKED}

    store.save(original)
    loaded = store.load()

    assert loaded.lesson_states[1] == LessonState.COMPLETED
    assert loaded.lesson_states[2] == LessonState.UNLOCKED
    assert all(isinstance(key, int) for key in loaded.lesson_states)
