"""
Create logger named agentsociety as singleton for ray.
"""

import logging
import time
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
import socket

__all__ = ["get_logger", "set_logger_level", "attach_otlp_handler"]


def get_logger():
    logger = logging.getLogger("fastsociety")
    # check if there is already a handler, avoid duplicate output
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        # set propagate to False, avoid duplicate output
        logger.propagate = False
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


def set_logger_level(level: str):
    """Set the logger level"""
    get_logger().setLevel(level)


def attach_otlp_handler(host="localhost", port=4317):
    """
    Attaches the OpenTelemetry handler to the existing logger.
    Call this after Alloy is running.
    """

    logger = get_logger()

    for h in logger.handlers:
        if isinstance(h, LoggingHandler):
            logger.info("OTLP logging handler is already attached.")
            return

    if not _wait_for_port(host, port, timeout=5):
        logger.warning(f"Alloy not reachable at {host}:{port}. OTLP logging disabled.")
        return

    try:
        resource = Resource.create({"service.name": "fastsociety"})
        endpoint = f"{host}:{port}"

        exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)

        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

        otlp_handler = LoggingHandler(
            level=logging.INFO, logger_provider=logger_provider
        )
        logger.addHandler(otlp_handler)
        logger.info(f"OTLP logging handler attached to {endpoint}.")
    except Exception as e:
        logger.error(f"Failed to initialize OTLP logging handler: {e}")


def _wait_for_port(host, port, timeout=5):
    """Internal helper to check if a port is open."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(1)
    return False
