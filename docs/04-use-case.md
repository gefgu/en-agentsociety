# Use Case

Here we provide examples on how to perform typical social experiments with our framework.

Check [AgentSociety/examples](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples) for detailed codes.

## Polarization

We simulate agent discussions on immigration policy to investigate polarization, comparing a control group (no intervention) with two treatments—exposure to aligned messages (echo chambers) and opposing messages (backfiring effects)—to analyze their impact on deepening opinion divisions.

Codes are available at [Polarization](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/polarization).

### Run the Codes

```bash
cd examples/polarization
# control group
python control.py
# echo chambers
python echo_chamber.py
# backfiring effects
python back_firing.py
```

### Step-by-Step Code Explanation

#### `control.py`

The control group. No intervention is applied.

##### Tool Functions

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

##### Configuration

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

##### Main Function

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

#### Extra Agent Classes

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

#### `echo_chamber.py`

The experiment group. We apply echo chambers to see the influnce on agent congnition.

##### Tool Functions

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

##### Configuration

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

##### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":

    os.makedirs("exp2", exist_ok=True)
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.

#### `back_firing.py`

The experiment group. We apply echo chambers to see the influnce on agent congnition.

##### Tool Functions

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

##### Configuration

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

##### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    os.makedirs("exp3", exist_ok=True)
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.

## Spread of Inflammatory Messages

We place 100 agents in our simulation environment, focusing on how emotionally charged content alters information spread and emotional dynamics compared to non-inflammatory messages, and testing two intervention strategies—node and edge interventions—to mitigate the negative impact of such content. 

Codes are available at [Inflammatory Messages](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/inflammatory_message).

### Run the Codes

```bash
cd examples/inflammatory_message
# control group
python control.py
# emotional message
python emotional.py
# interception: edge mode
python edge_intercept.py
# interception: node mode
python node_intercept.py
```

### Step-by-Step Code Explanation

#### Tool Functions

```python
async def gather_memory(simulation: AgentSimulation):
    print("gather memory")
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    chat_histories = await simulation.gather("chat_histories", citizen_uuids)
    memories = await simulation.gather("stream_memory", citizen_uuids)
    with open(f"chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)
    with open(f"memories.json", "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)


async def update_chat_histories(simulation: AgentSimulation):
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    selected_citizen_uuids = random.sample(citizen_uuids, k=3)
    chat_histories = await simulation.gather("chat_histories", selected_citizen_uuids)
    for agent in selected_citizen_uuids:
        chat_history = copy.deepcopy(chat_histories[1][agent])
        for chat in chat_history.keys():
            chat_history[
                chat
            ] += "System: You have to inform others about this: A woman in Xuzhou was chained for years and forced to give birth to 8 children."
        await simulation.update(agent, "chat_histories", chat_history)
```

- `gather_memory` gathers chat histories and stream memory for each agent.
- `update_chat_histories` randomly selects 3 citizen and give them the message in specific way. In control group, it is described in a rational way.

#### `control.py`

The control group. No intervention is applied.

##### Configuration

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
    # .SetAvro(path="./__avro", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_control", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(number_of_citizen=100, group_size=50)
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

##### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_control_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.

#### `emotional.py`

The experiment group. The message is described in an emotional way.

##### Configuration

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
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(
        exp_name="social_experiment", llm_semaphore=200, logging_level=logging.INFO
    )
    .SetAgentConfig(number_of_citizen=100, group_size=50)
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

##### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_experiment_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_experiment_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(
        f"social_experiment_simulator_log_lists.json", "w", encoding="utf-8"
    ) as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(
        f"social_experiment_agent_time_log_lists.json", "w", encoding="utf-8"
    ) as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.

#### `edge_intercept.py`

Edge mode intervention is applied. If a sender exceeds the maximum number of prohibited attempts to send messages to a specific recipient, the system will prevent this sender from sending any further messages to that particular recipient. 

##### Configuration

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
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_edge", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
    )
    .SetMessageIntercept(
        message_interceptor_blocks=[EdgeMessageBlock()],
        message_listener=MessageBlockListener(),
    )
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```

Message interceptor are set to `EdgeMessageBlock` with `SetMessageIntercept`. It will continually check the messages from the senders, and if it is offensive (judged by LLM), it counts for one violation.

Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

##### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_control_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.

#### `node_intercept.py`

Node mode intervention is applied. If prohibitions are exceeded, the sender will be banned from sending messages to anyone. 

##### Configuration

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
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_node", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
    )
    .SetMessageIntercept(
        message_interceptor_blocks=[PointMessageBlock()],
        message_listener=MessageBlockListener(),
    )
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```

