from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class LessonOneResult:
    """Everything the student chose, kept as plain recorded choices rather
    than a points rubric. Designing real per-dimension scoring (spec §20)
    is a content-design task that needs pedagogical judgment, not an
    architecture gap - deferred until there's more than one lesson to
    calibrate a rubric against."""

    guided_brief: AnalyticalBrief
    independent_brief: AnalyticalBrief
    decision_brief: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        """The only 'scoring' this vertical slice does: a choice was made
        for every field, in every stage - not skipped or left default."""
        return all(
            len(brief) > 0 for brief in (self.guided_brief, self.independent_brief, self.decision_brief)
        )
