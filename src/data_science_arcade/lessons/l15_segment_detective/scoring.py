from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.segment import SegmentChoices


@dataclass(frozen=True)
class LessonFifteenResult:
    """What the student chose per request, kept as plain recorded data
    rather than a points rubric - see LessonOneResult for why real
    per-dimension scoring is deferred."""

    guided_choices: SegmentChoices
    independent_choices: SegmentChoices
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_choices) > 0 and len(self.independent_choices) > 0 and len(self.decision_brief) > 0
