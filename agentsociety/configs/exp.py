from __future__ import annotations

import uuid
from collections.abc import Callable
from enum import Enum
from typing import Any, List, Literal, Optional, Union

import networkx as nx
from pydantic import (BaseModel, ConfigDict, Field, field_serializer,
                      model_validator)

from ..environment import EnvironmentConfig
from ..message.message_interceptor import (MessageBlockBase,
                                           MessageBlockListenerBase)
from ..survey import Survey

__all__ = [
    "WorkflowStepConfig",
    "MetricExtractorConfig",
    "EnvironmentConfig",
    "MessageInterceptConfig",
    "ExpConfig",
    "WorkflowType",
    "MetricType",
]


class WorkflowType(str, Enum):
    """
    Defines the types of workflow steps in the simulation.
    - **Description**:
        - Enumerates different types of workflow steps that can be executed during simulation.

    - **Types**:
        - `STEP`: Execute on a step-by-step unit.
        - `RUN`: Execute on a daily unit (day-based execution).
        - `INTERVIEW`: Sends an interview message to the specified agent.
        - `SURVEY`: Sends a questionnaire to the specified agent.
        - `ENVIRONMENT_INTERVENE`: Changes the environment variables (global prompt).
        - `UPDATE_STATE_INTERVENE`: Directly updates the state information of the specified agent.
        - `MESSAGE_INTERVENE`: Influences the agent's behavior and state by sending a message.
        - `NEXT_ROUND`: Proceed to the next round of the simulation —— reset agents but keep the memory.
        - `INTERVENE`: Represents other intervention methods driven by code.
        - `FUNCTION`: Represents function-based intervention methods.
    """

    STEP = "step"
    RUN = "run"
    INTERVIEW = "interview"
    SURVEY = "survey"
    ENVIRONMENT_INTERVENE = "environment"
    UPDATE_STATE_INTERVENE = "update_state"
    MESSAGE_INTERVENE = "message"
    NEXT_ROUND = "next_round"
    INTERVENE = "other"
    FUNCTION = "function"


class WorkflowStepConfig(BaseModel):
    """Represents a step in the workflow process."""

    model_config = ConfigDict(use_enum_values=True, use_attribute_docstrings=True)

    type: WorkflowType = Field(...)
    """The type of the workflow step"""

    func: Optional[Callable] = None
    """Optional function to be executed during this step - used for [FUNCTION, INTERVENE] type"""

    days: float = 1
    """Duration (in days) for which this step lasts - used for [RUN] type"""

    steps: int = 1
    """Number of steps for which this step lasts - used for [STEP] type"""

    ticks_per_step: int = 300
    """Number of ticks per step - used for [RUN, STEP] type. For example, if it is 300, then the step will run 300 ticks in the environment."""

    target_agent: Optional[list[int]] = None
    """List specifying the agents targeted by this step - used for [INTERVIEW, SURVEY, UPDATE_STATE_INTERVENE, MESSAGE_INTERVENE] type"""

    interview_message: Optional[str] = None
    """Optional message used for interviews during this step - used for [INTERVIEW] type"""

    survey: Optional[Survey] = None
    """Optional survey instance associated with this step - used for [SURVEY] type"""

    key: Optional[str] = None
    """Optional key identifier for the step - used for [ENVIRONMENT_INTERVENE, UPDATE_STATE_INTERVENE] type"""

    value: Optional[Any] = None
    """Optional value associated with the step - used for [ENVIRONMENT_INTERVENE, UPDATE_STATE_INTERVENE] type"""

    intervene_message: Optional[str] = None
    """Optional message used for interventions - used for [MESSAGE_INTERVENE] type"""

    description: Optional[str] = None
    """A descriptive text explaining the workflow step"""

    @field_serializer("func")
    def serialize_func(self, func, info):
        if func is None:
            return None
        # Handle partial function
        if hasattr(func, "func"):
            return func.func.__name__
        return func.__name__

    @field_serializer("survey")
    def serialize_survey(self, survey: Optional[Survey], info):
        if survey is None:
            return None
        else:
            return survey.to_dict()

    @model_validator(mode="after")
    def validate_func(self):
        if self.type == WorkflowType.STEP:
            if self.steps <= 0:
                raise ValueError("steps must be greater than 0 for STEP type")
        elif self.type == WorkflowType.RUN:
            if self.days <= 0:
                raise ValueError("days must be greater than 0 for RUN type")
        elif self.type == WorkflowType.INTERVIEW:
            if self.target_agent is None or self.interview_message is None:
                raise ValueError(
                    "target_agent and interview_message are required for INTERVIEW step"
                )
        elif self.type == WorkflowType.SURVEY:
            if self.target_agent is None or self.survey is None:
                raise ValueError("target_agent and survey are required for SURVEY step")
        elif self.type == WorkflowType.ENVIRONMENT_INTERVENE:
            if self.key is None or self.value is None:
                raise ValueError(
                    "key and value are required for ENVIRONMENT_INTERVENE step"
                )
        elif self.type == WorkflowType.UPDATE_STATE_INTERVENE:
            if self.key is None or self.value is None or self.target_agent is None:
                raise ValueError(
                    "key, value and target_agent are required for UPDATE_STATE_INTERVENE step"
                )
        elif self.type == WorkflowType.MESSAGE_INTERVENE:
            if self.intervene_message is None or self.target_agent is None:
                raise ValueError(
                    "intervene_message and target_agent are required for MESSAGE_INTERVENE step"
                )
        elif self.type == WorkflowType.NEXT_ROUND:
            if self.target_agent is not None:
                raise ValueError("target_agent is not allowed for NEXT_ROUND step")
        elif self.type == WorkflowType.INTERVENE:
            if self.func is None:
                raise ValueError(
                    "target_agent and intervene_message are required for INTERVENE step"
                )
        elif self.type == WorkflowType.FUNCTION:
            if self.func is None:
                raise ValueError("func is required for FUNCTION step")
        else:
            raise ValueError(f"Unknown workflow type: {self.type} in custom validator")
        return self


