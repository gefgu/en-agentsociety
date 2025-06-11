# Database Storage Layer

## Overview

The storage layer now provides a unified database writer that supports both PostgreSQL and SQLite with automatic path management and intelligent defaults.

## Key Features

- **Default SQLite**: Uses SQLite by default for easy setup
- **Automatic Path Management**: No need to specify storage paths for SQLite
- **Multi-Database Support**: Easy switching between SQLite and PostgreSQL
- **File Path Integration**: Includes `exp_info_file` path management from removed avro module

## Quick Start

### Basic Usage (SQLite - Default)

```python
from agentsociety.storage.pgsql import DatabaseConfig, DatabaseWriter

# Minimal configuration - everything auto-generated
config = DatabaseConfig()

# Initialize writer
writer = DatabaseWriter(
    tenant_id="default", 
    exp_id="my-experiment", 
    config=config, 
    init=True
)

# Access experiment info file path
exp_file = writer.exp_info_file  # auto: agentsociety_data/default/my-experiment/experiment_info.yaml
```

### Custom SQLite Configuration

```python
config = DatabaseConfig(
    db_type="sqlite",
    dsn="custom/path/mydb.db",
    storage_dir="custom/storage"
)
```

### PostgreSQL Configuration

```python
config = DatabaseConfig(
    db_type="postgresql",
    dsn="postgresql://user:pass@localhost:5432/dbname",
    storage_dir="pg_storage"
)
```

## Auto-Generated Paths

### SQLite (Default Behavior)
- **Database File**: `agentsociety_data/database.db`
- **Storage Directory**: `agentsociety_data/`
- **Experiment Files**: `agentsociety_data/{tenant_id}/{exp_id}/`
- **Exp Info File**: `agentsociety_data/{tenant_id}/{exp_id}/experiment_info.yaml`

### Custom Paths
```python
# Custom database location
config = DatabaseConfig(dsn="data/my_project.db")
# Results in:
# - Database: data/my_project.db
# - Storage: data/
# - Exp files: data/{tenant_id}/{exp_id}/
```

## Usage Examples

### Writing Data

```python
# Write dialogs
await writer.write_dialogs(dialog_list)

# Write agent statuses
await writer.write_statuses(status_list)

# Write profiles
await writer.write_profiles(profile_list)

# Update experiment info
await writer.update_exp_info(exp_info)
```

### Accessing Files

```python
# Get experiment info file path
exp_info_path = writer.exp_info_file

# Get base storage path
storage_path = writer.storage_path

# Example paths:
# exp_info_path: agentsociety_data/tenant1/exp1/experiment_info.yaml
# storage_path: agentsociety_data/tenant1/exp1/
```

## Database-Specific Features

### SQLite
- Automatic directory creation
- JSON serialization for arrays (friend_ids)
- Single file database
- No additional setup required

### PostgreSQL
- Native array support
- JSONB for complex data
- Requires external database setup
- Better performance for large datasets

## Migration Guide

### From Avro
The `exp_info_file` functionality from the removed avro module is now integrated:

```python
# Old avro approach
# avro_saver.exp_info_file

# New unified approach
writer.exp_info_file  # Same functionality, auto-managed paths
```

### Configuration Changes

```python
# Old separate configs
postgresql_config = PostgreSQLConfig(dsn="postgresql://...")
sqlite_config = SQLiteConfig(db_path="/path/to/db")

# New unified config
config = DatabaseConfig(db_type="postgresql", dsn="postgresql://...")
config = DatabaseConfig(db_type="sqlite", dsn="/path/to/db")
# Or simply: config = DatabaseConfig()  # Uses SQLite with auto paths
```

## Backward Compatibility

Original class names are preserved:

```python
# These still work
from agentsociety.storage.pgsql import PostgreSQLConfig, PgWriter

# But prefer the new names
from agentsociety.storage.pgsql import DatabaseConfig, DatabaseWriter
``` 