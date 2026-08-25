from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class LessonTwoResult:
    """What the student chose, kept as plain recorded data rather than a
    points rubric - see LessonOneResult for why real per-dimension scoring
    is deferred."""

    guided_source_choice: str
    independent_source_choice: str
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return bool(self.guided_source_choice) and bool(self.independent_source_choice) and len(self.decision_brief) > 0
