from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
import clickhouse_connect
from clickhouse_connect.driver.client import Client
from pathlib import Path

from .prometheusActor import PrometheusActor
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

user_location_type_table_query = """
CREATE TABLE IF NOT EXISTS agent_location_type (
  exp_id LowCardinality(String),
  simulation_step Int32,
  timestamp DateTime64(3),
  agent_id Int32,
  location_type LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
"""

step_agent_status_table_query = """
CREATE TABLE IF NOT EXISTS step_agent_status (
  exp_id LowCardinality(String),
  agent_id Int32,
  simulation_step Int32,
  timestamp DateTime64(3),
  lat Float32,
  lng Float32,
  parent_id Int32,
  action LowCardinality(String),
  status String CODEC(ZSTD(3))
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
"""

block_dispatcher_table_query = """
CREATE TABLE IF NOT EXISTS block_dispatcher (
    exp_id LowCardinality(String),
    simulation_step Int32,
    timestamp DateTime64(3),
    agent_id Int32,

    target_block LowCardinality(String),
    reason String CODEC(ZSTD(3)),

    possible_blocks Array(LowCardinality(String)),

    ctx_time String CODEC(ZSTD(3)),
    ctx_need String CODEC(ZSTD(3)),
    ctx_intention String CODEC(ZSTD(3)),
    ctx_emotion String CODEC(ZSTD(3)),
    ctx_thought String CODEC(ZSTD(3)),
    ctx_location String CODEC(ZSTD(3)),
    ctx_area_info String CODEC(ZSTD(3)),
    ctx_weather String CODEC(ZSTD(3)),
    ctx_temperature Int32,
    ctx_other_info String CODEC(ZSTD(3)),
    ctx_plan_target String CODEC(ZSTD(3))
)
ENGINE = MergeTree()
ORDER BY (exp_id, agent_id, timestamp)
PARTITION BY exp_id
"""

