import pygame

from data_science_arcade.ui.text import wrap_text


def paginate(paragraphs: list[str], font: pygame.font.Font, max_width: int, max_lines_per_page: int) -> list[list[str]]:
    """Wraps each paragraph independently (via the existing wrap_text()),
    joins them with one blank-line separator between consecutive
    paragraphs (not after the last), then slices the flattened line list
    into pages of at most max_lines_per_page lines each.

    A paragraph longer than one page's own budget simply spans multiple
    pages, the same way a real book paginates prose - not special-cased.

    Each paragraph is whitespace-normalized first (collapsing any embedded
    \\n/\\r/repeated spaces) - pygame's own font rendering doesn't honor
    embedded newlines (it silently fuses both fragments onto one visual
    line instead of breaking), a real risk for hand-authored prose in a
    way it never was for this codebase's existing short UI copy.

    If a separator would land as the first line of a new page (a visible
    gap at the top), it's stripped - the same separator landing as the
    last line of the previous page is fine (invisible trailing
    whitespace, same as a real book's own pagination)."""
    if max_lines_per_page < 1:
        raise ValueError("max_lines_per_page must be at least 1")

    all_lines: list[str] = []
    for index, paragraph in enumerate(paragraphs):
        normalized = " ".join(paragraph.split())
        all_lines.extend(wrap_text(normalized, font, max_width))
        if index < len(paragraphs) - 1:
            all_lines.append("")

    pages: list[list[str]] = []
    for start in range(0, len(all_lines), max_lines_per_page):
        page = all_lines[start : start + max_lines_per_page]
        if start > 0 and page and page[0] == "":
            page = page[1:]
        if page:
            pages.append(page)

    return pages if pages else [[]]
