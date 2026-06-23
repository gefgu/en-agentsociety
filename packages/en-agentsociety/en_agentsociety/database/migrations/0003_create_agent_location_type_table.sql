CREATE TABLE IF NOT EXISTS agent_location_type (
  exp_id LowCardinality(String),
  simulation_step Int32,
  timestamp DateTime64(3),
  agent_id Int32,
  location_type LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
