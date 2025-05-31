import base64
import importlib.metadata
import json
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlsplit

import click
from fastapi import APIRouter
import yaml
from pydantic import BaseModel, Field, model_validator

version_string_of_agentsociety = importlib.metadata.version("agentsociety")

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
PARAM_DECLS_VERSION = ("-V", "--version")


def load_config(
    config_path: Optional[str] = None, config_base64: Optional[str] = None
) -> Dict[Any, Any]:
    """Load configuration file, supports JSON and YAML formats, as well as base64 encoded config"""
    if config_base64:
        # Decode base64 config
        config_str = base64.b64decode(config_base64).decode("utf-8")
        # For base64 encoded config, try both JSON and YAML parsing
        try:
            # Try to parse as JSON
            return json.loads(config_str)
        except json.JSONDecodeError:
            try:
                # Try to parse as YAML
                return yaml.safe_load(config_str)
            except yaml.YAMLError as e:
                raise click.BadParameter(f"Failed to parse base64 config: {e}")
    elif config_path:
        # Determine format based on file extension
        path = Path(config_path)
        if not path.exists():
            raise click.BadParameter(f"Config file {config_path} does not exist")
        file_ext = path.suffix.lower()
        if file_ext in [".json"]:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise click.BadParameter(f"Failed to parse JSON config file: {e}")
        elif file_ext in [".yaml", ".yml"]:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise click.BadParameter(f"Failed to parse YAML config file: {e}")
        else:
            raise click.BadParameter(f"Unsupported config file format: {file_ext}")
    else:
        raise click.BadParameter("No config file or base64 encoded config provided")


def common_options(f):
    """Common configuration options decorator"""
    f = click.option("--config", "-c", help="Path to config file (.json, .yml, .yaml)")(
        f
    )
    f = click.option(
        "--config-base64", help="Base64 encoded config with JSON or YAML format"
    )(f)
    return f


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=version_string_of_agentsociety, prog_name="AgentSociety")
def cli():
    """AgentSociety CLI tool"""
    pass


@cli.command()
@common_options
def ui(config: str, config_base64: str):
    """Launch AgentSociety GUI"""
    config_data = load_config(config, config_base64)

    import uvicorn

    from ..configs import EnvConfig
    from ..logger import get_logger, set_logger_level
    from ..webapi.app import create_app, empty_get_tenant_id
    from ..executor import ProcessExecutor

    class WebUIConfig(BaseModel):
        addr: str = Field(default="127.0.0.1:8080")
        env: EnvConfig
        read_only: bool = Field(default=False)
        debug: bool = Field(default=False)
        logging_level: str = Field(default="INFO")

    async def _main():
        c = WebUIConfig.model_validate(config_data)
        set_logger_level(c.logging_level.upper())
        get_logger().info("Launching AgentSociety WebUI")
        get_logger().debug(f"WebUI config: {c}")
        # for compatibility with the old config
        # postgres:// in DSN is not supported by SQLAlchemy
        # replace it with postgresql://

        pg_dsn = c.env.pgsql.dsn
        if pg_dsn.startswith("postgresql://"):
            pg_dsn = pg_dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
        executor = ProcessExecutor(c.env.home_dir)
        get_tenant_id = empty_get_tenant_id
        more_state: Dict[str, Any] = {
            "executor": executor,
        }
        more_router = None

        app = create_app(
            pg_dsn=pg_dsn,
            mlflow_url=c.env.mlflow.mlflow_uri if c.env.mlflow.enabled else "",
            read_only=c.read_only,
            env=c.env,
            get_tenant_id=get_tenant_id,
            more_router=more_router,
            more_state=more_state,
        )

        # Start server
        url = urlsplit("//" + c.addr)
        host, port = url.hostname, url.port
        if host is None or host == "" or host == "localhost":
            host = "127.0.0.1"
        if port is None:
            port = 8080
        log_level = "debug" if c.debug else "info"
        get_logger().info("Starting server at %s:%s", host, port)
        config = uvicorn.Config(app, host=host, port=port, log_level=log_level)
        server = uvicorn.Server(config)
        await server.serve()

    import asyncio

    asyncio.run(_main())


