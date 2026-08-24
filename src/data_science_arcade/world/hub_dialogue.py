from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR

MENTOR_GREETING = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line2"),
    )
)
