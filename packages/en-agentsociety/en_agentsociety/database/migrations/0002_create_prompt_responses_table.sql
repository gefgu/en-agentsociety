CREATE TABLE IF NOT EXISTS prompt_responses (
    exp_id LowCardinality(String),
    simulation_step Int32,
    timestamp DateTime64(3),
    agent_id Int32,
    prompt String CODEC(ZSTD(3)),
    response String CODEC(ZSTD(3)),
    block_name LowCardinality(String),
    func_name LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
