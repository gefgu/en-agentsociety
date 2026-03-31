CREATE TABLE IF NOT EXISTS agent_spatial_snapshot (
  exp_id LowCardinality(String),
  simulation_step Int32,
  agent_id Int32,
  location_id String,
  description String CODEC(ZSTD(3)),
  price Float64,
  atmosphere Float64,
  satisfaction Float64,
  convenience Float64,
  uncertainty Float64
)
ENGINE = MergeTree()
ORDER BY (exp_id, simulation_step, agent_id, location_id)
PARTITION BY exp_id
