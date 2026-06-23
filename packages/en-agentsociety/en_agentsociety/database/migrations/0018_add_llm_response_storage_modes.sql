ALTER TABLE prompt_responses ADD COLUMN IF NOT EXISTS request_id String,
    ADD COLUMN IF NOT EXISTS input_tokens Int32,
    ADD COLUMN IF NOT EXISTS output_tokens Int32,
    ADD COLUMN IF NOT EXISTS prompt_chars Int32,
    ADD COLUMN IF NOT EXISTS response_chars Int32,
    ADD COLUMN IF NOT EXISTS prompt_identity LowCardinality(String),
    ADD COLUMN IF NOT EXISTS model_role LowCardinality(String),
    ADD COLUMN IF NOT EXISTS storage_mode LowCardinality(String),
    ADD COLUMN IF NOT EXISTS detail_available Int32;

CREATE TABLE IF NOT EXISTS prompt_response_details (
    exp_id LowCardinality(String),
    simulation_step Int32,
    timestamp DateTime64(3),
    agent_id Int32,
    request_id String,
    prompt String CODEC(ZSTD(3)),
    response String CODEC(ZSTD(3)),
    block_name LowCardinality(String),
    func_name LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp, request_id)
PARTITION BY exp_id
