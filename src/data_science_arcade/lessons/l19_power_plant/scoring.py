from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.sampling import SamplingAllocation


@dataclass(frozen=True)
class LessonNineteenResult:
    """What the student ended up with, kept as plain recorded data rather
    than a points rubric - see LessonOneResult for why real per-dimension
    scoring is deferred."""

    guided_allocation: SamplingAllocation
    independent_allocation: SamplingAllocation
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_allocation) > 0 and len(self.independent_allocation) > 0 and len(self.decision_brief) > 0
