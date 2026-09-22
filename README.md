# data-science-arcade

[![CI](https://github.com/michalmaj/data-science-arcade/actions/workflows/ci.yml/badge.svg)](https://github.com/michalmaj/data-science-arcade/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/michalmaj/data-science-arcade?include_prereleases&label=release)](https://github.com/michalmaj/data-science-arcade/releases)
[![Status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/michalmaj/data-science-arcade/releases)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)
[![Pygame](https://img.shields.io/badge/built%20with-Pygame-1a1a2e)](https://www.pygame.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Lessons](https://img.shields.io/badge/lessons-30-success)](README.md)
[![Languages](https://img.shields.io/badge/lang-PL%20%7C%20EN-blue)](README.md)
[![Code license](https://img.shields.io/badge/code%20license-MIT-green)](LICENSE-CODE)
[![Content license](https://img.shields.io/badge/content%20license-CC%20BY--SA%204.0-lightgrey)](LICENSE-CONTENT)

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

## Licensing

This project uses two licenses: the software is [MIT-licensed](LICENSE-CODE), and the educational
content (lessons, Handbook, glossary, EN/PL instructional text) is licensed under
[CC BY-SA 4.0](LICENSE-CONTENT). See [LICENSING.md](LICENSING.md) for exactly what falls under each.
