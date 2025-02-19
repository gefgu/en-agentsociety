# Simulation Config

```{admonition} Caution
:class: caution
This document is currently under active development. The complete version will be available soon. Stay tuned!
```

The `SimConfig` class centralizes runtime configurations for agent-based simulations. It supports multi-modal integrations including LLM services, distributed MQTT communication, map data, and metric tracking.

## Key Components

1. LLM Request Configuration (`LLMRequestConfig`)
Configures Language Model integrations (e.g., OpenAI, Anthropic).

```python
class LLMRequestConfig(BaseModel):
    request_type: LLMRequestType = Field(  # Provider type (openai/anthropic/etc)
        ..., 
        example="openai"
    )
    api_key: Union[list[str], str] = Field(  # API key(s) for load balancing
        ...,
        example=["sk-abc123", "sk-def456"]
    )
    model: str = Field(  # Model identifier
        ...,
        example="gpt-4-1106-preview"
    )
```

2. Simulator Runtime (`SimulatorRequestConfig`)
Controls core simulation parameters.

```python
class SimulatorRequestConfig(BaseModel):
    task_name: str = Field(  # Simulation scenario identifier
        "citysim", 
        example="urban-economy-v2"
    )
    max_day: int = Field(  # Hard stop after N days
        1000,
        ge=1,
        example=365
    )
    start_step: int = Field(  # Initial simulation step (in seconds)
        28800,  # 8 AM
        description="Simulation start time in seconds from midnight"
    )
    total_step: int = Field(  # Total simulation duration
        24 * 60 * 60 * 365,  # 1 year
        example=86400  # 1 day
    )
    min_step_time: int = Field(  # Minimum real-time between steps (ms)
        1000,
        description="Controls simulation speed. 1000ms = real-time speed"
    )
```

3. MQTT Communication (`MQTTConfig`)
Configures message broker for distributed simulations.

```python
class MQTTConfig(BaseModel):
    server: str = Field(  # Broker host
        ...,
        example="mqtt.eclipseprojects.io"
    )
    port: int = Field(  # Connection port
        ...,
        ge=1, 
        le=65535,
        example=1883
    )
    username: Optional[str] = Field(  # Auth credentials
        None,
        example="simulation_user"
    )
    password: Optional[str] = Field(
        None,
        example="secure_password_123"
    )
```

4. Spatial Configuration (`MapRequestConfig`)
Defines simulation environment geometry.

```python
class MapRequestConfig(BaseModel):
    file_path: str = Field(  # Path to map file
        ...,
        description="Supports GeoJSON and proprietary .map formats",
        example="/maps/berlin_2023.geojson"
    )
```

5. Metric Tracking (`MetricRequest`)
Configures experiment telemetry collection.

```python
class MetricRequest(BaseModel):
    mlflow: Optional[MlflowConfig] = Field(  # MLflow integration
        None,
        example=MlflowConfig.create(
            username="admin", 
            password="mlflow_pass",
            mlflow_uri="http://localhost:5000"
        )
    )
```

6. Data Persistence
```python
class PostgreSQLConfig(BaseModel):  # Relational storage
    dsn: str = Field(  # Connection string
        ...,
        example="postgresql://user:pass@localhost:5432/simdb"
    )
    enabled: bool = Field(  # Toggle storage
        False,
        example=True
    )

class AvroConfig(BaseModel):  # Binary serialization
    path: str = Field(  # Output directory
        ...,
        example="/data/avro_output"
    )
    enabled: bool = Field(
        False,
        example=True
    )
```

## Configuration Methods

Chainable builder pattern for fluent configuration:

```python
config = (
    SimConfig()
    # Set LLM provider with failover keys
    .SetLLMRequest(
        request_type=LLMRequestType.OPENAI,
        api_key=["sk-primary", "sk-backup"], 
        model="gpt-4-turbo"
    )
    # Configure distributed MQTT
    .SetMQTT(
        server="sim-cluster.prod", 
        port=1883,
        username="node_01",
        password="cluster_secret"
    )
    # Load city layout
    .SetMapRequest("/maps/tokyo_v3.map")
    # Enable metrics to MLflow
    .SetMetricRequest(
        username="mlflow_user",
        password="tracking123",
        mlflow_uri="http://mlflow.prod:5000"
    )
    # Enable PostgreSQL storage
    .SetPostgreSql(
        dsn="postgresql://simwriter:write_pass@db.prod:5432/simulations",
        enabled=True
    )
)
```
