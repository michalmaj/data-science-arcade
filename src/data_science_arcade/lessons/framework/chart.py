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


def chart_render_range(chart_type: str, scale: str, values: tuple[float, ...]) -> tuple[float, float]:
    """The exact (min, max) axis range `ChartDesignerScene` renders for a
    given chart_type/scale - extracted as a pure function, shared by the
    scene itself and by any lesson's own Python Mirror, so a Mirror
    computation of a visual effect (e.g. how much of the plotting range a
    real data gap occupies) always uses the identical range a screenshot
    would show, never a hardcoded approximation of it."""
    if chart_type == "bar" and scale == "zoomed":
        return min(values) * 0.9, max(values) * 1.05
    return 0.0, max(values) * 1.15
