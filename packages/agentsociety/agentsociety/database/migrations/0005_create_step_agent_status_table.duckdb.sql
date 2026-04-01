CREATE TABLE IF NOT EXISTS step_agent_status (
    exp_id VARCHAR,
    agent_id INTEGER,
    simulation_step INTEGER,
    timestamp TIMESTAMP,
    lat REAL,
    lng REAL,
    parent_id INTEGER,
    action VARCHAR,
    status VARCHAR
);
