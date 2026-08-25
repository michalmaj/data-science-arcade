from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class LessonSevenResult:
    """What the student chose, kept as plain recorded data rather than a
    points rubric - see LessonOneResult for why real per-dimension scoring
    is deferred."""

    guided_strategy: str
    independent_strategy: str
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return bool(self.guided_strategy) and bool(self.independent_strategy) and len(self.decision_brief) > 0
