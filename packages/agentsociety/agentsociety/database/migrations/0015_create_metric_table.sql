CREATE TABLE IF NOT EXISTS metric (
    exp_id      LowCardinality(String),
    key         LowCardinality(String),
    value       Float64,
    step        Int32,
    created_at  DateTime64(3)
)
ENGINE = MergeTree()
ORDER BY (exp_id, key, step)
PARTITION BY exp_id;
