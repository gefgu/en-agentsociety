CREATE TABLE IF NOT EXISTS agent_spatial_snapshot (
    exp_id VARCHAR,
    simulation_step INTEGER,
    agent_id INTEGER,
    location_id VARCHAR,
    description VARCHAR,
    price DOUBLE,
    atmosphere DOUBLE,
    satisfaction DOUBLE,
    convenience DOUBLE,
    uncertainty DOUBLE
);
