import json
from collections.abc import Callable
from pathlib import Path

from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.progress.model import LessonCheckpoint, LessonState, Progress

SAVE_VERSION = 2
DEFAULT_SAVE_PATH = Path.home() / ".data_science_arcade" / "save.json"


def _json_safe(value):
    """frozenset/set aren't JSON-serializable; everything else a lesson's
    `collected` dict actually holds (str/int/float/bool/dict/list/tuple) is,
    once tuples are recursively turned into lists. Sets/frozensets are
    inherently unordered, so sorting them for a deterministic save is safe;
    tuples are never sorted, since some (e.g. Lesson 29's FindingChoices)
    are order-significant."""
    if isinstance(value, (frozenset, set)):
        return sorted(value)
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _checkpoint_to_dict(checkpoint: LessonCheckpoint) -> dict:
    return {
        "stage_index": checkpoint.stage_index,
        "stage_fingerprint": checkpoint.stage_fingerprint,
        "collected": _json_safe(checkpoint.collected),
    }


def _checkpoint_from_dict(raw: dict) -> LessonCheckpoint:
    return LessonCheckpoint(
        stage_index=int(raw["stage_index"]),
        stage_fingerprint=str(raw["stage_fingerprint"]),
        collected=dict(raw.get("collected", {})),
    )


def _evaluation_to_dict(evaluation: LessonEvaluation) -> dict:
    return {
        "dimension_scores": {dimension.value: score for dimension, score in evaluation.dimension_scores.items()},
        "observations": [
            {"text_key": observation.text_key, "dimension": observation.dimension.value if observation.dimension else None}
            for observation in evaluation.observations
        ],
        "hints_used": evaluation.hints_used,
        "completed_thoughtfully": evaluation.completed_thoughtfully,
    }


def _evaluation_from_dict(raw: dict) -> LessonEvaluation:
    return LessonEvaluation(
        dimension_scores={ScoreDimension(key): float(value) for key, value in raw.get("dimension_scores", {}).items()},
        observations=tuple(
            FeedbackObservation(
                text_key=entry["text_key"],
                dimension=ScoreDimension(entry["dimension"]) if entry.get("dimension") else None,
            )
            for entry in raw.get("observations", [])
        ),
        hints_used=int(raw.get("hints_used", 0)),
        completed_thoughtfully=bool(raw.get("completed_thoughtfully", False)),
    )


MigrationFn = Callable[[dict], dict]


def _migrate_v1_to_v2(raw: dict) -> dict:
    """v2 adds checkpoints/evaluations/hints_used - purely additive, no v1
    field is renamed or reshaped."""
    migrated = dict(raw)
    migrated.setdefault("checkpoints", {})
    migrated.setdefault("evaluations", {})
    migrated.setdefault("hints_used", {})
    migrated["version"] = 2
    return migrated


MIGRATIONS: dict[int, MigrationFn] = {1: _migrate_v1_to_v2}


def _migrate_forward(raw: dict, from_version: int) -> dict | None:
    version = from_version
    while version < SAVE_VERSION:
        step = MIGRATIONS.get(version)
        if step is None:
            return None
        raw = step(raw)
        version += 1
    return raw


class ProgressStore:
    """Reads/writes a single versioned JSON save file.

    A missing file or corrupt JSON falls back to a fresh Progress(). An
    older version runs forward through MIGRATIONS; a version this build
    doesn't recognize (newer than SAVE_VERSION, or older than any migration
    can bridge) also falls back to fresh - but only after renaming the
    unreadable file aside, so the next save() doesn't silently destroy it.

    Each field is parsed independently: one corrupt checkpoint or
    evaluation shouldn't discard all 30 lessons' unlock/complete state the
    way a single try/except around the whole payload would.
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

        if not isinstance(raw, dict):
            self._quarantine(raw_version="unknown")
            return Progress()

        version = raw.get("version")
        if not isinstance(version, int) or version > SAVE_VERSION:
            self._quarantine(raw_version=str(version))
            return Progress()
        if version < SAVE_VERSION:
            migrated = _migrate_forward(raw, version)
            if migrated is None:
                self._quarantine(raw_version=str(version))
                return Progress()
            raw = migrated

        return Progress(
            language=raw.get("language", "en"),
            fullscreen=bool(raw.get("fullscreen", False)),
            lesson_states=self._parse_lesson_states(raw),
            checkpoints=self._parse_checkpoints(raw),
            evaluations=self._parse_evaluations(raw),
            hints_used=self._parse_hints_used(raw),
        )

    def _parse_lesson_states(self, raw: dict) -> dict[int, LessonState]:
        try:
            lesson_states = {int(number): LessonState(state) for number, state in raw.get("lessons", {}).items()}
        except (TypeError, ValueError):
            return dict(Progress().lesson_states)
        return lesson_states or dict(Progress().lesson_states)

    def _parse_checkpoints(self, raw: dict) -> dict[int, LessonCheckpoint]:
        checkpoints: dict[int, LessonCheckpoint] = {}
        for number, entry in raw.get("checkpoints", {}).items():
            try:
                checkpoints[int(number)] = _checkpoint_from_dict(entry)
            except (TypeError, ValueError, KeyError):
                continue  # one bad checkpoint doesn't cost the rest of the save
        return checkpoints

    def _parse_evaluations(self, raw: dict) -> dict[int, LessonEvaluation]:
        evaluations: dict[int, LessonEvaluation] = {}
        for number, entry in raw.get("evaluations", {}).items():
            try:
                evaluations[int(number)] = _evaluation_from_dict(entry)
            except (TypeError, ValueError, KeyError):
                continue
        return evaluations

    def _parse_hints_used(self, raw: dict) -> dict[int, int]:
        try:
            return {int(number): int(count) for number, count in raw.get("hints_used", {}).items()}
        except (TypeError, ValueError):
            return {}

    def _quarantine(self, raw_version: str) -> None:
        if not self.path.exists():
            return
        quarantine_path = self.path.with_name(f"{self.path.stem}.corrupt-v{raw_version}{self.path.suffix}")
        try:
            self.path.replace(quarantine_path)
        except OSError:
            pass  # best-effort - a save() right after this will just overwrite the unreadable file

    def save(self, progress: Progress) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": SAVE_VERSION,
            "language": progress.language,
            "fullscreen": progress.fullscreen,
            "lessons": {str(number): state.value for number, state in progress.lesson_states.items()},
            "checkpoints": {str(number): _checkpoint_to_dict(checkpoint) for number, checkpoint in progress.checkpoints.items()},
            "evaluations": {str(number): _evaluation_to_dict(evaluation) for number, evaluation in progress.evaluations.items()},
            "hints_used": {str(number): count for number, count in progress.hints_used.items()},
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