user_transport_type_table_query = """
CREATE TABLE IF NOT EXISTS agent_transport_type (
  exp_id LowCardinality(String),
  simulation_step Int32,
  timestamp DateTime64(3),
  agent_id Int32,
  transport_type LowCardinality(String)
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
        metrics_actor: Optional[ray.actor.ActorHandle[PrometheusActor]] = None,
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
        self._metrics_actor = metrics_actor

        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        self.adjust_needs_batch: deque = deque()
        self.last_adjust_needs_flush_time = time.time()
        self.prompt_responses_batch: deque = deque()
        self.last_prompt_responses_flush_time = time.time()
        self.location_type_batch: deque = deque()
        self.last_location_type_flush_time = time.time()
        self.step_agent_status_batch: deque = deque()
        self.last_step_agent_status_flush_time = time.time()
        self.block_dispatcher_batch: deque = deque()
        self.last_block_dispatcher_flush_time = time.time()
        self.transport_type_batch: deque = deque()
        self.last_transport_type_flush_time = time.time()

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
            self.client.command(user_location_type_table_query)
            self.client.command(user_transport_type_table_query)
            self.client.command(step_agent_status_table_query)
            self.client.command(block_dispatcher_table_query)
            get_logger().info("Tables created successfully in ClickHouse database.")
        except Exception as e:
            get_logger().error(f"Failed to create tables in ClickHouse database: {e}")

    def set_simulation_step(self, step: int):
        """Set the current simulation step."""
        self.simulation_step = step

    def _clean_incoming_record(self, timestamp: Any, agent_id: Any):
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

        return timestamp, agent_id

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

            self._metrics_actor.record_table_records.remote(
                "NeedsBlock_adjust_needs", len(records)
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
            timestamp = datetime.fromtimestamp(record["timestamp"])
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

            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            # Convert response to string if it's not already
            if not isinstance(response, str):
                # Handle ChatCompletion objects
                if hasattr(response, "choices") and len(response.choices) > 0:
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

        self._metrics_actor.record_table_records.remote(
            "prompt_responses", len(records)
        )

        self.prompt_responses_batch.clear()
        self.last_prompt_responses_flush_time = time.time()

    def insert_user_location_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        location_type: str,
    ):
        """Insert an agent location type record into ClickHouse."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert agent location type record."
            )
            return

        try:

            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            self.location_type_batch.append(
                {
                    "exp_id": self.exp_id,
                    "simulation_step": self.simulation_step,
                    "timestamp": timestamp,
                    "agent_id": agent_id,
                    "location_type": location_type,
                }
            )

            if (len(self.location_type_batch) >= self.batch_size) or (
                time.time() - self.last_location_type_flush_time >= self.batch_timeout
            ):
                self._flush_user_location_type_batch()

        except Exception as e:
            get_logger().error(f"Failed to insert agent location type record: {e}")

    def _flush_user_location_type_batch(self):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot flush batch."
            )
            return

        if not self.location_type_batch or len(self.location_type_batch) == 0:
            return

        records = list(self.location_type_batch)

        # Convert to columnar format
        column_data = [
            [r["exp_id"] for r in records],
            [r["simulation_step"] for r in records],
            [r["timestamp"] for r in records],
            [r["agent_id"] for r in records],
            [r["location_type"] for r in records],
        ]

        column_names = [
            "exp_id",
            "simulation_step",
            "timestamp",
            "agent_id",
            "location_type",
        ]

        self.client.insert(
            "agent_location_type",
            column_data,
            column_names=column_names,
            column_oriented=True,
        )

        self._metrics_actor.record_table_records.remote(
            "agent_location_type", len(records)
        )

        self.location_type_batch.clear()
        self.last_location_type_flush_time = time.time()

    def insert_user_transport_type_record(
        self,
        timestamp: datetime,
        agent_id: int,
        transport_type: str,
    ):
        """Insert an agent transport type record into ClickHouse."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert agent transport type record."
            )
            return

        try:

            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            self.transport_type_batch.append(
                {
                    "exp_id": self.exp_id,
                    "simulation_step": self.simulation_step,
                    "timestamp": timestamp,
                    "agent_id": agent_id,
                    "transport_type": transport_type,
                }
            )

            if (len(self.transport_type_batch) >= self.batch_size) or (
                time.time() - self.last_transport_type_flush_time >= self.batch_timeout
            ):
                self._flush_user_transport_type_batch()

        except Exception as e:
            get_logger().error(f"Failed to insert agent transport type record: {e}")

    def _flush_user_transport_type_batch(self):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot flush batch."
            )
            return

        if not self.transport_type_batch or len(self.transport_type_batch) == 0:
            return

        records = list(self.transport_type_batch)

        # Convert to columnar format
        column_data = [
            [r["exp_id"] for r in records],
            [r["simulation_step"] for r in records],
            [r["timestamp"] for r in records],
            [r["agent_id"] for r in records],
            [r["transport_type"] for r in records],
        ]

        column_names = [
            "exp_id",
            "simulation_step",
            "timestamp",
            "agent_id",
            "transport_type",
        ]

        self.client.insert(
            "agent_transport_type",
            column_data,
            column_names=column_names,
            column_oriented=True,
        )

        self._metrics_actor.record_table_records.remote(
            "agent_transport_type", len(records)
        )

        self.transport_type_batch.clear()
        self.last_transport_type_flush_time = time.time()


    def insert_step_agent_status_record(
        self,
        agent_id: int,
        timestamp: datetime,
        lat: float,
        lng: float,
        parent_id: int,
        action: str,
        status: str,
    ):
        """Insert a step agent status record into ClickHouse."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert step agent status record."
            )
            return

        try:
            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            self.step_agent_status_batch.append(
                {
                    "exp_id": self.exp_id,
                    "agent_id": agent_id,
                    "simulation_step": self.simulation_step,
                    "timestamp": timestamp,
                    "lat": lat,
                    "lng": lng,
                    "parent_id": parent_id,
                    "action": action,
                    "status": status,
                }
            )

            if (len(self.step_agent_status_batch) >= self.batch_size) or (
                time.time() - self.last_step_agent_status_flush_time >= self.batch_timeout
            ):
                self._flush_step_agent_status_batch()

        except Exception as e:
            get_logger().error(f"Failed to insert step agent status record: {e}")


    def _flush_step_agent_status_batch(self):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot flush batch."
            )
            return

        if not self.step_agent_status_batch or len(self.step_agent_status_batch) == 0:
            return

        records = list(self.step_agent_status_batch)

        # Convert to columnar format
        column_data = [
            [r["exp_id"] for r in records],
            [r["agent_id"] for r in records],
            [r["simulation_step"] for r in records],
            [r["timestamp"] for r in records],
            [r["lat"] for r in records],
            [r["lng"] for r in records],
            [r["parent_id"] for r in records],
            [r["action"] for r in records],
            [r["status"] for r in records],
        ]

        column_names = [
            "exp_id",
            "agent_id",
            "simulation_step",
            "timestamp",
            "lat",
            "lng",
            "parent_id",
            "action",
            "status",
        ]

        self.client.insert(
            "step_agent_status",
            column_data,
            column_names=column_names,
            column_oriented=True,
        )

        self._metrics_actor.record_table_records.remote(
            "step_agent_status", len(records)
        )

        self.step_agent_status_batch.clear()
        self.last_step_agent_status_flush_time = time.time()


    def insert_block_dispatcher_record(
        self,
        agent_id: int,
        timestamp: datetime,
        target_block: str,
        reason: str,
        possible_blocks: List[str],
        ctx_time: str,
        ctx_need: str,
        ctx_intention: str,
        ctx_emotion: str,
        ctx_thought: str,
        ctx_location: str,
        ctx_area_info: str,
        ctx_weather: str,
        ctx_temperature: int,
        ctx_other_info: str,
        ctx_plan_target: str,
    ):
        """Insert a block dispatcher batch record into ClickHouse."""
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot insert block dispatcher record."
            )
            return

        try:
            timestamp, agent_id = self._clean_incoming_record(timestamp, agent_id)

            record = {
                    "exp_id": self.exp_id,
                    "agent_id": agent_id,
                    "simulation_step": self.simulation_step,
                    "timestamp": timestamp,
                    "target_block": target_block,
                    "reason": reason,
                    "possible_blocks": possible_blocks,
                    "ctx_time": ctx_time,
                    "ctx_need": ctx_need,
                    "ctx_intention": ctx_intention,
                    "ctx_emotion": ctx_emotion,
                    "ctx_thought": ctx_thought,
                    "ctx_location": ctx_location,
                    "ctx_area_info": ctx_area_info,
                    "ctx_weather": ctx_weather,
                    "ctx_temperature": ctx_temperature,
                    "ctx_other_info": ctx_other_info,
                    "ctx_plan_target": ctx_plan_target,
                }

            self.block_dispatcher_batch.append(
                record
            )

            if (len(self.block_dispatcher_batch) >= self.batch_size) or (
                time.time() - self.last_block_dispatcher_flush_time >= self.batch_timeout
            ):
                self._flush_block_dispatcher_batch()

        except Exception as e:
            get_logger().error(f"Failed to insert block dispatcher record: {e}. Record: {record}")


    def _flush_block_dispatcher_batch(self):
        if self.client is None:
            get_logger().error(
                "ClickHouse client is not connected. Cannot flush batch."
            )
            return

        if not self.block_dispatcher_batch or len(self.block_dispatcher_batch) == 0:
            return

        records = list(self.block_dispatcher_batch)

        # Convert to columnar format
        column_data = [
            [r["exp_id"] for r in records],
            [r["agent_id"] for r in records],
            [r["simulation_step"] for r in records],
            [r["timestamp"] for r in records],
            [r["target_block"] for r in records],
            [r["reason"] for r in records],
            [r["possible_blocks"] for r in records],
            [r["ctx_time"] for r in records],
            [r["ctx_need"] for r in records],
            [r["ctx_intention"] for r in records],
            [r["ctx_emotion"] for r in records],
            [r["ctx_thought"] for r in records],
            [r["ctx_location"] for r in records],
            [r["ctx_area_info"] for r in records],
            [r["ctx_weather"] for r in records],
            [r["ctx_temperature"] for r in records],
            [r["ctx_other_info"] for r in records],
            [r["ctx_plan_target"] for r in records],
        ]

        column_names = [
            "exp_id",
            "agent_id",
            "simulation_step",
            "timestamp",
            "target_block",
            "reason",
            "possible_blocks",
            "ctx_time",
            "ctx_need",
            "ctx_intention",
            "ctx_emotion",
            "ctx_thought",
            "ctx_location",
            "ctx_area_info",
            "ctx_weather",
            "ctx_temperature",
            "ctx_other_info",
            "ctx_plan_target",
        ]

        self.client.insert(
            "block_dispatcher",
            column_data,
            column_names=column_names,
            column_oriented=True,
        )

        self._metrics_actor.record_table_records.remote(
            "block_dispatcher", len(records)
        )

        self.block_dispatcher_batch.clear()
        self.last_block_dispatcher_flush_time = time.time()


    def flush_all_batches(self):
        """Flush all batches to ClickHouse."""
        self._flush_adjust_needs_batch()
        self._flush_prompt_responses_batch()
        self._flush_user_location_type_batch()
        self._flush_step_agent_status_batch()
        self._flush_block_dispatcher_batch()
        self._flush_user_transport_type_batch()

    def close(self):
        """Close ClickHouse client connection."""
        if self.client:
            self.flush_all_batches()
            self.client.close()
            get_logger().info("ClickHouse client connection closed.")
