# Simulation Config

`SimConfig` class centralizes runtime configurations for agent-based simulations. It supports multi-modal integrations including LLM services, distributed MQTT communication, map data, and metric tracking.

## LLM Control

- LLM Request Configuration (`LLMRequestConfig`)
    Configures Language Model integrations (e.g., OpenAI, Anthropic). This configuration controls the basic access to the LLM, including the selection of the LLM provider, the corresponding model, and one or more API keys (for higher QPM).

    ```python
    class LLMRequestConfig(BaseModel):
        request_type: LLMRequestType = Field(  # Provider type (openai, etc)
            ..., 
            example="zhipuai"
        )
        api_key: Union[list[str], str] = Field(  # API key(s) for load balancing
            ...,
            example=["sk-abc123", "sk-def456"]
        )
        model: str = Field(  # Model identifier
            ...,
            example="GLM-4-Flash"
        )
    ```

## Simulation Environment Control

- Simulator Runtime (`SimulatorRequestConfig`)
    This configuration controls the simulation of the urban environment, including the starting time point of the simulation, the number of simulation steps per day, and the progression of the urban environment time for each simulation step.

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
        log_dir: str = Field(  # Directory for simulation logs
            "./log",
            example="/var/log/simulation"
        )
        steps_per_simulation_step: int = Field(  # Time increment per step (seconds)
            300,
            example=300,  # 5 minutes
            description="Urban space forward time during one simulation forward step"
        )
        steps_per_simulation_day: int = Field(  # Time increment per day (seconds)
            3600,  
            example=3600,  # 1 hour
            description="Urban space forward time during one simulation forward day"
        )
        primary_node_ip: str = Field(  # Host for primary simulation node
            "localhost",
            example="10.0.0.5",
            description="Primary node IP address for distributed simulation"
        )
    ```

- Simulation Location Configuration (`MapRequestConfig`)
    Defines simulation environment.

    ```python
    class MapRequestConfig(BaseModel):
        file_path: str = Field(  # Path to map file
            ...,
            example="data/beijing_map.pb" # beijing 5 ring
        )
    ```

## Infrastructure Setup

- Data Persistence
    How and where to store your experiment data.
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
- MQTT Communication (`MQTTConfig`)
    Configures message broker for distributed simulations. 
    **Required** for agents communication.

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

## Metric Tracking
- (`MetricRequest`)
    Configures experiment telemetry collection. We support MLflow as metric tracking tool.

    ```python
    class MetricRequest(BaseModel):
        mlflow: Optional[MlflowConfig] = Field(  # MLflow integration
            None,
            example=MlflowConfig(
                username="admin", 
                password="mlflow_pass",
                mlflow_uri="http://localhost:5000"
            )
        )
    ```

## Configuration Methods

Chainable builder pattern for fluent configuration:

```python
from agentsociety.exp_config import ExpConfig, SimConfig, WorkflowStep, WorkflowType

config = (
    SimConfig()
    # Set LLM provider with failover keys
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI,
        api_key=["sk-primary", "sk-backup"], 
        model="GLM-4-Flash"
    )
    # Configure simulation parameters
    .SetSimulatorRequest(
        task_name="citysim",
        max_day=365,
        start_step=28800,  # 8 AM
        total_step=86400,  # 1 day
        log_dir="/var/log/simulation",
        steps_per_simulation_step=300,  # 5 min
        steps_per_simulation_day=3600,  # 1 hour
        primary_node_ip="10.0.1.5"
    )
    # Configure distributed MQTT
    .SetMQTT(
        server="MQTT-BROKER", 
        port=1883,
        username="USER-NAME",
        password="USER-NAME"
    )
    # Load city layout
    .SetMapRequest("data/beijing_map.pb")
    # Enable metrics to MLflow
    .SetMetricRequest(
        username="USER-NAME",
        password="PASSWORD",
        mlflow_uri="http://mlflow.prod:5000"
    )
    # Enable PostgreSQL storage
    .SetPostgreSql(
        dsn="postgresql://simwriter:write_pass@db.prod:5432/simulations",
        enabled=True
    )
    # Configure Avro serialization
    .SetAvro(
        path="data/avro_output",
        enabled=True
    )
)
```
