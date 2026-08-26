from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.flow import EventPlacement


@dataclass(frozen=True)
class LessonTenResult:
    """What the student chose per check, kept as plain recorded data
    rather than a points rubric - see LessonOneResult for why real
    per-dimension scoring is deferred."""

    guided_rules: EventPlacement
    independent_rules: EventPlacement
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_rules) > 0 and len(self.independent_rules) > 0 and len(self.decision_brief) > 0
