from dataclasses import dataclass


@dataclass(frozen=True)
class NPC:
    """A recurring character (spec §6.3). avatar_color/avatar_initial are a
    placeholder portrait - swap for a real portrait image in the art pass
    (Phase 14) without changing anything that references this NPC."""

    id: str
    name_key: str
    role_key: str
    avatar_color: tuple[int, int, int]
    avatar_initial: str


MENTOR = NPC(
    id="mentor",
    name_key="npc.mentor.name",
    role_key="npc.mentor.role",
    avatar_color=(58, 214, 255),
    avatar_initial="M",
)
