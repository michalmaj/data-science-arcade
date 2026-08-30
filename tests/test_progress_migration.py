import json
from pathlib import Path

from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.progress.model import LessonCheckpoint, LessonState, Progress
from data_science_arcade.progress.store import ProgressStore

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_a_real_v1_save_file_loads_correctly_after_migrating_to_v2(tmp_path):
    path = tmp_path / "save.json"
    path.write_text((FIXTURES_DIR / "save_v1.json").read_text(encoding="utf-8"), encoding="utf-8")
    store = ProgressStore(path)

    progress = store.load()

    assert progress.language == "pl"
    assert progress.fullscreen is True
    assert progress.state_of(1) == LessonState.COMPLETED
    assert progress.state_of(2) == LessonState.COMPLETED
    assert progress.state_of(3) == LessonState.UNLOCKED
    # v2 fields land with sane empty defaults - a v1 save never had these
    assert progress.checkpoints == {}
    assert progress.evaluations == {}
    assert progress.hints_used == {}


def test_migrating_does_not_mutate_the_original_file_on_disk_until_a_real_save(tmp_path):
    path = tmp_path / "save.json"
    original_text = (FIXTURES_DIR / "save_v1.json").read_text(encoding="utf-8")
    path.write_text(original_text, encoding="utf-8")
    store = ProgressStore(path)

    store.load()

    assert path.read_text(encoding="utf-8") == original_text


def test_saving_after_a_migration_writes_the_current_version(tmp_path):
    path = tmp_path / "save.json"
    path.write_text((FIXTURES_DIR / "save_v1.json").read_text(encoding="utf-8"), encoding="utf-8")
    store = ProgressStore(path)

    progress = store.load()
    store.save(progress)

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == 2
    assert "checkpoints" in raw
    assert "evaluations" in raw
    assert "hints_used" in raw


def test_checkpoints_round_trip_including_a_lesson_29_style_tuple_choice(tmp_path):
    store = ProgressStore(tmp_path / "save.json")
    progress = Progress()
    progress.save_checkpoint(5, LessonCheckpoint(stage_index=2, stage_fingerprint="briefing|investigation|guided_work", collected={"guided_choices": ("checkout_completion", "payment_step_abandonment")}))

    store.save(progress)
    loaded = store.load()

    checkpoint = loaded.checkpoint_for(5)
    assert checkpoint is not None
    assert checkpoint.stage_index == 2
    assert checkpoint.stage_fingerprint == "briefing|investigation|guided_work"
    assert list(checkpoint.collected["guided_choices"]) == ["checkout_completion", "payment_step_abandonment"]


def test_checkpoints_round_trip_a_lesson_30_style_frozenset_choice(tmp_path):
    store = ProgressStore(tmp_path / "save.json")
    progress = Progress()
    progress.save_checkpoint(30, LessonCheckpoint(stage_index=2, stage_fingerprint="briefing|investigation_intro|investigation_hub", collected={"leads_investigated": frozenset({"redesign_correlation", "regional_breakdown"})}))

    store.save(progress)
    loaded = store.load()

    restored = loaded.checkpoint_for(30).collected["leads_investigated"]
    assert set(restored) == {"redesign_correlation", "regional_breakdown"}


def test_completing_a_lesson_clears_its_checkpoint():
    progress = Progress()
    progress.save_checkpoint(3, LessonCheckpoint(stage_index=4, stage_fingerprint="x", collected={}))

    progress.complete(3)

    assert progress.checkpoint_for(3) is None


def test_evaluations_round_trip_through_save_and_load(tmp_path):
    store = ProgressStore(tmp_path / "save.json")
    progress = Progress()
    evaluation = LessonEvaluation(
        dimension_scores={ScoreDimension.REASONING: 70.0, ScoreDimension.EVIDENCE: 65.0},
        observations=(FeedbackObservation("lesson.feedback.completed"), FeedbackObservation("lesson.feedback.hints_used", dimension=ScoreDimension.REASONING)),
        hints_used=2,
        completed_thoughtfully=True,
    )
    progress.record_evaluation(7, evaluation)

    store.save(progress)
    loaded = store.load()

    restored = loaded.evaluations[7]
    assert restored.dimension_scores == {ScoreDimension.REASONING: 70.0, ScoreDimension.EVIDENCE: 65.0}
    assert restored.hints_used == 2
    assert restored.completed_thoughtfully is True
    assert restored.observations[1].dimension == ScoreDimension.REASONING
    assert loaded.hints_used[7] == 2


def test_one_corrupt_checkpoint_does_not_lose_the_rest_of_the_save(tmp_path):
    path = tmp_path / "save.json"
    payload = {
        "version": 2,
        "language": "en",
        "fullscreen": False,
        "lessons": {"1": "completed", "2": "unlocked"},
        "checkpoints": {"1": {"stage_index": "not-a-number"}, "2": {"stage_index": 1, "stage_fingerprint": "a|b", "collected": {}}},
        "evaluations": {},
        "hints_used": {},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    store = ProgressStore(path)

    progress = store.load()

    assert progress.state_of(1) == LessonState.COMPLETED  # unaffected by lesson 1's bad checkpoint
    assert 1 not in progress.checkpoints  # the bad one is dropped
    assert progress.checkpoint_for(2).stage_index == 1  # the good one survives


def test_an_unreadable_newer_save_is_quarantined_instead_of_silently_overwritten(tmp_path):
    path = tmp_path / "save.json"
    path.write_text(json.dumps({"version": 999, "language": "pl"}), encoding="utf-8")
    store = ProgressStore(path)

    progress = store.load()

    assert progress == Progress()
    assert not path.exists()  # moved aside, not left in place to be silently overwritten
    quarantined = list(tmp_path.glob("save.corrupt-v999.json"))
    assert len(quarantined) == 1
    assert json.loads(quarantined[0].read_text(encoding="utf-8"))["language"] == "pl"
