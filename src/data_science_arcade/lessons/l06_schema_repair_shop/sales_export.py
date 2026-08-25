import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption

RAW_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64"),
        ColumnSchema("market", "object"),
        ColumnSchema("price", "object", description="Stored as text - decimal separator varies by market"),
        ColumnSchema("currency", "object", description="Casing is inconsistent across source systems"),
    )
)

PRICE_FIXED_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64"),
        ColumnSchema("market", "object"),
        ColumnSchema("price", "float64"),
        ColumnSchema("currency", "object"),
    )
)

# Hand-crafted (not random): 8 orders across 3 markets. DE/FR use a comma
# decimal separator (the European convention), US uses a period - both
# genuinely mean the same thing, they're just formatted differently, so a
# single correct rule ("comma is the decimal separator") cleans every row
# at once without needing a market-by-market split.
_ROWS = [
    (1, "DE", "19,99", "eur"),
    (2, "DE", "8,50", "EUR"),
    (3, "DE", "142,00", "eur"),
    (4, "FR", "24,90", "eur"),
    (5, "FR", "6,75", "Eur"),
    (6, "US", "19.99", "usd"),
    (7, "US", "45.00", "USD"),
    (8, "US", "3.25", "usd"),
]


def generate_sales_export() -> Dataset:
    frame = pd.DataFrame(_ROWS, columns=["order_id", "market", "price", "currency"])
    step = PipelineStep(
        "raw_export",
        python_code="sales = pd.read_csv('novamart_sales_export.csv')  # merged from several source systems",
    )
    return Dataset(name="sales", frame=frame, schema=RAW_SCHEMA, history=(step,))


def _comma_as_decimal(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(price=frame["price"].str.replace(",", ".", regex=False).astype(float))


def _comma_as_thousands(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(price=frame["price"].str.replace(",", "", regex=False).astype(float))


def _leading_digits_only(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(price=frame["price"].str.extract(r"(\d+)")[0].astype(float))


def _uppercase(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(currency=frame["currency"].str.upper())


def _titlecase(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(currency=frame["currency"].str.title())


def _first_letter_only(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(currency=frame["currency"].str[0].str.upper())


# Same 2 flagged columns reused for both the guided and independent
# passes, matching Lessons 01-05's pattern - each issue has one correct
# option plus two decoys (a plausible-but-wrong rule, and a silently
# destructive one), and every option genuinely transforms the column
# (right or wrong) rather than being a no-op or a rejected click.
REPAIR_ISSUES: tuple[RepairIssue, ...] = (
    RepairIssue(
        column="price",
        prompt_key="lesson.l06.issue.price.prompt",
        hint_key="lesson.l06.issue.price.hint",
        schema_after=PRICE_FIXED_SCHEMA,
        options=(
            RepairOption(
                "comma_as_decimal",
                "lesson.l06.option.price.comma_as_decimal",
                _comma_as_decimal,
                python_code="sales['price'] = sales['price'].str.replace(',', '.').astype(float)",
            ),
            RepairOption(
                "comma_as_thousands",
                "lesson.l06.option.price.comma_as_thousands",
                _comma_as_thousands,
                python_code="sales['price'] = sales['price'].str.replace(',', '').astype(float)",
            ),
            RepairOption(
                "leading_digits_only",
                "lesson.l06.option.price.leading_digits_only",
                _leading_digits_only,
                python_code="sales['price'] = sales['price'].str.extract(r'(\\d+)').astype(float)",
            ),
        ),
    ),
    RepairIssue(
        column="currency",
        prompt_key="lesson.l06.issue.currency.prompt",
        hint_key="lesson.l06.issue.currency.hint",
        options=(
            RepairOption(
                "uppercase",
                "lesson.l06.option.currency.uppercase",
                _uppercase,
                python_code="sales['currency'] = sales['currency'].str.upper()",
            ),
            RepairOption(
                "titlecase",
                "lesson.l06.option.currency.titlecase",
                _titlecase,
                python_code="sales['currency'] = sales['currency'].str.title()",
            ),
            RepairOption(
                "first_letter_only",
                "lesson.l06.option.currency.first_letter_only",
                _first_letter_only,
                python_code="sales['currency'] = sales['currency'].str[0].str.upper()",
            ),
        ),
    ),
)
