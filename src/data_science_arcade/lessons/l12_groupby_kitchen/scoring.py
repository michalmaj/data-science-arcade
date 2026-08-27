from dataclasses import dataclass

from data_science_arcade.lessons.framework.aggregation import PipelineChoices
from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class LessonTwelveResult:
    """What the student chose per request, kept as plain recorded data
    rather than a points rubric - see LessonOneResult for why real
    per-dimension scoring is deferred."""

    guided_choices: PipelineChoices
    independent_choices: PipelineChoices
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_choices) > 0 and len(self.independent_choices) > 0 and len(self.decision_brief) > 0
