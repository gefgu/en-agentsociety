# Message Interception

The message interception system provides control over agent communications in the simulation environment. This feature allows you to monitor, filter, and regulate messages exchanged between agents based on customizable rules.

## Overview

The message interception system consists of two main components:

1. **Message Interceptor**: The core component that handles message validation and forwarding, the supervisor is within the interceptor.
2. **Supervisor**: A specialized agent that implements message validation logic in its `forward` method.

## Message Interceptor

The `MessageInterceptor` class is responsible for intercepting and processing messages based on configured rules. It works in conjunction with a Supervisor to validate messages and handle interventions.

### Message Processing Flow

If the supervisor is enabled, the message interceptor will process the messages through the supervisor with the following flow:

1. AGENT_CHAT messages are collected from all agent groups in the simulation
   - Other message kinds are forwarded without validation.
2. The interceptor processes these messages through its supervisor
3. For each message:
   - The supervisor will validate the message and set a boolean value indicating whether the message is valid or not and put it in the `validation_dict` with the message as the key, the value is the boolean value.
   - If the message is valid, the message will be sent to the sender, as it is not modified.
   - If the message is invalid, it will not be sent to the sender, and a failed-to-send message will be returned to the sender.
   - Persuasion messages are extra messages that the supervisor wants to send to agents to persuade them, or just tell them something.

## Supervisor

The `SupervisorBase` class is a specialized agent that implements message validation and intervention logic. To create a custom supervisor, inherit from `SupervisorBase` and implement the `forward` method.

### Example of a Custom Supervisor

```python
from typing import Any, Optional

from agentsociety.agent import (AgentToolbox, Block, StatusAttribute,
                                SupervisorBase)
from agentsociety.memory import Memory
from agentsociety.message import Message

import random

class CustomSupervisor(SupervisorBase):
    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
        agent_params: Optional[Any] = None,
        blocks: Optional[list[Block]] = None,
    ):
        super().__init__(id, name, toolbox, memory, agent_params, blocks)
 
    async def forward(
        self,
        current_round_messages: list[Message],
    ) -> tuple[dict[Message, bool], list[Message]]:
        """
        Process and validate messages from the current round
        
        Args:
            current_round_messages: List of messages for the current round
            
        Returns:
            validation_dict: Dictionary mapping messages to their validation status
            persuasion_messages: List of intervention messages
        """
        validation_dict = {}
        persuasion_messages = []
        
        # Implement your validation logic here
        for message in current_round_messages:
            # Example validation logic
            is_valid = random.random() < 0.5  # Replace with actual validation
            validation_dict[message] = is_valid
                
        return validation_dict, persuasion_messages
```

This example is a simple supervisor that validates messages randomly, and no persuasion messages are sent.

## Usage Example

Here's how to configure message interception in your experiment, simply add the supervisor to the agents config:

```python
from agentsociety.config import Config

# Configure in experiment
config = Config(
    ...
        agents=AgentsConfig(
            ...
            supervisor=AgentConfig(
                agent_class=CustomSupervisor, # This is the supervisor class, inherit from SupervisorBase and implement the forward method
            ),
        ),
)
```
