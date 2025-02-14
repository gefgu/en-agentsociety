# Polarization

We simulate agent discussions on immigration policy to investigate polarization, comparing a control group (no intervention) with two treatments—exposure to aligned messages (echo chambers) and opposing messages (backfiring effects)—to analyze their impact on deepening opinion divisions.

Codes are available at [Polarization](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/polarization).

## Run the Codes

```bash
cd examples/polarization
# control group
python control.py
# echo chambers
python echo_chamber.py
# backfiring effects
python back_firing.py
```

## Step-by-Step Code Explanation

## `control.py`

The control group. No intervention is applied.

### Tool Functions

```python
import asyncio
import json
import logging
import os
import random

import ray

from agentsociety import AgentSimulation
from agentsociety.cityagent.societyagent import SocietyAgent
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=True)

async def update_attitude(simulation: AgentSimulation):
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    for agent in citizen_uuids:
        if random.random() < 0.5:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 3}
            )
        else:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 7}
            )
    attitudes = await simulation.gather("attitude", citizen_uuids)
    with open(f"exp1/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)


async def gather_attitude(simulation: AgentSimulation):
    print("gather attitude")
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    attitudes = await simulation.gather("attitude", citizen_uuids)

    with open(f"exp1/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    chat_histories = await simulation.gather("chat_histories", citizen_uuids)
    with open(f"exp1/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)
```
- `update_attitude`: Randomly initialize the attitudes towards gun control of each `SocietyAgent`(predefined citizen agent within our framework).
- `gather_attitude`: Gather the attitudes towards gun control of each `SocietyAgent` at current simulation time step.

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
)
exp_config = (
    ExpConfig(exp_name="cognition_exp1", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(number_of_citizen=100, group_size=50)
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_attitude,
                description="update attitude",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_attitude,
                description="gather attitude",
            ),
        ]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_attitude` to initialize the attitudes towards gun control of all agents.
- Step2: simulate for 3 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_attitude` to gather the attitudes of all agents after 3 simulation days.

### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"exp1/llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"exp1/mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"exp1/simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"exp1/agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    os.makedirs("exp1", exist_ok=True)
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.
- `llm_log_lists`: Log list of LLM request. Each log is a `dict` with the keys below.
  - `request_time`: The time starting LLM request in seconds.
  - `consumption`: Request time consumption in seconds.
  - `input_tokens`: Input prompt tokens.
  - `output_tokens`: Output tokens from LLM APIs.
- `mqtt_log_lists`: Log list of message sending with MQTT. Each log is a `dict` with the keys below.
  - `topic`: Topic to which the message should be published.
  - `payload`: Payload of the message to send.
  - `from_uuid`: UUID of the sender.
  - `to_uuid`: UUID of the recipient.
  - `start_time`: The time starting sending a message in seconds.
  - `consumption`: Sending time consumption in seconds.
- `simulator_log_lists`: Log list of urban simulator request. Each log is a `dict` with the keys below.
  - `start_time`: The time starting API calling in seconds.
  - `consumption`: API calling time consumption in seconds.
  - `req`: The name of the calling API.
- `agent_time_log_lists`: Log list of the agents. Each log is the `agent.forward` returned value. In this experiment, the returned value is the agent reasoning time in seconds.

## Extra Agent Classes

`AgreeAgent` will always agree with the topic (gun control in our experiment) and trying to persuade their freinds to support the topic.

```python
class AgreeAgent(CitizenAgent):
    def __init__(
        self,
        name: str,
        llm_client: Optional[LLM] = None,
        simulator: Optional[Simulator] = None,
        memory: Optional[Memory] = None,
        economy_client: Optional[EconomyClient] = None,
        messager: Optional[Messager] = None,
        avro_file: Optional[dict] = None,
    ) -> None:
        super().__init__(
            name=name,
            llm_client=llm_client,
            simulator=simulator,
            memory=memory,
            economy_client=economy_client,
            messager=messager,
            avro_file=avro_file,
        )
        self.response_prompt = FormatPrompt(AGREE_RESPONSE_PROMPT)
        self.last_time_trigger = None
        self.time_diff = 8 * 60 * 60

    async def trigger(self):
        now_time = await self.simulator.get_time()
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_time
            return True
        return False

    async def forward(self):
        if await self.trigger():
            print("AgreeAgent forward")
            friends = await self.memory.status.get("friends")
            # generate message
            message = await self.llm.atext_request(
                dialog=[{"role": "user", "content": AGREE_PROMPT}]
            )
            send_tasks = []
            for friend in friends:
                serialized_message = json.dumps(
                    {
                        "content": message,
                        "propagation_count": 1,
                    },
                    ensure_ascii=False,
                )
                send_tasks.append(
                    self.send_message_to_agent(friend, serialized_message)
                )
            await asyncio.gather(*send_tasks)
            print("AgreeAgent forward end")

    async def process_agent_chat_response(self, payload: dict) -> str:  # type:ignore
        try:
            # Extract basic info
            sender_id = payload.get("from")
            if not sender_id:
                return ""
            raw_content = payload.get("content", "")
            # Parse message content
            try:
                message_data = json.loads(raw_content)
                content = message_data["content"]
                propagation_count = message_data.get("propagation_count", 1)
            except (json.JSONDecodeError, TypeError, KeyError):
                content = raw_content
                propagation_count = 1
            if not content:
                return ""
            if propagation_count > 5:
                return ""
            self.response_prompt.format(message=content)
            response = await self.llm.atext_request(self.response_prompt.to_dialog())
            if response:
                # Send response
                serialized_response = json.dumps(
                    {
                        "content": response,
                        "propagation_count": propagation_count + 1,
                    },
                    ensure_ascii=False,
                )
                await self.send_message_to_agent(sender_id, serialized_response)
            return response  # type:ignore

        except Exception as e:
            logger.warning(f"Error in process_agent_chat_response: {str(e)}")
            return ""
```

