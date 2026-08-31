import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.workbench.context import LessonContext

CLAIM = BriefField(key="claim", prompt_key="common.back", options=(BriefOption("a", "common.back"), BriefOption("b", "common.back")))
EVIDENCE = EvidenceField(key="evidence", prompt_key="common.back", min_count=2, max_count=3)
LIMITATION = BriefField(key="limitation", prompt_key="common.back", options=(BriefOption("x", "common.back"),))
CONFIDENCE = BriefField(key="confidence", prompt_key="common.back", options=(BriefOption("low", "common.back"), BriefOption("high", "common.back")))
RECOMMENDATION = BriefField(key="recommendation", prompt_key="common.back", options=(BriefOption("wait", "common.back"),))
FOLLOW_UP = BriefField(key="follow_up", prompt_key="common.back", options=(BriefOption("recheck", "common.back"),))


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _context_with_evidence(count=4) -> LessonContext:
    context = LessonContext()
    for i in range(count):
        context.record_evidence(f"finding {i}", detail=f"{i * 10}%")
    return context


def _make_scene(app, context=None, on_complete=lambda choices: None, **kwargs):
    return DecisionBuilderScene(
        app,
        "app.title",
        steps=(CLAIM, EVIDENCE, LIMITATION, CONFIDENCE, RECOMMENDATION, FOLLOW_UP),
        context=context if context is not None else _context_with_evidence(),
        on_complete=on_complete,
        **kwargs,
    )


def test_steps_can_be_an_arbitrary_sequence_not_just_six_fixed_ones():
    # L02's own decision shape has no Confidence step and different step
    # names/count than L01's - the scene must not assume six named steps.
    app = _init_app()
    try:
        answer_strategy = BriefField(key="answer_strategy", prompt_key="common.back", options=(BriefOption("floor_and_range", "common.back"),))
        known_gap = BriefField(key="known_gap", prompt_key="common.back", options=(BriefOption("legacy_gap", "common.back"),))
        scene = DecisionBuilderScene(
            app,
            "app.title",
            steps=(answer_strategy, EVIDENCE, known_gap),
            context=_context_with_evidence(),
            on_complete=lambda choices: None,
        )
        assert len(scene._steps) == 3
        assert scene.evidence_field is EVIDENCE
    finally:
        pygame.quit()


def test_missing_evidence_field_raises_a_clear_error_not_stopiteration():
    app = _init_app()
    try:
        claim_only = BriefField(key="claim", prompt_key="common.back", options=(BriefOption("a", "common.back"),))
        try:
            DecisionBuilderScene(
                app, "app.title", steps=(claim_only,), context=_context_with_evidence(), on_complete=lambda choices: None
            )
            assert False, "expected a ValueError"
        except ValueError as error:
            assert "exactly one EvidenceField" in str(error)
    finally:
        pygame.quit()


def test_two_evidence_fields_raises_a_clear_error_not_a_silent_first_match():
    app = _init_app()
    try:
        second_evidence = EvidenceField(key="evidence_2", prompt_key="common.back", min_count=1, max_count=2)
        try:
            DecisionBuilderScene(
                app,
                "app.title",
                steps=(EVIDENCE, second_evidence),
                context=_context_with_evidence(),
                on_complete=lambda choices: None,
            )
            assert False, "expected a ValueError"
        except ValueError as error:
            assert "exactly one EvidenceField" in str(error)
    finally:
        pygame.quit()


def test_starts_on_claim_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.step_index == 0
        assert scene.next_button.enabled is False
    finally:
        pygame.quit()


def test_single_select_steps_behave_like_brief_builder_scene():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # claim=a
        assert scene.next_button.enabled is True

        scene.next_button.on_activate()

        assert scene.step_index == 1
        assert isinstance(scene._current_step(), EvidenceField)
    finally:
        pygame.quit()


def test_evidence_step_shows_one_toggle_button_per_real_context_evidence_item():
    app = _init_app()
    try:
        context = _context_with_evidence(count=4)
        scene = _make_scene(app, context=context)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert len(scene._evidence_toggle_buttons) == 4
    finally:
        pygame.quit()


def test_evidence_next_is_disabled_below_min_count_and_enabled_within_range():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()  # now on evidence step

        first_item_id = list(scene._evidence_toggle_buttons.keys())[0]
        scene._evidence_toggle_buttons[first_item_id].on_activate()
        assert scene.next_button.enabled is False  # 1 selected, min_count=2

        second_item_id = list(scene._evidence_toggle_buttons.keys())[1]
        scene._evidence_toggle_buttons[second_item_id].on_activate()
        assert scene.next_button.enabled is True  # 2 selected, within 2-3
    finally:
        pygame.quit()


def test_evidence_toggle_is_reversible():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        item_id = list(scene._evidence_toggle_buttons.keys())[0]
        scene._evidence_toggle_buttons[item_id].on_activate()
        assert item_id in scene._evidence_selected

        scene._evidence_toggle_buttons[item_id].on_activate()
        assert item_id not in scene._evidence_selected
    finally:
        pygame.quit()


