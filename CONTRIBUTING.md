# Contributing

## Setup

```bash
uv sync
uv run pytest -q
```

## Before opening a PR

- **EN/PL locale parity**: every user-visible string lives in both
  `src/data_science_arcade/localization/locales/en.json` and `pl.json`.
  Edit these with a text-editing tool, not a script that re-serializes the
  whole file (a plain `json.load`/`json.dump` round-trip silently strips
  the blank-line separators between sections). Both files must end up
  with exactly the same set of keys.
- **Screenshots for UI/localization changes**: if you touch a scene's
  layout or add/change locale text, render the affected screen(s) in
  both languages and check by eye that nothing overlaps or overflows -
  pygame doesn't clip anything by default, and a change that only breaks
  Polish (longer strings) or a specific dimension count won't show up in
  English or in the common case.
- **Regression tests for lesson/statistics changes**: a fix to a lesson's
  scoring, a dataset, or a claimed number needs a test that would have
  caught the original bug, not just a corrected value.
- Run `uv run pytest -q` before pushing - CI runs the same suite on
  Linux and macOS.

## Code style

- All code - identifiers, comments, docstrings, test names - is English
  only, regardless of the bilingual in-app content.
- Follow the patterns already established in the file/module you're
  touching rather than introducing a new one for the same problem.