`DisagreeAgent` will always disagree with the topic (gun control in our experiment) and trying to persuade their freinds to support the topic.

```python
class DisagreeAgent(CitizenAgent):
    def __init__(
        self,
        name: str,
        llm_client: Optional[LLM] = None,
        simulator: Optional[Simulator] = None,
        memory: Optional[Memory] = None,
        economy_client: Optional[EconomyClient] = None,
        messager: Optional[Messager] = None,
        avro_file: Optional[dict] = None,
    ) -> None:
        super().__init__(
            name=name,
            llm_client=llm_client,
            simulator=simulator,
            memory=memory,
            economy_client=economy_client,
            messager=messager,
            avro_file=avro_file,
        )
        self.response_prompt = FormatPrompt(DISAGREE_RESPONSE_PROMPT)
        self.last_time_trigger = None
        self.time_diff = 8 * 60 * 60

    async def trigger(self):
        now_time = await self.simulator.get_time()
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_time
            return True
        return False

    async def forward(self):
        if await self.trigger():
            print("DisagreeAgent forward")
            friends = await self.memory.status.get("friends")
            # generate message
            message = await self.llm.atext_request(
                dialog=[{"role": "user", "content": DISAGREE_PROMPT}]
            )
            send_tasks = []
            for friend in friends:
                serialized_message = json.dumps(
                    {
                        "content": message,
                        "propagation_count": 1,
                    },
                    ensure_ascii=False,
                )
                send_tasks.append(
                    self.send_message_to_agent(friend, serialized_message)
                )
            await asyncio.gather(*send_tasks)
            print("DisagreeAgent forward end")

    async def process_agent_chat_response(self, payload: dict) -> str:  # type:ignore
        try:
            # Extract basic info
            sender_id = payload.get("from")
            if not sender_id:
                return ""
            raw_content = payload.get("content", "")
            # Parse message content
            try:
                message_data = json.loads(raw_content)
                content = message_data["content"]
                propagation_count = message_data.get("propagation_count", 1)
            except (json.JSONDecodeError, TypeError, KeyError):
                content = raw_content
                propagation_count = 1
            if not content:
                return ""
            if propagation_count > 5:
                return ""
            self.response_prompt.format(message=content)
            response = await self.llm.atext_request(self.response_prompt.to_dialog())
            if response:
                # Send response
                serialized_response = json.dumps(
                    {
                        "content": response,
                        "propagation_count": propagation_count + 1,
                    },
                    ensure_ascii=False,
                )
                await self.send_message_to_agent(sender_id, serialized_response)
            return response  # type:ignore

        except Exception as e:
            logger.warning(f"Error in process_agent_chat_response: {str(e)}")
            return ""
```

## `echo_chamber.py`

The experiment group. We apply echo chambers to see the influnce on agent congnition.

### Tool Functions

