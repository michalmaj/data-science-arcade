from dataclasses import dataclass


@dataclass(frozen=True)
class APIRequestAttempt:
    """One entry in a pre-scripted, deterministic request log (spec §25
    Lesson 03 'API Courier'). A retried page is just another attempt for
    the same page_number later in the sequence - the console has no retry
    state machine of its own, it just plays the log back one click at a
    time, which is enough to teach the lesson without simulating a real
    HTTP client."""

    page_number: int
    status_key: str
    records_returned: int
    is_success: bool
