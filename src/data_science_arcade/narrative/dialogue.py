from dataclasses import dataclass

from data_science_arcade.narrative.npc import NPC

# Covers the spec §66 dialogue requirements every one of the 30 lessons
# has actually used: speaker, localized text, optional response choices.
# Conditional lines that branch on mission/lesson state were never added -
# no lesson's own narrative content ended up needing more branching than
# DialogueChoice.next_index already gives it.


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
