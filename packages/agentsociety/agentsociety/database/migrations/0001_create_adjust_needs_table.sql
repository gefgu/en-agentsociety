CREATE TABLE IF NOT EXISTS NeedsBlock_adjust_needs (
    exp_id LowCardinality(String),
    simulation_step Int32,
    timestamp DateTime64(3),
    agent_id Int32,
    prompt String CODEC(ZSTD(3)),
    actor LowCardinality(String),
    current_need LowCardinality(String),
    current_hunger Float32,
    current_energy Float32,
    current_safety Float32,
    current_social Float32,
    new_hunger Float32,
    new_energy Float32,
    new_safety Float32,
    new_social Float32
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id