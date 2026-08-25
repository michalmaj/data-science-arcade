from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class LessonThreeResult:
    """What the student ended up with, kept as plain recorded data rather
    than a points rubric - see LessonOneResult for why real per-dimension
    scoring is deferred."""

    guided_records_collected: int
    independent_records_collected: int
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return self.guided_records_collected > 0 and self.independent_records_collected > 0 and len(self.decision_brief) > 0
