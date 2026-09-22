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


def test_corrupt_json_is_quarantined_instead_of_silently_overwritten(tmp_path):
    path = tmp_path / "save.json"
    path.write_text("{not valid json", encoding="utf-8")
    store = ProgressStore(path)

    store.load()

    assert not path.exists()  # moved aside, not left for the next save() to clobber
    quarantined = list(tmp_path.glob("save.corrupt-*.json"))
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding="utf-8") == "{not valid json"  # original bytes preserved


def test_saving_never_leaves_a_partial_file_behind(tmp_path):
    path = tmp_path / "save.json"
    store = ProgressStore(path)

    store.save(Progress())

    assert not path.with_name(f"{path.name}.tmp").exists()  # temp file cleaned up by the atomic replace
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2


def test_saving_replaces_the_old_file_atomically_via_a_sibling_temp_file(tmp_path, monkeypatch):
    path = tmp_path / "save.json"
    store = ProgressStore(path)
    store.save(Progress(language="en"))

    from data_science_arcade.progress import store as store_module

    original_replace = store_module.Path.replace
    seen_tmp_contents = {}

    def spying_replace(self, target):
        # At the moment replace() is called, the temp file must already
        # hold the COMPLETE new payload and the destination must still
        # hold the OLD one - proving the write never touches the real
        # save path directly.
        seen_tmp_contents["tmp"] = json.loads(self.read_text(encoding="utf-8"))
        seen_tmp_contents["old"] = json.loads(target.read_text(encoding="utf-8"))
        return original_replace(self, target)

    monkeypatch.setattr(store_module.Path, "replace", spying_replace)
    store.save(Progress(language="pl"))

    assert seen_tmp_contents["tmp"]["language"] == "pl"
    assert seen_tmp_contents["old"]["language"] == "en"
    assert json.loads(path.read_text(encoding="utf-8"))["language"] == "pl"


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
