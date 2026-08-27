from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class LessonTwentyResult:
    """What the student did, kept as plain recorded data rather than a
    points rubric - see LessonOneResult for why real per-dimension
    scoring is deferred."""

    guided_final_checkpoint: int
    independent_final_checkpoint: int
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return self.guided_final_checkpoint > 0 and self.independent_final_checkpoint > 0 and len(self.decision_brief) > 0
