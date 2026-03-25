CREATE TABLE IF NOT EXISTS step_agent_status (
  exp_id LowCardinality(String),
  agent_id Int32,
  simulation_step Int32,
  timestamp DateTime64(3),
  lat Float32,
  lng Float32,
  parent_id Int32,
  action LowCardinality(String),
  status String CODEC(ZSTD(3))
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
