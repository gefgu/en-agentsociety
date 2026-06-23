CREATE TABLE IF NOT EXISTS agent_profile (
    exp_id      LowCardinality(String),
    agent_id    Int32,
    name        String,
    profile     String CODEC(ZSTD(3))
)
ENGINE = ReplacingMergeTree()
ORDER BY (exp_id, agent_id)
PARTITION BY exp_id;
