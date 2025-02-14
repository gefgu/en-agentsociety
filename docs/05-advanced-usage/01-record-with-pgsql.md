# Record Experiment with PostgreSQL

## Usage

Assign SimConfig with `SimConfig.SetPostgreSql`, e.g. `SimConfig().SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)`.

## Pg Table Definition

## Experiment Meta Info
```sql
CREATE TABLE IF NOT EXISTS <table_name> (
        id UUID PRIMARY KEY,
        name TEXT,
        num_day INT4,
        status INT4, 
        cur_day INT4,
        cur_t FLOAT,
        config TEXT,
        error TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
)

```

## Agent Profile
```sql
CREATE TABLE IF NOT EXISTS <table_name> (
    id UUID PRIMARY KEY,
    name TEXT,
    profile JSONB
)

```

## Agent Dialog
```sql
CREATE TABLE IF NOT EXISTS <table_name> (
    id UUID,
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
CREATE TABLE IF NOT EXISTS <table_name> (
    id UUID,
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
CREATE INDEX <table_name>_id_idx ON <table_name> (id)
CREATE INDEX <table_name>_day_t_idx ON <table_name> (day,t)
```

## Survey
```sql
CREATE TABLE IF NOT EXISTS <table_name> (
    id UUID,
    day INT4,
    t FLOAT,
    survey_id UUID,
    result JSONB,
    created_at TIMESTAMPTZ
)
CREATE INDEX <table_name>_id_idx ON <table_name> (id)
CREATE INDEX <table_name>_day_t_idx ON <table_name> (day,t)

```
