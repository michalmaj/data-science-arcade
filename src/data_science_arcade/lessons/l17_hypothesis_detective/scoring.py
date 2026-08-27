from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.prediction import PredictionChoices


@dataclass(frozen=True)
class LessonSeventeenResult:
    """What the student predicted per request, kept as plain recorded data
    rather than a points rubric - see LessonOneResult for why real
    per-dimension scoring is deferred."""

    guided_choices: PredictionChoices
    independent_choices: PredictionChoices
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.guided_choices) > 0 and len(self.independent_choices) > 0 and len(self.decision_brief) > 0
