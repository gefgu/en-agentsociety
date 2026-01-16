import subprocess
import time
import os

from ..logger import get_logger
from prometheus_client import start_http_server


def start_monitoring():
    """Starts the Prometheus and Grafana monitoring services."""
    compose_file = os.path.join(os.path.dirname(__file__), "docker-compose.yml")

    # Check if docker-compose file exists
    if not os.path.exists(compose_file):
        get_logger().warning(
            f"Docker compose file not found at {compose_file}. "
            "Skipping monitoring services."
        )
        return False

    get_logger().info("Starting Prometheus and Grafana monitoring services...")
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", compose_file, "up", "-d"],
            check=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
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
