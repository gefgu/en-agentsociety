# Record Experiment with Avro

## Usage

To enable Avro storage for recording experiment data, assign Avro configuration in the environment config:

```python
config = Config(
    ...
    env=EnvConfig(
        avro=AvroConfig(
            path="<SAVE-PATH>",
            enabled=True,
        ),
    ),
)
```

## Schema Definition

```json
{
    "type": "record",
    "name": "ExperimentInfo",
    "namespace": "agentsociety.simulation",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "name", "type": "string"},
        {"name": "num_day", "type": "int", "default": 0},
        {"name": "status", "type": "int"},
        {"name": "cur_day", "type": "int"},
        {"name": "cur_t", "type": "double"},
        {"name": "config", "type": "string"},
        {"name": "error", "type": "string"},
        {"name": "created_at", "type": "string"},
        {"name": "updated_at", "type": "string"},
    ],
}

```

## Agent Profile
```json
{
    "doc": "Agent属性",
    "name": "AgentProfile",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "profile", "type": "string"}
    ]
}
```

## Agent Dialog
```json
{
    "doc": "Agent对话",
    "name": "AgentDialog",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "type", "type": "int"},
        {"name": "speaker", "type": "string"},
        {"name": "content", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        }
    ]
}
```

## Agent Status
```json
{
    "doc": "Agent状态",
    "name": "AgentStatus",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "lng", "type": ["null", "double"]},
        {"name": "lat", "type": ["null", "double"]},
        {"name": "parent_id", "type": ["null", "int"]},
        {"name": "friend_ids", "type": {"type": "array", "items": "int"}},
        {"name": "action", "type": "string"},
        {"name": "status", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        }
    ]
}
```

## Survey 
```json
{
    "doc": "Agent问卷",
    "name": "AgentSurvey",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "survey_id", "type": "string"},
        {"name": "result", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        }
    ]
}
```

## Global Prompt
```json
{
    "doc": "全局Prompt",
    "name": "GlobalPrompt",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "prompt", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        }
    ]
}