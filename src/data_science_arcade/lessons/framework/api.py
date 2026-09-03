from dataclasses import dataclass


@dataclass(frozen=True)
class APIRequestAttempt:
    """One entry in a pre-scripted, deterministic request log. A retried
    page is just another attempt for the same page_number played later -
    the console has no live retry timer of its own, it just plays a
    hand-authored, deterministic outcome back one click at a time, enough
    to teach the lesson without simulating a real HTTP client.

    `has_more`/`next_cursor`/`total_count` are the pagination/completeness
    metadata a student reads directly off the response to decide whether
    to keep paginating (and how) and whether the running total is
    trustworthy - the framing dialogue only ever tells a student that the
    endpoint paginates at all, never the per-response values themselves
    (how many pages, whether a given one has more, what its own cursor
    is) - those only ever come from a real response. Every successful
    attempt in this lesson carries the same `total_count` (the API's own
    declared total, unaffected by how any individual page went) so a
    student isn't expected to remember a number from page 1 by the time
    they reach page 6; `has_more`/`next_cursor` are genuinely per-attempt
    and are what a student should actually be reading to decide what to
    do next.

    `continuation_options`, when set, replaces the console's normal
    single action button with real choices instead - see
    ContinuationOption. Originally only ever set on a failed attempt (the
    rate-limit retry/backoff/skip choice); also used for a real,
    non-failure pagination micro-decision (follow the real `next_cursor`
    vs. resend the same request) - the name reflects that it's "what can
    happen next," not specifically retrying a failure."""

    page_number: int
    status_key: str
    records_returned: int
    is_success: bool
    has_more: bool
    total_count: int | None = None
    next_cursor: str | None = None
    continuation_options: tuple["ContinuationOption", ...] | None = None


@dataclass(frozen=True)
class ContinuationOption:
    """One real choice offered instead of the console's normal single
    action button - see APIRequestAttempt.continuation_options. `result`
    is itself a full APIRequestAttempt (its own status/records/has_more/
    continuation_options), so a chain of choices - e.g. retrying
    immediately failing a second time, which then offers a real, narrower
    option set with "retry immediately" no longer on it - is just this
    same structure one level deeper, never special-cased in the scene
    itself: whatever the most recently resolved attempt's own
    `continuation_options` says is what's on offer next, resolved or not
    is just "is `continuation_options` None." Used for both a failure
    (rate-limit retry/backoff/skip) and a real, successful pagination
    micro-decision (follow `next_cursor` vs. resend the same request,
    which returns the same page again rather than new data - a student
    who picks it isn't punished, just shown the same response until they
    pick the option that actually reads the returned cursor)."""

    key: str
    label_key: str
    result: APIRequestAttempt
