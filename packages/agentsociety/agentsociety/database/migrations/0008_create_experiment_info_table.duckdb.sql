CREATE TABLE IF NOT EXISTS experiment_info (
    tenant_id VARCHAR,
    id VARCHAR,
    name VARCHAR,
    num_day INTEGER,
    status INTEGER,
    cur_day INTEGER,
    cur_t DOUBLE,
    config VARCHAR,
    error VARCHAR,
    input_tokens BIGINT,
    output_tokens BIGINT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
