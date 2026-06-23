CREATE TABLE IF NOT EXISTS block_dispatcher (
    exp_id LowCardinality(String),
    simulation_step Int32,
    timestamp DateTime64(3),
    agent_id Int32,
    target_block LowCardinality(String),
    reason String CODEC(ZSTD(3)),
    possible_blocks Array(LowCardinality(String)),
    ctx_time String CODEC(ZSTD(3)),
    ctx_need String CODEC(ZSTD(3)),
    ctx_intention String CODEC(ZSTD(3)),
    ctx_emotion String CODEC(ZSTD(3)),
    ctx_thought String CODEC(ZSTD(3)),
    ctx_location String CODEC(ZSTD(3)),
    ctx_area_info String CODEC(ZSTD(3)),
    ctx_weather String CODEC(ZSTD(3)),
    ctx_temperature Int32,
    ctx_other_info String CODEC(ZSTD(3)),
    ctx_plan_target String CODEC(ZSTD(3))
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