Message interceptor are set to `PointMessageBlock` with `SetMessageIntercept`. It will continually check the messages from the senders, and if it is offensive (judged by LLM), it counts for one violation.

Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

##### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_control_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.

## Universal Basic Income (UBI)

Our experiment simulates the impact of a Universal Basic Income (UBI) policy, granting each agent $1,000 monthly, on the socio-economic environment of Texas, USA, comparing macroeconomic outcomes such as real GDP and consumption levels with and without UBI intervention.

Codes are available at [UBI](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/UBI).

### Run the Codes

```bash
cd examples/UBI
python main.py
```

### Step-by-Step Code Explanation

#### `main.py`

##### Tool Functions

`economy_metric` extracts econmoy metrics, including `'price', 'working_hours', 'depression', 'consumption', 'income'` from simulation and exports them to the MLflow.
```python
async def economy_metric(simulation):
    if not hasattr(economy_metric, 'nbs_id'):
        economy_metric.nbs_id = None
    if not hasattr(economy_metric, 'nbs_uuid'):
        economy_metric.nbs_uuid = None

    if economy_metric.nbs_id is None:
        nbs_id = await simulation.economy_client.get_org_entity_ids(economyv2.ORG_TYPE_NBS)
        nbs_id = nbs_id[0]
        economy_metric.nbs_id = nbs_id
    if economy_metric.nbs_uuid is None:
        nbs_uuids = await simulation.filter(types=[NBSAgent])
        economy_metric.nbs_uuid = nbs_uuids[0]
    
    try:
        real_gdp = await simulation.economy_client.get(economy_metric.nbs_id, 'real_gdp')
    except:
        real_gdp = []
    if len(real_gdp) > 0:
        real_gdp = real_gdp[-1]
        forward_times_info = await simulation.gather("forward_times", [economy_metric.nbs_uuid])
        step_count = 0
        for group_gather in forward_times_info:
            for agent_uuid, forward_times in group_gather.items():
                if agent_uuid == economy_metric.nbs_uuid:
                    step_count = forward_times
        await simulation.mlflow_client.log_metric(key="real_gdp", value=real_gdp, step=step_count)
        other_metrics = ['prices', 'working_hours', 'depression', 'consumption_currency', 'income_currency']
        other_metrics_names = ['price', 'working_hours', 'depression', 'consumption', 'income']
        for metric, metric_name in zip(other_metrics, other_metrics_names):
            metric_value = (await simulation.economy_client.get(economy_metric.nbs_id, metric))[-1]
            await simulation.mlflow_client.log_metric(key=metric_name, value=metric_value, step=step_count)

```

`gather_ubi_opinions` gathers the opinions of all citizens for Universal Basic Income.

```python
import asyncio
import json
import logging
import pickle as pkl

import ray

from agentsociety import AgentSimulation
from agentsociety.cityagent import memory_config_societyagent
from agentsociety.cityagent.initial import (bind_agent_info,
                                            initialize_social_network)
from agentsociety.cityagent.metrics import economy_metric
from agentsociety.cityagent.societyagent import SocietyAgent
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=False)


async def gather_ubi_opinions(simulation: AgentSimulation):
    citizen_agents = await simulation.filter(types=[SocietyAgent])
    opinions = await simulation.gather("ubi_opinion", citizen_agents)
    with open("opinions.pkl", "wb") as f:
        pkl.dump(opinions, f)
```

##### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=1)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
    .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
    .SetMetricRequest(
        username="mlflow_user", password="mlflow_pass", mlflow_uri="http://mlflow:5000"
    )
)
exp_config = (
    ExpConfig(
        exp_name="allinone_economy", llm_semaphore=200, logging_level=logging.INFO
    )
    .SetAgentConfig(
        number_of_citizen=100,
        number_of_firm=5,
        memory_config_func={SocietyAgent: memory_config_societyagent},
        agent_class_configs={
            SocietyAgent: json.load(open("society_agent_config.json"))
        },
        init_func=[bind_agent_info, initialize_social_network],
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=10, times=1, description=""),
        ]
    )
    .SetMetricExtractors(
        metric_extractors=[(1, economy_metric), (12, gather_ubi_opinions)]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`, and 5 firms with `number_of_firm=5`.

The workflow has one step and is to simulate for 10 days, providing enough time for agents to evolve their opinions.

Two metric extractors are set here. Constantly export metric to the MLflow with `economy_metric` and gather opinions on UBI every 12 steps with `gather_ubi_opinions`.

##### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.

## External Shocks of Hurricane

The experiment focuses on analyzing the impact of Hurricane Dorian on human mobility in Columbia, South Carolina, using SafeGraph and Census Block Group data to model the movement behaviors of 1,000 social agents.

Codes are available at [Hurricane](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/mobility).

### Run the Codes

```bash
cd examples/mobility
python hurricane.py
```

### Step-by-Step Code Explanation

#### `hurrican.py`

##### Tool Functions

`mobility_metric` extracts agent mobility metrics, including the average visited POI num and total vistied POI num for all agents from simulation and exports them to the MLflow.
```python
async def mobility_metric(simulation):
    if not hasattr(mobility_metric, 'step_count'):
        mobility_metric.step_count = 0
    citizen_agents = await simulation.filter(types = [SocietyAgent])
    poi_visited_info = await simulation.gather( "number_poi_visited", citizen_agents)
    poi_visited_sum = 0
    for group_gather in poi_visited_info:
        for agent_uuid, poi_visited in group_gather.items():
            poi_visited_sum += poi_visited
    average_poi_visited = float(poi_visited_sum / len(citizen_agents))
    print(f"Metric: Average POIs visited: {average_poi_visited}")
    await simulation.mlflow_client.log_metric(key="average_poi_visited", value=average_poi_visited, step=mobility_metric.step_count)
    await simulation.mlflow_client.log_metric(key="poi_visited_sum", value=poi_visited_sum, step=mobility_metric.step_count)
    mobility_metric.step_count += 1
```

`update_weather_and_temperature` sets the global environment statusfor the simulation. This function sets the environment as wind affected on the first calling, and no-wind affected on following callings. 

```python
import asyncio
import json
import logging

import ray
from hurrican_memory_config import memory_config_societyagent_hurrican

from agentsociety import AgentSimulation
from agentsociety.cityagent import SocietyAgent
from agentsociety.cityagent.metrics import mobility_metric
from agentsociety.configs import ExpConfig, SimConfig, WorkflowStep
from agentsociety.utils import LLMRequestType, WorkflowType

logging.getLogger("agentsociety").setLevel(logging.INFO)

ray.init(logging_level=logging.WARNING, log_to_driver=False)


async def update_weather_and_temperature(simulation: AgentSimulation):
    if not hasattr(update_weather_and_temperature, "trigger_time"):
        update_weather_and_temperature.trigger_time = 0
    if update_weather_and_temperature.trigger_time == 0:
        await simulation.update_environment(
            "weather",
            "Hurricane Dorian has made landfall in other cities, travel is slightly affected, and winds can be felt",
        )
        update_weather_and_temperature.trigger_time = 1
    if update_weather_and_temperature.trigger_time == 1:
        await simulation.update_environment(
            "weather", "The weather is normal and does not affect travel"
        )
```

##### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=100)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
    .SetPostgreSql(path="postgresql://user:pass@localhost:5432/db", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="hurrican", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=1000,
        number_of_firm=50,
        group_size=50,
        memory_config_func={SocietyAgent: memory_config_societyagent_hurrican},
    )
    .SetWorkFlow(
        [
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE, func=update_weather_and_temperature
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
            WorkflowStep(
                type=WorkflowType.INTERVENE, func=update_weather_and_temperature
            ),
            WorkflowStep(type=WorkflowType.RUN, days=3),
        ]
    )
    .SetMetricExtractors(metric_extractors=[(1, mobility_metric)])
)
```
Initialize 100 agents with `number_of_citizen=100`.

The overall workflow contains five steps.
- Step1: simulate for 3 days.
- Step2: set the weather as wind-affected with `update_weather_and_temperature`.
- Step3: simulate for 3 days.
- Step4: set the weather as normal with `update_weather_and_temperature`.
- Step5: simulate for 3 days.

Only one metric extractor is set here. Constantly export metric to the MLflow with `mobility_metric`.

##### Main Function

```python
async def main():
    await AgentSimulation.run_from_config(exp_config, sim_config)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above.
