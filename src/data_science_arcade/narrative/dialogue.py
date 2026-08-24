from dataclasses import dataclass

from data_science_arcade.narrative.npc import NPC

# Covers the spec §66 dialogue requirements that have something to attach to
# right now: speaker, localized text, optional response choices. Conditional
# lines and mission-state triggers are deferred - there's no mission/lesson
# state yet for a line to condition on (that starts at Phase 7).


@dataclass(frozen=True)
class DialogueChoice:
    label_key: str
    next_index: int | None  # None ends the dialogue


@dataclass(frozen=True)
class DialogueLine:
    text_key: str
    speaker: NPC | None = None
    choices: tuple[DialogueChoice, ...] = ()


@dataclass(frozen=True)
class Dialogue:
    lines: tuple[DialogueLine, ...]
