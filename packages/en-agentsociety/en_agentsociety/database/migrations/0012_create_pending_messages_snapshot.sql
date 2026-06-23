CREATE TABLE IF NOT EXISTS pending_messages_snapshot (
  exp_id LowCardinality(String),
  simulation_step Int32,
  from_id Nullable(Int32),
  to_id Nullable(Int32),
  day Int32,
  t Float64,
  kind String,
  payload_json String CODEC(ZSTD(3)),
  created_at DateTime64(3),
  extra_json Nullable(String) CODEC(ZSTD(3))
)
ENGINE = MergeTree()
ORDER BY (exp_id, simulation_step, created_at)
PARTITION BY exp_id
