# data-science-arcade

A bilingual (Polish/English), gamified university course in practical data science, delivered as a
2D Pygame desktop application set inside the fictional company NovaMart.

The project is in early bootstrap — no lessons exist yet. Product and implementation direction live
in a local, gitignored specification (`decisions/PROJECT_SPEC.md`); see `CLAUDE.md` for a summary of
the architecture and workflow rules for contributors.

## Development

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python -m data_science_arcade
uv run pytest
```
