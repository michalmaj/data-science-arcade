from data_science_arcade.workbench.context import DecisionState, LessonContext


def test_starts_with_nothing_recorded():
    context = LessonContext()
    assert context.actions == ()
    assert context.evidence == ()
    assert context.decision is None


def test_record_action_returns_it_and_appends_it_in_order():
    context = LessonContext()

    first = context.record_action("first", python_code="a = 1")
    second = context.record_action("second")

    assert context.actions == (first, second)
    assert first.label_key == "first"
    assert first.python_code == "a = 1"
    assert second.python_code is None


def test_actions_get_unique_ids_even_with_the_same_label():
    context = LessonContext()

    one = context.record_action("same_label")
    two = context.record_action("same_label")

    assert one.id != two.id


def test_record_evidence_references_a_real_action_id_not_a_hand_typed_string():
    context = LessonContext()
    action = context.record_action("fixed_price_column", python_code="x = 1")

    evidence = context.record_evidence("price had a decimal separator issue", source_action=action)

    assert context.evidence == (evidence,)
    assert evidence.source_action_id == action.id


def test_evidence_without_a_source_action_is_allowed():
    context = LessonContext()

    evidence = context.record_evidence("a finding with no backing action")

    assert evidence.source_action_id is None


def test_set_decision_is_read_back_via_the_decision_property():
    context = LessonContext()
    decision = DecisionState(choices={"field": "option"}, supporting_evidence_ids=("evidence_1",))

    context.set_decision(decision)

    assert context.decision is decision


def test_python_mirror_joins_only_actions_that_have_real_code_in_order():
    context = LessonContext()
    context.record_action("no code here")
    context.record_action("first line", python_code="a = 1")
    context.record_action("also no code")
    context.record_action("second line", python_code="b = 2")

    assert context.python_mirror() == "a = 1\nb = 2"


def test_python_mirror_is_empty_string_when_nothing_has_code():
    context = LessonContext()
    context.record_action("no code")

    assert context.python_mirror() == ""


def test_two_separate_contexts_do_not_share_ids_or_state():
    first = LessonContext()
    second = LessonContext()

    action_a = first.record_action("a")
    action_b = second.record_action("b")

    assert first.actions == (action_a,)
    assert second.actions == (action_b,)
    # Both start their own counter at 1 - fine, since uniqueness only needs
    # to hold *within* one context, matching its fresh-per-stage lifetime.
    assert action_a.id == action_b.id == "action_1"
