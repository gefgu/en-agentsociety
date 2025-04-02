# Environment Configuration

The environment configuration defines the core infrastructure settings for the simulation framework. This configuration is managed through the `EnvConfig` class, which handles various components essential for the system's operation.

## Configuration Structure


The environment configuration consists of several key components.

The structure is as follows:

```yaml
env:
  redis:
  pgsql:
  avro:
  mlflow:
```

### Redis Configuration

An example of the `redis` section is as follows:

```yaml
redis:
  server: <CHANGE_ME>
  port: 6379
  password: <CHANGE_ME>
```

Redis serves as the message broker and temporary storage solution. The `redis` section configures:
- Connection parameters
- Message queue settings
- Caching configurations

The `RedisConfig` class contains the following fields:

- `server` (str, required): The Redis server address
- `port` (int, optional): Port number for Redis connection, defaults to 6379 (must be between 0-65535)
- `password` (str, optional): Password for Redis connection authentication
- `db` (int, optional): Database number for Redis connection, defaults to 0
- `timeout` (float, optional): Connection timeout in seconds, defaults to 60


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

## Environment Configuration in `config.yaml`

An example of the `env` section in `config.yaml` is as follows:

```yaml
env:
  redis:
    server: <REDIS-SERVER> # Redis server address
    port: 6379 # Redis port
    password: <CHANGE_ME> # Redis password
  pgsql:
    enabled: true # Whether to enable PostgreSQL
    dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres # PostgreSQL connection string
  avro:
    enabled: false # Whether to enable Avro
    path: <AVRO-OUTPUT-PATH> # Path to the Avro output file
  mlflow:
    enabled: false # Whether to enable MLflow
    mlflow_uri: http://localhost:59000 # MLflow server URI``
    username: <CHANGE_ME> # MLflow server username
    password: <CHANGE_ME> # MLflow server password
```
