CREATE TABLE IF NOT EXISTS agent_stream_snapshot (
  exp_id LowCardinality(String),
  simulation_step Int32,
  agent_id Int32,
  memory_id Int32,
  cognition_id Nullable(Int32),
  topic String,
  location String,
  description String CODEC(ZSTD(3)),
  day Int32,
  t Float64
)
ENGINE = MergeTree()
ORDER BY (exp_id, simulation_step, agent_id, memory_id)
PARTITION BY exp_id
