from pathlib import Path
from typing import List, Optional

import fastavro
from pydantic import BaseModel, Field, model_validator

from ..logger import get_logger
from .type import (
    StorageDialog,
    StorageGlobalPrompt,
    StorageProfile,
    StorageStatus,
    StorageSurvey,
)

__all__ = ["AvroSaver", "AvroConfig"]

PROFILE_SCHEMA = {
    "doc": "Agent属性",
    "name": "AgentProfile",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "profile", "type": "string"},
    ],
}

DIALOG_SCHEMA = {
    "doc": "Agent对话",
    "name": "AgentDialog",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "type", "type": "int"},
        {"name": "speaker", "type": "string"},
        {"name": "content", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        },
    ],
}

GLOBAL_PROMPT_SCHEMA = {
    "doc": "全局Prompt",
    "name": "GlobalPrompt",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "prompt", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        },
    ],
}

STATUS_SCHEMA = {
    "doc": "Agent状态",
    "name": "AgentStatus",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "lng", "type": ["null", "double"]},
        {"name": "lat", "type": ["null", "double"]},
        {"name": "parent_id", "type": ["null", "int"]},
        {"name": "friend_ids", "type": {"type": "array", "items": "int"}},
        {"name": "action", "type": "string"},
        {"name": "status", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        },
    ],
}

SURVEY_SCHEMA = {
    "doc": "Agent问卷",
    "name": "AgentSurvey",
    "namespace": "com.agentsociety",
    "type": "record",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "day", "type": "int"},
        {"name": "t", "type": "float"},
        {"name": "survey_id", "type": "string"},
        {"name": "result", "type": "string"},
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
        },
    ],
}

SCHEMA_MAP = {
    "profile": PROFILE_SCHEMA,
    "dialog": DIALOG_SCHEMA,
    "status": STATUS_SCHEMA,
    "survey": SURVEY_SCHEMA,
    "global_prompt": GLOBAL_PROMPT_SCHEMA,
}


class AvroConfig(BaseModel):
    """Avro configuration class."""

    enabled: bool = Field(False)
    """Whether Avro storage is enabled"""

    path: str = Field(...)
    """Avro file storage path"""

    @model_validator(mode="after")
    def validate_path(self):
        if not self.enabled:
            return self
        # check path is valid and is a directory
        path = Path(self.path)
        if path.exists() and not path.is_dir():
            raise ValueError(f"Path {self.path} is not a directory")
        return self


class AvroSaver:
    """Save data to avro file as local storage saving and logging"""

    def __init__(self, config: AvroConfig, exp_id: str, group_id: Optional[str]):
        """
        Initialize the AvroSaver.

        - **Args**:
            - `config` (AvroConfig): The configuration for the AvroSaver.
            - `exp_id` (str): The ID of the experiment.
            - `group_id` (Optional[str]): The ID of the group.
        """
        self._config = config
        self._exp_id = exp_id
        self._group_id = group_id
        if not self.enabled:
            get_logger().warning("AvroSaver is not enabled")
            return
        self._avro_path = Path(self._config.path) / f"{self._exp_id}"
        self._avro_path.mkdir(parents=True, exist_ok=True)
        if self._group_id is not None:
            self._avro_path = self._avro_path / f"{self._group_id}"
            self._avro_path.mkdir(parents=True, exist_ok=True)
            get_logger().info(f"AvroSaver initialized with path: {self._avro_path}")
            self._avro_file = {
                "profile": self._avro_path / f"profile.avro",
                "dialog": self._avro_path / f"dialog.avro",
                "status": self._avro_path / f"status.avro",
                "survey": self._avro_path / f"survey.avro",
            }
            # initialize avro files
            for key, file in self._avro_file.items():
                if not file.exists():
                    with open(file, "wb") as f:
                        schema = SCHEMA_MAP[key]
                        fastavro.writer(f, schema, [], codec="snappy")
        else:
            self._avro_file = {
                "global_prompt": self._avro_path / f"global_prompt.avro",
            }
            # initialize avro files
            for key, file in self._avro_file.items():
                if not file.exists():
                    with open(file, "wb") as f:
                        schema = SCHEMA_MAP[key]
                        fastavro.writer(f, schema, [], codec="snappy")

    @property
    def enabled(self):
        return self._config.enabled

    @property
    def exp_info_file(self):
        return self._avro_path / f"experiment_info.yaml"

    def close(self): ...

    def _check(self, is_group: bool = True):
        if not self.enabled:
            raise RuntimeError("AvroSaver is not enabled")
        if self._group_id is None and is_group:
            raise RuntimeError("AvroSaver is not initialized")

    def append_surveys(self, surveys: List[StorageSurvey]):
        """
        Append a survey to the avro file.

        - **Args**:
            - `surveys` (List[AvroSurvey]): The surveys to append.
        """
        self._check()
        with open(self._avro_file["survey"], "a+b") as f:
            fastavro.writer(
                f,
                SURVEY_SCHEMA,
                [survey.model_dump() for survey in surveys],
                codec="snappy",
            )

    def append_dialogs(self, dialogs: List[StorageDialog]):
        """
        Append a dialog to the avro file.

        - **Args**:
            - `dialogs` (List[AvroDialog]): The dialogs to append.
        """
        self._check()
        with open(self._avro_file["dialog"], "a+b") as f:
            fastavro.writer(
                f,
                DIALOG_SCHEMA,
                [dialog.model_dump() for dialog in dialogs],
                codec="snappy",
            )

    def append_profiles(self, profiles: List[StorageProfile]):
        """
        Append a profile to the avro file.

        - **Args**:
            - `profiles` (List[StorageProfile]): The profiles to append.
        """
        self._check()
        with open(self._avro_file["profile"], "a+b") as f:
            fastavro.writer(
                f,
                PROFILE_SCHEMA,
                [profile.model_dump() for profile in profiles],
                codec="snappy",
            )

    def append_statuses(self, statuses: List[StorageStatus]):
        """
        Append a status to the avro file.

        - **Args**:
            - `statuses` (List[StorageStatus]): The statuses to append.
        """
        self._check()
        with open(self._avro_file["status"], "a+b") as f:
            fastavro.writer(
                f,
                STATUS_SCHEMA,
                [status.model_dump() for status in statuses],
                codec="snappy",
            )

    def append_global_prompt(self, global_prompt: StorageGlobalPrompt):
        """
        Append a global prompt to the avro file.

        - **Args**:
            - `global_prompt` (List[StorageGlobalPrompt]): The global prompt to append.
        """
        self._check(is_group=False)
        with open(self._avro_file["global_prompt"], "a+b") as f:
            fastavro.writer(
                f,
                GLOBAL_PROMPT_SCHEMA,
                [global_prompt.model_dump()],
                codec="snappy",
            )
