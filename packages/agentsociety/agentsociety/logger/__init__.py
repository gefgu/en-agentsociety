"""
Create logger named agentsociety as singleton for ray.
"""

import json
import logging
import time
from typing import Dict, Optional
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
import socket

__all__ = ["get_logger", "set_logger_level", "attach_otlp_handler"]


_exp_id: Optional[str] = None


class ExpIdFilter(logging.Filter):
    """
    Logging filter to add exp_id to log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if _exp_id is not None:
            record.exp_id = _exp_id
        return True


def set_exp_id(exp_id: str) -> None:
    """
    Set the experiment ID globally. This will be automatically added to all log records.
    Call this once when the simulation starts.

    Args:
        exp_id: The experiment ID to set globally

    Example:
        >>> set_exp_id("exp_20250120_001")
        >>> get_logger().info("This log will include exp_id automatically")
    """
    global _exp_id
    _exp_id = str(exp_id)
    get_logger().debug(f"Global exp_id set to: {_exp_id}")


class FormattedOLTPHandler(LoggingHandler):
    """
    Custom OTLP logging handler with Loki-compatible formatting.
    """

    def emit(self, record: logging.LogRecord) -> None:
        original_args = record.args

        attributes = {}
        if isinstance(original_args, dict):
            attributes.update(original_args)

        context_attrs = {
            "code.filepath": record.pathname,
            "code.lineno": record.lineno,
            "code.func": record.funcName,
            "code.module": record.module,
        }

        if hasattr(record, "agent_id"):
            context_attrs["agent_id"] = record.agent_id
        if hasattr(record, "exp_id"):
            context_attrs["exp_id"] = record.exp_id

        attributes.update(context_attrs)

        record.args = attributes

        try:
            super().emit(record)
        except Exception as e:
            self.handleError(record)
        finally:
            record.args = original_args


def get_logger():
    logger = logging.getLogger("fastsociety")
    # check if there is already a handler, avoid duplicate output
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        # set propagate to False, avoid duplicate output
        logger.propagate = False
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

    if not any(isinstance(f, ExpIdFilter) for f in logger.filters):
        logger.addFilter(ExpIdFilter())

    return logger


def set_logger_level(level: str):
    """Set the logger level"""
    get_logger().setLevel(level)


def attach_otlp_handler(host="localhost", port=4317, labels: Dict[str, str] = None):
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
        resource_attrs = {
            "service.name": "fastsociety",
            "service.version": "1.0.0",
            "loki.resource.labels": "service.name, exp_id, agent_id",
        }
        if _exp_id is not None:
            resource_attrs["exp_id"] = _exp_id
        endpoint = f"{host}:{port}"

        exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)

        logger_provider = LoggerProvider(
            resource=Resource.create(attributes=resource_attrs)
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

        otlp_handler = FormattedOLTPHandler(
            level=logging.DEBUG, logger_provider=logger_provider
        )

        otlp_handler.setLevel(logging.DEBUG)
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
