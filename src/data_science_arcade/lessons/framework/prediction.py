from collections.abc import Callable
from dataclasses import dataclass

INCREASE = "increase"
DECREASE = "decrease"
NO_CHANGE = "no_change"
DIRECTIONS = (INCREASE, DECREASE, NO_CHANGE)


def actual_direction(before_value: float, after_value: float, threshold: float = 0.05) -> str:
    """The real direction a before/after pair moved, derived from the
    values themselves rather than hand-authored per request - so a
    request's "correct" answer can never drift out of sync with its own
    numbers. threshold is a relative (not absolute) change, so it works
    the same way for a percentage-point metric and a dollar metric:
    below it, the move counts as noise (NO_CHANGE) regardless of sign."""
    if before_value == 0:
        return INCREASE if after_value > 0 else NO_CHANGE
    relative_change = (after_value - before_value) / before_value
    if abs(relative_change) < threshold:
        return NO_CHANGE
    return INCREASE if relative_change > 0 else DECREASE


@dataclass(frozen=True)
class HypothesisRequest:
    """One "will this metric move, and which way?" prediction: the player
    picks a direction before any number is shown, then reveals the real
    before/after values for it. The correct direction is never hand-authored
    - see actual_direction() - so content can't assert a direction its own
    numbers don't back up."""

    key: str
    prompt_key: str
    metric_label_key: str
    before_value: float
    after_value: float
    hint_key: str | None = None
    value_format: Callable[[float], str] = lambda value: f"{value:.0%}"

    @property
    def correct_direction(self) -> str:
        return actual_direction(self.before_value, self.after_value)


PredictionChoices = dict[str, str]
