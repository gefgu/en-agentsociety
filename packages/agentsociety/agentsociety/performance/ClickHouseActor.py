from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
import clickhouse_connect
from clickhouse_connect.driver.client import Client
from pathlib import Path
from ..logger import get_logger
import ray
import time
from collections import defaultdict, deque
from typing import TypedDict
from datetime import datetime


create_adjust_needs_table_query = """
CREATE TABLE IF NOT EXISTS NeedsBlock_adjust_needs (
    -- 1. Use LowCardinality for repeated strings to save massive space
    exp_id LowCardinality(String),
    simulation_step Int32,
    timestamp DateTime64(3), -- (3) allows millisecond precision
    agent_id Int32,
    
    -- 2. The Heavy Text
    prompt String CODEC(ZSTD(3)), -- Explicit compression for large text
    
    -- 3. Metrics
    actor LowCardinality(String),
    current_need LowCardinality(String),

    current_hunger Float32,
    current_energy Float32,
    current_safety Float32,
    current_social Float32,

    new_hunger Float32,
    new_energy Float32,
    new_safety Float32,
    new_social Float32
)
ENGINE = MergeTree()
-- 4. Mandatory Sorting Key
ORDER BY (exp_id, agent_id, timestamp)
-- 5. Optional: Partitioning (Good for deleting old experiments easily)
PARTITION BY exp_id 
"""

prompt_and_responses_table_query = """
CREATE TABLE IF NOT EXISTS prompt_responses (
    exp_id LowCardinality(String),
    simulation_step Int32,
    timestamp DateTime64(3),
    agent_id Int32,
    prompt String CODEC(ZSTD(3)),
    response String CODEC(ZSTD(3)),
    block_name LowCardinality(String),
    func_name LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
"""


class AdjustNeedsRecord(TypedDict):
    exp_id: Optional[str]
    timestamp: datetime
    agent_id: int
    prompt: str
    actor: str
    current_need: str
    current_hunger: float
    current_energy: float
    current_safety: float
    current_social: float
    new_hunger: float
    new_energy: float
    new_safety: float
    new_social: float


