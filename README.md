# data-science-arcade

A bilingual (Polish/English), gamified university course in practical data science, delivered as a
2D Pygame desktop application set inside the fictional company NovaMart.

30 narrative lessons take a player from raw, messy tables through grouping, joins, experiments,
causality, and a final open-ended data-incident investigation - roughly 14 hours of content in
total. Every lesson is a real, playable scene sequence with its own data, scoring, and bilingual
copy; there is no placeholder content among the 30.

The interface is minimalist and text/data-first by design: a fixed 960x540 window, mouse-driven
menus and data tools, no external art or audio assets (see `assets/ASSET_MANIFEST.md`). It is built
and released as a focused interactive course, not a fully illustrated game.

## Development

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python -m data_science_arcade
uv run pytest
```

## Controls

- Mouse: all navigation, data tools, and lesson choices are click-driven.
- `Escape`: pause the current lesson (or back out of a confirmation prompt).
- `F11`: toggle fullscreen.
- Language (English/Polish) is switched from Settings, from the main menu.

## Save data

Progress persists to a single JSON file at `~/.data_science_arcade/save.json`, written atomically
on every save. "New Course" from the main menu asks for confirmation before erasing it, since it
resets every lesson's progress.

## Developer/instructor mode

Setting `DSA_DEV_MODE=1` unlocks every lesson for demonstration purposes without touching the real
save file:

```bash
DSA_DEV_MODE=1 uv run python -m data_science_arcade
```
