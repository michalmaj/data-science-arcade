from data_science_arcade.data_engine.schema import ColumnSchema, Schema


def test_column_names_returns_names_in_order():
    schema = Schema(
        columns=(
            ColumnSchema("customer_id", "int64"),
            ColumnSchema("region", "string"),
        )
    )

    assert schema.column_names() == ("customer_id", "region")
