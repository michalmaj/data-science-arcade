from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.flow import EventPlacement


@dataclass(frozen=True)
class LessonNineResult:
    """What the student decided per case, kept as plain recorded data
    rather than a points rubric - see LessonOneResult for why real
    per-dimension scoring is deferred."""

    guided_actions: EventPlacement
    independent_actions: EventPlacement
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_actions) > 0 and len(self.independent_actions) > 0 and len(self.decision_brief) > 0
