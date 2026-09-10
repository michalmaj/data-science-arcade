from data_science_arcade.handbook.entries import GlossaryEntry, HandbookEntry

# The editorial vertical slice this PR is scoped to: 4 full-prose articles
# tied to Lesson 01, ~10 glossary terms. Deliberately not theory for all 30
# lessons - see decisions/CONTENT_STYLE_GUIDE.md/TERMINOLOGY_GUIDE.md for
# the standards every entry here was written and reviewed against.

ASKING_AN_ANALYTICAL_QUESTION = HandbookEntry(
    id="asking_an_analytical_question",
    title_key="handbook.article.asking_an_analytical_question.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.asking_an_analytical_question.body.1",
        "handbook.article.asking_an_analytical_question.body.2",
        "handbook.article.asking_an_analytical_question.body.3",
        "handbook.article.asking_an_analytical_question.body.4",
        "handbook.article.asking_an_analytical_question.body.5",
    ),
    related_entry_ids=("analytical_question", "timeframe", "population"),
)

OBSERVATION_UNIT_AND_GRAIN = HandbookEntry(
    id="observation_unit_and_grain",
    title_key="handbook.article.observation_unit_and_grain.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.observation_unit_and_grain.body.1",
        "handbook.article.observation_unit_and_grain.body.2",
        "handbook.article.observation_unit_and_grain.body.3",
        "handbook.article.observation_unit_and_grain.body.4",
        "handbook.article.observation_unit_and_grain.body.5",
        "handbook.article.observation_unit_and_grain.body.6",
    ),
    related_entry_ids=("observation_unit", "grain"),
)

METRICS_NEED_DEFINITIONS = HandbookEntry(
    id="metrics_need_definitions",
    title_key="handbook.article.metrics_need_definitions.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.metrics_need_definitions.body.1",
        "handbook.article.metrics_need_definitions.body.2",
        "handbook.article.metrics_need_definitions.body.3",
        "handbook.article.metrics_need_definitions.body.4",
    ),
    related_entry_ids=("metric_definition",),
)

TIME_WINDOWS_CHANGE_ANSWERS = HandbookEntry(
    id="time_windows_change_answers",
    title_key="handbook.article.time_windows_change_answers.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.time_windows_change_answers.body.1",
        "handbook.article.time_windows_change_answers.body.2",
        "handbook.article.time_windows_change_answers.body.3",
        "handbook.article.time_windows_change_answers.body.4",
        "handbook.article.time_windows_change_answers.body.5",
    ),
    related_entry_ids=("time_window", "timeframe"),
)

SCHEMA_IS_A_CONTRACT = HandbookEntry(
    id="schema_is_a_contract",
    title_key="handbook.article.schema_is_a_contract.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.schema_is_a_contract.body.1",
        "handbook.article.schema_is_a_contract.body.2",
        "handbook.article.schema_is_a_contract.body.3",
        "handbook.article.schema_is_a_contract.body.4",
        "handbook.article.schema_is_a_contract.body.5",
    ),
)

MISSINGNESS_HAS_A_MECHANISM = HandbookEntry(
    id="missingness_has_a_mechanism",
    title_key="handbook.article.missingness_has_a_mechanism.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.missingness_has_a_mechanism.body.1",
        "handbook.article.missingness_has_a_mechanism.body.2",
        "handbook.article.missingness_has_a_mechanism.body.3",
        "handbook.article.missingness_has_a_mechanism.body.4",
        "handbook.article.missingness_has_a_mechanism.body.5",
    ),
)

DUPLICATES_NEED_AN_IDENTITY = HandbookEntry(
    id="duplicates_need_an_identity",
    title_key="handbook.article.duplicates_need_an_identity.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.duplicates_need_an_identity.body.1",
        "handbook.article.duplicates_need_an_identity.body.2",
        "handbook.article.duplicates_need_an_identity.body.3",
        "handbook.article.duplicates_need_an_identity.body.4",
        "handbook.article.duplicates_need_an_identity.body.5",
    ),
    related_entry_ids=("observation_unit_and_grain",),
)

OUTLIER_IS_A_FLAG_NOT_A_VERDICT = HandbookEntry(
    id="outlier_is_a_flag_not_a_verdict",
    title_key="handbook.article.outlier_is_a_flag_not_a_verdict.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.outlier_is_a_flag_not_a_verdict.body.1",
        "handbook.article.outlier_is_a_flag_not_a_verdict.body.2",
        "handbook.article.outlier_is_a_flag_not_a_verdict.body.3",
        "handbook.article.outlier_is_a_flag_not_a_verdict.body.4",
        "handbook.article.outlier_is_a_flag_not_a_verdict.body.5",
    ),
    related_entry_ids=("observation_unit_and_grain", "population"),
)

