import json
from pathlib import Path

from data_science_arcade.progress.model import LessonState, Progress

SAVE_VERSION = 1
DEFAULT_SAVE_PATH = Path.home() / ".data_science_arcade" / "save.json"


class ProgressStore:
    """Reads/writes a single versioned JSON save file.

    A missing file, corrupt JSON, or a save from an unrecognized version all
    fall back to a fresh Progress() rather than crashing - there's no prior
    version to migrate from yet, so "fail gracefully" is the only applicable
    half of the spec's "fail gracefully or migrate" save-compatibility rule.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else DEFAULT_SAVE_PATH

    def load(self) -> Progress:
        if not self.path.exists():
            return Progress()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return Progress()
        if not isinstance(raw, dict) or raw.get("version") != SAVE_VERSION:
            return Progress()

        try:
            lesson_states = {
                int(number): LessonState(state)
                for number, state in raw.get("lessons", {}).items()
            }
        except (TypeError, ValueError):
            return Progress()

        return Progress(
            language=raw.get("language", "en"),
            fullscreen=bool(raw.get("fullscreen", False)),
            lesson_states=lesson_states or dict(Progress().lesson_states),
        )

    def save(self, progress: Progress) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": SAVE_VERSION,
            "language": progress.language,
            "fullscreen": progress.fullscreen,
            "lessons": {str(number): state.value for number, state in progress.lesson_states.items()},
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
