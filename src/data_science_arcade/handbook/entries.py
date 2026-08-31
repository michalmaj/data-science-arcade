from dataclasses import dataclass


@dataclass(frozen=True)
class HandbookEntry:
    """A full-prose reference article (spec §46's theory/glossary layer).
    `related_entry_ids` may point at another HandbookEntry OR a
    GlossaryEntry - see registry.py's find_entry(), which searches the
    union of both. `source_keys` is deliberately often empty: a source is
    only ever added once it's been concretely verified (decisions/
    CONTENT_STYLE_GUIDE.md §9), never reconstructed from memory."""

    id: str
    title_key: str
    category_key: str
    body_paragraph_keys: tuple[str, ...]
    related_entry_ids: tuple[str, ...] = ()
    source_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class GlossaryEntry:
    """A short lookup term (2-5 sentences, CONTENT_STYLE_GUIDE §5) -
    deliberately no pagination at this length. `related_entry_id` may
    point at another GlossaryEntry OR a HandbookEntry, same as above."""

    id: str
    term_key: str
    definition_key: str
    related_entry_id: str | None = None
