# Environment Configuration

The environment configuration defines the core infrastructure settings for the simulation framework. This configuration is managed through the `EnvConfig` class, which handles various components essential for the system's operation.

## Configuration Structure


The environment configuration consists of several key components.

The structure is as follows:

```yaml
env:
  pgsql:
  avro:
  mlflow:
  s3:
```

### PostgreSQL Configuration 

An example of the `pgsql` section is as follows:

```yaml
pgsql:
  enabled: true
  dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres
```

The `pgsql` section manages the persistent storage database settings, including:
- Database connection parameters
- Table configurations
- Query settings

The `PostgreSQLConfig` class contains the following fields:

- `enabled` (bool, optional): Whether PostgreSQL storage is enabled, defaults to True
- `dsn` (str, required): Data source name for PostgreSQL connection, must start with "postgresql://"
- `num_workers` (Union[int, "auto"], optional): Number of workers for PostgreSQL operations, defaults to "auto"

The DSN (Data Source Name) string follows the format:

```
postgresql://user:password@host:port/database
```

### Avro Configuration

An example of the `avro` section is as follows:

```yaml
avro:
  enabled: true
  path: <CHANGE_ME>
```

The `avro` section handles data serialization settings:
- Schema definitions
- Serialization formats
- Data validation rules

The `AvroConfig` class contains the following fields:

- `enabled` (bool, optional): Whether Avro storage is enabled, defaults to False
- `path` (str, required): The file system path where Avro files will be stored. Must be a valid directory path.

### MLflow Configuration

An example of the `mlflow` section is as follows:

```yaml
mlflow:
  enabled: true
  mlflow_uri: <CHANGE_ME>
  username: <CHANGE_ME>
  password: <CHANGE_ME>
```

The `mlflow` component configures the machine learning experiment tracking:
- Experiment logging parameters
- Model tracking settings
- Metrics storage configuration
The `MlflowConfig` class contains the following fields:

- `enabled` (bool, optional): Whether MLflow tracking is enabled, defaults to False
- `username` (str, optional): Username for MLflow server authentication
- `password` (str, optional): Password for MLflow server authentication  
- `mlflow_uri` (str, required): URI for connecting to the MLflow tracking server

### S3 Configuration

```{admonition} Note
:class: note
When enabling S3 storage, the local file system will be replaced by S3, including `map.file_path`, `map.cache_path`, and `agents.*.memory_from_file`.
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
  pgsql:
    enabled: true # Whether to enable PostgreSQL
    dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres # PostgreSQL connection string
  avro:
    enabled: false # Whether to enable Avro
  mlflow:
    enabled: false # Whether to enable MLflow
    mlflow_uri: http://localhost:59000 # MLflow server URI``
    username: <CHANGE_ME> # MLflow server username
    password: <CHANGE_ME> # MLflow server password
  s3:
    enabled: false # Whether to enable S3 storage instead of local file system
    endpoint: <S3-ENDPOINT> # S3 endpoint
    access_key: <S3-ACCESS-KEY> # S3 access key
    secret_key: <S3-SECRET-KEY> # S3 secret key
    bucket: <S3-BUCKET> # S3 bucket
    region: <S3-REGION> # S3 region
    prefix: <S3-PREFIX> # prefix in path (optional)
```
