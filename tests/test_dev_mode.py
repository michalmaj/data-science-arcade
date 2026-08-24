from data_science_arcade.progress.dev_mode import DEV_MODE_ENV_VAR, is_dev_mode


def test_defaults_to_off_when_unset(monkeypatch):
    monkeypatch.delenv(DEV_MODE_ENV_VAR, raising=False)
    assert is_dev_mode() is False


def test_off_for_common_falsy_values(monkeypatch):
    for value in ("", "0", "false", "False", "  "):
        monkeypatch.setenv(DEV_MODE_ENV_VAR, value)
        assert is_dev_mode() is False


def test_on_for_any_other_value(monkeypatch):
    for value in ("1", "true", "yes", "on"):
        monkeypatch.setenv(DEV_MODE_ENV_VAR, value)
        assert is_dev_mode() is True
