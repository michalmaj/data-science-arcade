import os

DEV_MODE_ENV_VAR = "DSA_DEV_MODE"
_FALSY_VALUES = {"", "0", "false"}


def is_dev_mode() -> bool:
    """Non-primary developer/instructor mode (spec §29): unlocks every
    lesson for demonstration without touching the real save. Off by
    default; enabled by setting DSA_DEV_MODE=1 (or any non-falsy value)."""
    return os.environ.get(DEV_MODE_ENV_VAR, "").strip().lower() not in _FALSY_VALUES