@cli.command()
@common_options
def check(config: str, config_base64: str):
    import os

    """Pre-check the config"""
    config_dict = load_config(config, config_base64)

    from ..configs import Config

    c = Config.model_validate(config_dict)
    click.echo(f"Config format check. {click.style('Passed.', fg='green')}")

    # =================
    # check the connection to the pgsql server
    # =================
    from psycopg import connect
    from psycopg.errors import OperationalError

    try:
        conn = connect(
            conninfo=c.env.pgsql.dsn,
            autocommit=True,
        )
        conn.execute("SELECT 1")
        click.echo(f"Pgsql connection check. {click.style('Passed.', fg='green')}")
    except OperationalError as e:
        click.echo(f"Pgsql connection check. {click.style('Failed:', fg='red')} {e}")
        click.echo(
            f"Explanation: Please check the `dsn` (value={c.env.pgsql.dsn}) of the pgsql server. The format of `dsn` is `postgresql://<username>:<password>@<host>:<port>/<database_name>`. The item wrapped in `<>` should be replaced with the actual values."
        )
        error_msg = str(e)
        if "password authentication failed" in error_msg:
            click.echo(
                f"Explanation: The username or password of the pgsql server is incorrect."
            )
        elif "Temporary failure in name resolution" in error_msg:
            click.echo(
                f"Explanation: The host of the pgsql server is invalid. Maybe you should use `localhost` or `127.0.0.1` instead if you are running the simulation on a single machine (used to run docker compose)."
            )
        elif "Connection refused" in error_msg:
            click.echo(
                f"Explanation: The host or port of the pgsql server is incorrect."
            )
    except Exception as e:
        click.echo(f"Pgsql connection check. {click.style('Failed:', fg='red')} {e}")

    # =================
    # check the connection to the mlflow server
    # =================
    from mlflow import MlflowClient
    from mlflow.exceptions import MlflowException

    if c.env.mlflow.enabled:
        try:
            if c.env.mlflow.username is not None:
                os.environ["MLFLOW_TRACKING_USERNAME"] = c.env.mlflow.username
            if c.env.mlflow.password is not None:
                os.environ["MLFLOW_TRACKING_PASSWORD"] = c.env.mlflow.password
            os.environ["MLFLOW_HTTP_REQUEST_MAX_RETRIES"] = "1"
            os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = "5"
            client = MlflowClient(c.env.mlflow.mlflow_uri)
            client.get_experiment_by_name(c.exp.name)
            click.echo(f"Mlflow connection check. {click.style('Passed.', fg='green')}")
        except MlflowException as e:
            click.echo(
                f"Mlflow connection check. {click.style('Failed:', fg='red')} {e}"
            )
            error_msg = str(e)
            if e.get_http_status_code() == 401:
                click.echo(
                    f"Explanation: The `username` (value={c.env.mlflow.username}) or `password` (value={c.env.mlflow.password}) of the mlflow server is incorrect."
                )
            else:
                click.echo(
                    f"Explanation: Please check the `mlflow_uri` (value={c.env.mlflow.mlflow_uri}) of the mlflow server. The format of `mlflow_uri` is `http://<host>:<port>` or `https://<host>:<port>`. The item wrapped in `<>` should be replaced with the actual values."
                )
                if "Temporary failure in name resolution" in error_msg:
                    click.echo(
                        f"Explanation: The host of the mlflow server is invalid. Maybe you should use `localhost` or `127.0.0.1` instead if you are running the simulation on a single machine (used to run docker compose)."
                    )
                elif "Connection refused" in error_msg:
                    click.echo(
                        f"Explanation: The host or port of the mlflow server is incorrect."
                    )
                else:
                    click.echo(
                        f"Explanation: Please check the `mlflow_uri` (value={c.env.mlflow.mlflow_uri}) of the mlflow server."
                    )
        except Exception as e:
            click.echo(
                f"Mlflow connection check. {click.style('Failed:', fg='red')} {e}"
            )

    # =================
    # check whether the map file exists
    # =================
    if not os.path.exists(c.map.file_path):
        click.echo(
            f"Map file {c.map.file_path} does not exist. {click.style('Failed.', fg='red')}"
        )
        return
    click.echo(f"Map file. {click.style('Passed.', fg='green')}")


@cli.command()
@common_options
def run(
    config: str,
    config_base64: str,
):
    """Run the simulation"""
    config_dict = load_config(config, config_base64)

    import requests
    from ..configs import Config
    from ..simulation import AgentSociety
    from ..cityagent import default

    c = Config.model_validate(config_dict)

    # Check if we need to import community modules
    need_community = False
    if c.agents.citizens:
        for citizen in c.agents.citizens:
            if isinstance(citizen.agent_class, str):
                need_community = True
                break
            # go to check blocks
            if citizen.blocks is not None:
                for block in citizen.blocks.keys():
                    if isinstance(block, str):
                        need_community = True
                        break

    if c.agents.supervisor is not None and isinstance(
        c.agents.supervisor.agent_class, str
    ):
        need_community = True

    if c.exp.workflow:
        for step in c.exp.workflow:
            if step.func is not None and isinstance(step.func, str):
                need_community = True
                break

    if need_community:
        try:
            from agentsociety_community.agents import citizens, supervisors
            from agentsociety_community.blocks import citizens as citizen_blocks
            from agentsociety_community.workflows import functions as workflow_functions

            # get the mapping of the agent class
            workflow_function_map = workflow_functions.get_type_to_cls_dict()
            citizens_class_map = citizens.get_type_to_cls_dict()
            citizen_blocks_class_map = citizen_blocks.get_type_to_cls_dict()
            supervisors_class_map = supervisors.get_type_to_cls_dict()

            # process the agent_class in citizens
            for citizen in c.agents.citizens:
                if isinstance(citizen.agent_class, str):
                    if citizen.agent_class == "citizen":
                        # Skip mapping if it's just a citizen
                        continue
                    citizen.agent_class = citizens_class_map[citizen.agent_class]()
                if citizen.blocks is not None:
                    new_blocks = {}
                    for block_name, block_params in citizen.blocks.items():
                        if isinstance(block_name, str):
                            new_blocks[block_name] = citizen_blocks_class_map[block_name]()
                        else:
                            new_blocks[block_name] = block_params
                    citizen.blocks = new_blocks

            # process the agent_class in supervisor
            if c.agents.supervisor is not None and isinstance(
                c.agents.supervisor.agent_class, str
            ):
                c.agents.supervisor.agent_class = supervisors_class_map[
                    c.agents.supervisor.agent_class
                ]()

            # process the func in workflow
            for step in c.exp.workflow:
                if step.func is not None and isinstance(step.func, str):
                    # if func is a string, try to get the corresponding function from function_map
                    imported_func = workflow_function_map[step.func]()
                    step.func = imported_func
        except ImportError as e:
            import traceback

            print(traceback.format_exc())
            print(
                "agentsociety_community is not installed. Please install it with `pip install agentsociety-community`"
            )
            raise e

    c = default(c)
    society = AgentSociety(c)

    async def _run():
        try:
            await society.init()
            await society.run()
        finally:
            await society.close()

    import asyncio

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
