import subprocess
import time
import os

from ..logger import get_logger
from prometheus_client import start_http_server


def start_monitoring(user_data_path: str):
    """Starts the Prometheus and Grafana monitoring services."""
    compose_file = os.path.join(os.path.dirname(__file__), "docker-compose.yml")

    # Check if docker-compose file exists
    if not os.path.exists(compose_file):
        get_logger().warning(
            f"Docker compose file not found at {compose_file}. "
            "Skipping monitoring services."
        )
        return False

    # 1. Resolve to an absolute path. 
    # If user provides "./my_db", this converts it to "/home/user/project/my_db"
    abs_data_path = os.path.abspath(user_data_path)

    # 2. Ensure the directory exists (Docker will create it, but good practice to check permissions)
    os.makedirs(abs_data_path, exist_ok=True)
    get_logger().info(f"Database will be stored at: {abs_data_path}")

    # 3. Prepare the Environment Variables
    # Copy the current system env vars so we don't lose things like PATH
    cmd_env = os.environ.copy()
    
    # Inject our custom path variable
    cmd_env["CLICKHOUSE_DATA_PATH"] = abs_data_path

    get_logger().info("Starting Prometheus and Grafana monitoring services...")
    get_logger().info(
        f"Using ClickHouse data path: {cmd_env['CLICKHOUSE_DATA_PATH']}"
    )
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", compose_file, "up", "-d"],
            check=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            env=cmd_env,
        )
        get_logger().debug(f"Docker compose stdout: {result.stdout}")
        time.sleep(5)  # Wait for services to start
        get_logger().info(
            "Monitoring services started. "
            "Grafana: http://localhost:3000 (admin/admin), "
            "Prometheus: http://localhost:9091"

        )

        return True
    except subprocess.CalledProcessError as e:
        get_logger().error(f"Docker compose failed with return code {e.returncode}")
        get_logger().error(f"stdout: {e.stdout}")
        get_logger().error(f"stderr: {e.stderr}")

        # Check for common permission error
        if "permission denied" in e.stderr.lower():
            get_logger().warning(
                "Docker permission denied. Please run: "
                "'sudo usermod -aG docker $USER' and then log out/in, "
                "or run your script with 'sudo'. "
                "Continuing without monitoring..."
            )
        return False
    except FileNotFoundError as e:
        get_logger().warning(
            f"Docker command not found: {e}. "
            "Please install Docker. "
            "Continuing without monitoring..."
        )
        return False


def stop_monitoring():
    """Stops the Prometheus and Grafana monitoring services."""
    compose_file = os.path.join(os.path.dirname(__file__), "docker-compose.yml")

    if not os.path.exists(compose_file):
        return False

    get_logger().info("Stopping Prometheus and Grafana monitoring services...")
    try:
        subprocess.run(
            ["docker", "compose", "-f", compose_file, "down"],
            check=False,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
        )
        get_logger().info("Monitoring services stopped.")
        return True
    except FileNotFoundError as e:
        get_logger().warning(f"Docker command not found: {e}")
        return False
