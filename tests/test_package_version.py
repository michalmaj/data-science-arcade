import tomllib
from pathlib import Path

from packaging.version import Version

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

# The last version this project has actually shipped - bump this forward
# together with pyproject.toml's own version whenever a new one ships, so
# an accidental revert (a bad merge, a stale branch, a manual edit) fails
# this test loudly instead of silently shipping an older version number
# than a prior release.
_MINIMUM_VERSION = Version("1.0.0a1")


def _pyproject_version() -> Version:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    return Version(data["project"]["version"])


def test_pyproject_version_is_valid_pep440():
    # Version(...) itself raises InvalidVersion for anything that doesn't
    # conform - this just gives that failure a readable name and location.
    _pyproject_version()


def test_pyproject_version_has_not_regressed():
    assert _pyproject_version() >= _MINIMUM_VERSION, (
        f"pyproject.toml declares {_pyproject_version()}, older than the last shipped {_MINIMUM_VERSION} - "
        "did a merge or manual edit silently roll the version back?"
    )


def test_installed_package_metadata_matches_pyproject():
    # Catches the other half of the same class of bug: pyproject.toml was
    # bumped but `uv sync` was never re-run, so the installed package's
    # own metadata (what `importlib.metadata.version()` and a built wheel
    # would actually report) still lags behind the source of truth.
    import importlib.metadata

    installed = Version(importlib.metadata.version("data-science-arcade"))
    assert installed == _pyproject_version()
