from data_science_arcade.lessons.framework.segment import Segment, SegmentRequest, SliceOption
from data_science_arcade.lessons.l15_segment_detective.funnel_data import (
    generate_channel_funnel,
    generate_device_funnel,
    generate_region_funnel,
    segment_rate,
)


def _slice_option(key: str, label_key: str, dataset, segment_specs: list[tuple[str, str]]) -> SliceOption:
    segments = tuple(
        Segment(
            segment_key,
            segment_label_key,
            before_rate=segment_rate(dataset, "Q1", segment_key),
            after_rate=segment_rate(dataset, "Q2", segment_key),
        )
        for segment_key, segment_label_key in segment_specs
    )
    return SliceOption(key, label_key, segments)


DEVICE_OPTION = _slice_option(
    "device",
    "lesson.l15.slice.device",
    generate_device_funnel(),
    [("mobile", "lesson.l15.segment.mobile"), ("desktop", "lesson.l15.segment.desktop")],
)
REGION_OPTION = _slice_option(
    "region",
    "lesson.l15.slice.region",
    generate_region_funnel(),
    [("eu", "lesson.l15.segment.eu"), ("us", "lesson.l15.segment.us")],
)
CHANNEL_OPTION = _slice_option(
    "channel",
    "lesson.l15.slice.channel",
    generate_channel_funnel(),
    [("organic", "lesson.l15.segment.organic"), ("paid", "lesson.l15.segment.paid")],
)

# Hand-crafted, no trap outside the twist (matching every prior lesson's
# discipline): each request names one team's specific complaint, and the
# correct slice is whichever dimension actually contains that team's own
# segment - checking a different dimension wouldn't verify their number
# either way, even though (as the twist reveals) every dimension shows
# the same kind of within-segment decline. Correct-option index varies
# across all three requests so no single index reveals the answer.
SEGMENT_REQUESTS: tuple[SegmentRequest, ...] = (
    SegmentRequest(
        key="mobile_conversion_complaint",
        prompt_key="lesson.l15.request.mobile_conversion_complaint.prompt",
        hint_key="lesson.l15.request.mobile_conversion_complaint.hint",
        options=(REGION_OPTION, CHANNEL_OPTION, DEVICE_OPTION),
    ),
    SegmentRequest(
        key="eu_region_complaint",
        prompt_key="lesson.l15.request.eu_region_complaint.prompt",
        hint_key="lesson.l15.request.eu_region_complaint.hint",
        options=(DEVICE_OPTION, REGION_OPTION, CHANNEL_OPTION),
    ),
    SegmentRequest(
        key="paid_channel_complaint",
        prompt_key="lesson.l15.request.paid_channel_complaint.prompt",
        hint_key="lesson.l15.request.paid_channel_complaint.hint",
        options=(CHANNEL_OPTION, DEVICE_OPTION, REGION_OPTION),
    ),
)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "mobile_conversion_complaint": "device",
    "eu_region_complaint": "region",
    "paid_channel_complaint": "channel",
}
