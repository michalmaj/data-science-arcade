from dataclasses import dataclass


@dataclass(frozen=True)
class LensOption:
    key: str
    label_key: str
    # A real computed statistic (mean, median, ...) to overlay as a vertical
    # marker on the histogram when this option is picked - None for an
    # option that denies there's anything to measure, which draws no
    # marker at all (visually reinforcing that it isn't backed by a number).
    marker_value: float | None


@dataclass(frozen=True)
class DistributionLens:
    key: str
    prompt_key: str
    options: tuple[LensOption, ...]
    hint_key: str | None = None


LensChoices = dict[str, str]
