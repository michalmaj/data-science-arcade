import pytest

from data_science_arcade.localization.service import (
    DEFAULT_LOCALE,
    LOCALE_ENDONYMS,
    SUPPORTED_LOCALES,
    Localization,
    load_all_locales,
)


def test_every_supported_locale_has_an_endonym():
    assert set(LOCALE_ENDONYMS) == set(SUPPORTED_LOCALES)


def test_locale_files_have_exactly_the_same_keys():
    strings = load_all_locales()
    key_sets = {code: set(strings[code]) for code in SUPPORTED_LOCALES}
    reference = key_sets[DEFAULT_LOCALE]
    for code, keys in key_sets.items():
        assert keys == reference, f"{code}.json keys differ from {DEFAULT_LOCALE}.json"


def test_no_locale_file_has_a_blank_value():
    strings = load_all_locales()
    for code, table in strings.items():
        blanks = [key for key, value in table.items() if not value.strip()]
        assert not blanks, f"{code}.json has blank values for: {blanks}"


def test_defaults_to_english():
    localization = Localization()
    assert localization.locale == DEFAULT_LOCALE


def test_looks_up_the_active_locale():
    localization = Localization(strings={"en": {"greeting": "Hi"}, "pl": {"greeting": "Cześć"}})
    assert localization.t("greeting") == "Hi"
    localization.set_locale("pl")
    assert localization.t("greeting") == "Cześć"


def test_falls_back_to_english_when_the_key_is_missing_in_the_active_locale():
    localization = Localization(locale="pl", strings={"en": {"only_en": "value"}, "pl": {}})
    assert localization.t("only_en") == "value"


def test_returns_a_visible_marker_when_the_key_is_missing_everywhere():
    localization = Localization(strings={"en": {}, "pl": {}})
    assert localization.t("nope") == "??nope??"


def test_set_locale_rejects_an_unsupported_code():
    localization = Localization(strings={"en": {}, "pl": {}})
    with pytest.raises(ValueError):
        localization.set_locale("de")
