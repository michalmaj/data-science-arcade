from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief


@dataclass(frozen=True)
class AnalyticalAction:
    """Something a student actually did during a lesson - general and
    independent of Dataset.history (data_engine/dataset.py's own
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
    """Accumulates one lesson *instance's* worth of analytical actions,
    evidence, and (eventually) a decision - constructed once per lesson
    (alongside the `collected` dict every scenario.py already builds) and
    threaded via closures into every stage that needs it, so evidence
    discovered in an earlier stage is still visible in a later one.

    Recording is idempotent by content: recording an action/evidence item
    whose (label_key, python_code) - or (label_key, source_action_id) for
    evidence - exactly matches one already present returns the *existing*
    entry instead of appending a duplicate. This matters concretely for
    Lesson 06: guided_work and independent_challenge deliberately present
    the *same* issues again, and a student picking the same (rewarded,
    expected) correct option in both rounds must not double the Python
    Mirror or the evidence list. Recording genuinely different content
    (e.g. the wrong option in one round, the right one in the other)
    still records both - an honest record of two different attempts.

    Survives checkpoint/resume via to_dict()/restore_from_dict(), stashed
    by the owning scenario.py inside the same generic `collected` dict
    LessonRunner already checkpoints (e.g. collected["analytical_context"])
    - deliberately not a new typed LessonCheckpoint field, since that would
    mean touching the shared runtime foundation every one of the 30
    lessons uses for a concept exactly one lesson uses today. Every field
    on every dataclass here is already plain str/tuple[str, ...], so no
    new serialization machinery is needed - just explicit dict/list
    construction, same as everything else already living in `collected`.

    A bespoke scene emits into a LessonContext directly via record_action/
    record_evidence without needing to know Workbench exists; Workbench
    reads from the same object without needing to know which scene
    populated it - the two communicate only through this shared object.
    """

    def __init__(
        self,
        actions: tuple[AnalyticalAction, ...] = (),
        evidence: tuple[EvidenceItem, ...] = (),
        decision: DecisionState | None = None,
        next_id: int = 1,
    ) -> None:
        self._actions: list[AnalyticalAction] = list(actions)
        self._evidence: list[EvidenceItem] = list(evidence)
        self._decision = decision
        self._next_id = next_id

    def _new_id(self, prefix: str) -> str:
        id_ = f"{prefix}_{self._next_id}"
        self._next_id += 1
        return id_

    def record_action(self, label_key: str, python_code: str | None = None) -> AnalyticalAction:
        for existing in self._actions:
            if existing.label_key == label_key and existing.python_code == python_code:
                return existing
        action = AnalyticalAction(id=self._new_id("action"), label_key=label_key, python_code=python_code)
        self._actions.append(action)
        return action

    def record_evidence(self, label_key: str, source_action: AnalyticalAction | None = None) -> EvidenceItem:
        source_action_id = source_action.id if source_action is not None else None
        for existing in self._evidence:
            if existing.label_key == label_key and existing.source_action_id == source_action_id:
                return existing
        evidence = EvidenceItem(id=self._new_id("evidence"), label_key=label_key, source_action_id=source_action_id)
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

    def to_dict(self) -> dict:
        return {
            "actions": [{"id": a.id, "label_key": a.label_key, "python_code": a.python_code} for a in self._actions],
            "evidence": [
                {"id": e.id, "label_key": e.label_key, "source_action_id": e.source_action_id} for e in self._evidence
            ],
            "decision": (
                {"choices": dict(self._decision.choices), "supporting_evidence_ids": list(self._decision.supporting_evidence_ids)}
                if self._decision is not None
                else None
            ),
            "next_id": self._next_id,
        }

    def restore_from_dict(self, data: dict) -> None:
        """In-place restore (never rebind self._actions/etc. - a lesson's
        stage closures already hold a reference to this exact object).
        No-ops if `data` isn't strictly ahead of current state, which is
        what makes calling this unconditionally at the top of every
        analytical stage closure safe: a same-session call (restoring a
        snapshot this same object just wrote a moment ago) can never roll
        back state recorded since. Also no-ops on any malformed/corrupt
        payload rather than raising deep inside gameplay at stage-entry -
        matching progress/store.py's own "one bad entry can't cost the
        rest" discipline, since nothing else in this codebase unpacks
        JSON-sourced data into a dataclass constructor without that
        defensive boundary."""
        try:
            next_id = int(data.get("next_id", 1))
            if next_id <= self._next_id:
                return
            actions = tuple(
                AnalyticalAction(id=a["id"], label_key=a["label_key"], python_code=a.get("python_code"))
                for a in data.get("actions", [])
            )
            evidence = tuple(
                EvidenceItem(id=e["id"], label_key=e["label_key"], source_action_id=e.get("source_action_id"))
                for e in data.get("evidence", [])
            )
            raw_decision = data.get("decision")
            decision = (
                DecisionState(
                    choices=dict(raw_decision["choices"]),
                    supporting_evidence_ids=tuple(raw_decision.get("supporting_evidence_ids", ())),
                )
                if raw_decision is not None
                else None
            )
        except (KeyError, TypeError, ValueError):
            return

        self._actions = list(actions)
        self._evidence = list(evidence)
        self._decision = decision
        self._next_id = next_id
