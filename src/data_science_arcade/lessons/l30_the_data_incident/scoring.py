from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.investigation import InvestigationResult
from data_science_arcade.lessons.l30_the_data_incident.leads import MINIMUM_LEADS_REQUIRED


@dataclass(frozen=True)
class LessonThirtyResult:
    leads_investigated: InvestigationResult
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.leads_investigated) >= MINIMUM_LEADS_REQUIRED and len(self.decision_brief) > 0
