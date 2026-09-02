from dataclasses import dataclass


@dataclass(frozen=True)
class APIRequestAttempt:
    """One entry in a pre-scripted, deterministic request log. A retried
    page is just another attempt for the same page_number played later -
    the console has no live retry timer of its own, it just plays a
    hand-authored, deterministic outcome back one click at a time, enough
    to teach the lesson without simulating a real HTTP client.

    `has_more`/`total_count` are the pagination/completeness metadata the
    student has to read to decide whether to keep paginating and whether
    the running total is trustworthy - never stated in dialogue. Every
    real attempt in this lesson carries the same `total_count` (the API's
    own declared total, unaffected by how any individual page went) so a
    student isn't expected to remember a number from page 1 by the time
    they reach page 6; `has_more` is genuinely per-attempt and is what a
    student should actually be reading to know when to stop.

    `retry_options`, only set on a failed attempt, replaces the console's
    normal single "Send request" button with the real choices available
    instead - see RetryOption."""

    page_number: int
    status_key: str
    records_returned: int
    is_success: bool
    has_more: bool
    total_count: int | None = None
    retry_options: tuple["RetryOption", ...] | None = None


@dataclass(frozen=True)
class RetryOption:
    """One real choice offered after a failed request - see
    APIRequestAttempt.retry_options. `result` is itself a full
    APIRequestAttempt (its own status/records/has_more/retry_options),
    so a chain of choices - e.g. retrying immediately failing a second
    time, which then offers a real, narrower option set with "retry
    immediately" no longer on it - is just this same structure one level
    deeper, never special-cased in the scene itself: whatever the most
    recently resolved attempt's own `retry_options` says is what's on
    offer next, resolved or not is just "is `retry_options` None."""

    key: str
    label_key: str
    result: APIRequestAttempt
