import asyncio
import base64
import json
import logging
import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import datetime
import functools

import aiodocker

logger = logging.getLogger("docker_runner")


async def run_experiment_in_container(
    config_base64: Optional[str] = None,
    config: Optional[str] = None,
) -> str:
    """
    Run experiment in Docker container.

    Args:
        config_base64: Base64 encoded configuration
        config_file: Path to configuration file

    Returns:
        Container ID

    Raises:
        Exception: If container creation or startup fails
    """
    # Load configuration
    config_dict = None

    # Load configuration from file
    if config and not config_base64:
        if not os.path.exists(config):
            raise ValueError(f"Configuration file {config} does not exist")

        file_ext = Path(config).suffix.lower()
        if file_ext == ".json":
            with open(config, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        elif file_ext in [".yaml", ".yml"]:
            import yaml

            with open(config, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_ext}")

    # Load configuration from base64
    elif config_base64:
        try:
            config_dict = json.loads(base64.b64decode(config_base64).decode())
        except Exception as e:
            raise ValueError(f"Failed to decode base64 configuration: {e}")

    # Ensure configuration exists
    if not config_dict:
        raise ValueError("No configuration provided")

    # Get map paths from configuration
    map_path = config_dict.get("map", {}).get("file_path")
    map_cache_path = config_dict.get("map", {}).get("cache_path")

    # Check if either map file or cache file exists
    map_dir = None

    # First check cache path
    if map_cache_path and os.path.exists(map_cache_path):
        map_dir = os.path.dirname(map_cache_path)
        logger.info(f"Using map cache file: {map_cache_path}")
    # Then check map path
    elif map_path and os.path.exists(map_path):
        map_dir = os.path.dirname(map_path)
        logger.info(f"Using map file: {map_path}")
    # If neither exists, create directories and warn
    elif map_path or map_cache_path:
        if map_path:
            map_dir = os.path.dirname(map_path)
            os.makedirs(map_dir, exist_ok=True)
            logger.error(f"Map file does not exist: {map_path}")
        if map_cache_path:
            cache_dir = os.path.dirname(map_cache_path)
            os.makedirs(cache_dir, exist_ok=True)
            logger.error(f"Map cache file does not exist: {map_cache_path}")
        raise ValueError("Map file or cache is not found")
    else:
        # No map files specified
        logger.error("No map file or cache file specified in configuration")
        raise ValueError("No map file or cache file specified in configuration")

    # Check avro configuration
    avro_enabled = config_dict.get("avro", {}).get("enabled", False)
    avro_path = config_dict.get("avro", {}).get("path", "avro")

    # If avro is enabled, ensure directory exists
    if avro_enabled:
        os.makedirs(avro_path, exist_ok=True)
        logger.info(f"Avro enabled, output directory: {avro_path}")

    # Update paths in configuration to container paths
    container_config_dict = config_dict.copy()

    # Update map file paths for container
    if map_path:
        map_filename = os.path.basename(map_path)
        container_config_dict["map"]["file_path"] = f"/maps/{map_filename}"

    if map_cache_path:
        cache_filename = os.path.basename(map_cache_path)
        container_config_dict["map"]["cache_path"] = f"/maps/{cache_filename}"

    # Configure container
    binds = []

    # Add map directory mount if available
    if map_dir:
        binds.append(f"{os.path.abspath(map_dir)}:/maps:ro")
        logger.info(f"Added map bind mount: {os.path.abspath(map_dir)} -> /maps")

    # If cache directory is different from map directory, add it too
    if map_cache_path and os.path.dirname(map_cache_path) != map_dir:
        cache_dir = os.path.dirname(map_cache_path)
        binds.append(f"{os.path.abspath(cache_dir)}:/cache:ro")
        logger.info(f"Added cache bind mount: {os.path.abspath(cache_dir)} -> /cache")

        # Update cache path in container config
        cache_filename = os.path.basename(map_cache_path)
        container_config_dict["map"]["cache_path"] = f"/cache/{cache_filename}"
    elif map_cache_path:
        # Cache is in the same directory as map, update path
        cache_filename = os.path.basename(map_cache_path)
        container_config_dict["map"]["cache_path"] = f"/maps/{cache_filename}"

    # If avro is enabled, add mount
    if avro_enabled:
        if os.path.isabs(avro_path):
            binds.append(f"{os.path.abspath(avro_path)}:{avro_path}:rw")
            logger.info(
                f"Added avro bind mount: {os.path.abspath(avro_path)} -> {avro_path}"
            )
        else:
            # Relative path mount
            binds.append(f"{os.path.abspath(avro_path)}:/avro:rw")
            logger.info(f"Added avro bind mount: {os.path.abspath(avro_path)} -> /avro")

    # Convert to base64
    container_config_base64 = base64.b64encode(
        json.dumps(container_config_dict).encode()
    ).decode()

    # Initialize Docker client
    docker_host = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    docker = aiodocker.Docker(url=docker_host)

    try:
        container_config = {
            "Image": "agentsociety-runner:latest",
            "Cmd": [
                "python",
                "-m",
                "agentsociety.cli.cli",
                "run",
                "--config-base64",
                container_config_base64,
            ],
            "HostConfig": {
                "NetworkMode": "host",
                "Binds": binds,
            },
            "Labels": {
                "app": "agentsociety",
                "created_at": datetime.datetime.now().isoformat(),
                "description": config_dict.get("description", ""),
            },
        }

        # Create container
        container = await docker.containers.create(config=container_config)

        # Get container ID
        container_id = container.id
        logger.info(f"Created container: {container_id}")

        # Start container
        await container.start()
        logger.info(f"Started container: {container_id}")

        return container_id

    except Exception as e:
        logger.error(f"Error running experiment in container: {str(e)}")
        # Print detailed error information
        import traceback

        logger.error(traceback.format_exc())
        raise
    finally:
        await docker.close()


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    return wrapper


@handle_errors
def main():
    """Run experiment in Docker container."""
    # Create argument parser
    parser = argparse.ArgumentParser(description="Run experiment in Docker container")

    # Create mutually exclusive group
    group = parser.add_mutually_exclusive_group(required=True)

    # Add command line arguments to the group
    group.add_argument("--config", help="Path to configuration file")
    group.add_argument("--config-base64", help="Base64 encoded configuration")

    # Parse command line arguments
    args = parser.parse_args()

    # Run experiment
    container_id = asyncio.run(
        run_experiment_in_container(
            config_base64=args.config_base64,
            config=args.config,
        )
    )

    print(f"Experiment started in container: {container_id}")
    sys.exit(0)


if __name__ == "__main__":
    main()
