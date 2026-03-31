CREATE TABLE IF NOT EXISTS agent_kv_snapshot (
  exp_id LowCardinality(String),
  simulation_step Int32,
  agent_id Int32,
  key String,
  value_json String CODEC(ZSTD(3))
)
ENGINE = MergeTree()
ORDER BY (exp_id, simulation_step, agent_id, key)
PARTITION BY exp_id
