from dataclasses import dataclass


@dataclass(frozen=True)
class ChartOption:
    key: str
    label_key: str
    chart_type: str  # "bar" or "line"
    scale: str  # "zero_based" or "zoomed" - ignored for "line" (always drawn zero-based)
    categories: tuple[str, ...] | None = None  # overrides the request's own categories - for a recipe that charts a different slice/computation of the data (a cherry-picked window, a different denominator); None means "use the request's"
    values: tuple[float, ...] | None = None  # overrides the request's own values, paired with `categories` above


@dataclass(frozen=True)
class ChartRequest:
    key: str
    prompt_key: str
    categories: tuple[str, ...]
    values: tuple[float, ...]
    options: tuple[ChartOption, ...]
    hint_key: str | None = None


ChartChoices = dict[str, str]
