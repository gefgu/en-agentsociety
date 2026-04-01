CREATE TABLE IF NOT EXISTS prompt_responses (
    exp_id VARCHAR,
    simulation_step INTEGER,
    timestamp TIMESTAMP,
    agent_id INTEGER,
    prompt VARCHAR,
    response VARCHAR,
    block_name VARCHAR,
    func_name VARCHAR
);