class MetricType(str, Enum):
    """
    Defines the types of metric types.
    - **Description**:
        - Enumerates different types of metric types.

    - **Types**:
        - `FUNCTION`: Function-based metric.
        - `STATE`: State-based metric.
    """

    FUNCTION = "function"
    STATE = "state"


class MetricExtractorConfig(BaseModel):
    """Configuration for extracting metrics during simulation."""

    model_config = ConfigDict(use_enum_values=True, use_attribute_docstrings=True)

    type: MetricType = Field(MetricType.FUNCTION)
    """The type of metric extraction; defaults to FUNCTION"""

    func: Optional[Callable] = None
    """The function that extracts the metric - used for [FUNCTION] type"""

    step_interval: int = Field(10, ge=1)
    """Frequency interval (in simulation steps) for metric extraction"""

    target_agent: Optional[list] = None
    """List specifying the agents from which to extract metrics - used for [STATE] type"""

    key: Optional[str] = None
    """Optional key to store or identify the extracted metric - used for [STATE] type"""

    method: Optional[Literal["mean", "sum", "max", "min"]] = "sum"
    """Aggregation method applied to the metric values - used for [STATE] type"""

    extract_time: int = 0
    """The simulation time or step at which extraction occurs"""

    description: str = "None"
    """A descriptive text explaining the metric extractor"""

    # customize validator for target_agent and key
    @model_validator(mode="after")
    def validate_target_agent(self):
        if self.type == MetricType.STATE:
            if self.target_agent is None:
                raise ValueError("target_agent is required for STATE type")
            if self.key is None:
                raise ValueError("key is required for STATE type")
        return self

    @field_serializer("func")
    def serialize_func(self, func, info):
        if func is None:
            return None
        # Handle partial function
        if hasattr(func, "func"):
            return func.func.__name__
        return func.__name__


class MessageInterceptConfig(BaseModel):
    """Configuration for message interception in the simulation."""

    model_config = ConfigDict(
        use_enum_values=True,
        use_attribute_docstrings=True,
        arbitrary_types_allowed=True,
    )

    mode: Optional[Union[Literal["point"], Literal["edge"]]] = None
    """Mode of message interception, either set this or blocks"""

    max_violation_time: int = 3
    """Maximum number of allowed violations"""

    blocks: list[MessageBlockBase] = Field([])
    """List of message blocks, either set this or mode"""

    listener: Optional[type[MessageBlockListenerBase]] = None
    """Listener for message interception"""
    
    public_network: Optional[nx.Graph] = None
    """Public network for message interception"""

    private_network: Optional[nx.Graph] = None
    """Private network for message interception"""
    
    forward_strategy: Literal["outer_control", "inner_control"] = "inner_control"
    """Forward strategy for message interception"""

    # When serialize to json, change blocks and listener to their class name

    @field_serializer("blocks")
    def serialize_blocks(self, blocks, info):
        return [block.__class__.__name__ for block in blocks]

    @field_serializer("listener")
    def serialize_listener(self, listener, info):
        return listener.__class__.__name__ if listener else None


class ExpConfig(BaseModel):
    """Main configuration for the experiment."""

    model_config = ConfigDict(use_enum_values=True, use_attribute_docstrings=True)

    name: str = Field("default_experiment")
    """Name of the experiment"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    """Unique identifier for the experiment"""

    workflow: List[WorkflowStepConfig] = Field(..., min_length=1)
    """List of workflow steps"""

    environment: EnvironmentConfig
    """Environment configuration"""

    message_intercept: Optional[MessageInterceptConfig] = None
    """Message interception configuration"""

    metric_extractors: Optional[list[MetricExtractorConfig]] = None
    """List of metric extractors"""

    @field_serializer("id")
    def serialize_id(self, id, info):
        return str(id)