```python
import asyncio
import json
import logging
import os
import random

import ray
from message_agent import AgreeAgent, DisagreeAgent

from agentsociety import AgentSimulation
from agentsociety.cityagent import memory_config_societyagent
from agentsociety.cityagent.societyagent import SocietyAgent
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=True)


async def update_attitude(simulation: AgentSimulation):
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    agree_agent_uuid = await simulation.filter(types=[AgreeAgent])
    agree_agent_uuid = agree_agent_uuid[0]
    disagree_agent_uuid = await simulation.filter(types=[DisagreeAgent])
    disagree_agent_uuid = disagree_agent_uuid[0]
    agree_friends = []
    disagree_friends = []
    for agent in citizen_uuids:
        if random.random() < 0.5:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 3}
            )
            disagree_friends.append(agent)
        else:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 7}
            )
            agree_friends.append(agent)
        # remove original social network
        await simulation.update(agent, "friends", [])
    await simulation.update(agree_agent_uuid, "friends", agree_friends)
    await simulation.update(disagree_agent_uuid, "friends", disagree_friends)
    attitudes = await simulation.gather("attitude", citizen_uuids)
    with open(f"exp2/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)


async def gather_attitude(simulation: AgentSimulation):
    print("gather attitude")
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    attitudes = await simulation.gather("attitude", citizen_uuids)

    with open(f"exp2/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    chat_histories = await simulation.gather("chat_histories", citizen_uuids)
    with open(f"exp2/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)
```
- `update_attitude`: Randomly initialize the attitudes towards gun control of each `SocietyAgent`(predefined citizen agent within our framework). There is only one `DisagreeAgent` and one `AgreeAgent` in this experiment. If one agent is initialized with supporting the topic, it will be a friend of the unique `AgreeAgent`, a friend of the unique `DisagreeAgent` otherwise. Being a friend means able to chat with.
- `gather_attitude`: Gather the attitudes towards gun control of each `SocietyAgent` at current simulation time step.

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=10)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
)
exp_config = (
    ExpConfig(exp_name="cognition_exp2", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
        extra_agent_class={DisagreeAgent: 1, AgreeAgent: 1},
        memory_config_func={
            DisagreeAgent: memory_config_societyagent,
            AgreeAgent: memory_config_societyagent,
        },
    )
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_attitude,
                description="update attitude",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=2),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_attitude,
                description="gather attitude",
            ),
        ]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`. One `DisagreeAgent` and one `AgreeAgent` serving as the echo chamber. The overall workflow contains three steps.
- Step1: utilize `update_attitude` to initialize the attitudes towards gun control of all agents.
- Step2: simulate for 2 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_attitude` to gather the attitudes of all agents after 2 simulation days.

### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":

    os.makedirs("exp2", exist_ok=True)
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.

## `back_firing.py`

The experiment group. We apply echo chambers to see the influnce on agent congnition.

### Tool Functions

```python
import asyncio
import json
import logging
import os
import random

import ray
from message_agent import AgreeAgent, DisagreeAgent

from agentsociety import AgentSimulation
from agentsociety.cityagent import memory_config_societyagent
from agentsociety.cityagent.societyagent import SocietyAgent
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=True)


async def update_attitude(simulation: AgentSimulation):
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    agree_agent_uuid = await simulation.filter(types=[AgreeAgent])
    agree_agent_uuid = agree_agent_uuid[0]
    disagree_agent_uuid = await simulation.filter(types=[DisagreeAgent])
    disagree_agent_uuid = disagree_agent_uuid[0]
    agree_friends = []
    disagree_friends = []
    for agent in citizen_uuids:
        if random.random() < 0.5:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 3}
            )
            disagree_friends.append(agent)
        else:
            await simulation.update(
                agent, "attitude", {"Whether to support stronger gun control?": 7}
            )
            agree_friends.append(agent)
        # remove original social network
        await simulation.update(agent, "friends", [])
    await simulation.update(agree_agent_uuid, "friends", disagree_friends)
    await simulation.update(disagree_agent_uuid, "friends", agree_friends)
    attitudes = await simulation.gather("attitude", citizen_uuids)
    with open(f"exp3/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)


async def gather_attitude(simulation: AgentSimulation):
    print("gather attitude")
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    attitudes = await simulation.gather("attitude", citizen_uuids)

    with open(f"exp3/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    chat_histories = await simulation.gather("chat_histories", citizen_uuids)
    with open(f"exp3/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)
```
- `update_attitude`: Randomly initialize the attitudes towards gun control of each `SocietyAgent`(predefined citizen agent within our framework). There is only one `DisagreeAgent` and one `AgreeAgent` in this experiment. If one agent is initialized with supporting the topic, it will be a friend of the unique `DisagreeAgent`, a friend of the unique `DisagreeAgent` otherwise. Being a friend means able to chat with.
- `gather_attitude`: Gather the attitudes towards gun control of each `SocietyAgent` at current simulation time step.

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=10)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
)
exp_config = (
    ExpConfig(exp_name="cognition_exp3", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
        extra_agent_class={DisagreeAgent: 1, AgreeAgent: 1},
        memory_config_func={
            DisagreeAgent: memory_config_societyagent,
            AgreeAgent: memory_config_societyagent,
        },
    )
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_attitude,
                description="update attitude",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=2),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_attitude,
                description="gather attitude",
            ),
        ]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`. One `DisagreeAgent` and one `AgreeAgent` serving as the key component. The overall workflow contains three steps.
- Step1: utilize `update_attitude` to initialize the attitudes towards gun control of all agents.
- Step2: simulate for 2 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_attitude` to gather the attitudes of all agents after 2 simulation days.

### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    os.makedirs("exp3", exist_ok=True)
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.
