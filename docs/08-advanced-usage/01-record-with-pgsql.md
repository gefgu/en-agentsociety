# Record Experiment with PostgreSQL

## Usage

To enable PostgreSQL storage for recording experiment data, assign PostgreSQL configuration in the environment config:

```python
config = Config(
    ...
    env=EnvConfig(
        pgsql=PostgreSQLConfig(
            enabled=True,
            dsn="<PGSQL-DSN>",
            num_workers="auto",
        ),
    )
)
```

## Pg Table Definition

## Experiment Meta Info
```sql
CREATE TABLE IF NOT EXISTS as_experiment (
    tenant_id TEXT,
    id UUID,
    name TEXT,
    num_day INT4,
    status INT4, 
    cur_day INT4,
    cur_t FLOAT,
    config TEXT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, id)
)

```

## Agent Profile
```sql
CREATE TABLE IF NOT EXISTS as_<exp_id>_agent_profile (
    id INT4 PRIMARY KEY,
    name TEXT,
    profile JSONB
)
```

## Agent Dialog
```sql
CREATE TABLE IF NOT EXISTS as_<exp_id>_agent_dialog (
    id INT4,
    day INT4,
    t FLOAT,
    type INT4,
    speaker TEXT,
    content TEXT,
    created_at TIMESTAMPTZ
)
```

## Agent Status
```sql
CREATE TABLE IF NOT EXISTS as_<exp_id>_agent_status (
    id INT4,
    day INT4,
    t FLOAT,
    lng DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    parent_id INT4,
    friend_ids UUID[],
    action TEXT,
    status JSONB,
    created_at TIMESTAMPTZ
)
```

## Survey
```sql
CREATE TABLE IF NOT EXISTS as_<exp_id>_agent_survey (
    id INT4,
    day INT4,
    t FLOAT,
    survey_id TEXT,
    result TEXT,
    created_at TIMESTAMPTZ
)
```

## Global Prompt
```sql
CREATE TABLE IF NOT EXISTS as_<exp_id>_global_prompt (
    id INT4,
    prompt TEXT,
    created_at TIMESTAMPTZ
)
```