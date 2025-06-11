# Environment Configuration

The environment configuration defines the core infrastructure settings for the simulation framework. This configuration is managed through the `EnvConfig` class, which handles various components essential for the system's operation.

## Configuration Structure


The environment configuration consists of several key components.

The structure is as follows:

```yaml
env:
  db:
  s3:
```

### Database Configuration 

An example of the `db` section is as follows:

```yaml
db:
  enabled: true
  db_type: sqlite | postgresql
  pg_dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres
```

The `db` section manages the persistent storage database settings, including:
- Database connection parameters
- Table configurations
- Query settings

The `DatabaseConfig` class contains the following fields:

- `enabled` (bool, optional): Whether database storage is enabled, defaults to True
- `db_type` (str, required): Database type, currently supported: sqlite (default), postgresql
- `pg_dsn` (str, required): Data source name for PostgreSQL connection, must start with "postgresql://"

The DSN (Data Source Name) string follows the format:

```
postgresql://user:password@host:port/database
```

### S3 Configuration

```{admonition} Note
:class: note
When enabling S3 storage, the local file system will be replaced by S3, including `map.file_path`, and `agents.*.memory_from_file`.
```

An example of the `s3` section is as follows:

```yaml
s3:
  enabled: true
  endpoint: <S3-ENDPOINT>
  access_key: <S3-ACCESS-KEY>
  secret_key: <S3-SECRET-KEY>
  bucket: <S3-BUCKET>
  region: <S3-REGION>
  prefix: <S3-PREFIX>
```

The `s3` section manages the S3 storage settings, containing the following fields:

- `enabled` (bool): Whether S3 storage is enabled, defaults to False
- `endpoint` (str): S3 endpoint
- `access_key` (str): S3 access key
- `secret_key` (str): S3 secret key
- `bucket` (str): S3 bucket
- `region` (str): S3 region
- `prefix` (str): prefix in path (optional). Default is `""`.

## Environment Configuration in `config.yaml`

An example of the `env` section in `config.yaml` is as follows:

```yaml
env:
  db:
    enabled: true # Whether to enable database
    db_type: sqlite | postgresql
    pg_dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres # PostgreSQL connection string
  s3:
    enabled: false # Whether to enable S3 storage instead of local file system
    endpoint: <S3-ENDPOINT> # S3 endpoint
    access_key: <S3-ACCESS-KEY> # S3 access key
    secret_key: <S3-SECRET-KEY> # S3 secret key
    bucket: <S3-BUCKET> # S3 bucket
    region: <S3-REGION> # S3 region
    prefix: <S3-PREFIX> # prefix in path (optional)
```
