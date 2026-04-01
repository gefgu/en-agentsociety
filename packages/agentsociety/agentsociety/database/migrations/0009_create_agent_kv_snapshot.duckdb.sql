CREATE TABLE IF NOT EXISTS agent_kv_snapshot (
    exp_id VARCHAR,
    simulation_step INTEGER,
    agent_id INTEGER,
    key VARCHAR,
    value_json VARCHAR
);
