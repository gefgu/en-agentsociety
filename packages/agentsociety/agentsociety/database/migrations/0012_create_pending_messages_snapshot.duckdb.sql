CREATE TABLE IF NOT EXISTS pending_messages_snapshot (
    exp_id VARCHAR,
    simulation_step INTEGER,
    from_id INTEGER,
    to_id INTEGER,
    day INTEGER,
    t DOUBLE,
    kind VARCHAR,
    payload_json VARCHAR,
    created_at TIMESTAMP,
    extra_json VARCHAR
);
