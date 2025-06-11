# Launching the Web UI

```{admonition} Hint
:class: hint
If you want to deploy the service locally, you can follow the instructions in this section. If you prefer not to deploy it yourself and would rather use our online platform directly, you can skip this section.
```

Then, create a configuration file (e.g., `config.yaml`) with the required environment information. The configuration include:

```{admonition} Hint
:class: hint
The configuration follows similar format to the [Configuration](../02-configuration/01-configuration.md) section.
So you can use the configuration file for simulation to launch the Web UI if you don't want to change `addr`, `read_only`, `debug`, and `logging_level`.
```

- Required field:
  ```yaml
  env: EnvConfig  # Environment configuration, see EnvConfig definition in `agentsociety/configs/env.py`
  ```

- Optional fields:
  ```yaml
  addr: str            # Service address, default "127.0.0.1:8080"
  read_only: bool      # Read-only mode, default false
  debug: bool          # Debug mode, default false
  logging_level: str   # Logging level, default "INFO"
  ```

Once the configuration is ready, start the backend service using the following command:

 ```bash
 agentsociety ui -c config.yaml
 ```

- config.yaml example
    ```yaml
    addr: 127.0.0.1:8080 # Optional: Address for the UI service
    env: # Required
      db:
        enabled: true    # Enable database storage
        db_type: sqlite | postgresql
        pg_dsn: postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE  # PostgreSQL connection string
    ```

The UI service will be available at `http://localhost:8080` or the address specified in your configuration file.

```{admonition} Hint
:class: hint
The default `addr` is `127.0.0.1:8080` so that the WebUI server is only accessible on the local machine.
If you want to access the WebUI from other machines, you can change the `addr` to `0.0.0.0:8080`.
Please pay attention to the security risk when changing the `addr` to open to the public.
```