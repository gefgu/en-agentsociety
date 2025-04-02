from typing import Union, cast
from .bankagent import BankAgent
from .firmagent import FirmAgent
from .governmentagent import GovernmentAgent
from .memory_config import (
    memory_config_bank,
    memory_config_firm,
    memory_config_government,
    memory_config_nbs,
    memory_config_societyagent,
    DEFAULT_DISTRIBUTIONS,
)
from ..agent.distribution import Distribution, DistributionConfig
from ..configs import (
    Config,
    AgentClassType,
    MessageInterceptConfig,
    AgentConfig,
)
from .message_intercept import (
    EdgeMessageBlock,
    DoNothingListener,
    PointMessageBlock,
)
from .initial import bind_agent_info, initialize_social_network
from .nbsagent import NBSAgent
from .societyagent import SocietyAgent

__all__ = [
    "default",
    "SocietyAgent",
    "FirmAgent",
    "BankAgent",
    "NBSAgent",
    "GovernmentAgent",
    "memory_config_societyagent",
    "memory_config_government",
    "memory_config_firm",
    "memory_config_bank",
    "memory_config_nbs",
]


def _fill_in_agent_class_and_memory_config(self: AgentConfig):
    if isinstance(self.agent_class, str):
        if self.agent_class == AgentClassType.CITIZEN:
            self.agent_class = SocietyAgent
            if self.memory_config_func is None:
                self.memory_config_func = memory_config_societyagent
            distributions = cast(
                dict[str, Union[Distribution, DistributionConfig]],
                DEFAULT_DISTRIBUTIONS,
            )
            if self.memory_distributions is not None:
                distributions.update(self.memory_distributions)
            self.memory_distributions = distributions
        elif self.agent_class == AgentClassType.FIRM:
            self.agent_class = FirmAgent
            if self.memory_config_func is None:
                self.memory_config_func = memory_config_firm
        elif self.agent_class == AgentClassType.GOVERNMENT:
            self.agent_class = GovernmentAgent
            if self.memory_config_func is None:
                self.memory_config_func = memory_config_government
        elif self.agent_class == AgentClassType.BANK:
            self.agent_class = BankAgent
            if self.memory_config_func is None:
                self.memory_config_func = memory_config_bank
        elif self.agent_class == AgentClassType.NBS:
            self.agent_class = NBSAgent
            if self.memory_config_func is None:
                self.memory_config_func = memory_config_nbs
        else:
            raise ValueError(f"Invalid agent class: {self.agent_class}")
    return self


def _fill_in_message_intercept_config(
    self: MessageInterceptConfig,
) -> MessageInterceptConfig:
    if self.mode is None and len(self.blocks) == 0:
        raise ValueError("Either set blocks or mode")
    if self.mode is not None and len(self.blocks) > 0:
        raise ValueError("Either set blocks or mode, not both")
    if self.mode is not None:
        if self.mode == "point":
            self.blocks = [
                PointMessageBlock(
                    name="default_point_message_block",
                    max_violation_time=self.max_violation_time,
                )
            ]
        else:
            self.blocks = [
                EdgeMessageBlock(
                    name="default_edge_message_block",
                    max_violation_time=self.max_violation_time,
                )
            ]
    if len(self.blocks) > 0 and self.listener is None:
        self.listener = DoNothingListener
    return self


def default(config: Config) -> Config:
    """
    Use the default values in cityagent to fill in the config.
    """
    # =====================
    # agent config
    # =====================
    config.agents.citizens = [
        _fill_in_agent_class_and_memory_config(agent_config)
        for agent_config in config.agents.citizens
    ]
    config.agents.firms = [
        _fill_in_agent_class_and_memory_config(agent_config)
        for agent_config in config.agents.firms
    ]
    config.agents.governments = [
        _fill_in_agent_class_and_memory_config(agent_config)
        for agent_config in config.agents.governments
    ]
    config.agents.banks = [
        _fill_in_agent_class_and_memory_config(agent_config)
        for agent_config in config.agents.banks
    ]
    config.agents.nbs = [
        _fill_in_agent_class_and_memory_config(agent_config)
        for agent_config in config.agents.nbs
    ]
    # =====================
    # exp config
    # =====================
    if config.exp.message_intercept is not None:
        config.exp.message_intercept = _fill_in_message_intercept_config(
            config.exp.message_intercept
        )
    # =====================
    # init functions
    # =====================
    if len(config.agents.init_funcs) == 0:
        config.agents.init_funcs = [
            bind_agent_info,
            initialize_social_network,
        ]
    return config
