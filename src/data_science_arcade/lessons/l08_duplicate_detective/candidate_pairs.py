from data_science_arcade.lessons.framework.record_pair import RecordField, RecordPair

# Hand-crafted (not random): 5 candidate pairs, one headlining each variation
# type from spec §25 Lesson 08 - a genuinely correct verdict either way, no
# trap (the trap is reserved for the twist, matching every prior lesson's
# discipline of keeping guided/independent practice unambiguous). Customer
# IDs always differ between A and B - these are two separate database rows
# by definition, so ID is shown as a label, never a "matches" field.
CANDIDATE_PAIRS: tuple[RecordPair, ...] = (
    RecordPair(
        key="spelling_and_casing",
        id_a="C-10234",
        id_b="C-10391",
        hint_key="lesson.l08.pair.spelling_and_casing.hint",
        fields=(
            RecordField("lesson.l08.field.name", "Jonathan Kowalski", "Jon Kowalski", matches=False),
            RecordField("lesson.l08.field.email", "jkowalski@example.com", "JKOWALSKI@EXAMPLE.COM", matches=True),
            RecordField("lesson.l08.field.phone", "555-0142", "555-0142", matches=True),
            RecordField("lesson.l08.field.address", "12 Oak St, Warsaw", "12 Oak St, Warsaw", matches=True),
        ),
    ),
    RecordPair(
        key="changed_address",
        id_a="C-20456",
        id_b="C-20981",
        hint_key="lesson.l08.pair.changed_address.hint",
        fields=(
            RecordField("lesson.l08.field.name", "Maria Santos", "Maria Santos", matches=True),
            RecordField("lesson.l08.field.email", "maria.santos@example.com", "maria.santos@example.com", matches=True),
            RecordField("lesson.l08.field.phone", "555-0288", "555-0288", matches=True),
            RecordField("lesson.l08.field.address", "45 Elm St, Krakow", "7 Birch Ave, Krakow", matches=False),
        ),
    ),
    RecordPair(
        key="shared_phone",
        id_a="C-30112",
        id_b="C-30765",
        hint_key="lesson.l08.pair.shared_phone.hint",
        fields=(
            RecordField("lesson.l08.field.name", "Anna Nowak", "Piotr Nowak", matches=False),
            RecordField("lesson.l08.field.email", "anna.nowak@example.com", "piotr.nowak@example.com", matches=False),
            RecordField("lesson.l08.field.phone", "555-0399", "555-0399", matches=True),
            RecordField("lesson.l08.field.address", "8 Pine Rd, Gdansk", "8 Pine Rd, Gdansk", matches=True),
        ),
    ),
    RecordPair(
        key="duplicate_signup",
        id_a="C-40223",
        id_b="C-40890",
        hint_key="lesson.l08.pair.duplicate_signup.hint",
        fields=(
            RecordField("lesson.l08.field.name", "David Kim", "David Kim", matches=True),
            RecordField("lesson.l08.field.email", "david.kim@example.com", "david.kim@example.com", matches=True),
            RecordField("lesson.l08.field.phone", "555-0517", "555-0517", matches=True),
            RecordField("lesson.l08.field.address", "19 Cedar Ln, Poznan", "19 Cedar Ln, Poznan", matches=True),
        ),
    ),
    RecordPair(
        key="name_coincidence",
        id_a="C-50678",
        id_b="C-50912",
        hint_key="lesson.l08.pair.name_coincidence.hint",
        fields=(
            RecordField("lesson.l08.field.name", "Michael Chen", "Michael Chen", matches=True),
            RecordField("lesson.l08.field.email", "mchen88@example.com", "m.chen.krk@example.com", matches=False),
            RecordField("lesson.l08.field.phone", "555-0623", "555-0940", matches=False),
            RecordField("lesson.l08.field.address", "3 Maple Dr, Lodz", "61 Willow St, Wroclaw", matches=False),
        ),
    ),
)

# The correct verdict per pair - used by tests/scripts, not read by
# RecordPairScene itself (it just records whatever the player picks,
# matching every prior lesson's non-punitive pattern).
CORRECT_DECISION_BY_PAIR: dict[str, str] = {
    "spelling_and_casing": "merge",
    "changed_address": "merge",
    "shared_phone": "keep_separate",
    "duplicate_signup": "merge",
    "name_coincidence": "keep_separate",
}
