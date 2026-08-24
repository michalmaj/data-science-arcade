import json
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"
SUPPORTED_LOCALES = ("en", "pl")
DEFAULT_LOCALE = "en"
LOCALE_ENDONYMS = {"en": "English", "pl": "Polski"}


def load_all_locales() -> dict[str, dict[str, str]]:
    return {
        code: json.loads((LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8"))
        for code in SUPPORTED_LOCALES
    }


class Localization:
    """Key -> string lookup for the active locale, with an English fallback.

    A missing key never crashes the game: it falls back to English, and if
    that's missing too, a visibly-broken "??key??" marker is returned so a
    missing translation is easy to spot during development.
    """

    def __init__(
        self,
        locale: str = DEFAULT_LOCALE,
        strings: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self._strings = strings if strings is not None else load_all_locales()
        self.locale = locale if locale in self._strings else DEFAULT_LOCALE

    def set_locale(self, locale: str) -> None:
        if locale not in self._strings:
            raise ValueError(f"Unsupported locale: {locale!r}")
        self.locale = locale

    def t(self, key: str) -> str:
        value = self._strings.get(self.locale, {}).get(key)
        if value is not None:
            return value
        fallback = self._strings.get(DEFAULT_LOCALE, {}).get(key)
        if fallback is not None:
            return fallback
        return f"??{key}??"
