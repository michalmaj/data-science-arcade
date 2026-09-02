import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

PAGES_SCHEMA = Schema(
    columns=(
        ColumnSchema("page_number", "int64"),
        ColumnSchema("page_size", "int64"),
        ColumnSchema("actual_count", "int64"),
        ColumnSchema("status", "string"),
        ColumnSchema("has_more", "bool"),
    )
)

# Hand-crafted (not random): true total cancellation events last week is
# 137, never shown to the student directly - only via the API's own
# declared total_count metadata, discovered the same way every other
# lesson's hidden ground truth is. At PAGE_SIZE=25, a clean pull is 6
# pages (5 full + a naturally-smaller final page of 12 - that alone is
# not a bug). Page 3 silently returns fewer records than it should
# (a transient backend shard fault, no error surfaced, has_more still
# true) - a permanent loss of 9 real records nothing in this lesson
# retrieves. Page 5 is genuinely rate-limited on the first attempt; a
# correct backoff recovers its real, full 25 - unlike page 3's shortfall,
# this one *is* fully recoverable, which is exactly why the two failure
# modes must not be conflated (see scenario.py's Known Gap options).
PAGE_SIZE = 25
TOTAL_COUNT = 137
ESCALATION_THRESHOLD = 130
SHORTFALL_PAGE = 3
SHORTFALL_ACTUAL = 16
RATE_LIMITED_PAGE = 5

# The best a perfectly-executed pull (correct backoff, nothing skipped)
# actually achieves - still 9 short of TOTAL_COUNT, since page 3's loss
# is never recovered by anything this lesson's console does. A student
# who skips page 5 instead of backing off ends up further short still
# (BEST_ACHIEVABLE_TOTAL - PAGE_SIZE); both real running totals are
# computed live by APIConsoleScene itself, never read from here - this
# module only ever describes the API's own server-side record of what
# each page actually contained, not any one student's own choices.
BEST_ACHIEVABLE_TOTAL = 4 * PAGE_SIZE + SHORTFALL_ACTUAL + 12  # 128


def generate_pages() -> Dataset:
    """The API's own server-side record of what each page actually
    contained when pulled correctly - real for every student regardless
    of their own retry choices, unlike the live running total
    APIConsoleScene itself tracks per session."""
    rows = [
        (1, PAGE_SIZE, PAGE_SIZE, "ok", True),
        (2, PAGE_SIZE, PAGE_SIZE, "ok", True),
        (SHORTFALL_PAGE, PAGE_SIZE, SHORTFALL_ACTUAL, "ok", True),
        (4, PAGE_SIZE, PAGE_SIZE, "ok", True),
        (RATE_LIMITED_PAGE, PAGE_SIZE, PAGE_SIZE, "ok", True),
        (6, PAGE_SIZE, 12, "ok", False),
    ]
    frame = pd.DataFrame(rows, columns=["page_number", "page_size", "actual_count", "status", "has_more"])
    step = PipelineStep(
        "prepared",
        python_code="pages = pd.DataFrame(request_log)  # the API's own server-side record, one row per page",
    )
    return Dataset(name="pages", frame=frame, schema=PAGES_SCHEMA, history=(step,))


def page_shortfall(dataset: Dataset, page_number: int) -> int:
    row = dataset.frame[dataset.frame["page_number"] == page_number].iloc[0]
    return int(row["page_size"] - row["actual_count"])


# --- Optional mastery: a second, smaller pull with a different trap ---
#
# True total 58, page_size 25 -> a clean pull is 3 pages (25, 25, and a
# naturally-smaller last page of 8). The trap is on that very last page:
# it should be 8, but the real log only ever delivered 3 - has_more is
# correctly false (it genuinely is the last page) and nothing about its
# size alone looks wrong, since a small final page is normal. Only
# checking the declared total_count (58) against the real received sum
# (53) catches it - the deeper version of the required path's own skill,
# since there's no has_more=true-after-a-short-page cue to lean on here.
MASTERY_PAGE_SIZE = 25
MASTERY_TOTAL_COUNT = 58
MASTERY_RECEIVED_TOTAL = 25 + 25 + 3
