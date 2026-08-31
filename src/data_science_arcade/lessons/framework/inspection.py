from dataclasses import dataclass


@dataclass(frozen=True)
class InspectionOption:
    key: str
    label_key: str


@dataclass(frozen=True)
class InspectionPrompt:
    """A single ungraded micro-decision shown once, the first time
    WorkbenchScene's DATA tab opens with no repair issues to resolve -
    e.g. "what does one row actually represent here?" Which option gets
    picked is recorded (WorkbenchScene._make_answer_inspection) but never
    graded right/wrong, matching RepairIssue's own "record the choice"
    discipline - this exists to gate Continue on real engagement, not to
    score a correct answer."""

    prompt_key: str
    options: tuple[InspectionOption, ...]
    hint_key: str | None = None
    """Shown only when the workbench runs in guided mode."""