def test_evidence_selection_cannot_exceed_max_count():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        item_ids = list(scene._evidence_toggle_buttons.keys())
        for item_id in item_ids[:3]:
            scene._evidence_toggle_buttons[item_id].on_activate()
        assert len(scene._evidence_selected) == 3  # at max_count

        scene._evidence_toggle_buttons[item_ids[3]].on_activate()  # a 4th pick

        assert len(scene._evidence_selected) == 3  # still capped, not appended
    finally:
        pygame.quit()


def test_unselected_evidence_buttons_are_disabled_once_max_count_is_reached():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        item_ids = list(scene._evidence_toggle_buttons.keys())
        for item_id in item_ids[:3]:
            scene._evidence_toggle_buttons[item_id].on_activate()

        assert scene._evidence_toggle_buttons[item_ids[3]].enabled is False
        assert scene._evidence_toggle_buttons[item_ids[0]].enabled is True  # already-selected stays clickable
    finally:
        pygame.quit()


def test_back_from_evidence_preserves_the_toggled_selection():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        item_ids = list(scene._evidence_toggle_buttons.keys())
        scene._evidence_toggle_buttons[item_ids[0]].on_activate()
        scene._evidence_toggle_buttons[item_ids[1]].on_activate()
        scene.next_button.on_activate()  # -> limitation

        scene.back_button.on_activate()  # -> evidence again

        assert set(scene._evidence_selected) == {item_ids[0], item_ids[1]}
        assert scene._evidence_toggle_buttons[item_ids[0]].enabled is True
    finally:
        pygame.quit()


def test_finishing_the_last_step_calls_on_complete_with_every_choice():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))

        scene.buttons.buttons[0].on_activate()  # claim=a
        scene.next_button.on_activate()
        item_ids = list(scene._evidence_toggle_buttons.keys())
        scene._evidence_toggle_buttons[item_ids[0]].on_activate()
        scene._evidence_toggle_buttons[item_ids[1]].on_activate()
        scene.next_button.on_activate()  # -> limitation
        scene.buttons.buttons[0].on_activate()  # limitation=x
        scene.next_button.on_activate()  # -> confidence
        scene.buttons.buttons[0].on_activate()  # confidence=low
        scene.next_button.on_activate()  # -> recommendation
        scene.buttons.buttons[0].on_activate()  # recommendation=wait
        scene.next_button.on_activate()  # -> follow_up
        scene.buttons.buttons[0].on_activate()  # follow_up=recheck
        scene.next_button.on_activate()  # finish

        assert len(collected) == 1
        result = collected[0]
        assert result["claim"] == "a"
        assert result["limitation"] == "x"
        assert result["confidence"] == "low"
        assert result["recommendation"] == "wait"
        assert result["follow_up"] == "recheck"
        assert set(result["evidence"]) == {item_ids[0], item_ids[1]}
    finally:
        pygame.quit()


def test_next_does_nothing_on_the_evidence_step_below_min_count():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        scene._next()  # nothing selected yet, min_count=2

        assert scene.step_index == 1  # still on the evidence step
    finally:
        pygame.quit()


def test_evidence_option_labels_include_the_recorded_detail():
    app = _init_app()
    try:
        context = LessonContext()
        context.record_evidence("common.back", detail="42%")
        scene = _make_scene(app, context=context)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        item_id = list(scene._evidence_toggle_buttons.keys())[0]
        assert scene._evidence_toggle_buttons[item_id].label.endswith("42%")
    finally:
        pygame.quit()


def test_a_large_evidence_pool_still_fits_above_the_nav_row():
    # L01's real pool tops out at 5 items; L02's own Evidence Review
    # produces 8 - the fixed default spacing/height ran the last few
    # buttons under Back/Next, caught only by a real screenshot with a
    # real 8-item pool, not by any test written against L01's smaller one.
    app = _init_app()
    try:
        context = _context_with_evidence(count=8)
        scene = _make_scene(app, context=context)
        scene.buttons.buttons[0].on_activate()  # claim
        scene.next_button.on_activate()

        assert len(scene._evidence_toggle_buttons) == 8
        last_item_bottom = max(button.rect.bottom for button in scene._evidence_toggle_buttons.values())
        nav_top = scene.next_button.rect.top
        assert last_item_bottom <= nav_top
    finally:
        pygame.quit()


def test_draw_does_not_crash_on_every_step_guided_or_not():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            for _ in range(len(scene._steps)):
                scene.draw(app.logical_surface)
                if not scene._steps[scene.step_index].__class__.__name__ == "EvidenceField":
                    scene.buttons.buttons[0].on_activate()
                else:
                    ids = list(scene._evidence_toggle_buttons.keys())
                    scene._evidence_toggle_buttons[ids[0]].on_activate()
                    scene._evidence_toggle_buttons[ids[1]].on_activate()
                scene.next_button.on_activate()
    finally:
        pygame.quit()
