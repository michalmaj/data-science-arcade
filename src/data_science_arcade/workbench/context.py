import itertools
from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class AnalyticalAction:
    """Something a student actually did during a lesson stage - general
    and independent of Dataset.history (data_engine/dataset.py's own
    PipelineStep/python_mirror), which stays exactly as it is and keeps
    backing TwistRevealScene everywhere. Not every analytical action
    transforms a Dataset - picking a finding or a verdict is one too."""

    id: str
    label_key: str
    python_code: str | None = None


@dataclass(frozen=True)
class EvidenceItem:
    """A fact or finding discovered during analysis - deliberately not the
    same thing as lessons/framework/evaluation.py's FeedbackObservation,
    which assesses the *student's own reasoning quality*, not a fact about
    the data. source_action_id, when set, is a real AnalyticalAction.id
    this evidence came from - never a hand-typed string, so it can't drift
    out of sync with the action it actually references."""

    id: str
    label_key: str
    source_action_id: str | None = None


@dataclass(frozen=True)
class DecisionState:
    choices: AnalyticalBrief
    supporting_evidence_ids: tuple[str, ...] = ()


class LessonContext:
    """Accumulates one lesson *stage's* worth of analytical actions,
    evidence, and (eventually) a decision - constructed fresh per stage,
    matching Dataset's own per-stage lifetime in every scene that builds
    one (e.g. Lesson 06's guided_work/independent_challenge each build
    their own fresh Dataset). Deliberately NOT shared across a whole
    lesson attempt: guided and independent rounds must never blend (this
    codebase already keeps results like LessonSixResult's
    guided_resolution/independent_resolution strictly separate), and a
    shared id-namespace across two rounds risks a real id collision the
    moment a student picks the same thing in both.

    Purely in-memory, not checkpointed - not JSON-serializable, and this
    concept didn't exist when checkpoint/resume was built. A player who
    quits mid-stage and resumes later gets a fresh, empty context; that's
    expected, not a bug.

    A bespoke scene emits into a LessonContext directly via record_action/
    record_evidence without needing to know Workbench exists; Workbench
    reads from the same object without needing to know which scene
    populated it - the two communicate only through this shared object.
    """

    def __init__(self) -> None:
        self._actions: list[AnalyticalAction] = []
        self._evidence: list[EvidenceItem] = []
        self._decision: DecisionState | None = None
        self._id_counter = itertools.count(1)

    def record_action(self, label_key: str, python_code: str | None = None) -> AnalyticalAction:
        action = AnalyticalAction(id=f"action_{next(self._id_counter)}", label_key=label_key, python_code=python_code)
        self._actions.append(action)
        return action

    def record_evidence(self, label_key: str, source_action: AnalyticalAction | None = None) -> EvidenceItem:
        evidence = EvidenceItem(
            id=f"evidence_{next(self._id_counter)}",
            label_key=label_key,
            source_action_id=source_action.id if source_action is not None else None,
        )
        self._evidence.append(evidence)
        return evidence

    def set_decision(self, decision: DecisionState) -> None:
        self._decision = decision

    @property
    def actions(self) -> tuple[AnalyticalAction, ...]:
        return tuple(self._actions)

    @property
    def evidence(self) -> tuple[EvidenceItem, ...]:
        return tuple(self._evidence)

    @property
    def decision(self) -> DecisionState | None:
        return self._decision

    def python_mirror(self) -> str:
        return "\n".join(action.python_code for action in self._actions if action.python_code)
