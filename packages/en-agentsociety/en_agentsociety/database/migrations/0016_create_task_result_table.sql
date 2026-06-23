CREATE TABLE IF NOT EXISTS task_result (
    exp_id      LowCardinality(String),
    agent_id    Int32,
    context     String CODEC(ZSTD(3)),
    ground_truth String CODEC(ZSTD(3)),
    result      String CODEC(ZSTD(3)),
    created_at  DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, created_at)
PARTITION BY exp_id;
