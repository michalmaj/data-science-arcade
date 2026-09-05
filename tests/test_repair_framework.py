import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption, apply_resolution

SCHEMA = Schema(
    columns=(
        ColumnSchema("id", "int64", description_key="a"),
        ColumnSchema("code", "object", description_key="b"),
    )
)


def _dataset() -> Dataset:
    frame = pd.DataFrame({"id": [1, 2, 3], "code": ["a1", "A1", "a1"]})
    return Dataset(name="things", frame=frame, schema=SCHEMA)


ID_TO_STRING = RepairOption(
    "as_string",
    "label",
    lambda frame: frame.assign(id=frame["id"].astype("string")),
    result_dtype="string",
    result_description_key="fixed",
)
CODE_UPPER = RepairOption("upper", "label", lambda frame: frame.assign(code=frame["code"].str.upper()))

ID_ISSUE = RepairIssue(column="id", prompt_key="p", options=(ID_TO_STRING,))
CODE_ISSUE = RepairIssue(column="code", prompt_key="p", options=(CODE_UPPER,))


def test_apply_resolution_replays_the_chosen_options_real_transform():
    result = apply_resolution(_dataset(), (ID_ISSUE, CODE_ISSUE), {"id": "as_string", "code": "upper"})

    assert result.frame["id"].dtype == "string"
    assert list(result.frame["code"]) == ["A1", "A1", "A1"]


def test_apply_resolution_leaves_an_unresolved_issue_untouched():
    result = apply_resolution(_dataset(), (ID_ISSUE, CODE_ISSUE), {"id": "as_string"})

    assert result.frame["id"].dtype == "string"
    assert list(result.frame["code"]) == ["a1", "A1", "a1"]  # code never resolved, never touched


def test_apply_resolution_updates_only_the_resolved_columns_own_schema():
    result = apply_resolution(_dataset(), (ID_ISSUE,), {"id": "as_string"})

    id_schema = next(c for c in result.schema.columns if c.name == "id")
    code_schema = next(c for c in result.schema.columns if c.name == "code")
    assert id_schema.dtype == "string"
    assert id_schema.description_key == "fixed"
    assert code_schema == SCHEMA.columns[1]  # sibling column's own schema entry, byte-for-byte unchanged


def test_apply_resolution_records_real_python_mirror_history():
    id_to_string_with_code = RepairOption(
        "as_string",
        "label",
        lambda frame: frame.assign(id=frame["id"].astype("string")),
        python_code="things['id'] = things['id'].astype('string')",
    )
    issue = RepairIssue(column="id", prompt_key="p", options=(id_to_string_with_code,))

    result = apply_resolution(_dataset(), (issue,), {"id": "as_string"})

    assert result.python_mirror() == "things['id'] = things['id'].astype('string')"
    assert result.history[-1].name == "id_as_string"


def test_apply_resolution_with_an_empty_resolution_returns_the_dataset_unchanged():
    original = _dataset()
    result = apply_resolution(original, (ID_ISSUE, CODE_ISSUE), {})

    assert result.frame["id"].dtype == "int64"
    assert list(result.frame["code"]) == ["a1", "A1", "a1"]
