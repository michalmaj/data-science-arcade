from enum import Enum


class LessonStage(Enum):
    """The universal 6-act lesson template (spec §18). Every lesson walks
    through these in order; DEBRIEF is a 7th, implicit closing act."""

    BRIEFING = "briefing"
    INVESTIGATION = "investigation"
    GUIDED_WORK = "guided_work"
    INDEPENDENT_CHALLENGE = "independent_challenge"
    TWIST = "twist"
    DECISION = "decision"
    DEBRIEF = "debrief"
