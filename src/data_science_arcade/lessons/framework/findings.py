from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    key: str
    label_key: str
    python_code: str | None = None
    """Real pandas-equivalent code for this finding's own number(s), e.g.
    from lessons/l29_the_executive_brief/findings_data.py's percent_change/
    point_change - optional, and independent of any Dataset: a Finding
    pick doesn't transform data, it surfaces a fact already computed
    elsewhere, which is exactly the shape workbench/context.py's
    AnalyticalAction is meant to record."""


FindingChoices = tuple[str, ...]  # exactly `target_count` finding keys, in pick order