A_SUMMARY_IS_NOT_THE_DISTRIBUTION = HandbookEntry(
    id="a_summary_is_not_the_distribution",
    title_key="handbook.article.a_summary_is_not_the_distribution.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.a_summary_is_not_the_distribution.body.1",
        "handbook.article.a_summary_is_not_the_distribution.body.2",
        "handbook.article.a_summary_is_not_the_distribution.body.3",
        "handbook.article.a_summary_is_not_the_distribution.body.4",
        "handbook.article.a_summary_is_not_the_distribution.body.5",
    ),
    related_entry_ids=("quantile", "population"),
)

JOINS_HAVE_CARDINALITY = HandbookEntry(
    id="joins_have_cardinality",
    title_key="handbook.article.joins_have_cardinality.title",
    category_key="handbook.category.foundations",
    body_paragraph_keys=(
        "handbook.article.joins_have_cardinality.body.1",
        "handbook.article.joins_have_cardinality.body.2",
        "handbook.article.joins_have_cardinality.body.3",
        "handbook.article.joins_have_cardinality.body.4",
        "handbook.article.joins_have_cardinality.body.5",
    ),
    related_entry_ids=("observation_unit_and_grain", "duplicates_need_an_identity", "cardinality"),
)

HANDBOOK_ENTRIES: tuple[HandbookEntry, ...] = (
    ASKING_AN_ANALYTICAL_QUESTION,
    OBSERVATION_UNIT_AND_GRAIN,
    METRICS_NEED_DEFINITIONS,
    TIME_WINDOWS_CHANGE_ANSWERS,
    SCHEMA_IS_A_CONTRACT,
    MISSINGNESS_HAS_A_MECHANISM,
    DUPLICATES_NEED_AN_IDENTITY,
    OUTLIER_IS_A_FLAG_NOT_A_VERDICT,
    A_SUMMARY_IS_NOT_THE_DISTRIBUTION,
    JOINS_HAVE_CARDINALITY,
)

GLOSSARY_ENTRIES: tuple[GlossaryEntry, ...] = (
    GlossaryEntry(
        id="analytical_question",
        term_key="handbook.glossary.analytical_question.term",
        definition_key="handbook.glossary.analytical_question.definition",
        related_entry_id="asking_an_analytical_question",
    ),
    GlossaryEntry(
        id="observation_unit",
        term_key="handbook.glossary.observation_unit.term",
        definition_key="handbook.glossary.observation_unit.definition",
        related_entry_id="observation_unit_and_grain",
    ),
    GlossaryEntry(
        id="grain",
        term_key="handbook.glossary.grain.term",
        definition_key="handbook.glossary.grain.definition",
        related_entry_id="observation_unit_and_grain",
    ),
    GlossaryEntry(
        id="metric_definition",
        term_key="handbook.glossary.metric_definition.term",
        definition_key="handbook.glossary.metric_definition.definition",
        related_entry_id="metrics_need_definitions",
    ),
    GlossaryEntry(
        id="time_window",
        term_key="handbook.glossary.time_window.term",
        definition_key="handbook.glossary.time_window.definition",
        related_entry_id="time_windows_change_answers",
    ),
    GlossaryEntry(
        id="timeframe",
        term_key="handbook.glossary.timeframe.term",
        definition_key="handbook.glossary.timeframe.definition",
        related_entry_id="time_windows_change_answers",
    ),
    GlossaryEntry(
        id="population",
        term_key="handbook.glossary.population.term",
        definition_key="handbook.glossary.population.definition",
    ),
    GlossaryEntry(
        id="sample",
        term_key="handbook.glossary.sample.term",
        definition_key="handbook.glossary.sample.definition",
    ),
    GlossaryEntry(
        id="sampling",
        term_key="handbook.glossary.sampling.term",
        definition_key="handbook.glossary.sampling.definition",
    ),
    GlossaryEntry(
        id="confounder",
        term_key="handbook.glossary.confounder.term",
        definition_key="handbook.glossary.confounder.definition",
    ),
    GlossaryEntry(
        id="quantile",
        term_key="handbook.glossary.quantile.term",
        definition_key="handbook.glossary.quantile.definition",
        related_entry_id="a_summary_is_not_the_distribution",
    ),
    GlossaryEntry(
        id="cardinality",
        term_key="handbook.glossary.cardinality.term",
        definition_key="handbook.glossary.cardinality.definition",
        related_entry_id="joins_have_cardinality",
    ),
)


def find_entry(entry_id: str) -> HandbookEntry | GlossaryEntry | None:
    """Looks up the union of both registries - a related-entry reference
    or a navigation jump can land on either kind, and the caller needs to
    know which (paginated article detail vs. a short glossary popup)."""
    for entry in HANDBOOK_ENTRIES:
        if entry.id == entry_id:
            return entry
    for entry in GLOSSARY_ENTRIES:
        if entry.id == entry_id:
            return entry
    return None
