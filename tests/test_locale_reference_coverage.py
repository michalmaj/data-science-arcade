import ast
from pathlib import Path

from data_science_arcade.localization.service import DEFAULT_LOCALE, load_all_locales

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "data_science_arcade"

_TEXT_KEY_DATACLASS_NAMES = {"DialogueLine", "FeedbackObservation"}


def _literal_str(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_func_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _collect_literal_key_references() -> dict[str, list[str]]:
    """Every literal locale-key reference this codebase's own source makes
    through one of a few well-known, statically-resolvable call shapes:
    `DialogueLine(text_key=...)`, `FeedbackObservation("...", ...)` (its
    `text_key` is positional-first), and any `*.t("...")` call (covers
    `loc.t(...)`, `localization.t(...)`, `app.localization.t(...)`).

    Deliberately does NOT try to resolve a dynamic key - an f-string
    (`f"lesson.l16...option.{key}"`), a `.format()`-built string, or a key
    read out of a variable/tuple (`FeedbackObservation(key, ...)`) - since
    those depend on runtime data (or on a set the caller already builds
    and iterates exhaustively) that a static, single-call-site pass can't
    safely enumerate. Those stay each lesson's own responsibility, backed
    by that lesson's own exhaustive per-option test coverage instead."""
    references: dict[str, list[str]] = {}

    def _record(key: str, location: str) -> None:
        references.setdefault(key, []).append(location)

    for path in sorted(SRC_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func_name = _call_func_name(node)
            if func_name is None:
                continue
            location = f"{path.relative_to(SRC_ROOT.parent.parent)}:{node.lineno}"

            if func_name in _TEXT_KEY_DATACLASS_NAMES:
                key = None
                for kw in node.keywords:
                    if kw.arg == "text_key":
                        key = _literal_str(kw.value)
                if key is None and node.args:
                    key = _literal_str(node.args[0])
                if key is not None:
                    _record(key, location)
                continue

            if func_name == "t" and isinstance(node.func, ast.Attribute) and node.args:
                key = _literal_str(node.args[0])
                if key is not None:
                    _record(key, location)

    return references


def test_every_literal_locale_key_reference_exists_in_the_default_locale():
    strings = load_all_locales()
    default_keys = set(strings[DEFAULT_LOCALE])
    references = _collect_literal_key_references()
    missing = {key: locations for key, locations in references.items() if key not in default_keys}
    assert not missing, f"Literal locale key references missing from {DEFAULT_LOCALE}.json: {missing}"


def test_the_static_scan_actually_finds_a_meaningful_number_of_references():
    # A regression guard on the scan itself: if a future refactor renames
    # DialogueLine/FeedbackObservation or changes how `.t(...)` is called
    # everywhere, the coverage test above would start passing vacuously
    # (an empty reference set trivially has no missing keys). 500+ is
    # comfortably below the real count (thousands) but far above zero.
    references = _collect_literal_key_references()
    assert len(references) > 500
