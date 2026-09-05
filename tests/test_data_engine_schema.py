from data_science_arcade.data_engine.schema import ColumnSchema, Schema


def test_column_names_returns_names_in_order():
    schema = Schema(
        columns=(
            ColumnSchema("customer_id", "int64"),
            ColumnSchema("region", "string"),
        )
    )

    assert schema.column_names() == ("customer_id", "region")


def test_with_column_replaces_only_the_named_columns_dtype_and_description():
    schema = Schema(
        columns=(
            ColumnSchema("customer_id", "int64", description_key="a"),
            ColumnSchema("region", "string", description_key="b"),
        )
    )

    updated = schema.with_column("customer_id", dtype="string", description_key="c")

    assert updated.columns[0].dtype == "string"
    assert updated.columns[0].description_key == "c"
    assert updated.columns[1] == schema.columns[1]  # untouched sibling column


def test_with_column_with_no_overrides_keeps_the_column_exactly_as_it_was():
    schema = Schema(columns=(ColumnSchema("customer_id", "int64", description_key="a"),))

    updated = schema.with_column("customer_id")

    assert updated.columns[0] == schema.columns[0]


def test_with_column_never_mutates_the_original_schema():
    schema = Schema(columns=(ColumnSchema("customer_id", "int64"),))

    schema.with_column("customer_id", dtype="string")

    assert schema.columns[0].dtype == "int64"
