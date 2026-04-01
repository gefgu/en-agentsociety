CREATE TABLE IF NOT EXISTS agent_stream_snapshot (
    exp_id VARCHAR,
    simulation_step INTEGER,
    agent_id INTEGER,
    memory_id INTEGER,
    cognition_id INTEGER,
    topic VARCHAR,
    location VARCHAR,
    description VARCHAR,
    day INTEGER,
    t DOUBLE
);
