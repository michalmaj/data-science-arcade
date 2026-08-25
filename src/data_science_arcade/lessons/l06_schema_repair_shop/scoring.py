from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.repair import RepairResolution


@dataclass(frozen=True)
class LessonSixResult:
    """What the student ended up with, kept as plain recorded data rather
    than a points rubric - see LessonOneResult for why real per-dimension
    scoring is deferred."""

    guided_resolution: RepairResolution
    independent_resolution: RepairResolution
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_resolution) > 0 and len(self.independent_resolution) > 0 and len(self.decision_brief) > 0
