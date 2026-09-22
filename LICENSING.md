# Licensing

This project separates two kinds of material and licenses each one differently.

## Code — MIT (`LICENSE-CODE`)

Everything that makes the application run, regardless of which directory it
lives in:

- All Python source under `src/data_science_arcade/` that implements
  behavior — the scene/state system (`app/`, `core/`), UI widgets (`ui/`),
  the data engine, localization lookup mechanism, progress/save system,
  the scoring *framework* (dimension enums, evaluation plumbing), and every
  lesson's own `scenario.py`/`scoring.py` control flow and stage logic.
- All tests under `tests/`.
- GitHub Actions workflows and any other CI/build configuration under
  `.github/`.
- Packaging and build tooling (`pyproject.toml`, `uv.lock`, the build
  backend configuration).
- Config files and developer tooling (`.python-version`, `.gitignore`,
  editor/linter config, etc.).

## Educational content — CC BY-SA 4.0 (`LICENSE-CONTENT`)

The authored instructional material itself:

- Lesson narratives, briefings, dialogue, questions, answer options,
  feedback/observation copy, and objectives — the actual words a student
  reads, wherever they're stored (primarily `src/data_science_arcade/
  localization/locales/en.json` and `pl.json`, plus the narrative text
  embedded directly in a lesson's `scenario.py`, such as dialogue
  structure and speaker sequencing).
- The Handbook and glossary content (`handbook/registry.py`'s authored
  article/term selection, categorization, and cross-references, and the
  corresponding prose in the locale files).
- The EN/PL instructional translations as a body of work.
- Authored educational datasets and scenarios that are themselves part of
  a lesson's content design — the specific numbers, patterns, edge cases,
  and hidden ground truth a lesson's `data.py`/`*_data.py` module
  constructs, and the pedagogical scenario/business narrative those
  numbers exist to teach.
- Curriculum and documentation content describing what the course teaches
  and why (e.g. `decisions/CONTENT_STYLE_GUIDE.md`,
  `decisions/TERMINOLOGY_GUIDE.md`, and equivalent authored curriculum
  documents, where present and tracked).
- Any future authored educational art or audio, unless that specific
  asset ships with its own license (see `assets/ASSET_MANIFEST.md`, which
  records provenance and license for every third-party asset).

## Files that mix both

Several files necessarily contain both kinds of material at once — most
notably each lesson's `scenario.py` (control-flow code authored alongside
narrative/dialogue structure) and `data.py`/`*_data.py` modules (a Python
data generator implementing an authored educational dataset design), and
`handbook/registry.py` (a plain data structure whose *shape* is code but
whose *contents* — which articles exist, how they're categorized, how
they cross-reference each other — are curriculum decisions).

For these files: the implementation — control flow, function/class
structure, the mechanism that reads and executes the content — is MIT.
The authored educational expression — narrative wording, the pedagogical
design of a dataset, the choice and arrangement of curriculum content —
is CC BY-SA 4.0. This project does not physically separate these into
different files; the license that applies to a given piece of a mixed
file follows from what that piece *is* (mechanism vs. authored content),
not from which file it happens to live in.

## Why two licenses

The software exists to run the course; the course is what's actually
being taught. MIT keeps the application itself maximally reusable as
software (fork it, embed the engine, build a different course on top of
it). CC BY-SA 4.0 keeps the authored lessons free to use, adapt, and
redistribute for educational purposes, while requiring that adaptations
of the *content* remain similarly open (share-alike) and that the
original authorship is credited — appropriate for instructional material
in a way MIT's terms aren't designed for.
