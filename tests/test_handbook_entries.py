from data_science_arcade.handbook.registry import GLOSSARY_ENTRIES, HANDBOOK_ENTRIES, find_entry
from data_science_arcade.localization.service import load_all_locales

LOCALES = load_all_locales()


def _resolves_in_both_locales(key: str) -> bool:
    return key in LOCALES["en"] and key in LOCALES["pl"]


def test_no_duplicate_ids_within_or_across_registries():
    # related_entry_ids/related_entry_id are bare strings that can point
    # into either registry - a collision would make find_entry ambiguous.
    all_ids = [entry.id for entry in HANDBOOK_ENTRIES] + [entry.id for entry in GLOSSARY_ENTRIES]
    assert len(all_ids) == len(set(all_ids))


def test_every_handbook_entry_has_at_least_one_body_paragraph():
    for entry in HANDBOOK_ENTRIES:
        assert len(entry.body_paragraph_keys) > 0


def test_every_handbook_related_entry_id_resolves_via_the_union():
    for entry in HANDBOOK_ENTRIES:
        for related_id in entry.related_entry_ids:
            assert find_entry(related_id) is not None, f"{entry.id} references missing related id {related_id!r}"


def test_every_glossary_related_entry_id_resolves_via_the_union():
    for entry in GLOSSARY_ENTRIES:
        if entry.related_entry_id is not None:
            assert find_entry(entry.related_entry_id) is not None, f"{entry.id} references missing related id {entry.related_entry_id!r}"


def test_find_entry_returns_none_for_an_unknown_id():
    assert find_entry("does_not_exist") is None


def test_find_entry_finds_both_handbook_and_glossary_ids():
    assert find_entry(HANDBOOK_ENTRIES[0].id) is HANDBOOK_ENTRIES[0]
    assert find_entry(GLOSSARY_ENTRIES[0].id) is GLOSSARY_ENTRIES[0]


def test_every_handbook_entry_key_resolves_in_both_locales():
    for entry in HANDBOOK_ENTRIES:
        assert _resolves_in_both_locales(entry.title_key), entry.title_key
        assert _resolves_in_both_locales(entry.category_key), entry.category_key
        for key in entry.body_paragraph_keys:
            assert _resolves_in_both_locales(key), key
        for key in entry.source_keys:
            assert _resolves_in_both_locales(key), key


def test_every_glossary_entry_key_resolves_in_both_locales():
    for entry in GLOSSARY_ENTRIES:
        assert _resolves_in_both_locales(entry.term_key), entry.term_key
        assert _resolves_in_both_locales(entry.definition_key), entry.definition_key


def test_no_handbook_body_paragraph_contains_a_raw_newline():
    # pygame's own font rendering doesn't honor embedded newlines - it
    # fuses fragments onto one visual line instead of breaking, silently.
    # ui/handbook_pagination.py normalizes defensively too, but catching
    # this at the content source is cheaper than relying on that alone.
    for entry in HANDBOOK_ENTRIES:
        for key in entry.body_paragraph_keys:
            for locale in ("en", "pl"):
                text = LOCALES[locale][key]
                assert "\n" not in text and "\r" not in text, key


def test_no_glossary_definition_contains_a_raw_newline():
    for entry in GLOSSARY_ENTRIES:
        for locale in ("en", "pl"):
            text = LOCALES[locale][entry.definition_key]
            assert "\n" not in text and "\r" not in text, entry.id
