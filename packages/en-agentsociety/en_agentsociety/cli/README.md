# `cli/` — Command-Line Interface

This package provides the `en-agentsociety` command-line tool for running and managing simulations without writing Python code.

---

## Files

| File | Purpose |
|---|---|
| `cli.py` | Click/Typer CLI entry-point |

---

## Commands

```bash
# Run a simulation from a YAML config file
en-agentsociety run --config experiment.yaml

# Check experiment status
en-agentsociety status <experiment-id>

# List all experiments in a database
en-agentsociety list --db sqlite:///experiments.db

# Stop a running experiment
en-agentsociety stop <experiment-id>

# Export results to JSON
en-agentsociety export <experiment-id> --output results.json

# Start the web API server
en-agentsociety serve --host 0.0.0.0 --port 8080
```

---

## Config File Format

The CLI accepts YAML or JSON config files:

```yaml
name: my_city_simulation
llm:
  - model: gpt-4o
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1

agents:
  citizens:
    - agent_class: en_agentsociety.cityagent.SocietyAgent
      number: 100

env:
  db:
    pg_dsn: ${DATABASE_URL}

exp:
  workflow:
    - type: run
      days: 7
    - type: survey
      survey: ...
```

Environment variable interpolation (`${VAR_NAME}`) is supported.

---

## Installation

The CLI is automatically registered when you install the package:

```bash
pip install en-agentsociety
en-agentsociety --help
```
