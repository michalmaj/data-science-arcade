from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.record_pair import PairDecisions


@dataclass(frozen=True)
class LessonEightResult:
    """What the student decided, kept as plain recorded data rather than a
    points rubric - see LessonOneResult for why real per-dimension scoring
    is deferred."""

    guided_decisions: PairDecisions
    independent_decisions: PairDecisions
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_decisions) > 0 and len(self.independent_decisions) > 0 and len(self.decision_brief) > 0
