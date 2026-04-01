CREATE TABLE IF NOT EXISTS NeedsBlock_adjust_needs (
    exp_id VARCHAR,
    simulation_step INTEGER,
    timestamp TIMESTAMP,
    agent_id INTEGER,
    prompt VARCHAR,
    actor VARCHAR,
    current_need VARCHAR,
    current_hunger REAL,
    current_energy REAL,
    current_safety REAL,
    current_social REAL,
    new_hunger REAL,
    new_energy REAL,
    new_safety REAL,
    new_social REAL
);
