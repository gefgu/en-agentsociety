from types import SimpleNamespace

from en_agentsociety.configs.env import EnvConfig
from en_agentsociety.database.database_actor import DatabaseActor
from en_agentsociety.database.duckdb import DuckDBDatabase
from en_agentsociety.storage import DatabaseConfig


class FakeDatabase:
    def __init__(self):
        self.simulation_step = 12
        self.records = []

    def insert_record(self, table_name, record):
        self.records.append((table_name, record.as_record()))


def make_actor(storage_mode):
    actor_cls = DatabaseActor.__ray_metadata__.modified_class
    actor = object.__new__(actor_cls)
    actor._db = FakeDatabase()
    actor._llm_response_storage = storage_mode
    return actor


def test_lightview_prompt_response_stores_metadata_only():
    actor = make_actor("lightview")

    actor.insert_prompt_response_record(
        timestamp=1_700_000_000.0,
        agent_id=7,
        prompt="What should I do next?",
        response="Go to work",
        block_name="PlannerBlock",
        func_name="step",
        input_tokens=11,
        output_tokens=3,
        prompt_identity="daily_plan",
        model_role="base",
    )

    assert len(actor._db.records) == 1
    table_name, record = actor._db.records[0]
    assert table_name == "prompt_responses"
    assert record["prompt"] == ""
    assert record["response"] == ""
    assert record["prompt_chars"] == len("What should I do next?")
    assert record["response_chars"] == len("Go to work")
    assert record["input_tokens"] == 11
    assert record["output_tokens"] == 3
    assert record["storage_mode"] == "lightview"
    assert record["detail_available"] == 0
    assert record["request_id"]


def test_detailed_prompt_response_stores_index_and_detail_rows():
    actor = make_actor("detailed")

    actor.insert_prompt_response_record(
        timestamp=1_700_000_000.0,
        agent_id=7,
        prompt="Prompt text",
        response="Response text",
        block_name="PlannerBlock",
        func_name="step",
    )

    assert [table for table, _ in actor._db.records] == [
        "prompt_responses",
        "prompt_response_details",
    ]
    index_record = actor._db.records[0][1]
    detail_record = actor._db.records[1][1]
    assert index_record["prompt"] == "Prompt text"
    assert index_record["response"] == "Response text"
    assert index_record["storage_mode"] == "detailed"
    assert index_record["detail_available"] == 1
    assert detail_record["request_id"] == index_record["request_id"]
    assert detail_record["prompt"] == "Prompt text"
    assert detail_record["response"] == "Response text"


def test_non_string_openai_style_response_is_converted():
    actor = make_actor("detailed")
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="Converted response"),
            )
        ]
    )

    actor.insert_prompt_response_record(
        timestamp=1_700_000_000.0,
        agent_id=7,
        prompt="Prompt",
        response=response,
        block_name="PlannerBlock",
        func_name="step",
    )

    assert actor._db.records[0][1]["response"] == "Converted response"
    assert actor._db.records[1][1]["response"] == "Converted response"


def test_env_config_llm_response_storage_default_and_explicit():
    default_env = EnvConfig(db=DatabaseConfig())
    lightview_env = EnvConfig(
        db=DatabaseConfig(),
        llm_response_storage="lightview",
    )

    assert default_env.llm_response_storage == "detailed"
    assert lightview_env.llm_response_storage == "lightview"


def test_duckdb_conversion_supports_llm_response_storage_migration():
    raw_sql = (
        "ALTER TABLE prompt_responses ADD COLUMN IF NOT EXISTS request_id String, "
        "ADD COLUMN IF NOT EXISTS detail_available Int32;"
        "CREATE TABLE IF NOT EXISTS prompt_response_details ("
        "exp_id LowCardinality(String), "
        "timestamp DateTime64(3), "
        "prompt String CODEC(ZSTD(3))"
        ") ENGINE = MergeTree() ORDER BY exp_id PARTITION BY exp_id"
    )

    statements = DuckDBDatabase._to_duckdb_statements(raw_sql)

    assert (
        "ALTER TABLE prompt_responses ADD COLUMN IF NOT EXISTS request_id VARCHAR"
        in statements
    )
    assert (
        "ALTER TABLE prompt_responses ADD COLUMN IF NOT EXISTS detail_available INTEGER"
        in statements
    )
    assert any("prompt_response_details" in statement for statement in statements)
    assert all("CODEC" not in statement for statement in statements)
