from data_science_arcade.ui.mission_briefing_scene import MissionBriefingScene


def click_through_mission_briefing(app) -> None:
    """Every lesson's LessonRunner now shows a MissionBriefingScene (real
    title/objectives/duration) before its own first stage - tests that
    start a lesson need one extra click through "Start Mission" before
    reaching what used to be the very first screen. A no-op if the
    current scene isn't a briefing (e.g. resuming mid-lesson from a
    checkpoint skips it), so callers can call this unconditionally right
    after starting a lesson."""
    scene = app.scenes.current.inner
    if isinstance(scene, MissionBriefingScene):
        scene.buttons.buttons[0].on_activate()