@ray.remote
class ClickHouseActor:
    """
    ClickHouseActor for storing all details about the simulation in ClickHouse database.
    """

    def __init__(
        self,
        exp_id: str,
        home_dir: str,
        host: str = "localhost",
        port: int = 8123,
        username: str = "default",
        password: str = "clickhouse",
        database: str = "fastsociety",
        batch_size: int = 128,
        batch_timeout: float = 30.0,
        auto_create_database: bool = True,
    ):
        """
        Initialize ClickHouse client and create necessary tables.

        :param exp_id: Experiment ID for the simulation.
        :param home_dir: Home directory path for storing ClickHouse data.
        :param host: ClickHouse server host.
        :param port: ClickHouse server port.
        :param username: ClickHouse username.
        :param password: ClickHouse password.
        :param database: ClickHouse database name.
        :param batch_size: Number of records to batch before inserting.
        :param batch_timeout: Time in seconds to wait before inserting batch.
        :param auto_create_database: Whether to automatically create the database if it doesn't exist.
        """
        self.exp_id = exp_id
        self.home_dir = Path(home_dir)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.auto_create_database = auto_create_database
        self.db_path = self.home_dir / "clickhouse"
        self.db_path.mkdir(parents=True, exist_ok=True)

        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        self.adjust_needs_batch: deque = deque()
        self.last_adjust_needs_flush_time = time.time()
        self.prompt_responses_batch: deque = deque()
        self.last_prompt_responses_flush_time = time.time()

        self.simulation_step = -1

        self.client: Optional[Client] = None
        self._connect()

        self._create_tables()

        get_logger().info(f"ClickHouseActor initialized with {batch_size=}")

    def _connect(self):
        """Establish connection to ClickHouse server."""
        try:
            if self.auto_create_database:
                temp_client = None
                try:
                    temp_client = clickhouse_connect.get_client(
                        host=self.host,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                    )
                    temp_client.command(
                        f"CREATE DATABASE IF NOT EXISTS {self.database}"
                    )
                    get_logger().info(
                        f"Database '{self.database}' ensured in ClickHouse server."
                    )
                except Exception as e:
                    get_logger().error(
                        f"Failed to ensure database '{self.database}': {e}"
                    )
                finally:
                    if temp_client:
                        temp_client.close()
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
            )

            get_logger().info("Connected to ClickHouse server.")
        except Exception as e:
            get_logger().error(f"Failed to connect to ClickHouse server: {e}")
            self.client = None

    def _create_tables(self):
        """Create necessary tables in ClickHouse database."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot create tables."
            )
            return

        try:
            self.client.command(create_adjust_needs_table_query)
            self.client.command(prompt_and_responses_table_query)
            get_logger().info("Tables created successfully in ClickHouse database.")
        except Exception as e:
            get_logger().error(f"Failed to create tables in ClickHouse database: {e}")

    def set_simulation_step(self, step: int):
        """Set the current simulation step."""
        self.simulation_step = step

    def _flush_adjust_needs_batch(self):
        """Flush the adjust_needs batch to ClickHouse."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot flush batch."
            )
            return

        if not self.adjust_needs_batch or len(self.adjust_needs_batch) == 0:
            return

        try:
            records = list(self.adjust_needs_batch)

            # Convert to columnar format (most efficient)
            column_data = [
                [r["exp_id"] for r in records],  # exp_id column
                [self.simulation_step for _ in records],  # simulation_step column
                [r["timestamp"] for r in records],  # timestamp column
                [r["agent_id"] for r in records],  # agent_id column
                [r["prompt"] for r in records],  # prompt column
                [r["actor"] for r in records],  # actor column
                [r["current_need"] for r in records],  # current_need column
                [r["current_hunger"] for r in records],  # current_hunger column
                [r["current_energy"] for r in records],  # current_energy column
                [r["current_safety"] for r in records],  # current_safety column
                [r["current_social"] for r in records],  # current_social column
                [r["new_hunger"] for r in records],  # new_hunger column
                [r["new_energy"] for r in records],  # new_energy column
                [r["new_safety"] for r in records],  # new_safety column
                [r["new_social"] for r in records],  # new_social column
            ]

            column_names = [
                "exp_id",
                "simulation_step",
                "timestamp",
                "agent_id",
                "prompt",
                "actor",
                "current_need",
                "current_hunger",
                "current_energy",
                "current_safety",
                "current_social",
                "new_hunger",
                "new_energy",
                "new_safety",
                "new_social",
            ]

            self.client.insert(
                "NeedsBlock_adjust_needs",
                column_data,
                column_names=column_names,
                column_oriented=True,  # This tells ClickHouse it's columnar format
            )

            self.adjust_needs_batch.clear()
            self.last_adjust_needs_flush_time = time.time()

            get_logger().info(
                f"Flushed {len(records)} adjust_needs records to ClickHouse."
            )

        except Exception as e:
            get_logger().error(f"Failed to flush adjust_needs batch to ClickHouse: {e}")

    def insert_adjust_needs_record(self, record: AdjustNeedsRecord) -> None:
        """
        Add an adjust_needs record to the batch and flush if necessary.


        :param record: AdjustNeedsRecord dictionary containing the record details.
        """
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert record."
            )
            return

        # convert timestamp to datetime
        if isinstance(record["timestamp"], int):
            timestamp = datetime.fromtimestamp(record["timestamp"] / 1000.0)
            record["timestamp"] = timestamp

        record["exp_id"] = self.exp_id

        self.adjust_needs_batch.append(record)

        if (len(self.adjust_needs_batch) >= self.batch_size) or (
            time.time() - self.last_adjust_needs_flush_time >= self.batch_timeout
        ):
            self._flush_adjust_needs_batch()

    def insert_prompt_response_record(
        self,
        timestamp: datetime,
        agent_id: int,
        prompt: str,
        response: str,
        block_name: str,
        func_name: str,
    ):
        """Insert a prompt-response record into ClickHouse."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert prompt-response record."
            )
            return

        try:

            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp)
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()

            if not isinstance(agent_id, int):
              try:
                  agent_id = int(agent_id)
              except (ValueError, TypeError):
                  # If conversion fails, use -1 as a sentinel value
                  agent_id = -1

            # Convert response to string if it's not already
            if not isinstance(response, str):
                # Handle ChatCompletion objects
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    response = response.choices[0].message.content or ""
                else:
                    response = str(response)
            
            # Convert prompt to string if it's not already
            if not isinstance(prompt, str):
                prompt = str(prompt)

            self.prompt_responses_batch.append(
                {
                    "exp_id": self.exp_id,
                    "simulation_step": self.simulation_step,
                    "timestamp": timestamp,
                    "agent_id": agent_id,
                    "prompt": prompt,
                    "response": response,
                    "block_name": block_name,
                    "func_name": func_name,
                }
            )

            if (len(self.prompt_responses_batch) >= self.batch_size) or (
                time.time() - self.last_prompt_responses_flush_time
                >= self.batch_timeout
            ):
                self._flush_prompt_responses_batch()

        except Exception as e:
            get_logger().error(f"Failed to insert prompt-response record: {e}")

    def _flush_prompt_responses_batch(self):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot flush batch."
            )
            return

        if not self.prompt_responses_batch or len(self.prompt_responses_batch) == 0:
            return

        records = list(self.prompt_responses_batch)

        get_logger().debug(
            f"Flushing {len(records)} prompt-response records to ClickHouse."
        )

        # Convert to columnar format
        column_data = [
            [r["exp_id"] for r in records],
            [r["simulation_step"] for r in records],
            [r["timestamp"] for r in records],
            [r["agent_id"] for r in records],
            [r["prompt"] for r in records],
            [r["response"] for r in records],
            [r["block_name"] for r in records],
            [r["func_name"] for r in records],
        ]

        column_names = [
            "exp_id",
            "simulation_step",
            "timestamp",
            "agent_id",
            "prompt",
            "response",
            "block_name",
            "func_name",
        ]

        self.client.insert(
            "prompt_responses",
            column_data,
            column_names=column_names,
            column_oriented=True,
        )

        self.prompt_responses_batch.clear()
        self.last_prompt_responses_flush_time = time.time()

    def flush_all_batches(self):
        """Flush all batches to ClickHouse."""
        self._flush_adjust_needs_batch()
        self._flush_prompt_responses_batch()

    def close(self):
        """Close ClickHouse client connection."""
        if self.client:
            self.flush_all_batches()
            self.client.close()
            get_logger().info("ClickHouse client connection closed.")
